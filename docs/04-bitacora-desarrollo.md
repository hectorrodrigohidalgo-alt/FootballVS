# Bitácora de desarrollo

Última actualización: **12 de agosto de 2026**.

Este documento registra el avance verificable de FootballVS. Se actualiza al finalizar cada punto y distingue entre trabajo implementado localmente, validado y publicado en GitHub.

## Convenciones

- **Completado:** implementado y validado según los criterios del punto.
- **En progreso:** existe trabajo iniciado, pero falta una validación o decisión.
- **Pendiente:** todavía no se ha iniciado.
- Ningún secreto, clave real o valor de `local.settings.json` debe copiarse en esta bitácora.

## Resumen

| Fase | Estado | Avance | Rama de trabajo |
| --- | --- | ---: | --- |
| Fase 0 — Descubrimiento y fundaciones | Completada | 100% | `main` |
| Fase 1 — Esqueleto ejecutable | Completada | 10 de 10 puntos | `main` (integrada) |
| Fase 2 — Datos | Completada | 4 de 4 puntos | `main` (PR `#4`) |
| Fase 3 — Comparador y dashboard | En progreso | 5 de 6 puntos | `feat/Fase-3-Comparador-Dashboard` |
| Fase 4 — Modelo estadístico | Pendiente | 0% | — |
| Fase 5 — Calidad y despliegue | Pendiente | 0% | — |

## Fase 0 — Descubrimiento y fundaciones

Estado: **Completada**.

### Punto 0.1 — Problema, usuario y alcance

- Estado: completado.
- Objetivo: delimitar qué necesidad resuelve FootballVS y para quién.
- Resultado: se definió un usuario aficionado al fútbol, un flujo sin registro y un MVP centrado en comparar dos equipos.
- Decisiones: quedan fuera del MVP autenticación, pagos, apuestas, datos en vivo y predicciones individuales de jugadores.
- Evidencia: `docs/00-producto.md`.

### Punto 0.2 — Métricas y reglas funcionales

- Estado: completado.
- Resultado: se definieron forma reciente, resultados, goles, Elo, probabilidades 1X2 y goles estimados.
- Reglas: no se permite comparar el mismo equipo; la localía es obligatoria; los datos insuficientes se informan explícitamente.
- Decisión: los goles calculados por el modelo no se presentan como xG real.
- Evidencia: `docs/00-producto.md`.

### Punto 0.3 — Stack tecnológico

- Estado: completado.
- Frontend: React, TypeScript, Vite, Tailwind CSS, TanStack Query y Apache ECharts.
- Backend: Python y Azure Functions.
- Datos: `football-data.org` y Azure Cosmos DB.
- Modelo: Elo y Poisson con corrección Dixon-Coles.
- Infraestructura: Azure Static Web Apps, Azure Functions, Cosmos DB y GitHub Actions.
- Evidencia: `README.md` y `docs/01-arquitectura.md`.

### Punto 0.4 — Arquitectura

- Estado: completado.
- Resultado: se definió un monorepo con frontend, API, sincronización, almacenamiento y modelo estadístico separados.
- Decisión: el navegador nunca debe consultar directamente la API externa ni conocer su clave.
- Evidencia: `docs/01-arquitectura.md`.

### Punto 0.5 — Modelo de datos y endpoints

- Estado: completado.
- Resultado: se bosquejaron competiciones, temporadas, equipos, partidos, snapshots, historial Elo, versiones del modelo, predicciones y ejecuciones de sincronización.
- Evidencia: `docs/02-modelo-datos.md`.

### Punto 0.6 — Competición y proveedor inicial

- Estado: completado.
- Competición: Premier League, temporada 2026/27.
- Proveedor: `football-data.org` v4 con plan gratuito.
- Validación posterior: la ventana accesible quedó confirmada en el Punto 9 para 2023/24–2026/27.
- Evidencia: `docs/03-roadmap.md`.

### Punto 0.7 — Seguridad de configuración

- Estado: completado.
- Resultado: `.env`, `local.settings.json`, entornos virtuales, datos y artefactos del modelo quedan ignorados por Git.
- Decisión: sólo se publican plantillas como `.env.example` y `local.settings.json.example`.

### Punto 0.8 — Repositorio y flujo Git

- Estado: completado.
- Resultado: repositorio GitHub creado, rama principal `main`, Conventional Commits y trabajo mediante ramas cortas y pull requests.
- Commit de cierre de la fase: `25a9f06`.

### Punto 0.9 — Licencia

- Estado: completado.
- Resultado: código y documentación propios publicados bajo licencia MIT.
- Restricción: la licencia no concede derechos sobre datasets, escudos, marcas o recursos de terceros.
- Evidencia: `LICENSE` y `README.md`.

## Fase 1 — Esqueleto ejecutable

Estado: **Completada**.

### Punto 1 — Entorno de desarrollo

- Estado: completado.
- Objetivo: disponer de herramientas compatibles y reproducibles.
- Herramientas verificadas:
  - Git `2.52.0`.
  - Node.js `24.19.0` LTS.
  - npm `11.17.0`.
  - Python `3.12.10` de 64 bits.
  - Azure Functions Core Tools v4.
- Decisión: usar entornos locales aislados en lugar de una máquina virtual.
- Nota: en PowerShell se utilizan `npm.cmd` y `func.cmd` para evitar el bloqueo de scripts `.ps1`.

### Punto 2 — Rama de la fase

- Estado: completado y publicado.
- Rama: `feat/Fase-1-Fundacion`.
- Objetivo: mantener `main` estable durante la implementación.
- Publicación: rama disponible en `origin/feat/Fase-1-Fundacion` con integración continua activa.

### Punto 3 — Frontend React

- Estado: completado.
- Implementación:
  - React `19.2.8`.
  - TypeScript `6.0.2`.
  - Vite `8.2.1`.
  - Oxlint `1.75.0`.
  - Instalación reproducible mediante `package-lock.json`.
- Validaciones: lint y build de producción correctos; cero vulnerabilidades reportadas al instalar la plantilla.
- Archivos principales: `frontend/package.json`, `frontend/src/main.tsx` y `frontend/vite.config.ts`.

### Punto 4 — Tailwind y layout responsive

- Estado: completado y aprobado visualmente.
- Implementación:
  - Tailwind CSS `4.3.3` mediante el plugin oficial de Vite.
  - Diseño mobile-first.
  - Encabezado, introducción, competición, dos selectores, localía y botón condicionado.
  - Área reservada para el dashboard.
- Decisión visual: fondo verde musgo oscuro con degradado `#536449 → #2d3b29 → #172117`.
- Accesibilidad: etiquetas asociadas, foco visible, controles nativos y región `aria-live`.
- Validaciones: lint y build correctos.

### Punto 5 — API base con Azure Functions

- Estado: completado.
- Implementación:
  - Azure Functions con modelo Python v2.
  - Entorno aislado `api/.venv`.
  - Dependencia `azure-functions 1.25.0`.
  - Endpoint `GET /api/v1/health`.
  - Configuración local y ejemplo versionable separados.
- Respuesta verificada: HTTP `200` con estado, servicio, versión y timestamp UTC.
- Seguridad: `.venv` y `local.settings.json` permanecen ignorados por Git.
- Archivos principales: `api/function_app.py`, `api/host.json`, `api/requirements.txt` y `api/README.md`.

### Punto 6 — Contrato mock y conexión frontend–API

- Estado: completado y aprobado visualmente.
- Convención: campos JSON en inglés con `snake_case`; textos visibles en español.
- Endpoints implementados:
  - `GET /api/v1/competitions`.
  - `GET /api/v1/competitions/{competition_id}/teams`.
  - `GET /api/v1/comparisons?team1={id}&team2={id}&venue={team1|team2|neutral}`.
- Dataset mock: Arsenal, Chelsea, Liverpool y Manchester City.
- Métricas: resultados, goles por partido, forma reciente, Elo, probabilidades 1X2 y goles estimados.
- Comportamiento: los datos son determinísticos; una misma solicitud produce el mismo resultado.
- Errores: contrato uniforme con `error.code` y `error.message`; estados `400` y `404` verificados.
- Frontend:
  - TanStack Query `5.101.4`.
  - Caché de cinco minutos y un reintento automático.
  - Skeletons, panel de error y botón `Reintentar`.
  - Dashboard tipado y etiqueta visible de datos simulados.
- Validaciones:
  - Endpoints exitosos con HTTP `200`.
  - Selección inválida con HTTP `400`.
  - Recurso inexistente con HTTP `404`.
  - CORS permitido para `http://localhost:5173`.
  - Lint y build del frontend correctos.
- Archivos principales: `api/mock_data.py`, `api/http_responses.py`, `frontend/src/api/`, `frontend/src/components/` y `frontend/src/App.tsx`.

### Punto 7 — Pruebas automáticas

- Estado: completado.
- Fecha: 8 de agosto de 2026.
- Objetivo: detectar regresiones del contrato HTTP y de los flujos principales antes de configurar integración continua.
- Frontend:
  - Vitest `4.1.10`, Testing Library React `16.3.2`, jest-dom `7.0.0`, user-event `14.6.3` y jsdom `30.0.1`.
  - Caché aislada de TanStack Query y reintentos desactivados durante cada prueba.
  - Casos para URL y respuesta del cliente HTTP, traducción de errores, habilitación del botón, envío del formulario, render del dashboard y estado de error.
  - Ejecución con un worker basado en hilos para reducir uso de recursos en local y futuros runners gratuitos.
- API:
  - pytest `9.1.1` y Ruff `0.16.2`, definidos en `requirements-dev.txt`.
  - Casos para salud, competiciones, resúmenes de equipos, comparación determinística, suma de probabilidades y errores `400/404`.
- Resultado: 4 pruebas frontend y 9 pruebas API aprobadas; 13 en total.
- Validaciones adicionales: Oxlint, TypeScript, Ruff y build Vite aprobados.
- Seguridad: las pruebas usan datos mock; no leen ni exponen la clave de `local.settings.json`.
- Archivos principales: `frontend/src/**/*.test.tsx`, `frontend/src/api/client.test.ts`, `frontend/src/test/`, `api/tests/`, `api/pyproject.toml` y `api/requirements-dev.txt`.

### Punto 8 — Integración continua

- Estado: completado.
- Fecha de inicio: 8 de agosto de 2026.
- Objetivo: rechazar automáticamente cambios que rompan la calidad del frontend o la API.
- Implementación local:
  - Workflow `Continuous Integration` para eventos `push`, `pull_request` y ejecución manual.
  - Trabajo `Frontend quality` con Node.js 24, caché npm, instalación reproducible mediante `npm ci`, Oxlint, TypeScript, Vitest y build Vite.
  - Trabajo `API quality` con Python 3.12, caché pip, instalación desde `requirements-dev.txt`, Ruff y pytest.
  - Trabajos independientes sobre `ubuntu-latest`, con límite de diez minutos.
  - Permiso mínimo `contents: read` y cancelación de ejecuciones obsoletas de la misma referencia.
- Validación local:
  - Reconstrucción desde `package-lock.json` aprobada y cero vulnerabilidades reportadas por npm.
  - Frontend: lint, tipos, 4 pruebas y build aprobados.
  - API: reconstrucción de dependencias, Ruff y 9 pruebas aprobados.
- Validación en GitHub:
  - Commit validado: `3d37a1c`.
  - Evento: `push` sobre `feat/Fase-1-Fundacion`.
  - `Frontend quality`: completado correctamente.
  - `API quality`: completado correctamente.
  - Ejecución: `https://github.com/hectorrodrigohidalgo-alt/FootballVS/actions/runs/31277269875`.
- Seguridad: el workflow no recibe secretos ni consulta `football-data.org`; utiliza exclusivamente datos mock.
- Archivo principal: `.github/workflows/ci.yml`.
- Resultado: integración continua activa y aprobada en GitHub Actions.

### Punto 9 — Validación autenticada del proveedor

- Estado: completado.
- Fecha de inicio: 8 de agosto de 2026.
- Proveedor: `football-data.org` API v4 mediante el plan gratuito.
- Implementación:
  - Cliente HTTP reutilizable basado en la biblioteca estándar de Python.
  - Herramienta local que carga `local.settings.json` sin mostrar la clave.
  - Host restringido a `https://api.football-data.org` para evitar enviar el token a otro destino.
  - Pausas de 6,5 segundos entre solicitudes para respetar el límite gratuito.
  - Pruebas simuladas de autenticación, configuración insegura, errores y ventana histórica.
- Validación autenticada:
  - Competición: Premier League, código `PL`, identificador `2021`.
  - Temporada actual informada: 2026/27, con 20 equipos y 10 partidos en la jornada 1.
  - Temporadas accesibles para equipos y partidos: 2026/27, 2025/26, 2024/25 y 2023/24.
  - Primera temporada restringida: 2022/23.
  - El recurso de competición lista 128 temporadas, pero la cuenta no tiene acceso operativo a todas ellas.
  - La ejecución final utilizó 10 solicitudes espaciadas y concluyó correctamente.
- Decisión de datos: entrenar inicialmente con 2023/24–2025/26 y añadir 2026/27 conforme se jueguen partidos.
- Seguridad: la clave no fue mostrada, registrada ni añadida a Git; CI continúa usando sólo mocks.
- Validaciones locales: Ruff aprobado y 16 pruebas API aprobadas.
- Archivos principales: `api/football_data_client.py`, `api/tools/validate_football_data.py` y sus pruebas.
- Resultado: autenticación, cobertura de `PL` y ventana histórica confirmadas.

### Punto 10 — Documentación y cierre de fase

- Estado: completado.
- Objetivo: entregar instrucciones reproducibles, evidencia de calidad y un pull request revisable hacia `main`.
- Documentación preparada:
  - README raíz con estado real del stack, badge de CI e inicio rápido.
  - Guía integral de desarrollo local.
  - Instrucciones específicas para frontend y API.
  - Checklist ampliado de contribución y pull request.
- Validación final local:
  - Enlaces internos de Markdown resueltos correctamente.
  - Oxlint y comprobación TypeScript aprobados.
  - 4 pruebas frontend y build Vite aprobados.
  - Ruff y 16 pruebas API aprobados.
  - `git diff --check` sin errores.
- Cierre en GitHub:
  - Pull request: `https://github.com/hectorrodrigohidalgo-alt/FootballVS/pull/2`.
  - Rama base: `main`.
  - Rama de trabajo: `feat/Fase-1-Fundacion`.
  - Estado del PR: integrado mediante squash en `main`.
  - Commit de integración: `fd26dee` (`#2`).
  - Cierre documental posterior: `0486d72` (`#3`).
  - GitHub Actions del PR: completado correctamente.
  - Ejecución: `https://github.com/hectorrodrigohidalgo-alt/FootballVS/actions/runs/31279018227`.
- Resultado: documentación reproducible y Fase 1 integrada y cerrada en `main`.

## Fase 2 — Datos

Estado: **Completada e integrada**.

### Punto 1 — Integración resiliente del proveedor

- Estado: completado.
- Fecha: 9 de agosto de 2026.
- Objetivo: consumir `football-data.org` sin exponer la clave y respetando las restricciones del plan gratuito.
- Implementación:
  - Intervalo automático de 6,1 segundos entre solicitudes del mismo cliente.
  - Máximo de dos reintentos para `429`, errores HTTP `5xx` transitorios y fallos de conexión.
  - Soporte de la cabecera `Retry-After` y espera exponencial cuando no está disponible.
  - Errores de autenticación, permisos, parámetros y recursos inexistentes sin reintentos innecesarios.
  - Validación de tiempos y cantidad de reintentos al construir el cliente.
  - Dependencias de reloj y espera inyectables para probar el comportamiento sin llamadas ni pausas reales.
- Seguridad: el token permanece únicamente en el backend y nunca se incorpora a mensajes de error.
- Validaciones: Ruff aprobado y 20 pruebas API aprobadas; todas utilizan respuestas simuladas.
- Archivos principales: `api/football_data_client.py` y `api/tests/test_football_data_client.py`.
- Resultado: cliente del proveedor preparado para realizar consultas controladas durante la normalización y sincronización.

### Punto 2 — Normalización de datos

- Estado: completado.
- Fecha: 9 de agosto de 2026.
- Objetivo: desacoplar el formato externo de `football-data.org` del modelo interno de FootballVS.
- Implementación:
  - Normalizadores independientes para competiciones, temporadas, equipos y partidos.
  - Identificadores deterministas con el formato `football-data:{entidad}:{provider_id}`.
  - Conservación de `provider_id` para trazabilidad y futuras sincronizaciones idempotentes.
  - Referencias consistentes entre competición, temporada, equipos y partidos.
  - Fechas de sincronización convertidas a UTC y temporadas con nombre legible, por ejemplo `2026/27`.
  - Soporte de marcadores, jornada y ganador nulos en partidos todavía programados.
  - Rechazo explícito de objetos incompletos, tipos inválidos y marcas horarias sin zona.
- Decisión: no se almacena la respuesta cruda del proveedor; sólo los campos necesarios y validados por el contrato interno.
- Validaciones: Ruff aprobado y 29 pruebas API aprobadas con registros terminados, programados e inválidos.
- Archivos principales: `api/data_normalizer.py` y `api/tests/test_data_normalizer.py`.
- Resultado: entidades estables y listas para persistirse sin depender del formato externo en el resto de la aplicación.

#### Explicación sencilla de la normalización

`football-data.org` entrega información de fútbol usando su propio formato. El
normalizador funciona como un traductor: recibe esos datos, comprueba que estén
completos y los ordena usando siempre las reglas de FootballVS.

Por ejemplo, el proveedor puede identificar al Arsenal con el número `57`. El
normalizador conserva ese número como `provider_id` y además crea la etiqueta
interna estable `football-data:team:57`. Si el equipo vuelve a descargarse, se
genera exactamente la misma etiqueta, lo que permitirá evitar duplicados al
implementar la base de datos.

El archivo `api/data_normalizer.py` realiza cuatro tareas principales:

1. Convierte competiciones, temporadas, equipos y partidos al formato interno.
2. Crea identificadores únicos y conecta cada partido con su competición,
   temporada, equipo local y equipo visitante.
3. Comprueba que los campos obligatorios tengan el tipo y contenido esperados.
4. Permite campos vacíos en partidos aún no jugados, como marcador y ganador.

Si falta información necesaria, se produce un
`FootballDataNormalizationError` y el registro no continúa hacia la futura capa
de persistencia.

El archivo `api/tests/test_data_normalizer.py` actúa como un profesor que revisa
el trabajo del normalizador. Sus pruebas comprueban competiciones, temporadas,
equipos, partidos finalizados, partidos programados y respuestas incompletas o
inválidas. De esta manera, un cambio futuro no puede alterar el contrato interno
sin que las pruebas lo detecten.

El flujo actual puede resumirse así:

```text
football-data.org
       |
       v
data_normalizer.py
       |
       v
Datos limpios, relacionados y listos para guardar
```

En este punto los datos sólo se transforman y validan; todavía no se almacenan
en una base de datos. La persistencia corresponde al Punto 3.

### Punto 3 — Persistencia y sincronización idempotente

- Estado: completado.
- Fecha: 9 de agosto de 2026.
- Objetivo: guardar localmente datos reales y permitir que una sincronización pueda repetirse sin generar duplicados.
- Implementación:
  - Contrato `DataRepository` independiente de una tecnología concreta.
  - Repositorio local SQLite basado en documentos JSON e incluido en Python.
  - Clave primaria compuesta por tipo de entidad e identificador determinista.
  - Operaciones `upsert` que crean documentos nuevos o reemplazan los existentes.
  - Sincronizador de una competición y temporada que descarga primero todos los recursos, después normaliza y finalmente persiste.
  - Herramienta de terminal con configuración local segura y resumen sin claves ni respuestas crudas.
  - Base predeterminada `api/data/footballvs.db`, excluida de Git mediante `data/`.
- Decisión: comenzar con SQLite sin costo y mantener el repositorio desacoplado para añadir Cosmos DB cuando exista una suscripción activa.
- Validaciones automatizadas: Ruff aprobado y 34 pruebas API aprobadas.
- Validación real:
  - Competición `PL`, temporada 2026/27.
  - Primera ejecución: 1 competición, 1 temporada, 20 equipos y 380 partidos procesados.
  - Segunda ejecución: los totales almacenados permanecieron en 1 competición, 1 temporada, 20 equipos y 380 partidos.
  - Resultado: la repetición actualizó los mismos identificadores y no produjo duplicados.
- Archivos principales: `api/data_repository.py`, `api/data_sync.py`, `api/tools/sync_football_data.py` y sus pruebas.
- Trabajo posterior: implementar el adaptador Cosmos DB y un disparador programado cuando la suscripción de Azure esté activa.
- Resultado: datos reales persistidos localmente y sincronización idempotente verificada.

### Punto 4 — Estadísticas agregadas

- Estado: completado técnicamente; pendiente de integración.
- Fecha: 10 de agosto de 2026.
- Objetivo: transformar partidos normalizados en métricas comparables por equipo y temporada.
- Implementación:
  - Snapshots deterministas por equipo, competición y temporada.
  - Partidos, victorias, empates, derrotas, puntos, porcentaje de victoria y puntos por partido.
  - Goles a favor, goles en contra, diferencia y promedios por partido.
  - Porterías a cero y partidos en que ambos equipos marcaron.
  - Estadísticas separadas como local y visitante.
  - Forma cronológica de los últimos 5 y 10 partidos.
  - Exclusión de partidos no finalizados para no inventar resultados.
  - Valores en cero para equipos de una temporada sin partidos finalizados.
  - Herramienta local que calcula y persiste snapshots mediante `upsert`.
- Validaciones automatizadas: Ruff aprobado y 39 pruebas API aprobadas.
- Validación con datos reales:
  - 2025/26: 20 snapshots calculados, con hasta 38 partidos finalizados por equipo.
  - 2026/27: 20 snapshots calculados con métricas iniciales en cero al no existir todavía resultados finalizados.
  - Total local: 40 snapshots almacenados sin publicar la base ni el dataset en Git.
- Archivos principales: `api/team_statistics.py`, `api/tools/calculate_team_statistics.py` y `api/tests/test_team_statistics.py`.
- Resultado: estadísticas precalculadas, reproducibles y listas para alimentar los futuros endpoints de comparación.

### Cierre de la Fase 2

- Pull request: `https://github.com/hectorrodrigohidalgo-alt/FootballVS/pull/4`.
- Estado: integrado mediante squash en `main`.
- Commit de integración: `f645dca` (`#4`).
- GitHub Actions: cuatro verificaciones aprobadas entre eventos `push` y `pull_request`.
- Resultado: Fase 2 cerrada con la rama principal limpia y sincronizada.

## Fase 3 — Comparador y dashboard

Estado: **En progreso**.

### Inicio de fase

- Fecha: 11 de agosto de 2026.
- Rama: `feat/Fase-3-Comparador-Dashboard`.
- Base: commit `f645dca` de `main`.
- Plan: seis puntos controlables para API real, comparación, frontend, gráficos, estados de experiencia y cierre.
- Decisión: Elo permanece en la Fase 4; la Fase 3 preparará el contrato visual sin mostrar valores inventados.

### Punto 1 — Catálogo real para selectores

- Estado: completado.
- Fecha: 11 de agosto de 2026.
- Objetivo: servir competiciones y equipos normalizados desde SQLite sin romper las pruebas ni depender del proveedor en cada consulta.
- Implementación:
  - Contrato `DataCatalog` independiente de la fuente de datos.
  - Catálogo mock conservado para CI y pruebas aisladas.
  - Catálogo de repositorio que transforma documentos internos al contrato público del frontend.
  - Selección mediante `APP_DATA_SOURCE=mock|repository`.
  - Competición pública identificada por código (`PL`) y temporada actual resuelta desde el repositorio.
  - Equipos de los selectores derivados únicamente de los partidos de la temporada actual para excluir participantes históricos.
  - Respuestas con metadato `source` para identificar si los datos provienen de mock o repositorio.
- Validaciones automatizadas: 44 pruebas API aprobadas.
- Validación real local: Premier League 2026/27 y 20 equipos devueltos desde SQLite.
- Archivos principales: `api/data_catalog.py`, `api/function_app.py`, `api/tests/test_data_catalog.py` y `api/tests/test_function_app.py`.
- Resultado: endpoints de competiciones y equipos preparados para alimentar el frontend con datos reales sincronizados.

### Punto 2 — Endpoint real de comparación

- Estado: completado.
- Fecha: 12 de agosto de 2026.
- Objetivo: comparar dos equipos usando snapshots y partidos persistidos, sin métricas predictivas ficticias.
- Implementación:
  - Servicio de comparación desacoplado del endpoint HTTP.
  - Selección de estadísticas generales, locales o visitantes según la localía solicitada.
  - Métricas de resultados, puntos, goles, porterías a cero, ambos marcan y forma reciente.
  - Historial directo limitado a partidos finalizados de la competición seleccionada, ordenado del más reciente al más antiguo.
  - Últimos diez enfrentamientos incluidos junto con victorias de cada equipo y empates.
  - Respuesta `404` uniforme cuando faltan equipos, temporada o snapshots.
  - El modo `mock` permanece disponible para CI; el modo `repository` usa exclusivamente SQLite.
- Decisión de integridad: `prediction` y `elo_rating` son `null` hasta la Fase 4, evitando presentar valores inventados como reales.
- Validaciones automatizadas: Ruff aprobado y 46 pruebas API aprobadas.
- Validación real local: comparación 2026/27 construida desde SQLite con temporada, equipos, métricas, historial y predicción no disponible.
- Archivos principales: `api/comparison_service.py`, `api/function_app.py`, `api/data_catalog.py` y `api/tests/test_comparison_service.py`.
- Resultado: `GET /api/v1/comparisons` puede responder con información trazable del repositorio.

### Punto 3 — Frontend conectado al contrato real

- Estado: completado.
- Fecha: 12 de agosto de 2026.
- Objetivo: permitir que el usuario seleccione datos reales y consulte el nuevo contrato sin romper el modo mock.
- Implementación:
  - Selector de competición alimentado por la API y preparado para más de una opción.
  - Selección automática de la primera competición disponible.
  - Reinicio de equipos y resultados cuando cambia la competición.
  - Consulta de comparación con `competition`, identificadores reales de equipos y localía.
  - Tipos TypeScript ampliados para métricas agregadas, historial directo y disponibilidad del modelo.
  - `prediction` y `elo_rating` aceptan `null` de forma segura.
  - Mensajes visibles para predicción y Elo pendientes, sin presentar datos ficticios como reales.
  - Historial directo utilizado como contenido informativo mientras se desarrolla la visualización completa.
  - Mensaje de error específico cuando todavía no existen snapshots para la selección.
- Validaciones: Oxlint, TypeScript, 5 pruebas frontend y build Vite aprobados.
- Archivos principales: `frontend/src/App.tsx`, `frontend/src/api/types.ts`, `frontend/src/api/client.test.ts`, `frontend/src/App.test.tsx` y `frontend/src/components/ComparisonDashboard.tsx`.
- Resultado: flujo de selección y comparación compatible tanto con datos mock como con SQLite real.

### Punto 4 — Dashboard visual con Apache ECharts

- Estado: completado.
- Fecha: 12 de agosto de 2026.
- Objetivo: transformar las métricas del contrato de comparación en gráficos legibles, interactivos y adaptables a distintos tamaños de pantalla.
- Implementación:
  - Apache ECharts `6.1.0` instalado como dependencia directa del frontend.
  - Registro modular de radar, línea y barras con renderizado SVG para evitar cargar tipos de gráficos que el dashboard no utiliza.
  - Wrapper React reutilizable que crea una sola instancia por contenedor, actualiza sus opciones y libera sus recursos al desmontarse.
  - `ResizeObserver` para recalcular automáticamente el tamaño de cada gráfico cuando cambia su tarjeta o el ancho de la pantalla.
  - Radar normalizado de 0 a 100 para porcentaje de victorias, puntos, ataque, defensa, porterías a cero y forma reciente.
  - Línea de forma reciente que convierte victoria, empate y derrota en 3, 1 y 0 puntos respectivamente.
  - Barras para victorias de cada equipo y empates en el historial directo, acompañadas por una lista textual de resultados.
  - Tarjetas estadísticas ampliadas con puntos por partido, porcentaje de victorias y porterías a cero.
  - Estados vacíos específicos cuando la temporada todavía no tiene resultados o no existen enfrentamientos sincronizados.
  - Texto alternativo y configuración ARIA en los gráficos; la información del historial también permanece disponible como texto.
- Decisiones:
  - Los valores del radar son comparativos y normalizados; no son predicciones ni sustituyen las cifras exactas mostradas en las tarjetas.
  - El eje de ataque usa 3 goles por partido como referencia superior y el de defensa invierte los goles recibidos, de modo que una cifra mayor siempre representa mejor rendimiento.
  - Elo y probabilidades continúan pendientes hasta la Fase 4.
- Pruebas:
  - Conversión de forma a puntos y normalización del radar.
  - Estado sin datos y construcción de las barras del historial.
  - Ciclo de vida del wrapper: inicialización, actualización y liberación de ECharts.
  - Las pruebas generales reemplazan el dibujo SVG por un componente accesible; la integración gráfica se comprueba de forma aislada sin depender de dimensiones inexistentes en JSDOM.
- Validaciones: Oxlint y TypeScript aprobados; 10 pruebas frontend aprobadas; build Vite de producción aprobado.
- Observación: Vite informa que el bundle gráfico supera su umbral recomendado de 500 kB; no bloquea el build y se evaluará división de código durante la optimización de experiencia y rendimiento.
- Archivos principales: `frontend/src/charts/echarts.ts`, `frontend/src/charts/comparisonOptions.ts`, `frontend/src/components/EChart.tsx`, `frontend/src/components/ComparisonCharts.tsx` y sus pruebas.
- Resultado: el comparador presenta radar, evolución de forma e historial directo sin inventar métricas ausentes.

### Punto 5 — Estados de experiencia, responsive y accesibilidad

- Estado: completado y validado visualmente.
- Fecha: 12 de agosto de 2026.
- Objetivo: hacer que el comparador comunique correctamente lo que ocurre durante cada consulta y mantenga su uso en pantallas pequeñas, teclado y tecnologías de asistencia.
- Estados de experiencia:
  - Uso de `isLoading` para distinguir una consulta de equipos realmente activa de una consulta diferida todavía deshabilitada.
  - Estados específicos cuando no existen competiciones o equipos sincronizados.
  - Reintentos independientes: un fallo de competiciones no solicita equipos vacíos y un fallo de equipos no vuelve a descargar competiciones innecesariamente.
  - Skeleton durante la primera comparación y aviso discreto durante una actualización que conserva datos visibles.
  - Errores anunciados mediante `role="alert"` y estados informativos mediante `role="status"`.
- Antigüedad de datos:
  - Umbral acordado de 48 horas calculado desde `model.data_updated_at`.
  - Advertencia informativa que no bloquea la comparación.
  - Manejo seguro de fechas inválidas mediante un estado desconocido, sin romper el dashboard.
- Responsive:
  - Contenido preparado desde 320 px sin desplazamiento horizontal.
  - Tarjetas estadísticas de dos columnas en móviles estrechos y cuatro columnas cuando existe espacio.
  - Nombres, resultados y contenedores gráficos capaces de ajustarse y dividir líneas largas.
  - Formularios y gráficos verificados en vista móvil y escritorio.
- Accesibilidad:
  - Enlace inicial “Saltar al contenido principal” visible al recibir foco.
  - Región de resultados conectada con el botón mediante `aria-controls` y marcada con `aria-busy` durante consultas.
  - Anuncio breve cuando una comparación queda lista, evitando que un lector de pantalla vuelva a leer todo el dashboard.
  - Forma reciente descrita con palabras completas además de sus indicadores visuales V/E/D.
  - Focos visibles en selectores, radios y botones.
  - Preferencia `prefers-reduced-motion` respetada por CSS y por las animaciones de ECharts.
- Pruebas automatizadas:
  - Catálogos vacíos, reintento aislado, región ocupada durante la carga y enlace de navegación rápida.
  - Datos recientes, antiguos e inválidos.
  - Desactivación de animación gráfica cuando el sistema solicita movimiento reducido.
- Validaciones automáticas: Oxlint y TypeScript aprobados; 19 pruebas frontend aprobadas; build Vite aprobado; Ruff y 46 pruebas API aprobadas; `git diff --check` correcto.
- Validación manual confirmada: vista de 320 px sin desbordamiento, dashboard adaptable y enlace de salto visible mediante teclado.
- Observación: la advertencia de Vite por el tamaño del bundle de ECharts permanece como optimización de rendimiento para la Fase 5; no bloquea el build ni el MVP actual.
- Archivos principales: `frontend/src/App.tsx`, `frontend/src/components/DashboardStates.tsx`, `frontend/src/components/ComparisonDashboard.tsx`, `frontend/src/components/ComparisonCharts.tsx`, `frontend/src/components/EChart.tsx`, `frontend/src/utils/dataFreshness.ts` y sus pruebas.
- Resultado: experiencia de comparación comprensible, adaptable y tolerante a estados incompletos o datos antiguos.

### Punto 6 — Validación y cierre de fase

- Estado: en progreso; validación local y revisión previa completadas, pull request pendiente.
- Fecha: 12 de agosto de 2026.
- Objetivo: comprobar el conjunto completo de la Fase 3, actualizar la documentación general y preparar una integración revisable hacia `main`.
- Alcance revisado:
  - 29 archivos modificados o creados respecto de `main` antes de la documentación final.
  - Catálogo y comparación reales, contrato frontend, dashboard ECharts, estados de experiencia, responsive y accesibilidad.
  - Ningún `.env`, `local.settings.json` real ni base `footballvs.db` está versionado.
- Validación local reproducible:
  - Instalación limpia del frontend mediante `npm ci`: 137 paquetes instalados y cero vulnerabilidades reportadas.
  - Oxlint y TypeScript aprobados.
  - 19 pruebas frontend aprobadas en 5 archivos.
  - Build Vite de producción aprobado.
  - Ruff aprobado y 46 pruebas API aprobadas.
  - `git diff --check` sin errores de espacios.
- Validación remota previa:
  - Último commit funcional: `85775e6`.
  - Workflow de evento `push`: completado correctamente.
  - Ejecución: `https://github.com/hectorrodrigohidalgo-alt/FootballVS/actions/runs/31615301178`.
  - No existía otro pull request para la rama al comenzar este punto.
- Documentación corregida: README general actualizado para distinguir capacidades reales actuales, modo mock, modo repositorio y modelo pendiente de la Fase 4; contrato HTTP sincronizado en la documentación de arquitectura y API.
- Observación no bloqueante: Vite continúa informando un bundle superior a 500 kB por Apache ECharts; la optimización mediante división de código se evaluará en la Fase 5.
- Trabajo pendiente para completar el punto: publicar este cierre, crear el pull request, verificar sus checks e integrar mediante squash.

## Próximo paso

Publicar la documentación de cierre, crear el pull request de la **Fase 3** desde terminal y comprobar sus verificaciones automáticas.

## Plantilla para próximas actualizaciones

Al completar un punto nuevo, añadir:

```markdown
### Punto N — Nombre

- Estado: completado | en progreso | pendiente.
- Fecha:
- Objetivo:
- Implementación:
- Decisiones:
- Validaciones:
- Archivos principales:
- Trabajo pendiente:
```
