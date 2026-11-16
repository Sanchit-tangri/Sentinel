import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import io
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from agents.orchestrator import RemediationOrchestrator
from agents.auditor import AuditorAgent
from agents.developer import DeveloperAgent
from rag.memory_store import MemoryStore
from routing.omniroute_client import OmniRouteClient, ModelTier
from workspace.project_manager import ProjectManager

app = FastAPI(
    title="Sentinel Multi-Agent API",
    description="Backend for Sentinel Autonomous Security Patching Framework with OmniRoute and Context Remembrance RAG",
    version="0.3.0"
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
memory_store = MemoryStore()
omniroute_client = OmniRouteClient()
orchestrator = RemediationOrchestrator(
    memory_store=memory_store,
    omniroute_client=omniroute_client
)
auditor = AuditorAgent()
developer = DeveloperAgent(omniroute_client=omniroute_client)
project_manager = ProjectManager(
    auditor=auditor,
    patcher=orchestrator.patcher,
    omniroute=omniroute_client,
    memory_store=memory_store
)


class CodePayload(BaseModel):
    code: str
    filename: str = "snippet.py"
    session_id: Optional[str] = None


class GeneratePayload(BaseModel):
    prompt: str
    tech_stack: str = "python"
    session_id: Optional[str] = None


class PipelinePayload(BaseModel):
    prompt: str
    filename: str = "application.py"


class QueryMemoryPayload(BaseModel):
    query: str
    top_k: int = 3


@app.get("/")
def read_root():
    return {
        "message": "Welcome to Sentinel Multi-Agent Security API",
        "version": "0.3.0",
        "features": [
            "Modular Agents",
            "OmniRoute Dynamic Multi-Model Gateway",
            "Context Remembrance Engine (Anti-Hallucination)",
            "Self-Learning RAG Ingestion",
            "OWASP Remediation Loop"
        ]
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "sentinel-backend",
        "omniroute_active_model": omniroute_client.last_model_used or "initialized",
        "simulation_mode": omniroute_client.force_simulation
    }


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
    """Scan raw code for security vulnerabilities."""
    result = auditor.audit_code(code=payload.code, filename=payload.filename)
    return result.model_dump()


@app.post("/api/remediate")
def remediate_code_endpoint(payload: CodePayload):
    """
    Run the complete Architect -> Auditor -> Patcher loop with
    OmniRoute and Context Remembrance, recording verified fixes in RAG memory.
    """
    result = orchestrator.remediate_code(
        raw_code=payload.code,
        filename=payload.filename,
        session_id=payload.session_id
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

class FullstackScaffoldPayload(BaseModel):
    prompt: str


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
            detail="No readable source code files found in archive (supported: .py, .js, .ts, .html, .css, .sql, etc.)"
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

