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
func.cmd start
```

Comprobar el estado:

```text
GET http://localhost:7071/api/v1/health
```

`local.settings.json` y `.venv/` son locales y no deben publicarse en Git.

## Calidad y pruebas

Desde `api/`, con el entorno virtual preparado:

```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m pytest
```

Las pruebas utilizan únicamente el dataset mock y no necesitan una clave de API.
