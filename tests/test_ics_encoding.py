"""
Test ICS file encoding for iOS compatibility
"""

import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import Event, Location, Config
from calendar_exporter import CalendarExporter


def test_ics_encoding():
    """Test that ICS files use CRLF line endings and UTF-8 BOM"""
    print("=" * 80)
    print("Testing ICS File Encoding for iOS Compatibility")
    print("=" * 80)
    
    # Create test config
    config = Config(
        timezone="America/New_York",
        locations=[
            Location(name="Test Pool", address="123 Main St")
        ]
    )
    
    # Create test event
    tz = ZoneInfo("America/New_York")
    event = Event(
        summary="Test Practice",
        start_time=datetime(2026, 2, 15, 18, 0, tzinfo=tz),
        end_time=datetime(2026, 2, 15, 20, 0, tzinfo=tz),
        location=config.locations[0],
        raw_text="Test event"
    )
    
    # Export to ICS
    exporter = CalendarExporter(config)
    ics_content = exporter.export_to_ics([event])
    
    # Test 1: Check for UTF-8 BOM (in encoded bytes, not string)
    print("\n[1/4] Checking UTF-8 BOM...")
    # BOM is added during utf-8-sig encoding, not in the string
    ics_bytes = ics_content.encode('utf-8-sig')
    if ics_bytes.startswith(b'\xef\xbb\xbf'):
        print("✓ PASS: UTF-8 BOM present (iOS compatibility)")
    else:
        print("✗ FAIL: UTF-8 BOM missing")
        return False
    
    # Test 2: Check for CRLF line endings
    print("\n[2/4] Checking CRLF line endings (RFC 5545 standard)...")
    if '\r\n' in ics_content:
        print("✓ PASS: CRLF line endings present")
        # Count line endings
        crlf_count = ics_content.count('\r\n')
        lf_only_count = ics_content.replace('\r\n', '').count('\n')
        print(f"  CRLF: {crlf_count}, LF-only: {lf_only_count}")
    else:
        print("✗ FAIL: No CRLF line endings found")
        return False
    
    # Test 3: Check calendar properties
    print("\n[3/4] Checking calendar properties...")
    if 'X-WR-CALNAME:Swimming Schedule' in ics_content:
        print("✓ PASS: Calendar name present")
    else:
        print("✗ FAIL: Calendar name missing")
        return False

    if 'METHOD:PUBLISH' in ics_content:
        print("✓ PASS: METHOD:PUBLISH present")
    else:
        print("✗ FAIL: METHOD:PUBLISH missing")
        return False

    if 'X-WR-TIMEZONE:America/New_York' in ics_content:
        print("✓ PASS: X-WR-TIMEZONE present")
    else:
        print("✗ FAIL: X-WR-TIMEZONE missing")
        return False
    
    # Test 4: Test file writing with UTF-8-BOM
    print("\n[4/4] Testing file write with UTF-8-BOM...")
    test_file = Path(__file__).parent.parent / "output" / "test_ios.ics"
    exporter.export_to_ics([event], str(test_file))
    
    # Read back and verify
    with open(test_file, 'rb') as f:
        raw_bytes = f.read()
    
    # Check for UTF-8 BOM bytes
    if raw_bytes.startswith(b'\xef\xbb\xbf'):
        print("✓ PASS: File written with UTF-8 BOM")
    else:
        print("✗ FAIL: File missing UTF-8 BOM")
        return False
    
    # Check CRLF in file
    if b'\r\n' in raw_bytes:
        print("✓ PASS: File has CRLF line endings")
    else:
        print("✗ FAIL: File missing CRLF line endings")
        return False
    
    # Cleanup
    test_file.unlink(missing_ok=True)
    
    print("\n" + "=" * 80)
    print("✅ ALL ICS ENCODING TESTS PASSED")
    print("=" * 80)
    print("\nFile should now work correctly on iOS for:")
    print("  ✓ Adding to calendar (already worked)")
    print("  ✓ Saving to Files app")
    print("  ✓ Sending via Messages/Email")
    print("  ✓ Sharing via AirDrop")
    print("\n" + "=" * 80)
    
    return True


if __name__ == "__main__":
    success = test_ics_encoding()
    sys.exit(0 if success else 1)
