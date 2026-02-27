"""Tests for shared calendar CRUD operations."""

from datetime import datetime

from models import Config, Event
from shared_calendar_manager import SharedCalendarManager


def test_shared_calendar_crud(tmp_path) -> None:
    manager = SharedCalendarManager(storage_dir=str(tmp_path / "shared"))
    config = Config.get_default_config()

    events = [
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

    shared_calendar = manager.save(
        name="Test Team Schedule",
        description="Weekly practice for testing",
        events=events,
    )

    assert shared_calendar.id is not None
    assert shared_calendar.name == "Test Team Schedule"
    assert shared_calendar.description == "Weekly practice for testing"
    assert shared_calendar.event_count == 2
    assert len(shared_calendar.events) == 2

    calendars = manager.list_all()
    assert len(calendars) == 1
    assert calendars[0].name == "Test Team Schedule"

    retrieved = manager.get_by_id(shared_calendar.id, config.locations)
    assert retrieved is not None
    assert retrieved.name == "Test Team Schedule"
    assert len(retrieved.events) == 2

    events2 = [
        Event(
            start_time=datetime(2026, 3, 1, 9, 0),
            end_time=datetime(2026, 3, 1, 11, 0),
            summary="Weekend Practice",
            location=config.locations["Brandeis"],
            location_name="Brandeis",
        )
    ]

    manager.save(
        name="Weekend Schedule",
        description="Saturday morning practices",
        events=events2,
    )

    calendars = manager.list_all()
    assert len(calendars) == 2

    deleted = manager.delete(shared_calendar.id)
    assert deleted is True

    calendars = manager.list_all()
    assert len(calendars) == 1

    stats = manager.get_stats()
    assert stats["total_calendars"] == 1
    assert stats["total_size_kb"] > 0
