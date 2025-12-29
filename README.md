# Memoir Cloud

A personal photo gallery web application hosted on Azure.

## Status

✅ **Deployed** - Live on Azure!

| Environment | URL |
|-------------|-----|
| **Frontend** | https://blue-pond-076428c0f.2.azurestaticapps.net |
| **Backend API** | https://memoir-api.icystone-ff15642b.eastus.azurecontainerapps.io |

## Azure Resources

| Resource | Name | Location |
|----------|------|----------|
| Resource Group | `rg-memoir-cloud` | East US |
| Storage Account | `stmemoircloudeast` | East US |
| Container Apps Env | `memoir-cloud-env` | East US |
| Container App | `memoir-api` | East US |
| Container Registry | `acrmemorcloud` | East US |
| Static Web App | `memoir-cloud-web` | East US 2 |
| Application Insights | `memoir-insights` | East US |

## Documentation

- [Technical Specification](docs/SPEC.md) - Architecture, API design, and implementation details

## Quick Links

| Component | Description |
|-----------|-------------|
| `frontend/` | React + TypeScript photo gallery UI |
| `backend/` | Python FastAPI server |
| `uploader/` | CLI tool for uploading photos |
| `infra/` | Bicep templates for Azure infrastructure |

## Architecture Overview

```
User → Azure Static Web Apps (React frontend)
         ↓ API calls
       Azure Container Apps (FastAPI backend)
         ↓ reads from
       Azure Blob Storage (photos in quarterly containers)
         ↓ telemetry
       Application Insights (monitoring)
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- npm 9+

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/memoir-cloud.git
   cd memoir-cloud
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ..
   ```

4. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **Install uploader CLI (optional, for development)**
   ```bash
   cd uploader
   pip install -e .
   cd ..
   ```

### Running Locally

The app runs in **demo mode** when no Azure connection string is configured, displaying placeholder images from [picsum.photos](https://picsum.photos).

1. **Start the backend** (in one terminal)
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

2. **Start the frontend** (in another terminal)
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open the app**
   
   Navigate to [http://localhost:3000](http://localhost:3000)

### Environment Variables

For production or to connect to Azure Storage, create a `.env` file in the `backend/` directory:

```env
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_ACCOUNT_NAME=your_account_name
APPLICATIONINSIGHTS_CONNECTION_STRING=your_app_insights_connection_string
```

### Project Structure

```
memoir-cloud/
├── backend/           # FastAPI server
│   └── app/
│       ├── routers/   # API endpoints
│       ├── services/  # Business logic
│       └── models/    # Pydantic schemas
├── frontend/          # React + Vite app
│   └── src/
│       ├── components/
│       ├── pages/
│       └── services/
├── uploader/          # CLI upload tool
├── infra/             # Bicep IaC templates
└── docs/              # Documentation
```

## Using the Uploader

The `memoir-uploader` CLI tool uploads photos to Azure Blob Storage with automatic HEIC conversion, thumbnail generation, and EXIF metadata extraction.

### Configuration

Get your Azure Storage connection string from the Azure Portal:
1. Go to your Storage Account → **Security + networking** → **Access keys**
2. Copy the **Connection string**

Then configure the uploader:

```bash
memoir-uploader config
# Paste your connection string when prompted (input is hidden)
```

### Uploading Photos

```bash
# Preview what will be uploaded (no Azure required)
memoir-uploader upload ~/Pictures/vacation --dry-run

# Upload photos
memoir-uploader upload ~/Pictures/vacation

# Upload recursively with duplicate detection
memoir-uploader upload ~/Pictures --recursive --skip-duplicates

# Override date for photos without EXIF (e.g., scanned photos)
memoir-uploader upload ~/Pictures/scanned --date 1995-06-15
```

### Managing Photos

```bash
# List all containers with photo counts
memoir-uploader list

# List photos in storage
memoir-uploader photos                # Recent photos from all containers
memoir-uploader photos 2024-Q3        # Photos from specific quarter

# View details of a specific photo
memoir-uploader show <photo-id>

# Delete a photo
memoir-uploader delete <photo-id>
memoir-uploader delete <photo-id> --force  # Skip confirmation
```

### Supported Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| JPEG | `.jpg`, `.jpeg` | Native support |
| PNG | `.png` | Native support |
| WebP | `.webp` | Native support |
| HEIC/HEIF | `.heic`, `.heif` | Auto-converted to JPEG |

Photos are automatically organized into quarterly containers (e.g., `2025-q4`) based on EXIF date or file modification time.

## Monitoring with Application Insights

Application Insights tracks telemetry from both the frontend and backend:

- **Page views** - When users navigate through the gallery
- **Photo views** - When users view individual photos
- **API requests** - All backend API calls with latency and errors
- **Custom events** - Session tracking and user interactions

### Viewing Telemetry

1. Go to the [Azure Portal](https://portal.azure.com)
2. Navigate to `rg-memoir-cloud` → `memoir-insights`
3. Use **Logs** to query telemetry with KQL:
   ```kql
   traces
   | where timestamp > ago(1h)
   | order by timestamp desc
   ```

4. Use **Live Metrics** to see real-time traffic

## Azure Deployment

### Prerequisites

- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli) installed
- An Azure subscription

### Deploy Infrastructure

1. **Login to Azure**
   ```bash
   az login
   ```

2. **Create a resource group**
   ```bash
   az group create --name rg-memoir-cloud --location eastus
   ```

3. **Deploy with Bicep (recommended)**
   
   The Bicep templates deploy the full architecture:
   - Azure Container Apps (backend)
   - Azure Static Web Apps (frontend)
   - Azure Container Registry
   - Azure Blob Storage
   - Application Insights + Log Analytics
   
   ```bash
   az deployment group create \
     --resource-group rg-memoir-cloud \
     --template-file infra/main.bicep \
     --parameters environment=prod
   ```

4. **Alternative: Deploy Storage Account only (for uploader)**
   
   If you just want to use the uploader without deploying the web app:
   
   ```bash
   az storage account create \
     --name stmemoircloud2025 \
     --resource-group rg-memoir-cloud \
     --location eastus \
     --sku Standard_LRS \
     --allow-blob-public-access true
   ```

5. **Get the connection string**
   ```bash
   az storage account show-connection-string \
     --name stmemoircloud2025 \
     --resource-group rg-memoir-cloud \
     --output tsv
   ```

6. **Configure the uploader**
   ```bash
   memoir-uploader config
   # Paste the connection string when prompted
   ```

### Clean Up

To delete all resources:

```bash
az group delete --name rg-memoir-cloud --yes
```

## GitHub Actions CI/CD

The project includes a GitHub Actions workflow that automatically deploys on push to `main`.

### Required Secrets

Add these secrets to your GitHub repository (Settings → Secrets → Actions):

| Secret | Description |
|--------|-------------|
| `AZURE_CREDENTIALS` | Azure service principal credentials (JSON) |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Static Web App deployment token |

### Getting the Secrets

1. **Create Azure Service Principal**:
   ```bash
   az ad sp create-for-rbac --name "memoir-cloud-github" \
     --role contributor \
     --scopes /subscriptions/<subscription-id>/resourceGroups/rg-memoir-cloud \
     --json-auth
   ```
   Copy the entire JSON output to `AZURE_CREDENTIALS`.

2. **Grant ACR Push Permission**:
   ```bash
   az role assignment create \
     --assignee <clientId-from-above> \
     --role AcrPush \
     --scope /subscriptions/<subscription-id>/resourceGroups/rg-memoir-cloud/providers/Microsoft.ContainerRegistry/registries/acrmemorcloud
   ```

3. **Get Static Web App Token**:
   ```bash
   az staticwebapp secrets list --name memoir-cloud-web \
     --resource-group rg-memoir-cloud --query "properties.apiKey" -o tsv
   ```
   Copy this to `AZURE_STATIC_WEB_APPS_API_TOKEN`.

### Workflow Triggers

- **Push to main**: Full deployment (backend + frontend)
- **Pull requests**: Build and test only (no deployment)
- **Manual**: Use "Run workflow" button in GitHub Actions tab
