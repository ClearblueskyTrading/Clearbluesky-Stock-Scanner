# ============================================================
# ClearBlueSky - Emotional Dip Scanner
# ============================================================
# Scans for stocks that dropped purely from emotional sentiment
# Designed to run ~3:30 PM, buy by 4 PM, bounce next 1-2 days
# Filters out fundamental dips (earnings misses, etc.)

import time
from datetime import datetime
from typing import List, Dict
from finviz.screener import Screener
import finviz

from scan_settings import load_config
from enhanced_dip_scanner import (
    EMOTIONAL_KEYWORDS,
    FUNDAMENTAL_KEYWORDS,
    analyze_dip_quality,
    get_sp500_dips,
)


def run_emotional_dip_scan(progress_callback=None, index: str = "sp500") -> List[Dict]:
    """
    Run Emotional Dip scan - finds stocks that dropped from sentiment only.
    
    Designed for 3:30 PM runs, buy by 4 PM close.
    Filters for:
    - Emotional news triggers (no fundamental problems)
    - Above SMA200 (healthy stock)
    - Buy/Strong Buy analyst rating
    - Good upside to price target
    - High relative volume (conviction)
    
    Args:
        progress_callback: function(msg) for status updates
        index: 'sp500', 'etfs', or 'velocity' (Leveraged high-conviction universe)
    
    Returns:
        List of emotional dip candidates sorted by score
    """
    config = load_config()
    
    index_name = "S&P 500" if index == "sp500" else ("ETFs" if index == "etfs" else "Leveraged (high-conviction)")
    
    if progress_callback:
        progress_callback(f"Scanning {index_name} for emotional dips...")
    
    # Get dip candidates (same base function as swing scanner)
    min_dip = float(config.get('emotional_dip_min_percent', 1.5))
    max_dip = float(config.get('emotional_dip_max_percent', 4.0))
    min_price = float(config.get('min_price', 5.0))
    max_price = float(config.get('max_price', 500.0))
    min_volume = int(float(config.get('min_avg_volume', 500000)))
    
    # Temporarily override config for dip range
    temp_config = config.copy()
    temp_config['dip_min_percent'] = min_dip
    temp_config['dip_max_percent'] = max_dip
    
    if index == "velocity":
        from enhanced_dip_scanner import get_dips_from_ticker_list
        from velocity_scanner import SCAN_UNIVERSE
        candidates = get_dips_from_ticker_list(SCAN_UNIVERSE, temp_config)
    else:
        candidates = get_sp500_dips(temp_config, index)
    
    if not candidates:
        if progress_callback:
            progress_callback("No dip candidates found.")
        return []
    
    if progress_callback:
        progress_callback(f"Found {len(candidates)} dips. Analyzing for emotional triggers...")
    
    # Deep analysis - filter for EMOTIONAL ONLY
    results = []
    require_above_sma200 = config.get('emotional_require_above_sma200', False)
    min_upside = float(config.get('emotional_min_upside_to_target', 5.0))
    require_buy_rating = config.get('emotional_require_buy_rating', False)
    min_vol_ratio = float(config.get('emotional_min_volume_ratio', 1.2))
    
    for i, candidate in enumerate(candidates):
        ticker = candidate['ticker']
        
        if progress_callback:
            progress_callback(f"Analyzing {ticker} ({i+1}/{len(candidates)})...")
        
        # Deep analysis (reuse cached Finviz quote to avoid redundant API calls)
        analysis = analyze_dip_quality(ticker)
        cached_quote = analysis.pop('_quote', None)
        candidate.update(analysis)
        
        # === FILTERING FOR EMOTIONAL DIPS ===
        
        # 1. MUST NOT be a fundamental dip (emotional or unclear are OK)
        dip_type = candidate.get('dip_type', 'unclear')
        if dip_type == 'fundamental':
            continue
        
        # 2. MUST have no fundamental red flags
        if any('fundamental' in flag.lower() for flag in candidate.get('red_flags', [])):
            continue
        
        # 3. MUST be above SMA200 if required (use cached quote from analyze_dip_quality)
        if require_above_sma200:
            sma200_pct = None
            try:
                quote = cached_quote or {}
                sma200_str = quote.get('SMA200', '')
                if sma200_str:
                    sma200_pct = float(sma200_str.replace('%', ''))
            except Exception:
                pass
            
            if sma200_pct is None or sma200_pct < 0:
                continue
        
        # 4. MUST have Buy/Strong Buy rating if required
        if require_buy_rating:
            rating = candidate.get('analyst_rating', '')
            if rating not in ['Buy', 'Strong Buy', 'Outperform', 'Overweight']:
                continue
        
        # 5. MUST have good upside to target
        upside = candidate.get('upside_percent', 0)
        if upside is None or upside < min_upside:
            continue
        
        # 6. Relative volume check (skip if not available)
        rel_vol = candidate.get('rel_volume') or 0
        try:
            if isinstance(rel_vol, str):
                rel_vol = float(rel_vol.replace('x', '').replace(',', ''))
            else:
                rel_vol = float(rel_vol)
        except Exception:
            rel_vol = 0
        # Only filter on rel_vol if we have a valid reading
        if rel_vol > 0 and rel_vol < min_vol_ratio:
            continue
        
        # === SCORE CALCULATION (emotional-specific) ===
        score = 50  # Base
        
        # Dip type boost (emotional = confirmed buyable, unclear = no bad news found)
        if dip_type == 'emotional':
            score += 20
        elif dip_type == 'unclear':
            score += 10  # No news = probably not fundamental
        
        # Analyst rating boost
        analyst_score = candidate.get('analyst_score', 0)
        if analyst_score >= 4:
            score += 15
        elif analyst_score >= 3:
            score += 5
        
        # Upside boost
        if upside >= 30:
            score += 15
        elif upside >= 20:
            score += 10
        elif upside >= min_upside:
            score += 5
        
        # Relative volume boost
        if rel_vol >= 3.0:
            score += 10
        elif rel_vol >= 2.0:
            score += 5
        
        # RSI oversold boost (use cached quote)
        try:
            quote = cached_quote or {}
            rsi_str = quote.get('RSI (14)', '')
            if rsi_str:
                rsi = float(rsi_str)
                if rsi < 30:
                    score += 10
                elif rsi < 40:
                    score += 5
        except Exception:
            pass
        
        # Green flags boost
        score += len(candidate.get('green_flags', [])) * 2
        
        # Red flags penalty
        score -= len(candidate.get('red_flags', [])) * 5
        
        candidate['score'] = max(0, min(100, score))
        candidate['recommendation'] = 'STRONG BUY' if score >= 75 else 'BUY' if score >= 65 else 'LEAN BUY'
        
        results.append(candidate)
        
        # Rate limit
        if i < len(candidates) - 1:
            time.sleep(0.5)
    
    # Sort by score
    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    if progress_callback:
        progress_callback(f"Scan complete. {len(results)} emotional dip candidates found.")
    
    return results


if __name__ == "__main__":
    print("Running Emotional Dip scan...")
    results = run_emotional_dip_scan(lambda msg: print(msg))
    
    print("\n" + "="*60)
    print("EMOTIONAL DIP CANDIDATES (Buy by 4 PM)")
    print("="*60)
    
    for r in results[:10]:
        print(f"\n{r['ticker']} - Score: {r.get('score', 'N/A')}")
        print(f"  Price: ${r.get('price', 'N/A')} | Change: {r.get('change', 'N/A')}%")
        print(f"  Type: {r.get('dip_type', 'N/A')} | Rating: {r.get('analyst_rating', 'N/A')}")
        print(f"  Target: ${r.get('price_target', 'N/A')} | Upside: {r.get('upside_percent', 'N/A')}%")
        print(f"  Recommendation: {r.get('recommendation', 'N/A')}")
        if r.get('green_flags'):
            print(f"  + {', '.join(r['green_flags'][:3])}")
