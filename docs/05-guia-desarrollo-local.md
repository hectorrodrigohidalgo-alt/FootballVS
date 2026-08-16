# Guía de desarrollo local

Esta guía permite levantar FootballVS desde un clon limpio en Windows PowerShell. El modo predeterminado usa datos mock; el modo `repository` utiliza competiciones, equipos, snapshots e historial real sincronizados en SQLite.

## Requisitos

| Herramienta | Versión validada | Uso |
| --- | --- | --- |
| Git | 2.52.0 | Control de versiones |
| Node.js | 24.19.0 LTS | Frontend y pruebas |
| npm | 11.17.0 | Dependencias frontend |
| Python | 3.12.10, 64 bits | API y pruebas |
| Azure Functions Core Tools | v4 | Host local de la API |

En PowerShell se recomienda usar `npm.cmd` y `func.cmd` para evitar conflictos con los wrappers `.ps1`.

## 1. Clonar el repositorio

```powershell
git clone https://github.com/hectorrodrigohidalgo-alt/FootballVS.git
cd FootballVS
```

Para probar una rama de trabajo concreta:

```powershell
git switch nombre-de-la-rama
```

## 2. Preparar la API

Desde la raíz:

```powershell
cd api
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item local.settings.json.example local.settings.json
```

El archivo `local.settings.json` es local e ignorado por Git. El modo mock funciona con los valores de ejemplo. Para validar o sincronizar el proveedor real, reemplaza `replace_me` por tu clave dentro de este archivo sin compartirla.

Iniciar Azure Functions:

```powershell
.\.venv\Scripts\Activate.ps1
func.cmd start
```

La API queda disponible en `http://localhost:7071`. Comprobar salud:

```powershell
Invoke-RestMethod http://localhost:7071/api/v1/health
```

## 3. Preparar el frontend

Abre una segunda terminal en la raíz del repositorio:

```powershell
cd frontend
npm.cmd ci
Copy-Item .env.example .env.local
npm.cmd run dev
```

Abrir `http://localhost:5173`. Mantén la API y Vite ejecutándose en terminales diferentes.

## 4. Ejecutar las validaciones

Frontend, desde `frontend/`:

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build
```

API, desde `api/`:

```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m pytest
```

Las pruebas y GitHub Actions usan respuestas simuladas y repositorios temporales; nunca necesitan la clave real ni realizan llamadas al proveedor.

## 5. Validar el proveedor real

Con `FOOTBALL_DATA_API_KEY` configurada únicamente en `api/local.settings.json`, desde `api/`:

```powershell
.venv\Scripts\python.exe -m tools.validate_football_data
```

La herramienta sólo contacta `https://api.football-data.org`, pausa entre solicitudes y presenta un resumen sin token ni respuestas completas. No es necesaria para levantar el modo mock.

## 6. Usar datos reales desde SQLite

Configura estas variables dentro de `api/local.settings.json`:

```json
{
  "APP_DATA_SOURCE": "repository",
  "FOOTBALLVS_DB_PATH": "data/footballvs.db"
}
```

Después sincroniza la temporada y calcula sus snapshots desde `api/`:

```powershell
.venv\Scripts\python.exe -m tools.sync_football_data --season 2026
.venv\Scripts\python.exe -m tools.calculate_team_statistics --season 2026
```

Reinicia Azure Functions después de cambiar `APP_DATA_SOURCE`. La base SQLite
permanece dentro de `api/data/` y no se publica en Git. En producción, GitHub
Actions genera otra copia temporal y la empaqueta como snapshot de sólo lectura.

## 7. Endpoints locales

| Método | Ruta | Fuente actual |
| --- | --- | --- |
| GET | `/api/v1/health` | Proceso local |
| GET | `/api/v1/competitions` | Mock o repositorio |
| GET | `/api/v1/competitions/{competition_id}/teams` | Mock o repositorio |
| GET | `/api/v1/comparisons?competition={id}&team1={id}&team2={id}&venue={team1\|team2\|neutral}` | Mock o repositorio |

Equipos mock disponibles: `arsenal`, `chelsea`, `liverpool` y `manchester-city`.

## 8. Seguridad local

- No añadir `.env`, `.env.local` ni `local.settings.json` a Git.
- No colocar la clave en variables que comiencen con `VITE_`; Vite las expone al navegador.
- Versionar sólo `.env.example` y `local.settings.json.example` con valores ficticios.
- No copiar claves en capturas, logs, commits, issues o pull requests.
- Configurar la clave como GitHub Secret para el despliegue; Azure no necesita
  conocerla y `local.settings.json` nunca se publica.

## 9. Problemas frecuentes

### npm indica que no existe el script `dev`

Comprueba que la terminal esté dentro de `frontend/`:

```powershell
Get-Location
npm.cmd run
```

### PowerShell bloquea `npm.ps1`

Usa `npm.cmd` en los comandos del proyecto.

Si PowerShell bloquea también `Activate.ps1`, permite scripts sólo para la terminal actual y vuelve a activarlo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### `npm ci` devuelve `EPERM` sobre Tailwind

Detén `npm.cmd run dev` con `Ctrl+C` antes de reinstalar dependencias. Un proceso Vite abierto puede mantener bloqueado el binario nativo.

### El frontend no conecta con la API

Confirma que Azure Functions escuche en `http://localhost:7071` y que `frontend/.env.local` contenga:

```text
VITE_API_BASE_URL=http://localhost:7071/api/v1
```

Reinicia Vite después de modificar variables `.env`.

### El verificador rechaza la configuración

Comprueba localmente que `FOOTBALL_DATA_API_KEY` ya no tenga `replace_me` y que `FOOTBALL_DATA_BASE_URL` siga apuntando al host HTTPS oficial. No pegues esos valores en reportes o conversaciones.
