# FootballVS Frontend

Interfaz responsive construida con React, TypeScript, Vite, Tailwind CSS, TanStack Query y Apache ECharts.

El dashboard utiliza radar, línea de forma reciente y barras de historial directo. Los gráficos se redimensionan automáticamente y muestran estados vacíos cuando todavía no existen resultados suficientes.

## Experiencia y accesibilidad

- Diseño adaptable desde 320 px.
- Estados diferenciados de carga, actualización, vacío y error.
- Advertencia cuando los datos llevan más de 48 horas sin sincronizarse.
- Navegación por teclado con enlace para saltar al contenido principal.
- Regiones de estado para tecnologías de asistencia y soporte de movimiento reducido.
- Auditorías WCAG A/AA con Axe y pruebas responsive en 320, 768 y 1280 px.

## Preparación local

Desde PowerShell, dentro de `frontend/`:

```powershell
npm.cmd ci
Copy-Item .env.example .env.local
```

`VITE_API_BASE_URL` es una URL pública del backend. La clave de `football-data.org` nunca debe agregarse a una variable `VITE_*` ni al frontend.

## Ejecución

Con la API disponible en `http://localhost:7071`:

```powershell
npm.cmd run dev
```

Abrir `http://localhost:5173`.

## Calidad y pruebas

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build
```

`test:watch` mantiene Vitest abierto durante el desarrollo:

```powershell
npm.cmd run test:watch
```

Las pruebas simulan las respuestas HTTP; no necesitan ejecutar Azure Functions ni disponer de una clave real.

## Pruebas end-to-end

La suite Playwright inicia Vite en `http://localhost:5273` y Azure Functions en
`http://localhost:7171`, ambos en puertos exclusivos para no interferir con el
desarrollo normal. El backend usa datos mock y no requiere API key ni SQLite.

La primera vez, instalar únicamente Chromium:

```powershell
npx playwright install chromium
```

Después ejecutar escritorio y móvil:

```powershell
npm run test:e2e
```

Azure Functions Core Tools debe estar instalado y `api/.venv` preparado con
`api/requirements-dev.txt`. Los reportes y evidencias de fallos permanecen
ignorados por Git. En CI, la validación E2E es obligatoria y publica el reporte
HTML como artefacto.
