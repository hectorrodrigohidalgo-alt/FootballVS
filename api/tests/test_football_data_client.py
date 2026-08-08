import json
from io import BytesIO
from urllib.error import HTTPError

import pytest

from football_data_client import (
    FootballDataClient,
    FootballDataConfigurationError,
    FootballDataRequestError,
)


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def test_client_sends_the_token_only_to_the_official_host() -> None:
    captured_request = None

    def opener(request, *, timeout):
        nonlocal captured_request
        captured_request = request
        assert timeout == 15
        return FakeResponse({"code": "PL"})

    client = FootballDataClient(api_key="secret-token", opener=opener)
    result = client.get_json("competitions/PL", {"season": 2026})

    assert result == {"code": "PL"}
    assert captured_request.full_url.endswith("competitions/PL?season=2026")
    assert captured_request.get_header("X-auth-token") == "secret-token"


@pytest.mark.parametrize(
    ("api_key", "base_url"),
    [
        ("", "https://api.football-data.org/v4"),
        ("replace_me", "https://api.football-data.org/v4"),
        ("secret-token", "http://api.football-data.org/v4"),
        ("secret-token", "https://example.com/v4"),
    ],
)
def test_client_rejects_unsafe_configuration(api_key: str, base_url: str) -> None:
    with pytest.raises(FootballDataConfigurationError):
        FootballDataClient(api_key=api_key, base_url=base_url)


def test_client_maps_authentication_errors_without_exposing_the_token() -> None:
    def opener(request, *, timeout):
        del timeout
        raise HTTPError(
            request.full_url,
            401,
            "Unauthorized",
            hdrs=None,
            fp=BytesIO(b'{"message":"invalid token"}'),
        )

    client = FootballDataClient(api_key="never-print-this", opener=opener)

    with pytest.raises(FootballDataRequestError) as captured_error:
        client.get_json("competitions/PL")

    assert captured_error.value.status_code == 401
    assert "rejected the API key" in str(captured_error.value)
    assert "never-print-this" not in str(captured_error.value)
