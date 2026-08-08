# Plan de desarrollo

## Estado actual

- Fase 0: completada e integrada en `main`.
- Fase 1: completada, 10 de 10 puntos, con CI verde e integrada en `main` mediante los PR `#2` y `#3`.
- Próximo objetivo: iniciar la Fase 2 — Datos.

## Fase 0 — Descubrimiento y fundaciones

- [x] Definir problema, usuario, flujo y alcance del MVP.
- [x] Elegir stack y arquitectura objetivo.
- [x] Definir modelo estadístico inicial y evaluación.
- [x] Bosquejar modelo de datos y endpoints.
- [x] Crear estructura, reglas Git y archivos seguros.
- [x] Elegir Premier League, temporada 2026/27, como competición inicial.
- [x] Seleccionar `football-data.org` y validar la cobertura básica y los límites de su plan gratuito.
- [x] Crear repositorio remoto y primer commit.
- [x] Adoptar la licencia MIT para el código y la documentación propios del repositorio.

Salida: alcance acordado, proveedor validado y repositorio base publicado. **Completada.**

### Restricciones confirmadas del proveedor

- API: `football-data.org` v4.
- Competición: Premier League (`PL`), incluida en la cobertura gratuita.
- Plan: Free, 12 competiciones y 10 solicitudes por minuto.
- Datos incluidos: resultados con demora, fixtures/calendario con demora y tablas de posiciones.
- Datos avanzados, estadísticas detalladas y diez temporadas históricas no forman parte del plan gratuito estándar.
- El servicio no se tratará como una fuente de datos abierta: su uso queda sujeto a los términos aceptados al registrar la cuenta y se evitará redistribuir el dataset original.
- La validación autenticada confirmó equipos y partidos para cuatro temporadas: 2023/24–2026/27; 2022/23 está restringida.
- La ventana inicial de entrenamiento será 2023/24–2025/26 y la temporada 2026/27 se incorporará progresivamente.
- La clave se almacenará sólo en variables seguras del backend; nunca en el frontend ni en Git.

## Fase 1 — Esqueleto ejecutable

- [x] Punto 1: preparar y validar el entorno de desarrollo.
- [x] Punto 2: crear la rama `feat/Fase-1-Fundacion`.
- [x] Punto 3: crear el frontend React/TypeScript/Vite.
- [x] Punto 4: configurar Tailwind CSS y el layout responsive.
- [x] Punto 5: crear la API Python con Azure Functions.
- [x] Punto 6: implementar el contrato mock y conectar frontend–API.
- [x] Punto 7: añadir pruebas automáticas y reforzar validaciones locales.
- [x] Punto 8: configurar lint, tipos, pruebas y build en GitHub Actions.
- [x] Punto 9: configurar la clave en backend y comprobar acceso a `PL` y temporadas disponibles.
- [x] Punto 10: completar documentación y cerrar la fase mediante pull request.

Salida: aplicación local y pipeline verde. **Completada.**

Detalle verificable: `docs/04-bitacora-desarrollo.md`.

## Fase 2 — Datos

- [ ] Integrar el proveedor y manejar límites/errores.
- [ ] Normalizar competiciones, equipos y partidos.
- [ ] Persistir datos y ejecutar sincronización idempotente.
- [ ] Calcular estadísticas agregadas.

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
