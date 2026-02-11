#!/usr/bin/env python3
"""Ingest a YouTube video's transcript into shared RAG memory.

Example:
  python scripts/IngestYouTubeToRag.py "https://youtu.be/UWKNLR4jOI0" --index
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import parse_qs, urlparse

import requests
from youtube_transcript_api import YouTubeTranscriptApi


def parse_video_id(url_or_id: str) -> str:
    raw = (url_or_id or "").strip()
    if not raw:
        raise ValueError("Video URL or ID is required.")

    if re.fullmatch(r"[A-Za-z0-9_-]{11}", raw):
        return raw

    u = urlparse(raw)
    host = (u.netloc or "").lower()
    path = (u.path or "").strip("/")

    if "youtu.be" in host and path:
        return path.split("/")[0]

    if "youtube.com" in host:
        if path == "watch":
            q = parse_qs(u.query or "")
            vid = (q.get("v") or [""])[0]
            if vid:
                return vid
        if path.startswith("shorts/"):
            return path.split("/", 1)[1]
        if path.startswith("embed/"):
            return path.split("/", 1)[1]

    raise ValueError(f"Could not parse video ID from: {url_or_id}")


def slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (text or "").strip().lower()).strip("-")
    if not s:
        s = "youtube-notes"
    return s[:max_len].strip("-")


def mmss(seconds: float) -> str:
    total = int(max(0, seconds))
    m, s = divmod(total, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def get_oembed_title(url: str) -> Tuple[str, str]:
    endpoint = "https://www.youtube.com/oembed"
    try:
        r = requests.get(endpoint, params={"url": url, "format": "json"}, timeout=20)
        r.raise_for_status()
        j = r.json()
        return str(j.get("title") or "").strip(), str(j.get("author_name") or "").strip()
    except Exception:
        return "", ""


def fetch_transcript(video_id: str):
    api = YouTubeTranscriptApi()
    # Prefer English, then fall back to auto-generated if needed.
    langs = ["en", "en-US", "en-GB"]
    return api.fetch(video_id, languages=langs)


def build_markdown(
    *,
    source_url: str,
    video_id: str,
    title: str,
    channel: str,
    transcript_items,
) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    transcript_plain = " ".join(str(x.text).strip() for x in transcript_items if str(x.text).strip())
    transcript_plain = re.sub(r"\s+", " ", transcript_plain).strip()

    lines = [
        "# YouTube Transcript Ingest",
        "",
        f"- Title: {title or '(unknown title)'}",
        f"- Channel: {channel or '(unknown channel)'}",
        f"- Video ID: {video_id}",
        f"- Source: {source_url}",
        f"- Ingested At: {now}",
        f"- Transcript Snippets: {len(transcript_items)}",
        "",
        "## Transcript (Plain)",
        transcript_plain if transcript_plain else "(No transcript text found.)",
        "",
        "## Transcript (Timestamped)",
    ]

    for item in transcript_items:
        text = str(item.text).strip()
        if not text:
            continue
        lines.append(f"- [{mmss(float(item.start))}] {text}")

    return "\n".join(lines).strip() + "\n"


def ingest(
    url_or_id: str,
    memory_root: Path,
    section: str,
    run_indexer: bool,
) -> Tuple[Path, int]:
    video_id = parse_video_id(url_or_id)
    source_url = url_or_id if url_or_id.startswith("http") else f"https://youtu.be/{video_id}"
    title, channel = get_oembed_title(source_url)
    transcript_items = fetch_transcript(video_id)

    target_dir = memory_root / section
    target_dir.mkdir(parents=True, exist_ok=True)
    date_tag = dt.datetime.now().strftime("%Y%m%d")
    file_slug = slugify(title or video_id)
    out_path = target_dir / f"youtube_{video_id}_{file_slug}_{date_tag}.md"

    content = build_markdown(
        source_url=source_url,
        video_id=video_id,
        title=title,
        channel=channel,
        transcript_items=transcript_items,
    )
    out_path.write_text(content, encoding="utf-8")

    if run_indexer:
        indexer = memory_root / "velocity_rag.py"
        if indexer.exists():
            subprocess.run(["python", str(indexer)], check=False)

    return out_path, len(transcript_items)


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest YouTube transcript into shared RAG memory.")
    parser.add_argument("url_or_id", help="YouTube URL or video ID")
    parser.add_argument(
        "--memory-root",
        default=r"D:\scanner\velocity_memory",
        help="RAG memory root path",
    )
    parser.add_argument(
        "--section",
        default="strategy_updates",
        help="Subfolder under memory root (default: strategy_updates)",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="Run velocity_rag indexer after saving transcript",
    )
    args = parser.parse_args()

    out_path, count = ingest(
        url_or_id=args.url_or_id,
        memory_root=Path(args.memory_root),
        section=args.section,
        run_indexer=args.index,
    )
    print(f"Saved: {out_path}")
    print(f"Transcript snippets: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
