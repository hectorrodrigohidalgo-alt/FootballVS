# FootballVS

[![Continuous Integration](https://github.com/hectorrodrigohidalgo-alt/FootballVS/actions/workflows/ci.yml/badge.svg)](https://github.com/hectorrodrigohidalgo-alt/FootballVS/actions/workflows/ci.yml)
[![Deploy Azure Static Web Apps](https://github.com/hectorrodrigohidalgo-alt/FootballVS/actions/workflows/deploy-static-web-app.yml/badge.svg)](https://github.com/hectorrodrigohidalgo-alt/FootballVS/actions/workflows/deploy-static-web-app.yml)

FootballVS es una aplicación web responsive para comparar dos equipos de fútbol
mediante estadísticas históricas, ratings Elo, probabilidades Poisson y
visualizaciones interactivas.

El MVP utiliza Premier League 2025/26 y 2026/27 desde la API v4 de
`football-data.org` mediante su plan gratuito.

**Sitio público:**
[FootballVS en Azure](https://ambitious-island-0894cf010.7.azurestaticapps.net)

## Estado

Las Fases 0 a 4 están completadas. La Fase 5 tiene desplegado el MVP público
con datos reales, calidad automatizada y comprobaciones posteriores a cada
publicación. La rama de la fase se integrará en `main` al completar el cierre
documental.

## MVP

El usuario podrá:

1. Seleccionar una competición y dos equipos distintos.
2. Indicar cuál juega como local o si el encuentro es neutral.
3. Ejecutar la comparación cuando la selección sea válida.
4. Consultar forma reciente, estadísticas agregadas y enfrentamientos directos.
5. Explorar radar, evolución de forma y distribución del historial mediante gráficos interactivos.
6. Consultar ratings Elo, probabilidades 1X2, goles estimados y marcadores más
   probables con información sobre el funcionamiento del modelo.

El MVP no incluye autenticación, pagos, apuestas, datos en vivo ni predicciones de jugadores.

## Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, TanStack Query y Apache ECharts.
- API: Python 3.11 con Azure Functions administrada por Static Web Apps.
- Datos: cliente resiliente de `football-data.org`, normalización,
  sincronización idempotente y snapshot SQLite de sólo lectura.
- Comparación: snapshots estadísticos, filtros por localía e historial directo.
- Modelos: Elo `elo-v0.1.0` y Poisson `poisson-v0.1.0`, seleccionados mediante
  backtesting temporal.
- Calidad: Vitest, Testing Library, Playwright, Axe, pytest, Ruff, Oxlint,
  auditoría de dependencias y GitHub Actions.
- Modos de ejecución: `mock` para desarrollo aislado y CI; `repository` para datos reales sincronizados.
- Despliegue: Azure Static Web Apps Free con API administrada y GitHub Actions.
- Producción: GitHub Actions genera el snapshot, publica el sistema y ejecuta
  un smoke test contra el recorrido real.
- Actualización: el snapshot se reconstruye automáticamente una vez al día y
  también admite ejecución manual.

## Estructura

```text
frontend/       Aplicación web
api/            API HTTP y lógica de aplicación
ml/             Entrenamiento, evaluación y artefactos del modelo
scripts/        Importación y mantenimiento de datos
docs/           Producto, arquitectura y planificación
.github/        Automatización y plantillas de colaboración
```

## Documentación

- [Definición del producto](docs/00-producto.md)
- [Arquitectura técnica](docs/01-arquitectura.md)
- [Modelo de datos](docs/02-modelo-datos.md)
- [Plan de desarrollo](docs/03-roadmap.md)
- [Bitácora de desarrollo](docs/04-bitacora-desarrollo.md)
- [Guía de desarrollo local](docs/05-guia-desarrollo-local.md)
- [Modelo estadístico](docs/06-modelo-estadistico.md)
- [Despliegue y operación](docs/07-despliegue-produccion.md)
- [Forma de contribuir](CONTRIBUTING.md)

## Inicio rápido

Clonar el repositorio y preparar la API:

```powershell
git clone https://github.com/hectorrodrigohidalgo-alt/FootballVS.git
cd FootballVS\api
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item local.settings.json.example local.settings.json
.\.venv\Scripts\Activate.ps1
func.cmd start
```

En una segunda terminal, preparar el frontend:

```powershell
cd FootballVS\frontend
npm.cmd ci
Copy-Item .env.example .env.local
npm.cmd run dev
```

Abrir `http://localhost:5173`. El modo predeterminado usa datos simulados y no requiere una clave real. Para trabajar con datos sincronizados, configura `APP_DATA_SOURCE=repository` y `FOOTBALLVS_DB_PATH` en `api/local.settings.json`. Consulta la [guía local completa](docs/05-guia-desarrollo-local.md) para validaciones, variables y solución de problemas.

## Aviso sobre las predicciones

Las probabilidades de FootballVS son estimaciones estadísticas y no garantizan resultados. No deben presentarse como asesoría de apuestas.

## Licencia

El código y la documentación propios de FootballVS se distribuyen bajo la [licencia MIT](LICENSE).

La licencia MIT no concede derechos sobre datos obtenidos de `football-data.org`, nombres y escudos de equipos, marcas comerciales ni otros recursos de terceros. Esos elementos permanecen sujetos a los términos y derechos de sus respectivos propietarios.
