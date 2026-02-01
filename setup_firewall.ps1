# Windows Firewall Setup Script
# Run this as Administrator to allow network access

Write-Host "`n=== Swimming Calendar - Firewall Setup ===`n" -ForegroundColor Cyan

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "`nRight-click this file and select 'Run as Administrator'`n" -ForegroundColor Yellow
    pause
    exit 1
}

# Create firewall rule
Write-Host "Creating firewall rule for port 8501..." -ForegroundColor Yellow

try {
    # Remove old rule if exists
    Remove-NetFirewallRule -DisplayName "Swimming Calendar App" -ErrorAction SilentlyContinue
    
    # Create new rule
    New-NetFirewallRule `
        -DisplayName "Swimming Calendar App" `
        -Direction Inbound `
        -LocalPort 8501 `
        -Protocol TCP `
        -Action Allow `
        -Profile Private,Domain `
        -Description "Allow access to Swimming Schedule Converter on local network"
    
    Write-Host "`n✅ SUCCESS: Firewall rule created!" -ForegroundColor Green
    Write-Host "`nYour app is now accessible from:" -ForegroundColor Cyan
    
    # Get local IP
    $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"} | Select-Object -First 1).IPAddress
    
    if ($ip) {
        Write-Host "  - This PC:        http://localhost:8501" -ForegroundColor White
        Write-Host "  - Other devices:  http://$ip:8501" -ForegroundColor Yellow
    } else {
        Write-Host "  - This PC:        http://localhost:8501" -ForegroundColor White
        Write-Host "  - Network access enabled (run ipconfig to find your IP)" -ForegroundColor Yellow
    }
    
    Write-Host "`n📱 Try accessing from your phone/tablet!`n" -ForegroundColor Green
    
} catch {
    Write-Host "`n❌ ERROR: Failed to create firewall rule" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "`nTry manually:" -ForegroundColor Yellow
    Write-Host "  1. Open Windows Firewall settings" -ForegroundColor Gray
    Write-Host "  2. Allow port 8501 for TCP traffic`n" -ForegroundColor Gray
    exit 1
}

pause
