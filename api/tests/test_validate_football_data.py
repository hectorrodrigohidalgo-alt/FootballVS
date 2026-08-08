from typing import Any

from football_data_client import FootballDataRequestError
from tools.validate_football_data import validate_provider_access


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict | None]] = []

    def get_json(
        self, path: str, query: dict[str, int] | None = None
    ) -> dict[str, Any]:
        self.calls.append((path, query))
        if path == "competitions/PL":
            return {
                "id": 2021,
                "code": "PL",
                "name": "Premier League",
                "currentSeason": {"startDate": "2026-08-01"},
                "seasons": [
                    {"startDate": "2026-08-01", "endDate": "2027-05-31"},
                    {"startDate": "2025-08-01", "endDate": "2026-05-31"},
                ],
            }

        if query == {"season": 2026}:
            return {"teams": [{"id": index} for index in range(20)]}

        if query == {"season": 2026, "matchday": 1}:
            return {"matches": [{"id": index} for index in range(10)]}

        raise FootballDataRequestError("Restricted", status_code=403)


def test_validation_reports_access_and_stops_at_first_restricted_season() -> None:
    client = FakeClient()
    delays: list[float] = []

    result = validate_provider_access(
        client,
        max_season_probes=6,
        delay_seconds=6.5,
        sleep=delays.append,
    )

    assert result["authenticated"] is True
    assert result["current_season_start_year"] == 2026
    assert result["accessible_seasons"] == [
        {
            "start_year": 2026,
            "start_date": "2026-08-01",
            "end_date": "2027-05-31",
            "team_count": 20,
            "matchday_1_match_count": 10,
        }
    ]
    assert result["first_inaccessible_season"] == 2025
    assert result["request_count"] == 4
    assert delays == [6.5, 6.5, 6.5]
