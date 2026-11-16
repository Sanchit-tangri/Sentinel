# Sentinel: Autonomous Security Patching & Code Synthesis Framework
## Master Architecture & Implementation Plan (v2.0)

**Author:** Enterprise Architecture & AI Systems Group  
**Status:** In Active Development (Phase 1 Baseline Implemented; Phase 2 OmniRoute & Context Engine Transition Underway)  
**Target Milestone:** Enterprise-grade self-healing code generation with zero-context-loss model routing.

---

## 1. Executive Summary & Strategic Vision

Modern engineering organizations face a structural bottleneck: development velocity outpaces security verification. The traditional paradigm—treating security as a reactive post-commit or CI/CD gate—generates massive backlog debt and leaves critical zero-day windows open.

**Sentinel** inverts this paradigm by shifting security left into the exact millisecond code is conceived and generated. Operating as a decentralized, autonomous multi-agent mesh, Sentinel continuously:
1. Defines formal trust boundaries and security invariants before code generation.
2. Synthesizes defensive implementations using an intelligent multi-model gateway (**OmniRoute**).
3. Audits code via a dual static/heuristic verification engine against the OWASP Top 10 and CWE taxonomies.
4. Surgically patches vulnerabilities in an iterative convergence loop.
5. Ingests verified patch post-mortems into an episodic **Self-Learning RAG** memory store.

### The Multi-Model Challenge & Context Resilience
In production, relying on a single monolithic LLM exposes the platform to rate-limiting, regional latency spikes, vendor lock-in, and ballooning inference costs. Sentinel incorporates **OmniRoute** to route queries across best-of-breed models (e.g., Claude 3.5 Sonnet, GPT-4o, DeepSeek-Coder, Qwen2.5-Coder, local vLLM instances) depending on latency, cost, and task complexity.

However, **dynamic model switching introduces catastrophic risk: Context Amnesia and Hallucination Drift.** Each model family has divergent tokenizers, system-prompt sensitivities, context window dynamics, and attention decay patterns. When OmniRoute shifts execution mid-loop (e.g., from an expensive frontier model to a fast local model), naive implementations lose variable references, introduce phantom APIs, and violate architectural invariants.

To solve this, Sentinel incorporates a **Model-Agnostic Context Remembrance Engine & Dual-Tier RAG Architecture**, decoupling memory and state from individual LLM context windows into an external, immutable session ledger and semantic vector retrieval plane.

---

## 2. Current Implementation Status Audit (As of November 2026)

| Component | Status | % Done | Implemented Details | Remaining / Technical Debt |
| :--- | :---: | :---: | :--- | :--- |
| **Project Scaffolding & API** | 🟡 Partial | **65%** | FastAPI app (`backend/main.py`), Pydantic schemas (`schemas/models.py`), CORS configuration, basic REST endpoints (`/api/audit`, `/api/remediate`, `/api/rag/search`). | Missing WebSocket/SSE streaming endpoints for real-time token/thought streams; missing authentication and tenant isolation. |
| **Architect Agent** | 🔴 Stubbed | **20%** | Static rule-based specifications (`agents/architect/agent.py`) defining hardcoded trust boundaries and prohibited patterns. | Needs dynamic repository profiling, dependency inspection, and framework-aware invariant generation. |
| **Developer Agent** | 🔴 Stubbed | **10%** | Minimal boilerplate stub returning a static dummy Python function (`agents/developer/agent.py`). | **Critical path:** Needs integration with OmniRoute gateway, dynamic prompt construction, and context re-hydration. |
| **Auditor Agent** | 🟡 Functional (Static) | **50%** | Regex-based static analysis engine detecting SQLi (CWE-89), Command Injection (CWE-78), eval/exec/pickle (CWE-95, CWE-502), and secrets (CWE-798). | Needs AST-based semantic analysis, taint tracking, and AI-assisted heuristic validation to prevent false negatives. |
| **Patcher Agent** | 🟡 Functional (Rule-based) | **45%** | Regex-based surgical replacement for SQLi, CWE-78, CWE-95; unified diff generation via `difflib` (`agents/patcher/agent.py`). | Needs LLM-driven patch synthesis via OmniRoute when regex heuristics fail; AST validation to ensure functional invariance. |
| **RAG & Memory Store** | 🟡 Functional (Prototype) | **40%** | Dual-mode memory store (`rag/memory_store.py`) supporting ChromaDB vector storage with a graceful JSON file fallback; records successful patch diffs. | Needs semantic code chunking, hybrid BM25 + dense vector search, episodic context persistence, and cross-session retrieval. |
| **Remediation Loop** | 🟡 Functional (Synchronous) | **60%** | Orchestrator (`agents/orchestrator/orchestrator.py`) runs Architect -> Auditor -> Patcher -> Verify -> RAG Ingest loop up to `max_iterations`. | Lacks sandboxed execution (isolated test runner) to verify patches don't break business logic; blocking synchronous calls. |
| **Frontend UI** | 🔴 Unstarted | **5%** | Vanilla Next.js boilerplate initialized with Tailwind CSS. | Completely unimplemented. Needs real-time agent thought telemetry, side-by-side diff review, RAG memory inspector, and IDE integration. |
| **Test Suite & Benchmarks** | 🔴 Missing | **0%** | No unit tests, integration tests, or evaluation benchmarks for CWE patches. | Needs standard OWASP Benchmark / SecEval integration to measure patch convergence and false positive rates. |

**Overall Project Progress:** **~32% Core Prototype Complete** (Foundational plumbing in place; reasoning engine, OmniRoute gateway, and context persistence pending).

---

## 3. Target System Architecture

```
                                  +-------------------------------------------+
                                  |            Next.js Frontend / IDE         |
                                  |   (Real-time Telemetry, Diff UI, Logs)    |
                                  +---------------------+---------------------+
                                                        | WebSocket / REST
                                                        v
                                  +---------------------+---------------------+
                                  |       Sentinel Orchestrator Core          |
                                  | (State Machine, Convergence Verification) |
                                  +----------+--------------------+-----------+
                                             |                    |
                 +---------------------------+                    +---------------------------+
                 |                                                                            |
                 v                                                                            v
  +--------------+---------------+                                             +--------------+---------------+
  |    Context Remembrance       |                                             |    OmniRoute Intelligent     |
  |         Engine               |                                             |       Routing Gateway        |
  |------------------------------|                                             |------------------------------|
  | - Session Ledger (Immutable) |                                             | - Latency & Cost Optimization|
  | - Normalized Context Brief   |                                             | - Fallback & Circuit Breakers|
  | - AST Symbol Table Cache     | <=========================================> | - Frontier LLMs (Claude/GPT) |
  | - Active Diff Lineage        |        Hydrates Switched Model Prompts      | - Open LLMs (Qwen/DeepSeek)  |
  +--------------+---------------+                                             | - Local Sovereign (vLLM/Ollama|
                 |                                                             +--------------+---------------+
                 v                                                                            |
  +--------------+---------------+                                                            |
  |    Dual-Tier RAG Engine      |                                                            |
  |------------------------------|                                                            |
  | 1. Episodic Remediation RAG  |                                                            |
  |    (Verified Diffs, Post-    |                                                            |
  |     Mortems, CWE Playbooks)  |                                                            |
  | 2. Codebase Semantic RAG     |                                                            |
  |    (Project Symbols, Graph,  |                                                            |
  |     Dependency Signatures)   |                                                            |
  +------------------------------+                                                            |
                 ^                                                                            |
                 |                                                                            |
                 +-------------------+--------------------+-----------------------------------+
                                     |                    |
                                     v                    v
                              +------+-----+       +------+-----+
                              |  Auditor   | <---> |  Patcher   |
                              |  (AST/AI)  |       |  (Surgical)|
                              +------------+       +------------+
```

---

## 4. Detailed Implementation Phases

### Phase 1: Core Foundation Hardening & Sandboxing (Current Phase - Completion)
**Goal:** Stabilize the baseline pipeline, eliminate mock stubs, and establish deterministic execution verification.

1. **Deterministic Sandboxing (`backend/sandbox/`)**:
   - Implement an isolated execution environment (Docker / lightweight process container) to run unit tests against generated/patched code.
   - Guard against regressions: A patch is rejected if existing unit tests fail, even if the security auditor passes.
2. **Schema & Telemetry Upgrades**:
   - Implement asynchronous FastAPI event streams (Server-Sent Events / WebSockets) streaming agent phase changes (`ARCHITECT_ANALYZING`, `DEVELOPER_GENERATING`, `AUDITOR_SCANNING`, `PATCHER_REMEDIATING`).
3. **Comprehensive Test Suite (`backend/tests/`)**:
   - Establish regression test suite covering OWASP Top 10 categories:
     - SQL Injection (CWE-89)
     - OS Command Injection (CWE-78)
     - Code Injection & Unsafe Deserialization (CWE-95, CWE-502)
     - Server-Side Request Forgery (SSRF - CWE-918)
     - Broken Access Control / IDOR (CWE-639)

---

### Phase 2: OmniRoute Gateway & Context Remembrance Engine (High Priority)
**Goal:** Integrate the OmniRoute model routing gateway for code generation and deploy the Context Remembrance Engine to completely eliminate hallucination and state loss across model transitions.

#### 2.1 OmniRoute Integration Layer (`backend/routing/`)
1. **Unified Routing Client (`backend/routing/omniroute_client.py`)**:
   - Abstraction layer over OmniRoute API supporting dynamic model selection:
     - **Tier 1 (High Reasoning / Strategic):** Claude 3.5 Sonnet / GPT-4o (Architect analysis, complex multi-file logic).
     - **Tier 2 (High-Throughput Code Generation):** DeepSeek-Coder-V2/V3 / Qwen-2.5-Coder-32B (Developer agent code synthesis).
     - **Tier 3 (Rapid Surgical Patching / Local Fallback):** Mistral-Codestral / local vLLM instances (Patcher agent diff synthesis).
   - Configure automatic failover triggers:
     - HTTP 429 (Rate Limit) -> Seamlessly route to secondary provider.
     - Latency spike (> 8,000ms) -> Route to fast speculative model.
     - Context window overflow -> Route to extended-window models.

#### 2.2 Context Remembrance Engine (`backend/context/`)
1. **Decoupled Session Ledger (`backend/context/session_ledger.py`)**:
   - LLMs are treated as stateless compute functions; conversation state is never owned by the remote LLM session.
   - Maintain a centralized, serializable state machine tracking:
     - `task_id`: Global unique session identifier.
     - `architect_invariants`: Permanent architectural boundaries that cannot be hallucinated away.
     - `symbol_table`: Extracted classes, functions, variable types, and import statements in scope.
     - `audit_findings_trail`: Historical log of all findings, remediations attempted, and reasons for failure.
     - `active_code_snapshot`: Canonical current state of the source file.
2. **Model-Agnostic Context Normalizer (`backend/context/normalizer.py`)**:
   - Translates the session state into a standardized prompt envelope compatible with *any* model:
     ```markdown
     <sentinel_context>
       <architect_invariants>...</architect_invariants>
       <scoped_symbols>...</scoped_symbols>
       <prior_remediation_attempts>...</prior_remediation_attempts>
       <target_cwe_constraints>...</target_cwe_constraints>
     </sentinel_context>
     ```
   - Normalizes tokenizer boundaries and strips proprietary formatting quirks before dispatching to the routed model.
3. **Anti-Hallucination & Drift Validator (`backend/context/drift_guard.py`)**:
   - Post-generation semantic checker comparing output against the AST Symbol Table:
     - Validates that the newly generated code did not introduce nonexistent packages or mutate untouched function signatures.
     - Detects hallucinated variables or forgotten business requirements caused by a model switch.

---

### Phase 3: Dual-Tier Self-Learning RAG & Semantic Code Search
**Goal:** Supercharge retrieval accuracy by separating episodic patch memory from codebase-level semantic knowledge.

1. **Tier 1: Episodic Remediation RAG (`backend/rag/episodic/`)**:
   - ChromaDB / Qdrant vector store indexing verified patch solutions.
   - Store triples: `(CWE_ID + Vulnerability_Signature, Insecure_AST, Surgical_Diff, Rationale)`.
   - Before the Patcher Agent calls OmniRoute, it queries Episodic RAG for the top $k=3$ most similar historical fixes, injecting proven patch patterns directly into the prompt.
2. **Tier 2: Codebase Semantic RAG (`backend/rag/codebase/`)**:
   - AST-aware chunker parsing the entire user repository into semantic units (classes, functions, interfaces).
   - When generating or patching code, provide the routed model with precise surrounding context (imported utilities, database models, internal auth helpers) to prevent hallucinating custom implementations.
3. **Continuous Reinforcement Loop**:
   - Autonomous feedback rating: If a generated patch passes both static audit and sandbox test runs, its vector weight is elevated.
   - If a patch fails the Auditor or breaks a test, the negative pattern is stored as an anti-pattern example.

---

### Phase 4: Hybrid Dual-Engine Auditor (Static AST + Semantic LLM Scanner)
**Goal:** Eliminate regex fragility by upgrading the Auditor Agent to an enterprise-grade static + semantic analysis engine.

1. **Python AST & Tree-Sitter Integration (`backend/agents/auditor/ast_engine.py`)**:
   - Replace regular expressions with concrete syntax tree parsing via `tree-sitter`.
   - Implement dataflow taint analysis: Track untrusted user input sources (`request.args`, `payload`) to sensitive sinks (`db.execute`, `subprocess`, `open`).
2. **OmniRoute Semantic Security Audit**:
   - Secondary verification pass using a fine-tuned or routed LLM to identify contextual business logic flaws (e.g., IDOR, race conditions, authentication bypasses) that static AST engines cannot detect.
3. **Convergence & Loop Control**:
   - Enforce mathematical convergence: If the Auditor detects no net reduction in vulnerability severity over 2 consecutive iterations, halt the loop and escalate to human review with diagnostic telemetry.

---

### Phase 5: Next.js Interactive Dashboard & Real-Time Telemetry
**Goal:** Provide full visibility into the agent mesh, model routing decisions, and diff lineages.

1. **Mission Control UI (`frontend/src/app/dashboard/`)**:
   - **Live Agent Mesh Visualizer:** Interactive DAG showing active agent states (`Architect` -> `Developer` -> `Auditor` -> `Patcher`).
   - **OmniRoute Telemetry Card:** Live model indicator showing which model is currently active (e.g., switched from Claude-Sonnet to DeepSeek-Coder), latency metrics, and token cost.
   - **Side-by-Side Diff Viewer:** Interactive Monaco / Prism diff viewer displaying real-time code transformations.
   - **Context Remembrance Inspector:** Live view of the Session Ledger, showing invariants, scoped symbols, and RAG memories retrieved.
2. **WebSocket Real-Time Stream**:
   - Bi-directional communication channel streaming intermediate thoughts, audit findings, and AST validation errors.

---

### Phase 6: Custom NLP Engine & Sovereign Local LLMs (Long-Term Vision)
**Goal:** Transition from external cloud routing to a 100% sovereign, air-gapped local environment.

1. **Model Distillation from RAG Memories**:
   - Export curated `(vulnerable_code, context, verified_patch)` pairs from the Episodic RAG store.
   - Fine-tune open-weight base models (Qwen-2.5-Coder-7B/14B, DeepSeek-Coder) using LoRA / QLoRA for dedicated agent roles.
2. **Local Inference Serving (vLLM / llama.cpp)**:
   - Host fine-tuned models on local GPU infrastructure with speculative decoding for sub-second patch generation.
   - OmniRoute configured to prioritize 0-cost local inference, falling back to frontier cloud models only for edge-case reasoning tasks.

---

## 5. Risk Matrix & Strategic Mitigation

| Risk Vector | Business & Technical Impact | Architectural Mitigation |
| :--- | :--- | :--- |
| **Model Drift & Hallucination on Switch** | Broken code, syntax errors, hallucinated third-party dependencies. | **Context Remembrance Engine:** Strict session ledger, AST symbol table injection, and post-generation drift validation before auditing. |
| **Infinite Remediation Loops** | High API costs, latency timeouts, thread exhaustion. | **Convergence Circuit Breakers:** Strict `max_iterations` (default: 3), diff delta monitoring, and automated loop escalation. |
| **Functional Logic Breakage (Over-Patching)** | Code is secure but no longer performs its business function. | **Deterministic Sandboxing:** Unit test execution runner verifying that patched code passes functional assertions. |
| **Vendor Rate Limits / Outages** | Development downtime, failed builds. | **OmniRoute Smart Fallback:** Automatic dynamic failover across multi-region and multi-provider models. |
| **RAG Retrieval Poisoning** | Incorrect or insecure patch ingested into memory, propagating bad fixes. | **Zero-Trust Verification Gate:** Only patches that pass 100% of Auditor checks and Sandbox unit tests are written to Episodic RAG. |

---

## 6. Immediate Next Steps & Action Items

1. **Step 1:** Implement the **Context Remembrance Engine** (`backend/context/`) to establish the immutable session ledger and prompt normalizer.
2. **Step 2:** Build the **OmniRoute Gateway Client** (`backend/routing/omniroute_client.py`) with support for dynamic model routing and fallback circuits.
3. **Step 3:** Upgrade `DeveloperAgent` and `PatcherAgent` to utilize OmniRoute with injected Context Remembrance and Episodic RAG memories.
4. **Step 4:** Build the **Sandboxed Execution Runner** (`backend/sandbox/`) to validate functional tests alongside security audits.
5. **Step 5:** Build the **Next.js Dashboard** with Monaco diff editing, live agent telemetry, and OmniRoute routing metrics.
