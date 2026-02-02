# ============================================================
# ClearBlueSky - Custom Watchlist Scanner
# Scan user-defined list of tickers
# ============================================================

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCHLIST_FILE = os.path.join(BASE_DIR, "watchlist.json")

try:
    import finviz
    FINVIZ_AVAILABLE = True
except ImportError:
    FINVIZ_AVAILABLE = False


def load_watchlist() -> List[str]:
    """Load watchlist from file."""
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, 'r') as f:
                data = json.load(f)
                return data.get('tickers', [])
        except:
            pass
    return []


def save_watchlist(tickers: List[str]):
    """Save watchlist to file."""
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump({
            'tickers': tickers,
            'updated': datetime.now().isoformat()
        }, f, indent=2)


def add_to_watchlist(ticker: str) -> bool:
    """Add a ticker to the watchlist."""
    ticker = ticker.upper().strip()
    if not ticker:
        return False

    tickers = load_watchlist()
    if ticker not in tickers:
        tickers.append(ticker)
        save_watchlist(tickers)
        return True
    return False


def remove_from_watchlist(ticker: str) -> bool:
    """Remove a ticker from the watchlist."""
    ticker = ticker.upper().strip()
    tickers = load_watchlist()
    if ticker in tickers:
        tickers.remove(ticker)
        save_watchlist(tickers)
        return True
    return False


def clear_watchlist():
    """Clear all tickers from watchlist."""
    save_watchlist([])


def analyze_ticker(ticker: str) -> Dict:
    """
    Analyze a single ticker and return comprehensive data.
    """
    result = {
        'ticker': ticker,
        'score': 50,  # Start neutral
        'price': 'N/A',
        'change': 'N/A',
        'volume': 'N/A',
        'rel_volume': 'N/A',
        'company': ticker,
        'sector': 'N/A',
        'industry': 'N/A',
        'market_cap': 'N/A',
        'pe': 'N/A',
        'target': 'N/A',
        'rsi': 'N/A',
        'sma50': 'N/A',
        'sma200': 'N/A',
        'short_float': 'N/A',
        'short_ratio': 'N/A',
        'earnings': 'N/A',
        'recom': 'N/A',
        'green_flags': [],
        'red_flags': [],
        'analysis_notes': [],
    }

    if not FINVIZ_AVAILABLE:
        result['red_flags'].append('Finviz not available')
        return result

    try:
        quote = finviz.get_stock(ticker)
        if not quote:
            result['red_flags'].append('No data available')
            return result

        # Basic data
        result['price'] = quote.get('Price', 'N/A')
        result['change'] = quote.get('Change', 'N/A')
        result['volume'] = quote.get('Volume', 'N/A')
        result['rel_volume'] = quote.get('Rel Volume', 'N/A')
        result['company'] = quote.get('Company', ticker)
        result['sector'] = quote.get('Sector', 'N/A')
        result['industry'] = quote.get('Industry', 'N/A')
        result['market_cap'] = quote.get('Market Cap', 'N/A')
        result['pe'] = quote.get('P/E', 'N/A')
        result['target'] = quote.get('Target Price', 'N/A')
        result['rsi'] = quote.get('RSI (14)', 'N/A')
        result['sma50'] = quote.get('SMA50', 'N/A')
        result['sma200'] = quote.get('SMA200', 'N/A')
        result['short_float'] = quote.get('Short Float', 'N/A')
        result['short_ratio'] = quote.get('Short Ratio', 'N/A')
        result['earnings'] = quote.get('Earnings', 'N/A')
        result['recom'] = quote.get('Recom', 'N/A')

        # === SCORING ===

        # Price change today
        change = quote.get('Change', '')
        if change and change != '-':
            try:
                change_val = float(change.replace('%', ''))
                if change_val >= 3:
                    result['green_flags'].append(f'Strong day: +{change_val:.1f}%')
                    result['score'] += 10
                elif change_val >= 1:
                    result['green_flags'].append(f'Positive day: +{change_val:.1f}%')
                    result['score'] += 5
                elif change_val <= -3:
                    result['red_flags'].append(f'Down big: {change_val:.1f}%')
                    result['score'] -= 5
            except:
                pass

        # RSI analysis
        rsi = quote.get('RSI (14)', '')
        if rsi and rsi != '-':
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
            except:
                pass

        # SMA analysis
        sma50 = quote.get('SMA50', '')
        sma200 = quote.get('SMA200', '')
        if sma50 and sma200 and sma50 != '-' and sma200 != '-':
            try:
                sma50_pct = float(sma50.replace('%', ''))
                sma200_pct = float(sma200.replace('%', ''))

                if sma50_pct > 0 and sma200_pct > 0:
                    result['green_flags'].append('Above SMA50 & SMA200')
                    result['score'] += 15
                elif sma200_pct > 0:
                    result['green_flags'].append('Above SMA200')
                    result['score'] += 10
                elif sma200_pct < -10:
                    result['red_flags'].append('Well below SMA200')
                    result['score'] -= 10
            except:
                pass

        # Analyst rating
        recom = quote.get('Recom', '')
        if recom and recom != '-':
            try:
                recom_val = float(recom)
                if recom_val <= 1.5:
                    result['green_flags'].append('Strong Buy rating')
                    result['score'] += 15
                elif recom_val <= 2.0:
                    result['green_flags'].append('Buy rating')
                    result['score'] += 10
                elif recom_val >= 4.0:
                    result['red_flags'].append('Sell rating')
                    result['score'] -= 15
            except:
                pass

        # Price target upside
        target = quote.get('Target Price', '')
        price = quote.get('Price', '')
        if target and price and target != '-' and price != '-':
            try:
                target_val = float(target)
                price_val = float(price)
                upside = ((target_val - price_val) / price_val) * 100

                if upside >= 30:
                    result['green_flags'].append(f'High upside: {upside:.0f}%')
                    result['score'] += 15
                elif upside >= 15:
                    result['green_flags'].append(f'Good upside: {upside:.0f}%')
                    result['score'] += 10
                elif upside < 0:
                    result['red_flags'].append(f'Below target: {upside:.0f}%')
                    result['score'] -= 5
            except:
                pass

        # Relative volume
        rel_vol = quote.get('Rel Volume', '')
        if rel_vol and rel_vol != '-':
            try:
                rv_val = float(rel_vol)
                if rv_val >= 2:
                    result['analysis_notes'].append(f'High volume: {rv_val:.1f}x average')
                elif rv_val >= 1.5:
                    result['analysis_notes'].append(f'Above avg volume: {rv_val:.1f}x')
            except:
                pass

        # Short interest
        short_float = quote.get('Short Float', '')
        if short_float and short_float != '-':
            try:
                sf_val = float(short_float.replace('%', ''))
                if sf_val >= 20:
                    result['red_flags'].append(f'High short interest: {sf_val:.1f}%')
                elif sf_val >= 10:
                    result['analysis_notes'].append(f'Elevated short interest: {sf_val:.1f}%')
            except:
                pass

        # Cap score at 0-100
        result['score'] = max(0, min(100, result['score']))

    except Exception as e:
        result['red_flags'].append(f'Error: {str(e)}')

    return result


def scan_watchlist(progress_callback=None) -> List[Dict]:
    """
    Scan all tickers in the watchlist.
    Returns list of analyzed stocks sorted by score.
    """
    def progress(msg):
        print(msg)
        if progress_callback:
            progress_callback(msg)

    tickers = load_watchlist()

    if not tickers:
        progress("Watchlist is empty. Add tickers first!")
        return []

    progress(f"Scanning {len(tickers)} watchlist stocks...")

    results = []
    for i, ticker in enumerate(tickers):
        progress(f"Analyzing {ticker} ({i+1}/{len(tickers)})...")

        result = analyze_ticker(ticker)
        results.append(result)

        # Rate limiting
        if i < len(tickers) - 1:
            time.sleep(0.3)

    # Sort by score
    results.sort(key=lambda x: x.get('score', 0), reverse=True)

    progress(f"Watchlist scan complete. {len(results)} stocks analyzed.")
    return results


# Testing
if __name__ == "__main__":
    # Test with some tickers
    test_tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
    save_watchlist(test_tickers)

    results = scan_watchlist(print)

    print("\n" + "="*60)
    print("WATCHLIST SCAN RESULTS")
    print("="*60)

    for r in results:
        print(f"\n{r['ticker']} - Score: {r['score']}")
        print(f"  Price: ${r['price']} | Change: {r['change']}")
        print(f"  RSI: {r['rsi']} | Target: ${r['target']}")
        if r['green_flags']:
            print(f"  + {', '.join(r['green_flags'])}")
        if r['red_flags']:
            print(f"  - {', '.join(r['red_flags'])}")
