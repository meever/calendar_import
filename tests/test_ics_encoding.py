"""Test ICS file encoding for iOS compatibility."""

import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from calendar_exporter import CalendarExporter
from models import Config, Event, Location


def test_ics_encoding() -> None:
    config = Config(timezone="America/New_York")
    config.add_location(Location(name="Test Pool", address="123 Main St"))

    tz = ZoneInfo("America/New_York")
    event = Event(
        summary="Test Practice",
        start_time=datetime(2026, 2, 15, 18, 0, tzinfo=tz),
        end_time=datetime(2026, 2, 15, 20, 0, tzinfo=tz),
        location=config.locations["Test Pool"],
        raw_text="Test event",
    )

    exporter = CalendarExporter(config)
    ics_content = exporter.export_to_ics([event])
    ics_bytes = ics_content.encode("utf-8-sig")

    assert ics_bytes.startswith(b"\xef\xbb\xbf")
    assert "\r\n" in ics_content
    assert "X-WR-CALNAME:Swimming Schedule" in ics_content
    assert "METHOD:PUBLISH" in ics_content
    assert "X-WR-TIMEZONE:America/New_York" in ics_content
    assert "DTSTAMP:" in ics_content

    vevent_match = re.search(r"BEGIN:VEVENT.*?END:VEVENT", ics_content, re.DOTALL)
    assert vevent_match and "DTSTAMP:" in vevent_match.group(0)

    test_file = Path(__file__).parent.parent / "output" / "test_ios.ics"
    exporter.export_to_ics([event], str(test_file))

    with open(test_file, "rb") as file_pointer:
        raw_bytes = file_pointer.read()

    assert raw_bytes.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" in raw_bytes

    test_file.unlink(missing_ok=True)
