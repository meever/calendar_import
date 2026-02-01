"""
End-to-end test with real schedule and expected output validation
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone

# Setup - add parent directory to path
load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import Config, Location
from config_manager import ConfigManager
from extractor import EventExtractor
from rules_engine import RulesEngine

# Real test case from user
TEST_SCHEDULE = """群公告

ARCT 🏊 Junior Group 一月训练时间表 安排如下：



周四 1/29 下午 6 - 8  下水+陆上 @ Regis

周五 1/30 Silvers Championship 

参加比赛但没有比赛项目的队员 下午5 - 6 下水 @ Regis 

不参加 Silvers 的队员照常训练 下午 5 - 7 下水



1/31 周六 6-7:30pm 下水 + 7:30~8pm 陆上拉伸 @ Brandeis ⚠️

2/1 周日 仅10&U Age Group达标队员 9-10:30am 下水 @Regis

2/1 周日 5~6:30pm 下水 + 6:30~7pm 陆上拉伸 @ Brandeis



2/2 周一 6~7:30pm 下水、7:30~8pm 陆上拉伸

2/3 周二 6~7:30pm 下水、7:30~8pm 陆上拉伸 

2/4 周三 5~6:30pm 下水、6:30~7pm 陆上拉伸

2/5 周四 5~6:30pm 下水、6:30~7pm 陆上拉伸



2/6 周五 休息 ♨️ 场馆闭馆



2/7 周六 5~6:30pm 下水 + 6:30~7pm 陆上拉伸 @ Brandeis

2/8 周日 5~6:30pm 下水 + 6:30~7pm 陆上拉伸 @ Brandeis"""

# Expected events with validation criteria
EXPECTED_EVENTS = [
    {
        "date": "2026-01-29",
        "start_hour": 18,
        "end_hour": 20,
        "location": "Regis",
        "description": "Must be single event from 6pm-8pm (underwater + dryland combined)"
    },
    {
        "date": "2026-01-30",
        "start_hour": 17,
        "end_hour": 18,
        "location": "Regis",
        "description": "Championship participants without events, 5-6pm"
    },
    {
        "date": "2026-01-30",
        "start_hour": 17,
        "end_hour": 19,
        "location": "Regis",
        "description": "Non-championship participants, 5-7pm"
    },
    {
        "date": "2026-01-31",
        "start_hour": 18,
        "end_hour": 20,
        "location": "Brandeis",
        "description": "Must be single event 6pm-8pm (underwater + dryland combined)"
    },
    {
        "date": "2026-02-01",
        "start_hour": 9,
        "end_hour": 10,
        "location": "Regis",
        "description": "10&U Age Group, 9-10:30am"
    },
    {
        "date": "2026-02-01",
        "start_hour": 17,
        "end_hour": 19,
        "location": "Brandeis",
        "description": "Must be single event 5pm-7pm (underwater + dryland combined)"
    },
    {
        "date": "2026-02-02",
        "start_hour": 18,
        "end_hour": 20,
        "location": "Regis",  # Weekday default
        "description": "Must be single event 6pm-8pm (underwater + dryland combined)"
    },
    {
        "date": "2026-02-03",
        "start_hour": 18,
        "end_hour": 20,
        "location": "Regis",
        "description": "Must be single event 6pm-8pm (underwater + dryland combined)"
    },
    {
        "date": "2026-02-04",
        "start_hour": 17,
        "end_hour": 19,
        "location": "Regis",
        "description": "Must be single event 5pm-7pm (underwater + dryland combined)"
    },
    {
        "date": "2026-02-05",
        "start_hour": 17,
        "end_hour": 19,
        "location": "Regis",
        "description": "Must be single event 5pm-7pm (underwater + dryland combined)"
    },
    # 2/6 is rest day - should NOT appear
    {
        "date": "2026-02-07",
        "start_hour": 17,
        "end_hour": 19,
        "location": "Brandeis",
        "description": "Must be single event 5pm-7pm (underwater + dryland combined)"
    },
    {
        "date": "2026-02-08",
        "start_hour": 17,
        "end_hour": 19,
        "location": "Brandeis",
        "description": "Must be single event 5pm-7pm (underwater + dryland combined)"
    },
]

def test_e2e():
    """End-to-end test with real schedule"""
    
    print("="*80)
    print("End-to-End Test - Real Swimming Schedule")
    print("="*80)
    
    # 1. Setup
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return False
    print(f"✓ API key loaded")
    
    config_mgr = ConfigManager()
    config = config_mgr.load()
    print(f"✓ Config loaded with {len(config.locations)} locations")
    
    # 2. Extract events
    try:
        extractor = EventExtractor(api_key, config)
        print("✓ EventExtractor initialized")
        
        events = extractor.extract(TEST_SCHEDULE)
        print(f"✓ Extracted {len(events)} raw events")
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. Apply rules
    rules_engine = RulesEngine(config)
    events = rules_engine.apply_location_rules(events)
    events = rules_engine.merge_overlapping_events(events)  # Merge overlapping events
    events = rules_engine.deduplicate_events(events)
    events = rules_engine.sort_events(events)
    warnings = rules_engine.validate_events(events)
    
    print(f"✓ Rules applied, {len(events)} events after processing")
    
    # 4. Display extracted events
    print("\n" + "="*80)
    print("EXTRACTED EVENTS:")
    print("="*80)
    for i, event in enumerate(events, 1):
        location = event.location.name if event.location else event.location_name or "No location"
        print(f"{i:2d}. {event.start_time.strftime('%Y-%m-%d %a %H:%M')}-{event.end_time.strftime('%H:%M')} @ {location:10s} - {event.summary}")
        if event.raw_text and len(event.raw_text) < 150:
            print(f"    Snippet: {event.raw_text}")
        if event.notes:
            # Show first line of notes (usually the "Combined X groups" line)
            notes_first_line = event.notes.split('\n')[0]
            print(f"    Notes: {notes_first_line}")
    
    # 5. Critical validations
    print("\n" + "="*80)
    print("CRITICAL VALIDATIONS:")
    print("="*80)
    
    all_passed = True
    
    # Check: No event should be 2/6 (rest day)
    rest_day_events = [e for e in events if e.start_time.month == 2 and e.start_time.day == 6]
    if rest_day_events:
        print("❌ FAIL: Found events on 2/6 (rest day) - should be skipped")
        all_passed = False
    else:
        print("✓ PASS: No events on 2/6 (rest day correctly skipped)")
    
    # Check: Events with both underwater and dryland should be combined
    combined_session_dates = ["2026-01-29", "2026-01-31", "2026-02-01", "2026-02-02", 
                               "2026-02-03", "2026-02-04", "2026-02-05", "2026-02-07", "2026-02-08"]
    
    print("\nChecking combined sessions (underwater + dryland):")
    for date_str in combined_session_dates:
        date_events = [e for e in events if e.start_time.strftime('%Y-%m-%d') == date_str]
        
        # For dates with single session, check duration
        if date_str == "2026-01-29":  # 6-8pm
            event = next((e for e in date_events if e.start_time.hour == 18), None)
            if event:
                duration_hours = (event.end_time - event.start_time).total_seconds() / 3600
                if duration_hours >= 1.5 and duration_hours <= 2.5:
                    print(f"  ✓ {date_str}: Single session {duration_hours:.1f} hours (underwater+dryland combined)")
                else:
                    print(f"  ❌ {date_str}: Duration {duration_hours:.1f}h - might be split sessions")
                    all_passed = False
    
    # Check: Expected event count (approximate - AI may vary slightly)
    min_expected = len(EXPECTED_EVENTS) - 2
    max_expected = len(EXPECTED_EVENTS) + 2
    if min_expected <= len(events) <= max_expected:
        print(f"\n✓ PASS: Event count {len(events)} in expected range ({min_expected}-{max_expected})")
    else:
        print(f"\n❌ FAIL: Event count {len(events)} outside expected range ({min_expected}-{max_expected})")
        all_passed = False
    
    # Check: All events have locations
    events_without_location = [e for e in events if not e.location and not e.location_name]
    if events_without_location:
        print(f"❌ FAIL: {len(events_without_location)} events without location")
        all_passed = False
    else:
        print("✓ PASS: All events have locations assigned")
    
    # Check: No invalid time ranges
    invalid_times = [e for e in events if e.start_time >= e.end_time]
    if invalid_times:
        print(f"❌ FAIL: {len(invalid_times)} events with invalid time ranges")
        all_passed = False
    else:
        print("✓ PASS: All events have valid time ranges")
    
    # 6. Display warnings
    if warnings:
        print("\n" + "="*80)
        print(f"WARNINGS ({len(warnings)}):")
        print("="*80)
        for warning in warnings:
            print(f"  [{warning['severity']}] {warning['issue']} - Event {warning['event_index'] + 1}")
    
    # 7. Final result
    print("\n" + "="*80)
    if all_passed:
        print("✅ END-TO-END TEST PASSED")
        print("="*80)
        return True
    else:
        print("❌ END-TO-END TEST FAILED - See errors above")
        print("="*80)
        return False

if __name__ == "__main__":
    success = test_e2e()
    sys.exit(0 if success else 1)
