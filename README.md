# FootballVS

FootballVS es una aplicación web responsive para comparar dos equipos de fútbol mediante estadísticas históricas, visualizaciones interactivas y probabilidades estimadas por un modelo estadístico.

El MVP comenzará con la Premier League 2026/27 y utilizará la API v4 de `football-data.org` mediante su plan gratuito.

## Estado

Fase 0 completada — definición y fundaciones del proyecto.

## MVP

El usuario podrá:

1. Seleccionar una competición y dos equipos distintos.
2. Indicar cuál juega como local o si el encuentro es neutral.
3. Ejecutar la comparación cuando la selección sea válida.
4. Consultar forma reciente, resultados históricos, enfrentamientos directos y evolución Elo.
5. Ver probabilidades de victoria, empate y derrota, además de marcadores probables.

El MVP no incluye autenticación, pagos, apuestas, datos en vivo ni predicciones de jugadores.

## Stack previsto

- Frontend: React, TypeScript, Vite, Tailwind CSS y Apache ECharts.
- API: Python con Azure Functions.
- Datos: API externa de fútbol y Azure Cosmos DB.
- Analítica: pandas, NumPy, Elo y Poisson con corrección Dixon-Coles.
- Infraestructura: Azure Static Web Apps, Azure Functions, Cosmos DB y GitHub Actions.

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
- [Forma de contribuir](CONTRIBUTING.md)

## Configuración local

La instalación de las aplicaciones se realizará en la Fase 1. Las variables previstas están documentadas en `.env.example`; nunca deben guardarse claves reales en Git.

## Aviso sobre las predicciones

Las probabilidades de FootballVS son estimaciones estadísticas y no garantizan resultados. No deben presentarse como asesoría de apuestas.

## Licencia

El código y la documentación propios de FootballVS se distribuyen bajo la [licencia MIT](LICENSE).

La licencia MIT no concede derechos sobre datos obtenidos de `football-data.org`, nombres y escudos de equipos, marcas comerciales ni otros recursos de terceros. Esos elementos permanecen sujetos a los términos y derechos de sus respectivos propietarios.
