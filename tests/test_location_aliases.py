"""
Tests for location alias resolution in Config.resolve_location()
"""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models import Config, Location


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
