import json
from collections.abc import Mapping

import azure.functions as func
import pytest

from data_catalog import RepositoryDataCatalog
from data_repository import SQLiteDataRepository
from function_app import compare_teams, health, list_competitions, list_teams


def make_request(
    *,
    params: Mapping[str, str] | None = None,
    route_params: Mapping[str, str] | None = None,
) -> func.HttpRequest:
    """Crea la misma solicitud HTTP que recibiría una función en Azure."""
    return func.HttpRequest(
        method="GET",
        url="http://localhost:7071/api/test",
        headers={},
        params=params or {},
        route_params=route_params or {},
        body=b"",
    )


def response_body(response: func.HttpResponse) -> dict:
    """Decodifica una respuesta para verificar su contrato JSON."""
    return json.loads(response.get_body())


def test_health_reports_service_status() -> None:
    response = health(make_request())
    body = response_body(response)

    assert response.status_code == 200
    assert body["status"] == "ok"
    assert body["service"] == "footballvs-api"
    assert body["timestamp"].endswith("+00:00")


def test_competitions_returns_the_mock_premier_league() -> None:
    response = list_competitions(make_request())
    body = response_body(response)

    assert response.status_code == 200
    assert body["data"][0]["id"] == "PL"
    assert body["meta"]["source"] == "mock"


def test_teams_returns_summaries_without_statistics() -> None:
    response = list_teams(make_request(route_params={"competition_id": "pl"}))
    body = response_body(response)

    assert response.status_code == 200
    assert len(body["data"]) == 4
    assert body["data"][0]["name"] == "Arsenal"
    assert all("statistics" not in team for team in body["data"])


def test_teams_rejects_an_unknown_competition() -> None:
    response = list_teams(make_request(route_params={"competition_id": "UCL"}))

    assert response.status_code == 404
    assert response_body(response)["error"]["code"] == "competition_not_found"


def test_catalog_endpoints_can_read_repository_data(tmp_path, monkeypatch) -> None:
    repository = SQLiteDataRepository(tmp_path / "footballvs.db")
    repository.initialize()
    repository.upsert_many(
        "competition",
        [
            {
                "id": "football-data:competition:2021",
                "code": "PL",
                "name": "Premier League",
                "country": "England",
                "current_season_id": "football-data:season:2403",
            }
        ],
    )
    repository.upsert_many(
        "season",
        [{"id": "football-data:season:2403", "name": "2026/27"}],
    )
    repository.upsert_many(
        "team",
        [
            {
                "id": "football-data:team:57",
                "name": "Arsenal FC",
                "short_name": "Arsenal",
                "tla": "ARS",
            }
        ],
    )
    repository.upsert_many(
        "match",
        [
            {
                "id": "football-data:match:1",
                "competition_id": "football-data:competition:2021",
                "season_id": "football-data:season:2403",
                "home_team_id": "football-data:team:57",
                "away_team_id": "football-data:team:57",
            }
        ],
    )
    catalog = RepositoryDataCatalog(repository)
    monkeypatch.setattr("function_app.create_data_catalog", lambda: catalog)

    competitions_response = list_competitions(make_request())
    teams_response = list_teams(
        make_request(route_params={"competition_id": "pl"})
    )

    assert response_body(competitions_response)["meta"]["source"] == "repository"
    assert response_body(teams_response)["data"][0]["id"] == "football-data:team:57"


def test_comparison_is_deterministic_and_probabilities_sum_to_one() -> None:
    request = make_request(
        params={"team1": "Arsenal", "team2": "Liverpool", "venue": "team1"}
    )

    first_response = compare_teams(request)
    second_response = compare_teams(request)
    first_body = response_body(first_response)

    prediction = first_body["data"]["prediction"]
    probability_sum = (
        prediction["team_1_win_probability"]
        + prediction["draw_probability"]
        + prediction["team_2_win_probability"]
    )

    assert first_response.status_code == 200
    assert first_body == response_body(second_response)
    assert first_body["data"]["team_1"]["id"] == "arsenal"
    assert first_body["data"]["team_2"]["id"] == "liverpool"
    assert probability_sum == pytest.approx(1, abs=0.0001)


@pytest.mark.parametrize(
    ("params", "expected_status", "expected_code"),
    [
        (
            {"team1": "arsenal", "team2": "", "venue": "team1"},
            400,
            "missing_parameters",
        ),
        (
            {"team1": "arsenal", "team2": "arsenal", "venue": "team1"},
            400,
            "invalid_team_selection",
        ),
        (
            {"team1": "unknown", "team2": "liverpool", "venue": "team1"},
            404,
            "team_not_found",
        ),
        (
            {"team1": "arsenal", "team2": "liverpool", "venue": "outside"},
            400,
            "invalid_venue",
        ),
    ],
)
def test_comparison_validation_errors(
    params: dict[str, str], expected_status: int, expected_code: str
) -> None:
    response = compare_teams(make_request(params=params))

    assert response.status_code == expected_status
    assert response_body(response)["error"]["code"] == expected_code
