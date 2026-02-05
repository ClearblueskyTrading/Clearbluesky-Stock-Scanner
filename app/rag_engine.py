"""
ClearBlueSky – RAG book knowledge (ChromaDB).
Chunk trading books (.txt and .pdf), embed, and retrieve relevant excerpts for analysis.
"""

import os
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAG_DIR = Path(BASE_DIR) / "rag_store"
COLLECTION_NAME = "trading_books"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

_chroma_ok = None


def _chroma_available():
    global _chroma_ok
    if _chroma_ok is None:
        try:
            import chromadb
            _chroma_ok = True
        except ImportError:
            _chroma_ok = False
    return _chroma_ok


def _chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    text = (text or "").strip().replace("\r\n", "\n")
    while start < len(text):
        end = start + size
        chunk = text[start:end]
        if not chunk.strip():
            start = end - overlap
            continue
        chunks.append(chunk.strip())
        start = end - overlap
    return chunks


def get_client():
    """Persistent ChromaDB client. Returns None if chromadb not installed."""
    if not _chroma_available():
        return None
    try:
        import chromadb
        RAG_DIR.mkdir(parents=True, exist_ok=True)
        return chromadb.PersistentClient(path=str(RAG_DIR))
    except Exception:
        return None


def _text_from_pdf(filepath):
    """Extract plain text from a PDF file. Returns str or None on error."""
    try:
        import fitz
        doc = fitz.open(filepath)
        parts = []
        for page in doc:
            parts.append(page.get_text() or "")
        doc.close()
        return "\n".join(parts).strip() or None
    except Exception:
        return None


def build_index(books_folder, progress_callback=None):
    """
    Index all .txt and .pdf files under books_folder. Chunk and add to ChromaDB.
    progress_callback(msg) optional. Returns number of chunks added.
    """
    def progress(msg):
        if progress_callback:
            progress_callback(msg)
    client = get_client()
    if not client:
        progress("ChromaDB not installed; pip install chromadb")
        return 0
    books_folder = Path(books_folder) if books_folder else None
    if not books_folder or not books_folder.is_dir():
        progress("No books folder")
        return 0
    try:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        collection = client.create_collection(name=COLLECTION_NAME, metadata={"description": "Trading book excerpts"})
    except Exception as e:
        progress(f"ChromaDB error: {e}")
        return 0
    ids = []
    documents = []
    n = 0
    # .txt files
    for fp in sorted(books_folder.rglob("*.txt")):
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
            if not (text or "").strip():
                continue
            chunks = _chunk_text(text)
            for i, chunk in enumerate(chunks):
                doc_id = f"{fp.stem}_{n}_{i}"
                ids.append(doc_id)
                documents.append(chunk)
                n += 1
        except Exception:
            continue
    # .pdf files
    for fp in sorted(books_folder.rglob("*.pdf")):
        try:
            text = _text_from_pdf(fp)
            if not (text or "").strip():
                continue
            chunks = _chunk_text(text)
            for i, chunk in enumerate(chunks):
                doc_id = f"{fp.stem}_{n}_{i}"
                ids.append(doc_id)
                documents.append(chunk)
                n += 1
        except Exception:
            continue
    if not documents:
        progress("No .txt or .pdf chunks found")
        return 0
    try:
        collection.add(ids=ids[:10000], documents=documents[:10000])  # cap for free tier
        progress(f"Indexed {len(documents)} chunks (.txt + .pdf) from {books_folder}")
        return len(documents)
    except Exception as e:
        progress(f"Add error: {e}")
        return 0


def get_relevant_chunks(query, k=5):
    """
    Retrieve up to k most relevant chunks for query. Returns list of strings.
    If no index or chromadb, returns [].
    """
    client = get_client()
    if not client:
        return []
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
        results = collection.query(query_texts=[query], n_results=min(k, 20))
        if not results or not results.get("documents"):
            return []
        return [doc for doc in (results["documents"][0] or []) if doc]
    except Exception:
        return []


def get_rag_context_for_scan(scan_type, analysis_summary="", k=5):
    """
    Build a query from scan_type and optional summary; return formatted string of chunks
    for inclusion in system prompt. If no chunks, returns "".
    """
    query = f"{scan_type} scan technical analysis pattern setup"
    if analysis_summary:
        query = f"{query} {analysis_summary[:200]}"
    chunks = get_relevant_chunks(query, k=k)
    if not chunks:
        return ""
    return "Relevant book excerpts (use for pattern/strategy context):\n" + "\n---\n".join(chunks[:k])
