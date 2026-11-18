import sys
import os
import io
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from agents.orchestrator import RemediationOrchestrator, SessionEventBus
from agents.auditor import AuditorAgent
from agents.developer import DeveloperAgent
from rag.memory_store import MemoryStore
from routing.omniroute_client import OmniRouteClient, ModelTier
from workspace.project_manager import ProjectManager
from schemas.models import AgentConfig, VulnerabilityFinding

app = FastAPI(
    title="Sentinel v1.0 Polyglot Studio API",
    description="Backend for Sentinel v1.0 Polyglot Multi-Agent Studio with Real-Time WebSocket Streaming & Interactive Vibe Coding",
    version="1.0.0"
)

# Enable CORS for Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared singletons
event_bus = SessionEventBus()
memory_store = MemoryStore()
omniroute_client = OmniRouteClient()
auditor = AuditorAgent(name="Snooze")
developer = DeveloperAgent(omniroute_client=omniroute_client)
orchestrator = RemediationOrchestrator(
    memory_store=memory_store,
    omniroute_client=omniroute_client,
    event_bus=event_bus
)
project_manager = ProjectManager(
    auditor=auditor,
    patcher=orchestrator.patcher,
    omniroute=omniroute_client,
    memory_store=memory_store,
    event_bus=event_bus
)


class CodePayload(BaseModel):
    code: str
    filename: str = "snippet.py"
    session_id: Optional[str] = None
    mode: Optional[str] = "autopilot"  # "autopilot" or "vibe_interactive"
    agent_config: Optional[AgentConfig] = None


class GeneratePayload(BaseModel):
    prompt: str
    tech_stack: str = "python"
    session_id: Optional[str] = None
    agent_config: Optional[AgentConfig] = None


class PipelinePayload(BaseModel):
    prompt: str
    filename: str = "application.py"
    session_id: Optional[str] = None
    mode: Optional[str] = "autopilot"
    agent_config: Optional[AgentConfig] = None


class QueryMemoryPayload(BaseModel):
    query: str
    top_k: int = 3


class FullstackScaffoldPayload(BaseModel):
    prompt: str


@app.get("/")
def read_root():
    return {
        "message": "Welcome to Sentinel v1.0 Polyglot Multi-Agent Security Studio",
        "version": "1.0.0",
        "features": [
            "Polyglot AST & Call-Graph Engine (MERN, Spring Boot, Android, Python)",
            "Polyglot Security Auditor (OWASP Top 10, CWE, Exploit PoC & Multi-Strategy Fixes)",
            "Real-Time WebSocket Event Bus & Telemetry Streaming (/ws/session/{session_id})",
            "Interactive Vibe Coding Mode (Approval Gate & Custom Instructions)",
            "OmniRoute Dynamic Multi-Model Gateway",
            "Context Remembrance Engine (1-Hop Dependency Graph Anti-Hallucination)",
            "Self-Learning RAG Ingestion"
        ]
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "sentinel-backend",
        "version": "1.0.0",
        "omniroute_active_model": omniroute_client.last_model_used or "initialized",
        "simulation_mode": omniroute_client.force_simulation
    }


# ==============================================================================
# Real-Time WebSocket Telemetry & Vibe Coding Endpoint
# ==============================================================================

@app.websocket("/ws/session/{session_id}")
async def websocket_session_endpoint(websocket: WebSocket, session_id: str):
    """
    Real-Time WebSocket streaming endpoint for Sentinel v1.0 Multi-Agent Studio.
    Streams telemetry:
      - AGENT_STATE: {"type": "AGENT_STATE", "agent": "dex|pixel|snooze|glitch", "status": "thinking|scanning|editing", "message": "..."}
      - CURSOR_MOVE: {"type": "CURSOR_MOVE", "agent": "...", "file": "...", "line": ..., "column": ...}
      - VULN_DETECTED: {"type": "VULN_DETECTED", "finding": {...}}
      - LIVE_DIFF_CHUNK: {"type": "LIVE_DIFF_CHUNK", "file": "...", "original_lines": [...], "patched_lines": [...], "explanation": "..."}
    Handles interactive Vibe Coding commands:
      - APPROVE_FIX: {"action": "APPROVE_FIX", "finding_id": "...", "selected_strategy": "...", "custom_instruction": "..."}
      - START_REMEDIATION: {"action": "START_REMEDIATION", "code": "...", "filename": "...", "mode": "autopilot|vibe_interactive", "agent_config": {...}}
      - PING: {"action": "PING"}
    """
    await websocket.accept()
    await event_bus.register(session_id, websocket)

    try:
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "session_id": session_id,
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Connected to Sentinel v1.0 Real-Time Event Bus for session {session_id}"
        })

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "PING":
                await websocket.send_json({"type": "PONG", "timestamp": datetime.utcnow().isoformat()})

            elif action == "APPROVE_FIX":
                # Unlock paused vibe_interactive remediation loop
                success = event_bus.submit_approval(session_id, data)
                await websocket.send_json({
                    "type": "APPROVAL_ACKNOWLEDGED",
                    "session_id": session_id,
                    "finding_id": data.get("finding_id"),
                    "selected_strategy": data.get("selected_strategy"),
                    "success": success
                })

            elif action == "START_REMEDIATION":
                code = data.get("code", "")
                filename = data.get("filename", "snippet.py")
                mode = data.get("mode", "autopilot")
                agent_config = data.get("agent_config", {})
                asyncio.create_task(
                    orchestrator.remediate_code_async(
                        raw_code=code,
                        filename=filename,
                        session_id=session_id,
                        mode=mode,
                        agent_config=agent_config
                    )
                )

            elif action == "START_PIPELINE":
                prompt = data.get("prompt", "")
                filename = data.get("filename", "application.py")
                # Run synchronous synthesis in threadpool to prevent blocking async event loop
                asyncio.create_task(
                    asyncio.to_thread(
                        orchestrator.synthesize_and_secure,
                        prompt=prompt,
                        filename=filename
                    )
                )

    except WebSocketDisconnect:
        await event_bus.unregister(session_id, websocket)
    except Exception:
        await event_bus.unregister(session_id, websocket)


# ==============================================================================
# REST API Endpoints (Preserving 100% Backwards Compatibility)
# ==============================================================================

@app.post("/api/pipeline")
def run_pipeline_endpoint(payload: PipelinePayload):
    """
    Unified Autonomous Pipeline:
    From prompt to Architect invariants -> Developer OmniRoute synthesis
    -> Auditor verification -> Patcher remediation -> RAG persistence.
    Returns the complete cinematic timeline of agents in action.
    """
    result = orchestrator.synthesize_and_secure(
        prompt=payload.prompt,
        filename=payload.filename
    )
    return result


@app.post("/api/generate")
def generate_code_endpoint(payload: GeneratePayload):
    """
    Generate defensive code satisfying architectural security invariants
    using OmniRoute and Context Remembrance.
    """
    result = developer.implement(task_prompt=payload.prompt)
    return result


@app.post("/api/audit")
def audit_code_endpoint(payload: CodePayload):
    """Scan raw code for security vulnerabilities across all supported stacks."""
    sec_level = payload.agent_config.security_level if payload.agent_config else "balanced"
    result = auditor.audit_code(code=payload.code, filename=payload.filename, security_level=sec_level)
    return result.model_dump()


@app.post("/api/remediate")
async def remediate_code_endpoint(payload: CodePayload):
    """
    Run the complete Architect -> Auditor -> Patcher loop with
    OmniRoute, Context Remembrance, and Real-Time WebSocket event streaming.
    """
    config_dict = payload.agent_config.model_dump() if payload.agent_config else {}
    result = await orchestrator.remediate_code_async(
        raw_code=payload.code,
        filename=payload.filename,
        session_id=payload.session_id,
        mode=payload.mode or "autopilot",
        agent_config=config_dict
    )
    return result


@app.post("/api/rag/search")
def search_remediation_memory(payload: QueryMemoryPayload):
    """Retrieve learned remediation patterns from RAG store."""
    results = memory_store.search_similar_remediations(query=payload.query, top_k=payload.top_k)
    return {"query": payload.query, "results": results}


# ==============================================================================
# Multi-File System & ZIP Ingestion / Export Endpoints
# ==============================================================================

@app.post("/api/project/upload-zip")
async def upload_zip_project_endpoint(file: UploadFile = File(...)):
    """
    Ingests an entire ZIP codebase, performs whole-repository security scanning,
    applies surgical patches across all files, and prepares an interactive localhost sandbox.
    """
    zip_bytes = await file.read()
    extracted_files = project_manager.extract_zip(zip_bytes)
    if not extracted_files:
        raise HTTPException(
            status_code=400,
            detail="No readable source code files found in archive (supported: .py, .js, .ts, .jsx, .tsx, .java, .kt, .xml, etc.)"
        )
    workspace = project_manager.process_project(
        files=extracted_files,
        project_name=file.filename or "Uploaded Codebase"
    )
    return workspace.model_dump()


@app.post("/api/project/generate-fullstack")
def generate_fullstack_project_endpoint(payload: FullstackScaffoldPayload):
    """
    Generates a complete multi-file fullstack project scaffold from a prompt:
    backend/app.py, database/schema.sql, frontend/index.html, requirements.txt,
    and runs a full security audit & localhost sandbox preview.
    """
    scaffold_files = project_manager.generate_fullstack_scaffold(payload.prompt)
    workspace = project_manager.process_project(
        files=scaffold_files,
        project_name="Fullstack Microservice"
    )
    return workspace.model_dump()


@app.get("/api/project/download-zip/{session_id}")
def download_remediated_zip_endpoint(session_id: str):
    """
    Exports the complete sanitized and patched multi-file project as a clean ZIP archive.
    """
    zip_bytes = project_manager.get_cached_zip(session_id)
    if not zip_bytes:
        raise HTTPException(status_code=404, detail="Workspace session not found or expired.")
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=sentinel-remediated-{session_id}.zip"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, app_dir=os.path.dirname(os.path.abspath(__file__)))
