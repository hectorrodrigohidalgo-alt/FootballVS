# Despliegue y operación

## Recurso público

- Sitio: `https://ambitious-island-0894cf010.7.azurestaticapps.net`
- Azure Static Web App: `footballvs-web`
- Grupo de recursos: `rg-footballvs`
- Plan esperado: `Free`
- API: Azure Functions administrada bajo `/api/v1`
- Datos de producción: snapshot SQLite con `APP_DATA_SOURCE=repository`

No se requieren Function App, Storage Account, Cosmos DB ni Application
Insights independientes para el MVP.

## Configuración protegida

GitHub Actions requiere estos secretos del repositorio:

- `AZURE_STATIC_WEB_APPS_API_TOKEN`: autoriza únicamente el despliegue del
  recurso Static Web Apps.
- `FOOTBALL_DATA_API_KEY`: permite generar el snapshot durante el workflow.

GitHub muestra los nombres, pero nunca vuelve a mostrar los valores. No deben
copiarse a código, documentación, logs, issues ni pull requests.

Azure contiene esta configuración de aplicación no sensible:

```text
APP_DATA_SOURCE=repository
```

## Flujo de publicación

`deploy-static-web-app.yml` se ejecuta con cada push a `main`, diariamente a las
10:17 UTC y también de forma manual. El workflow sincroniza 2025/26 y 2026/27,
calcula estadísticas y Elo, compila React, despliega y prueba el sitio público.
El cron comienza a operar cuando el workflow está integrado en la rama
predeterminada.

Después de integrar la fase, ejecutar manualmente desde `main`:

```powershell
gh workflow run deploy-static-web-app.yml --ref main
gh run list --workflow deploy-static-web-app.yml --limit 1
```

Para observar una ejecución concreta:

```powershell
gh run watch ID_DE_EJECUCION --exit-status
```

## Comprobaciones públicas

El workflow ejecuta automáticamente:

```powershell
cd api
.venv\Scripts\python.exe -m tools.smoke_test_public_deployment
```

El resultado correcto confirma:

- documento React disponible;
- `/api/v1/health` en estado `ok`;
- catálogo con `meta.source=repository`;
- al menos dos equipos reales;
- comparación con metadata de modelo.

Una comprobación manual mínima puede realizarse con:

```powershell
curl.exe --fail https://ambitious-island-0894cf010.7.azurestaticapps.net/api/v1/health
curl.exe --fail https://ambitious-island-0894cf010.7.azurestaticapps.net/api/v1/competitions
```

## Recuperación

Si el snapshot real causa un error, cambiar temporalmente al catálogo mock:

```powershell
az staticwebapp appsettings set `
  --name footballvs-web `
  --resource-group rg-footballvs `
  --setting-names APP_DATA_SOURCE=mock
```

Después de corregir y desplegar el snapshot, restaurar producción:

```powershell
az staticwebapp appsettings set `
  --name footballvs-web `
  --resource-group rg-footballvs `
  --setting-names APP_DATA_SOURCE=repository
```

## Control de costos

Comprobar periódicamente que el recurso continúa en el plan gratuito:

```powershell
az staticwebapp show `
  --name footballvs-web `
  --resource-group rg-footballvs `
  --query "{Nombre:name,Plan:sku.name,Grupo:resourceGroup}" `
  --output table
```

El presupuesto de Azure envía alertas, pero no bloquea por sí mismo el consumo.
No actualizar a Standard ni añadir servicios facturables sin revisar primero el
impacto.

Cada actualización realiza seis solicitudes principales al proveedor y suele
consumir cerca de dos minutos de GitHub Actions. Este uso debe vigilarse junto
con los límites gratuitos de las cuentas, aunque no añade un recurso facturable
de Azure.

## Mantenimiento de temporada

Las temporadas `2025` y `2026` están declaradas explícitamente en el workflow
para que el dataset sea reproducible. Al comenzar 2027/28 se deben cambiar a
`2026` y `2027`, validar el acceso del plan gratuito y ejecutar el backtesting
antes de publicar el nuevo snapshot.
