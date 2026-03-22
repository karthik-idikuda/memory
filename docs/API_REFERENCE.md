# NEURON-X Omega — API Reference

## Base URL

```
http://localhost:8000/api/v1
```

## Rate Limiting

60 requests/minute per IP (BUG-010). Returns `429` when exceeded.

---

## Brain Operations

### POST `/brain/remember`

Store a memory.

**Request:**
```json
{
  "text": "I love eating pizza",
  "source": "user",
  "emotion": null,
  "decay_class": null
}
```

**Response:**
```json
{
  "action": "FORGE",
  "engram_id": "a1b2c3d4e5f6...",
  "surprise_score": 0.95,
  "is_new": true,
  "conflict": null
}
```

---

### POST `/brain/recall`

Query memories using WSRA-X scoring.

**Request:**
```json
{
  "query": "What food does user like?",
  "top_k": 7
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "...",
      "raw": "I love eating pizza",
      "score": 4.231,
      "confidence": 0.85,
      "zone": "HOT",
      "emotion": "happy",
      "is_anchor": false,
      "age_days": 2.5
    }
  ]
}
```

---

### POST `/brain/context`

Get AI-ready context injection string.

**Request:**
```json
{
  "message": "What do you know about me?",
  "top_k": 7,
  "remember": true
}
```

**Response:**
```json
{
  "system_prompt_addition": "You are an AI assistant...",
  "action": "FORGE",
  "memories_count": 5
}
```

---

### GET `/brain/stats`

**Response:**
```json
{
  "brain_name": "default",
  "total_engrams": 42,
  "total_axons": 156,
  "session_engrams": 5,
  "interaction_count": 12,
  "zone_counts": { "HOT": 5, "WARM": 20, "COLD": 15, "SILENT": 2 }
}
```

---

### POST `/brain/audit`

Run thermal zone audit.

---

### POST `/brain/end-session`

Save brain, create bonds, end session.

---

## Memory CRUD

### GET `/memories?page=0&page_size=50&zone=HOT&emotion=happy`

Paginated memory list with optional filters.

### GET `/memories/{id}`

Get single memory by ID.

### DELETE `/memories/{id}`

Delete a memory.

### PATCH `/memories/{id}`

Update memory fields. Body: `{ "confidence": 0.9, "tags": ["updated"] }`

---

## Bonds

### GET `/bonds`

List all axon bonds.

### GET `/bonds/{engram_id}`

Get bonds for a specific memory.

---

## NRNLANG-Ω

### POST `/nrnlang/execute`

Execute single command: `{ "command": "FORGE engram(\"test\")" }`

### POST `/nrnlang/script`

Execute multi-line script: `{ "script": "..." }`

---

## Export

### GET `/export/{format}`

Export brain. Formats: `json`, `markdown`, `csv`, `nrnlang`.

---

## SSE Streaming

### GET `/stream/events`

Server-Sent Events stream. Event types: `remember`, `recall`, `audit`, `delete`, `update`, `nrnlang`, `heartbeat`.

```javascript
const es = new EventSource('/api/v1/stream/events');
es.onmessage = (e) => console.log(JSON.parse(e.data));
```
