# Memoir Cloud Backend

FastAPI backend for the Memoir Cloud photo gallery.

## Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Storage connection string |
| `AZURE_STORAGE_ACCOUNT_NAME` | Azure Storage account name |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | App Insights connection string |

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/years` - List years with photos
- `GET /api/photos/{year}` - Get photos for a year (paginated)
- `GET /api/photo/{id}` - Get single photo details
- `POST /api/telemetry` - Record telemetry event
