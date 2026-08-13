# Modelo estadístico

Este documento registra las reglas, parámetros, pruebas y limitaciones del
modelo de FootballVS. Los valores marcados como provisionales deben validarse
mediante backtesting temporal antes de presentarse como versión definitiva.

## Rating Elo — diseño inicial

Elo representa la fuerza relativa de cada equipo. Antes de un partido convierte
la diferencia entre ratings en un resultado esperado:

```text
E = 1 / (1 + 10 ^ ((rating_rival - rating_equipo) / 400))
```

Después del encuentro actualiza ambos equipos comparando el resultado real con
el esperado:

```text
rating_nuevo = rating_anterior + K × (resultado_real - E)
```

El resultado real vale `1` para victoria, `0.5` para empate y `0` para derrota.
Los puntos ganados por un equipo son los perdidos por el otro.

### Parámetros aprobados provisionalmente

| Parámetro | Valor inicial | Regla |
| --- | ---: | --- |
| Rating inicial | 1500 | Todos los equipos del primer periodo histórico parten iguales. |
| Factor K | 20 | Equilibrio provisional entre adaptación y estabilidad. |
| Ventaja local | 65 | Se suma sólo al calcular el resultado esperado; no se almacena en el rating. |
| Campo neutral | 0 | No aplica ventaja a ningún equipo. |
| Cambio de temporada | 75% | Se conserva el 75% de la diferencia respecto de 1500. |
| Equipo ascendido | 1400 | Hipótesis inicial por el salto competitivo hacia Premier League. |

La primera implementación se identificará como `elo-v0.1.0` y tendrá estado
experimental. Sus parámetros serán inmutables: si el backtesting selecciona
otros valores se creará una versión nueva en vez de sobrescribir el significado
del historial existente.

La regresión entre temporadas se calcula así:

```text
rating_nueva_temporada = 1500 + (rating_anterior - 1500) × 0.75
```

### Decisiones de alcance

- La ventaja local permanece constante aunque exista una racha de derrotas. El
  rating general ya disminuye con esos resultados; modificar también la ventaja
  castigaría dos veces la misma señal.
- Elo utiliza únicamente victoria, empate o derrota. No existe bonificación por
  diferencia de goles; los marcadores se modelarán posteriormente con Poisson.
- Un equipo ascendido puede superar rápidamente los 1400 puntos si sus
  resultados son mejores de lo esperado.
- Todos los partidos deben procesarse cronológicamente y cada predicción debe
  utilizar exclusivamente ratings calculados antes del encuentro.
- Los partidos con el mismo `utc_date` forman un bloque simultáneo: todos se
  predicen con los ratings existentes antes de ese horario y sus cambios se
  aplican sólo después de calcular el bloque completo. El orden interno de la
  base de datos no puede aportar información de otro encuentro simultáneo.
- `utc_date` determina el orden, incluso para encuentros aplazados; `matchday`
  es un dato informativo y nunca reposiciona un partido en el historial.
- El rating no tendrá límites mínimos o máximos artificiales. Se almacenará y
  calculará con precisión completa; sólo su presentación en el dashboard se
  redondeará al entero más cercano.
- En el primer periodo histórico todos los participantes comienzan en 1500. En
  cada temporada posterior sólo se consulta la inmediatamente anterior: un
  equipo presente conserva el 75% de su diferencia respecto de 1500; uno
  ausente se considera ascendido y comienza en 1400. No se recuperan ratings de
  hace dos o más temporadas porque falta información sobre su rendimiento en
  la categoría inferior.

## Evidencia preliminar para el factor K

Se realizó una prueba exploratoria de sólo lectura sobre los 380 partidos
finalizados disponibles localmente para una temporada. Todos los equipos
partieron en 1500 y todavía no se incorporó ventaja local.

| K | Error cuadrático | Log Loss adaptado | Acierto en resultados decisivos |
| ---: | ---: | ---: | ---: |
| 10 | 0.172320 | 0.674442 | 61.23% |
| 20 | 0.168929 | 0.667319 | 61.23% |
| 30 | 0.168056 | 0.665424 | 59.78% |
| 40 | 0.168399 | 0.666210 | 60.14% |

`K=20` se conserva como punto de partida porque obtiene un error cercano al
mínimo y mantiene mayor estabilidad y acierto decisivo que `K=30`. La selección
definitiva requiere las tres temporadas completas, ventaja local, regresión
entre temporadas y una evaluación temporal formal.

## Backtesting temporal de Elo

El resultado observado se codificará como `1` para victoria, `0.5` para empate
y `0` para derrota. La métrica principal será el error cuadrático medio; como
evidencia secundaria se registrarán error absoluto medio, acierto en partidos
con ganador y estabilidad de los ratings, comparados contra un baseline
constante de `0.5`.

Las ventanas respetarán el tiempo:

```text
Procesar 2023/24       → evaluar 2024/25
Procesar hasta 2024/25 → evaluar 2025/26
```

La temporada 2026/27 no formará parte de esta evaluación mientras esté
incompleta. Se probará la cuadrícula de 180 combinaciones formada por:

- `K`: 10, 20, 30 y 40;
- ventaja local: 0, 40, 65, 80 y 100;
- conservación entre temporadas: 50%, 75% y 100%;
- rating de ascendidos: 1400, 1450 y 1500.

La configuración se elegirá por su error cuadrático temporal promedio. Las
métricas secundarias servirán para evitar seleccionar un resultado inestable
cuando la diferencia principal sea mínima. Log Loss, Brier Score y calibración
1X2 se aplicarán al modelo probabilístico de Poisson y Dixon-Coles.

La configuración inicial (`K=20`, ventaja local `65`, conservación `75%` y
ascendido `1400`) sólo será sustituida si otra combinación reduce al menos un
1% relativo su error cuadrático promedio y la mejora se mantiene en ambas
ventanas temporales. Por debajo de ese umbral se conservará la opción inicial
para evitar ajustar el modelo a ruido. En empates se priorizarán menor error
absoluto, mayor estabilidad y parámetros más conservadores.

## Historial auditable

Cada partido producirá dos documentos `elo_history`, uno por equipo, con
identificadores de equipo, partido, competición y temporada; fecha del partido;
rating anterior; ajuste de localía; resultado esperado y real; cambio; rating
posterior; versión del modelo y fecha de cálculo. Esta trazabilidad permitirá
reproducir el proceso y representar la evolución sin modificar los encuentros
normalizados.

## Explicación en el sitio

La información del modelo no aparecerá permanentemente en la página principal.
Al activar el apartado Elo del dashboard se abrirá un diálogo con desplazamiento
interno que explicará en lenguaje sencillo:

- qué representa Elo;
- cómo se ganan y pierden puntos;
- cómo influyen rival y localía;
- cómo se trata el cambio de temporada y los equipos ascendidos;
- qué limitaciones tiene el modelo.

El diálogo conservará la comparación y podrá cerrarse con sus controles, la
tecla `Escape` o una acción fuera del panel, devolviendo el foco al elemento que
lo abrió.
