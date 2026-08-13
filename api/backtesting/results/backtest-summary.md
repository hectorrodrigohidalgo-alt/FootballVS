# Resultado del backtesting temporal

- Versión: `temporal-backtest-v0.1.0`
- Competición: `football-data:competition:2021`
- Modelo seleccionado: `poisson-v0.1.0`
- Los resultados no contienen registros individuales de partidos.

## Resultados por temporada

| Temporada | Cobertura | Modelo | Log Loss 1X2 | Brier | Log Loss marcador | Accuracy |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| 2024/25 | 92.89% | Poisson | 0.995697 | 0.594799 | 2.988669 | 51.84% |
| 2024/25 | 92.89% | Dixon-Coles | 0.994778 | 0.594345 | 2.992202 | 51.84% |

`rho` 2024/25: -0.13 con 275 observaciones anteriores.

| 2025/26 | 92.63% | Poisson | 1.045469 | 0.629049 | 2.941780 | 48.01% |
| 2025/26 | 92.63% | Dixon-Coles | 1.043591 | 0.627979 | 2.937865 | 48.30% |

`rho` 2025/26: -0.06 con 628 observaciones anteriores.

## Decisión

| Criterio | Cumplido |
| --- | --- |
| `minimum_coverage` | Sí |
| `maximum_season_regression` | Sí |
| `exact_score_log_loss_improved` | Sí |
| `minimum_relative_improvement` | No |

Mejora relativa de Dixon-Coles en Log Loss 1X2: **0.14%**.

La selección aplica cobertura mínima por temporada, mejora global mínima del 1%, estabilidad temporal y mejora del marcador exacto.

## Evaluación Elo

- Combinaciones evaluadas: **180**.
- MSE promedio baseline: **0.158357**.
- MSE promedio mejor candidato: **0.156879**.
- Mejora relativa: **0.93%**.
- Baseline reemplazado: **No**.
- Configuración seleccionada: K=20, localía=65, retención=75.00%, ascendidos=1400.
