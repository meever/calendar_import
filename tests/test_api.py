"""API connectivity test for Gemini."""

import pytest
from google import genai


@pytest.mark.api
def test_api_connectivity(api_key: str) -> None:
    client = genai.Client(api_key=api_key)

    models = list(client.models.list())
    assert len(models) > 0

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say 'API working' in 2 words",
    )
    assert response.text
