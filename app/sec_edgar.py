"""
ClearBlueSky – SEC EDGAR insider context (10b5-1 plan vs discretionary).
Fetches company CIK, recent Form 4 filings, and checks for 10b5-1 plan language.
"""

import re
import time

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

SEC_HEADERS = {"User-Agent": "ClearBlueSky Stock Scanner contact@example.com"}
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"

_tickers_cache = None


def _get_cik(ticker):
    """Resolve ticker to 10-digit zero-padded CIK. Returns None if not found."""
    global _tickers_cache
    if not REQUESTS_AVAILABLE:
        return None
    ticker = (ticker or "").strip().upper()
    if not ticker:
        return None
    try:
        if _tickers_cache is None:
            r = requests.get(COMPANY_TICKERS_URL, headers=SEC_HEADERS, timeout=15)
            r.raise_for_status()
            data = r.json()
            _tickers_cache = {str(v.get("ticker", "")).upper(): v.get("cik_str") for v in (data or {}).values() if v.get("ticker")}
        cik = _tickers_cache.get(ticker)
        if cik is not None:
            return str(cik).zfill(10)
        return None
    except Exception:
        return None


def _get_recent_form4(cik):
    """Get most recent Form 4 accession and primary document for CIK. Returns (accession, primary_doc) or (None, None)."""
    if not REQUESTS_AVAILABLE or not cik:
        return None, None
    try:
        url = SUBMISSIONS_URL.format(cik=cik)
        r = requests.get(url, headers=SEC_HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        filings = data.get("filings") or {}
        recent = filings.get("recent") or {}
        forms = recent.get("form") or []
        accessions = recent.get("accessionNumber") or []
        primaries = recent.get("primaryDocument") or []
        for i, form in enumerate(forms):
            if form and str(form).strip().upper() == "4":
                acc = accessions[i] if i < len(accessions) else None
                prim = primaries[i] if i < len(primaries) else None
                if acc and prim:
                    return acc, prim
        return None, None
    except Exception:
        return None, None


def _fetch_filing_content(accession, primary_doc, cik):
    """Fetch primary document content. Returns text or None."""
    if not REQUESTS_AVAILABLE or not accession or not primary_doc:
        return None
    try:
        acc_clean = accession.replace("-", "")
        cik_num = str(int(cik)) if cik else "0"
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{acc_clean}/{primary_doc}"
        r = requests.get(url, headers=SEC_HEADERS, timeout=15)
        r.raise_for_status()
        return r.text or ""
    except Exception:
        return None


def get_insider_10b5_1_context(ticker):
    """
    For a ticker, check most recent Form 4 filing for 10b5-1 plan language.
    Returns dict: is_10b5_1_plan (bool or None), insider_context ("10b5-1 plan" | "Discretionary" | "Unknown").
    """
    out = {"is_10b5_1_plan": None, "insider_context": "Unknown"}
    if not REQUESTS_AVAILABLE:
        return out
    try:
        cik = _get_cik(ticker)
        if not cik:
            return out
        time.sleep(0.2)
        accession, primary_doc = _get_recent_form4(cik)
        if not accession or not primary_doc:
            return out
        time.sleep(0.2)
        content = _fetch_filing_content(accession, primary_doc, cik)
        if not content:
            return out
        content_lower = content.lower()
        if re.search(r"10b5-1|10b5\u20131|rule\s*10b5-1|rule\s*10b5\u20131", content_lower):
            out["is_10b5_1_plan"] = True
            out["insider_context"] = "10b5-1 plan"
        else:
            out["is_10b5_1_plan"] = False
            out["insider_context"] = "Discretionary"
    except Exception:
        pass
    return out
