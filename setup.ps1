# RAGShield — Complete Project Setup Script
# Run this script to set up the entire RAGShield project

Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     RAGShield — Project Setup                    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ─── Backend Setup ────────────────────────────────────────────────────────────
Write-Host "📦 Setting up Python Backend..." -ForegroundColor Yellow

Set-Location backend

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "   Creating virtual environment..."
    python -m venv venv
}

# Activate
Write-Host "   Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "   Installing Python dependencies (this may take a few minutes)..."
pip install -r requirements.txt --quiet

# Copy .env if not exists
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "   ✅ Created .env file — Add your GEMINI_API_KEY!" -ForegroundColor Green
}

# Create required directories
@("data/pdfs", "data/poisoned", "data/evaluation", "vector_db", "models") | ForEach-Object {
    if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
}
Write-Host "   ✅ Backend setup complete" -ForegroundColor Green

Set-Location ..

# ─── Frontend Setup ───────────────────────────────────────────────────────────
Write-Host ""
Write-Host "⚛️  Setting up React Frontend..." -ForegroundColor Yellow

Set-Location frontend
npm install --silent
Write-Host "   ✅ Frontend setup complete" -ForegroundColor Green

Set-Location ..

# ─── Done ─────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ RAGShield is ready!                          ║" -ForegroundColor Green
Write-Host "╠══════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║                                                  ║" -ForegroundColor Green
Write-Host "║  1. Add GEMINI_API_KEY to backend/.env           ║" -ForegroundColor White
Write-Host "║  2. Start backend:  .\start_backend.ps1          ║" -ForegroundColor White
Write-Host "║  3. Start frontend: .\start_frontend.ps1         ║" -ForegroundColor White
Write-Host "║  4. Open: http://localhost:5173                  ║" -ForegroundColor White
Write-Host "║                                                  ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Green
