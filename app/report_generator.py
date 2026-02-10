"""
ClearBlueSky PDF Report Generator
Generates date/time-stamped PDF reports for uploads. No HTML.
"""

import os
import sys
import time
from datetime import datetime, date
from pathlib import Path
import json

# Get the directory where this script is located (portable support)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    import finviz
    FINVIZ_AVAILABLE = True
except ImportError:
    FINVIZ_AVAILABLE = False

try:
    from finviz_safe import get_stock_safe
except ImportError:
    get_stock_safe = None


def _default_risk_checks():
    """Default risk_checks when no Finviz data."""
    return {
        "earnings_date": None,
        "days_until_earnings": None,
        "earnings_timing": None,
        "earnings_safe": True,
        "ex_div_date": None,
        "ex_div_safe": True,
        "relative_volume": None,
        "volume_unusual": False,
    }

# Elite Swing Trader System Prompt (included in every report)
# Used identically in PDF, JSON instructions, and when sending to AI — same prompt everywhere.
MASTER_TRADING_REPORT_DIRECTIVE = r"""
═══════════════════════════════════════════════════════════════════════════════
ELITE SWING TRADER - AI Analysis Directive
═══════════════════════════════════════════════════════════════════════════════

You are a professional stock analyst. Use the scan data, market intelligence, news,
earnings flags, and price history below to produce a human-ready trading report.

TARGET AUDIENCE: Experienced trader. Output must be direct, actionable, no fluff.
Assume the reader knows basics; focus on setup quality, catalyst, invalidation, and execution.

Context: Swing trading, 1-5 day holds (optimal 1-2 days). Universe is S&P 500
stocks + leveraged bull ETFs. Cash account, ~$20K portfolio.

CRITICAL DATA TO USE:
- **EARNINGS WARNINGS**: Tickers with "EARNINGS IN X DAYS" (1-3 days) → AVOID unless exceptional.
- **NEWS SENTIMENT**: DANGER = skip. NEGATIVE = extra caution. POSITIVE = bullish catalyst.
- **OVERNIGHT MARKETS**: Use overseas data for gap risk and sentiment.
- **PRICE AT REPORT**: Compare scanner price vs live price for drift.
- **RELATIVE VOLUME**: 1.5x+ = unusual interest. Use with price action.
- **RSI**: >75 = extended (wait for dip). <30 = oversold potential.
- **Leveraged ETFs (SOXL, TQQQ, etc.)**: MAX 3-DAY HOLD due to decay.

REQUIRED OUTPUT FORMAT — Produce your response in this exact structure:

📊 MARKET SNAPSHOT
──────────────────
[Date] Key indices (SPY, QQQ, DIA) + % change. Sector leader(s). VIX level + trend.
Regime: [e.g. Relief rally in bear context / Risk-on / Defensive]
Overnight: [Asia, Europe impact on US open]. Trade implication: [1 line — e.g. tight stops / swing freely]

🎯 TIER 1: ELITE SETUPS (90+ SCORES)
═══════════════════════════════════════════════════════════════════════════════

#. [TICKER] - [COMPANY NAME] ⭐
   Score: [X]/100 | Price: $[X.XX] ([±X.XX]%) | R:R [X]:1
   Entry: $[X]-[X] | Stop: $[X] | Target: $[X]/$[X]
   Setup: [Technical thesis — SMA structure, RSI, pattern, relative strength vs sector]
   Catalyst: [News, upgrade, sector theme — is it priced in or fresh?]
   Invalidation: [Price level or event that breaks the thesis — e.g. "Break below $X kills it"]
   Timing: [When to enter — open, dip to X, breakout above X, or wait for pullback]
   [Relevant headline(s) if they drive the trade]

[Repeat for each Tier 1 pick — up to 5]

🎯 TIER 2: STRONG SETUPS (85-90 SCORES)
═══════════════════════════════════════════════════════════════════════════════

[Same format. Add ⚠️ if extended (RSI >70), wait-for-dip, or other caution]

🎯 TIER 3: TACTICAL PLAYS (75-85 SCORES)
═══════════════════════════════════════════════════════════════════════════════

[Same format. For leveraged ETFs add: ⚠️ 3-DAY MAX HOLD (leveraged decay)]
[Include correlation note if relevant — e.g. "Trades with NVDA/SEMIs"]

❌ AVOID LIST - DO NOT TRADE
═══════════════════════════════════════════════════════════════════════════════

[Group by reason. Experienced trader needs to know WHY to avoid — prevents FOMO.]

🚫 EARNINGS TOO CLOSE (Binary Risk)
   • [TICKER] - Earnings [date] ([X] days)

🚫 EXTREME OVEREXTENSION (RSI > 75)
   • [TICKER] - RSI [X.XX]

🚫 RELATIVE WEAKNESS (Red on Green Day)
   • [TICKER] - Down [X]% while sector/indices up

🚫 NEWS RED FLAGS
   • [TICKER] - [DANGER/NEGATIVE reason from headlines]

⚠️ RISK MANAGEMENT
═══════════════════════════════════════════════════════════════════════════════

• Order type: LIMIT preferred (avoid slippage on gaps); when to use market
• Hard -5% stops on ALL positions
• 50% profit rule: take half at T1 if gap up 3%+
• Hold period: 5-day max, 3-day for leveraged
• Entry window: [e.g. 9:45-10:15 AM best, or wait for dip]
• Position sizing: Conviction-based ($2K cautious, $5K standard, $10K conviction)
• Regime-aware: [e.g. "Relief rally in bear context — tight stops mandatory"]

📈 KEY INSIGHT / SECTOR ROTATION
═══════════════════════════════════════════════════════════════════════════════

1-3 sentences: Money flow direction, sector rotation signal, correlation.
E.g. "Money flowing INTO Semis/Hardware, OUT OF Software. Buy leaders, avoid laggards."

TOP 5 PLAYS: Your highest-conviction picks (can span tiers). Exactly 5.
For each: Ticker, Score, Entry, Stop, Target, Setup, Catalyst, Invalidation.
Include news/catalysts and execution timing. Experienced trader needs actionable detail.

═══════════════════════════════════════════════════════════════════════════════
END OF DIRECTIVE — Scan data follows below.
═══════════════════════════════════════════════════════════════════════════════

This report was generated by ClearBlueSky Stock Scanner.
GitHub: https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner/releases
"""


class ReportGenerator:
    """Generate date/time-stamped PDF reports only."""

    def __init__(self, save_dir=None):
        if save_dir is None:
            save_dir = os.path.join(BASE_DIR, "reports")
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def _finviz_get_stock_with_retry(self, ticker, max_attempts=3):
        """Call finviz.get_stock with timeout + retries on failure (timeout, 429, etc.)."""
        if get_stock_safe is not None:
            return get_stock_safe(ticker, timeout=30.0, max_attempts=max_attempts)
        # Fallback if finviz_safe not available
        last_error = None
        for attempt in range(max_attempts):
            try:
                stock = finviz.get_stock(ticker)
                if stock is not None:
                    return stock
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                if attempt < max_attempts - 1 and ('429' in err_str or 'timeout' in err_str or 'rate' in err_str or 'connection' in err_str):
                    time.sleep(1.5 * (attempt + 1))
                    continue
                break
        if last_error:
            print(f"  Finviz get_stock for {ticker}: {last_error}")
        return None

    def get_finviz_data(self, ticker, config=None):
        """Get stock data from Finviz; augment price/volume via failover (yfinance > finviz > alpaca)."""
        data = {'ticker': ticker, 'price': 'N/A', 'change': 'N/A'}
        
        if not FINVIZ_AVAILABLE:
            return data
        
        stock = self._finviz_get_stock_with_retry(ticker)
        if stock:
            # Normalize SMA so we never store None (avoids "null" in JSON/report)
            sma50_raw = stock.get('SMA50') or stock.get('SMA 50') or stock.get('50-Day SMA')
            sma200_raw = stock.get('SMA200') or stock.get('SMA 200') or stock.get('200-Day SMA')
            data.update({
                'price': stock.get('Price', 'N/A'),
                'change': stock.get('Change', 'N/A'),
                'volume': stock.get('Volume', 'N/A'),
                'company': stock.get('Company', ticker),
                'sector': stock.get('Sector', 'N/A'),
                'industry': stock.get('Industry', 'N/A'),
                'market_cap': stock.get('Market Cap', 'N/A'),
                'pe': stock.get('P/E', 'N/A'),
                'target': stock.get('Target Price', 'N/A'),
                'rsi': stock.get('RSI (14)', 'N/A'),
                'sma50': sma50_raw if sma50_raw not in (None, '') else 'N/A',
                'sma200': sma200_raw if sma200_raw not in (None, '') else 'N/A',
                'perf_week': stock.get('Perf Week', 'N/A'),
                'perf_month': stock.get('Perf Month', 'N/A'),
                'perf_quarter': stock.get('Perf Quarter', 'N/A'),
                'rel_volume': stock.get('Rel Volume', 'N/A'),
                'recom': stock.get('Recom', 'N/A'),
            })
            # Get news (with one retry on failure + polite delay)
            time.sleep(0.5)  # pause before news fetch — respect Finviz rate limits
            for _ in range(2):
                try:
                    news = finviz.get_news(ticker)
                    data['news'] = news[:5] if news else []
                    break
                except Exception as e:
                    if '429' in str(e).lower() or 'timeout' in str(e).lower():
                        time.sleep(3)  # longer backoff on rate limit
                        continue
                    data['news'] = []
                    break
        
            data['risk_checks'] = self._parse_risk_checks(stock)
        else:
            data['risk_checks'] = _default_risk_checks()

        # Price/volume failover: yfinance > finviz > alpaca (improve when Finviz is missing or stale)
        try:
            from data_failover import get_price_volume
            pv = get_price_volume(ticker, config)
            if pv:
                data['price'] = pv['price']
                data['volume'] = pv['volume'] if pv.get('volume') else data.get('volume', 'N/A')
                if pv.get('change_pct') is not None:
                    data['change'] = f"{pv['change_pct']}%"
        except Exception:
            pass
        return data

    def _derive_sma200_status(self, row):
        """Return 'Above', 'Below', or 'N/A' for 200 SMA. Uses TA price_vs_sma200 if available, else parses Finviz SMA200."""
        ta_dict = row.get('ta') or {}
        pct = ta_dict.get('price_vs_sma200')
        if pct is not None:
            try:
                return 'Above' if float(pct) > 0 else 'Below'
            except (ValueError, TypeError):
                pass  # Fall through to raw SMA200 parsing
        raw = row.get('sma200') or row.get('SMA200')
        if raw in (None, '', 'N/A'):
            return 'N/A'
        try:
            s = str(raw).replace('%', '').strip()
            if not s:
                return 'N/A'
            val = float(s)
            return 'Above' if val > 0 else 'Below' if val < 0 else 'At'
        except (TypeError, ValueError):
            return 'N/A'

    def _parse_risk_checks(self, stock):
        """Build risk_checks from Finviz stock dict: earnings, ex-dividend, relative volume."""
        result = {
            "earnings_date": None,
            "days_until_earnings": None,
            "earnings_timing": None,
            "earnings_safe": True,
            "ex_div_date": None,
            "ex_div_safe": True,
            "relative_volume": None,
            "volume_unusual": False,
        }
        if not stock:
            return result
        # Earnings: Finviz often "Feb 06 AMC" or "Feb 06 BMO" or "-"
        earnings_str = (stock.get("Earnings") or stock.get("Earnings Date") or "").strip()
        if earnings_str and earnings_str != "-":
            timing = None
            if "AMC" in earnings_str.upper():
                timing = "AMC"
                earnings_str = earnings_str.upper().replace("AMC", "").strip()
            elif "BMO" in earnings_str.upper():
                timing = "BMO"
                earnings_str = earnings_str.upper().replace("BMO", "").strip()
            try:
                # "Feb 06" or "Mon Feb 06" -> assume current year
                parts = [p for p in earnings_str.split() if p]
                if len(parts) >= 2:
                    # Use last two tokens as month + day (e.g. "Feb 06" or "Mon Feb 06" -> "Feb 06")
                    month_day = f"{parts[-2]} {parts[-1]}"
                else:
                    month_day = earnings_str
                earnings_date = datetime.strptime(f"{month_day} {date.today().year}", "%b %d %Y").date()
                if earnings_date < date.today():
                    earnings_date = earnings_date.replace(year=earnings_date.year + 1)
                days_until = (earnings_date - date.today()).days
                result["earnings_date"] = earnings_date.isoformat()
                result["days_until_earnings"] = days_until
                result["earnings_timing"] = timing
                result["earnings_safe"] = days_until > 5
            except Exception:
                result["earnings_date"] = earnings_str
                result["earnings_safe"] = False
        # Ex-dividend: Finviz "Ex-Dividend Date" or "Ex-Div Date"
        ex_div_str = (stock.get("Ex-Dividend Date") or stock.get("Ex-Div Date") or "").strip()
        if ex_div_str and ex_div_str not in ("-", "N/A", ""):
            try:
                # "Mar 15" or similar
                ex_date = datetime.strptime(f"{ex_div_str} {date.today().year}", "%b %d %Y").date()
                if ex_date < date.today():
                    ex_date = ex_date.replace(year=ex_date.year + 1)
                result["ex_div_date"] = ex_date.isoformat()
                result["ex_div_safe"] = (ex_date - date.today()).days > 3
            except Exception:
                result["ex_div_date"] = ex_div_str
                result["ex_div_safe"] = False
        # Relative volume: "1.23" or "1.23x"
        rel_vol_raw = stock.get("Rel Volume") or stock.get("Relative Volume") or ""
        if rel_vol_raw not in (None, "", "N/A", "-"):
            try:
                rv = float(str(rel_vol_raw).replace("x", "").strip())
                result["relative_volume"] = round(rv, 2)
                result["volume_unusual"] = rv > 1.5
            except Exception:
                pass
        return result

    def _load_leveraged_mapping(self):
        """Load underlying -> leveraged ticker mapping from leveraged_tickers.json. Returns dict (e.g. {'MU': 'MUU'})."""
        path = Path(BASE_DIR) / "leveraged_tickers.json"
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {str(k).strip().upper(): str(v).strip().upper() for k, v in data.items() if not str(k).startswith("_") and v}
        except Exception:
            return {}

    def _wrap_line(self, text, max_ch=90):
        """Wrap a long line into list of strings of at most max_ch chars (break on space)."""
        lines = []
        for raw in text.split("\n"):
            raw = raw.replace("\r", "")
            while len(raw) > max_ch:
                idx = raw.rfind(" ", 0, max_ch + 1)
                if idx <= 0:
                    idx = max_ch
                lines.append(raw[:idx].strip())
                raw = raw[idx:].strip()
            if raw:
                lines.append(raw)
        return lines

    def _build_analysis_package(self, stocks_data, scan_type, timestamp_display, watchlist_matches, config=None, instructions=None, market_breadth=None, market_intel=None, price_history=None):
        """Build JSON-serializable analysis package for API and file save. instructions = full AI prompt; market_breadth = optional breadth dict from breadth.py; market_intel = optional dict from market_intel.py; price_history = optional 30-day summary dict."""
        leveraged_map = self._load_leveraged_mapping()  # Load once, not per-ticker
        stocks_json = []
        for s in stocks_data:
            news_list = s.get('news') or []
            headlines = []
            for item in news_list[:10]:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    headlines.append({"url": str(item[0]) if item[0] else "", "title": str(item[1]).strip()})
                elif isinstance(item, dict):
                    headlines.append({"url": str(item.get("url", "")), "title": str(item.get("title") or item.get("headline", "")).strip()})
                else:
                    headlines.append({"url": "", "title": str(item).strip()})
            row = {
                "ticker": s.get("ticker", ""),
                "score": s.get("score", 0),
                "on_watchlist": bool(s.get("on_watchlist")),
                "price": s.get("price", "N/A"),
                "change": s.get("change", "N/A"),
                "company": s.get("company", s.get("ticker", "")),
                "sector": s.get("sector", "N/A"),
                "industry": s.get("industry", "N/A"),
                "pe": s.get("pe", "N/A"),
                "target": s.get("target", "N/A"),
                "rsi": s.get("rsi", "N/A"),
                "sma50": s.get("sma50") or "N/A",
                "sma200": s.get("sma200") or "N/A",
                "sma200_status": s.get("sma200_status", "N/A"),
                "rel_volume": s.get("rel_volume", "N/A"),
                "recom": s.get("recom", "N/A"),
                "news": headlines,
                "ta": s.get("ta") or {},
                "sentiment_score": s.get("sentiment_score"),
                "sentiment_label": s.get("sentiment_label"),
                "earnings_in_topics": bool(s.get("earnings_in_topics")),
                "relevance_avg": s.get("relevance_avg"),
                "av_headlines": (s.get("av_headlines") or [])[:5],
                "insider_10b5_1_plan": s.get("insider_10b5_1_plan"),
                "insider_context": s.get("insider_context"),
                "risk_checks": s.get("risk_checks") or _default_risk_checks(),
                "smart_money": s.get("smart_money") or {},
            }
            for k in ("Owner", "Relationship", "Date", "Transaction", "Cost", "Shares", "Value"):
                if s.get(k) not in (None, "", "N/A"):
                    row[k.lower()] = s.get(k)
            if s.get("score", 0) >= 60 and s.get("ticker") in leveraged_map:
                row["leveraged_play"] = leveraged_map[s["ticker"]]
            stocks_json.append(row)
        backtest_stats = None
        try:
            from backtest_db import get_stats_for_scan_type
            backtest_stats = get_stats_for_scan_type(scan_type, min_signals=5)
        except Exception:
            pass
        out = {
            "scan_type": scan_type,
            "timestamp": timestamp_display,
            "watchlist_matches": list(watchlist_matches) if watchlist_matches else [],
            "backtest_stats": backtest_stats,
            "stocks": stocks_json,
        }
        if market_breadth is not None and "error" not in (market_breadth or {}):
            out["market_breadth"] = market_breadth
        if market_intel is not None:
            out["market_intel"] = market_intel
        if price_history:
            out["price_history_30d"] = price_history
        if instructions not in (None, ""):
            out["instructions"] = instructions.strip()
        return out

    def generate_combined_report_pdf(self, results, scan_type="Scan", min_score=60, progress_callback=None, watchlist_tickers=None, config=None, index=None):
        """Generate ONE PDF report. index='sp500' or 'etfs' to include market breadth (full index fetch)."""
        def progress(msg):
            print(msg)
            if progress_callback:
                progress_callback(msg)

        watch_set = (watchlist_tickers or set()) if isinstance(watchlist_tickers, set) else set()
        qualifying = []
        for r in results:
            ticker = r.get('Ticker', r.get('ticker', ''))
            score = r.get('SCORE', r.get('Score', r.get('score', 0)))
            try:
                score = int(float(score)) if score else 0
            except Exception:
                score = 0
            if ticker and score >= min_score:
                on_watchlist = bool(ticker and str(ticker).strip().upper() in watch_set)
                qualifying.append({'ticker': ticker, 'score': score, 'data': r, 'on_watchlist': on_watchlist})

        if not qualifying:
            progress(f"No stocks scored above {min_score}")
            return None, None, None

        qualifying.sort(key=lambda x: (not x.get('on_watchlist'), -x['score']))
        qualifying = qualifying[:15]
        now = datetime.now()
        timestamp_file = now.strftime('%Y%m%d_%H%M%S')
        timestamp_display = now.strftime('%B %d, %Y at %I:%M:%S %p')
        safe_type = "".join(c if c.isalnum() else "_" for c in scan_type)[:20]
        base_name = f"{safe_type}_Scan_{timestamp_file}"
        filepath_pdf = self.save_dir / f"{base_name}.pdf"
        filepath_txt = self.save_dir / f"{base_name}.txt"

        stocks_data = []
        insider_keys = ('Owner', 'Relationship', 'Date', 'Transaction', 'Cost', 'Shares', 'Value')
        for i, q in enumerate(qualifying, 1):
            ticker = q['ticker']
            score = q['score']
            on_watchlist = q.get('on_watchlist', False)
            progress(f"Processing {i}/{len(qualifying)}: {ticker}...")
            data = self.get_finviz_data(ticker, config)
            row = {'ticker': ticker, 'score': score, 'on_watchlist': on_watchlist, **data}
            r = q.get('data', {})
            for k in insider_keys:
                if k in r and r[k] not in (None, '', 'N/A'):
                    row[k] = r[k]
            try:
                if (config or {}).get("include_ta_in_report", True):
                    from ta_engine import get_ta_for_ticker
                    row['ta'] = get_ta_for_ticker(ticker)
                else:
                    row['ta'] = {}
            except Exception:
                row['ta'] = {}
            # Never leave SMA null; flag 200 SMA status for report
            row['sma50'] = row.get('sma50') or 'N/A'
            row['sma200'] = row.get('sma200') or 'N/A'
            row['sma200_status'] = self._derive_sma200_status(row)
            try:
                av_key = (config or {}).get("alpha_vantage_api_key") or ""
                if av_key.strip():
                    from news_sentiment import get_sentiment_for_ticker
                    sent = get_sentiment_for_ticker(ticker, av_key, limit=10)
                    row["sentiment_score"] = sent.get("sentiment_score")
                    row["sentiment_label"] = sent.get("sentiment_label")
                    row["earnings_in_topics"] = sent.get("earnings_in_topics", False)
                    row["relevance_avg"] = sent.get("relevance_avg")
                    row["av_headlines"] = sent.get("headlines", [])[:5]
                else:
                    row["sentiment_score"] = row["sentiment_label"] = row["relevance_avg"] = None
                    row["earnings_in_topics"] = False
                    row["av_headlines"] = []
            except Exception:
                row["sentiment_score"] = row["sentiment_label"] = row["relevance_avg"] = None
                row["earnings_in_topics"] = False
                row["av_headlines"] = []
            if (config or {}).get("use_sec_insider_context") and any(row.get(k) for k in ("Owner", "Transaction", "Date", "Value")):
                try:
                    from sec_edgar import get_insider_10b5_1_context
                    ctx = get_insider_10b5_1_context(ticker)
                    row["insider_10b5_1_plan"] = ctx.get("is_10b5_1_plan")
                    row["insider_context"] = ctx.get("insider_context", "Unknown")
                    time.sleep(0.5)  # polite delay for SEC EDGAR
                except Exception:
                    row["insider_10b5_1_plan"] = None
                    row["insider_context"] = "Unknown"
            else:
                row["insider_10b5_1_plan"] = None
                row["insider_context"] = None
            stocks_data.append(row)
            time.sleep(0.8)  # polite delay between Finviz + API calls per ticker

        # ── Ticker enrichment (earnings, news flags, price stamp, leveraged) ──
        try:
            from ticker_enrichment import enrich_scan_results
            is_swing = "swing" in scan_type.lower() or "dip" in scan_type.lower()
            is_premarket = "premarket" in scan_type.lower() or "pre-market" in scan_type.lower() or "pre market" in scan_type.lower()
            stocks_data = enrich_scan_results(
                stocks_data,
                include_earnings=True,
                include_news_flags=True,
                include_price_stamp=True,
                include_leveraged=is_swing or is_premarket,  # leveraged suggestions on swing/premarket
                progress_callback=progress,
            )
        except Exception as e:
            print(f"[ENRICHMENT] Warning: ticker enrichment failed: {e}")

        tickers_list = ", ".join([s['ticker'] for s in stocks_data])
        watchlist_matches = [s['ticker'] for s in stocks_data if s.get('on_watchlist')]
        data_lines = []
        for s in stocks_data:
            line = f"- {s['ticker']}: Scanner Score {s['score']}, Price ${s.get('price','N/A')}, Today {s.get('change','N/A')}, RSI {s.get('rsi','N/A')}, Target ${s.get('target','N/A')}, P/E {s.get('pe','N/A')}, RelVol {s.get('rel_volume','N/A')}x"
            rc = s.get("risk_checks") or _default_risk_checks()
            if rc.get("earnings_safe") is False and rc.get("days_until_earnings") is not None:
                line += f" | EARNINGS IN {rc.get('days_until_earnings')} DAYS (avoid swing)"
            elif rc.get("earnings_safe") is True:
                line += " | Earnings safe"
            if s.get("insider_context") not in (None, ""):
                line += f" | Insider: {s.get('insider_context', 'Unknown')}"
            # Enrichment: earnings warning
            earnings = s.get("earnings")
            if earnings and earnings.get("warning"):
                line += f" | {earnings['warning']}"
            # Enrichment: news sentiment
            ns = s.get("news_sentiment")
            if ns and ns.get("sentiment") not in (None, "NEUTRAL"):
                line += f" | News: {ns['sentiment']}"
                if ns.get("red_flags"):
                    line += f" ({ns['red_flags'][0][:40]})"
                elif ns.get("green_flags"):
                    line += f" ({ns['green_flags'][0][:40]})"
            # Enrichment: price stamp
            if s.get("price_at_report"):
                line += f" | Live ${s['price_at_report']}"
            # Enrichment: leveraged play
            lp = s.get("leveraged_play")
            if lp:
                line += f" | Leveraged: {lp['leveraged_ticker']}"
            data_lines.append(line)

        market_breadth = None
        if index and index in ("sp500", "etfs"):
            try:
                from breadth import fetch_full_index_for_breadth, calculate_market_breadth
                all_stocks = fetch_full_index_for_breadth(index, progress)
                if all_stocks:
                    market_breadth = calculate_market_breadth(all_stocks)
            except Exception:
                pass

        # Market Intelligence (Google News, Finviz news, sectors, market snapshot)
        market_intel = None
        if (config or {}).get("use_market_intel", True):
            try:
                from market_intel import gather_market_intel, format_intel_for_prompt
                market_intel = gather_market_intel(progress_callback=progress)
                market_intel_prompt = format_intel_for_prompt(market_intel)
            except Exception:
                market_intel_prompt = ""
        else:
            market_intel_prompt = ""

        # Smart Money signals (WSB for all scanners; full package for Trend)
        smart_money_data = {}
        smart_money_prompt = ""
        try:
            from smart_money import get_smart_money_batch, format_smart_money_for_prompt
            ticker_list = [s['ticker'] for s in stocks_data]
            is_trend = "trend" in scan_type.lower()
            smart_money_data = get_smart_money_batch(ticker_list, full=is_trend, progress_callback=progress)
            # Attach to each stock row for JSON output
            for s in stocks_data:
                t = s['ticker'].upper()
                if t in smart_money_data and smart_money_data[t]:
                    s['smart_money'] = smart_money_data[t]
            # Build prompt lines
            sm_lines = []
            for s in stocks_data:
                t = s['ticker'].upper()
                sm = smart_money_data.get(t, {})
                line = format_smart_money_for_prompt(t, sm)
                if line:
                    sm_lines.append(line)
            if sm_lines:
                smart_money_prompt = "\n\nSMART MONEY SIGNALS:\n" + "\n".join(sm_lines) + "\n"
        except Exception:
            pass

        # Insider data folded into Trend and Swing scans
        insider_prompt = ""
        if "trend" in scan_type.lower() or "swing" in scan_type.lower() or "dip" in scan_type.lower():
            try:
                from insider_scanner import get_insider_data_for_tickers
                ticker_list_ins = [s['ticker'] for s in stocks_data]
                insider_data = get_insider_data_for_tickers(ticker_list_ins, progress_callback=progress)
                if insider_data:
                    # Attach to stock rows for JSON
                    for s in stocks_data:
                        t = s['ticker'].upper()
                        if t in insider_data:
                            s['recent_insider'] = insider_data[t]
                    # Build prompt
                    ins_lines = []
                    for t, trades in insider_data.items():
                        for trade in trades[:2]:  # max 2 per ticker
                            ins_lines.append(f"  {t}: {trade.get('Transaction','?')} by {trade.get('Owner','?')} | ${trade.get('Value','?')} | {trade.get('Date','?')}")
                    if ins_lines:
                        insider_prompt = "\n\nRECENT INSIDER ACTIVITY (for scan tickers):\n" + "\n".join(ins_lines) + "\n"
            except Exception as e:
                print(f"[INSIDER] Insider enrichment failed: {e}")

        # 30-day price history (fresh download every scan run — sanity check)
        price_history = {}
        price_history_prompt = ""
        try:
            from price_history import fetch_price_history, format_price_history_for_prompt, price_history_for_json
            ph_tickers = [s['ticker'] for s in stocks_data]
            price_history = fetch_price_history(scan_tickers=ph_tickers, progress_callback=progress)
            price_history_prompt = format_price_history_for_prompt(price_history)
        except Exception:
            pass

        watchlist_line = f"\nWATCHLIST MATCHES (prioritize these): {', '.join(watchlist_matches)}\n" if watchlist_matches else ""
        breadth_line_prompt = ""
        if market_breadth and "error" not in market_breadth:
            regime = market_breadth.get("market_regime", "N/A")
            sma50_pct = market_breadth.get("sp500_above_sma50_pct") if market_breadth.get("sp500_above_sma50_pct") is not None else "N/A"
            sma200_pct = market_breadth.get("sp500_above_sma200_pct") if market_breadth.get("sp500_above_sma200_pct") is not None else "N/A"
            breadth_line_prompt = f"\nMarket breadth (position sizing): {regime} | Above SMA50: {sma50_pct}% | Above SMA200: {sma200_pct}% | A/D: {market_breadth.get('advance_decline')} | Avg RSI: {market_breadth.get('avg_rsi_sp500')}\n"
        ai_prompt = f"""SCAN: {scan_type}.{breadth_line_prompt}
{market_intel_prompt}{smart_money_prompt}{insider_prompt}{price_history_prompt}

STOCKS TO ANALYZE: {tickers_list}
{watchlist_line}

DATA SUMMARY:
{chr(10).join(data_lines)}

Use the directive above. Produce output in: MARKET SNAPSHOT → TIER 1/2/3 picks (Setup + Catalyst for each) → AVOID LIST (categorized) → RISK MANAGEMENT → KEY INSIGHT → TOP 5 PLAYS. Include news/catalysts and entry details — more detail for humans.
"""

        leveraged_mapping = self._load_leveraged_mapping()
        LEVERAGED_MIN_SCORE = 60  # only suggest leveraged when score is "good"
        body_lines = [
            "",
            "═══════════════════════════════════════════════════",
            "STOCK DATA (from scanner)",
            "═══════════════════════════════════════════════════",
            ""
        ]
        if market_breadth and "error" not in market_breadth:
            regime = market_breadth.get("market_regime", "N/A")
            sma50 = market_breadth.get("sp500_above_sma50_pct") if market_breadth.get("sp500_above_sma50_pct") is not None else "N/A"
            sma200 = market_breadth.get("sp500_above_sma200_pct") if market_breadth.get("sp500_above_sma200_pct") is not None else "N/A"
            ad = market_breadth.get("advance_decline")
            rsi = market_breadth.get("avg_rsi_sp500")
            body_lines.append(f"Market breadth: {regime} | Above SMA50: {sma50}% | Above SMA200: {sma200}% | A/D: {ad} | Avg RSI: {rsi}")
            body_lines.append("")
        # Add market intelligence to text report
        if market_intel_prompt:
            body_lines.append(market_intel_prompt)
            body_lines.append("")
        # Add smart money signals to text report
        if smart_money_prompt:
            body_lines.append(smart_money_prompt)
            body_lines.append("")
        # Add insider activity to text report
        if insider_prompt:
            body_lines.append(insider_prompt)
            body_lines.append("")
        # Add 30-day price history to text report
        if price_history_prompt:
            body_lines.append(price_history_prompt)
            body_lines.append("")
        for s in stocks_data:
            ticker = s['ticker']
            score = s.get('score', 0)
            body_lines.append(f"——— {ticker} ———")
            price_line = f"Score {s['score']}  | Price ${s.get('price','N/A')}"
            if s.get("price_at_report"):
                price_line += f"  (live ${s['price_at_report']} at {s.get('report_time','')})"
            price_line += f"  | Change {s.get('change','N/A')}  | RSI {s.get('rsi','N/A')}  | Target ${s.get('target','N/A')}  | P/E {s.get('pe','N/A')}  | RelVol {s.get('rel_volume','N/A')}x"
            body_lines.append(price_line)
            # Enrichment: earnings warning
            earnings = s.get("earnings")
            if earnings and earnings.get("warning"):
                body_lines.append(f"*** {earnings['warning']} *** (Earnings date: {earnings.get('earnings_date','N/A')})")
            elif earnings and earnings.get("earnings_date"):
                body_lines.append(f"Earnings date: {earnings['earnings_date']} ({earnings.get('days_away','?')} days away)")
            rc = s.get("risk_checks") or _default_risk_checks()
            if rc.get("earnings_safe") is False and rc.get("days_until_earnings") is not None:
                body_lines.append(f"EARNINGS IN {rc.get('days_until_earnings')} DAYS - avoid for swing")
            elif rc.get("earnings_date") and rc.get("earnings_safe") is True:
                body_lines.append("Earnings safe (>5 days out)")
            if rc.get("ex_div_safe") is False and rc.get("ex_div_date"):
                body_lines.append(f"Ex-div {rc.get('ex_div_date')} - price drop expected")
            if rc.get("volume_unusual") and rc.get("relative_volume") is not None:
                body_lines.append(f"RelVol {rc.get('relative_volume')}x (unusual)")
            # Enrichment: news sentiment
            ns = s.get("news_sentiment")
            if ns and ns.get("sentiment") != "NEUTRAL":
                flag_line = f"News Sentiment: {ns['sentiment']}"
                if ns.get("red_flags"):
                    flag_line += " | Red flags: " + "; ".join(ns['red_flags'][:3])
                if ns.get("green_flags"):
                    flag_line += " | Green flags: " + "; ".join(ns['green_flags'][:3])
                body_lines.append(flag_line)
            if any(s.get(k) for k in ('Owner', 'Transaction', 'Date', 'Value')):
                body_lines.append(f"Insider: {s.get('Owner','')} | {s.get('Relationship','')} | {s.get('Date','')} | {s.get('Transaction','')} | Cost {s.get('Cost','')} | Shares {s.get('Shares','')} | Value {s.get('Value','')}")
                if s.get("insider_context") not in (None, ""):
                    body_lines.append(f"Insider context: {s.get('insider_context', 'Unknown')} (from SEC Form 4)")
            # Leveraged play (enrichment-based or legacy mapping)
            lp = s.get("leveraged_play")
            if lp:
                body_lines.append(f"Leveraged play: {lp['leveraged_ticker']} ({lp.get('match_type','direct')}) - NOT for long-term (volatility decay)")
            elif score >= LEVERAGED_MIN_SCORE and ticker in leveraged_mapping:
                lev = leveraged_mapping[ticker]
                body_lines.append(f"Leveraged play: {lev} (use in place of {ticker} for leveraged exposure)")
                body_lines.append("  Leveraged ETFs are high-risk; not suitable for long-term buy-and-hold (volatility decay).")
            body_lines.append(f"Company: {s.get('company', ticker)}  | Sector: {s.get('sector','N/A')}")
            body_lines.append(f"SMA50: {s.get('sma50','N/A')}  | SMA200: {s.get('sma200','N/A')}  | SMA200 status: {s.get('sma200_status','N/A')}  | Recom: {s.get('recom','N/A')}")
            ta_dict = s.get('ta') or {}
            if ta_dict:
                from ta_engine import format_ta_for_report
                body_lines.append(format_ta_for_report(ta_dict))
            if s.get("sentiment_label") is not None or s.get("sentiment_score") is not None:
                sent_line = f"Sentiment: {s.get('sentiment_label', 'N/A')} (score {s.get('sentiment_score', 'N/A')})"
                if s.get("earnings_in_topics"):
                    sent_line += " | Earnings in recent news"
                body_lines.append(sent_line)
            news_list = s.get('news') or []
            if news_list:
                body_lines.append("Headlines:")
                for i, item in enumerate(news_list[:5]):
                    if isinstance(item, (list, tuple)) and len(item) > 1:
                        head = item[1]
                    elif isinstance(item, dict):
                        head = item.get('title') or item.get('headline') or str(item)
                    else:
                        head = str(item)
                    body_lines.append(f"  {i+1}. {str(head).strip()}")
            body_lines.append("")
        full_text_txt = MASTER_TRADING_REPORT_DIRECTIVE.strip() + "\n\n" + ai_prompt + "\n".join(body_lines)
        instructions_for_json = MASTER_TRADING_REPORT_DIRECTIVE.strip() + "\n\n" + ai_prompt

        # Log signals for backtest feedback loop
        try:
            from backtest_db import log_signals_from_report
            log_signals_from_report(stocks_data, scan_type)
        except Exception:
            pass
        # Build and save JSON analysis package (for API + future use)
        # Build JSON-safe price history summary (no daily rows)
        ph_json = {}
        try:
            if price_history:
                from price_history import price_history_for_json
                ph_json = price_history_for_json(price_history)
        except Exception:
            pass
        analysis_package = self._build_analysis_package(stocks_data, scan_type, timestamp_display, watchlist_matches, config=config, instructions=instructions_for_json, market_breadth=market_breadth, market_intel=market_intel, price_history=ph_json)
        filepath_json = self.save_dir / f"{base_name}.json"
        try:
            with open(filepath_json, 'w', encoding='utf-8') as f:
                json.dump(analysis_package, f, indent=2)
            progress(f"JSON saved: {filepath_json}")
        except Exception:
            pass

        # Append slim record to long-term scan history (scan_history.json)
        try:
            history_path = self.save_dir / "scan_history.json"
            # Slim record: no instructions blob, no daily price rows
            slim_stocks = []
            for s in analysis_package.get("stocks", []):
                slim = {k: s[k] for k in ("ticker", "score", "price", "change", "sector",
                                           "rsi", "sma200_status", "rel_volume", "recom",
                                           "on_watchlist") if k in s}
                if s.get("leveraged_play"):
                    slim["leveraged_play"] = s["leveraged_play"]
                if s.get("smart_money"):
                    slim["smart_money"] = s["smart_money"]
                slim_stocks.append(slim)
            history_entry = {
                "scan_type": scan_type,
                "timestamp": timestamp_display,
                "stocks": slim_stocks,
            }
            if analysis_package.get("market_breadth"):
                history_entry["market_breadth"] = analysis_package["market_breadth"]
            if analysis_package.get("price_history_30d"):
                history_entry["price_history_30d"] = analysis_package["price_history_30d"]
            # Load existing history, append, save
            history = []
            if history_path.exists():
                try:
                    with open(history_path, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                    if not isinstance(history, list):
                        history = [history]
                except Exception:
                    history = []
            history.append(history_entry)
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import inch

            c = canvas.Canvas(str(filepath_pdf), pagesize=letter)
            width, height = letter
            margin = inch
            x, y = margin, height - margin
            c.setFont("Helvetica", 9)
            line_height = 11
            max_width_ch = 100

            # 0) Date/time stamp on first page
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x, y, f"Report generated: {timestamp_display}")
            y -= line_height * 1.5
            c.setFont("Helvetica", 9)

            # 0b) Master Trading Report Directive (for any AI that receives this PDF)
            for line in MASTER_TRADING_REPORT_DIRECTIVE.strip().replace("\r", "").split("\n"):
                if y < margin + line_height:
                    c.showPage()
                    c.setFont("Helvetica", 9)
                    y = height - margin
                draw_line = line[:max_width_ch] if len(line) > max_width_ch else line
                c.drawString(x, y, draw_line)
                y -= line_height
            y -= line_height

            # 1) Scan-specific AI prompt and watchlist
            for line in ai_prompt.replace("\r", "").split("\n"):
                if y < margin + line_height:
                    c.showPage()
                    c.setFont("Helvetica", 9)
                    y = height - margin
                draw_line = line[:max_width_ch] if len(line) > max_width_ch else line
                c.drawString(x, y, draw_line)
                y -= line_height

            # 2) Market breadth (if present)
            if market_breadth and "error" not in market_breadth:
                regime = market_breadth.get("market_regime", "N/A")
                sma50 = market_breadth.get("sp500_above_sma50_pct") if market_breadth.get("sp500_above_sma50_pct") is not None else "N/A"
                sma200 = market_breadth.get("sp500_above_sma200_pct") if market_breadth.get("sp500_above_sma200_pct") is not None else "N/A"
                ad = market_breadth.get("advance_decline")
                rsi = market_breadth.get("avg_rsi_sp500")
                breadth_line = f"Market breadth: {regime} | Above SMA50: {sma50}% | Above SMA200: {sma200}% | A/D: {ad} | Avg RSI: {rsi}"
                if y < margin + line_height:
                    c.showPage()
                    c.setFont("Helvetica", 9)
                    y = height - margin
                draw_line = breadth_line[:max_width_ch] if len(breadth_line) > max_width_ch else breadth_line
                c.drawString(x, y, draw_line)
                y -= line_height * 2
            # 3) Per-ticker technicals
            for s in stocks_data:
                ticker = s['ticker']
                score = s.get('score', 0)
                on_watchlist = s.get('on_watchlist', False)
                y -= line_height
                if y < margin + line_height:
                    c.showPage()
                    c.setFont("Helvetica", 9)
                    y = height - margin
                c.setFont("Helvetica-Bold", 11)
                header = f"——— {ticker} ———"
                if on_watchlist:
                    header += "  ★ WATCHLIST"
                c.drawString(x, y, header[:max_width_ch] if len(header) > max_width_ch else header)
                y -= line_height
                c.setFont("Helvetica", 9)
                tech_lines = [
                    f"Score {s['score']}  | Price ${s.get('price','N/A')}  | Change {s.get('change','N/A')}  | RSI {s.get('rsi','N/A')}  | Target ${s.get('target','N/A')}  | P/E {s.get('pe','N/A')}  | RelVol {s.get('rel_volume','N/A')}x",
                ]
                rc = s.get("risk_checks") or _default_risk_checks()
                if rc.get("earnings_safe") is False and rc.get("days_until_earnings") is not None:
                    tech_lines.append(f"EARNINGS IN {rc.get('days_until_earnings')} DAYS - avoid for swing")
                elif rc.get("earnings_date") or rc.get("earnings_safe") is True:
                    tech_lines.append("Earnings safe (>5 days out)" if rc.get("earnings_safe") else "Earnings: no date")
                if rc.get("ex_div_safe") is False and rc.get("ex_div_date"):
                    tech_lines.append(f"Ex-div {rc.get('ex_div_date')} - price drop expected")
                if rc.get("volume_unusual") and rc.get("relative_volume") is not None:
                    tech_lines.append(f"RelVol {rc.get('relative_volume')}x (unusual)")
                if any(s.get(k) for k in ('Owner', 'Transaction', 'Date', 'Value')):
                    tech_lines.append(f"Insider: {s.get('Owner','')} | {s.get('Relationship','')} | {s.get('Date','')} | {s.get('Transaction','')} | Cost {s.get('Cost','')} | Shares {s.get('Shares','')} | Value {s.get('Value','')}")
                    if s.get("insider_context") not in (None, ""):
                        tech_lines.append(f"Insider context: {s.get('insider_context', 'Unknown')} (from SEC Form 4)")
                if score >= LEVERAGED_MIN_SCORE and ticker in leveraged_mapping:
                    lev = leveraged_mapping[ticker]
                    tech_lines.append(f"Leveraged play: {lev} (use in place of {ticker} for leveraged exposure)")
                    tech_lines.append("  Leveraged ETFs are high-risk; not for long-term buy-and-hold (volatility decay).")
                tech_lines.extend([
                    f"Company: {s.get('company', ticker)}  | Sector: {s.get('sector','N/A')}",
                    f"SMA50: {s.get('sma50','N/A')}  | SMA200: {s.get('sma200','N/A')}  | SMA200 status: {s.get('sma200_status','N/A')}  | Recom: {s.get('recom','N/A')}",
                ])
                ta_dict = s.get('ta') or {}
                if ta_dict:
                    from ta_engine import format_ta_for_report
                    tech_lines.append(format_ta_for_report(ta_dict))
                if s.get("sentiment_label") is not None or s.get("sentiment_score") is not None:
                    sent_line = f"Sentiment: {s.get('sentiment_label', 'N/A')} (score {s.get('sentiment_score', 'N/A')})"
                    if s.get("earnings_in_topics"):
                        sent_line += " | Earnings in recent news"
                    tech_lines.append(sent_line)
                news_list = s.get('news') or []
                if news_list:
                    tech_lines.append("Headlines:")
                    for i, item in enumerate(news_list[:5]):
                        if isinstance(item, (list, tuple)) and len(item) > 1:
                            head = item[1]
                        elif isinstance(item, dict):
                            head = item.get('title') or item.get('headline') or str(item)
                        else:
                            head = str(item)
                        tech_lines.append(f"  {i+1}. {str(head).strip()}")
                tech_lines.append("")
                for line in tech_lines:
                    if y < margin + line_height:
                        c.showPage()
                        c.setFont("Helvetica", 9)
                        y = height - margin
                    draw_line = line[:max_width_ch] if len(line) > max_width_ch else line
                    c.drawString(x, y, draw_line)
                    y -= line_height
                y -= line_height

            # Footer: attribution and GitHub link
            y -= line_height * 2
            if y < margin + line_height * 3:
                c.showPage()
                c.setFont("Helvetica", 9)
                y = height - margin
            c.setFont("Helvetica-Oblique", 8)
            footer_line_1 = "This report was generated by ClearBlueSky Stock Scanner."
            footer_line_2 = "GitHub: https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner/releases"
            c.drawString(x, y, footer_line_1)
            y -= line_height
            c.drawString(x, y, footer_line_2)

            c.save()
            progress(f"PDF saved: {filepath_pdf}")
            return str(filepath_pdf), full_text_txt, analysis_package
        except ImportError:
            with open(filepath_txt, 'w', encoding='utf-8') as f:
                f.write(full_text_txt)
            progress(f"Report saved as TXT (install reportlab for PDF): {filepath_txt}")
            return str(filepath_txt), full_text_txt, analysis_package
        except Exception as e:
            with open(filepath_txt, 'w', encoding='utf-8') as f:
                f.write(full_text_txt)
            progress(f"PDF failed, saved as TXT: {filepath_txt}")
            return str(filepath_txt), full_text_txt, analysis_package

# Backward compatibility: app may still import HTMLReportGenerator
HTMLReportGenerator = ReportGenerator


def generate_report(ticker, scan_type="Analysis", score=None):
    """Quick single-ticker PDF report. Returns path."""
    gen = ReportGenerator()
    results = [{'ticker': ticker, 'score': score or 75}]
    path, _, _ = gen.generate_combined_report_pdf(results, scan_type, min_score=0)
    return path


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        gen = ReportGenerator()
        results = [{'ticker': t, 'score': 80} for t in sys.argv[1:]]
        path, _, _ = gen.generate_combined_report_pdf(results, "Test", min_score=0)
        print(f"Report: {path}")
