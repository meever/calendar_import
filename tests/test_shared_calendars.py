"""
Tests for SharedCalendarManager

Tests CRUD operations for shared calendars without requiring API calls.
"""

import sys
from pathlib import Path
import shutil
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shared_calendar_manager import SharedCalendarManager
from models import Event, Config, Location


def test_shared_calendar_crud():
    """Test creating, listing, retrieving, and deleting shared calendars"""
    
    # Setup: Use temp directory
    test_dir = Path(__file__).parent / "test_shared_calendars"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    manager = SharedCalendarManager(storage_dir=str(test_dir))
    
    # Create test config with location
    config = Config.get_default_config()
    
    # Create test events
    events = [
        Event(
            start_time=datetime(2026, 2, 27, 18, 0),
            end_time=datetime(2026, 2, 27, 20, 0),
            summary="Swim Practice",
            location=config.locations["Regis"],
            location_name="Regis"
        ),
        Event(
            start_time=datetime(2026, 2, 28, 17, 0),
            end_time=datetime(2026, 2, 28, 19, 0),
            summary="Swim Practice",
            location=config.locations["Regis"],
            location_name="Regis"
        )
    ]
    
    # Test 1: Save shared calendar
    print("Test 1: Saving shared calendar...")
    shared_cal = manager.save(
        name="Test Team Schedule",
        description="Weekly practice for testing",
        events=events
    )
    
    assert shared_cal.id is not None, "Calendar should have ID"
    assert shared_cal.name == "Test Team Schedule", "Name should match"
    assert shared_cal.description == "Weekly practice for testing", "Description should match"
    assert shared_cal.event_count == 2, f"Should have 2 events, got {shared_cal.event_count}"
    assert len(shared_cal.events) == 2, "Events list should have 2 items"
    print(f"✓ Saved calendar with ID: {shared_cal.id}")
    
    # Test 2: List all shared calendars
    print("\nTest 2: Listing all shared calendars...")
    all_calendars = manager.list_all()
    assert len(all_calendars) == 1, f"Should have 1 calendar, got {len(all_calendars)}"
    assert all_calendars[0].name == "Test Team Schedule"
    print(f"✓ Found {len(all_calendars)} calendar(s)")
    
    # Test 3: Get by ID
    print("\nTest 3: Retrieving calendar by ID...")
    retrieved = manager.get_by_id(shared_cal.id, config.locations)
    assert retrieved is not None, "Should retrieve calendar"
    assert retrieved.name == "Test Team Schedule"
    assert len(retrieved.events) == 2
    print(f"✓ Retrieved calendar: {retrieved.name}")
    
    # Test 4: Save another calendar
    print("\nTest 4: Saving second calendar...")
    events2 = [
        Event(
            start_time=datetime(2026, 3, 1, 9, 0),
            end_time=datetime(2026, 3, 1, 11, 0),
            summary="Weekend Practice",
            location=config.locations["Brandeis"],
            location_name="Brandeis"
        )
    ]
    
    shared_cal2 = manager.save(
        name="Weekend Schedule",
        description="Saturday morning practices",
        events=events2
    )
    
    all_calendars = manager.list_all()
    assert len(all_calendars) == 2, f"Should have 2 calendars, got {len(all_calendars)}"
    print(f"✓ Now have {len(all_calendars)} calendars")
    
    # Test 5: Delete calendar
    print("\nTest 5: Deleting calendar...")
    deleted = manager.delete(shared_cal.id)
    assert deleted == True, "Delete should succeed"
    
    all_calendars = manager.list_all()
    assert len(all_calendars) == 1, f"Should have 1 calendar after delete, got {len(all_calendars)}"
    print(f"✓ Deleted calendar, {len(all_calendars)} remaining")
    
    # Test 6: Get stats
    print("\nTest 6: Getting stats...")
    stats = manager.get_stats()
    assert stats["total_calendars"] == 1, "Stats should show 1 calendar"
    assert stats["total_size_kb"] > 0, "Should have non-zero size"
    print(f"✓ Stats: {stats['total_calendars']} calendars, {stats['total_size_kb']:.2f} KB")
    
    # Cleanup
    print("\nCleaning up test directory...")
    shutil.rmtree(test_dir)
    print("✓ Test directory removed")
    
    print("\n✅ All SharedCalendarManager tests passed!")


if __name__ == "__main__":
    test_shared_calendar_crud()
