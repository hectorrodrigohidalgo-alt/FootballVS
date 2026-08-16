# Arquitectura técnica

## Arquitectura de producción

FootballVS utiliza un único recurso Azure Static Web Apps Free. Ese recurso
sirve el frontend React y una API Python administrada bajo el mismo dominio.
No existen una Function App, una Storage Account ni una base Cosmos DB
facturables por separado.

```text
football-data.org
        |
        | GitHub Actions: sincroniza, normaliza y calcula
        v
Snapshot SQLite de sólo lectura
        |
        | despliegue seguro
        v
Azure Static Web Apps Free
  ├── Frontend React + Apache ECharts
  └── /api/v1 — Azure Functions administrada (Python 3.11)
        ^
        |
     Navegador
```

La clave de `football-data.org` sólo existe como secreto de GitHub Actions. El
navegador y la API publicada nunca la reciben. Azure usa
`APP_DATA_SOURCE=repository` para leer el snapshot empaquetado.

## Componentes

### Frontend

- React, TypeScript y Vite.
- Tailwind CSS para diseño responsive desde 320 px.
- Apache ECharts cargado bajo demanda para gráficos interactivos.
- TanStack Query para estado remoto, caché y reintentos controlados.
- Fallback SPA y cabeceras defensivas mediante `staticwebapp.config.json`.
- En producción consulta rutas relativas `/api/v1` bajo el mismo dominio.

### API

- Azure Functions con modelo Python v2, administrada por Static Web Apps.
- Runtime de producción Python 3.11; Python 3.12 permanece validado localmente.
- Endpoints anónimos y versionados bajo `/api/v1`.
- Validación de parámetros y respuestas JSON con cabeceras defensivas.

Endpoints:

- `GET /api/v1/health`
- `GET /api/v1/competitions`
- `GET /api/v1/competitions/{id}/teams`
- `GET /api/v1/comparisons?competition={id}&team1={id}&team2={id}&venue={team1|team2|neutral}`

### Datos

- El proveedor es `football-data.org` y la competición inicial usa el código
  `PL`.
- `DataRepository` desacopla la lógica de consulta de la tecnología física.
- SQLite guarda documentos JSON por `entity_type` e identificador estable.
- Cada sincronización usa `upsert`, por lo que repetirla no duplica registros.
- El workflow genera `api/data/footballvs.db` temporalmente; Git lo ignora, pero
  Azure recibe una copia empaquetada de sólo lectura.
- El snapshot publicado incluye como máximo la temporada actual y una anterior.
- El cliente limita solicitudes, reintenta errores transitorios y restringe el
  token al host HTTPS oficial.

Cosmos DB queda únicamente como alternativa futura si el volumen o la
actualización en línea justifican abandonar el snapshot gratuito.

### Modelo estadístico

- Elo mide fortaleza dinámica y procesa partidos por `utc_date`.
- Cada temporada vuelve hacia la media con retención del 40 % y asigna 1400 a
  equipos ascendidos sin historial.
- Poisson estima goles, probabilidades 1X2, más/menos de 2.5, ambos marcan y
  marcadores probables.
- La localía, muestras mínimas y corte temporal forman parte del contrato.
- Dixon-Coles fue evaluado, pero no reemplazó a Poisson al no superar la mejora
  mínima del 1 % acordada.

## Automatización

### Integración continua

`ci.yml` ejecuta calidad de frontend, API, accesibilidad y E2E sin secretos ni
solicitudes al proveedor. Utiliza mocks y repositorios temporales.

### Despliegue

`deploy-static-web-app.yml`:

1. Lee `FOOTBALL_DATA_API_KEY` desde GitHub Secrets.
2. Sincroniza Premier League 2025/26 y 2026/27.
3. Calcula snapshots de equipos y Elo.
4. Compila el frontend.
5. Publica frontend, API y SQLite en Azure Static Web Apps Free.
6. Ejecuta un smoke test público de página, salud, catálogo, equipos y
   comparación real.

El workflow se activa con cada push a `main`, manualmente o todos los días a las
10:17 UTC. La programación sólo entra en vigor cuando el archivo existe en la
rama predeterminada.

## Seguridad y operación

- `.env`, `local.settings.json`, bases SQLite y configuración local de Azure se
  mantienen fuera de Git.
- Los secretos se almacenan en GitHub Secrets; Azure sólo recibe la selección
  no sensible `APP_DATA_SOURCE=repository`.
- El frontend aplica CSP, Permissions Policy, Referrer Policy y protección
  contra detección de tipo.
- La API no almacena ni registra el token del proveedor.
- GitHub Actions conserva el resultado verificable de CI, despliegue y smoke
  test.
- El plan Azure debe permanecer en `Free`; cualquier evolución a servicios
  facturables requiere una decisión explícita.

Consulta [Despliegue y operación](07-despliegue-produccion.md) para comandos de
verificación, mantenimiento y recuperación.
