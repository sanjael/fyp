# Start RAGShield Backend
Write-Host "Starting RAGShield Backend..." -ForegroundColor Cyan
Set-Location backend
& ".\venv\Scripts\Activate.ps1"
Write-Host "[OK] Backend running at http://localhost:8000" -ForegroundColor Green
Write-Host "[Docs] API Docs at http://localhost:8000/api/docs" -ForegroundColor Green
python main.py
