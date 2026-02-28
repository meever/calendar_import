# Restart Streamlit App - Ensures .env is reloaded

Write-Host "`nStopping any running Streamlit/Python processes..." -ForegroundColor Yellow

# Stop all streamlit and python processes
Get-Process | Where-Object {$_.ProcessName -like "*streamlit*" -or $_.ProcessName -like "*python*"} | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

Write-Host "Starting Streamlit app..." -ForegroundColor Green
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*"} | Select-Object -First 1).IPAddress
if ($ipAddress) {
    Write-Host "Local: http://localhost:8501" -ForegroundColor Cyan
    Write-Host "Network: http://$($ipAddress):8501" -ForegroundColor Cyan
} else {
    Write-Host "Local: http://localhost:8501" -ForegroundColor Cyan
}
Write-Host "🌐 Accessible from local network (192.168.x.x)`n" -ForegroundColor Yellow

$projectRoot = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$venvPython = Join-Path $projectRoot ".venv/Scripts/python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

if ($python -eq "python") {
    Write-Host "Warning: .venv not found at $venvPython. Falling back to PATH python." -ForegroundColor Yellow
}

# Start in background on all interfaces (0.0.0.0)
Start-Process -FilePath $python -ArgumentList "-m", "streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501" -WorkingDirectory $projectRoot -WindowStyle Hidden

Write-Host "✅ App restarted! Opening browser..." -ForegroundColor Green
Start-Sleep -Seconds 3
Start-Process "http://localhost:8501"
