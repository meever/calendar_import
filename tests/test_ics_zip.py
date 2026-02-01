"""
Test ICS ZIP export for iOS Files compatibility
"""

import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import zipfile
from io import BytesIO

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import Event, Location, Config
from calendar_exporter import CalendarExporter


def test_ics_zip_export():
    """Test that ZIP contains an ICS with BOM, CRLF, and required headers"""
    config = Config(
        timezone="America/New_York",
        locations=[
            Location(name="Test Pool", address="123 Main St")
        ]
    )

    tz = ZoneInfo("America/New_York")
    event = Event(
        summary="Test Practice",
        start_time=datetime(2026, 2, 15, 18, 0, tzinfo=tz),
        end_time=datetime(2026, 2, 15, 20, 0, tzinfo=tz),
        location=config.locations[0],
        raw_text="Test event"
    )

    exporter = CalendarExporter(config)
    zip_bytes = exporter.export_to_ics_zip([event], ics_filename="test.ics")

    with zipfile.ZipFile(BytesIO(zip_bytes), "r") as zf:
        assert "test.ics" in zf.namelist(), "ICS file missing from ZIP"
        ics_bytes = zf.read("test.ics")

    assert ics_bytes.startswith(b"\xef\xbb\xbf"), "ICS missing UTF-8 BOM"

    ics_content = ics_bytes.decode("utf-8-sig")
    assert "\r\n" in ics_content, "ICS missing CRLF line endings"
    assert "METHOD:PUBLISH" in ics_content, "ICS missing METHOD:PUBLISH"
    assert "X-WR-TIMEZONE:America/New_York" in ics_content, "ICS missing X-WR-TIMEZONE"
    assert "X-WR-CALNAME:Swimming Schedule" in ics_content, "ICS missing X-WR-CALNAME"


if __name__ == "__main__":
    test_ics_zip_export()