import os
from datetime import UTC, datetime

import azure.functions as func

from data_catalog import create_data_catalog
from http_responses import error_response, json_response
from mock_data import TEAMS, VALID_VENUES, build_comparison

# El MVP expone endpoints públicos de solo lectura. La protección de la clave del
# proveedor ocurre en el backend y nunca se envía al navegador.
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.function_name(name="health")
@app.route(route="v1/health", methods=[func.HttpMethod.GET])
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Informa si el proceso de la API está disponible."""
    # Azure Functions exige que el parámetro se llame `req`, aunque este endpoint
    # no necesite leer datos de la solicitud.
    del req
    payload = {
        "status": "ok",
        "service": "footballvs-api",
        "version": os.getenv("APP_VERSION", "development"),
        "timestamp": datetime.now(UTC).isoformat(),
    }

    return json_response(payload)


@app.function_name(name="list_competitions")
@app.route(route="v1/competitions", methods=[func.HttpMethod.GET])
def list_competitions(req: func.HttpRequest) -> func.HttpResponse:
    """Lista las competiciones disponibles para los selectores de la interfaz."""
    del req
    catalog = create_data_catalog()
    return json_response(
        {"data": catalog.list_competitions(), "meta": {"source": catalog.source}}
    )


@app.function_name(name="list_teams")
@app.route(
    route="v1/competitions/{competition_id}/teams",
    methods=[func.HttpMethod.GET],
)
def list_teams(req: func.HttpRequest) -> func.HttpResponse:
    """Lista los equipos de una competición conocida."""
    # Los parámetros incluidos en la ruta se obtienen desde `route_params`.
    # Normalizamos a mayúsculas porque el identificador oficial es `PL`.
    competition_id = (req.route_params.get("competition_id") or "").upper()
    catalog = create_data_catalog()
    teams = catalog.list_teams(competition_id)
    if teams is None:
        return error_response(
            "competition_not_found",
            "The requested competition does not exist.",
            404,
        )

    return json_response(
        {
            "data": teams,
            "meta": {
                "competition_id": competition_id,
                "source": catalog.source,
            },
        }
    )


@app.function_name(name="compare_teams")
@app.route(route="v1/comparisons", methods=[func.HttpMethod.GET])
def compare_teams(req: func.HttpRequest) -> func.HttpResponse:
    """Devuelve métricas mock determinísticas para dos equipos."""
    # Los parámetros de consulta llegan como texto. Se normalizan antes de
    # validarlos para aceptar diferencias de mayúsculas y minúsculas.
    team_1_id = (req.params.get("team1") or "").lower()
    team_2_id = (req.params.get("team2") or "").lower()
    venue = (req.params.get("venue") or "").lower()

    # El orden de las validaciones produce errores específicos y evita acceder
    # al diccionario de equipos con identificadores inválidos.
    if not team_1_id or not team_2_id or not venue:
        return error_response(
            "missing_parameters",
            "The team1, team2 and venue parameters are required.",
            400,
        )

    if team_1_id == team_2_id:
        return error_response(
            "invalid_team_selection",
            "The selected teams must be different.",
            400,
        )

    if team_1_id not in TEAMS or team_2_id not in TEAMS:
        return error_response(
            "team_not_found",
            "One or more selected teams do not exist.",
            404,
        )

    if venue not in VALID_VENUES:
        return error_response(
            "invalid_venue",
            "The venue must be team1, team2 or neutral.",
            400,
        )

    # Sólo después de validar la solicitud se calculan las métricas simuladas.
    return json_response(
        {
            "data": build_comparison(team_1_id, team_2_id, venue),
            "meta": {"source": "mock"},
        }
    )
