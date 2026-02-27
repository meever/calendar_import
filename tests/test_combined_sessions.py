"""Test combined swim+dryland session handling rules."""

import pytest

from extractor import EventExtractor
from rules_engine import RulesEngine

# Test case with combined session (no separate times)
TEST_SCHEDULE = """
2026年2月训练安排：

2/9 周一 5~6:30 下水+陆上拉伸
2/10 周二 6~7:30pm 下水、7:30~8pm 陆上拉伸
"""

@pytest.mark.api
def test_combined_session_handling(api_key: str, config):
    """Test combined session rules for single-range and split-range inputs."""
    config.gemini_model = "gemini-2.5-flash"

    extractor = EventExtractor(api_key, config)
    events = extractor.extract(TEST_SCHEDULE)

    rules_engine = RulesEngine(config)
    events = rules_engine.apply_location_rules(events)
    events = rules_engine.sort_events(events)

    assert len(events) == 2

    # Event 1: 2/9 周一 5~6:30 下水+陆上拉伸
    # Rule: single time range should be used exactly (no auto-extension)
    event1 = events[0]
    expected_duration_1 = 1.5  # 5:00-6:30
    actual_duration_1 = (event1.end_time - event1.start_time).total_seconds() / 3600
    assert abs(actual_duration_1 - expected_duration_1) < 0.1
    
    # Event 2: 2/10 周二 6~7:30pm 下水、7:30~8pm 陆上拉伸 → should NOT be extended (has separate times)
    event2 = events[1]
    expected_duration_2 = 2.0  # 6:00-8:00 = 2 hours (already has separate times)
    actual_duration_2 = (event2.end_time - event2.start_time).total_seconds() / 3600
    
    assert abs(actual_duration_2 - expected_duration_2) < 0.1
