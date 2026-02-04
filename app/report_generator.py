"""
ClearBlueSky PDF Report Generator
Generates date/time-stamped PDF reports for uploads. No HTML.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
import json

# Get the directory where this script is located (portable support)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    import finviz
    FINVIZ_AVAILABLE = True
except ImportError:
    FINVIZ_AVAILABLE = False

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
        
        return data

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

    def generate_combined_report_pdf(self, results, scan_type="Scan", min_score=60, progress_callback=None, watchlist_tickers=None, config=None):
        """Generate ONE PDF report."""
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
            return None

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
            stocks_data.append(row)
            time.sleep(0.2)

        tickers_list = ", ".join([s['ticker'] for s in stocks_data])
        watchlist_matches = [s['ticker'] for s in stocks_data if s.get('on_watchlist')]
        data_lines = []
        for s in stocks_data:
            line = f"- {s['ticker']}: Scanner Score {s['score']}, Price ${s.get('price','N/A')}, Today {s.get('change','N/A')}, RSI {s.get('rsi','N/A')}, Target ${s.get('target','N/A')}, P/E {s.get('pe','N/A')}, RelVol {s.get('rel_volume','N/A')}x"
            data_lines.append(line)

        watchlist_line = f"\nWATCHLIST MATCHES (prioritize these): {', '.join(watchlist_matches)}\n" if watchlist_matches else ""
        ai_prompt = f"""You are a professional stock analyst. Analyze these {scan_type.lower()} scan candidates.

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
        for s in stocks_data:
            ticker = s['ticker']
            score = s.get('score', 0)
            body_lines.append(f"——— {ticker} ———")
            body_lines.append(f"Score {s['score']}  | Price ${s.get('price','N/A')}  | Change {s.get('change','N/A')}  | RSI {s.get('rsi','N/A')}  | Target ${s.get('target','N/A')}  | P/E {s.get('pe','N/A')}  | RelVol {s.get('rel_volume','N/A')}x")
            if any(s.get(k) for k in ('Owner', 'Transaction', 'Date', 'Value')):
                body_lines.append(f"Insider: {s.get('Owner','')} | {s.get('Relationship','')} | {s.get('Date','')} | {s.get('Transaction','')} | Cost {s.get('Cost','')} | Shares {s.get('Shares','')} | Value {s.get('Value','')}")
            if score >= LEVERAGED_MIN_SCORE and ticker in leveraged_mapping:
                lev = leveraged_mapping[ticker]
                body_lines.append(f"Leveraged play: {lev} (use in place of {ticker} for leveraged exposure)")
                body_lines.append("  Leveraged ETFs are high-risk; not suitable for long-term buy-and-hold (volatility decay).")
            body_lines.append(f"Company: {s.get('company', ticker)}  | Sector: {s.get('sector','N/A')}")
            body_lines.append(f"SMA50: {s.get('sma50','N/A')}  | SMA200: {s.get('sma200','N/A')}  | Recom: {s.get('recom','N/A')}")
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

            # 2) Per-ticker technicals
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
                if any(s.get(k) for k in ('Owner', 'Transaction', 'Date', 'Value')):
                    tech_lines.append(f"Insider: {s.get('Owner','')} | {s.get('Relationship','')} | {s.get('Date','')} | {s.get('Transaction','')} | Cost {s.get('Cost','')} | Shares {s.get('Shares','')} | Value {s.get('Value','')}")
                if score >= LEVERAGED_MIN_SCORE and ticker in leveraged_mapping:
                    lev = leveraged_mapping[ticker]
                    tech_lines.append(f"Leveraged play: {lev} (use in place of {ticker} for leveraged exposure)")
                    tech_lines.append("  Leveraged ETFs are high-risk; not for long-term buy-and-hold (volatility decay).")
                tech_lines.extend([
                    f"Company: {s.get('company', ticker)}  | Sector: {s.get('sector','N/A')}",
                    f"SMA50: {s.get('sma50','N/A')}  | SMA200: {s.get('sma200','N/A')}  | Recom: {s.get('recom','N/A')}",
                ])
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
            return str(filepath_pdf)
        except ImportError:
            with open(filepath_txt, 'w', encoding='utf-8') as f:
                f.write(full_text_txt)
            progress(f"Report saved as TXT (install reportlab for PDF): {filepath_txt}")
            return str(filepath_txt)
        except Exception as e:
            with open(filepath_txt, 'w', encoding='utf-8') as f:
                f.write(full_text_txt)
            progress(f"PDF failed, saved as TXT: {filepath_txt}")
            return str(filepath_txt)

# Backward compatibility: app may still import HTMLReportGenerator
HTMLReportGenerator = ReportGenerator


def generate_report(ticker, scan_type="Analysis", score=None):
    """Quick single-ticker PDF report."""
    gen = ReportGenerator()
    results = [{'ticker': ticker, 'score': score or 75}]
    return gen.generate_combined_report_pdf(results, scan_type, min_score=0)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        gen = ReportGenerator()
        results = [{'ticker': t, 'score': 80} for t in sys.argv[1:]]
        path = gen.generate_combined_report_pdf(results, "Test", min_score=0)
        print(f"Report: {path}")
