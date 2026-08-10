# Bitácora de desarrollo

Última actualización: **8 de agosto de 2026**.

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
| Fase 2 — Datos | En progreso | 3 de 4 puntos | `feat/Fase-2-Datos` |
| Fase 3 — Comparador y dashboard | Pendiente | 0% | — |
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

Estado: **En progreso**.

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

## Próximo paso

Continuar el **Punto 4 de la Fase 2** con el cálculo de estadísticas agregadas.

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
