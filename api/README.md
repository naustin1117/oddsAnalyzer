# NHL Shots Betting Analysis API

FastAPI backend to expose betting predictions and historical results to front-end applications.

## Features

- **Today's Predictions**: Get current day's betting recommendations
- **Upcoming Predictions**: Fetch predictions for upcoming games
- **Historical Results**: Query past predictions with win/loss results
- **Performance Statistics**: Overall and confidence-level specific stats
- **API Key Authentication**: Secure your endpoints
- **CORS Support**: Ready for front-end integration
- **Auto-generated OpenAPI docs**: Interactive API documentation

## Installation

1. Install dependencies:
```bash
pip install -r requirements-api.txt
```

2. Set your API key (optional - defaults to `dev-key-123`):
```bash
export API_KEY_1="your-secure-api-key-here"
```

## Running the API

### Development
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Interactive docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc
- **OpenAPI schema**: http://localhost:8000/openapi.json

## Endpoints

### Health & Info

#### `GET /`
Root endpoint with API information.

**Response:**
```json
{
  "name": "NHL Shots Betting API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

#### `GET /health`
Health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-01T10:30:00",
  "predictions_count": 1523
}
```

### Predictions

#### `GET /predictions/today`
Get today's betting predictions.

**Headers:**
- `X-API-Key`: Your API key (required)

**Query Parameters:**
- `confidence` (optional): Filter by confidence level (`HIGH`, `MEDIUM`, `LOW`)

**Example:**
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8000/predictions/today?confidence=HIGH"
```

**Response:**
```json
{
  "count": 3,
  "predictions": [
    {
      "game_id": "6ae7364b8ba48aeb54053e31ec17198d",
      "nhl_game_id": 2025020003,
      "game_time": "2025-12-01T19:00:00-05:00",
      "away_team": "Toronto Maple Leafs",
      "home_team": "Boston Bruins",
      "player_id": 8478420,
      "player_name": "David Pastrnak",
      "player_team": "Boston Bruins",
      "line": 3.5,
      "over_odds": -115,
      "under_odds": -105,
      "recommendation": "BET OVER 3.5",
      "confidence": "HIGH",
      "edge": 0.087,
      "model_prob": 0.583,
      "implied_prob": 0.496,
      "actual_shots": null,
      "result": null,
      "units_won": null,
      "prediction_date": "2025-12-01T08:00:00"
    }
  ]
}
```

#### `GET /predictions/upcoming`
Get upcoming predictions for the next N days.

**Headers:**
- `X-API-Key`: Your API key (required)

**Query Parameters:**
- `days` (optional): Number of days ahead (1-30, default: 7)
- `confidence` (optional): Filter by confidence level (`HIGH`, `MEDIUM`, `LOW`)

**Example:**
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8000/predictions/upcoming?days=3&confidence=HIGH"
```

### Results

#### `GET /results`
Get historical betting results.

**Headers:**
- `X-API-Key`: Your API key (required)

**Query Parameters:**
- `days` (optional): Number of days back (1-365, default: 30)
- `confidence` (optional): Filter by confidence level (`HIGH`, `MEDIUM`, `LOW`)
- `result` (optional): Filter by result type (`WIN`, `LOSS`, `PUSH`)

**Example:**
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8000/results?days=7&confidence=HIGH&result=WIN"
```

**Response:** Same structure as predictions, but with `actual_shots`, `result`, and `units_won` populated.

### Statistics

#### `GET /stats`
Get overall performance statistics and breakdown by confidence level.

**Headers:**
- `X-API-Key`: Your API key (required)

**Query Parameters:**
- `days` (optional): Limit to last N days (1-365)

**Example:**
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8000/stats?days=30"
```

**Response:**
```json
{
  "overall": {
    "total_bets": 224,
    "wins": 125,
    "losses": 90,
    "pushes": 9,
    "win_rate": 55.8,
    "total_units": -14.53,
    "roi": -6.5
  },
  "by_confidence": [
    {
      "confidence": "HIGH",
      "total_bets": 85,
      "wins": 51,
      "losses": 32,
      "pushes": 2,
      "win_rate": 60.0,
      "total_units": -0.09,
      "roi": -0.1
    },
    {
      "confidence": "MEDIUM",
      "total_bets": 96,
      "wins": 55,
      "losses": 38,
      "pushes": 3,
      "win_rate": 57.3,
      "total_units": -1.78,
      "roi": -1.9
    },
    {
      "confidence": "LOW",
      "total_bets": 43,
      "wins": 22,
      "losses": 20,
      "pushes": 1,
      "win_rate": 51.2,
      "total_units": -12.66,
      "roi": -29.4
    }
  ]
}
```

#### `GET /stats/confidence/{level}`
Get statistics for a specific confidence level.

**Headers:**
- `X-API-Key`: Your API key (required)

**Path Parameters:**
- `level`: Confidence level (`HIGH`, `MEDIUM`, or `LOW`)

**Query Parameters:**
- `days` (optional): Limit to last N days (1-365)

**Example:**
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8000/stats/confidence/HIGH"
```

## Authentication

All endpoints (except `/` and `/health`) require API key authentication via the `X-API-Key` header.

### Setting API Keys

**Development:**
The default API key is `dev-key-123`. You can use this for local testing.

**Production:**
Set environment variables for your API keys:
```bash
export API_KEY_1="your-first-api-key"
```

You can add multiple API keys by adding them to the `API_KEYS` set in `api/config.py`.

### Example with curl
```bash
curl -H "X-API-Key: your-api-key-here" \
  http://localhost:8000/predictions/today
```

### Example with JavaScript fetch
```javascript
fetch('http://localhost:8000/predictions/today', {
  headers: {
    'X-API-Key': 'your-api-key-here'
  }
})
  .then(response => response.json())
  .then(data => console.log(data));
```

### Example with Python requests
```python
import requests

headers = {'X-API-Key': 'your-api-key-here'}
response = requests.get('http://localhost:8000/predictions/today', headers=headers)
data = response.json()
```

## CORS Configuration

By default, the API allows requests from:
- `http://localhost:3000` (React default)
- `http://localhost:5173` (Vite default)
- `http://localhost:8080` (Vue default)

To add your production frontend URL, edit `api/config.py`:

```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-frontend-domain.com",  # Add this
]
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Invalid API Key"
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid confidence level. Must be HIGH, MEDIUM, or LOW"
}
```

### 404 Not Found
```json
{
  "detail": "No verified results found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error loading predictions: ..."
}
```

## Deployment

### Using Docker

Create a `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-api.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t nhl-betting-api .
docker run -p 8000:8000 -e API_KEY_1="your-key" nhl-betting-api
```

### Using Docker Compose

Create a `docker-compose.yml`:
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_KEY_1=your-secure-key-here
    volumes:
      - ./data:/app/data:ro
    restart: unless-stopped
```

Run:
```bash
docker-compose up -d
```

## Development

### Running Tests
```bash
pytest tests/test_api.py
```

### Code Quality
```bash
# Format code
black api/

# Lint
flake8 api/

# Type checking
mypy api/
```

## Front-End Integration Examples

### React with Axios
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'X-API-Key': process.env.REACT_APP_API_KEY
  }
});

// Get today's HIGH confidence predictions
const getTodaysPicks = async () => {
  const response = await api.get('/predictions/today?confidence=HIGH');
  return response.data.predictions;
};

// Get stats
const getStats = async () => {
  const response = await api.get('/stats');
  return response.data;
};
```

### Vue with Fetch
```javascript
const API_BASE = 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY;

export const getTodaysPredictions = async (confidence = null) => {
  const url = confidence
    ? `${API_BASE}/predictions/today?confidence=${confidence}`
    : `${API_BASE}/predictions/today`;

  const response = await fetch(url, {
    headers: { 'X-API-Key': API_KEY }
  });

  return await response.json();
};
```

## Support

For issues or questions, open an issue in the repository.