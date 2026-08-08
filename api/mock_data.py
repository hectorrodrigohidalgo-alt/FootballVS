from typing import Any

# Dataset pequeño y deliberadamente ficticio. En una fase posterior será
# reemplazado por equipos y partidos obtenidos desde football-data.org.
COMPETITION = {
    "id": "PL",
    "name": "Premier League",
    "country": "England",
    "season": "2026/27",
}

TEAMS: dict[str, dict[str, Any]] = {
    "arsenal": {
        "id": "arsenal",
        "name": "Arsenal",
        "short_name": "Arsenal",
        "tla": "ARS",
        "statistics": {
            "matches_played": 10,
            "wins": 7,
            "draws": 2,
            "losses": 1,
            "goals_for_per_match": 2.1,
            "goals_against_per_match": 0.8,
            "recent_form": ["W", "W", "D", "W", "W"],
            "elo_rating": 1852,
        },
    },
    "chelsea": {
        "id": "chelsea",
        "name": "Chelsea",
        "short_name": "Chelsea",
        "tla": "CHE",
        "statistics": {
            "matches_played": 10,
            "wins": 5,
            "draws": 3,
            "losses": 2,
            "goals_for_per_match": 1.8,
            "goals_against_per_match": 1.2,
            "recent_form": ["W", "D", "W", "L", "W"],
            "elo_rating": 1778,
        },
    },
    "liverpool": {
        "id": "liverpool",
        "name": "Liverpool",
        "short_name": "Liverpool",
        "tla": "LIV",
        "statistics": {
            "matches_played": 10,
            "wins": 6,
            "draws": 2,
            "losses": 2,
            "goals_for_per_match": 2.0,
            "goals_against_per_match": 1.0,
            "recent_form": ["W", "L", "W", "W", "D"],
            "elo_rating": 1831,
        },
    },
    "manchester-city": {
        "id": "manchester-city",
        "name": "Manchester City",
        "short_name": "Man City",
        "tla": "MCI",
        "statistics": {
            "matches_played": 10,
            "wins": 7,
            "draws": 1,
            "losses": 2,
            "goals_for_per_match": 2.3,
            "goals_against_per_match": 1.1,
            "recent_form": ["W", "W", "L", "W", "W"],
            "elo_rating": 1864,
        },
    },
}

VALID_VENUES = {"team1", "team2", "neutral"}


def team_summaries() -> list[dict[str, str]]:
    """Entrega al selector sólo la identidad básica de cada equipo."""
    # No se incluyen estadísticas aquí para mantener pequeña la respuesta que
    # llena los desplegables del frontend.
    return [
        {
            "id": team["id"],
            "name": team["name"],
            "short_name": team["short_name"],
            "tla": team["tla"],
        }
        for team in TEAMS.values()
    ]


def build_comparison(team_1_id: str, team_2_id: str, venue: str) -> dict[str, Any]:
    """Construye métricas mock repetibles para una solicitud ya validada."""
    team_1 = TEAMS[team_1_id]
    team_2 = TEAMS[team_2_id]
    team_1_stats = team_1["statistics"]
    team_2_stats = team_2["statistics"]

    # La localía se representa provisionalmente como 65 puntos Elo adicionales.
    # Es una regla mock para probar el contrato, no el modelo predictivo final.
    team_1_bonus = 65 if venue == "team1" else 0
    team_2_bonus = 65 if venue == "team2" else 0
    rating_difference = (
        team_1_stats["elo_rating"]
        + team_1_bonus
        - team_2_stats["elo_rating"]
        - team_2_bonus
    )

    # La curva logística de Elo convierte la diferencia de rating en una fuerza
    # relativa entre 0 y 1. Luego reservamos una parte para el empate.
    team_1_strength = 1 / (1 + 10 ** (-rating_difference / 400))
    draw_probability = max(0.18, min(0.27, 0.27 - abs(rating_difference) / 2000))
    decisive_probability = 1 - draw_probability
    team_1_probability = decisive_probability * team_1_strength
    team_2_probability = 1 - draw_probability - team_1_probability

    # Los goles estimados combinan el ataque propio con la defensa rival y un
    # pequeño ajuste por localía. Tampoco deben confundirse con xG real.
    team_1_goal_bonus = 0.2 if venue == "team1" else 0
    team_2_goal_bonus = 0.2 if venue == "team2" else 0
    estimated_team_1_goals = (
        team_1_stats["goals_for_per_match"]
        + team_2_stats["goals_against_per_match"]
    ) / 2 + team_1_goal_bonus
    estimated_team_2_goals = (
        team_2_stats["goals_for_per_match"]
        + team_1_stats["goals_against_per_match"]
    ) / 2 + team_2_goal_bonus

    # Redondear en el límite de la API evita que el frontend reciba decimales
    # extensos, conservando valores determinísticos para futuras pruebas.
    return {
        "competition": COMPETITION,
        "team_1": team_1,
        "team_2": team_2,
        "venue": venue,
        "prediction": {
            "team_1_win_probability": round(team_1_probability, 4),
            "draw_probability": round(draw_probability, 4),
            "team_2_win_probability": round(team_2_probability, 4),
            "estimated_team_1_goals": round(estimated_team_1_goals, 2),
            "estimated_team_2_goals": round(estimated_team_2_goals, 2),
        },
        "model": {
            "version": "mock-contract-v1",
            "is_mock": True,
            "data_updated_at": "2026-08-07T00:00:00+00:00",
        },
    }
