# Modelo de datos inicial

El esquema se validó contra los campos disponibles en `football-data.org`. Las
entidades normalizadas usan identificadores deterministas con el formato
`football-data:{entidad}:{provider_id}` y conservan el identificador numérico
externo para trazabilidad.

## Entidades

### competition

- `id`, `provider_id`, `code`, `name`, `country`
- `current_season_id`, `last_synced_at`

### season

- `id`, `provider_id`, `competition_id`, `name`, `start_date`, `end_date`

### team

- `id`, `provider_id`, `name`, `short_name`, `tla`
- `crest_url`, `country`, `last_synced_at`

### match

- `id`, `provider_id`, `competition_id`, `season_id`
- `utc_date`, `status`, `matchday`
- `home_team_id`, `away_team_id`
- `home_score`, `away_score`, `winner`
- `updated_at`

La unicidad de `provider_id` hace que la importación sea idempotente.

### team_snapshot

- `team_id`, `competition_id`, `season_id`, `calculated_at`
- `matches`, `wins`, `draws`, `losses`
- `goals_for`, `goals_against`, `points_per_game`
- `home_stats`, `away_stats`, `recent_form`

### elo_history

- `team_id`, `match_id`, `rating_before`, `rating_after`, `calculated_at`

### model_version

- `id`, `algorithm`, `trained_at`, `data_cutoff`
- `parameters`, `metrics`, `artifact_uri`, `status`

### prediction

- `id`, `model_version_id`, `home_team_id`, `away_team_id`
- `venue`, `calculated_at`, `input_data_cutoff`
- `estimated_home_goals`, `estimated_away_goals`
- `home_win_probability`, `draw_probability`, `away_win_probability`
- `over_2_5_probability`, `both_score_probability`, `score_matrix`

### sync_run

- `id`, `provider`, `started_at`, `finished_at`, `status`
- `requested_resource`, `records_read`, `records_written`, `error_summary`

## Particiones propuestas

La partición exacta se decidirá tras medir patrones de acceso. Como punto de partida:

- Partidos por `competition_id` o `season_id`.
- Equipos y snapshots por `team_id`.
- Predicciones por una clave estable de comparación y versión.
- Ejecuciones de sincronización por `provider`.

No se fijará el diseño físico de Cosmos DB hasta validar consultas, volumen y límites del plan gratuito.

## Persistencia local validada

SQLite utiliza temporalmente una tabla documental con clave primaria compuesta
por `entity_type` e `id`. Cada carga ejecuta un `upsert`: crea el documento si no
existe y reemplaza su contenido si ya está guardado. Esta estructura permitió
verificar la idempotencia antes de decidir contenedores y particiones físicas de
Cosmos DB.
