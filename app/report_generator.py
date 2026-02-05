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

# Master directive for any AI that receives this PDF (included in every report)
MASTER_TRADING_REPORT_DIRECTIVE = r"""
═══════════════════════════════════════════════════════════════════════════════
INSTRUCTIONS FOR AI: Follow this directive when analyzing this report.
═══════════════════════════════════════════════════════════════════════════════

To fulfill your role as a lead stock analyst at a major investment bank, you must
ensure your data requests are exhaustive, technical, and grounded in proven market
mechanics. Based on the methodologies of Farley, Bassal, Murphy, and other experts,
the following is the comprehensive framework you must use.

THE MASTER TRADING REPORT DIRECTIVE

Role and Objective:
Act as my Senior Quantitative Research Assistant. I am a lead analyst managing a
'Buy & Hold Trend Following' and Swing Trading portfolio. Your objective is to
produce a daily, multi-page analytical report for the watchlist in this document.
You must filter out market noise and provide only high-probability data grounded
in Pattern Cycle analysis. For each ticker, you will provide a 'Road Map' of
convergence zones where time, price, and trend align.

--- Section I: Technical Landscape & 3D Charting ---

Charts: For every ticker, use Yahoo Finance for chart analysis. Open the chart for each
symbol (e.g. https://finance.yahoo.com/quote/AAPL/chart or search "Yahoo Finance [TICKER] chart").
Apply the framework below to those live charts.

For every ticker, analyze three distinct time frames (the 3D Charting approach):

1. Primary Screen (Holding Period): Daily or 60-minute bars.
2. Higher Magnitude (Landscape): Weekly or monthly to identify major S/R.
3. Lower Magnitude (Execution): 5-minute or 1-minute to pinpoint entry.

Required Indicator Data:
- Moving Average Ribbons (MARs): 20, 50, and 200-period SMAs/EMAs. Note if MARs are
  spreading (accelerating momentum) or inverting (trend change).
- Bollinger Bands (BB): 20-bar/2-std dev daily, 13-bar/2-std dev intraday. Report
  if price is 'climbing the ladder' (bullish) or 'slippery slope' (bearish).
- Fibonacci Retracements: 38%, 50%, 62% from the most recent major trend leg.
- Oscillators: MACD Histogram slopes and RSI; identify bullish/bearish divergences.

--- Section II: Pattern Recognition & The 7-Bells ---

Scan for and report:
- Reversal Patterns: Head and Shoulders (neckline status), Double/Triple Tops and
  Bottoms, V-reversals (Spikes).
- Continuation Patterns: Bull/Bear Flags, Pennants, Symmetrical Triangles.
- The 7-Bells: Dip Trip (pullbacks to S/R in strong trends), Coiled Spring (NR7),
  Hole-in-the-Wall (gaps after strong moves), 3rd Watch (breakouts through triple
  tops, e.g. Cup and Handle).

--- Section III: Market Mechanics & Sentiment ---

- Volume Analysis: Power Spikes vs Breakout Volume. Use OBV to confirm volume
  leading price.
- NYSE TICK: Current TICK readings for intraday buying/selling pulses.
- Cross-Market: S&P 500 trend, Bond yields, Sector rotation (e.g. Tech vs Basic).

--- Section IV: Execution and Risk Management ---

For every identified trade include:
1. Execution Target (ET): Exact price to pull the trigger.
2. Failure Target (FT): Stop Loss price that proves the setup wrong.
3. Profit Target (PT): Next major S/R barrier.
4. Reward:Risk Ratio: Must be at least 3:1.

--- Standard Output Format per Ticker ---

[TICKER] - [CURRENT PRICE] - [CHANGE %]
- Latest News: Summary of catalysts and macro events.
- Trend Polarity: Bull or Bear based on 200-day MA.
- Key S/R Levels: Horizontal highs/lows, Fib levels, MARs.
- Active Pattern: e.g. "Bull Flag forming on 60-min, resting on 50-day EMA."
- Road Map: Entry $ | Stop Loss $ | Target $
- Analyst Note: Detached, analytical guidance (Pattern Cycle stage).

--- Final Instructions ---

Use professional, calm, and disciplined language. Prioritize accuracy over
speed. If a setup looks too good to be true, evaluate it for Pattern Failure.
Generate this report daily after the closing bell to prepare for the next session.

═══════════════════════════════════════════════════════════════════════════════
END OF AI DIRECTIVE — Below is this scan's watchlist and data.
═══════════════════════════════════════════════════════════════════════════════
"""


class ReportGenerator:
    """Generate date/time-stamped PDF reports only."""

    def __init__(self, save_dir=None):
        if save_dir is None:
            save_dir = os.path.join(BASE_DIR, "reports")
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def _finviz_get_stock_with_retry(self, ticker, max_attempts=3):
        """Call finviz.get_stock with retries on failure (timeout, 429, etc.)."""
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

    def get_finviz_data(self, ticker):
        """Get stock data from Finviz (with retry on transient errors)."""
        data = {'ticker': ticker, 'price': 'N/A', 'change': 'N/A'}
        
        if not FINVIZ_AVAILABLE:
            return data
        
        stock = self._finviz_get_stock_with_retry(ticker)
        if stock:
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
                'sma50': stock.get('SMA50', 'N/A'),
                'sma200': stock.get('SMA200', 'N/A'),
                'perf_week': stock.get('Perf Week', 'N/A'),
                'perf_month': stock.get('Perf Month', 'N/A'),
                'perf_quarter': stock.get('Perf Quarter', 'N/A'),
                'rel_volume': stock.get('Rel Volume', 'N/A'),
                'recom': stock.get('Recom', 'N/A'),
            })
            # Get news (with one retry on failure)
            for _ in range(2):
                try:
                    news = finviz.get_news(ticker)
                    data['news'] = news[:5] if news else []
                    break
                except Exception as e:
                    if '429' in str(e).lower() or 'timeout' in str(e).lower():
                        time.sleep(2)
                        continue
                    data['news'] = []
                    break
        
            data['risk_checks'] = self._parse_risk_checks(stock)
        else:
            data['risk_checks'] = _default_risk_checks()
        return data

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

    def _build_analysis_package(self, stocks_data, scan_type, timestamp_display, watchlist_matches, config=None, instructions=None, market_breadth=None):
        """Build JSON-serializable analysis package for API and file save. instructions = full AI prompt; market_breadth = optional breadth dict from breadth.py."""
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
                "sma50": s.get("sma50", "N/A"),
                "sma200": s.get("sma200", "N/A"),
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
            }
            for k in ("Owner", "Relationship", "Date", "Transaction", "Cost", "Shares", "Value"):
                if s.get(k) not in (None, "", "N/A"):
                    row[k.lower()] = s.get(k)
            leveraged = self._load_leveraged_mapping()
            if s.get("score", 0) >= 60 and s.get("ticker") in leveraged:
                row["leveraged_play"] = leveraged[s["ticker"]]
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
        if instructions not in (None, ""):
            out["instructions"] = instructions.strip()
        return out

    def generate_combined_report_pdf(self, results, scan_type="Scan", min_score=60, progress_callback=None, watchlist_tickers=None, config=None, index=None):
        """Generate ONE PDF report. index='sp500' or 'russell2000' to include market breadth (full index fetch)."""
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
            data = self.get_finviz_data(ticker)
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
                    time.sleep(0.25)
                except Exception:
                    row["insider_10b5_1_plan"] = None
                    row["insider_context"] = "Unknown"
            else:
                row["insider_10b5_1_plan"] = None
                row["insider_context"] = None
            stocks_data.append(row)
            time.sleep(0.2)

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
            data_lines.append(line)

        market_breadth = None
        if index and index in ("sp500", "russell2000"):
            try:
                from breadth import fetch_full_index_for_breadth, calculate_market_breadth
                all_stocks = fetch_full_index_for_breadth(index, progress)
                if all_stocks:
                    market_breadth = calculate_market_breadth(all_stocks)
            except Exception:
                pass

        watchlist_line = f"\nWATCHLIST MATCHES (prioritize these): {', '.join(watchlist_matches)}\n" if watchlist_matches else ""
        breadth_line_prompt = ""
        if market_breadth and "error" not in market_breadth:
            regime = market_breadth.get("market_regime", "N/A")
            breadth_line_prompt = f"\nMarket breadth (position sizing): {regime} | Above SMA50: {market_breadth.get('sp500_above_sma50_pct')}% | A/D: {market_breadth.get('advance_decline')} | Avg RSI: {market_breadth.get('avg_rsi_sp500')}\n"
        ai_prompt = f"""You are a professional stock analyst. Analyze these {scan_type.lower()} scan candidates.{breadth_line_prompt}

IMPORTANT: For each stock:
1. Use the technical data (chart data and scanner data) in this report to assess setup
2. Search for recent news on each ticker to check for catalysts or red flags
3. Determine if any price movement is EMOTIONAL (buyable dip) or FUNDAMENTAL (avoid)

═══════════════════════════════════════════════════
STOCKS TO ANALYZE: {tickers_list}
{watchlist_line}═══════════════════════════════════════════════════

DATA SUMMARY:
{chr(10).join(data_lines)}

═══════════════════════════════════════════════════
FOR EACH STOCK, PROVIDE:
═══════════════════════════════════════════════════

1. YOUR SCORE (1-100):
   - 90-100: Elite setup, high conviction
   - 80-89: Excellent, strong setup
   - 70-79: Good, worth considering
   - 60-69: Decent, smaller position
   - Below 60: Skip

2. CHART ANALYSIS:
   - Trend direction
   - Key support level
   - Key resistance level
   - Any patterns visible

3. NEWS CHECK:
   - Search recent news for this ticker
   - Any catalysts (earnings, upgrades, contracts)?
   - Any red flags (downgrades, lawsuits, guidance cuts)?
   - Is the move EMOTIONAL (trade it) or FUNDAMENTAL (skip it)?

4. RECOMMENDATION: BUY / HOLD / PASS

5. IF BUY - ORDER SETTINGS:
   - Entry Price: $XX.XX (limit order price)
   - Position Size: X shares (for $2,000-5,000 position)
   - Stop Loss: $XX.XX (where to exit if wrong)
   - Target 1: $XX.XX (take 50% profit)
   - Target 2: $XX.XX (trail rest with stop)

6. ORDER TYPE RECOMMENDATION:
   - Use LIMIT order at $XX.XX, or
   - Use STOP-LIMIT if breaks above $XX.XX, or
   - Use TRAILING STOP of X% for profit protection

═══════════════════════════════════════════════════
FINAL SUMMARY:
═══════════════════════════════════════════════════

TOP 10 PICKS (ranked by your score):
For each pick give: Ticker, Your Score, Entry, Stop, Target, Why

AVOID LIST:
Which stocks to skip and why (news red flags, bad chart, etc.)

NEWS ALERTS:
Any breaking news or upcoming events (earnings dates, FDA decisions, etc.) that could affect these trades

MARKET CONTEXT:
Current market conditions affecting these trades

RISK MANAGEMENT:
- Best order type for current volatility
- Suggested trailing stop % for winners
- Max position size recommendation
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
            sma50 = market_breadth.get("sp500_above_sma50_pct")
            sma200 = market_breadth.get("sp500_above_sma200_pct")
            ad = market_breadth.get("advance_decline")
            rsi = market_breadth.get("avg_rsi_sp500")
            body_lines.append(f"Market breadth: {regime} | Above SMA50: {sma50}% | Above SMA200: {sma200}% | A/D: {ad} | Avg RSI: {rsi}")
            body_lines.append("")
        for s in stocks_data:
            ticker = s['ticker']
            score = s.get('score', 0)
            body_lines.append(f"——— {ticker} ———")
            body_lines.append(f"Score {s['score']}  | Price ${s.get('price','N/A')}  | Change {s.get('change','N/A')}  | RSI {s.get('rsi','N/A')}  | Target ${s.get('target','N/A')}  | P/E {s.get('pe','N/A')}  | RelVol {s.get('rel_volume','N/A')}x")
            rc = s.get("risk_checks") or _default_risk_checks()
            if rc.get("earnings_safe") is False and rc.get("days_until_earnings") is not None:
                body_lines.append(f"EARNINGS IN {rc.get('days_until_earnings')} DAYS - avoid for swing")
            elif rc.get("earnings_date") and rc.get("earnings_safe") is True:
                body_lines.append("Earnings safe (>5 days out)")
            if rc.get("ex_div_safe") is False and rc.get("ex_div_date"):
                body_lines.append(f"Ex-div {rc.get('ex_div_date')} - price drop expected")
            if rc.get("volume_unusual") and rc.get("relative_volume") is not None:
                body_lines.append(f"RelVol {rc.get('relative_volume')}x (unusual)")
            if any(s.get(k) for k in ('Owner', 'Transaction', 'Date', 'Value')):
                body_lines.append(f"Insider: {s.get('Owner','')} | {s.get('Relationship','')} | {s.get('Date','')} | {s.get('Transaction','')} | Cost {s.get('Cost','')} | Shares {s.get('Shares','')} | Value {s.get('Value','')}")
                if s.get("insider_context") not in (None, ""):
                    body_lines.append(f"Insider context: {s.get('insider_context', 'Unknown')} (from SEC Form 4)")
            if score >= LEVERAGED_MIN_SCORE and ticker in leveraged_mapping:
                lev = leveraged_mapping[ticker]
                body_lines.append(f"Leveraged play: {lev} (use in place of {ticker} for leveraged exposure)")
                body_lines.append("  Leveraged ETFs are high-risk; not suitable for long-term buy-and-hold (volatility decay).")
            body_lines.append(f"Company: {s.get('company', ticker)}  | Sector: {s.get('sector','N/A')}")
            body_lines.append(f"SMA50: {s.get('sma50','N/A')}  | SMA200: {s.get('sma200','N/A')}  | Recom: {s.get('recom','N/A')}")
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
        analysis_package = self._build_analysis_package(stocks_data, scan_type, timestamp_display, watchlist_matches, config=config, instructions=instructions_for_json, market_breadth=market_breadth)
        filepath_json = self.save_dir / f"{base_name}.json"
        try:
            with open(filepath_json, 'w', encoding='utf-8') as f:
                json.dump(analysis_package, f, indent=2)
            progress(f"JSON saved: {filepath_json}")
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
                sma50 = market_breadth.get("sp500_above_sma50_pct")
                sma200 = market_breadth.get("sp500_above_sma200_pct")
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
                    f"SMA50: {s.get('sma50','N/A')}  | SMA200: {s.get('sma200','N/A')}  | Recom: {s.get('recom','N/A')}",
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
