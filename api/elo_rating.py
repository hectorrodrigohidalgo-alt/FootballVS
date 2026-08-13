from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from itertools import groupby
from typing import Any


class EloRatingError(ValueError):
    """Indica que los datos o parámetros no permiten calcular Elo."""


@dataclass(frozen=True)
class EloParameters:
    """Parámetros inmutables que identifican una versión del cálculo."""

    model_version: str = "elo-v0.1.0"
    initial_rating: float = 1500.0
    promoted_rating: float = 1400.0
    k_factor: float = 20.0
    home_advantage: float = 65.0
    season_retention: float = 0.75

    def __post_init__(self) -> None:
        numeric_values = (
            self.initial_rating,
            self.promoted_rating,
            self.k_factor,
            self.home_advantage,
            self.season_retention,
        )
        if not self.model_version.strip():
            raise EloRatingError("model_version must be non-empty text.")
        if any(isinstance(value, bool) for value in numeric_values):
            raise EloRatingError("Elo parameters must be numeric values.")
        if self.k_factor <= 0:
            raise EloRatingError("k_factor must be greater than zero.")
        if self.home_advantage < 0:
            raise EloRatingError("home_advantage cannot be negative.")
        if not 0 <= self.season_retention <= 1:
            raise EloRatingError("season_retention must be between zero and one.")


def expected_score(rating: float, opponent_rating: float) -> float:
    """Convierte la diferencia Elo en una puntuación esperada entre 0 y 1."""
    return 1 / (1 + 10 ** ((opponent_rating - rating) / 400))


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise EloRatingError("calculated_at must include a timezone.")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _required_text(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise EloRatingError(f"{field} must be non-empty text.")
    return value.strip()


def _finished_score(match: dict[str, Any]) -> tuple[int, int]:
    home_score = match.get("home_score")
    away_score = match.get("away_score")
    if (
        isinstance(home_score, bool)
        or not isinstance(home_score, int)
        or isinstance(away_score, bool)
        or not isinstance(away_score, int)
    ):
        raise EloRatingError("A finished match requires integer full-time scores.")
    return home_score, away_score


def _actual_scores(home_score: int, away_score: int) -> tuple[float, float]:
    if home_score > away_score:
        return 1.0, 0.0
    if home_score < away_score:
        return 0.0, 1.0
    return 0.5, 0.5


def _history_id(model_version: str, match_id: str, team_id: str) -> str:
    return f"footballvs:elo-history:{model_version}:{match_id}:{team_id}"


def _rating_id(model_version: str, competition_id: str, team_id: str) -> str:
    return f"footballvs:elo-rating:{model_version}:{competition_id}:{team_id}"


def calculate_elo_history(
    matches: list[dict[str, Any]],
    seasons: list[dict[str, Any]],
    *,
    competition_id: str,
    parameters: EloParameters | None = None,
    calculated_at: datetime | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Calcula historial y rating actual sin modificar partidos normalizados."""
    config = parameters or EloParameters()
    calculation_time = _timestamp(calculated_at or datetime.now(UTC))
    competition_seasons = sorted(
        (
            season
            for season in seasons
            if season.get("competition_id") == competition_id
        ),
        key=lambda season: (
            _required_text(season, "start_date"),
            _required_text(season, "id"),
        ),
    )
    if not competition_seasons:
        raise EloRatingError("The competition requires at least one season.")

    matches_by_season: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for match in matches:
        if match.get("competition_id") == competition_id:
            matches_by_season[_required_text(match, "season_id")].append(match)

    ratings: dict[str, float] = {}
    previous_participants: set[str] = set()
    history: list[dict[str, Any]] = []
    latest_season_by_team: dict[str, str] = {}

    for season_index, season in enumerate(competition_seasons):
        season_id = _required_text(season, "id")
        season_matches = matches_by_season.get(season_id, [])
        participants = {
            _required_text(match, field)
            for match in season_matches
            for field in ("home_team_id", "away_team_id")
        }

        # El primer periodo parte igualado. Después sólo la temporada anterior
        # concede continuidad; el resto se considera ascendido.
        for team_id in participants:
            if season_index == 0:
                ratings[team_id] = config.initial_rating
            elif team_id in previous_participants:
                previous_rating = ratings[team_id]
                ratings[team_id] = config.initial_rating + (
                    previous_rating - config.initial_rating
                ) * config.season_retention
            else:
                ratings[team_id] = config.promoted_rating
            latest_season_by_team[team_id] = season_id

        finished_matches = sorted(
            (match for match in season_matches if match.get("status") == "FINISHED"),
            key=lambda match: (
                _required_text(match, "utc_date"),
                _required_text(match, "id"),
            ),
        )

        # Todos los encuentros del mismo instante leen el mismo estado Elo. Los
        # cambios se acumulan y sólo se aplican al finalizar el bloque.
        for utc_date, simultaneous_group in groupby(
            finished_matches, key=lambda match: _required_text(match, "utc_date")
        ):
            pending_changes: dict[str, float] = defaultdict(float)
            block_records: list[dict[str, Any]] = []
            teams_in_block: set[str] = set()

            for match in simultaneous_group:
                match_id = _required_text(match, "id")
                home_team_id = _required_text(match, "home_team_id")
                away_team_id = _required_text(match, "away_team_id")
                if home_team_id == away_team_id:
                    raise EloRatingError("A team cannot play against itself.")
                if home_team_id in teams_in_block or away_team_id in teams_in_block:
                    raise EloRatingError(
                        "A team cannot appear twice in the same simultaneous block."
                    )
                teams_in_block.update((home_team_id, away_team_id))

                home_score, away_score = _finished_score(match)
                home_actual, away_actual = _actual_scores(home_score, away_score)
                home_before = ratings[home_team_id]
                away_before = ratings[away_team_id]
                home_expected = expected_score(
                    home_before + config.home_advantage, away_before
                )
                away_expected = 1 - home_expected
                home_change = config.k_factor * (home_actual - home_expected)
                away_change = -home_change
                pending_changes[home_team_id] += home_change
                pending_changes[away_team_id] += away_change

                shared = {
                    "match_id": match_id,
                    "competition_id": competition_id,
                    "season_id": season_id,
                    "utc_date": utc_date,
                    "model_version": config.model_version,
                    "calculated_at": calculation_time,
                }
                block_records.extend(
                    [
                        {
                            "id": _history_id(
                                config.model_version, match_id, home_team_id
                            ),
                            **shared,
                            "team_id": home_team_id,
                            "opponent_team_id": away_team_id,
                            "venue": "home",
                            "rating_before": home_before,
                            "venue_adjustment": config.home_advantage,
                            "expected_score": home_expected,
                            "actual_score": home_actual,
                            "rating_change": home_change,
                            "rating_after": home_before + home_change,
                        },
                        {
                            "id": _history_id(
                                config.model_version, match_id, away_team_id
                            ),
                            **shared,
                            "team_id": away_team_id,
                            "opponent_team_id": home_team_id,
                            "venue": "away",
                            "rating_before": away_before,
                            "venue_adjustment": 0.0,
                            "expected_score": away_expected,
                            "actual_score": away_actual,
                            "rating_change": away_change,
                            "rating_after": away_before + away_change,
                        },
                    ]
                )

            for team_id, rating_change in pending_changes.items():
                ratings[team_id] += rating_change
            history.extend(block_records)

        previous_participants = participants

    current_ratings = [
        {
            "id": _rating_id(config.model_version, competition_id, team_id),
            "team_id": team_id,
            "competition_id": competition_id,
            "season_id": latest_season_by_team[team_id],
            "rating": rating,
            "model_version": config.model_version,
            "parameters": asdict(config),
            "calculated_at": calculation_time,
        }
        for team_id, rating in sorted(ratings.items())
        if team_id in previous_participants
    ]
    return history, current_ratings
