"""
Centralized major settings and policy defaults.

Only cross-module or user-facing knobs are included here.
Local, single-use presentation constants should remain close to usage.
"""

from datetime import datetime


DEFAULT_TIMEZONE = "America/New_York"
DEFAULT_WEEKDAY_LOCATION = "Regis"
DEFAULT_WEEKEND_LOCATION = "Brandeis"
DEFAULT_EVENT_TITLE = "Swim Practice"

DEFAULT_GEMINI_MODEL = "gemini-flash-latest"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8501

DEFAULT_CONFIG_PATH = "config.json"
DEFAULT_SHARED_CALENDARS_DIR = "shared_calendars"
SHARED_CALENDAR_ID_LENGTH = 8

CALENDAR_NAME_PREFIX = "Swimming Schedule"
ICS_METHOD = "PUBLISH"
ICS_DEFAULT_FILENAME = "swimming_schedule.ics"

AI_MAX_RETRY_ATTEMPTS = 3
AI_RETRY_WAIT_MULTIPLIER_SECONDS = 3
AI_MIN_INPUT_LENGTH = 10
AI_INFERRED_FROM_SCHEDULE = "(Inferred from schedule)"
AI_TRANSIENT_ERROR_KEYWORDS = ("503", "UNAVAILABLE", "429", "quota", "rate")


def current_schedule_year() -> int:
    """Return the current year used for schedule inference defaults."""
    return datetime.now().year
