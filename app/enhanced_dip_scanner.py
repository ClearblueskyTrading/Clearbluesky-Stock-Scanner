# ============================================================
# TRADEBOT - Enhanced Dip Scanner
# ============================================================
# Uses news, analyst ratings, and price targets to filter
# EMOTIONAL dips (buy) from FUNDAMENTAL dips (avoid)

import time
from datetime import datetime
from typing import List, Dict, Optional
from finviz.screener import Screener
import finviz

from scan_settings import load_config
from finviz_safe import get_stock_safe

# News keywords that suggest EMOTIONAL dip (buyable)
EMOTIONAL_KEYWORDS = [
    'tariff', 'trump', 'tweet', 'rumor', 'fear', 'concern', 'worry',
    'selloff', 'rotation', 'sector', 'downgrade', 'analyst', 'rating',
    'market', 'broader', 'sentiment', 'profit taking', 'pullback',
    'consolidation', 'overbought', 'correction', 'volatility',
    'geopolitical', 'trade war', 'uncertainty', 'headline',
]

# News keywords that suggest FUNDAMENTAL dip (avoid)
FUNDAMENTAL_KEYWORDS = [
    'earnings miss', 'missed', 'revenue miss', 'guidance cut', 'lowered guidance',
    'warning', 'profit warning', 'sec investigation', 'fraud', 'lawsuit',
    'ceo resign', 'cfo resign', 'executive depart', 'accounting', 'restate',
    'bankruptcy', 'default', 'debt', 'layoff', 'restructur', 'recall',
    'fda reject', 'trial fail', 'discontinue', 'terminate', 'lose contract',
    'data breach', 'hack', 'cybersecurity incident',
]

# Analyst rating values (higher = better)
RATING_SCORES = {
    'strong buy': 5,
    'buy': 4,
    'outperform': 4,
    'overweight': 4,
    'hold': 3,
    'neutral': 3,
    'equal-weight': 3,
    'underperform': 2,
    'underweight': 2,
    'sell': 1,
    'strong sell': 0,
}


def get_sp500_dips(config: Dict, index: str = "sp500") -> List[Dict]:
    """
    Scan index for stocks down within configured range.
    index: 'sp500' or 'etfs'
    Returns raw list before filtering.
    """
    min_dip = float(config.get('dip_min_percent', 1.0))
    max_dip = float(config.get('dip_max_percent', 5.0))
    min_price = float(config.get('min_price', 5.0))
    max_price = float(config.get('max_price', 500.0))
    min_volume = int(float(config.get('min_avg_volume', 500000)))
    
    # Index filter (Finviz: idx_sp500, ind_exchangetradedfund for ETFs)
    if index == 'etfs':
        idx_filter = 'ind_exchangetradedfund'
    else:
        idx_filter = 'idx_sp500'
    
    filters = [
        idx_filter,
        f'sh_price_o{int(min_price)}',
        f'sh_price_u{int(max_price)}',
        f'sh_avgvol_o{int(min_volume/1000)}',  # Finviz uses K
        'ta_change_d',  # Down today
    ]
    
    try:
        screener = Screener(filters=filters, order='change')
        results = []
        
        for stock in screener:
            try:
                change_str = stock.get('Change', '0%').replace('%', '')
                change = float(change_str)
                
                # Filter for our dip range (negative values)
                if -max_dip <= change <= -min_dip:
                    sector = stock.get('Sector') or ''
                    results.append({
                        'ticker': stock.get('Ticker'),
                        'company': stock.get('Company'),
                        'price': float(stock.get('Price', 0)),
                        'change': change,
                        'volume': stock.get('Volume'),
                        'rel_volume': stock.get('Rel Volume'),
                        'sector': sector,
                        'industry': stock.get('Industry'),
                    })
            except Exception:
                continue
        
        return results
        
    except Exception as e:
        print(f"Screener error: {e}")
        return []


def get_dips_from_ticker_list(ticker_list: List[str], config: Dict) -> List[Dict]:
    """
    Get dip candidates from a fixed ticker list (e.g. Leveraged high-conviction universe).
    For each ticker, fetches quote via Finviz; keeps those down within configured dip range.
    Returns same structure as get_sp500_dips for use by emotional_dip_scanner.
    """
    min_dip = float(config.get('dip_min_percent', 1.0))
    max_dip = float(config.get('dip_max_percent', 5.0))
    min_price = float(config.get('min_price', 5.0))
    max_price = float(config.get('max_price', 500.0))
    min_volume = int(float(config.get('min_avg_volume', 500000)))
    results = []
    for i, ticker in enumerate(ticker_list or []):
        ticker = (ticker or "").strip().upper()
        if not ticker:
            continue
        try:
            stock = get_stock_safe(ticker)
            if not stock:
                time.sleep(0.5)
                continue
            change_str = (stock.get('Change') or '0%').replace('%', '').strip()
            change = float(change_str)
            price = float(stock.get('Price') or 0)
            vol_str = (stock.get('Volume') or '0').replace(',', '').replace('K', 'e3').replace('M', 'e6')
            try:
                vol = int(float(vol_str))
            except (TypeError, ValueError):
                vol = 0
            if -max_dip > change or change > -min_dip:
                continue
            if price < min_price or price > max_price or vol < min_volume:
                continue
            results.append({
                'ticker': stock.get('Ticker') or ticker,
                'company': stock.get('Company') or ticker,
                'price': price,
                'change': change,
                'volume': stock.get('Volume'),
                'rel_volume': stock.get('Rel Volume'),
                'sector': stock.get('Sector') or '',
                'industry': stock.get('Industry') or '',
            })
        except Exception:
            pass
        time.sleep(0.5)  # polite delay between Finviz calls
    return results


def analyze_dip_quality(ticker: str) -> Dict:
    """
    Deep analysis of a dip candidate.
    Checks news, analyst ratings, price targets.
    Returns quality assessment.
    """
    result = {
        'ticker': ticker,
        'news_sentiment': 'unknown',
        'dip_type': 'unknown',  # 'emotional' or 'fundamental'
        'analyst_rating': None,
        'analyst_score': 0,
        'price_target': None,
        'upside_percent': None,
        'recommendation': 'neutral',
        'red_flags': [],
        'green_flags': [],
        'score': 50,  # Start neutral
    }
    
    try:
        # Get detailed quote data (with timeout + retry protection)
        quote = get_stock_safe(ticker, timeout=30.0, max_attempts=3)
        
        if not quote:
            return result
        
        # === ANALYST RATING ===
        rating = quote.get('Recom', '')
        if rating:
            try:
                # Finviz returns numeric rating (1=Strong Buy, 5=Strong Sell)
                rating_num = float(rating)
                if rating_num <= 1.5:
                    result['analyst_rating'] = 'Strong Buy'
                    result['analyst_score'] = 5
                    result['green_flags'].append('Analysts rate Strong Buy')
                    result['score'] += 15
                elif rating_num <= 2.0:
                    result['analyst_rating'] = 'Buy'
                    result['analyst_score'] = 4
                    result['green_flags'].append('Analysts rate Buy')
                    result['score'] += 10
                elif rating_num <= 2.5:
                    result['analyst_rating'] = 'Outperform'
                    result['analyst_score'] = 4
                    result['score'] += 5
                elif rating_num <= 3.5:
                    result['analyst_rating'] = 'Hold'
                    result['analyst_score'] = 3
                elif rating_num <= 4.0:
                    result['analyst_rating'] = 'Underperform'
                    result['analyst_score'] = 2
                    result['red_flags'].append('Analysts rate Underperform')
                    result['score'] -= 10
                else:
                    result['analyst_rating'] = 'Sell'
                    result['analyst_score'] = 1
                    result['red_flags'].append('Analysts rate Sell')
                    result['score'] -= 20
            except Exception:
                pass

        # === PRICE TARGET ===
        target = quote.get('Target Price', '')
        price = quote.get('Price', '')
        if target and price:
            try:
                target_val = float(target)
                price_val = float(price)
                result['price_target'] = target_val
                upside = ((target_val - price_val) / price_val) * 100
                result['upside_percent'] = round(upside, 1)
                
                if upside >= 30:
                    result['green_flags'].append(f'High upside to target: {upside:.0f}%')
                    result['score'] += 15
                elif upside >= 15:
                    result['green_flags'].append(f'Good upside to target: {upside:.0f}%')
                    result['score'] += 10
                elif upside >= 5:
                    result['score'] += 5
                elif upside < 0:
                    result['red_flags'].append(f'Below price target by {abs(upside):.0f}%')
                    result['score'] -= 10
            except Exception:
                pass
        
        # === NEWS ANALYSIS === (with one retry on failure)
        try:
            news = None
            for _attempt in range(2):
                try:
                    news = finviz.get_news(ticker)
                    break
                except Exception as e:
                    if '429' in str(e).lower() or 'timeout' in str(e).lower():
                        time.sleep(4)  # longer backoff on Finviz rate limit
                        continue
                    break
            if news:
                news_text = ' '.join([n[1].lower() for n in news[:10]])  # Last 10 headlines
                
                # Check for fundamental problems
                fundamental_hits = []
                for keyword in FUNDAMENTAL_KEYWORDS:
                    if keyword in news_text:
                        fundamental_hits.append(keyword)
                
                # Check for emotional triggers
                emotional_hits = []
                for keyword in EMOTIONAL_KEYWORDS:
                    if keyword in news_text:
                        emotional_hits.append(keyword)
                
                if fundamental_hits:
                    result['dip_type'] = 'fundamental'
                    result['news_sentiment'] = 'negative'
                    result['red_flags'].append(f'Fundamental news: {", ".join(fundamental_hits[:3])}')
                    result['score'] -= 25
                elif emotional_hits:
                    result['dip_type'] = 'emotional'
                    result['news_sentiment'] = 'emotional'
                    result['green_flags'].append(f'Emotional dip: {", ".join(emotional_hits[:3])}')
                    result['score'] += 15
                else:
                    result['dip_type'] = 'unclear'
                    result['news_sentiment'] = 'neutral'
        except Exception:
            pass

        # === TECHNICAL FACTORS ===
        # RSI - oversold is good for dips
        rsi = quote.get('RSI (14)', '')
        if rsi:
            try:
                rsi_val = float(rsi)
                if rsi_val < 30:
                    result['green_flags'].append(f'Oversold RSI: {rsi_val:.0f}')
                    result['score'] += 10
                elif rsi_val < 40:
                    result['green_flags'].append(f'Low RSI: {rsi_val:.0f}')
                    result['score'] += 5
                elif rsi_val > 70:
                    result['red_flags'].append(f'Overbought RSI: {rsi_val:.0f}')
                    result['score'] -= 5
            except Exception:
                pass
        
        # Check if above key MAs (healthy stock in a dip)
        sma50 = quote.get('SMA50', '')
        sma200 = quote.get('SMA200', '')
        if sma50 and sma200 and price:
            try:
                # These come as percentages from current price
                sma50_pct = float(sma50.replace('%', ''))
                sma200_pct = float(sma200.replace('%', ''))
                
                if sma50_pct > 0 and sma200_pct > 0:
                    result['green_flags'].append('Above SMA50 & SMA200')
                    result['score'] += 10
                elif sma200_pct > 0:
                    result['green_flags'].append('Above SMA200')
                    result['score'] += 5
                elif sma200_pct < -10:
                    result['red_flags'].append('Well below SMA200')
                    result['score'] -= 10
            except Exception:
                pass
        
        # === FINAL RECOMMENDATION ===
        if result['score'] >= 75:
            result['recommendation'] = 'STRONG BUY'
        elif result['score'] >= 65:
            result['recommendation'] = 'BUY'
        elif result['score'] >= 55:
            result['recommendation'] = 'LEAN BUY'
        elif result['score'] >= 45:
            result['recommendation'] = 'NEUTRAL'
        elif result['score'] >= 35:
            result['recommendation'] = 'LEAN AVOID'
        else:
            result['recommendation'] = 'AVOID'
        
        # Cap score at 0-100
        result['score'] = max(0, min(100, result['score']))
        
        # Keep quote for optional institutional gates (Swing)
        result['_quote'] = quote
    except Exception as e:
        result['red_flags'].append(f'Analysis error: {str(e)}')
    
    return result


def run_enhanced_dip_scan(progress_callback=None, index: str = "sp500") -> List[Dict]:
    """
    Run full enhanced dip scan.
    
    Args:
        progress_callback: function(msg) for status updates
        index: 'sp500' or 'etfs'
    
    1. Get stocks down within range
    2. Analyze each for news/analyst/targets
    3. Score and rank
    4. Return sorted results
    """
    config = load_config()
    
    index_name = "S&P 500" if index == "sp500" else "ETFs"
    
    if progress_callback:
        progress_callback(f"Scanning {index_name} for dips...")
    
    # Step 1: Get dip candidates
    candidates = get_sp500_dips(config, index)
    
    if not candidates:
        return []
    
    if progress_callback:
        progress_callback(f"Found {len(candidates)} dips. Analyzing quality...")
    
    # Step 2: Deep analysis on each (news + analyst ratings always; rate limiting)
    results = []
    for i, candidate in enumerate(candidates):
        ticker = candidate['ticker']
        
        if progress_callback:
            progress_callback(f"Analyzing {ticker} ({i+1}/{len(candidates)})...")
        
        # Always run news + analyst check (required for all scans)
        analysis = analyze_dip_quality(ticker)
        candidate.update(analysis)
        candidate.pop('_quote', None)
        
        # Rate limit - Finviz doesn't like rapid fire
        if i < len(candidates) - 1:
            time.sleep(0.8)
        
        results.append(candidate)
    
    # Step 3: Sort by score
    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    if progress_callback:
        progress_callback(f"Scan complete. {len(results)} candidates scored.")
    
    return results


# For direct testing
if __name__ == "__main__":
    print("Running enhanced dip scan...")
    results = run_enhanced_dip_scan(lambda msg: print(msg))
    
    print("\n" + "="*60)
    print("TOP DIP CANDIDATES")
    print("="*60)
    
    for r in results[:10]:
        print(f"\n{r['ticker']} - Score: {r.get('score', 'N/A')}")
        print(f"  Price: ${r.get('price', 'N/A')} | Change: {r.get('change', 'N/A')}%")
        print(f"  Type: {r.get('dip_type', 'N/A')} | Rating: {r.get('analyst_rating', 'N/A')}")
        print(f"  Target: ${r.get('price_target', 'N/A')} | Upside: {r.get('upside_percent', 'N/A')}%")
        print(f"  Recommendation: {r.get('recommendation', 'N/A')}")
        if r.get('green_flags'):
            print(f"  + {', '.join(r['green_flags'])}")
        if r.get('red_flags'):
            print(f"  - {', '.join(r['red_flags'])}")
