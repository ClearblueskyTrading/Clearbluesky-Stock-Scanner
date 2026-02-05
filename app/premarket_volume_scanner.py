# ============================================================
# ClearBlueSky - Pre-Market Volume Scanner
# ============================================================
# Scans for unusual pre-market volume activity (7:00 AM - 9:25 AM)
# Identifies strength before the opening bell
# Focuses on Semiconductors, Precious Metals, and high-conviction moves

import time
from datetime import datetime
from typing import List, Dict, Optional
from finviz.screener import Screener
import finviz

from scan_settings import load_config


def get_float_category(float_size: float) -> str:
    """Categorize float size"""
    if float_size < 20_000_000:
        return "Low"
    elif float_size < 100_000_000:
        return "Mid"
    else:
        return "High"


def run_premarket_volume_scan(progress_callback=None, index: str = "sp500") -> List[Dict]:
    """
    Run Pre-Market Volume scan - finds unusual activity before market open.
    
    Designed for 7:00 AM - 9:25 AM runs.
    
    Parameters tracked:
    - Relative Volume (Pre-Market Vol / Avg Pre-Market Vol)
    - Gap Percentage & Direction
    - Float Analysis (Low/Mid/High)
    - Dollar Volume (liquidity gate)
    - Vol/Float Ratio
    - Sector Heat (aggregate by sector)
    
    Args:
        progress_callback: function(msg) for status updates
        index: 'sp500', 'russell2000', or 'etfs'
    
    Returns:
        List of pre-market volume candidates sorted by score
    """
    config = load_config()
    
    index_name = "S&P 500" if index == "sp500" else ("ETFs" if index == "etfs" else "Russell 2000")
    
    if progress_callback:
        progress_callback(f"Scanning {index_name} for pre-market volume activity...")
    
    # Get current time to validate scan window
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    # Warn if outside optimal window (7:00 AM - 9:25 AM)
    if current_hour < 7 or (current_hour == 9 and current_minute > 25) or current_hour >= 10:
        if progress_callback:
            progress_callback("⚠️ Outside optimal pre-market window (7:00 AM - 9:25 AM)")
    
    # Base filters
    min_price = float(config.get('min_price', 5.0))
    max_price = float(config.get('max_price', 500.0))
    min_volume = int(float(config.get('min_avg_volume', 500000)))
    
    # Pre-market specific filters
    min_pm_volume = int(config.get('premarket_min_volume', 100000))
    min_rel_vol = float(config.get('premarket_min_relative_volume', 2.0))
    min_gap = float(config.get('premarket_min_gap_percent', 2.0))
    max_gap = float(config.get('premarket_max_gap_percent', 15.0))
    min_dollar_vol = float(config.get('premarket_min_dollar_volume', 500000))
    min_vol_float_ratio = float(config.get('premarket_min_vol_float_ratio', 0.01))
    track_sector_heat = config.get('premarket_track_sector_heat', True)
    
    # Index filter (Finviz: idx_sp500, idx_rut, ind_exchangetradedfund for ETFs)
    if index == 'etfs':
        idx_filter = 'ind_exchangetradedfund'
    else:
        idx_filter = 'idx_sp500' if index == 'sp500' else 'idx_rut'
    
    # Use Finviz screener for unusual volume
    # Note: Finviz may not have pre-market volume directly, so we use regular volume
    # and gap filters as proxy
    filters = [
        idx_filter,
        f'sh_price_o{int(min_price)}',
        f'sh_price_u{int(max_price)}',
        f'sh_avgvol_o{int(min_volume/1000)}',
        'ta_change_u',  # Unusual volume
    ]
    
    try:
        screener = Screener(filters=filters, order='change')
        candidates = []
        
        for stock in screener:
            try:
                ticker = stock.get('Ticker')
                if not ticker:
                    continue
                
                price = float(stock.get('Price', 0))
                change_str = stock.get('Change', '0%').replace('%', '')
                change = float(change_str)
                
                # Filter by gap percentage
                if abs(change) < min_gap or abs(change) > max_gap:
                    continue
                
                candidates.append({
                    'ticker': ticker,
                    'company': stock.get('Company', ticker),
                    'price': price,
                    'change': change,
                    'gap_percent': abs(change),
                    'gap_direction': 'up' if change > 0 else 'down',
                    'volume': stock.get('Volume', '0'),
                    'rel_volume': stock.get('Rel Volume', '1.0x'),
                    'sector': stock.get('Sector', 'N/A'),
                    'industry': stock.get('Industry', 'N/A'),
                })
            except Exception as e:
                continue
        
        if not candidates:
            if progress_callback:
                progress_callback("No pre-market candidates found.")
            return []
        
        if progress_callback:
            progress_callback(f"Found {len(candidates)} candidates. Analyzing volume patterns...")
        
        # Deep analysis
        results = []
        sector_volumes = {}  # Track sector heat
        
        for i, candidate in enumerate(candidates):
            ticker = candidate['ticker']
            
            if progress_callback:
                progress_callback(f"Analyzing {ticker} ({i+1}/{len(candidates)})...")
            
            try:
                # Get detailed quote
                quote = finviz.get_stock(ticker)
                if not quote:
                    continue
                
                # Extract key metrics
                volume_str = candidate.get('volume', '0')
                try:
                    volume = int(volume_str.replace(',', ''))
                except:
                    volume = 0
                
                rel_vol_str = candidate.get('rel_volume', '1.0x')
                try:
                    rel_vol = float(rel_vol_str.replace('x', '').replace(' ', ''))
                except:
                    rel_vol = 1.0
                
                # Dollar volume
                dollar_volume = volume * price
                if dollar_volume < min_dollar_vol:
                    continue
                
                # Float analysis
                float_str = quote.get('Float', '')
                float_size = None
                try:
                    if 'M' in float_str:
                        float_size = float(float_str.replace('M', '')) * 1_000_000
                    elif 'B' in float_str:
                        float_size = float(float_str.replace('B', '')) * 1_000_000_000
                    else:
                        float_size = float(float_str.replace(',', ''))
                except:
                    pass
                
                # Vol/Float ratio
                vol_float_ratio = 0.0
                if float_size and float_size > 0:
                    vol_float_ratio = volume / float_size
                    if vol_float_ratio < min_vol_float_ratio:
                        continue
                
                float_category = get_float_category(float_size) if float_size else "Unknown"
                
                # Market cap for context
                market_cap = quote.get('Market Cap', 'N/A')
                
                # === SCORE CALCULATION ===
                score = 50  # Base
                
                # Relative volume boost (most important)
                if rel_vol >= 5.0:
                    score += 25
                elif rel_vol >= 3.0:
                    score += 20
                elif rel_vol >= min_rel_vol:
                    score += 15
                
                # Gap strength
                gap_pct = candidate.get('gap_percent', 0)
                if gap_pct >= 10:
                    score += 15
                elif gap_pct >= 5:
                    score += 10
                elif gap_pct >= min_gap:
                    score += 5
                
                # Dollar volume (liquidity)
                if dollar_volume >= 5_000_000:
                    score += 10
                elif dollar_volume >= 2_000_000:
                    score += 7
                elif dollar_volume >= min_dollar_vol:
                    score += 5
                
                # Float category (low float = volatility opportunity)
                if float_category == "Low":
                    score += 10
                elif float_category == "Mid":
                    score += 5
                
                # Vol/Float ratio (turnover)
                if vol_float_ratio >= 0.05:
                    score += 10
                elif vol_float_ratio >= 0.02:
                    score += 5
                
                # Sector preference (Semiconductors, Precious Metals)
                sector = candidate.get('sector', '').lower()
                if 'semiconductor' in sector or 'technology' in sector:
                    score += 5
                if 'precious' in sector or 'metals' in sector or 'mining' in sector:
                    score += 5
                
                # Track sector heat
                if track_sector_heat:
                    sector_name = candidate.get('sector', 'Unknown')
                    if sector_name not in sector_volumes:
                        sector_volumes[sector_name] = []
                    sector_volumes[sector_name].append({
                        'ticker': ticker,
                        'volume': volume,
                        'rel_vol': rel_vol,
                    })
                
                candidate.update({
                    'score': max(0, min(100, score)),
                    'volume': volume,
                    'relative_volume': rel_vol,
                    'dollar_volume': dollar_volume,
                    'float_size': float_size,
                    'float_category': float_category,
                    'vol_float_ratio': round(vol_float_ratio, 4),
                    'market_cap': market_cap,
                    'recommendation': 'STRONG BUY' if score >= 80 else 'BUY' if score >= 70 else 'WATCH',
                })
                
                results.append(candidate)
                
            except Exception as e:
                continue
            
            # Rate limit
            if i < len(candidates) - 1:
                time.sleep(0.3)
        
        # Sort by score
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Add sector heat summary
        if track_sector_heat and sector_volumes:
            heat_summary = []
            for sector, stocks in sector_volumes.items():
                avg_rel_vol = sum(s['rel_vol'] for s in stocks) / len(stocks)
                total_volume = sum(s['volume'] for s in stocks)
                heat_summary.append({
                    'sector': sector,
                    'stock_count': len(stocks),
                    'avg_relative_volume': round(avg_rel_vol, 2),
                    'total_volume': total_volume,
                })
            heat_summary.sort(key=lambda x: x['avg_relative_volume'], reverse=True)
            
            # Add top sectors to results metadata
            if results:
                results[0]['_sector_heat'] = heat_summary[:5]  # Top 5 sectors
        
        if progress_callback:
            progress_callback(f"Scan complete. {len(results)} pre-market candidates found.")
        
        return results
        
    except Exception as e:
        if progress_callback:
            progress_callback(f"Error: {str(e)}")
        return []


if __name__ == "__main__":
    print("Running Pre-Market Volume scan...")
    results = run_premarket_volume_scan(lambda msg: print(msg))
    
    print("\n" + "="*60)
    print("PRE-MARKET VOLUME CANDIDATES (7:00 AM - 9:25 AM)")
    print("="*60)
    
    for r in results[:10]:
        print(f"\n{r['ticker']} - Score: {r.get('score', 'N/A')}")
        print(f"  Price: ${r.get('price', 'N/A')} | Gap: {r.get('gap_percent', 'N/A')}% ({r.get('gap_direction', 'N/A')})")
        print(f"  Volume: {r.get('volume', 'N/A'):,} | Rel Vol: {r.get('relative_volume', 'N/A')}x")
        print(f"  Dollar Vol: ${r.get('dollar_volume', 'N/A'):,.0f} | Float: {r.get('float_category', 'N/A')}")
        print(f"  Sector: {r.get('sector', 'N/A')} | Recommendation: {r.get('recommendation', 'N/A')}")
