"""
ClearBlueSky HTML Report Generator
Creates interactive HTML reports with Copy to AI buttons
Made with Claude AI
"""

import os
import sys
import requests
import time
from datetime import datetime
from pathlib import Path
import json
import base64

# Get the directory where this script is located (portable support)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    import finviz
    FINVIZ_AVAILABLE = True
except ImportError:
    FINVIZ_AVAILABLE = False

class HTMLReportGenerator:
    """Generate interactive HTML reports with AI copy buttons"""
    
    def __init__(self, save_dir=None):
        if save_dir is None:
            save_dir = os.path.join(BASE_DIR, "reports")
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finviz.com/',
        }
        
        # Load config for custom AI URL
        self.config = {}
        try:
            config_path = Path(os.path.join(BASE_DIR, "user_config.json"))
            if config_path.exists():
                self.config = json.load(open(config_path))
        except:
            pass
    
    def get_chart_url(self, ticker, timeframe='d'):
        """Get Finviz chart URL"""
        return f"https://finviz.com/chart.ashx?t={ticker}&ty=c&ta=1&p={timeframe}&s=l"
    
    def get_finviz_data(self, ticker):
        """Get stock data from Finviz"""
        data = {'ticker': ticker, 'price': 'N/A', 'change': 'N/A'}
        
        if not FINVIZ_AVAILABLE:
            return data
        
        try:
            stock = finviz.get_stock(ticker)
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
            
            # Get news
            try:
                news = finviz.get_news(ticker)
                if news:
                    data['news'] = news[:5]
                    print(f"  Got {len(news)} news items for {ticker}")
                else:
                    data['news'] = []
            except Exception as e:
                print(f"  News error for {ticker}: {e}")
                data['news'] = []
                
        except Exception as e:
            print(f"Error getting data for {ticker}: {e}")
        
        return data
    
    def generate_combined_report(self, results, scan_type="Scan", min_score=60, progress_callback=None):
        """Generate ONE HTML report with all qualifying stocks"""
        
        def progress(msg):
            print(msg)
            if progress_callback:
                progress_callback(msg)
        
        # Filter and sort by score
        qualifying = []
        for r in results:
            ticker = r.get('Ticker', r.get('ticker', ''))
            score = r.get('SCORE', r.get('Score', r.get('score', 0)))
            try:
                score = int(float(score)) if score else 0
            except:
                score = 0
            
            if ticker and score >= min_score:
                qualifying.append({'ticker': ticker, 'score': score, 'data': r})
        
        if not qualifying:
            progress(f"No stocks scored above {min_score}")
            return None
        
        qualifying.sort(key=lambda x: x['score'], reverse=True)
        qualifying = qualifying[:15]  # Top 15
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"{scan_type}_Scan_{timestamp}.html"
        filepath = self.save_dir / filename
        
        progress(f"Creating report with {len(qualifying)} stocks...")
        
        # Build stock data
        stocks_html = []
        stocks_data = []
        
        for i, q in enumerate(qualifying, 1):
            ticker = q['ticker']
            score = q['score']
            
            progress(f"Processing {i}/{len(qualifying)}: {ticker}...")
            
            data = self.get_finviz_data(ticker)
            stocks_data.append({'ticker': ticker, 'score': score, **data})
            
            # Build HTML for this stock
            news_html = ""
            if data.get('news') and len(data['news']) > 0:
                news_items = ""
                for n in data['news'][:3]:
                    # News is tuple: (date, title, url, source)
                    if isinstance(n, (list, tuple)) and len(n) >= 2:
                        title = str(n[1])[:80]  # Index 1 is the title
                        url = n[2] if len(n) > 2 else "#"
                        source = n[3] if len(n) > 3 else ""
                        news_items += f'<li><a href="{url}" target="_blank" style="color:#2563eb; text-decoration:none;">{title}</a> <span style="color:#888; font-size:0.85em;">({source})</span></li>'
                    else:
                        title = str(n)[:80]
                        news_items += f"<li>{title}</li>"
                if news_items:
                    news_html = f"<div class='news'><b>📰 Recent News:</b><ul>{news_items}</ul></div>"
            
            stock_html = f"""
            <div class="stock-card" id="stock-{ticker}">
                <div class="stock-header">
                    <div class="stock-rank">#{i}</div>
                    <div class="stock-info">
                        <h2>{ticker}</h2>
                        <p class="company">{data.get('company', ticker)} | {data.get('sector', 'N/A')}</p>
                    </div>
                    <div class="stock-score score-{self._score_class(score)}">
                        <span class="score-num">{score}</span>
                        <span class="score-label">{self._score_label(score)}</span>
                    </div>
                </div>
                
                <div class="stock-metrics">
                    <div class="metric"><span>Price</span><b>{data.get('price', 'N/A')}</b></div>
                    <div class="metric"><span>Change</span><b>{data.get('change', 'N/A')}</b></div>
                    <div class="metric"><span>Volume</span><b>{data.get('rel_volume', 'N/A')}x</b></div>
                    <div class="metric"><span>RSI</span><b>{data.get('rsi', 'N/A')}</b></div>
                    <div class="metric"><span>Target</span><b>${data.get('target', 'N/A')}</b></div>
                    <div class="metric"><span>P/E</span><b>{data.get('pe', 'N/A')}</b></div>
                </div>
                
                <div class="chart-container">
                    <img src="{self.get_chart_url(ticker, 'd')}" alt="{ticker} Daily Chart" class="chart">
                </div>
                
                {news_html}
            </div>
            """
            stocks_html.append(stock_html)
            time.sleep(0.2)
        
        # Build AI prompt with comprehensive analysis request
        tickers_list = ", ".join([s['ticker'] for s in stocks_data])
        
        # Build detailed data summary
        data_lines = []
        for s in stocks_data:
            line = f"- {s['ticker']}: Scanner Score {s['score']}, Price ${s.get('price','N/A')}, Today {s.get('change','N/A')}, RSI {s.get('rsi','N/A')}, Target ${s.get('target','N/A')}, P/E {s.get('pe','N/A')}, RelVol {s.get('rel_volume','N/A')}x"
            data_lines.append(line)
        
        ai_prompt = f"""You are a professional stock analyst. Analyze these {scan_type.lower()} scan candidates.

IMPORTANT: For each stock:
1. Look at the daily chart image provided in this report to assess technicals
2. Search for recent news on each ticker to check for catalysts or red flags
3. Determine if any price movement is EMOTIONAL (buyable dip) or FUNDAMENTAL (avoid)

═══════════════════════════════════════════════════
STOCKS TO ANALYZE: {tickers_list}
═══════════════════════════════════════════════════

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

TOP 3 PICKS (ranked by your score):
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
        
        # Generate full HTML
        html = self._generate_html(scan_type, qualifying, stocks_html, ai_prompt, timestamp)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        progress(f"Report saved: {filepath}")
        return str(filepath)
    
    def _score_class(self, score):
        if score >= 80: return "high"
        if score >= 60: return "mid"
        return "low"
    
    def _score_label(self, score):
        if score >= 90: return "ELITE"
        if score >= 80: return "EXCELLENT"
        if score >= 70: return "STRONG"
        if score >= 60: return "DECENT"
        return "WEAK"
    
    def _generate_html(self, scan_type, qualifying, stocks_html, ai_prompt, timestamp):
        """Generate complete HTML document"""
        
        summary_rows = "".join([
            f"<tr><td>{i}</td><td><b>{q['ticker']}</b></td><td>{q['score']}</td><td>{self._score_label(q['score'])}</td></tr>"
            for i, q in enumerate(qualifying, 1)
        ])
        
        # Escape prompt for JavaScript
        ai_prompt_escaped = ai_prompt.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{scan_type} Scan Results - {timestamp}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #333; }}
        
        .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 30px; text-align: center; position: sticky; top: 0; z-index: 100; }}
        .header h1 {{ font-size: 2em; margin-bottom: 5px; }}
        .header p {{ opacity: 0.8; }}
        
        .ai-buttons {{ display: flex; gap: 10px; justify-content: center; margin-top: 20px; flex-wrap: wrap; }}
        .ai-btn {{ padding: 12px 24px; border: none; border-radius: 25px; font-size: 14px; font-weight: bold; cursor: pointer; transition: all 0.3s; display: flex; align-items: center; gap: 8px; }}
        .ai-btn:hover {{ transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0,0,0,0.3); }}
        .ai-btn.claude {{ background: linear-gradient(135deg, #D97706 0%, #F59E0B 100%); color: white; }}
        .ai-btn.gemini {{ background: linear-gradient(135deg, #4285F4 0%, #34A853 100%); color: white; }}
        .ai-btn.chatgpt {{ background: linear-gradient(135deg, #10A37F 0%, #1A7F64 100%); color: white; }}
        .ai-btn.copy {{ background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%); color: white; }}
        
        .copied {{ position: fixed; top: 20px; right: 20px; background: #10B981; color: white; padding: 15px 25px; border-radius: 10px; font-weight: bold; display: none; z-index: 1000; animation: fadeIn 0.3s; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        
        .summary {{ background: white; border-radius: 15px; padding: 25px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .summary h2 {{ margin-bottom: 15px; color: #1a1a2e; }}
        .summary table {{ width: 100%; border-collapse: collapse; }}
        .summary th, .summary td {{ padding: 10px; text-align: left; border-bottom: 1px solid #eee; }}
        .summary th {{ background: #f8f9fa; color: #666; font-weight: 600; }}
        .summary tr:hover {{ background: #f8f9fa; }}
        
        .stock-card {{ background: white; border-radius: 15px; padding: 25px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .stock-header {{ display: flex; align-items: center; gap: 20px; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #f0f0f0; }}
        .stock-rank {{ width: 50px; height: 50px; background: #1a1a2e; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2em; font-weight: bold; }}
        .stock-info {{ flex: 1; }}
        .stock-info h2 {{ font-size: 1.8em; color: #1a1a2e; }}
        .stock-info .company {{ color: #666; margin-top: 5px; }}
        
        .stock-score {{ text-align: center; padding: 15px 25px; border-radius: 15px; }}
        .stock-score.score-high {{ background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; }}
        .stock-score.score-mid {{ background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: white; }}
        .stock-score.score-low {{ background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%); color: white; }}
        .score-num {{ font-size: 2em; font-weight: bold; display: block; }}
        .score-label {{ font-size: 0.85em; opacity: 0.9; }}
        
        .stock-metrics {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 15px; margin-bottom: 20px; }}
        .metric {{ background: #f8f9fa; padding: 15px; border-radius: 10px; text-align: center; }}
        .metric span {{ display: block; color: #666; font-size: 0.85em; margin-bottom: 5px; }}
        .metric b {{ font-size: 1.1em; color: #1a1a2e; }}
        
        .chart-container {{ margin: 20px 0; text-align: center; }}
        .chart {{ max-width: 100%; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        
        .news {{ background: #f8f9fa; padding: 15px; border-radius: 10px; margin-top: 15px; }}
        .news ul {{ margin-left: 20px; margin-top: 10px; }}
        .news li {{ margin-bottom: 5px; color: #555; }}
        
        .footer {{ text-align: center; padding: 30px; color: #666; }}
        
        @media (max-width: 768px) {{
            .stock-metrics {{ grid-template-columns: repeat(3, 1fr); }}
            .ai-buttons {{ flex-direction: column; align-items: center; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 {scan_type} Scan Results</h1>
        <p>{datetime.now().strftime('%B %d, %Y at %I:%M %p')} | {len(qualifying)} Qualifying Stocks</p>
        
        <div style="background: rgba(255,255,255,0.15); border-radius: 10px; padding: 15px; margin: 15px auto; max-width: 600px;">
            <p style="margin: 0 0 10px 0; font-size: 14px;">📝 <b>How to use:</b></p>
            <p style="margin: 0; font-size: 13px; opacity: 0.9;">1. Click "Copy AI Prompt" below</p>
            <p style="margin: 0; font-size: 13px; opacity: 0.9;">2. Click an AI button (Claude, Gemini, etc.)</p>
            <p style="margin: 0; font-size: 13px; opacity: 0.9;">3. Press Ctrl+V (or Cmd+V) to paste the prompt</p>
            <p style="margin: 0; font-size: 13px; opacity: 0.9;">4. Get BUY/SELL/HOLD recommendations!</p>
        </div>
        
        <div class="ai-buttons">
            <button class="ai-btn copy" onclick="copyPrompt()">📋 Copy AI Prompt</button>
            <button class="ai-btn claude" onclick="openAI('claude')">🤖 Claude</button>
            <button class="ai-btn gemini" onclick="openAI('gemini')">✨ Gemini</button>
            <button class="ai-btn chatgpt" onclick="openAI('chatgpt')">💬 ChatGPT</button>
            <button class="ai-btn qwen" onclick="openAI('qwen')" style="background: linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%);">🚀 Qwen3 (Free)</button>
            <button class="ai-btn other" onclick="openAI('other')" style="background: linear-gradient(135deg, #6B7280 0%, #4B5563 100%);">🔗 Other</button>
        </div>
        
        <p style="font-size: 12px; opacity: 0.7; margin-top: 10px;">💡 Qwen3: Select model "Qwen3-VL-235B-A22B" - Free super AI with vision (can read charts!)</p>
    </div>
    
    <div class="copied" id="copied">✓ Prompt Copied to Clipboard! Now paste (Ctrl+V) in your AI chat.</div>
    
    <div class="container">
        <div class="summary">
            <h2>📈 Summary</h2>
            <table>
                <thead>
                    <tr><th>#</th><th>Ticker</th><th>Score</th><th>Rating</th></tr>
                </thead>
                <tbody>
                    {summary_rows}
                </tbody>
            </table>
        </div>
        
        {"".join(stocks_html)}
    </div>
    
    <div class="footer">
        <p>ClearBlueSky Stock Scanner & AI Research Tool | Made with Claude</p>
        <p style="font-size: 12px; margin-top: 5px;">Contact: Discord ID 340935763405570048 | For educational purposes only</p>
    </div>
    
    <script>
        const aiPrompt = `{ai_prompt_escaped}`;
        
        function copyPrompt() {{
            navigator.clipboard.writeText(aiPrompt).then(() => {{
                const copied = document.getElementById('copied');
                copied.style.display = 'block';
                copied.style.background = '#10B981';
                copied.textContent = '✓ Prompt Copied to Clipboard! Now paste (Ctrl+V) in your AI chat.';
                setTimeout(() => {{ copied.style.display = 'none'; }}, 4000);
            }}).catch(err => {{
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = aiPrompt;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                const copied = document.getElementById('copied');
                copied.style.display = 'block';
                setTimeout(() => {{ copied.style.display = 'none'; }}, 4000);
            }});
        }}
        
        function openAI(service) {{
            const urls = {{
                'claude': 'https://claude.ai/new',
                'gemini': 'https://gemini.google.com/app',
                'chatgpt': 'https://chat.openai.com/',
                'qwen': 'https://chat.qwen.ai/c/guest',
                'other': '{self.config.get("other_ai_url", "https://claude.ai/new")}'
            }};
            window.open(urls[service], '_blank');
        }}
    </script>
</body>
</html>"""


# Keep backward compatibility
class TickerReportGenerator(HTMLReportGenerator):
    """Alias for backward compatibility"""
    pass


def generate_report(ticker, scan_type="Analysis", score=None):
    """Quick single ticker report"""
    gen = HTMLReportGenerator()
    results = [{'ticker': ticker, 'score': score or 75}]
    return gen.generate_combined_report(results, scan_type, min_score=0)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        gen = HTMLReportGenerator()
        results = [{{'ticker': t, 'score': 80}} for t in sys.argv[1:]]
        path = gen.generate_combined_report(results, "Test", min_score=0)
        print(f"Report: {{path}}")
