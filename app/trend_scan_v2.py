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
    index: 'sp500' or 'russell2000'
    """
    def progress(msg):
        print(msg)
        if progress_callback:
            progress_callback(msg)
    
    index_name = "S&P 500" if index == "sp500" else "Russell 2000"
    progress(f"Starting Trend Scan ({index_name})...")
    
    try:
        # Get overview data
        progress("Fetching overview data...")
        overview = Overview()
        filters = {
            'Index': 'S&P 500' if index == "sp500" else 'RUSSELL 2000',
            '200-Day Simple Moving Average': 'Price above SMA200',
            '50-Day Simple Moving Average': 'Price above SMA50',
            '20-Day Simple Moving Average': 'Price above SMA20',
            'Average Volume': 'Over 500K',
            'Price': 'Over $5'
        }
        overview.set_filter(filters_dict=filters)
        df_overview = overview.screener_view()
        
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
    """Calculate 1-100 trend score"""
    scores = []
    
    for _, row in df.iterrows():
        score = 0
        
        def get_pct(val):
            if pd.isna(val) or val == '-':
                return None
            try:
                if isinstance(val, str):
                    return float(val.replace('%', ''))
                return float(val) * 100 if abs(float(val)) < 1 else float(val)
            except:
                return None
        
        def get_num(val):
            if pd.isna(val) or val == '-':
                return None
            try:
                if isinstance(val, str):
                    val = val.replace(',', '')
                return float(val)
            except:
                return None
        
        # QUARTER PERFORMANCE (25 points)
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
        
        # MONTH PERFORMANCE (20 points)
        month = get_pct(row.get('Perf Month', 0))
        if month is not None:
            if month >= 15:
                score += 20
            elif month >= 10:
                score += 15
            elif month >= 5:
                score += 10
            elif month >= 0:
                score += 5
        
        # WEEK PERFORMANCE (10 points)
        week = get_pct(row.get('Perf Week', 0))
        if week is not None:
            if week >= 5:
                score += 10
            elif week >= 2:
                score += 8
            elif week >= 0:
                score += 4
        
        # RELATIVE VOLUME (15 points)
        rel_vol = get_num(row.get('Rel Volume', row.get('Relative Volume', 0)))
        if rel_vol is not None:
            if rel_vol >= 3:
                score += 15
            elif rel_vol >= 2:
                score += 12
            elif rel_vol >= 1.5:
                score += 8
            elif rel_vol >= 1:
                score += 5
            else:
                score += 2
        
        # TODAY'S CHANGE (10 points)
        change = get_pct(row.get('Change', 0))
        if change is not None:
            if change >= 5:
                score += 10
            elif change >= 2:
                score += 8
            elif change >= 0:
                score += 5
            elif change > -2:
                score += 2
        
        # YEARLY PERFORMANCE (10 points bonus)
        year = get_pct(row.get('Perf Year', row.get('Perf YTD', 0)))
        if year is not None:
            if year >= 100:
                score += 10
            elif year >= 50:
                score += 7
            elif year >= 25:
                score += 5
            elif year >= 0:
                score += 2
        
        # Base points for passing all MA filters (10 points)
        score += 10
        
        scores.append(min(score, 100))
    
    df['SCORE'] = scores
    return df


if __name__ == "__main__":
    trend_scan(lambda m: print(f"  >> {m}"))
