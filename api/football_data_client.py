import json
import os
import time
from collections.abc import Callable, Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

OFFICIAL_HOST = "api.football-data.org"
DEFAULT_BASE_URL = "https://api.football-data.org/v4"
DEFAULT_REQUEST_INTERVAL_SECONDS = 6.1
DEFAULT_MAX_RETRIES = 2
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


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
        request_interval_seconds: float = DEFAULT_REQUEST_INTERVAL_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        opener: Callable[..., Any] = urlopen,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
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

        if timeout_seconds <= 0:
            raise FootballDataConfigurationError(
                "timeout_seconds must be greater than zero."
            )
        if request_interval_seconds < 0:
            raise FootballDataConfigurationError(
                "request_interval_seconds cannot be negative."
            )
        if max_retries < 0:
            raise FootballDataConfigurationError("max_retries cannot be negative.")

        self._api_key = resolved_api_key
        self._base_url = resolved_base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._request_interval_seconds = request_interval_seconds
        self._max_retries = max_retries
        self._opener = opener
        self._clock = clock
        self._sleep = sleep
        self._last_request_at: float | None = None

    def _wait_for_request_slot(self) -> None:
        """Espacia solicitudes para respetar la cuota gratuita del proveedor."""
        if self._last_request_at is not None:
            elapsed = self._clock() - self._last_request_at
            remaining = self._request_interval_seconds - elapsed
            if remaining > 0:
                self._sleep(remaining)
        self._last_request_at = self._clock()

    def _retry_delay(self, error: HTTPError, attempt: int) -> float:
        """Prioriza Retry-After y usa espera exponencial como alternativa."""
        retry_after = error.headers.get("Retry-After") if error.headers else None
        if retry_after:
            try:
                return max(float(retry_after), 0)
            except ValueError:
                pass
        return self._request_interval_seconds * (2**attempt)

    def _open_json(self, request: Request) -> dict[str, Any]:
        """Ejecuta una solicitud, reintentando solo errores transitorios."""
        for attempt in range(self._max_retries + 1):
            self._wait_for_request_slot()
            try:
                with self._opener(
                    request, timeout=self._timeout_seconds
                ) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                if (
                    error.code in RETRYABLE_STATUS_CODES
                    and attempt < self._max_retries
                ):
                    self._sleep(self._retry_delay(error, attempt))
                    continue
                messages = {
                    400: "football-data.org rejected the request parameters.",
                    401: "football-data.org rejected the API key.",
                    403: "The current plan cannot access this resource.",
                    404: "The requested football-data.org resource was not found.",
                    429: "The football-data.org request limit was reached.",
                }
                raise FootballDataRequestError(
                    messages.get(
                        error.code, "football-data.org returned an HTTP error."
                    ),
                    status_code=error.code,
                ) from error
            except URLError as error:
                if attempt < self._max_retries:
                    self._sleep(self._request_interval_seconds * (2**attempt))
                    continue
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

        raise AssertionError("The provider retry loop ended unexpectedly.")

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

        return self._open_json(request)
