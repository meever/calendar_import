"""
Test combined swim+dryland session extension (30-minute rule)
Now handled by AI in the extraction phase (hybrid approach)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Setup
load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import Config
from config_manager import ConfigManager
from extractor import EventExtractor
from rules_engine import RulesEngine

# Test case with combined session (no separate times)
TEST_SCHEDULE = """
2026年2月训练安排：

2/9 周一 5~6:30 下水+陆上拉伸
2/10 周二 6~7:30pm 下水、7:30~8pm 陆上拉伸
"""

def test_combined_session_extension():
    """Test that combined sessions without separate times get extended by 30 minutes"""
    
    print("="*80)
    print("Testing Combined Session 30-Minute Extension")
    print("="*80)
    
    # 1. Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return False
    print(f"✓ API key loaded: {api_key[:20]}...")
    
    # 2. Load config
    config_manager = ConfigManager()
    config = config_manager.get_config()
    print(f"✓ Config loaded with {len(config.locations)} locations")
    
    # 3. Extract events
    extractor = EventExtractor(api_key, config)
    print("✓ EventExtractor initialized")
    
    try:
        events = extractor.extract(TEST_SCHEDULE)
        print(f"✓ Extracted {len(events)} events")
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. Apply rules (mechanical operations only - AI handles semantic rules)
    rules_engine = RulesEngine(config)
    events = rules_engine.apply_location_rules(events)
    events = rules_engine.sort_events(events)
    
    print(f"✓ Rules applied")
    
    # 4. Display results
    print("\n" + "="*80)
    print("EXTRACTED EVENTS:")
    print("="*80)
    
    for i, event in enumerate(events, 1):
        location = event.location.name if event.location else event.location_name or "No location"
        duration = (event.end_time - event.start_time).total_seconds() / 3600
        print(f"\n{i}. {event.start_time.strftime('%Y-%m-%d %a %H:%M')}-{event.end_time.strftime('%H:%M')} @ {location}")
        print(f"   Duration: {duration:.1f} hours")
        print(f"   Snippet: {event.raw_text}")
        if event.notes:
            print(f"   Notes: {event.notes}")
    
    # 5. Validate results
    print("\n" + "="*80)
    print("VALIDATION:")
    print("="*80)
    
    if len(events) != 2:
        print(f"❌ FAIL: Expected 2 events, got {len(events)}")
        return False
    
    # Event 1: 2/9 周一 5~6:30 下水+陆上拉伸 → should be extended to 7:00pm
    event1 = events[0]
    expected_duration_1 = 2.0  # 5:00-7:00 = 2 hours
    actual_duration_1 = (event1.end_time - event1.start_time).total_seconds() / 3600
    
    if abs(actual_duration_1 - expected_duration_1) < 0.1:
        print(f"✓ Event 1: Extended correctly (5:00-7:00, {actual_duration_1:.1f}h)")
    else:
        print(f"❌ Event 1: Expected {expected_duration_1}h, got {actual_duration_1:.1f}h")
        return False
    
    # Check if extension note was added
    if event1.notes and "30" in event1.notes:
        print(f"✓ Event 1: Has note about extended time")
    else:
        # Note: AI might not add a note, it just extends the time correctly
        print(f"ℹ Event 1: No extension note (AI handles semantically)")
    
    # Event 2: 2/10 周二 6~7:30pm 下水、7:30~8pm 陆上拉伸 → should NOT be extended (has separate times)
    event2 = events[1]
    expected_duration_2 = 2.0  # 6:00-8:00 = 2 hours (already has separate times)
    actual_duration_2 = (event2.end_time - event2.start_time).total_seconds() / 3600
    
    # Event 2 should have correct duration (AI handles this semantically)
    if abs(actual_duration_2 - expected_duration_2) < 0.1:
        print(f"✓ Event 2: Correct duration (AI detected separate times, {actual_duration_2:.1f}h)")
    else:
        print(f"❌ Event 2: Expected {expected_duration_2}h, got {actual_duration_2:.1f}h")
        return False
    
    print("\n" + "="*80)
    print("✅ TEST PASSED - Combined session extension works correctly!")
    print("="*80)
    return True

if __name__ == "__main__":
    success = test_combined_session_extension()
    sys.exit(0 if success else 1)
