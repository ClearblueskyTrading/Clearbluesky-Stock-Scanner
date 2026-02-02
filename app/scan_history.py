# ============================================================
# ClearBlueSky - Scan History Module
# Track scan history and export to CSV
# ============================================================

import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "scan_history.json")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")


def load_history() -> List[Dict]:
    """Load scan history from file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                data = json.load(f)
                return data.get('scans', [])
        except:
            pass
    return []


def save_history(scans: List[Dict]):
    """Save scan history to file."""
    # Keep only last 100 scans
    scans = scans[-100:]
    with open(HISTORY_FILE, 'w') as f:
        json.dump({
            'scans': scans,
            'updated': datetime.now().isoformat()
        }, f, indent=2)


def add_scan_to_history(scan_type: str, results: List[Dict], index: str = None,
                        elapsed_time: int = 0, filters: Dict = None):
    """
    Add a scan result to history.

    Args:
        scan_type: 'Trend', 'Swing', 'Watchlist'
        results: List of result dicts
        index: 'sp500', 'russell2000', or None for watchlist
        elapsed_time: Scan duration in seconds
        filters: Active filters used
    """
    history = load_history()

    # Extract top tickers for summary
    top_tickers = []
    for r in results[:5]:
        ticker = r.get('Ticker', r.get('ticker', ''))
        score = r.get('SCORE', r.get('Score', r.get('score', 0)))
        if ticker:
            top_tickers.append({'ticker': ticker, 'score': score})

    scan_record = {
        'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
        'timestamp': datetime.now().isoformat(),
        'type': scan_type,
        'index': index,
        'result_count': len(results),
        'elapsed_time': elapsed_time,
        'top_tickers': top_tickers,
        'filters': filters or {},
    }

    history.append(scan_record)
    save_history(history)

    return scan_record['id']


def get_recent_scans(limit: int = 20) -> List[Dict]:
    """Get recent scan history."""
    history = load_history()
    return history[-limit:][::-1]  # Most recent first


def get_scan_by_id(scan_id: str) -> Optional[Dict]:
    """Get a specific scan by ID."""
    history = load_history()
    for scan in history:
        if scan.get('id') == scan_id:
            return scan
    return None


def clear_history():
    """Clear all scan history."""
    save_history([])


def export_results_to_csv(results: List[Dict], scan_type: str,
                          filename: str = None) -> str:
    """
    Export scan results to CSV file.

    Args:
        results: List of result dicts
        scan_type: Type of scan for filename
        filename: Optional custom filename

    Returns:
        Path to exported file
    """
    # Ensure export directory exists
    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)

    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{scan_type}_Export_{timestamp}.csv"

    filepath = os.path.join(EXPORT_DIR, filename)

    # Determine columns from results
    if not results:
        return None

    # Get all unique keys from results
    all_keys = set()
    for r in results:
        all_keys.update(r.keys())

    # Define preferred column order
    preferred_order = [
        'ticker', 'Ticker',
        'score', 'Score', 'SCORE',
        'company', 'Company',
        'price', 'Price',
        'change', 'Change',
        'volume', 'Volume',
        'rel_volume', 'Rel Volume',
        'sector', 'Sector',
        'industry', 'Industry',
        'rsi', 'RSI (14)',
        'target', 'Target Price',
        'pe', 'P/E',
        'market_cap', 'Market Cap',
        'short_float', 'Short Float',
        'recom', 'Recom',
        'recommendation',
        'dip_type',
        'earnings_date',
        'green_flags',
        'red_flags',
    ]

    # Order columns: preferred first, then alphabetically
    columns = []
    for col in preferred_order:
        if col in all_keys:
            columns.append(col)
            all_keys.discard(col)
    columns.extend(sorted(all_keys))

    # Write CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()

        for result in results:
            # Convert lists to strings for CSV
            row = {}
            for key, value in result.items():
                if isinstance(value, list):
                    row[key] = '; '.join(str(v) for v in value)
                else:
                    row[key] = value
            writer.writerow(row)

    return filepath


def export_history_to_csv(filename: str = None) -> str:
    """
    Export scan history summary to CSV.

    Returns:
        Path to exported file
    """
    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)

    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Scan_History_{timestamp}.csv"

    filepath = os.path.join(EXPORT_DIR, filename)
    history = load_history()

    if not history:
        return None

    columns = ['id', 'timestamp', 'type', 'index', 'result_count',
               'elapsed_time', 'top_tickers']

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()

        for scan in history:
            row = scan.copy()
            # Format top tickers
            top = scan.get('top_tickers', [])
            row['top_tickers'] = ', '.join([f"{t['ticker']}({t['score']})" for t in top])
            writer.writerow(row)

    return filepath


def get_export_dir() -> str:
    """Get the exports directory path."""
    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)
    return EXPORT_DIR


# Testing
if __name__ == "__main__":
    # Add some test data
    test_results = [
        {'ticker': 'AAPL', 'score': 85, 'price': '150.00', 'change': '+2.5%'},
        {'ticker': 'MSFT', 'score': 82, 'price': '310.00', 'change': '+1.8%'},
        {'ticker': 'GOOGL', 'score': 78, 'price': '125.00', 'change': '+1.2%'},
    ]

    # Add to history
    scan_id = add_scan_to_history('Trend', test_results, 'sp500', 45)
    print(f"Added scan: {scan_id}")

    # Export to CSV
    csv_path = export_results_to_csv(test_results, 'Trend')
    print(f"Exported to: {csv_path}")

    # Show history
    print("\nRecent scans:")
    for scan in get_recent_scans(5):
        print(f"  {scan['timestamp']}: {scan['type']} - {scan['result_count']} results")
