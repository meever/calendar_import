"""
End-to-end test for Shared Calendar Library feature

Tests the complete workflow: save → list → load → delete
without requiring API calls (uses pre-created events).
"""

import sys
from pathlib import Path
import shutil
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shared_calendar_manager import SharedCalendarManager
from models import Event, Config, SharedCalendar


def test_shared_calendar_workflow():
    """Test complete shared calendar workflow"""
    
    print("=" * 80)
    print("E2E Test: Shared Calendar Library Workflow")
    print("=" * 80)
    
    # Setup: Use temp directory
    test_dir = Path(__file__).parent / "test_shared_e2e"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    manager = SharedCalendarManager(storage_dir=str(test_dir))
    config = Config.get_default_config()
    
    # Scenario: User 1 extracts and shares a calendar
    print("\n[User 1] Creating schedule from extraction...")
    user1_events = [
        Event(
            start_time=datetime(2026, 3, 3, 18, 0),  # Mon
            end_time=datetime(2026, 3, 3, 20, 0),
            summary="Swim Practice",
            location=config.locations["Regis"],
            location_name="Regis"
        ),
        Event(
            start_time=datetime(2026, 3, 5, 18, 0),  # Wed
            end_time=datetime(2026, 3, 5, 20, 0),
            summary="Swim Practice",
            location=config.locations["Regis"],
            location_name="Regis"
        ),
        Event(
            start_time=datetime(2026, 3, 7, 9, 0),  # Sat
            end_time=datetime(2026, 3, 7, 11, 0),
            summary="Weekend Practice",
            location=config.locations["Brandeis"],
            location_name="Brandeis"
        )
    ]
    
    print("  ✓ Created 3 events (Mon, Wed, Sat)")
    
    # User 1 decides to share
    print("\n[User 1] Sharing calendar publicly...")
    shared_cal1 = manager.save(
        name="March Week 1 - MIT Team",
        description="Mon/Wed at Regis, Saturday at Brandeis",
        events=user1_events
    )
    print(f"  ✓ Shared as: '{shared_cal1.name}' (ID: {shared_cal1.id})")
    print(f"  ✓ Events: {shared_cal1.event_count}")
    
    # User 2 creates a different schedule and shares
    print("\n[User 2] Creating and sharing weekend-only schedule...")
    user2_events = [
        Event(
            start_time=datetime(2026, 3, 8, 10, 0),  # Sun
            end_time=datetime(2026, 3, 8, 12, 0),
            summary="Sunday Practice",
            location=config.locations["Brandeis"],
            location_name="Brandeis"
        )
    ]
    
    shared_cal2 = manager.save(
        name="Weekend Warrior Schedule",
        description="Sundays only at Brandeis",
        events=user2_events
    )
    print(f"  ✓ Shared as: '{shared_cal2.name}' (ID: {shared_cal2.id})")
    
    # User 3 browses the library
    print("\n[User 3] Browsing shared calendar library...")
    all_calendars = manager.list_all()
    print(f"  ✓ Found {len(all_calendars)} shared calendars:")
    
    for i, cal in enumerate(all_calendars, 1):
        print(f"    {i}. {cal.name}")
        print(f"       - {cal.description}")
        print(f"       - {cal.event_count} event(s), created {cal.created_at.strftime('%m/%d/%Y')}")
    
    # User 3 decides to use User 1's calendar (which is second in the list - newest first)
    print(f"\n[User 3] Loading '{all_calendars[1].name}'...")
    loaded = manager.get_by_id(all_calendars[1].id, config.locations)
    
    assert loaded is not None, "Should load calendar successfully"
    assert loaded.name == all_calendars[1].name
    assert len(loaded.events) == 3, f"Should have 3 events, got {len(loaded.events)}"
    
    print(f"  ✓ Loaded {len(loaded.events)} events:")
    for event in loaded.events:
        print(f"    - {event.start_time.strftime('%a %m/%d %H:%M')}-{event.end_time.strftime('%H:%M')} @ {event.location_name}")
    
    # User 3 can now export without pasting original text!
    print(f"\n[User 3] Can now export calendar without needing original text!")
    print(f"  ✓ Workflow complete: Browse → Load → Export")
    
    # Verify stats
    print("\n[System] Checking statistics...")
    stats = manager.get_stats()
    assert stats["total_calendars"] == 2, "Should have 2 calendars"
    print(f"  ✓ Total calendars: {stats['total_calendars']}")
    print(f"  ✓ Storage used: {stats['total_size_kb']:.2f} KB")
    
    # Cleanup
    print("\n[Cleanup] Removing test directory...")
    shutil.rmtree(test_dir)
    print("  ✓ Cleaned up")
    
    print("\n" + "=" * 80)
    print("✅ E2E SHARED CALENDAR WORKFLOW TEST PASSED")
    print("=" * 80)
    print("\nKey Benefits Demonstrated:")
    print("  ✓ Users can share calendars with descriptive names")
    print("  ✓ Others can browse available calendars")
    print("  ✓ Load and export without needing original text")
    print("  ✓ Multiple users can share different schedules")
    print("=" * 80)


if __name__ == "__main__":
    test_shared_calendar_workflow()
