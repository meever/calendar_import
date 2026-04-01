"""Tests for ICS and ZIP export (encoding, headers, iOS compatibility)."""

import re
from datetime import datetime
from pathlib import Path
from io import BytesIO
from zoneinfo import ZoneInfo
import zipfile

from calendar_exporter import CalendarExporter
from models import Config, Event, Location


def _make_test_event():
    """Return a single test event and its config."""
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
    return config, event


class TestIcsEncoding:
    """ICS string output: BOM, CRLF, required headers, DTSTAMP."""

    def test_utf8_bom_and_crlf(self):
        config, event = _make_test_event()
        exporter = CalendarExporter(config)
        ics_content = exporter.export_to_ics([event])
        ics_bytes = ics_content.encode("utf-8-sig")

        assert ics_bytes.startswith(b"\xef\xbb\xbf")
        assert "\r\n" in ics_content

    def test_required_headers(self):
        config, event = _make_test_event()
        exporter = CalendarExporter(config)
        ics_content = exporter.export_to_ics([event])

        assert "X-WR-CALNAME:Swimming Schedule" in ics_content
        assert "METHOD:PUBLISH" in ics_content
        assert "X-WR-TIMEZONE:America/New_York" in ics_content

    def test_dtstamp_inside_vevent(self):
        config, event = _make_test_event()
        exporter = CalendarExporter(config)
        ics_content = exporter.export_to_ics([event])

        vevent = re.search(r"BEGIN:VEVENT.*?END:VEVENT", ics_content, re.DOTALL)
        assert vevent and "DTSTAMP:" in vevent.group(0)

    def test_file_output(self, tmp_path):
        config, event = _make_test_event()
        exporter = CalendarExporter(config)
        out_file = tmp_path / "test.ics"
        exporter.export_to_ics([event], str(out_file))

        raw = out_file.read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf")
        assert b"\r\n" in raw


class TestIcsZipExport:
    """ZIP packaging: contains valid ICS with correct encoding and headers."""

    def test_zip_contains_ics_with_correct_format(self):
        config, event = _make_test_event()
        exporter = CalendarExporter(config)
        zip_bytes = exporter.export_to_ics_zip([event], ics_filename="test.ics")

        with zipfile.ZipFile(BytesIO(zip_bytes), "r") as zf:
            assert "test.ics" in zf.namelist()
            ics_bytes = zf.read("test.ics")

        assert ics_bytes.startswith(b"\xef\xbb\xbf")
        ics_content = ics_bytes.decode("utf-8-sig")
        assert "\r\n" in ics_content
        assert "METHOD:PUBLISH" in ics_content
        assert "X-WR-TIMEZONE:America/New_York" in ics_content
        assert "X-WR-CALNAME:Swimming Schedule" in ics_content
