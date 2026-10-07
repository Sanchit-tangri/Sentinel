# Sentinel Implementation Plan

This document outlines the phased implementation plan for Sentinel, an autonomous multi-agent framework for real-time security patching and vulnerability remediation. The project will transition from an initial API-driven architecture to a fully custom, locally-run NLP and LLM environment.

## Architecture Overview

*   **Frontend:** Next.js (React), deployed on Vercel (future).
*   **Backend Orchestrator & API:** Python (FastAPI), coordinating agent workflow, lifecycle, and API exposure.
*   **Modular Multi-Agent Architecture (Dedicated Agent Packages):**
    *   **Architect Agent (`backend/agents/architect/`):** Analyzes target requirements, determines security trust boundaries, defines invariants, and constraints.
    *   **Developer Agent (`backend/agents/developer/`):** Generates defensive implementations conforming to architect specs.
    *   **Auditor Agent (`backend/agents/auditor/`):** Hybrid dual-engine scanner (static AST/regex analysis + AI heuristics) mapping to OWASP Top 10 and CWEs.
    *   **Patcher Agent (`backend/agents/patcher/`):** Synthesizes surgical diffs and patches to remediate vulnerabilities without breaking functional logic.
*   **Self-Learning RAG Engine (`backend/rag/`):**
    *   **Continuous Learning Loop:** Persists successful patch diffs, audit post-mortems, false-positive feedback, and CVE/CWE remediations.
    *   **Vector Store & Knowledge Base:** Uses local embeddings (e.g., ChromaDB / FAISS + FastEmbed / sentence-transformers) to index code vulnerabilities and proven fixes.
    *   **Agent Retrieval Augmented Generation:** Auditor and Patcher agents retrieve similar past vulnerabilities and verified remediation patterns dynamically during execution.

## Phase 1: Foundation, Modular Agents, and Self-Learning RAG
**Goal:** Build the modular agent architecture and initial self-learning RAG pipeline using accessible APIs/local models to validate the remediation loop.

1.  **Modular Repository Structure & Core Scaffolding**
    *   Restructure backend into dedicated directories for each agent:
        *   `backend/agents/architect/`
        *   `backend/agents/developer/`
        *   `backend/agents/auditor/`
        *   `backend/agents/patcher/`
        *   `backend/agents/orchestrator/`
    *   Configure FastAPI with CORS and WebSocket/SSE streaming endpoints for real-time agent status.
2.  **Self-Learning RAG System Setup (`backend/rag/`)**
    *   Initialize vector storage (e.g. ChromaDB / FAISS) with local or API-based embeddings.
    *   Seed the knowledge base with OWASP Top 10 patterns, CWE remediation guides, and secure coding baselines.
    *   Implement **Feedback & Self-Learning Ingestion**:
        *   When Patcher successfully remediates code validated by Auditor, index the `(vulnerability, original_code, diff, explanation)` tuple into the vector store.
        *   Enable Auditor and Patcher to query the vector store for nearest-neighbor remediation memories before acting.
3.  **Core Multi-Agent Loop**
    *   Implement the Iterative Remediation Algorithm loop: Architect -> Developer -> Auditor -> Patcher.
    *   Static analysis engine (regex/AST for OWASP Top 10 patterns).
    *   Convergence check: loop repeats until Auditor passes with 0 critical findings or max iteration limit is reached.
4.  **Agent Logic & API Integration**
    *   Define prompts, schemas, and persona interfaces for each agent directory.
    *   Connect agents to provider interface (OpenAI / Anthropic / Ollama) with tool/memory retrieval capabilities.
5.  **Local Testing Environment & Benchmark**
    *   Create a local sandbox for agents to safely execute and test generated/patched code.
    *   Build a test suite of vulnerable code snippets (SQLi, XSS, SSRF, IDOR) to validate self-learning and patching.

## Phase 2: Custom NLP Engine
**Goal:** Replace basic pattern matching and some API dependencies with a custom NLP engine.

1.  **NLP Engine Architecture**
    *   Design a specialized NLP model for parsing code semantics, ASTs, and identifying structural vulnerabilities.
2.  **Training & Fine-tuning**
    *   Curate a dataset of secure and insecure code patterns from accumulated RAG memory and open-source vulnerability datasets.
    *   Train the NLP engine to recognize contextual weaknesses and business logic flaws.
3.  **Integration**
    *   Replace the API-based heuristic analysis in the Auditor Agent with the custom NLP engine.

## Phase 3: Fully Autonomous Local LLM
**Goal:** Replace external LLM APIs with custom-trained, locally hosted LLMs optimized for secure code generation and self-learning adaptation.

1.  **Data Collection & Memory Distillation**
    *   Export high-quality remediation samples from the RAG vector store for fine-tuning datasets.
2.  **Model Training**
    *   Fine-tune open-source base models (e.g., Llama 3, Mistral, Qwen-Coder) specifically for the roles of Architect, Developer, Auditor, and Patcher.
3.  **Deployment & Optimization**
    *   Deploy custom LLMs locally (e.g., vLLM, llama.cpp, or Ollama) to serve the backend.
    *   Optimize for low-latency patching (<15 seconds target).
4.  **Final Pipeline Switch**
    *   Fully decouple from external APIs. The entire framework (Frontend -> Local Backend Orchestrator -> Modular Agents -> Self-Learning RAG -> Local LLMs) runs 100% locally and privately.

## Phase 4: Production Deployment & Integration
**Goal:** Prepare the application for real-world usage.

1.  **Frontend Dashboard:** Interactive agent visualization dashboard in Next.js displaying real-time agent thought streams, RAG lookups, and code diffs.
2.  **Frontend Deployment:** Deploy Next.js frontend to Vercel with secure local or hybrid backend tunnel support.
3.  **IDE Integration:** (Future) Develop VS Code / JetBrains extensions communicating with the Sentinel agent core.
