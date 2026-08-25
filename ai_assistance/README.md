# AI Care Assistant - Team 4 Plant Guardian

Lightweight FastAPI service that generates clear caretaker instructions from structured plant care data using Groq's fast LLM API.

## Features

- **POST /generate-care-instruction** - Accepts structured plant care data and returns natural-language instructions
- **Strict LLM Constraints** - Never invents or modifies critical details (location, action, amount, timestamp)
- **Pydantic Validation** - Full input/output validation with enums for care actions
- **Groq Integration** - Uses `llama-3.1-8b-instant` for sub-second responses
- **Docker Ready** - Single-container deployment for GCP Compute Engine
- **Environment Config** - Secure API key management via `.env`

## Quick Start

### 1. Local Development

```bash
cd ai_care_assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy env template and add your Groq API key
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Run the service
uvicorn app.main:app --reload --port 8000
```

### 2. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Generate care instruction
curl -X POST http://localhost:8000/generate-care-instruction \
  -H "Content-Type: application/json" \
  -d '{
    "plant_name": "Monstera",
    "species": "Monstera deliciosa",
    "location": "Living Room",
    "specific_spot": "Near east window",
    "action": "water",
    "amount_ml": 500,
    "notes": "Use filtered water",
    "timestamp": "2024-01-15T10:00:00"
  }'
```

### 3. Run Tests

```bash
pytest tests/ -v
```

## Docker Deployment

### Build Image

```bash
docker build -t ai-care-assistant .
```

### Run Container

```bash
docker run -d \
  --name ai-care-assistant \
  -p 8000:8000 \
  --env-file .env \
  ai-care-assistant
```

### Deploy to GCP Compute Engine

```bash
# Tag and push to GitHub Container Registry (or Docker Hub)
docker tag ai-care-assistant ghcr.io/yourusername/ai-care-assistant:latest
docker push ghcr.io/yourusername/ai-care-assistant:latest

# On GCP VM:
docker pull ghcr.io/yourusername/ai-care-assistant:latest
docker run -d --name ai-care-assistant -p 8000:8000 --env-file .env ghcr.io/yourusername/ai-care-assistant:latest
```

## API Reference

### POST /generate-care-instruction

**Request Body:**
```json
{
  "plant_name": "string (1-100 chars)",
  "species": "string (1-100 chars)",
  "location": "string (1-200 chars)",
  "specific_spot": "string (1-200 chars)",
  "action": "water|fertilize|prune|repot|mist|check|move|other",
  "amount_ml": "integer (0-10000, required for water/fertilize/mist)",
  "notes": "string (optional, max 500 chars)",
  "timestamp": "ISO 8601 datetime (optional, defaults to now)"
}
```

**Response:**
```json
{
  "instruction": "Water the Monstera (Monstera deliciosa) in the Living Room near the east window with 500 ml using filtered water.",
  "plant_name": "Monstera",
  "species": "Monstera deliciosa",
  "location": "Living Room",
  "specific_spot": "Near east window",
  "action": "water",
  "amount_ml": 500,
  "notes": "Use filtered water",
  "timestamp": "2024-01-15T10:00:00",
  "generated_at": "2024-01-15T10:00:01"
}
```

### GET /health

Returns service health status.

## Validation Rules

- `amount_ml` **required** for `water`, `fertilize`, `mist` actions
- `amount_ml` **forbidden** for `prune`, `repot`, `check`, `move`, `other` actions
- All string fields have length limits
- Action must be one of the defined enum values

## LLM Behavior Guarantees

The system prompt enforces:
1. **No hallucination** - Only uses provided data
2. **No modification** - Preserves exact location, action, amount, timestamp
3. **No additions** - No frequency, schedule, or advice beyond input
4. **Single sentence** - Concise, natural-language output

## Project Structure

```
ai_care_assistant/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app & endpoints
│   ├── schemas.py       # Pydantic models
│   ├── llm_service.py   # Groq API integration
│   └── prompts.py       # System & user prompts
├── tests/
│   ├── __init__.py
│   └── test_app.py      # Unit & integration tests
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | - | Your Groq API key |
| `GROQ_MODEL` | No | `llama-3.1-8b-instant` | LLM model to use |

## License

MIT - Built for Plant Guardian Hackathon Team 4