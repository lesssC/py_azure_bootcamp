# chambaYA

Kiosco comunitario que conecta las habilidades empíricas de jóvenes periurbanos
con vacantes locales y talleres técnicos, sin exigir un currículum digital.

## Problema y propuesta social

En barrios periurbanos, las vacantes suelen publicarse en papel en bodegas y
mercados. chambaYA digitaliza ese canal: un voluntario carga una fotografía,
Document Intelligence extrae el texto y un agente de Azure OpenAI relaciona la
habilidad del joven con hasta tres oportunidades. El resultado se puede
imprimir como ticket o enviar por SMS en una evolución posterior.

## Los cinco temas del bootcamp

1. **Agentes de IA / Azure AI Foundry:** matching semántico sobre el catálogo y
   OCR de anuncios con Azure AI Document Intelligence.
2. **Docker y Azure Container Apps:** aplicación Streamlit en contenedor,
   `minReplicas: 0` y entrada pública por el puerto 8501.
3. **Azure SQL Database:** catálogo relacional con configuración General
   Purpose Serverless y pausa automática.
4. **VNet y NSG:** Container Apps se integra en `snet-app`; SQL usa Private
   Endpoint en `snet-db`, con NSG asociado y acceso público deshabilitado.
5. **Entra ID, Managed Identity, Key Vault y Azure Monitor:** el Bicep del
   entorno estándar asigna una identidad administrada para ACR, Azure OpenAI,
   Document Intelligence, Key Vault y Azure SQL. Los logs se envían a Log
   Analytics.

El NSG no sustituye un Private Endpoint: la protección de SQL se consigue aquí
con ambos mecanismos.

## Estructura

```text
redsosten-azure/
├── .github/workflows/deploy.yml
├── bicep/main.bicep
├── bicep/modules/resources.bicep
├── sql/schema.sql
└── src/
    ├── app.py
    ├── ai_agent.py              # Fachada de compatibilidad
    ├── services/
    │   ├── config.py            # Secretos, Key Vault y SQL/Entra
    │   ├── catalog.py           # Lectura y escritura de Azure SQL
    │   ├── matching.py          # Azure OpenAI y ticket local
    │   ├── ocr.py               # Azure Document Intelligence
    │   └── announcement.py      # OCR a campos editables
    ├── assets/
    ├── .streamlit/
    ├── Dockerfile
    └── requirements.txt
```

## Arquitectura modular

La aplicación separa la interfaz de Streamlit de los servicios de dominio:

- `app.py` contiene únicamente la composición de pantallas, formularios,
  estados de sesión y mensajes para la persona usuaria.
- `services/config.py` centraliza variables de entorno, Key Vault y la
  autenticación SQL con secreto o Managed Identity.
- `services/catalog.py` encapsula las consultas parametrizadas a
  `OfertasOportunidades` y el estado del catálogo.
- `services/matching.py` contiene el matching con Azure OpenAI y el fallback
  local para tickets.
- `services/ocr.py` contiene la integración con Document Intelligence.
- `services/announcement.py` transforma OCR en propuestas editables sin
  publicar datos automáticamente.
- `ai_agent.py` conserva una fachada pequeña para no romper imports existentes
  ni futuras integraciones.

Esta separación permite probar y cambiar cada integración de Azure sin mezclar
credenciales, consultas SQL y componentes visuales.

## Ejecutar localmente

```powershell
cd src
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example .env
streamlit run app.py
```

Sin variables de Azure, la aplicación usa tres vacantes de demostración. Para
Azure OpenAI local se puede usar `AZURE_OPENAI_API_KEY`; en Azure se recomienda
dejarla vacía y usar `DefaultAzureCredential`. El mismo mecanismo permite
consultar SQL y Document Intelligence sin claves en el código.

### Estado del entorno publicado

La URL publicada actualmente usa un entorno **Container Apps Express**, que no
admite Managed Identity ni integración VNet. Por eso la PoC desplegada conserva
la cadena SQL como secreto de Container Apps y usa secretos administrados para
Azure OpenAI y Document Intelligence. Las claves no están en el código ni en
Git.

El Bicep mantiene el diseño objetivo de producción con Managed Identity,
Private Endpoint y SQL privado. Para activarlo se debe migrar a un entorno
Container Apps estándar; esa migración puede cambiar la URL y no debe hacerse
sobre Express durante una demostración en vivo.

## Aprovisionar Azure con Bicep

Requisitos: Azure CLI, extensión Bicep, Docker y una suscripción con permisos
para crear recursos y asignaciones RBAC.

Primero inicia sesión y obtén el identificador del usuario Entra que será
administrador de SQL:

```powershell
az login
$entraAdminObjectId = az ad signed-in-user show --query id --output tsv
$entraAdminLogin = az ad signed-in-user show --query userPrincipalName --output tsv
```

Construye la imagen y publica el nombre completo en la plantilla. El recurso
Container Apps necesita una imagen que escuche en el puerto 8501:

```powershell
$location = "westus"
$resourceGroup = "rg-redsosten-student"
$deployment = "redsosten-infra"
$sqlPassword = Read-Host "SQL admin password" -AsSecureString
$sqlPasswordPlain = [System.Net.NetworkCredential]::new("", $sqlPassword).Password

az deployment sub create `
  --name $deployment `
  --location $location `
  --template-file bicep/main.bicep `
  --parameters resourceGroupName=$resourceGroup `
    sqlAdminPassword=$sqlPasswordPlain `
    entraAdminObjectId=$entraAdminObjectId `
    entraAdminLogin=$entraAdminLogin `
    containerImage="mcr.microsoft.com/k8se/quickstart:latest"
```

El `quickstart` se incluye solo como imagen inicial de validación de recursos y
usa el puerto 80 por defecto. Para ejecutar la aplicación final, el workflow
publica la imagen y actualiza el puerto a 8501:

```powershell
az containerapp update `
  --name ca-redsosten-kiosco `
  --resource-group $resourceGroup `
  --image "$acrLoginServer/redsosten:latest" `
  --registry-server $acrLoginServer `
  --registry-identity system `
  --target-port 8501
```

También puedes desplegar una imagen propia desde el inicio pasando
`containerTargetPort=8501`.

> Azure SQL Serverless, Container Apps a cero y Log Analytics no significan
> costo total garantizado de cero. Revisa Cost Management y elimina el grupo de
> recursos al terminar la evaluación.

## Preparar el catálogo SQL

Después del despliegue, ejecuta [sql/schema.sql](sql/schema.sql) contra
`sqldb-redsosten`. Como SQL está privado, ejecuta el script desde una máquina
con conectividad a la VNet, por ejemplo un agente temporal o una herramienta
conectada a la red. Después crea el usuario de la identidad de Container Apps
con el administrador Entra:

```sql
CREATE USER [ca-redsosten-kiosco] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [ca-redsosten-kiosco];
```

El nombre anterior debe coincidir con el nombre de la identidad administrada.
El output `managedIdentityPrincipalId` sirve para identificarla; en entornos
con restricciones de resolución del nombre, usa el flujo de creación de
usuario externo soportado por Azure SQL/Entra.

## CI/CD con GitHub Actions

El workflow [deploy.yml](.github/workflows/deploy.yml) valida Python, inicia
sesión mediante OIDC y publica la imagen en ACR antes de actualizar Container
Apps. Configura estos secretos del repositorio:

- `AZURE_CLIENT_ID`: aplicación federada para GitHub Actions.
- `AZURE_TENANT_ID`: identificador del tenant.
- `AZURE_SUBSCRIPTION_ID`: identificador de la suscripción.
- `AZURE_RESOURCE_GROUP`: `rg-redsosten-student`.
- `AZURE_ACR_NAME`: nombre del ACR, sin `.azurecr.io`.

La identidad federada necesita permisos de Contributor sobre el grupo de
recursos y la identidad de Container Apps necesita `AcrPull`, asignado por
Bicep. No uses `AZURE_CREDENTIALS` ni publiques claves de servicio.

Para crear la aplicación federada, registra una aplicación en **Microsoft Entra
ID > App registrations**, agrega una credencial federada con:

- Organization: `lesssC`
- Repository: `py_azure_bootcamp`
- Entity type: `Branch`
- Branch: `main`
- Audience: `api://AzureADTokenExchange`

Asigna a esa aplicación el rol **Contributor** sobre
`rg-redsosten-student`. Después guarda su **Application (client) ID** como
`AZURE_CLIENT_ID`. El tenant es
`c4a66c34-2bb7-451f-8be1-b2c26a430158` y la suscripción es
`8d336fc4-f6af-4475-97e7-c6ca477e661a`.

El deployment activo de Azure OpenAI es `gpt-4-1-mini` sobre
`gpt-4.1-mini` con SKU `GlobalStandard`. `gpt-4o-mini` fue retirado en la
región/fecha de esta entrega y no tiene cuota Standard disponible en la
suscripción.

## Demo

1. Abre la URL de Container Apps.
2. Selecciona una habilidad y genera el ticket.
3. En la pestaña de bodega, carga una foto y ejecuta OCR.
4. Muestra en Azure Portal la revisión activa, los logs de Log Analytics, el
   Private Endpoint y la identidad de Container Apps.

## Checklist final de entrega

### Código fuente y lógica de negocio

- [x] `consultar_vacantes_bd()` desglosa las filas de `pyodbc` por índice para
  evitar duplicar título, dirección, teléfono o requisitos.
- [x] Las credenciales de Azure OpenAI, SQL y Document Intelligence se leen
  desde variables de entorno, secretos de Container Apps, Key Vault o
  `DefaultAzureCredential`; no hay claves en el código.
- [x] El agente devuelve un ticket/SMS con hasta tres opciones, dirección,
  contacto y recomendación, usando el catálogo consultado.
- [x] El flujo OCR permite revisar los campos antes de publicar una oferta en
  Azure SQL.

### Infraestructura y costos

- [x] Azure SQL Serverless usa `autoPauseDelay: 60` en Bicep.
- [x] El diseño estándar de Container Apps define escalado a cero.
- [x] El diseño objetivo incluye `snet-app`, `snet-db`, VNet, NSG, Private
  Endpoint y Private DNS para SQL.
- [ ] El entorno Express publicado debe migrarse a Container Apps estándar para
  activar realmente Managed Identity, VNet y Private Endpoint sin cambiar de
  forma manual la configuración.

### IA y despliegue

- [x] La aplicación llama al endpoint real de Azure OpenAI cuando está
  configurado; conserva un fallback local explícito para desarrollo.
- [x] El despliegue activo documentado es `gpt-4-1-mini` sobre `gpt-4.1-mini`.
  `gpt-4o-mini` no está disponible en la cuota/región actual.
- [x] Document Intelligence procesa fotografías de anuncios y chambaYA
  propone campos editables.

### Repositorio y presentación

- [x] La raíz contiene `bicep/`, `sql/`, `src/`, `.github/workflows/` y
  `README.md`.
- [x] El workflow usa OIDC para GitHub Actions, sin `AZURE_CREDENTIALS`.
- [x] La documentación explica el problema social, la arquitectura Azure y
  el comando `az deployment sub create --location eastus --template-file
  bicep/main.bicep`.
- [x] La marca visible de la aplicación es **chambaYA**, con logo, iconos
  Material Symbols y la paleta terracota, amarillo suave, opal, marfil y
  turquesa.

### Defensa académica

- [ ] Mostrar el recorrido completo: oficio → matching → ticket → OCR →
  validación → catálogo SQL.
- [ ] Explicar cómo PaaS, Serverless, IaC, identidad y monitoreo convierten
  anuncios físicos en oportunidades consultables.
- [ ] Mostrar que Bicep permite repetir o destruir la arquitectura sin
  depender de ClickOps.
