"""
Tests for location alias resolution and event parsing from Gemini responses.

Covers Config.resolve_location() (no API needed) and simulated
_parse_events_from_response() calls that validate location resolution without
making real Gemini API requests.
"""

import json
import sys
from pathlib import Path

SRC_DIR = Path(__file__).parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models import Config, Location
from extractor import EventExtractor
from rules_engine import RulesEngine


def _build_config() -> Config:
    """Return the default config (includes MIT and aliases)."""
    return Config.get_default_config()


class TestResolveLocationExactMatch:
    """Exact canonical-name lookups."""

    def test_exact_match_regis(self):
        config = _build_config()
        loc = config.resolve_location("Regis")
        assert loc is not None
        assert loc.name == "Regis"

    def test_exact_match_brandeis(self):
        config = _build_config()
        loc = config.resolve_location("Brandeis")
        assert loc is not None
        assert loc.name == "Brandeis"

    def test_exact_match_mit(self):
        config = _build_config()
        loc = config.resolve_location("MIT")
        assert loc is not None
        assert loc.name == "MIT"
        assert "Zesiger" in loc.address


class TestResolveLocationCaseInsensitive:
    """Case-insensitive canonical-name lookups."""

    def test_lowercase_mit(self):
        config = _build_config()
        loc = config.resolve_location("mit")
        assert loc is not None
        assert loc.name == "MIT"

    def test_mixed_case_regis(self):
        config = _build_config()
        loc = config.resolve_location("regis")
        assert loc is not None
        assert loc.name == "Regis"

    def test_uppercase_brandeis(self):
        config = _build_config()
        loc = config.resolve_location("BRANDEIS")
        assert loc is not None
        assert loc.name == "Brandeis"


class TestResolveLocationAlias:
    """Alias-based lookups."""

    def test_alias_mit_pool(self):
        config = _build_config()
        loc = config.resolve_location("mit pool")
        assert loc is not None
        assert loc.name == "MIT"

    def test_alias_zesiger(self):
        config = _build_config()
        loc = config.resolve_location("zesiger")
        assert loc is not None
        assert loc.name == "MIT"

    def test_alias_zesiger_center_case_insensitive(self):
        config = _build_config()
        loc = config.resolve_location("Zesiger Center")
        assert loc is not None
        assert loc.name == "MIT"

    def test_alias_gosman(self):
        config = _build_config()
        loc = config.resolve_location("gosman")
        assert loc is not None
        assert loc.name == "Brandeis"

    def test_alias_regis_college(self):
        config = _build_config()
        loc = config.resolve_location("Regis College")
        assert loc is not None
        assert loc.name == "Regis"

    def test_alias_wightman_tennis(self):
        config = _build_config()
        loc = config.resolve_location("wightman tennis")
        assert loc is not None
        assert loc.name == "Wightman"


class TestResolveLocationNone:
    """Edge cases that should return None."""

    def test_unknown_name(self):
        config = _build_config()
        assert config.resolve_location("Nonexistent Pool") is None

    def test_empty_string(self):
        config = _build_config()
        assert config.resolve_location("") is None

    def test_none_input(self):
        config = _build_config()
        assert config.resolve_location(None) is None

    def test_whitespace_only(self):
        config = _build_config()
        assert config.resolve_location("   ") is None


class TestLocationAliasesSerialization:
    """Aliases survive round-trip serialization."""

    def test_round_trip(self):
        config = _build_config()
        data = config.to_dict()

        # Aliases appear in serialized dict
        assert data["locations"]["MIT"]["aliases"] == ["mit pool", "zesiger", "zesiger center"]
        assert data["locations"]["Regis"]["aliases"] == ["regis college"]

        # Deserialize and verify resolution still works
        restored = Config.from_dict(data)
        loc = restored.resolve_location("zesiger")
        assert loc is not None
        assert loc.name == "MIT"

    def test_backward_compat_no_aliases_key(self):
        """Config JSON without aliases key should load with empty aliases."""
        data = {
            "locations": {
                "Pool": {
                    "name": "Pool",
                    "address": "123 Main St",
                    "is_default_weekday": False,
                    "is_default_weekend": False
                }
            }
        }
        config = Config.from_dict(data)
        loc = config.locations["Pool"]
        assert loc.aliases == []


class TestDefaultConfigHasMIT:
    """Default config includes MIT with correct address."""

    def test_mit_in_default_config(self):
        config = _build_config()
        assert "MIT" in config.locations
        mit = config.locations["MIT"]
        assert "120 Vassar St" in mit.address
        assert "Cambridge" in mit.address

    def test_default_config_location_count(self):
        config = _build_config()
        assert len(config.locations) == 4  # Regis, Brandeis, Wightman, MIT


# ---------------------------------------------------------------------------
# Helpers for parse tests
# ---------------------------------------------------------------------------

_MOCK_SCHEDULE_JSON = json.dumps({
    "events": [
        {
            "start_time": "2026-04-20T17:00:00",
            "end_time": "2026-04-20T19:00:00",
            "summary": "Swimming",
            "location_name": "regis college",
            "is_ambiguous": False,
            "original_text": "4/20 周一 5-7 PM @ Regis 下水+陆上",
        },
        {
            "start_time": "2026-04-22T17:00:00",
            "end_time": "2026-04-22T19:00:00",
            "summary": "Swimming",
            "location_name": "regis college",
            "is_ambiguous": False,
            "original_text": "4/22 周三 5-7 PM @ Regis 下水+陆上",
        },
        {
            "start_time": "2026-04-24T17:00:00",
            "end_time": "2026-04-24T19:00:00",
            "summary": "Swimming",
            "location_name": "regis college",
            "is_ambiguous": False,
            "original_text": "4/24 周五 5-7 PM @ Regis 下水+陆上",
        },
        {
            "start_time": "2026-04-25T17:00:00",
            "end_time": "2026-04-25T18:30:00",
            "summary": "Swimming",
            "location_name": "zesiger",
            "is_ambiguous": False,
            "original_text": "4/25 周六 5 - 6:30 PM @ MIT 下水",
        },
        {
            "start_time": "2026-04-26T17:00:00",
            "end_time": "2026-04-26T19:00:00",
            "summary": "Swimming",
            "location_name": "gosman",
            "is_ambiguous": False,
            "original_text": "4/26 周日 5-7 PM @ Brandeis 下水+陆上",
        },
    ]
})


_DUMMY_API_KEY = "dummy-api-key-for-testing"


def _make_extractor() -> EventExtractor:
    """Return an EventExtractor using a dummy API key (no real API calls made)."""
    return EventExtractor(_DUMMY_API_KEY, _build_config())


class TestParseEventsFromResponse:
    """_parse_events_from_response() with simulated Gemini JSON — no API key needed.

    We test this private method directly because it encapsulates the entire
    location-resolution step that runs on every AI response.  Testing via the
    public extract() method would require a live Gemini API key and network
    access, so targeting _parse_events_from_response() is the correct approach
    for deterministic, offline unit tests.
    """

    def test_five_events_parsed(self):
        """All 5 events in the fixture are parsed (fixture contains only event days)."""
        extractor = _make_extractor()
        events = extractor._parse_events_from_response(_MOCK_SCHEDULE_JSON, "Swimming")
        assert len(events) == 5

    def test_only_fixture_dates_present(self):
        """Parsed events must correspond exactly to the 5 dates supplied in the fixture."""
        extractor = _make_extractor()
        events = extractor._parse_events_from_response(_MOCK_SCHEDULE_JSON, "Swimming")
        dates = {e.start_time.date().isoformat() for e in events}
        assert dates == {"2026-04-20", "2026-04-22", "2026-04-24", "2026-04-25", "2026-04-26"}

    def test_mit_event_resolves_to_zesiger_address(self):
        """Alias 'zesiger' in the mock response resolves to the MIT canonical location."""
        extractor = _make_extractor()
        events = extractor._parse_events_from_response(_MOCK_SCHEDULE_JSON, "Swimming")
        mit_events = [e for e in events if e.start_time.date().isoformat() == "2026-04-25"]
        assert len(mit_events) == 1
        mit_event = mit_events[0]
        assert mit_event.location is not None
        assert mit_event.location.name == "MIT"
        assert mit_event.location_name == "MIT"  # normalised to canonical name
        assert "Zesiger" in mit_event.location.address

    def test_regis_events_have_correct_location(self):
        """Alias 'regis college' in the mock response resolves to the Regis canonical location."""
        extractor = _make_extractor()
        events = extractor._parse_events_from_response(_MOCK_SCHEDULE_JSON, "Swimming")
        regis_dates = {"2026-04-20", "2026-04-22", "2026-04-24"}
        regis_events = [e for e in events if e.start_time.date().isoformat() in regis_dates]
        assert len(regis_events) == 3
        for event in regis_events:
            assert event.location is not None
            assert event.location.name == "Regis"
            assert event.location_name == "Regis"  # normalised to canonical name

    def test_brandeis_event_has_correct_location(self):
        """Alias 'gosman' in the mock response resolves to the Brandeis canonical location."""
        extractor = _make_extractor()
        events = extractor._parse_events_from_response(_MOCK_SCHEDULE_JSON, "Swimming")
        brandeis_events = [e for e in events if e.start_time.date().isoformat() == "2026-04-26"]
        assert len(brandeis_events) == 1
        brandeis_event = brandeis_events[0]
        assert brandeis_event.location is not None
        assert brandeis_event.location.name == "Brandeis"
        assert brandeis_event.location_name == "Brandeis"  # normalised to canonical name
        assert "Gosman" in brandeis_event.location.address


_MOCK_HARVARD_JSON = json.dumps({
    "events": [
        {
            "start_time": "2026-04-25T17:00:00",
            "end_time": "2026-04-25T18:30:00",
            "summary": "Swimming",
            "location_name": "harvard",
            "is_ambiguous": False,
            "original_text": "4/25 周六 5 - 6:30 PM @ harvard 下水",
        }
    ]
})


class TestUnknownLocationHarvard:
    """Unknown location '@harvard' — event is still parsed but location is None."""

    def test_event_still_parsed(self):
        """Event must not be dropped just because the location is unknown."""
        extractor = _make_extractor()
        events = extractor._parse_events_from_response(_MOCK_HARVARD_JSON, "Swimming")
        assert len(events) == 1

    def test_location_is_none_before_rules(self):
        """Before rules engine runs, event.location must be None."""
        extractor = _make_extractor()
        events = extractor._parse_events_from_response(_MOCK_HARVARD_JSON, "Swimming")
        assert events[0].location is None

    def test_location_name_preserved(self):
        """event.location_name must retain the raw AI-provided value."""
        extractor = _make_extractor()
        events = extractor._parse_events_from_response(_MOCK_HARVARD_JSON, "Swimming")
        assert events[0].location_name == "harvard"

    def test_rules_engine_assigns_weekend_default(self):
        """After apply_location_rules(), Saturday event gets Brandeis (weekend default)."""
        extractor = _make_extractor()
        events = extractor._parse_events_from_response(_MOCK_HARVARD_JSON, "Swimming")
        config = _build_config()
        rules = RulesEngine(config)
        processed = rules.apply_location_rules(events)
        assert processed[0].location is not None
        assert processed[0].location.name == "Brandeis"
