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

from scan_settings import load_config, SECTOR_FINVIZ_MAP

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


def check_earnings_proximity(quote: dict) -> dict:
    """
    Check if stock has earnings coming up soon.
    Returns dict with earnings info and risk assessment.
    """
    result = {
        'earnings_date': None,
        'days_to_earnings': None,
        'earnings_risk': 'unknown',
        'earnings_flag': None
    }

    try:
        # Finviz provides earnings date in quote data
        earnings_str = quote.get('Earnings', '')
        if not earnings_str or earnings_str == '-':
            return result

        # Parse earnings date (format varies: "Feb 15 AMC", "Jan 28 BMO", etc.)
        from datetime import datetime
        import re

        # Extract date part
        date_match = re.match(r'([A-Za-z]{3}\s+\d{1,2})', earnings_str)
        if date_match:
            date_str = date_match.group(1)
            current_year = datetime.now().year

            try:
                # Try parsing with current year
                earnings_date = datetime.strptime(f"{date_str} {current_year}", "%b %d %Y")

                # If earnings date is in the past, try next year
                if earnings_date < datetime.now():
                    earnings_date = datetime.strptime(f"{date_str} {current_year + 1}", "%b %d %Y")

                days_to_earnings = (earnings_date - datetime.now()).days
                result['earnings_date'] = earnings_date.strftime("%Y-%m-%d")
                result['days_to_earnings'] = days_to_earnings

                # Assess earnings risk
                if days_to_earnings <= 3:
                    result['earnings_risk'] = 'high'
                    result['earnings_flag'] = f'EARNINGS IN {days_to_earnings} DAYS - High Risk'
                elif days_to_earnings <= 7:
                    result['earnings_risk'] = 'medium'
                    result['earnings_flag'] = f'Earnings in {days_to_earnings} days'
                elif days_to_earnings <= 14:
                    result['earnings_risk'] = 'low'
                    result['earnings_flag'] = f'Earnings in ~{days_to_earnings} days'
                else:
                    result['earnings_risk'] = 'none'

            except ValueError:
                pass

    except Exception:
        pass

    return result


def get_sp500_dips(config: Dict, index: str = "sp500") -> List[Dict]:
    """
    Scan index for stocks down within configured range.
    index: 'sp500' or 'russell2000'
    Returns raw list before filtering.
    """
    min_dip = float(config.get('dip_min_percent', 1.0))
    max_dip = float(config.get('dip_max_percent', 5.0))
    min_price = float(config.get('min_price', 5.0))
    max_price = float(config.get('max_price', 500.0))
    min_volume = int(float(config.get('min_avg_volume', 500000)))
    sector_filter = config.get('sector_filter', 'All Sectors')

    # Index filter
    idx_filter = 'idx_sp500' if index == 'sp500' else 'idx_rut'

    filters = [
        idx_filter,
        f'sh_price_o{int(min_price)}',
        f'sh_price_u{int(max_price)}',
        f'sh_avgvol_o{int(min_volume/1000)}',  # Finviz uses K
        'ta_change_d',  # Down today
    ]

    # Add sector filter if specified
    if sector_filter and sector_filter != "All Sectors":
        # Map sector name to Finviz sector filter code
        sector_codes = {
            "Technology": "sec_technology",
            "Healthcare": "sec_healthcare",
            "Financial": "sec_financial",
            "Consumer Cyclical": "sec_consumercyclical",
            "Consumer Defensive": "sec_consumerdefensive",
            "Industrials": "sec_industrials",
            "Energy": "sec_energy",
            "Basic Materials": "sec_basicmaterials",
            "Communication Services": "sec_communicationservices",
            "Real Estate": "sec_realestate",
            "Utilities": "sec_utilities"
        }
        sector_code = sector_codes.get(sector_filter)
        if sector_code:
            filters.append(sector_code)
    
    try:
        screener = Screener(filters=filters, order='change')
        results = []
        
        for stock in screener:
            try:
                change_str = stock.get('Change', '0%').replace('%', '')
                change = float(change_str)
                
                # Filter for our dip range (negative values)
                if -max_dip <= change <= -min_dip:
                    results.append({
                        'ticker': stock.get('Ticker'),
                        'company': stock.get('Company'),
                        'price': float(stock.get('Price', 0)),
                        'change': change,
                        'volume': stock.get('Volume'),
                        'rel_volume': stock.get('Rel Volume'),
                        'sector': stock.get('Sector'),
                        'industry': stock.get('Industry'),
                    })
            except:
                continue
        
        return results
        
    except Exception as e:
        print(f"Screener error: {e}")
        return []


def analyze_dip_quality(ticker: str) -> Dict:
    """
    Deep analysis of a dip candidate.
    Checks news, analyst ratings, price targets, earnings proximity.
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
        'earnings_date': None,
        'days_to_earnings': None,
        'earnings_risk': 'unknown',
        'short_float': None,
        'short_ratio': None,
        'short_interest_flag': None,
    }
    
    try:
        # Get detailed quote data
        quote = finviz.get_stock(ticker)
        
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
            except:
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
            except:
                pass
        
        # === NEWS ANALYSIS ===
        try:
            news = finviz.get_news(ticker)
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
        except:
            pass

        # === TECHNICAL FACTORS - ENHANCED RSI ANALYSIS ===
        # RSI - oversold is good for dips
        rsi = quote.get('RSI (14)', '')
        if rsi:
            try:
                rsi_val = float(rsi)
                result['rsi'] = rsi_val

                # Get performance data for multi-timeframe context
                perf_week = quote.get('Perf Week', '')
                perf_month = quote.get('Perf Month', '')

                # Analyze RSI with performance context
                weekly_down = False
                monthly_down = False

                if perf_week and perf_week != '-':
                    try:
                        week_pct = float(perf_week.replace('%', ''))
                        weekly_down = week_pct < -3  # Down more than 3% weekly
                    except:
                        pass

                if perf_month and perf_month != '-':
                    try:
                        month_pct = float(perf_month.replace('%', ''))
                        monthly_down = month_pct < -5  # Down more than 5% monthly
                    except:
                        pass

                # Enhanced RSI scoring with multi-timeframe context
                if rsi_val < 30:
                    result['green_flags'].append(f'Oversold RSI: {rsi_val:.0f}')
                    result['score'] += 10

                    # Extra bonus if oversold with weekly/monthly downtrend (capitulation)
                    if weekly_down and monthly_down:
                        result['green_flags'].append('RSI oversold + multi-week selloff (capitulation?)')
                        result['score'] += 10
                    elif weekly_down:
                        result['green_flags'].append('RSI oversold + weekly downtrend')
                        result['score'] += 5

                elif rsi_val < 40:
                    result['green_flags'].append(f'Low RSI: {rsi_val:.0f}')
                    result['score'] += 5

                    if weekly_down:
                        result['green_flags'].append('Low RSI with weekly weakness')
                        result['score'] += 3

                elif rsi_val > 70:
                    result['red_flags'].append(f'Overbought RSI: {rsi_val:.0f}')
                    result['score'] -= 5

                    # If overbought but stock is down today, could be distribution
                    if result.get('change', 0) < 0:
                        result['red_flags'].append('Overbought RSI + down day (distribution?)')
                        result['score'] -= 5

                elif rsi_val > 50 and rsi_val <= 70:
                    # Neutral to slightly bullish - note it
                    result['rsi_note'] = f'RSI neutral-bullish: {rsi_val:.0f}'

            except:
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
            except:
                pass

        # === EARNINGS PROXIMITY CHECK ===
        earnings_info = check_earnings_proximity(quote)
        result['earnings_date'] = earnings_info['earnings_date']
        result['days_to_earnings'] = earnings_info['days_to_earnings']
        result['earnings_risk'] = earnings_info['earnings_risk']

        if earnings_info['earnings_risk'] == 'high':
            result['red_flags'].append(earnings_info['earnings_flag'])
            result['score'] -= 20  # Significant penalty for imminent earnings
        elif earnings_info['earnings_risk'] == 'medium':
            result['red_flags'].append(earnings_info['earnings_flag'])
            result['score'] -= 10
        elif earnings_info['earnings_risk'] == 'low':
            # Just a note, no score change
            result['green_flags'].append(earnings_info['earnings_flag'])

        # === SHORT INTEREST CHECK ===
        short_float = quote.get('Short Float', '')
        short_ratio = quote.get('Short Ratio', '')

        if short_float and short_float != '-':
            try:
                sf_val = float(short_float.replace('%', ''))
                result['short_float'] = sf_val

                # High short interest can indicate squeeze potential or fundamental problems
                if sf_val >= 20:
                    result['short_interest_flag'] = 'HIGH_SHORT'
                    result['red_flags'].append(f'High short interest: {sf_val:.1f}%')
                    # Could be squeeze potential but also risky - slight penalty
                    result['score'] -= 5
                elif sf_val >= 10:
                    result['short_interest_flag'] = 'ELEVATED_SHORT'
                    result['green_flags'].append(f'Elevated short interest: {sf_val:.1f}% (squeeze potential)')
                    # Moderate short interest on a dip could indicate squeeze opportunity
                    result['score'] += 5
                elif sf_val >= 5:
                    result['short_interest_flag'] = 'MODERATE_SHORT'
            except:
                pass

        if short_ratio and short_ratio != '-':
            try:
                sr_val = float(short_ratio)
                result['short_ratio'] = sr_val

                # Short ratio > 5 days to cover is significant
                if sr_val >= 10:
                    if not result.get('short_interest_flag'):
                        result['short_interest_flag'] = 'HIGH_SHORT_RATIO'
                    result['green_flags'].append(f'High days to cover: {sr_val:.1f} days')
                elif sr_val >= 5:
                    result['green_flags'].append(f'Days to cover: {sr_val:.1f}')
            except:
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
        
    except Exception as e:
        result['red_flags'].append(f'Analysis error: {str(e)}')
    
    return result


def run_enhanced_dip_scan(progress_callback=None, index: str = "sp500") -> List[Dict]:
    """
    Run full enhanced dip scan.

    Args:
        progress_callback: function(msg) for status updates
        index: 'sp500' or 'russell2000'

    1. Get stocks down within range
    2. Analyze each for news/analyst/targets
    3. Score and rank
    4. Return sorted results
    """
    config = load_config()

    index_name = "S&P 500" if index == "sp500" else "Russell 2000"
    sector_filter = config.get('sector_filter', 'All Sectors')
    sector_msg = f" [{sector_filter}]" if sector_filter != "All Sectors" else ""

    if progress_callback:
        progress_callback(f"Scanning {index_name}{sector_msg} for dips...")
    
    # Step 1: Get dip candidates
    candidates = get_sp500_dips(config, index)
    
    if not candidates:
        return []
    
    if progress_callback:
        progress_callback(f"Found {len(candidates)} dips. Analyzing quality...")
    
    # Step 2: Deep analysis on each (with rate limiting)
    results = []
    check_news = config.get('dip_require_news_check', True)
    check_analyst = config.get('dip_require_analyst_check', True)
    
    for i, candidate in enumerate(candidates):
        ticker = candidate['ticker']
        
        if progress_callback:
            progress_callback(f"Analyzing {ticker} ({i+1}/{len(candidates)})...")
        
        if check_news or check_analyst:
            # Deep analysis
            analysis = analyze_dip_quality(ticker)
            candidate.update(analysis)
            
            # Rate limit - Finviz doesn't like rapid fire
            if i < len(candidates) - 1:
                time.sleep(0.5)
        else:
            # Basic scoring without deep analysis
            candidate['score'] = 50
            candidate['recommendation'] = 'NEUTRAL'
            candidate['dip_type'] = 'unchecked'
        
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
