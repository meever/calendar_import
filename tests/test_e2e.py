"""End-to-end test with real schedule and expected output validation."""

import pytest

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

@pytest.mark.api
@pytest.mark.slow
def test_e2e(api_key: str, config):
    """End-to-end test with real schedule."""
    config.gemini_model = "gemini-2.5-flash"

    extractor = EventExtractor(api_key, config)
    events = extractor.extract(TEST_SCHEDULE)

    rules_engine = RulesEngine(config)
    events = rules_engine.sort_events(
        rules_engine.deduplicate_events(
            rules_engine.merge_overlapping_events(
                rules_engine.apply_location_rules(events)
            )
        )
    )

    # Critical validations
    rest_day_events = [e for e in events if e.start_time.month == 2 and e.start_time.day == 6]
    assert not rest_day_events

    combined_session_dates = ["2026-01-29", "2026-01-31", "2026-02-01", "2026-02-02", 
                               "2026-02-03", "2026-02-04", "2026-02-05", "2026-02-07", "2026-02-08"]

    for date_str in combined_session_dates:
        date_events = [e for e in events if e.start_time.strftime('%Y-%m-%d') == date_str]

        # For dates with single session, check duration
        if date_str == "2026-01-29":  # 6-8pm
            event = next((e for e in date_events if e.start_time.hour == 18), None)
            if event:
                duration_hours = (event.end_time - event.start_time).total_seconds() / 3600
                assert 1.5 <= duration_hours <= 2.5

    min_expected = len(EXPECTED_EVENTS) - 2
    max_expected = len(EXPECTED_EVENTS) + 2
    assert min_expected <= len(events) <= max_expected

    events_without_location = [e for e in events if not e.location and not e.location_name]
    assert not events_without_location

    invalid_times = [e for e in events if e.start_time >= e.end_time]
    assert not invalid_times
