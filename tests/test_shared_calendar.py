"""Tests for shared calendar CRUD and multi-user workflow."""

from datetime import datetime

from models import Config, Event
from shared_calendar_manager import SharedCalendarManager


def _make_events(config):
    """Return a pair of sample events at Regis."""
    return [
        Event(
            start_time=datetime(2026, 2, 27, 18, 0),
            end_time=datetime(2026, 2, 27, 20, 0),
            summary="Swim Practice",
            location=config.locations["Regis"],
            location_name="Regis",
        ),
        Event(
            start_time=datetime(2026, 2, 28, 17, 0),
            end_time=datetime(2026, 2, 28, 19, 0),
            summary="Swim Practice",
            location=config.locations["Regis"],
            location_name="Regis",
        ),
    ]


class TestSharedCalendarCRUD:
    """Save, list, retrieve, delete, stats."""

    def test_save_and_list(self, tmp_path):
        mgr = SharedCalendarManager(storage_dir=str(tmp_path / "sc"))
        config = Config.get_default_config()
        events = _make_events(config)

        cal = mgr.save("Team Schedule", "Weekly practice", events)
        assert cal.id is not None
        assert cal.name == "Team Schedule"
        assert cal.event_count == 2

        calendars = mgr.list_all()
        assert len(calendars) == 1
        assert calendars[0].name == "Team Schedule"

    def test_get_by_id(self, tmp_path):
        mgr = SharedCalendarManager(storage_dir=str(tmp_path / "sc"))
        config = Config.get_default_config()
        cal = mgr.save("Test", "desc", _make_events(config))

        retrieved = mgr.get_by_id(cal.id, config.locations)
        assert retrieved is not None
        assert len(retrieved.events) == 2

    def test_delete(self, tmp_path):
        mgr = SharedCalendarManager(storage_dir=str(tmp_path / "sc"))
        config = Config.get_default_config()
        cal = mgr.save("Test", "desc", _make_events(config))

        assert mgr.delete(cal.id) is True
        assert mgr.list_all() == []

    def test_stats(self, tmp_path):
        mgr = SharedCalendarManager(storage_dir=str(tmp_path / "sc"))
        config = Config.get_default_config()
        mgr.save("Test", "desc", _make_events(config))

        stats = mgr.get_stats()
        assert stats["total_calendars"] == 1
        assert stats["total_size_kb"] > 0


class TestSharedCalendarWorkflow:
    """Multi-calendar scenario (formerly test_shared_calendar_e2e)."""

    def test_multiple_calendars_list_and_load(self, tmp_path):
        mgr = SharedCalendarManager(storage_dir=str(tmp_path / "sc"))
        config = Config.get_default_config()

        mgr.save("Schedule A", "First", _make_events(config))
        mgr.save(
            "Schedule B",
            "Second",
            [
                Event(
                    start_time=datetime(2026, 3, 8, 10, 0),
                    end_time=datetime(2026, 3, 8, 12, 0),
                    summary="Sunday Practice",
                    location=config.locations["Brandeis"],
                    location_name="Brandeis",
                )
            ],
        )

        all_cals = mgr.list_all()
        assert len(all_cals) == 2

        # Newest first
        loaded = mgr.get_by_id(all_cals[0].id, config.locations)
        assert loaded is not None
        assert loaded.event_count > 0

        stats = mgr.get_stats()
        assert stats["total_calendars"] == 2
