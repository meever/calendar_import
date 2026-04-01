"""Helpers for reading optional Streamlit secrets safely."""

from typing import Any, Optional

from streamlit.errors import StreamlitSecretNotFoundError


def get_streamlit_secret(secrets: Any, key: str, default: Optional[str] = None) -> Optional[str]:
    """Return a Streamlit secret value or a default when secrets are unavailable."""
    try:
        return secrets[key]
    except (KeyError, StreamlitSecretNotFoundError):
        return default