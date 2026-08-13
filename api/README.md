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

Endpoints disponibles en los modos `mock` y `repository`:

- `GET /api/v1/competitions`
- `GET /api/v1/competitions/{competition_id}/teams`
- `GET /api/v1/comparisons?competition={id}&team1={id}&team2={id}&venue={team1|team2|neutral}`

`local.settings.json` y `.venv/` son locales y no deben publicarse en Git.

## Calidad y pruebas

Desde `api/`, con el entorno virtual preparado:

```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m pytest
```

Las pruebas usan datos aislados y repositorios temporales; no realizan llamadas al proveedor ni necesitan una clave de API.

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

## Estadísticas agregadas

Después de sincronizar una temporada, calcular y guardar sus snapshots:

```powershell
.venv\Scripts\python.exe -m tools.calculate_team_statistics --season 2026
```

Cada snapshot resume resultados, puntos, goles, porterías a cero, ambos equipos
marcan, rendimiento como local y visitante, y forma de los últimos 5 y 10
partidos. Sólo se incluyen encuentros con estado `FINISHED`; una temporada sin
resultados produce métricas en cero en lugar de datos inventados.

## Fuente de datos de los endpoints

La variable `APP_DATA_SOURCE` selecciona el origen usado por los endpoints de
competiciones y equipos:

- `mock`: datos ficticios, valor predeterminado y modo usado por CI.
- `repository`: documentos reales sincronizados en SQLite.

Para utilizar el repositorio local, establece en `local.settings.json`:

```json
"APP_DATA_SOURCE": "repository",
"FOOTBALLVS_DB_PATH": "data/footballvs.db"
```

El endpoint de equipos toma sólo los participantes presentes en los partidos de
la temporada actual; así evita mezclar clubes históricos almacenados por otras
temporadas.

## Comparación real

Con `APP_DATA_SOURCE=repository`, el endpoint:

```text
GET /api/v1/comparisons?competition=PL&team1={id}&team2={id}&venue={team1|team2|neutral}
```

combina equipos, snapshots e historial directo almacenados en SQLite. La
localía selecciona estadísticas local/visitante y el campo neutral usa los
totales generales. Sólo los enfrentamientos finalizados de la competición se
incluyen en el historial. Hasta implementar la Fase 4, `prediction` y
`elo_rating` son `null` de forma explícita.

## Rating Elo experimental

Para calcular `elo-v0.1.0` cronológicamente sobre todas las temporadas
sincronizadas de Premier League:

```powershell
.venv\Scripts\python.exe -m tools.calculate_elo_ratings
```

El comando persiste dos tipos documentales mediante `upsert`:

- `elo_history`: un registro auditable por equipo y partido.
- `elo_rating`: el rating actual de cada participante de la temporada más reciente.

Repetir el cálculo reemplaza los mismos identificadores y no crea duplicados.
Los partidos originales permanecen intactos. La versión es experimental hasta
completar el backtesting temporal de la Fase 4.

## Baseline Poisson experimental

`poisson_model.py` implementa `poisson-v0.1.0` como una función pura que recibe
partidos, temporadas, equipos, localía y corte temporal. Utiliza como máximo la
temporada actual con peso `1.0` y la anterior con peso `0.4`.

El modelo separa ataque y defensa local/visitante, exige muestras mínimas,
aplica un prior equivalente a tres partidos y genera goles estimados,
probabilidades 1X2, más/menos de 2.5, ambos marcan y matriz de 0–0 a 6–6. En
campo neutral usa fuerzas generales sin asignar ventaja local.

La salida incluye parámetros, fuerzas, tamaños de muestra, `input_data_cutoff`
y `calculated_at`. Todavía no se sirve desde el endpoint público: primero debe
compararse con Dixon-Coles y superar el backtesting temporal.

## Backtesting temporal

Con las temporadas 2023/24, 2024/25 y 2025/26 sincronizadas, ejecutar desde
`api/`:

```powershell
.venv\Scripts\python.exe -m tools.run_backtesting
```

El comando evalúa 2024/25 y 2025/26 en orden cronológico. Cada predicción usa
únicamente partidos anteriores a su `utc_date`; los encuentros sin muestra
suficiente se excluyen y contabilizan. Compara Poisson con Dixon-Coles y prueba
las 180 configuraciones Elo acordadas.

Los archivos `backtesting/results/backtest-summary.json` y
`backtesting/results/backtest-summary.md` contienen sólo métricas agregadas,
parámetros, cobertura y decisión. No publican registros individuales ni datos
originales de los partidos.
