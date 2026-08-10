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

## Control de solicitudes y errores

`FootballDataClient` espera 6,1 segundos entre solicitudes para mantenerse bajo
el límite gratuito de 10 solicitudes por minuto. Ante un límite `429`, errores
transitorios `5xx` o fallos de conexión realiza hasta dos reintentos. La espera
respeta `Retry-After` cuando el proveedor lo informa y, en caso contrario, crece
de forma exponencial. Los errores permanentes de autenticación, permisos,
parámetros o recursos inexistentes se devuelven inmediatamente y nunca incluyen
la clave.

## Normalización

`data_normalizer.py` convierte competiciones, temporadas, equipos y partidos al
contrato interno antes de persistirlos. Cada entidad recibe un identificador
estable como `football-data:team:57`, conserva su `provider_id` y valida campos,
tipos y relaciones obligatorias. Los partidos programados admiten jornada y
marcadores nulos; los registros incompletos se rechazan explícitamente.

## Persistencia y sincronización local

Durante el desarrollo, los datos normalizados se guardan en SQLite mediante el
contrato `DataRepository`. La base predeterminada es `data/footballvs.db` dentro
de `api/` y está ignorada por Git. Los documentos usan una clave primaria
compuesta por tipo e ID; `upsert` reemplaza un documento existente cuando se
repite una sincronización.

Con `local.settings.json` configurado, sincronizar la Premier League 2026/27:

```powershell
.venv\Scripts\python.exe -m tools.sync_football_data --season 2026
```

El resumen muestra cuántos registros se procesaron y los totales almacenados,
pero nunca imprime la clave ni las respuestas crudas. La implementación está
separada del sincronizador para poder añadir un repositorio Cosmos DB sin cambiar
la normalización ni el flujo de descarga.
