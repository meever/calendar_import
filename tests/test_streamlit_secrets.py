"""Tests for safe Streamlit secret access."""

from streamlit.errors import StreamlitSecretNotFoundError

from streamlit_secrets import get_streamlit_secret


class MissingSecrets:
    """Test double that behaves like Streamlit when no secrets file exists."""

    def __getitem__(self, key: str) -> str:
        raise StreamlitSecretNotFoundError("No secrets found")


def test_get_streamlit_secret_returns_default_when_secrets_file_missing() -> None:
    assert get_streamlit_secret(MissingSecrets(), "APP_PASSWORD") is None
    assert get_streamlit_secret(MissingSecrets(), "APP_PASSWORD", "") == ""


def test_get_streamlit_secret_returns_default_when_key_missing() -> None:
    assert get_streamlit_secret({}, "APP_PASSWORD", "fallback") == "fallback"


def test_get_streamlit_secret_returns_value_when_present() -> None:
    assert get_streamlit_secret({"APP_PASSWORD": "secret"}, "APP_PASSWORD") == "secret"