"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — FastAPI Server                         ║
║  NRNLANG-Ω: REST API — all endpoints                    ║
╚══════════════════════════════════════════════════════════╝

Endpoints:
  POST   /api/v1/brain/remember     → Store a memory
  POST   /api/v1/brain/recall       → Query memories
  POST   /api/v1/brain/context      → Full context for AI injection
  GET    /api/v1/brain/stats        → Brain statistics
  POST   /api/v1/brain/audit        → Run thermal audit
  POST   /api/v1/brain/end-session  → End session (save + bond)

  GET    /api/v1/memories           → List all memories (paginated, BUG-015)
  GET    /api/v1/memories/{id}      → Get specific memory
  DELETE /api/v1/memories/{id}      → Delete memory
  PATCH  /api/v1/memories/{id}      → Update memory

  GET    /api/v1/bonds              → List all bonds
  GET    /api/v1/bonds/{id}         → Get bonds for engram

  POST   /api/v1/nrnlang/execute    → Execute NRNLANG-Ω command
  POST   /api/v1/nrnlang/script     → Execute NRNLANG-Ω script

  GET    /api/v1/stream/events      → SSE real-time events (BUG-019)
  GET    /api/v1/export/{format}    → Export brain

BUG-010 FIX: Rate limiting (60 req/min)
BUG-012 FIX: All endpoints validated
BUG-016 FIX: Streaming endpoint for real-time events
"""

import time
import json
import asyncio
import logging
from typing import Optional, List
from contextlib import asynccontextmanager

logger = logging.getLogger("NEURONX.API")

try:
    from fastapi import FastAPI, HTTPException, Query, Request, Response
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse, JSONResponse
    from pydantic import BaseModel, Field
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'neuronx-core'))

from neuronx.brain.neuron import NeuronBrain
from neuronx.language.nrnlang import NRNLangInterpreter
from neuronx.config import RATE_LIMIT_REQUESTS_PER_MINUTE, DEFAULT_PAGE_SIZE


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Global State
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

_brain: Optional[NeuronBrain] = None
_interpreter: Optional[NRNLangInterpreter] = None
_event_listeners: List[asyncio.Queue] = []


def get_brain() -> NeuronBrain:
    global _brain, _interpreter
    if _brain is None:
        data_dir = os.environ.get("NEURONX_DATA_DIR", "data")
        brain_name = os.environ.get("NEURONX_BRAIN_NAME", "default")
        _brain = NeuronBrain(name=brain_name, data_dir=data_dir)
        _interpreter = NRNLangInterpreter(brain=_brain)
    return _brain


def get_interpreter() -> NRNLangInterpreter:
    get_brain()
    return _interpreter


def push_event(event_type: str, data: dict):
    """Push SSE event to all connected listeners."""
    event = {"type": event_type, "data": data, "timestamp": time.time()}
    for queue in _event_listeners:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Request/Response Models
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

if HAS_FASTAPI:

    class RememberRequest(BaseModel):
        text: str = Field(..., min_length=1, max_length=5000)
        source: str = Field(default="user")
        emotion: Optional[str] = None
        decay_class: Optional[str] = None

    class RecallRequest(BaseModel):
        query: str = Field(..., min_length=1, max_length=1000)
        top_k: int = Field(default=7, ge=1, le=50)

    class ContextRequest(BaseModel):
        message: str = Field(..., min_length=1, max_length=5000)
        top_k: int = Field(default=7, ge=1, le=50)
        remember: bool = Field(default=True)

    class NRNLangRequest(BaseModel):
        command: str = Field(..., min_length=1)

    class NRNLangScriptRequest(BaseModel):
        script: str = Field(..., min_length=1)

    class UpdateMemoryRequest(BaseModel):
        confidence: Optional[float] = None
        weight: Optional[float] = None
        tags: Optional[List[str]] = None
        emotion: Optional[str] = None

    class ChatRequest(BaseModel):
        message: str = Field(..., min_length=1)
        provider: str = Field(...) # "openai" or "anthropic"
        api_key: str = Field(...)
        model: str = Field(...)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Rate Limiter (BUG-010 FIX)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class RateLimiter:
    """BUG-010 FIX: Simple in-memory rate limiter."""

    def __init__(self, rpm: int = RATE_LIMIT_REQUESTS_PER_MINUTE):
        self.rpm = rpm
        self.requests: dict = {}

    def check(self, client_ip: str) -> bool:
        now = time.time()
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if now - t < 60
        ]

        if len(self.requests[client_ip]) >= self.rpm:
            return False

        self.requests[client_ip].append(now)
        return True


rate_limiter = RateLimiter()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FastAPI App
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_app() -> "FastAPI":
    if not HAS_FASTAPI:
        raise ImportError("FastAPI is required. Install with: pip install fastapi uvicorn")

    @asynccontextmanager
    async def lifespan(app):
        get_brain()
        logger.info("NEURON-X API Server started")
        yield
        if _brain:
            _brain.end_session()
        logger.info("NEURON-X API Server stopped")

    app = FastAPI(
        title="NEURON-X Omega API",
        description="Self-Sovereign AI Memory Platform",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Rate limiting middleware ──
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        if not rate_limiter.check(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded", "retry_after": 60},
            )
        response = await call_next(request)
        return response

    # ━━━━━━━━━━━━━━━━━━━━━
    # Brain Endpoints
    # ━━━━━━━━━━━━━━━━━━━━━

    @app.post("/api/v1/brain/remember")
    async def remember(req: RememberRequest):
        brain = get_brain()
        result = brain.remember(req.text, source=req.source, emotion=req.emotion, decay_class=req.decay_class)
        push_event("remember", {"action": result.action, "id": result.engram_id})
        return {
            "action": result.action,
            "engram_id": result.engram_id,
            "surprise_score": result.surprise_score,
            "is_new": result.is_new,
            "conflict": result.conflict,
        }

    @app.post("/api/v1/brain/recall")
    async def recall(req: RecallRequest):
        brain = get_brain()
        results = brain.recall(req.query, top_k=req.top_k)
        push_event("recall", {"query": req.query, "count": len(results)})
        return {
            "results": [
                {
                    "id": e.id,
                    "raw": e.raw,
                    "score": score,
                    "confidence": e.confidence,
                    "zone": e.zone,
                    "emotion": e.emotion,
                    "is_anchor": e.is_anchor,
                    "age_days": e.age_days,
                }
                for e, score in results
            ],
        }

    @app.post("/api/v1/brain/context")
    async def context(req: ContextRequest):
        brain = get_brain()
        ctx = brain.get_context(req.message, top_k=req.top_k, remember=req.remember)
        return {
            "system_prompt_addition": ctx.system_prompt_addition,
            "action": ctx.action,
            "memories_count": len(ctx.memories_used),
        }

    @app.post("/api/v1/brain/chat")
    async def chat(req: ChatRequest):
        import urllib.request
        import json
        
        brain = get_brain()
        # 1. Get context
        ctx = brain.get_context(req.message, top_k=7, remember=True)
        
        reply_text = ""
        
        try:
            # 2. Call Provider
            if req.provider == "openai":
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {req.api_key}"
                }
                data = {
                    "model": req.model,
                    "messages": [
                        {"role": "system", "content": ctx.system_prompt_addition},
                        {"role": "user", "content": req.message}
                    ]
                }
                req_obj = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req_obj) as response:
                    res_body = json.loads(response.read().decode('utf-8'))
                    reply_text = res_body['choices'][0]['message']['content']
                    
            elif req.provider == "anthropic":
                url = "https://api.anthropic.com/v1/messages"
                headers = {
                    "Content-Type": "application/json",
                    "x-api-key": req.api_key,
                    "anthropic-version": "2023-06-01"
                }
                data = {
                    "model": req.model,
                    "max_tokens": 1024,
                    "system": ctx.system_prompt_addition,
                    "messages": [
                        {"role": "user", "content": req.message}
                    ]
                }
                req_obj = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req_obj) as response:
                    res_body = json.loads(response.read().decode('utf-8'))
                    reply_text = res_body['content'][0]['text']
                    
            elif req.provider == "nvidia":
                from langchain_nvidia_ai_endpoints import ChatNVIDIA
                client = ChatNVIDIA(
                    model=req.model,
                    api_key=req.api_key,
                    temperature=0.6,
                    top_p=0.9,
                    max_tokens=4096,
                )
                messages = [
                    {"role": "system", "content": ctx.system_prompt_addition},
                    {"role": "user", "content": req.message}
                ]
                reply_text = ""
                for chunk in client.stream(messages):
                    reply_text += chunk.content
                    
            else:
                raise HTTPException(400, "Unknown provider")
                
            # 3. Remember AI response
            brain.remember(reply_text, source="assistant")
            
        except Exception as e:
            logger.error(f"Chat API error: {e}")
            raise HTTPException(500, f"Error calling {req.provider} API: {str(e)}")
            
        return {
            "reply": reply_text,
            "context_used": len(ctx.memories_used)
        }

    @app.get("/api/v1/brain/stats")
    async def stats():
        brain = get_brain()
        return brain.get_stats()

    @app.post("/api/v1/brain/audit")
    async def audit():
        brain = get_brain()
        result = brain.run_audit()
        push_event("audit", result)
        return result

    @app.post("/api/v1/brain/end-session")
    async def end_session():
        brain = get_brain()
        brain.end_session()
        return {"status": "ok", "message": "Session ended, brain saved"}

    # ━━━━━━━━━━━━━━━━━━━━━
    # Memory Endpoints (BUG-015: paginated)
    # ━━━━━━━━━━━━━━━━━━━━━

    @app.get("/api/v1/memories")
    async def list_memories(
        page: int = Query(0, ge=0),
        page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=200),
        zone: Optional[str] = None,
        emotion: Optional[str] = None,
    ):
        brain = get_brain()
        engrams = list(brain.soma.engrams.values())

        if zone:
            engrams = [e for e in engrams if e.zone == zone]
        if emotion:
            engrams = [e for e in engrams if e.emotion == emotion]

        total = len(engrams)
        start = page * page_size
        end = start + page_size
        page_items = engrams[start:end]

        return {
            "memories": [e.to_dict() for e in page_items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        }

    @app.get("/api/v1/memories/{memory_id}")
    async def get_memory(memory_id: str):
        brain = get_brain()
        engram = brain.soma.get_engram(memory_id)
        if not engram:
            raise HTTPException(404, f"Memory {memory_id} not found")
        return engram.to_dict()

    @app.delete("/api/v1/memories/{memory_id}")
    async def delete_memory(memory_id: str):
        brain = get_brain()
        if brain.soma.remove_engram(memory_id):
            push_event("delete", {"id": memory_id})
            return {"status": "deleted", "id": memory_id}
        raise HTTPException(404, f"Memory {memory_id} not found")

    @app.patch("/api/v1/memories/{memory_id}")
    async def update_memory(memory_id: str, req: UpdateMemoryRequest):
        brain = get_brain()
        engram = brain.soma.get_engram(memory_id)
        if not engram:
            raise HTTPException(404, f"Memory {memory_id} not found")
        if req.confidence is not None:
            engram.confidence = max(0.0, min(1.0, req.confidence))
        if req.weight is not None:
            engram.weight = max(0.1, min(3.0, req.weight))
        if req.tags is not None:
            engram.tags = req.tags
        if req.emotion is not None:
            engram.emotion = req.emotion
        push_event("update", {"id": memory_id})
        return engram.to_dict()

    # ━━━━━━━━━━━━━━━━━━━━━
    # Bond Endpoints
    # ━━━━━━━━━━━━━━━━━━━━━

    @app.get("/api/v1/bonds")
    async def list_bonds():
        brain = get_brain()
        return {
            "bonds": [a.to_dict() for a in brain.soma.axons],
            "total": len(brain.soma.axons),
        }

    @app.get("/api/v1/bonds/{engram_id}")
    async def get_bonds_for(engram_id: str):
        brain = get_brain()
        axons = brain.soma.get_axons_for(engram_id)
        return {"bonds": [a.to_dict() for a in axons], "count": len(axons)}

    # ━━━━━━━━━━━━━━━━━━━━━
    # NRNLANG-Ω Endpoints (BUG-017)
    # ━━━━━━━━━━━━━━━━━━━━━

    @app.post("/api/v1/nrnlang/execute")
    async def nrnlang_execute(req: NRNLangRequest):
        interp = get_interpreter()
        try:
            result = interp.execute(req.command)
            push_event("nrnlang", {"command": req.command, "result": result.get("log", "")})
            return result
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/v1/nrnlang/script")
    async def nrnlang_script(req: NRNLangScriptRequest):
        interp = get_interpreter()
        results = interp.execute_script(req.script)
        return {"results": results}

    # ━━━━━━━━━━━━━━━━━━━━━
    # SSE Streaming (BUG-016, BUG-019)
    # ━━━━━━━━━━━━━━━━━━━━━

    @app.get("/api/v1/stream/events")
    async def sse_events():
        """BUG-016, BUG-019 FIX: Real-time SSE events."""
        queue = asyncio.Queue(maxsize=100)
        _event_listeners.append(queue)

        async def generator():
            try:
                while True:
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=30)
                        yield f"data: {json.dumps(event)}\n\n"
                    except asyncio.TimeoutError:
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"
            finally:
                _event_listeners.remove(queue)

        return StreamingResponse(generator(), media_type="text/event-stream")

    # ━━━━━━━━━━━━━━━━━━━━━
    # Export Endpoints (BUG-018)
    # ━━━━━━━━━━━━━━━━━━━━━

    @app.get("/api/v1/export/{fmt}")
    async def export_brain(fmt: str):
        brain = get_brain()
        try:
            output = brain.export(format=fmt)
            media_type = "application/json" if fmt == "json" else "text/plain"
            return Response(content=output, media_type=media_type)
        except Exception as e:
            raise HTTPException(400, str(e))

    return app


# Create app instance for uvicorn
if HAS_FASTAPI:
    app = create_app()
