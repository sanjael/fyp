# Start RAGShield Backend
Write-Host "Starting RAGShield Backend..." -ForegroundColor Cyan
Set-Location backend
& ".\venv\Scripts\Activate.ps1"
uvicorn app.main:app --reload --port 8080
