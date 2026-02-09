# ClearBlueSky - Trend Scanner
# Made with Claude AI

import sys
import os

# Get the directory where this script is located (portable support)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import pandas as pd
from datetime import datetime
from finvizfinance.screener.overview import Overview
from finvizfinance.screener.performance import Performance

from scan_settings import load_config

OUTPUT_DIR = os.path.join(BASE_DIR, "scans")

def trend_scan(progress_callback=None, index="sp500"):
    """
    TREND SCAN with company info and scoring
    progress_callback: function(message) for status updates
    index: 'sp500' or 'etfs'
    """
    def progress(msg):
        print(msg)
        if progress_callback:
            progress_callback(msg)
    
    index_name = "S&P 500" if index == "sp500" else "ETFs"
    progress(f"Starting Trend Scan ({index_name})...")
    
    try:
        # Get overview data (can take a minute for full index)
        progress("Fetching overview data (this may take a minute)...")
        overview = Overview()
        if index == "etfs":
            filters = {
                'Industry': 'Exchange Traded Fund',
                '200-Day Simple Moving Average': 'Price above SMA200',
                '50-Day Simple Moving Average': 'Price above SMA50',
                '20-Day Simple Moving Average': 'Price above SMA20',
                'Average Volume': 'Over 500K',
                'Price': 'Over $5'
            }
        else:
            filters = {
                'Index': 'S&P 500',
                '200-Day Simple Moving Average': 'Price above SMA200',
                '50-Day Simple Moving Average': 'Price above SMA50',
                '20-Day Simple Moving Average': 'Price above SMA20',
                'Average Volume': 'Over 500K',
                'Price': 'Over $5'
            }
        overview.set_filter(filters_dict=filters)
        df_overview = overview.screener_view()
        
        import time
        time.sleep(1.0)  # polite delay between Finviz screener calls
        progress("Fetching performance data...")
        perf = Performance()
        perf.set_filter(filters_dict=filters)
        df_perf = perf.screener_view()
        
        if df_overview is None or df_perf is None:
            progress("No results from screeners")
            return None
        
        config = load_config()
        progress(f"Merging {len(df_overview)} stocks...")
        df = pd.merge(df_overview, df_perf, on='Ticker', how='inner', suffixes=('', '_perf'))
        
        progress(f"Scoring {len(df)} candidates...")
        df = calculate_scores(df)
        df = df.sort_values('SCORE', ascending=False)
        
        # Save CSV
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filepath = os.path.join(OUTPUT_DIR, f'trend_scan_{timestamp}.csv')
        df.to_csv(filepath, index=False)
        
        progress(f"Done! {len(df)} stocks scored.")
        return df
        
    except Exception as e:
        progress(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def calculate_scores(df):
    """
    Calculate 1-100 long-term trend score.
    Heavily weights YTD/quarterly/monthly performance for sector rotation holds.
    Short-term noise (daily change) is minimal.
    """
    scores = []
    
    for _, row in df.iterrows():
        score = 0
        
        def get_pct(val):
            if pd.isna(val) or val == '-':
                return None
            try:
                if isinstance(val, str):
                    return float(val.replace('%', ''))
                # finvizfinance returns decimals (0.05 = 5%); always convert
                return float(val) * 100
            except Exception:
                return None
        
        def get_num(val):
            if pd.isna(val) or val == '-':
                return None
            try:
                if isinstance(val, str):
                    val = val.replace(',', '')
                return float(val)
            except Exception:
                return None
        
        # YEARLY / YTD PERFORMANCE (30 points) - heaviest weight for long-term
        year = get_pct(row.get('Perf Year', row.get('Perf YTD', 0)))
        if year is not None:
            if year >= 100:
                score += 30
            elif year >= 50:
                score += 25
            elif year >= 30:
                score += 20
            elif year >= 15:
                score += 15
            elif year >= 5:
                score += 10
            elif year >= 0:
                score += 5
        
        # QUARTER PERFORMANCE (25 points) - sector rotation signal
        qtr = get_pct(row.get('Perf Quart', row.get('Perf Quarter', 0)))
        if qtr is not None:
            if qtr >= 30:
                score += 25
            elif qtr >= 20:
                score += 20
            elif qtr >= 10:
                score += 15
            elif qtr >= 5:
                score += 10
            elif qtr >= 0:
                score += 5
        
        # MONTH PERFORMANCE (15 points)
        month = get_pct(row.get('Perf Month', 0))
        if month is not None:
            if month >= 15:
                score += 15
            elif month >= 10:
                score += 12
            elif month >= 5:
                score += 8
            elif month >= 0:
                score += 4
        
        # WEEK PERFORMANCE (5 points) - minor for long-term
        week = get_pct(row.get('Perf Week', 0))
        if week is not None:
            if week >= 3:
                score += 5
            elif week >= 1:
                score += 3
            elif week >= 0:
                score += 1
        
        # RELATIVE VOLUME (10 points) - institutional interest
        rel_vol = get_num(row.get('Rel Volume', row.get('Relative Volume', 0)))
        if rel_vol is not None:
            if rel_vol >= 3:
                score += 10
            elif rel_vol >= 2:
                score += 8
            elif rel_vol >= 1.5:
                score += 6
            elif rel_vol >= 1:
                score += 3
            else:
                score += 1
        
        # TODAY'S CHANGE (5 points) - minimal for long-term
        change = get_pct(row.get('Change', 0))
        if change is not None:
            if change >= 3:
                score += 5
            elif change >= 1:
                score += 3
            elif change >= 0:
                score += 2
            elif change > -2:
                score += 1
        
        # Base points for passing all MA filters (10 points)
        score += 10
        
        scores.append(min(score, 100))
    
    df['SCORE'] = scores
    return df


if __name__ == "__main__":
    trend_scan(lambda m: print(f"  >> {m}"))
