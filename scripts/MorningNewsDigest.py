#!/usr/bin/env python3
"""Generate a Finviz-first morning news digest for last ~24 hours.

Usage:
    python scripts/MorningNewsDigest.py
    python scripts/MorningNewsDigest.py --save
    python scripts/MorningNewsDigest.py --top 12 --memory-root "D:\\scanner\\velocity_memory"
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
APP_DIR = os.path.join(REPO_ROOT, "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

try:
    from market_intel import gather_market_intel
except Exception as exc:  # pragma: no cover - runtime protection
    raise SystemExit(f"Could not import market_intel.py: {exc}")


THEME_KEYWORDS: Dict[str, List[str]] = {
    "Macro/Fed": [
        "fed",
        "fomc",
        "powell",
        "cpi",
        "ppi",
        "inflation",
        "jobs",
        "payroll",
        "gdp",
        "rates",
        "treasury",
        "yield",
    ],
    "Earnings/Guidance": [
        "earnings",
        "guidance",
        "eps",
        "revenue",
        "beat",
        "miss",
        "outlook",
    ],
    "Tech/AI/Semis": [
        "ai",
        "semiconductor",
        "chip",
        "nvidia",
        "amd",
        "intel",
        "apple",
        "microsoft",
        "cloud",
        "datacenter",
    ],
    "Energy/Commodities": [
        "oil",
        "crude",
        "natural gas",
        "opec",
        "gold",
        "copper",
        "commodity",
    ],
    "Policy/Geopolitics": [
        "tariff",
        "sanction",
        "geopolitical",
        "war",
        "ceasefire",
        "china",
        "taiwan",
        "middle east",
        "europe",
    ],
    "M&A/Legal": [
        "merger",
        "acquisition",
        "antitrust",
        "doj",
        "sec",
        "lawsuit",
        "probe",
    ],
}

HIGH_IMPACT_WORDS = {
    "fed",
    "cpi",
    "inflation",
    "jobs",
    "earnings",
    "guidance",
    "downgrade",
    "upgrade",
    "tariff",
    "opec",
    "war",
}

PRIORITY_SOURCES = {
    "reuters",
    "bloomberg",
    "wall street journal",
    "wsj",
    "financial times",
    "cnbc",
    "marketwatch",
    "barrons",
}


@dataclass
class NewsItem:
    title: str
    source: str
    date_text: str
    link: str
    themes: List[str]
    score: float
    age_hours: Optional[float]


def _parse_finviz_date(date_text: str, now: datetime) -> Optional[datetime]:
    text = (date_text or "").strip()
    if not text:
        return None

    # Common Finviz style: "Today 09:35AM", "Yesterday 03:10PM"
    m = re.match(r"^(Today|Yesterday)\s*,?\s*(\d{1,2}:\d{2}\s*[AP]M)$", text, re.I)
    if m:
        day_word = m.group(1).lower()
        hm = m.group(2).upper().replace(" ", "")
        base_day = now.date()
        if day_word == "yesterday":
            base_day = (now - timedelta(days=1)).date()
        try:
            t = datetime.strptime(hm, "%I:%M%p").time()
            return datetime.combine(base_day, t)
        except ValueError:
            return None

    # Other observed formats from dataframe exports
    fmts = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%m/%d/%Y %I:%M%p",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
        "%b-%d-%y %I:%M%p",
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _parse_pct(value: str) -> Optional[float]:
    s = str(value or "").strip().replace("%", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _extract_themes(title: str) -> List[str]:
    t = title.lower()
    out: List[str] = []
    for theme, words in THEME_KEYWORDS.items():
        if any(w in t for w in words):
            out.append(theme)
    return out


def _score_item(title: str, source: str, themes: List[str], age_hours: Optional[float]) -> float:
    t = title.lower()
    src = (source or "").lower()
    score = 0.0

    score += 1.5 * len(themes)
    if any(k in t for k in HIGH_IMPACT_WORDS):
        score += 1.5
    if any(src_name in src for src_name in PRIORITY_SOURCES):
        score += 1.0

    if age_hours is not None:
        if age_hours <= 3:
            score += 1.0
        elif age_hours <= 24:
            score += 0.5

    return round(score, 2)


def _build_digest(intel: Dict, top_n: int = 10) -> Tuple[str, str]:
    now = datetime.now()
    finviz_rows = intel.get("finviz_news") or []
    parsed: List[NewsItem] = []

    for row in finviz_rows:
        title = str(row.get("title", "")).strip()
        if not title:
            continue
        source = str(row.get("source", "")).strip()
        date_text = str(row.get("date", "")).strip()
        link = str(row.get("link", "")).strip()

        dt = _parse_finviz_date(date_text, now)
        age_hours: Optional[float] = None
        if dt is not None:
            age_hours = (now - dt).total_seconds() / 3600.0
            if age_hours < 0:
                age_hours = 0.0

        # If time parse works, enforce 24-hour snapshot. If not, keep but it will score lower.
        if age_hours is not None and age_hours > 24:
            continue

        themes = _extract_themes(title)
        score = _score_item(title, source, themes, age_hours)
        parsed.append(
            NewsItem(
                title=title,
                source=source,
                date_text=date_text,
                link=link,
                themes=themes,
                score=score,
                age_hours=age_hours,
            )
        )

    parsed.sort(
        key=lambda x: (
            -x.score,
            x.age_hours if x.age_hours is not None else 9999.0,
        )
    )

    theme_counts = Counter()
    for item in parsed:
        for theme in item.themes:
            theme_counts[theme] += 1

    sectors = intel.get("sector_performance") or []
    sector_rank: List[Tuple[str, float]] = []
    for s in sectors:
        name = str(s.get("name", "")).strip()
        pct = _parse_pct(str(s.get("change_today", "")))
        if name and pct is not None:
            sector_rank.append((name, pct))
    sector_rank.sort(key=lambda x: x[1], reverse=True)
    leaders = sector_rank[:3]
    laggards = list(reversed(sector_rank[-3:])) if len(sector_rank) >= 3 else sector_rank

    lines: List[str] = []
    lines.append("=== MORNING NEWS DIGEST (FINVIZ-FIRST) ===")
    lines.append(f"Generated: {now.strftime('%Y-%m-%d %I:%M %p')}")
    lines.append(f"Articles considered (<=24h or unknown time): {len(parsed)}")

    if theme_counts:
        theme_line = ", ".join(f"{k}: {v}" for k, v in theme_counts.most_common(5))
        lines.append(f"Theme heatmap: {theme_line}")
    else:
        lines.append("Theme heatmap: (insufficient data)")

    if leaders:
        lead_text = ", ".join(f"{n} {v:+.2f}%" for n, v in leaders)
        lines.append(f"Sector leaders (today): {lead_text}")
    if laggards:
        lag_text = ", ".join(f"{n} {v:+.2f}%" for n, v in laggards)
        lines.append(f"Sector laggards (today): {lag_text}")

    lines.append("")
    lines.append("Top relevant headlines:")
    if not parsed:
        lines.append("- No Finviz headlines available right now.")
    else:
        for idx, item in enumerate(parsed[:top_n], start=1):
            theme_tag = ", ".join(item.themes) if item.themes else "General"
            when = item.date_text if item.date_text else "time N/A"
            src = item.source if item.source else "Unknown source"
            lines.append(f"{idx}. [{theme_tag}] {item.title}")
            lines.append(f"   Source: {src} | Time: {when} | Priority: {item.score:.2f}")
            if item.link:
                lines.append(f"   Link: {item.link}")

    # Build markdown variant (same content, markdown bullets)
    md: List[str] = []
    md.append("# Morning News Digest (Finviz-first)")
    md.append("")
    md.append(f"- Generated: {now.strftime('%Y-%m-%d %H:%M')}")
    md.append(f"- Articles considered: {len(parsed)}")
    if theme_counts:
        md.append(f"- Theme heatmap: {', '.join(f'{k} ({v})' for k, v in theme_counts.most_common(6))}")
    if leaders:
        md.append(f"- Sector leaders: {', '.join(f'{n} {v:+.2f}%' for n, v in leaders)}")
    if laggards:
        md.append(f"- Sector laggards: {', '.join(f'{n} {v:+.2f}%' for n, v in laggards)}")
    md.append("")
    md.append("## Top Relevant Headlines")
    if not parsed:
        md.append("- No Finviz headlines available right now.")
    else:
        for item in parsed[:top_n]:
            theme_tag = ", ".join(item.themes) if item.themes else "General"
            src = item.source if item.source else "Unknown source"
            when = item.date_text if item.date_text else "time N/A"
            md.append(f"- **[{theme_tag}]** {item.title}")
            md.append(f"  - Source: {src} | Time: {when} | Priority: {item.score:.2f}")
            if item.link:
                md.append(f"  - Link: {item.link}")

    return "\n".join(lines), "\n".join(md)


def _save_digest(markdown_text: str, memory_root: str) -> str:
    market_dir = os.path.join(memory_root, "market_context")
    os.makedirs(market_dir, exist_ok=True)
    name = f"morning_news_digest_{datetime.now().strftime('%Y%m%d')}.md"
    out_path = os.path.join(market_dir, name)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Finviz-first morning news digest.")
    parser.add_argument("--top", type=int, default=10, help="Number of top headlines to show.")
    parser.add_argument("--save", action="store_true", help="Save digest markdown into market_context.")
    parser.add_argument(
        "--memory-root",
        default="D:\\scanner\\velocity_memory",
        help="Base memory directory (default: D:\\scanner\\velocity_memory).",
    )
    args = parser.parse_args()

    intel = gather_market_intel()
    text_digest, md_digest = _build_digest(intel, top_n=max(3, min(args.top, 30)))
    print(text_digest)

    if args.save:
        out_path = _save_digest(md_digest, args.memory_root)
        print("")
        print(f"Saved digest: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
