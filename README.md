# FootballVS

[![Continuous Integration](https://github.com/hectorrodrigohidalgo-alt/FootballVS/actions/workflows/ci.yml/badge.svg)](https://github.com/hectorrodrigohidalgo-alt/FootballVS/actions/workflows/ci.yml)

FootballVS es una aplicación web responsive para comparar dos equipos de fútbol mediante estadísticas históricas y visualizaciones interactivas. El modelo estadístico se incorporará en la Fase 4.

El MVP comenzará con la Premier League 2026/27 y utilizará la API v4 de `football-data.org` mediante su plan gratuito.

La cuenta gratuita validada permite consultar equipos y partidos desde 2023/24 hasta 2026/27. El entrenamiento inicial utilizará las tres temporadas completas 2023/24–2025/26 y añadirá 2026/27 progresivamente.

## Estado

Las Fases 0, 1 y 2 están completadas e integradas en `main`. La Fase 3 dispone de catálogo y comparaciones reales desde SQLite, dashboard interactivo y experiencia responsive y accesible; actualmente se encuentra en proceso de cierre mediante pull request.

## MVP

El usuario podrá:

1. Seleccionar una competición y dos equipos distintos.
2. Indicar cuál juega como local o si el encuentro es neutral.
3. Ejecutar la comparación cuando la selección sea válida.
4. Consultar forma reciente, estadísticas agregadas y enfrentamientos directos.
5. Explorar radar, evolución de forma y distribución del historial mediante gráficos interactivos.

Elo, probabilidades 1X2 y marcadores estimados corresponden a la Fase 4 y se muestran explícitamente como no disponibles cuando se utilizan datos reales.

El MVP no incluye autenticación, pagos, apuestas, datos en vivo ni predicciones de jugadores.

## Stack

Implementado hasta la Fase 3:

- Frontend: React, TypeScript, Vite, Tailwind CSS, TanStack Query y Apache ECharts.
- API: Python con Azure Functions.
- Datos: cliente resiliente de `football-data.org`, normalización, sincronización idempotente y persistencia local SQLite.
- Comparación: snapshots estadísticos, filtros por localía e historial directo.
- Calidad: Vitest, Testing Library, pytest, Ruff, Oxlint y GitHub Actions.
- Modos de ejecución: `mock` para desarrollo aislado y CI; `repository` para datos reales sincronizados.

Previsto para fases posteriores:

- Persistencia: Azure Cosmos DB.
- Analítica: pandas, NumPy, Elo y Poisson con corrección Dixon-Coles.
- Despliegue: Azure Static Web Apps y Azure Functions.

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
