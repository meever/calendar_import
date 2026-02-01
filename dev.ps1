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
    
    Write-Host "`n" + "="*60 + "`n"
}

# Step 2: Start the app
Write-Host "Step 2: Starting Streamlit app...`n" -ForegroundColor Yellow

# Stop any existing instances
Get-Process | Where-Object {$_.ProcessName -like "*streamlit*" -or $_.ProcessName -like "*python*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Start app on local network (0.0.0.0 - accessible from 192.168.x.x)
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"} | Select-Object -First 1).IPAddress
Write-Host "✅ Launching app..." -ForegroundColor Green
Write-Host "   Local: http://localhost:8501" -ForegroundColor Cyan
Write-Host "   Network: http://$ipAddress:8501" -ForegroundColor Cyan
Write-Host "   🌐 Accessible from local network (192.168.x.x)" -ForegroundColor Yellow
Write-Host "   Press Ctrl+C to stop`n" -ForegroundColor Gray

& "D:/code/calendar_import/venv/Scripts/python.exe" -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
