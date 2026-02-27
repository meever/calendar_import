"""Automated extraction test with canonical schedule input."""

import pytest

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

@pytest.mark.api
def test_extraction(api_key: str, config):
    """Test the full extraction pipeline."""
    config.gemini_model = "gemini-2.5-flash"

    extractor = EventExtractor(api_key, config)
    events = extractor.extract(TEST_SCHEDULE)

    rules_engine = RulesEngine(config)
    events = rules_engine.apply_location_rules(events)
    events = rules_engine.merge_overlapping_events(events)
    events = rules_engine.deduplicate_events(events)
    events = rules_engine.sort_events(events)
    warnings = rules_engine.validate_events(events)

    expected_count = 12
    assert len(events) == expected_count
    assert isinstance(warnings, list)
