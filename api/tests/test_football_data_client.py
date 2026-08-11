import json
from io import BytesIO
from urllib.error import HTTPError, URLError

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

    client = FootballDataClient(
        api_key="never-print-this", opener=opener, request_interval_seconds=0
    )

    with pytest.raises(FootballDataRequestError) as captured_error:
        client.get_json("competitions/PL")

    assert captured_error.value.status_code == 401
    assert "rejected the API key" in str(captured_error.value)
    assert "never-print-this" not in str(captured_error.value)


def test_client_spaces_consecutive_requests() -> None:
    now = 100.0
    delays: list[float] = []

    def clock() -> float:
        return now

    def sleep(seconds: float) -> None:
        nonlocal now
        delays.append(seconds)
        now += seconds

    client = FootballDataClient(
        api_key="secret-token",
        opener=lambda request, *, timeout: FakeResponse({"url": request.full_url}),
        request_interval_seconds=6.1,
        clock=clock,
        sleep=sleep,
    )

    client.get_json("competitions/PL")
    client.get_json("competitions/PL/teams")

    assert delays == [pytest.approx(6.1)]


def test_client_retries_rate_limit_using_retry_after() -> None:
    attempts = 0
    delays: list[float] = []

    def opener(request, *, timeout):
        nonlocal attempts
        del timeout
        attempts += 1
        if attempts == 1:
            raise HTTPError(
                request.full_url,
                429,
                "Too Many Requests",
                hdrs={"Retry-After": "7"},
                fp=BytesIO(b"{}"),
            )
        return FakeResponse({"code": "PL"})

    client = FootballDataClient(
        api_key="secret-token",
        opener=opener,
        request_interval_seconds=0,
        sleep=delays.append,
    )

    assert client.get_json("competitions/PL") == {"code": "PL"}
    assert attempts == 2
    assert delays == [7]


def test_client_retries_connection_errors_and_reports_final_failure() -> None:
    attempts = 0

    def opener(request, *, timeout):
        nonlocal attempts
        del request, timeout
        attempts += 1
        raise URLError("offline")

    client = FootballDataClient(
        api_key="secret-token",
        opener=opener,
        request_interval_seconds=0,
        max_retries=2,
        sleep=lambda seconds: None,
    )

    with pytest.raises(FootballDataRequestError, match="Could not connect"):
        client.get_json("competitions/PL")

    assert attempts == 3


def test_client_does_not_retry_non_transient_errors() -> None:
    attempts = 0

    def opener(request, *, timeout):
        nonlocal attempts
        del timeout
        attempts += 1
        raise HTTPError(
            request.full_url,
            403,
            "Forbidden",
            hdrs=None,
            fp=BytesIO(b"{}"),
        )

    client = FootballDataClient(
        api_key="secret-token", opener=opener, request_interval_seconds=0
    )

    with pytest.raises(FootballDataRequestError) as captured_error:
        client.get_json("competitions/PL")

    assert captured_error.value.status_code == 403
    assert attempts == 1
