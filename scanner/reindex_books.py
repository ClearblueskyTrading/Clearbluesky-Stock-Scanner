#!/usr/bin/env python3
"""Re-index AI Knowledge from rag_books_folder into ChromaDB. Run from scanner dir."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

# Common locations (D:\cursor\AI_Knowledge is the project drop folder)
FALLBACK_PATHS = [
    Path(__file__).resolve().parent.parent / "AI_Knowledge",  # D:\cursor\AI_Knowledge
    Path.home() / "OneDrive" / "Desktop" / "Claude AI Knowledge",
    Path.home() / "Desktop" / "Claude AI Knowledge",
]

def main():
    from scan_settings import load_config
    from rag_engine import build_index
    
    config = load_config() or {}
    folder = config.get("rag_books_folder", "").strip()
    path = Path(folder) if folder else None
    
    if not path or not path.is_dir():
        for p in FALLBACK_PATHS:
            if p.exists() and p.is_dir():
                path = p
                print(f"Using fallback: {path}")
                break
    
    if not path or not path.is_dir():
        print("No AI Knowledge folder found.")
        print("Set rag_books_folder in scanner/user_config.json to your AI Knowledge path.")
        print("Example: \"rag_books_folder\": \"C:\\\\Users\\\\You\\\\Desktop\\\\AI_Knowledge\"")
        return 1
    
    def progress(msg):
        print(msg)
    
    try:
        n = build_index(str(path), progress_callback=progress)
        print(f"Done. {n} chunks indexed.")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        if "chroma" in str(e).lower() or "pydantic" in str(e).lower():
            print("Tip: ChromaDB may have Python 3.14 issues. Try: py -3.12 reindex_books.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())
