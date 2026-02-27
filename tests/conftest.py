import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv


load_dotenv()
SRC_DIR = Path(__file__).parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def api_key() -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        pytest.skip("GEMINI_API_KEY not set; skipping API test")
    return key


@pytest.fixture
def config():
    from config_manager import ConfigManager

    manager = ConfigManager()
    cfg = manager.load()
    return cfg
