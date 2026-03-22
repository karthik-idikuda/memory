"""
NEURON-X Omega — Web API Server
FastAPI backend connecting web UI to NeuronBrain
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from brain.neuron import NeuronBrain

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
os.makedirs(DATA_DIR, exist_ok=True)

BRAIN_NAME = os.environ.get("BRAIN_NAME", "default")
SOMA_PATH = os.path.join(DATA_DIR, f"{BRAIN_NAME}.soma")

# Global state
ai_client = None
model_name = "claude-sonnet-4-20250514"
brain = NeuronBrain(soma_path=SOMA_PATH, ai_client=None, model=model_name)
brain.start_pulse()

app = FastAPI(title="NEURON-X Omega API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Models ──

class ChatRequest(BaseModel):
    message: str

class SearchRequest(BaseModel):
    query: str
    top_k: int = 7

class ConnectRequest(BaseModel):
    api_key: str
    model: str = "claude-sonnet-4-20250514"


# ── CONNECT/DISCONNECT ──

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "brain": BRAIN_NAME,
        "connected": ai_client is not None,
        "model": model_name,
        "total_engrams": len(brain.soma.engrams),
        "total_axons": len(brain.soma.axons),
    }


@app.post("/api/connect")
def connect_ai(req: ConnectRequest):
    """Connect to AI provider with API key and model."""
    global ai_client, model_name
    try:
        import anthropic
        ai_client = anthropic.Anthropic(api_key=req.api_key)
        model_name = req.model
        brain.ai_client = ai_client
        brain.model = model_name
        # Test the connection
        ai_client.messages.create(
            model=model_name,
            max_tokens=10,
            messages=[{"role": "user", "content": "hi"}],
        )
        return {"status": "connected", "model": model_name}
    except Exception as e:
        ai_client = None
        brain.ai_client = None
        return {"status": "error", "error": str(e)}


@app.post("/api/disconnect")
def disconnect_ai():
    """Disconnect AI — switch to offline mode."""
    global ai_client
    ai_client = None
    brain.ai_client = None
    return {"status": "disconnected"}


# ── BRAIN ENDPOINTS ──

@app.get("/api/stats")
def get_stats():
    stats = brain.get_brain_stats()
    return stats


@app.post("/api/chat")
def chat(req: ChatRequest):
    results = brain.process_input(req.message)

    response_text = None
    if ai_client:
        try:
            response_text = brain.chat(req.message)
        except Exception as e:
            response_text = f"AI Error: {str(e)}"

    query_results = brain.query(req.message, top_k=5)
    memories = []
    for engram, score in query_results:
        memories.append({
            "id": engram.id,
            "text": engram.raw,
            "zone": engram.zone,
            "heat": round(engram.heat, 3),
            "confidence": round(engram.confidence, 2),
            "emotion": engram.emotion,
            "score": round(score, 3),
            "age_days": round(engram.age_days, 1),
            "spark": round(engram.spark, 3),
            "weight": round(engram.weight, 2),
        })

    actions = []
    for r in results:
        actions.append({
            "action": r["action"],
            "text": r["text"],
            "surprise": r.get("surprise", 0),
            "emotion": r.get("emotion", "neutral"),
            "clash_result": r.get("clash_result"),
        })

    return {
        "response": response_text,
        "actions": actions,
        "memories": memories,
        "connected": ai_client is not None,
    }


@app.get("/api/memories")
def get_memories(zone: Optional[str] = None, limit: int = 50):
    engrams = brain.get_all_memories(zone=zone, limit=limit)
    return [{
        "id": e.id,
        "text": e.raw,
        "zone": e.zone,
        "heat": round(e.heat, 3),
        "spark": round(e.spark, 3),
        "weight": round(e.weight, 2),
        "confidence": round(e.confidence, 2),
        "emotion": e.emotion,
        "decay_class": e.decay_class,
        "truth": e.truth,
        "age_days": round(e.age_days, 1),
        "access_count": e.access_count,
        "bonds": len(e.axons),
        "tags": e.tags,
        "is_anchor": e.is_anchor,
        "born": e.born,
        "source": getattr(e, 'source', 'user'),
    } for e in engrams]


@app.post("/api/search")
def search_memories(req: SearchRequest):
    results = brain.query(req.query, top_k=req.top_k)
    return [{
        "id": e.id,
        "text": e.raw,
        "zone": e.zone,
        "heat": round(e.heat, 3),
        "confidence": round(e.confidence, 2),
        "emotion": e.emotion,
        "score": round(score, 3),
        "age_days": round(e.age_days, 1),
        "spark": round(e.spark, 3),
        "weight": round(e.weight, 2),
    } for e, score in results]


@app.get("/api/bonds")
def get_bonds():
    types = {0: "TIME", 1: "WORD", 2: "EMOTION", 3: "CLASH", 4: "REINFORCE", 5: "HERALD"}
    return [{
        "from_id": a.from_id[:8],
        "to_id": a.to_id[:8],
        "from_full": a.from_id,
        "to_full": a.to_id,
        "synapse": round(a.synapse, 3),
        "type": types.get(a.axon_type, "?"),
        "from_text": brain.soma.engrams.get(a.from_id, None) and brain.soma.engrams[a.from_id].raw[:40],
        "to_text": brain.soma.engrams.get(a.to_id, None) and brain.soma.engrams[a.to_id].raw[:40],
    } for a in sorted(brain.soma.axons, key=lambda x: x.synapse, reverse=True)]


@app.get("/api/conflicts")
def get_conflicts():
    pairs = brain.get_active_conflicts()
    return [{
        "old": {"id": a.id, "text": a.raw, "truth": a.truth, "confidence": a.confidence},
        "new": {"id": b.id, "text": b.raw, "truth": b.truth, "confidence": b.confidence},
    } for a, b in pairs]


@app.post("/api/audit")
def run_audit():
    stats = brain.audit()
    return stats


@app.get("/api/nrnlang/{engram_id}")
def get_nrnlang(engram_id: str):
    from utils.nrnlang import NRNLangInterpreter
    nrn = NRNLangInterpreter(brain)
    engram = brain.soma.get_engram(engram_id)
    if not engram:
        matches = [eid for eid in brain.soma.engrams if eid.startswith(engram_id)]
        if len(matches) == 1:
            engram = brain.soma.get_engram(matches[0])
        else:
            raise HTTPException(status_code=404, detail="Engram not found")
    return {"nrnlang": nrn.engram_to_nrnlang(engram)}


@app.get("/api/nrnlang-brain")
def get_nrnlang_brain():
    from utils.nrnlang import NRNLangInterpreter
    nrn = NRNLangInterpreter(brain)
    return {"nrnlang": nrn.brain_to_nrnlang()}


@app.post("/api/save")
def save_brain():
    brain.soma.save()
    return {"status": "saved"}


# ── Static frontend ──
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))

app.mount("/", StaticFiles(directory=WEB_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    print("""
    NEURON-X Omega — Web Dashboard
    Open: http://localhost:8000
    """)
    uvicorn.run(app, host="0.0.0.0", port=8000)
