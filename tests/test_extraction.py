"""Automated test for event extraction with the test case"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Setup - add parent directory to path
load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import Config, Location
from config_manager import ConfigManager
from extractor import EventExtractor
from rules_engine import RulesEngine

# Test case from user
TEST_SCHEDULE = """周四 1/29 下午 6 - 8 下水+陆上 @ Regis
周五 1/30 下午 6 - 8 下水 @ Regis
周六 1/31 上午 9 - 11 下水+陆上 @ Brandeis
周日 2/1 上午 9 - 11 下水 @ Wightman

周四 2/5 下午 6 - 8 下水+陆上 @ Regis
周五 2/6 下午 6 - 8 下水 @ Regis
周六 2/7 上午 9 - 11 下水+陆上 @ Brandeis
周日 2/8 上午 9 - 11 下水 @ Brandeis

周四 2/12 下午 6 - 8 下水+陆上 @ Regis
周五 2/13 下午 6 - 8 下水 @ Regis
周六 2/14 上午 9 - 11 下水+陆上 @ Brandeis
周日 2/15 上午 9 - 11 下水 @ Brandeis"""

def test_extraction():
    """Test the full extraction pipeline"""
    
    # Load API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return False
    
    print(f"✓ API key loaded: {api_key[:20]}...")
    
    # Load config
    config_mgr = ConfigManager()
    config = config_mgr.load()
    print(f"✓ Config loaded with {len(config.locations)} locations")
    
    # Initialize extractor
    try:
        extractor = EventExtractor(api_key, config)
        print("✓ EventExtractor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize extractor: {e}")
        return False
    
    # Extract events
    print("\nExtracting events...")
    try:
        events = extractor.extract(TEST_SCHEDULE)
        print(f"✓ Extracted {len(events)} events")
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Apply rules
    rules_engine = RulesEngine(config)
    events = rules_engine.apply_location_rules(events)
    events = rules_engine.merge_overlapping_events(events)
    events = rules_engine.deduplicate_events(events)
    events = rules_engine.sort_events(events)
    warnings = rules_engine.validate_events(events)
    
    print(f"✓ Rules applied, {len(events)} events after deduplication")
    print(f"✓ {len(warnings)} warnings")
    
    # Display results
    print("\nExtracted Events:")
    for i, event in enumerate(events, 1):
        location = event.location.name if event.location else event.location_name or "No location"
        print(f"{i}. {event.start_time.strftime('%Y-%m-%d %H:%M')} - {event.summary} @ {location}")
        if event.raw_text:
            print(f"   Snippet: {event.raw_text[:100]}")  # Show first 100 chars
    
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - [{warning['severity']}] {warning['issue']}")
    
    # Validate expected results
    expected_count = 12
    if len(events) == expected_count:
        print(f"\n✅ TEST PASSED: Got expected {expected_count} events")
        return True
    else:
        print(f"\n❌ TEST FAILED: Expected {expected_count} events, got {len(events)}")
        return False

if __name__ == "__main__":
    success = test_extraction()
    sys.exit(0 if success else 1)
