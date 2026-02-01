# Run all tests for the swimming schedule converter
# Exit on first failure

Write-Host "`n=== Swimming Schedule Converter Test Suite ===" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ForegroundColor Gray

# Test 1: API Key Validation
Write-Host "[1/6] Testing API Key..." -ForegroundColor Yellow
& "D:/code/calendar_import/venv/Scripts/python.exe" tests/test_api.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ API Key test failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n" + "="*60 + "`n"

# Test 2: Event Extraction
Write-Host "[2/6] Testing Event Extraction..." -ForegroundColor Yellow
& "D:/code/calendar_import/venv/Scripts/python.exe" tests/test_extraction.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Event extraction test failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n" + "="*60 + "`n"

# Test 3: Combined Sessions Extension
Write-Host "[3/6] Testing Combined Session Extension (30-min rule)..." -ForegroundColor Yellow
& "D:/code/calendar_import/venv/Scripts/python.exe" tests/test_combined_sessions.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Combined session test failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n" + "="*60 + "`n"

# Test 4: Cache Functionality
Write-Host "[4/6] Testing Cache Functionality..." -ForegroundColor Yellow
& "D:/code/calendar_import/venv/Scripts/python.exe" tests/test_cache.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Cache test failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n" + "="*60 + "`n"

# Test 5: ICS Encoding (iOS Compatibility)
Write-Host "[5/6] Testing ICS Encoding for iOS..." -ForegroundColor Yellow
& "D:/code/calendar_import/venv/Scripts/python.exe" tests/test_ics_encoding.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "\n❌ ICS encoding test failed!" -ForegroundColor Red
    exit 1
}

Write-Host "\n" + "="*60 + "\n"

# Test 6: End-to-End Test
Write-Host "[6/6] Running End-to-End Test..." -ForegroundColor Yellow
& "D:/code/calendar_import/venv/Scripts/python.exe" tests/test_e2e.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ End-to-end test failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n" + "="*60
Write-Host "`n✅ ALL TESTS PASSED!" -ForegroundColor Green
Write-Host "Ready to deploy.`n" -ForegroundColor Gray
