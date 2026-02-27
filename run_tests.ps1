# Run tests for the swimming schedule converter
# Default: non-API tests only (quota-safe)

param(
    [switch]$Full,
    [switch]$ApiOnly
)

Write-Host "`n=== Swimming Schedule Converter Test Suite ===" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ForegroundColor Gray

if (Test-Path "D:/code/calendar_import/.venv/Scripts/python.exe") {
    $python = "D:/code/calendar_import/.venv/Scripts/python.exe"
} elseif (Test-Path "D:/code/calendar_import/venv/Scripts/python.exe") {
    $python = "D:/code/calendar_import/venv/Scripts/python.exe"
} else {
    $python = "python"
}

# Ensure pytest is available in the selected environment
& $python -m pytest --version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "pytest not found in environment. Installing dependencies from requirements.txt..." -ForegroundColor Yellow
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n❌ Failed to install dependencies." -ForegroundColor Red
        Write-Host "Run: $python -m pip install -r requirements.txt" -ForegroundColor Gray
        exit 1
    }

    & $python -m pytest --version *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n❌ pytest is still unavailable after install." -ForegroundColor Red
        Write-Host "Run: $python -m pip install pytest" -ForegroundColor Gray
        exit 1
    }
}

if ($ApiOnly) {
    Write-Host "Running API tests only..." -ForegroundColor Yellow
    & $python -m pytest -m "api" tests
} elseif ($Full) {
    Write-Host "Running full test suite (includes API tests)..." -ForegroundColor Yellow
    & $python -m pytest tests
} else {
    Write-Host "Running non-API tests only (quota-safe default)..." -ForegroundColor Yellow
    & $python -m pytest -m "not api" tests
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Test run failed!" -ForegroundColor Red
    exit 1
}

Write-Host ("`n" + ("=" * 60))
Write-Host "`n✅ TESTS PASSED!" -ForegroundColor Green
Write-Host "Use -Full to include API tests, or -ApiOnly for API-only checks.`n" -ForegroundColor Gray
