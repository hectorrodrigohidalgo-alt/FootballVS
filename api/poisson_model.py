from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from math import exp
from typing import Any, Literal

Venue = Literal["team1", "team2", "neutral"]


class PoissonModelError(ValueError):
    """Indica configuración inválida o datos que impiden calcular el modelo."""


class InsufficientPoissonDataError(PoissonModelError):
    """Explica qué muestra histórica mínima todavía no está disponible."""

    def __init__(self, message: str, *, details: dict[str, int]) -> None:
        super().__init__(message)
        self.details = details


@dataclass(frozen=True)
class PoissonParameters:
    model_version: str = "poisson-v0.1.0"
    current_season_weight: float = 1.0
    previous_season_weight: float = 0.4
    prior_matches: float = 3.0
    minimum_venue_matches: int = 5
    minimum_neutral_matches: int = 10
    minimum_league_matches: int = 20
    maximum_score: int = 6

    def __post_init__(self) -> None:
        if not self.model_version.strip():
            raise PoissonModelError("model_version must be non-empty text.")
        if self.current_season_weight <= 0 or self.previous_season_weight < 0:
            raise PoissonModelError("Season weights must be non-negative.")
        if self.prior_matches < 0:
            raise PoissonModelError("prior_matches cannot be negative.")
        minimums = (
            self.minimum_venue_matches,
            self.minimum_neutral_matches,
            self.minimum_league_matches,
        )
        if any(isinstance(value, bool) or value <= 0 for value in minimums):
            raise PoissonModelError("Minimum match counts must be positive integers.")
        if isinstance(self.maximum_score, bool) or self.maximum_score < 0:
            raise PoissonModelError("maximum_score must be a non-negative integer.")


@dataclass
class WeightedTotals:
    matches: float = 0.0
    goals_for: float = 0.0
    goals_against: float = 0.0
    raw_matches: int = 0

    def record(self, goals_for: int, goals_against: int, weight: float) -> None:
        self.matches += weight
        self.goals_for += goals_for * weight
        self.goals_against += goals_against * weight
        self.raw_matches += 1


def _parse_timestamp(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise PoissonModelError(f"{field} must be non-empty text.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise PoissonModelError(f"{field} must be an ISO timestamp.") from error
    if parsed.tzinfo is None:
        raise PoissonModelError(f"{field} must include a timezone.")
    return parsed.astimezone(UTC)


def _format_timestamp(value: datetime, field: str) -> str:
    if value.tzinfo is None:
        raise PoissonModelError(f"{field} must include a timezone.")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _required_text(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise PoissonModelError(f"{field} must be non-empty text.")
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
        raise PoissonModelError("A finished match requires integer full-time scores.")
    return home_score, away_score


def _season_window(
    seasons: list[dict[str, Any]], competition_id: str, target_season_id: str
) -> dict[str, float]:
    ordered = sorted(
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
    target_index = next(
        (
            index
            for index, season in enumerate(ordered)
            if season.get("id") == target_season_id
        ),
        None,
    )
    if target_index is None:
        raise PoissonModelError("The target season does not belong to the competition.")
    return {
        _required_text(ordered[target_index], "id"): 1.0,
        **(
            {_required_text(ordered[target_index - 1], "id"): 0.4}
            if target_index > 0
            else {}
        ),
    }


def _smoothed_rate(
    goals: float, matches: float, league_average: float, prior_matches: float
) -> float:
    return (goals + league_average * prior_matches) / (matches + prior_matches)


def _relative_strength(smoothed_rate: float, league_average: float) -> float:
    # En una muestra formada sólo por 0-0 la fuerza relativa es neutra; el
    # promedio cero seguirá produciendo cero goles esperados.
    return smoothed_rate / league_average if league_average > 0 else 1.0


def _poisson_probabilities(expected_goals: float, maximum: int) -> list[float]:
    probabilities = [exp(-expected_goals)]
    for goals in range(1, maximum + 1):
        probabilities.append(probabilities[-1] * expected_goals / goals)
    return probabilities


def _complete_distribution(expected_goals: float) -> list[float]:
    probabilities = [exp(-expected_goals)]
    cumulative = probabilities[0]
    goals = 1
    while cumulative < 1 - 1e-12 and goals <= 100:
        probability = probabilities[-1] * expected_goals / goals
        probabilities.append(probability)
        cumulative += probability
        goals += 1
    return probabilities


def _outcome_probabilities(
    home_expected: float, away_expected: float
) -> dict[str, float]:
    home_distribution = _complete_distribution(home_expected)
    away_distribution = _complete_distribution(away_expected)
    home_win = draw = away_win = 0.0
    for home_goals, home_probability in enumerate(home_distribution):
        for away_goals, away_probability in enumerate(away_distribution):
            probability = home_probability * away_probability
            if home_goals > away_goals:
                home_win += probability
            elif home_goals < away_goals:
                away_win += probability
            else:
                draw += probability
    total = home_win + draw + away_win
    return {
        "home_win": home_win / total,
        "draw": draw / total,
        "away_win": away_win / total,
    }


def predict_poisson(
    matches: list[dict[str, Any]],
    seasons: list[dict[str, Any]],
    *,
    competition_id: str,
    season_id: str,
    team_1_id: str,
    team_2_id: str,
    venue: Venue,
    input_data_cutoff: datetime,
    parameters: PoissonParameters | None = None,
    calculated_at: datetime | None = None,
) -> dict[str, Any]:
    """Genera el baseline Poisson usando exclusivamente datos previos al corte."""
    if team_1_id == team_2_id:
        raise PoissonModelError("The teams must be different.")
    if venue not in {"team1", "team2", "neutral"}:
        raise PoissonModelError("venue must be team1, team2 or neutral.")
    config = parameters or PoissonParameters()
    cutoff = input_data_cutoff.astimezone(UTC) if input_data_cutoff.tzinfo else None
    if cutoff is None:
        raise PoissonModelError("input_data_cutoff must include a timezone.")
    calculation_time = calculated_at or datetime.now(UTC)
    season_weights = _season_window(seasons, competition_id, season_id)
    # Los pesos pertenecen al modelo y sustituyen los valores auxiliares usados
    # para localizar las dos temporadas.
    season_weights[season_id] = config.current_season_weight
    other_seasons = [item for item in season_weights if item != season_id]
    if other_seasons:
        season_weights[other_seasons[0]] = config.previous_season_weight

    league_home = WeightedTotals()
    league_away = WeightedTotals()
    team_home: dict[str, WeightedTotals] = {
        team_1_id: WeightedTotals(),
        team_2_id: WeightedTotals(),
    }
    team_away: dict[str, WeightedTotals] = {
        team_1_id: WeightedTotals(),
        team_2_id: WeightedTotals(),
    }
    eligible_matches: list[dict[str, Any]] = []

    for match in matches:
        match_season_id = match.get("season_id")
        if (
            match.get("competition_id") != competition_id
            or match_season_id not in season_weights
            or match.get("status") != "FINISHED"
            or _parse_timestamp(_required_text(match, "utc_date"), "utc_date") >= cutoff
        ):
            continue
        eligible_matches.append(match)
        home_team_id = _required_text(match, "home_team_id")
        away_team_id = _required_text(match, "away_team_id")
        home_score, away_score = _finished_score(match)
        weight = season_weights[str(match_season_id)]
        league_home.record(home_score, away_score, weight)
        league_away.record(away_score, home_score, weight)
        if home_team_id in team_home:
            team_home[home_team_id].record(home_score, away_score, weight)
        if away_team_id in team_away:
            team_away[away_team_id].record(away_score, home_score, weight)

    if league_home.raw_matches < config.minimum_league_matches:
        raise InsufficientPoissonDataError(
            "The league does not have enough previous finished matches.",
            details={
                "league_matches": league_home.raw_matches,
                "required_league_matches": config.minimum_league_matches,
            },
        )

    league_home_average = league_home.goals_for / league_home.matches
    league_away_average = league_away.goals_for / league_away.matches
    league_overall_average = (
        league_home.goals_for + league_away.goals_for
    ) / (2 * league_home.matches)

    if venue == "team1":
        home_id, away_id = team_1_id, team_2_id
    elif venue == "team2":
        home_id, away_id = team_2_id, team_1_id
    else:
        home_id = away_id = ""

    if venue != "neutral":
        home_totals = team_home[home_id]
        away_totals = team_away[away_id]
        if (
            home_totals.raw_matches < config.minimum_venue_matches
            or away_totals.raw_matches < config.minimum_venue_matches
        ):
            raise InsufficientPoissonDataError(
                "The teams do not have enough matches in the required venue.",
                details={
                    "home_team_matches": home_totals.raw_matches,
                    "away_team_matches": away_totals.raw_matches,
                    "required_team_matches": config.minimum_venue_matches,
                },
            )
        home_attack = _relative_strength(
            _smoothed_rate(
                home_totals.goals_for,
                home_totals.matches,
                league_home_average,
                config.prior_matches,
            ),
            league_home_average,
        )
        home_defense = _relative_strength(
            _smoothed_rate(
                home_totals.goals_against,
                home_totals.matches,
                league_away_average,
                config.prior_matches,
            ),
            league_away_average,
        )
        away_attack = _relative_strength(
            _smoothed_rate(
                away_totals.goals_for,
                away_totals.matches,
                league_away_average,
                config.prior_matches,
            ),
            league_away_average,
        )
        away_defense = _relative_strength(
            _smoothed_rate(
                away_totals.goals_against,
                away_totals.matches,
                league_home_average,
                config.prior_matches,
            ),
            league_home_average,
        )
        home_expected = league_home_average * home_attack * away_defense
        away_expected = league_away_average * away_attack * home_defense
        expected_by_team = {
            home_id: home_expected,
            away_id: away_expected,
        }
        feature_details = {
            "league_home_goals_per_match": league_home_average,
            "league_away_goals_per_match": league_away_average,
            "home_team_id": home_id,
            "away_team_id": away_id,
            "home_attack_strength": home_attack,
            "home_defense_strength": home_defense,
            "away_attack_strength": away_attack,
            "away_defense_strength": away_defense,
            "home_team_raw_matches": home_totals.raw_matches,
            "away_team_raw_matches": away_totals.raw_matches,
            "home_team_weighted_matches": home_totals.matches,
            "away_team_weighted_matches": away_totals.matches,
        }
    else:
        overall: dict[str, WeightedTotals] = {}
        for team_id in (team_1_id, team_2_id):
            combined = WeightedTotals(
                matches=team_home[team_id].matches + team_away[team_id].matches,
                goals_for=team_home[team_id].goals_for + team_away[team_id].goals_for,
                goals_against=(
                    team_home[team_id].goals_against
                    + team_away[team_id].goals_against
                ),
                raw_matches=(
                    team_home[team_id].raw_matches + team_away[team_id].raw_matches
                ),
            )
            overall[team_id] = combined
        if any(
            totals.raw_matches < config.minimum_neutral_matches
            for totals in overall.values()
        ):
            raise InsufficientPoissonDataError(
                "The teams do not have enough previous matches for neutral venue.",
                details={
                    "team_1_matches": overall[team_1_id].raw_matches,
                    "team_2_matches": overall[team_2_id].raw_matches,
                    "required_team_matches": config.minimum_neutral_matches,
                },
            )
        attacks = {
            team_id: _relative_strength(
                _smoothed_rate(
                    totals.goals_for,
                    totals.matches,
                    league_overall_average,
                    config.prior_matches,
                ),
                league_overall_average,
            )
            for team_id, totals in overall.items()
        }
        defenses = {
            team_id: _relative_strength(
                _smoothed_rate(
                    totals.goals_against,
                    totals.matches,
                    league_overall_average,
                    config.prior_matches,
                ),
                league_overall_average,
            )
            for team_id, totals in overall.items()
        }
        expected_by_team = {
            team_1_id: league_overall_average
            * attacks[team_1_id]
            * defenses[team_2_id],
            team_2_id: league_overall_average
            * attacks[team_2_id]
            * defenses[team_1_id],
        }
        feature_details = {
            "league_goals_per_team_match": league_overall_average,
            "team_1_attack_strength": attacks[team_1_id],
            "team_1_defense_strength": defenses[team_1_id],
            "team_2_attack_strength": attacks[team_2_id],
            "team_2_defense_strength": defenses[team_2_id],
            "team_1_raw_matches": overall[team_1_id].raw_matches,
            "team_2_raw_matches": overall[team_2_id].raw_matches,
            "team_1_weighted_matches": overall[team_1_id].matches,
            "team_2_weighted_matches": overall[team_2_id].matches,
        }
        home_expected = expected_by_team[team_1_id]
        away_expected = expected_by_team[team_2_id]

    if venue == "team2":
        team_1_expected = expected_by_team[team_1_id]
        team_2_expected = expected_by_team[team_2_id]
    else:
        team_1_expected = expected_by_team[team_1_id]
        team_2_expected = expected_by_team[team_2_id]

    team_1_distribution = _poisson_probabilities(
        team_1_expected, config.maximum_score
    )
    team_2_distribution = _poisson_probabilities(
        team_2_expected, config.maximum_score
    )
    matrix = [
        {
            "team_1_goals": team_1_goals,
            "team_2_goals": team_2_goals,
            "probability": team_1_probability * team_2_probability,
        }
        for team_1_goals, team_1_probability in enumerate(team_1_distribution)
        for team_2_goals, team_2_probability in enumerate(team_2_distribution)
    ]
    matrix_probability = sum(item["probability"] for item in matrix)
    if venue == "team2":
        venue_outcomes = _outcome_probabilities(home_expected, away_expected)
        outcomes = {
            "team_1_win_probability": venue_outcomes["away_win"],
            "draw_probability": venue_outcomes["draw"],
            "team_2_win_probability": venue_outcomes["home_win"],
        }
    else:
        venue_outcomes = _outcome_probabilities(team_1_expected, team_2_expected)
        outcomes = {
            "team_1_win_probability": venue_outcomes["home_win"],
            "draw_probability": venue_outcomes["draw"],
            "team_2_win_probability": venue_outcomes["away_win"],
        }
    total_expected = team_1_expected + team_2_expected
    under_or_equal_two = exp(-total_expected) * (
        1 + total_expected + total_expected**2 / 2
    )
    both_score = (
        1
        - exp(-team_1_expected)
        - exp(-team_2_expected)
        + exp(-total_expected)
    )

    return {
        "model_version": config.model_version,
        "status": "experimental",
        "competition_id": competition_id,
        "season_id": season_id,
        "team_1_id": team_1_id,
        "team_2_id": team_2_id,
        "venue": venue,
        "estimated_team_1_goals": team_1_expected,
        "estimated_team_2_goals": team_2_expected,
        **outcomes,
        "over_2_5_probability": 1 - under_or_equal_two,
        "under_2_5_probability": under_or_equal_two,
        "both_teams_score_probability": both_score,
        "score_matrix": matrix,
        "top_scorelines": sorted(
            matrix, key=lambda item: item["probability"], reverse=True
        )[:3],
        "probability_outside_matrix": max(0.0, 1 - matrix_probability),
        "input_data_cutoff": _format_timestamp(input_data_cutoff, "input_data_cutoff"),
        "calculated_at": _format_timestamp(calculation_time, "calculated_at"),
        "matches_used": len(eligible_matches),
        "features": feature_details,
        "parameters": asdict(config),
    }
