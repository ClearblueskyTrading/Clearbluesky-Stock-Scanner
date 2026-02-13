# Re-index AI Knowledge folder into scanner RAG
# Run from D:\cursor. Updates scanner/rag_store for get_relevant_chunks.

$ScannerDir = "D:\cursor\scanner"
$ReindexScript = "$ScannerDir\reindex_books.py"

if (-not (Test-Path $ReindexScript)) {
    Write-Host "reindex_books.py not found" -ForegroundColor Red
    exit 1
}

Write-Host "Re-indexing AI Knowledge..." -ForegroundColor Cyan
Write-Host "  Uses rag_books_folder from scanner/user_config.json"
Write-Host ""

Push-Location $ScannerDir
try {
    python reindex_books.py
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "If folder not found: Edit scanner/user_config.json and set rag_books_folder to your AI Knowledge path." -ForegroundColor Yellow
