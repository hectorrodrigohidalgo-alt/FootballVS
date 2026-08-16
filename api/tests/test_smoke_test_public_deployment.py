from typing import Any

import pytest

from tools.smoke_test_public_deployment import (
    PublicDeploymentError,
    verify_eventually,
    verify_public_deployment,
)


def test_verifies_public_repository_flow() -> None:
    def request_text(url: str) -> str:
        assert url == "https://footballvs.example"
        return '<div id="root"></div>'

    def request_json(url: str) -> dict[str, Any]:
        if url.endswith("/health"):
            return {"status": "ok"}
        if url.endswith("/competitions"):
            return {"data": [{"id": "PL"}], "meta": {"source": "repository"}}
        if url.endswith("/competitions/PL/teams"):
            return {
                "data": [{"id": "team:1"}, {"id": "team:2"}],
                "meta": {"source": "repository"},
            }
        assert "team1=team%3A1" in url
        assert "team2=team%3A2" in url
        return {
            "data": {"model": {"version": "poisson-v0.1.0", "is_available": True}},
            "meta": {"source": "repository"},
        }

    result = verify_public_deployment(
        "https://footballvs.example/",
        request_text=request_text,
        request_json=request_json,
    )

    assert result["status"] == "ok"
    assert result["team_count"] == 2
    assert result["prediction_available"] is True


def test_retries_complete_flow_until_azure_is_ready() -> None:
    attempts = 0
    delays: list[float] = []

    def verify(base_url: str) -> dict[str, Any]:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise PublicDeploymentError("Not propagated yet.")
        return {"status": "ok", "base_url": base_url}

    result = verify_eventually(
        "https://footballvs.example",
        attempts=3,
        delay_seconds=2,
        verify=verify,
        sleep=delays.append,
    )

    assert result["status"] == "ok"
    assert attempts == 3
    assert delays == [2, 2]


def test_fails_when_repository_mode_is_not_active() -> None:
    def request_json(url: str) -> dict[str, Any]:
        if url.endswith("/health"):
            return {"status": "ok"}
        return {"data": [{"id": "PL"}], "meta": {"source": "mock"}}

    with pytest.raises(PublicDeploymentError, match="real repository"):
        verify_public_deployment(
            "https://footballvs.example",
            request_text=lambda _: '<div id="root"></div>',
            request_json=request_json,
        )
