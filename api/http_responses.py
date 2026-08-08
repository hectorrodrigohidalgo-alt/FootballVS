import json
from typing import Any

import azure.functions as func


def json_response(payload: dict[str, Any], status_code: int = 200) -> func.HttpResponse:
    """Crea respuestas JSON uniformes para todos los endpoints."""
    # Los datos siguen siendo mock, por eso se evita almacenarlos en caché.
    return func.HttpResponse(
        body=json.dumps(payload),
        headers={"Cache-Control": "no-store"},
        mimetype="application/json",
        status_code=status_code,
    )


def error_response(code: str, message: str, status_code: int) -> func.HttpResponse:
    """Mantiene un único contrato de error para frontend, logs y pruebas."""
    return json_response(
        {"error": {"code": code, "message": message}},
        status_code=status_code,
    )
