import json
import os
from collections.abc import Callable, Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

OFFICIAL_HOST = "api.football-data.org"
DEFAULT_BASE_URL = "https://api.football-data.org/v4"


class FootballDataConfigurationError(ValueError):
    """Indica que falta una configuración segura del proveedor."""


class FootballDataRequestError(RuntimeError):
    """Representa un fallo remoto sin incluir la clave ni la respuesta cruda."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class FootballDataClient:
    """Cliente mínimo para football-data.org basado en la biblioteca estándar."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        *,
        timeout_seconds: float = 15,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        resolved_api_key = api_key or os.getenv("FOOTBALL_DATA_API_KEY", "")
        resolved_base_url = base_url or os.getenv(
            "FOOTBALL_DATA_BASE_URL", DEFAULT_BASE_URL
        )

        if not resolved_api_key or resolved_api_key == "replace_me":
            raise FootballDataConfigurationError(
                "FOOTBALL_DATA_API_KEY is missing or still uses the placeholder."
            )

        # Restringir el destino evita enviar el token a un host distinto si la
        # URL local fuese modificada accidentalmente.
        parsed_base_url = urlsplit(resolved_base_url)
        if (
            parsed_base_url.scheme != "https"
            or parsed_base_url.hostname != OFFICIAL_HOST
        ):
            raise FootballDataConfigurationError(
                "FOOTBALL_DATA_BASE_URL must use the official HTTPS host."
            )

        self._api_key = resolved_api_key
        self._base_url = resolved_base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._opener = opener

    def get_json(
        self,
        path: str,
        query: Mapping[str, str | int] | None = None,
    ) -> dict[str, Any]:
        """Realiza un GET autenticado y entrega un objeto JSON."""
        normalized_path = path.lstrip("/")
        url = f"{self._base_url}/{normalized_path}"
        if query:
            url = f"{url}?{urlencode(query)}"

        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "FootballVS/0.1",
                "X-Auth-Token": self._api_key,
            },
            method="GET",
        )

        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            messages = {
                400: "football-data.org rejected the request parameters.",
                401: "football-data.org rejected the API key.",
                403: "The current plan cannot access this resource.",
                404: "The requested football-data.org resource was not found.",
                429: "The football-data.org request limit was reached.",
            }
            raise FootballDataRequestError(
                messages.get(error.code, "football-data.org returned an HTTP error."),
                status_code=error.code,
            ) from error
        except URLError as error:
            raise FootballDataRequestError(
                "Could not connect to football-data.org."
            ) from error
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError) as error:
            raise FootballDataRequestError(
                "football-data.org returned an invalid JSON response."
            ) from error

        if not isinstance(payload, dict):
            raise FootballDataRequestError(
                "football-data.org returned an unexpected response shape."
            )

        return payload
