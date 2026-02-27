"""End-to-end test for shared calendar workflow (no API calls)."""

from datetime import datetime

from models import Config, Event
from shared_calendar_manager import SharedCalendarManager


def test_shared_calendar_workflow(tmp_path) -> None:
    manager = SharedCalendarManager(storage_dir=str(tmp_path / "shared_e2e"))
    config = Config.get_default_config()

    user1_events = [
        Event(
            start_time=datetime(2026, 3, 3, 18, 0),
            end_time=datetime(2026, 3, 3, 20, 0),
            summary="Swim Practice",
            location=config.locations["Regis"],
            location_name="Regis",
        ),
        Event(
            start_time=datetime(2026, 3, 5, 18, 0),
            end_time=datetime(2026, 3, 5, 20, 0),
            summary="Swim Practice",
            location=config.locations["Regis"],
            location_name="Regis",
        ),
        Event(
            start_time=datetime(2026, 3, 7, 9, 0),
            end_time=datetime(2026, 3, 7, 11, 0),
            summary="Weekend Practice",
            location=config.locations["Brandeis"],
            location_name="Brandeis",
        ),
    ]

    manager.save(
        name="March Week 1 - MIT Team",
        description="Mon/Wed at Regis, Saturday at Brandeis",
        events=user1_events,
    )

    user2_events = [
        Event(
            start_time=datetime(2026, 3, 8, 10, 0),
            end_time=datetime(2026, 3, 8, 12, 0),
            summary="Sunday Practice",
            location=config.locations["Brandeis"],
            location_name="Brandeis",
        )
    ]

    manager.save(
        name="Weekend Warrior Schedule",
        description="Sundays only at Brandeis",
        events=user2_events,
    )

    all_calendars = manager.list_all()
    assert len(all_calendars) == 2

    loaded = manager.get_by_id(all_calendars[1].id, config.locations)
    assert loaded is not None
    assert loaded.name == all_calendars[1].name
    assert len(loaded.events) == 3

    stats = manager.get_stats()
    assert stats["total_calendars"] == 2
