# FootballVS API

API serverless construida con Azure Functions y Python 3.12 mediante el modelo de programación v2.

## Preparación local

Desde PowerShell, dentro de `api/`:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item local.settings.json.example local.settings.json
```

## Ejecución

```powershell
.\.venv\Scripts\Activate.ps1
func.cmd start
```

Comprobar el estado:

```text
GET http://localhost:7071/api/v1/health
```

Endpoints mock disponibles:

- `GET /api/v1/competitions`
- `GET /api/v1/competitions/{competition_id}/teams`
- `GET /api/v1/comparisons?team1={id}&team2={id}&venue={team1|team2|neutral}`

`local.settings.json` y `.venv/` son locales y no deben publicarse en Git.

## Calidad y pruebas

Desde `api/`, con el entorno virtual preparado:

```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m pytest
```

Las pruebas utilizan únicamente el dataset mock y no necesitan una clave de API.

## Validación segura de football-data.org

La clave real debe existir únicamente en `local.settings.json` bajo
`FOOTBALL_DATA_API_KEY`. Para comprobar autenticación, acceso a Premier League y
temporadas recientes:

```powershell
.venv\Scripts\python.exe -m tools.validate_football_data
```

La herramienta respeta el límite gratuito mediante pausas, comprueba equipos y
partidos de la jornada 1, sólo contacta el host HTTPS oficial y nunca imprime la
clave ni las respuestas completas del proveedor.
