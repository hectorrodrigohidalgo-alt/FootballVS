# Contribuir a FootballVS

## Flujo de trabajo

1. Mantener `main` estable y desplegable.
2. Crear una rama corta desde `main`: `feat/...`, `fix/...`, `docs/...` o `chore/...`.
3. Hacer cambios pequeños con pruebas y documentación relacionadas.
4. Abrir un pull request en borrador y esperar que CI finalice correctamente.
5. Integrar mediante squash para conservar un historial legible.

## Commits

Usar Conventional Commits:

- `feat: add team selectors`
- `fix: prevent comparing the same team`
- `docs: define prediction metrics`
- `test: cover match normalization`
- `chore: configure frontend linting`

## Criterio de terminado

- El comportamiento solicitado funciona y sus errores son comprensibles.
- Se añadieron o actualizaron pruebas relevantes.
- Lint, tipos, pruebas y build finalizan correctamente.
- No hay secretos ni archivos generados versionados.
- La documentación refleja cualquier decisión pública o técnica nueva.
