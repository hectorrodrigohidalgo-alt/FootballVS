import json
from typing import Any

import azure.functions as func


def json_response(payload: dict[str, Any], status_code: int = 200) -> func.HttpResponse:
    """Crea respuestas JSON uniformes para todos los endpoints."""
    # La API pública no debe ser interpretada como otro tipo de contenido ni
    # filtrar la URL de origen a destinos externos. Las respuestas se obtienen
    # nuevamente para no servir comparaciones o estados de salud obsoletos.
    return func.HttpResponse(
        body=json.dumps(payload),
        headers={
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        },
        mimetype="application/json",
        status_code=status_code,
    )


def error_response(code: str, message: str, status_code: int) -> func.HttpResponse:
    """Mantiene un único contrato de error para frontend, logs y pruebas."""
    return json_response(
        {"error": {"code": code, "message": message}},
        status_code=status_code,
    )
