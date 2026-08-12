# FootballVS Frontend

Interfaz responsive construida con React, TypeScript, Vite, Tailwind CSS, TanStack Query y Apache ECharts.

El dashboard utiliza radar, línea de forma reciente y barras de historial directo. Los gráficos se redimensionan automáticamente y muestran estados vacíos cuando todavía no existen resultados suficientes.

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
