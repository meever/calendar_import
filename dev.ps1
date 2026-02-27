# Development Workflow Script
# Run tests, then start the app

param(
    [switch]$SkipTests
)

Write-Host "`n🏊 Swimming Schedule Converter - Dev Workflow`n" -ForegroundColor Cyan

# Step 1: Run tests (unless skipped)
if (-not $SkipTests) {
    Write-Host "Step 1: Running tests..." -ForegroundColor Yellow
    & ".\run_tests.ps1"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n❌ Tests failed! Fix errors before running app." -ForegroundColor Red
        exit 1
    }
    
    Write-Host ("`n" + ("=" * 60) + "`n")
}

# Step 2: Start the app
Write-Host "Step 2: Starting Streamlit app...`n" -ForegroundColor Yellow

if (Test-Path "D:/code/calendar_import/.venv/Scripts/python.exe") {
    $python = "D:/code/calendar_import/.venv/Scripts/python.exe"
} elseif (Test-Path "D:/code/calendar_import/venv/Scripts/python.exe") {
    $python = "D:/code/calendar_import/venv/Scripts/python.exe"
} else {
    $python = "python"
}

# Stop any existing instances
Get-Process | Where-Object {$_.ProcessName -like "*streamlit*" -or $_.ProcessName -like "*python*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Start app on localhost only
Write-Host "✅ Launching app..." -ForegroundColor Green
Write-Host "   Local: http://localhost:8501" -ForegroundColor Cyan
Write-Host "   🔒 Localhost only (127.0.0.1)" -ForegroundColor Yellow
Write-Host "   Press Ctrl+C to stop`n" -ForegroundColor Gray

& $python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
