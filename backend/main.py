from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List

from agents.orchestrator import RemediationOrchestrator
from agents.auditor import AuditorAgent
from rag.memory_store import MemoryStore

app = FastAPI(
    title="Sentinel Multi-Agent API",
    description="Backend for Sentinel Autonomous Security Patching Framework with Self-Learning RAG",
    version="0.2.0"
)

# Enable CORS for Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared memory & orchestrator instance
memory_store = MemoryStore()
orchestrator = RemediationOrchestrator(memory_store=memory_store)
auditor = AuditorAgent()

class CodePayload(BaseModel):
    code: str
    filename: str = "snippet.py"

class QueryMemoryPayload(BaseModel):
    query: str
    top_k: int = 3

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Sentinel Multi-Agent Security API",
        "version": "0.2.0",
        "features": ["Modular Agents", "Self-Learning RAG", "OWASP Remediation Loop"]
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "sentinel-backend"}

@app.post("/api/audit")
def audit_code_endpoint(payload: CodePayload):
    """Scan raw code for security vulnerabilities."""
    result = auditor.audit_code(code=payload.code, filename=payload.filename)
    return result.model_dump()

@app.post("/api/remediate")
def remediate_code_endpoint(payload: CodePayload):
    """Run the complete Architect -> Auditor -> Patcher loop and record lessons in RAG."""
    result = orchestrator.remediate_code(raw_code=payload.code, filename=payload.filename)
    return result

@app.post("/api/rag/search")
def search_remediation_memory(payload: QueryMemoryPayload):
    """Retrieve learned remediation patterns from RAG store."""
    results = memory_store.search_similar_remediations(query=payload.query, top_k=payload.top_k)
    return {"query": payload.query, "results": results}
