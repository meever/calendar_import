"""
Application pipeline orchestration.
"""

from typing import List

from extractor import EventExtractor
from models import Config, Event
from rules_engine import RulesEngine
from settings import DEFAULT_EVENT_TITLE


def process_schedule(raw_text: str, api_key: str, config: Config) -> List[Event]:
    """
    Run extraction and deterministic business rules.

    Returns processed events ready for review/export.
    """
    extractor = EventExtractor(api_key=api_key, config=config)
    events = extractor.extract(raw_text)

    rules_engine = RulesEngine(config)
    events = rules_engine.apply_location_rules(events)
    events = rules_engine.merge_overlapping_events(events)
    events = rules_engine.deduplicate_events(events)
    events = rules_engine.sort_events(events)

    for event in events:
        if not event.summary:
            event.summary = DEFAULT_EVENT_TITLE

    return events
