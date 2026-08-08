# Arquitectura técnica

## Decisión

Se utilizará un monorepo con frontend React/TypeScript, API serverless Python y un proceso separado de sincronización y cálculo. Esto mantiene bajo el costo y permite desplegar cada componente de manera independiente.

```text
football-data.org API v4
       |
       v
Sincronizador programado --> Normalización --> Cosmos DB
                                  |
                                  +--> Elo y estadísticas
                                  +--> Entrenamiento/evaluación del modelo
                                                   |
Navegador --> Static Web Apps --> Azure Functions -+
   |                                  |
   +-------- Apache ECharts <---------+
```

## Componentes

### Frontend

- React + TypeScript + Vite.
- Tailwind CSS para diseño responsive.
- Apache ECharts para gráficos interactivos.
- TanStack Query para caché y estado remoto.
- Validación de respuestas de API antes de representarlas.

### API

- Azure Functions con Python.
- Endpoints versionados bajo `/api/v1`.
- La clave del proveedor vive sólo en configuración segura del backend.
- Respuestas precalculadas y cacheables para reducir consumo y latencia.

Endpoints iniciales:

- `GET /api/v1/competitions`
- `GET /api/v1/competitions/{id}/teams`
- `GET /api/v1/teams/{id}/summary`
- `GET /api/v1/comparisons?team1={id}&team2={id}&venue={team1|team2|neutral}`
- `GET /api/v1/health`

### Datos y sincronización

- El proveedor inicial es `football-data.org` y la competición se consulta con el código `PL`.
- El navegador nunca consulta directamente al proveedor externo.
- Una función programada importa cambios respetando límites de uso.
- El plan gratuito admite 10 solicitudes por minuto; el cliente aplicará limitación, reintentos con espera y caché.
- La sincronización no dependerá de datos en vivo: los resultados y calendarios gratuitos pueden llegar con demora.
- Los identificadores externos se conservan junto a identificadores internos.
- La escritura de partidos es idempotente.
- Se registra cada ejecución, rango consultado, resultado y error.
- La disponibilidad histórica se comprobó mediante los recursos autenticados de competición, equipos y partidos: la ventana accesible es 2023/24–2026/27 y 2022/23 está restringida.

### Modelo estadístico

Primera versión:

1. Elo para medir fortaleza dinámica.
2. Poisson para estimar goles de cada equipo.
3. Corrección Dixon-Coles para marcadores bajos y dependencias frecuentes.
4. Ajustes por localía, forma temporal y fuerza ofensiva/defensiva.

No se llamará `xG` a estos goles estimados porque no provienen de eventos de disparo. Una versión posterior podrá comparar Gradient Boosting sólo si existe volumen y calidad suficientes.

## Despliegue objetivo

- Azure Static Web Apps Free: frontend y previews.
- Azure Functions: API y tareas programadas.
- Azure Cosmos DB Free Tier: datos normalizados y resultados precalculados.
- GitHub Actions: validación, build y despliegue.

## Seguridad y observabilidad

- Secretos únicamente en variables locales ignoradas y secretos de Azure/GitHub.
- CORS limitado al dominio de la aplicación.
- Validación de parámetros y límites de consulta.
- Logs estructurados sin claves ni datos sensibles.
- Monitoreo de errores, duración, consumo y última sincronización.
