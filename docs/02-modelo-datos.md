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
- `points`, `win_percentage`, `points_per_game`
- `goals_for`, `goals_against`, `goal_difference`
- `goals_for_per_match`, `goals_against_per_match`
- `clean_sheets`, `both_teams_scored`
- `home_stats`, `away_stats`, `recent_form`

### elo_history

- `id`, `team_id`, `match_id`, `competition_id`, `season_id`, `utc_date`
- `rating_before`, `venue_adjustment`, `expected_score`, `actual_score`
- `rating_change`, `rating_after`, `model_version`, `calculated_at`

Cada partido genera un registro por equipo. La ventaja local queda trazada en
`venue_adjustment`, pero no se incorpora permanentemente a `rating_after`. Los
partidos originales no se modifican durante el cálculo.

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

## Persistencia de producción

El MVP usa SQLite como snapshot documental tanto en desarrollo como en
producción. Una única tabla almacena `entity_type`, `id` y el JSON normalizado;
la clave primaria compuesta hace idempotentes los `upsert`.

GitHub Actions crea `api/data/footballvs.db`, calcula los documentos derivados y
lo empaqueta con la API. El archivo está ignorado por Git y la aplicación
publicada sólo lo consulta; cada despliegue reemplaza el snapshot completo.

Esta decisión evita recursos de almacenamiento facturables y es adecuada para
una competición, dos temporadas y lecturas públicas de baja escala.

## Evolución posible

`DataRepository` permite incorporar otro adaptador sin cambiar normalización,
estadísticas ni modelos. Cosmos DB sólo se evaluará si se requieren escrituras
en línea, varias competiciones o un volumen que deje de ser práctico para el
snapshot. En ese caso deberán medirse consultas, particiones y costo antes de
cambiar la arquitectura.
