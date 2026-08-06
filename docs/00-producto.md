# Definición del producto

## Problema

Comparar equipos suele exigir visitar varias fuentes y traducir tablas aisladas a una lectura común. FootballVS concentrará métricas históricas, forma reciente y estimaciones estadísticas en una experiencia visual única.

## Usuario objetivo

Aficionado al fútbol que desea analizar rápidamente un posible cruce entre dos equipos, sin conocimientos técnicos ni necesidad de registrarse.

## Flujo principal

1. El usuario elige una competición.
2. Selecciona Equipo 1 y Equipo 2.
3. Define localía o campo neutral.
4. El botón `Comparar` se habilita sólo si la selección es válida.
5. El dashboard muestra datos, fecha de actualización y estimaciones del modelo.
6. El usuario cambia equipos o filtros y actualiza la comparación.

## Alcance del MVP

### Incluido

- Diseño responsive para móvil, tablet y escritorio.
- Premier League de Inglaterra como competición inicial, comenzando con la temporada 2026/27.
- Datos básicos obtenidos desde `football-data.org`, ampliables según cobertura y presupuesto.
- Comparación de dos equipos distintos.
- Resumen de partidos jugados, ganados, empatados, perdidos, goles a favor y en contra.
- Forma de los últimos 5 y 10 partidos, separable por localía.
- Enfrentamientos directos cuando existan datos suficientes.
- Rating Elo y su evolución.
- Probabilidades local/empate/visita y matriz de marcadores probables.
- Fecha de última sincronización y manejo explícito de datos insuficientes.

### Fuera del MVP

- Registro, perfiles y roles administrativos.
- Resultados o eventos en vivo.
- Notificaciones, pagos y funciones sociales.
- Plantillas, lesiones y predicciones individuales de jugadores.
- Recomendaciones o asesoría para apuestas.
- Power BI embebido.

## Métricas visibles

- Partidos, victorias, empates y derrotas.
- Porcentaje de victoria y puntos por partido.
- Goles anotados, recibidos y diferencia de gol por partido.
- Porterías a cero y ambos equipos marcan, si la fuente lo permite.
- Forma reciente.
- Historial directo.
- Rating Elo.
- Goles esperados por el modelo (`goles estimados`), no `xG` real.
- Probabilidades 1X2, más/menos de 2.5 goles y marcadores probables.

## Reglas funcionales

- No se permite comparar un equipo consigo mismo.
- La localía es obligatoria porque modifica las probabilidades; campo neutral es una opción válida.
- Si faltan datos, el sistema informa la limitación en vez de inventar valores.
- Toda predicción muestra versión del modelo, fecha de cálculo y periodo de datos.

## Criterios de éxito del MVP

- Comparación usable desde un móvil de 360 px de ancho.
- Respuesta del dashboard en menos de 2 segundos cuando los datos estén precalculados.
- Cero claves secretas expuestas al navegador o al repositorio.
- Sincronización repetible sin duplicar partidos.
- Predicciones evaluadas con división temporal, Log Loss, Brier Score y calibración.
- Pruebas automáticas sobre reglas, transformaciones y endpoints críticos.

## Decisiones de identidad y experiencia

- Nombre definitivo del proyecto: FootballVS.
- Idioma de la aplicación: español.
- No se contempla internacionalización, ya que el proyecto es de uso personal y tiene fines educativos.
- El diseño visual y la identidad gráfica se definirán e implementarán durante la Fase 1.

## Decisiones de datos

- Competición piloto: Premier League de Inglaterra.
- Código del proveedor: `PL`.
- Temporada operativa inicial: 2026/27.
- Proveedor: `football-data.org`, API v4 y plan gratuito.
- El MVP trabajará con resultados, calendario y tablas; no dependerá de estadísticas avanzadas de pago.
- El uso y la conservación de datos respetarán los términos de la cuenta de `football-data.org`; no se publicará una copia del dataset original.
- Antes de entrenar el modelo se comprobará con la API autenticada cuántas temporadas históricas están disponibles para la cuenta gratuita.
