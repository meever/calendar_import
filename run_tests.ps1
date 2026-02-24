# Run all tests for the swimming schedule converter
# Exit on first failure

Write-Host "`n=== Swimming Schedule Converter Test Suite ===" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ForegroundColor Gray

if (Test-Path "D:/code/calendar_import/.venv/Scripts/python.exe") {
    $python = "D:/code/calendar_import/.venv/Scripts/python.exe"
} elseif (Test-Path "D:/code/calendar_import/venv/Scripts/python.exe") {
    $python = "D:/code/calendar_import/venv/Scripts/python.exe"
} else {
    $python = "python"
}

# Test 1: API Key Validation
Write-Host "[1/8] Testing API Key..." -ForegroundColor Yellow
& $python tests/test_api.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ API Key test failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n" + "="*60 + "`n"

# Test 2: Event Extraction
Write-Host "[2/8] Testing Event Extraction..." -ForegroundColor Yellow
& $python tests/test_extraction.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Event extraction test failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n" + "="*60 + "`n"

# Test 3: Combined Sessions Extension
Write-Host "[3/8] Testing Combined Session Handling..." -ForegroundColor Yellow
& $python tests/test_combined_sessions.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Combined session test failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n" + "="*60 + "`n"

# Test 4: ICS Encoding (iOS Compatibility)
Write-Host "[4/8] Testing ICS Encoding for iOS..." -ForegroundColor Yellow
& $python tests/test_ics_encoding.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "\n❌ ICS encoding test failed!" -ForegroundColor Red
    exit 1
}

Write-Host "\n" + "="*60 + "\n"

# Test 5: ICS ZIP Packaging
Write-Host "[5/8] Testing ICS ZIP Packaging..." -ForegroundColor Yellow
& $python tests/test_ics_zip.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "\n❌ ICS ZIP test failed!" -ForegroundColor Red
    exit 1
}

Write-Host "\n" + "="*60 + "\n"

# Test 6: End-to-End Test
Write-Host "[6/8] Running End-to-End Test..." -ForegroundColor Yellow
& $python tests/test_e2e.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ End-to-end test failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n" + "="*60 + "`n"

# Test 7: Shared Calendars Unit
Write-Host "[7/8] Testing Shared Calendar CRUD..." -ForegroundColor Yellow
& $python tests/test_shared_calendars.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Shared calendar CRUD test failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n" + "="*60 + "`n"

# Test 8: Shared Calendars E2E
Write-Host "[8/8] Testing Shared Calendar Workflow E2E..." -ForegroundColor Yellow
& $python tests/test_shared_calendar_e2e.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Shared calendar E2E test failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n" + "="*60
Write-Host "`n✅ ALL TESTS PASSED!" -ForegroundColor Green
Write-Host "Ready to deploy.`n" -ForegroundColor Gray
