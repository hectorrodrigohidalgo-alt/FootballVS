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

## Implementación experimental

`api/elo_rating.py` implementa las reglas de `elo-v0.1.0` y produce historial
por partido y ratings actuales. `api/tools/calculate_elo_ratings.py` realiza el
cálculo desde SQLite y persiste ambos tipos mediante identificadores
deterministas.

La primera ejecución local procesó 380 partidos finalizados, generó 760
documentos de historial y 20 ratings actuales. Una segunda ejecución conservó
los mismos totales y la suma global de cambios fue cero. Estos valores todavía
no se sirven en la API: permanecen experimentales hasta completar el
backtesting temporal.

## Poisson — diseño inicial

El baseline Poisson utilizará una ventana móvil máxima de dos temporadas. Los
partidos de la temporada que contiene la fecha de predicción tendrán peso `1.0`
y los de la temporada inmediatamente anterior peso `0.4`. Las temporadas más
antiguas quedarán fuera de la estimación activa, aunque podrán utilizarse como
periodos anteriores en el backtesting.

El peso de 40% evita que una plantilla anterior domine durante toda la nueva
temporada, pero conserva información suficiente al comienzo, cuando todavía se
han jugado pocos encuentros. Este valor es provisional y deberá compararse con
otras ponderaciones sin utilizar partidos posteriores a la predicción.

Poisson calculará por separado ataque y defensa como local y visitante. Cada
fuerza será una razón respecto del promedio de goles local o visitante de la
liga. Para un encuentro entre local `A` y visitante `B`:

```text
goles_esperados_A = promedio_local_liga × ataque_local_A × defensa_visitante_B
goles_esperados_B = promedio_visitante_liga × ataque_visitante_B × defensa_local_A
```

Una fuerza ofensiva superior a `1` representa producción sobre el promedio. En
defensa, un valor inferior a `1` representa menos goles recibidos que el
promedio. La localía se deriva de estos datos separados y no reutiliza los 65
puntos temporales definidos para Elo.

El modelo sólo generará una estimación si, antes de la fecha del encuentro:

- el equipo local posee al menos 5 partidos en condición de local dentro de la
  ventana ponderada;
- el visitante posee al menos 5 partidos en condición de visitante;
- la liga acumula al menos 20 partidos finalizados anteriores.

Si falta cualquiera de estos requisitos, la respuesta indicará datos
insuficientes en vez de inventar una predicción. Un partido de la temporada
anterior cuenta como antecedente disponible aunque su contribución numérica
tenga peso `0.4`.

Superados los mínimos se aplicará un suavizado equivalente a 3 partidos con
rendimiento promedio de liga:

```text
tasa_suavizada =
  (goles_ponderados + promedio_liga × 3)
  / (partidos_ponderados + 3)
```

El prior evita tasas cero o valores extremos después de pocos encuentros. Su
influencia disminuye conforme el equipo acumula más partidos ponderados.

La matriz visible de marcadores abarcará de `0–0` a `6–6` (`7 × 7`). La masa
de probabilidad donde uno o ambos equipos marquen 7 o más goles se conservará
como `probability_outside_matrix`; no se descartará ni redistribuirá. La suma de
la matriz y ese excedente deberá ser igual a 1 dentro de la tolerancia numérica.

En campo neutral se utilizarán ataque y defensa generales calculados con todas
las condiciones y el promedio de goles por equipo de la liga. No se aplicará
ventaja local ni se asignará artificialmente una condición a uno de los clubes.
Cada equipo deberá poseer al menos 10 partidos anteriores y la liga al menos 20;
se conservarán la ventana 100%/40% y el prior de tres partidos.

El baseline se identificará como `poisson-v0.1.0` y generará goles estimados,
probabilidades 1X2, más y menos de 2.5 goles, ambos equipos marcan, matriz de
marcadores, los tres resultados exactos más probables y probabilidad fuera de
matriz. La futura salida `dixon-coles-v0.1.0` se conservará separada para medir
si sus ajustes a marcadores bajos mejoran realmente al baseline.

La implementación vive en `api/poisson_model.py`. Su salida incluye también las
fuerzas calculadas y los tamaños de muestra, permitiendo explicar y reproducir
cada resultado. La validación local inicial usó 380 partidos previos y confirmó
que las probabilidades 1X2 suman 1, al igual que la matriz más su excedente. El
baseline no se publicará en la API antes del backtesting.

### Qué significa la probabilidad de un marcador

Poisson no elige un único resultado como si supiera lo que ocurrirá. Distribuye
la probabilidad entre todos los marcadores posibles a partir de los goles
estimados de cada equipo.

Supongamos que el modelo calcula:

```text
Goles estimados Equipo 1: 2.10
Goles estimados Equipo 2: 0.90
```

Estos valores son medias estadísticas, no un marcador literal: un equipo no
puede anotar `2.10` goles. Significan que, en muchos partidos con condiciones
similares, el promedio se aproximaría a esos valores.

La distribución de Poisson transforma cada media en probabilidades de marcar
exactamente cero, uno, dos o más goles:

```text
P(equipo marca k goles) = e^(-lambda) × lambda^k / k!
```

Donde:

- `lambda` es la media de goles estimada para el equipo;
- `k` es una cantidad exacta de goles: 0, 1, 2, 3, etc.;
- `e` y `k!` forman parte de la distribución matemática de Poisson.

Para calcular un marcador exacto, el baseline asume provisionalmente que las
cantidades de goles de ambos equipos son independientes y multiplica las dos
probabilidades.

Ejemplo ilustrativo:

```text
Probabilidad de que Equipo 1 marque exactamente 2: 27%
Probabilidad de que Equipo 2 marque exactamente 0: 41%

Probabilidad del marcador 2–0:
0.27 × 0.41 = 0.1107 = 11.07%
```

La interpretación correcta es:

> Según las tasas de ataque, defensa, localía y muestra histórica utilizadas,
> aproximadamente 11 de cada 100 partidos estadísticamente similares podrían
> terminar 2–0.

No significa que exista una certeza del 11%, que el marcador vaya a ocurrir ni
que todos los supuestos del modelo representen perfectamente el partido. Una
lesión, expulsión, cambio táctico u otra información ausente puede alterar el
resultado real.

El mismo cálculo se repite para cada celda de la matriz:

| Equipo 1 \ Equipo 2 | 0 goles | 1 gol | 2 goles |
| --- | ---: | ---: | ---: |
| 0 goles | P(0–0) | P(0–1) | P(0–2) |
| 1 gol | P(1–0) | P(1–1) | P(1–2) |
| 2 goles | P(2–0) | P(2–1) | P(2–2) |

FootballVS muestra las celdas entre 0 y 6 goles por equipo. La probabilidad de
resultados con 7 o más goles se conserva como `probability_outside_matrix`, por
lo que la matriz y el excedente continúan sumando 100%.

### Cómo se derivan las demás probabilidades

Las probabilidades del dashboard se obtienen sumando grupos de marcadores de la
misma matriz:

- **Victoria del Equipo 1:** todas las celdas donde sus goles superan los del
  Equipo 2, como 1–0, 2–0, 2–1 o 3–2.
- **Empate:** la diagonal 0–0, 1–1, 2–2, 3–3 y siguientes.
- **Victoria del Equipo 2:** todas las celdas donde marca más goles.
- **Más de 2.5 goles:** resultados con al menos tres goles totales, como 2–1,
  3–0 o 2–2.
- **Menos de 2.5 goles:** resultados con cero, uno o dos goles totales, como
  0–0, 1–0 o 1–1.
- **Ambos equipos marcan:** celdas donde cada equipo tiene al menos un gol,
  como 1–1, 2–1 o 2–3.

Por tanto, goles estimados, marcador exacto, 1X2 y mercados de goles no son
predicciones independientes: todos proceden de las mismas tasas y deben ser
matemáticamente consistentes entre sí.

### Por qué se añadirá Dixon-Coles

El baseline multiplica las probabilidades de gol como si ambos equipos actuaran
de manera independiente. En partidos reales, el estado del marcador puede
cambiar el comportamiento de los dos: con 0–0 cerca del final pueden asumir
menos riesgo, y un primer gol puede modificar el ritmo del encuentro.

Dixon-Coles conserva la estructura de Poisson, pero ajusta específicamente
`0–0`, `1–0`, `0–1` y `1–1`. El parámetro `rho` controla la intensidad y el
sentido de esa corrección. FootballVS no fijará `rho` por intuición: probará
valores históricos y conservará el ajuste sólo si mejora la evaluación temporal
respecto de `poisson-v0.1.0`.

Para estimar `rho` se utilizarán todas las temporadas completas anteriores al
periodo objetivo con el mismo peso. Esta ventana es distinta de las fuerzas
Poisson: `rho` representa un patrón general de dependencia en marcadores bajos,
mientras ataque y defensa conservan su ventana reciente 100%/40%. Ningún
partido de la temporada evaluada o posterior podrá intervenir en la estimación.

### Implementación de Dixon-Coles

La corrección se identifica como `dixon-coles-v0.1.0` y se implementa en
`api/dixon_coles.py`. Recibe las medias de goles producidas por Poisson y
modifica únicamente cuatro marcadores mediante el factor `tau`:

```text
tau(0, 0) = 1 - lambda × mu × rho
tau(0, 1) = 1 + lambda × rho
tau(1, 0) = 1 + mu × rho
tau(1, 1) = 1 - rho
tau(x, y) = 1 para cualquier otro marcador
```

`lambda` y `mu` son los goles esperados de los dos equipos. La probabilidad
Poisson de cada uno de esos cuatro marcadores se multiplica por su `tau`. Los
demás resultados, como 2–0, 2–1 o 3–2, permanecen intactos. Los cuatro cambios
se compensan entre sí, de modo que no se crea ni elimina probabilidad total.

Después del ajuste se vuelven a calcular victoria del Equipo 1, empate,
victoria del Equipo 2 y ambos equipos marcan. Más/menos de 2.5 no cambia porque
los cuatro resultados corregidos poseen como máximo dos goles totales. La
salida registra el modelo base, `rho`, cantidad de partidos usados y fecha de
corte, para poder reproducirla y auditarla.

`rho` se estima automáticamente probando desde `-0.20` hasta `0.20`, en pasos de
`0.01`. Para cada candidato se calcula la probabilidad asignada a cada marcador
histórico exacto y su Log Loss promedio:

```text
Log Loss de marcador exacto = promedio de -log(probabilidad observada)
```

Se selecciona el valor con menor error. Si dos valores empatan se prefiere el
más cercano a cero, evitando una corrección innecesaria. Cualquier candidato
que produzca un `tau` nulo o negativo se descarta.

Para predecir una temporada objetivo, la estimación de `rho` utiliza todos los
partidos finalizados de temporadas completas anteriores, con igual peso. No
utiliza encuentros de la temporada objetivo ni posteriores. Esta regla evita
filtración del futuro y es deliberadamente distinta de la ventana reciente
100%/40% con la que Poisson calcula las fuerzas de ataque y defensa.

## Resultado del backtesting temporal

El backtesting `temporal-backtest-v0.1.0` evaluó progresivamente las temporadas
2024/25 y 2025/26. Cada partido utilizó sólo encuentros con `utc_date`
estrictamente anterior; los partidos simultáneos compartieron el mismo corte.
Las probabilidades se limitaron únicamente para las métricas al intervalo
`0.000001–0.999999` y luego se normalizaron.

Poisson y Dixon-Coles alcanzaron una cobertura de 92.89% en 2024/25 y 92.63%
en 2025/26. Los encuentros restantes se registraron como datos insuficientes y
no recibieron probabilidades inventadas.

| Modelo | Log Loss 1X2 global | Brier global | Log Loss marcador global | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| Poisson | 1.020548 | 0.611900 | 2.965258 | 49.93% |
| Dixon-Coles | 1.019150 | 0.611138 | 2.965072 | 50.07% |

Dixon-Coles mejoró el Log Loss 1X2 un 0.14%. Cumplió cobertura, estabilidad por
temporada y mejora del marcador exacto, pero no alcanzó el umbral relativo de
1%. En consecuencia, `poisson-v0.1.0` permanece como modelo probabilístico
seleccionado y Dixon-Coles conserva estado experimental.

Para Elo se probaron las 180 combinaciones documentadas. El mejor candidato
usó `K=20`, ventaja local `40`, retención `75%` y rating de ascendidos `1400`.
Su MSE promedio fue `0.156879`, frente a `0.158357` del baseline, una mejora de
0.93%. Aunque mejoró ambas ventanas, no alcanzó el 1%; se mantiene
`elo-v0.1.0` con `K=20`, ventaja local `65`, retención `75%` y ascendidos en
`1400`.

Los resultados agregados se versionan en `api/backtesting/results/`. No se
incluyen registros partido por partido ni respuestas originales del proveedor.
