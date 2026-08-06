# Plan de desarrollo

## Fase 0 — Descubrimiento y fundaciones

- [x] Definir problema, usuario, flujo y alcance del MVP.
- [x] Elegir stack y arquitectura objetivo.
- [x] Definir modelo estadístico inicial y evaluación.
- [x] Bosquejar modelo de datos y endpoints.
- [x] Crear estructura, reglas Git y archivos seguros.
- [ ] Elegir competición/temporada inicial.
- [ ] Validar cobertura, licencia y límites reales del proveedor.
- [ ] Crear repositorio remoto y primer commit.

Salida: alcance acordado, proveedor validado y repositorio base publicado.

## Fase 1 — Esqueleto ejecutable

- Crear frontend React/TypeScript/Vite.
- Crear Azure Functions Python.
- Añadir lint, tipos, pruebas y build en CI.
- Implementar layout responsive y contrato API simulado.

Salida: aplicación local y pipeline verde.

## Fase 2 — Datos

- Integrar proveedor y manejar límites/errores.
- Normalizar competiciones, equipos y partidos.
- Persistir datos y ejecutar sincronización idempotente.
- Calcular estadísticas agregadas.

Salida: datos reales consultables y trazables.

## Fase 3 — Comparador y dashboard

- Selectores y validaciones.
- Endpoint de comparación.
- Tarjetas, forma reciente, radar, Elo e historial directo.
- Estados de carga, vacío, error y datos antiguos.

Salida: comparación completa sin predicción avanzada.

## Fase 4 — Modelo

- Implementar Elo y baseline Poisson.
- Añadir corrección Dixon-Coles y localía.
- Backtesting temporal y calibración.
- Versionar y servir predicciones.

Salida: estimaciones reproducibles y evaluadas.

## Fase 5 — Calidad y despliegue

- Pruebas end-to-end, accesibilidad, rendimiento y seguridad.
- Aprovisionar servicios Azure gratuitos.
- Configurar secretos, observabilidad y despliegues.
- Completar documentación técnica y de usuario.

Salida: MVP público.

## Hitos y versiones sugeridas

- `v0.1.0`: fundaciones.
- `v0.2.0`: pipeline de datos.
- `v0.3.0`: API de comparación.
- `v0.4.0`: dashboard interactivo.
- `v0.5.0`: modelo predictivo.
- `v1.0.0`: MVP público.
