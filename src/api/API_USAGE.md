# OSC FastAPI Usage Guide

Complete REST API for all OSCFacade operations.

## Quick Start

```bash
# Install dependencies
pip install fastapi uvicorn

# Set environment variables
export OPENAI_API_KEY="your-key"
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/osc"

# Run the server
uvicorn src.api.app:app --reload --port 8000

# Access interactive docs
open http://localhost:8000/docs
```

## API Endpoints

### Natural Language Generation

#### Generate SML from Natural Language
```bash
POST /facade/nl/clip-to-sml
Content-Type: application/json

{
  "text": "Create a C major scale, quarter notes, 2 bars"
}

# Response
{
  "sml": {
    "name": "generated-clip",
    "bars": [
      {
        "bar_index": 0,
        "items": [
          {"note": "C4", "duration": "quarter"},
          {"note": "D4", "duration": "quarter"},
          ...
        ]
      }
    ]
  }
}
```

#### Generate and Store to Database
```bash
POST /facade/nl/clip-to-db
Content-Type: application/json

{
  "text": "Create a jazzy bass line in F, 4 bars"
}

# Response: 42 (clip_id)
```

### SML/DSL Conversion

#### Convert SML Clip to DSL
```bash
POST /facade/sml/clip-to-dsl
Content-Type: application/json

{
  "name": "my-riff",
  "bars": [
    {
      "bar_index": 0,
      "items": [
        {"note": "C4", "duration": "quarter"},
        {"note": "E4", "duration": "quarter"}
      ]
    }
  ]
}

# Response: DSL clip format
{
  "name": "my-riff",
  "bars": [...],
  "notes": [...]
}
```

#### Convert SML Composition to DSL
```bash
POST /facade/sml/composition-to-dsl
Content-Type: application/json

{
  "project": {
    "name": "my-song",
    "ticks_per_quarter": 480,
    "tempo_map": [{"bar": 1, "tempo_bpm": 120}],
    "meter_map": [{"bar": 1, "numerator": 4, "denominator": 4}],
    "key_map": [{"bar": 1, "key": "C", "mode": "major"}],
    "tracks": {...}
  }
}
```

### Database Operations

#### Load Complete DSL Project
```bash
POST /facade/dsl/load
Content-Type: application/json

# From file
{
  "path": "src/dsl/examples/02-multi-track.json"
}

# OR from JSON
{
  "dsl_json": {
    "project": {...}
  }
}

# Response
{
  "composition_id": 1,
  "clip_ids": [1, 2, 3],
  "composition_name": "my-song"
}
```

### Search Operations

#### Search Clips by Tags or Name
```bash
POST /facade/clips/search
Content-Type: application/json

# By tags
{
  "tags": ["verse", "melody"]
}

# OR by name pattern
{
  "name_pattern": "%bass%"
}

# Response
{
  "clips": [
    {
      "clip_id": 1,
      "name": "bass-verse",
      "tags": ["verse", "bass"],
      "notes": [...]
    }
  ]
}
```

### Export Operations

#### Export Clip to DSL
```bash
GET /facade/clips/1/dsl

# Response: DSL clip format
{
  "clip_id": 1,
  "name": "my-clip",
  "notes": [...],
  "bars": [...]
}
```

#### Export Composition to DSL
```bash
GET /facade/compositions/1/dsl

# Response: Complete DSL project
{
  "project": {
    "name": "my-song",
    "tracks": [...],
    "clip_library": [...]
  }
}
```

### MIDI Export

#### Export Composition to MIDI
```bash
POST /facade/compositions/1/midi
Content-Type: application/json

{
  "output_path": "output.mid"
}

# Response
{
  "midi_bytes": "base64-encoded-midi-data",
  "output_path": "output.mid"
}
```

### Playback Operations

**Note:** Playback endpoints trigger audio on the **server side**. For client-side playback, use MIDI export instead.

#### Play SML Clip (Server-Side)
```bash
POST /facade/playback/sml
Content-Type: application/json

{
  "sml_clip": {
    "name": "test",
    "bars": [
      {
        "bar_index": 0,
        "items": [
          {"note": "C4", "duration": "quarter"}
        ]
      }
    ]
  },
  "config": {
    "sf2_path": "FluidR3_GM.sf2",
    "bpm": 120,
    "loop": false
  }
}

# Response
{
  "status": "playing",
  "message": "Playback started on server"
}
```

#### Generate and Play from Natural Language
```bash
POST /facade/playback/nl
Content-Type: application/json

{
  "nl_request": {
    "text": "Create a funky bass line"
  },
  "config": {
    "sf2_path": "FluidR3_GM.sf2",
    "bpm": 120,
    "loop": false
  }
}

# Response: Generated SML clip (playback happens in background)
{
  "sml": {
    "name": "generated-clip",
    "bars": [...]
  }
}
```

#### Play Stored Clip from Database
```bash
POST /facade/playback/clip/1
Content-Type: application/json

{
  "sf2_path": "FluidR3_GM.sf2",
  "bpm": 140,
  "loop": true
}

# Response
{
  "status": "playing",
  "clip_id": 1
}
```

## Complete Workflow Example

```bash
# 1. Generate clip from natural language
curl -X POST http://localhost:8000/facade/nl/clip-to-sml \
  -H "Content-Type: application/json" \
  -d '{"text": "Create a C major arpeggio, quarter notes"}' \
  > sml_clip.json

# 2. Play it to preview (server-side)
curl -X POST http://localhost:8000/facade/playback/sml \
  -H "Content-Type: application/json" \
  -d '{
    "sml_clip": '$(cat sml_clip.json | jq .sml)',
    "config": {"sf2_path": "FluidR3_GM.sf2", "bpm": 120}
  }'

# 3. If you like it, store to database
curl -X POST http://localhost:8000/facade/nl/clip-to-db \
  -H "Content-Type: application/json" \
  -d '{"text": "Create a C major arpeggio, quarter notes"}'
# Returns: 42 (clip_id)

# 4. Search for it
curl -X POST http://localhost:8000/facade/clips/search \
  -H "Content-Type: application/json" \
  -d '{"tags": ["arpeggio"]}'

# 5. Export to DSL
curl http://localhost:8000/facade/clips/42/dsl > clip_42.json

# 6. Play from database
curl -X POST http://localhost:8000/facade/playback/clip/42 \
  -H "Content-Type: application/json" \
  -d '{"sf2_path": "FluidR3_GM.sf2", "bpm": 120}'
```

## Python Client Example

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Generate from natural language
response = requests.post(
    f"{BASE_URL}/facade/nl/clip-to-sml",
    json={"text": "Create a jazzy bass line in F"}
)
sml_clip = response.json()["sml"]

# 2. Convert to DSL
response = requests.post(
    f"{BASE_URL}/facade/sml/clip-to-dsl",
    json=sml_clip
)
dsl_clip = response.json()

# 3. Store to database
response = requests.post(
    f"{BASE_URL}/clips/from-sml",
    json=sml_clip
)
clip_id = response.json()["clip_id"]

# 4. Search by tags
response = requests.post(
    f"{BASE_URL}/facade/clips/search",
    json={"tags": ["bass", "jazz"]}
)
clips = response.json()["clips"]

# 5. Export to DSL
response = requests.get(f"{BASE_URL}/facade/clips/{clip_id}/dsl")
exported_dsl = response.json()

# 6. Play (server-side)
requests.post(
    f"{BASE_URL}/facade/playback/clip/{clip_id}",
    json={"sf2_path": "FluidR3_GM.sf2", "bpm": 120}
)
```

## JavaScript/TypeScript Client Example

```typescript
const BASE_URL = "http://localhost:8000";

// Generate and play workflow
async function generateAndPlay(prompt: string) {
  // 1. Generate from NL
  const nlResponse = await fetch(`${BASE_URL}/facade/nl/clip-to-sml`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: prompt })
  });
  const { sml } = await nlResponse.json();
  
  // 2. Play it (server-side)
  await fetch(`${BASE_URL}/facade/playback/sml`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sml_clip: sml,
      config: { sf2_path: "FluidR3_GM.sf2", bpm: 120 }
    })
  });
  
  return sml;
}

// Store if user likes it
async function storeClip(prompt: string) {
  const response = await fetch(`${BASE_URL}/facade/nl/clip-to-db`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: prompt })
  });
  return await response.json(); // Returns clip_id
}

// Search clips
async function searchClips(tags: string[]) {
  const response = await fetch(`${BASE_URL}/facade/clips/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tags })
  });
  const { clips } = await response.json();
  return clips;
}
```

## Request/Response Models

All Pydantic models from the facade are used directly:

- `NLToSMLRequest`: `{"text": string}`
- `NLToSMLResponse`: `{"sml": object}`
- `DSLLoadConfig`: `{"path"?: string, "dsl_json"?: object}`
- `DSLLoadResult`: `{"composition_id": int, "clip_ids": int[], "composition_name": string}`
- `ClipSearchRequest`: `{"tags"?: string[], "name_pattern"?: string}`
- `ClipDSLResponse`: `{"clips": object[]}`
- `PlaybackConfig`: `{"sf2_path"?: string, "bpm": int, "loop": bool}`

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Success
- `404 Not Found`: Resource not found (e.g., clip_id doesn't exist)
- `500 Internal Server Error`: Processing error (check error details in response)

Example error response:
```json
{
  "detail": "LangGraph clip generation failed: OpenAI API key not set"
}
```

## Interactive Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

Use these to explore all endpoints, test requests, and see response schemas.
