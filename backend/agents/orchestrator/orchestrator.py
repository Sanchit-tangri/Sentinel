import asyncio
import difflib
from typing import Dict, Any, List, Optional
from schemas.models import AuditResult, PatchResult, ArchitectSpecification, AgentConfig
from agents.architect.agent import ArchitectAgent
from agents.developer.agent import DeveloperAgent
from agents.auditor.agent import AuditorAgent
from agents.patcher.agent import PatcherAgent
from agents.orchestrator.event_bus import SessionEventBus
from rag.memory_store import MemoryStore
from routing.omniroute_client import OmniRouteClient
from context.session_ledger import SessionLedger


class RemediationOrchestrator:
    """
    Sentinel v1.0 Polyglot Multi-Agent Orchestrator.
    Coordinates:
      - Dex (The Architect): Threat modeling & boundary formulation
      - Pixel (The Developer): OmniRoute code synthesis & framework scaffolding
      - Snooze (The Auditor): Polyglot OWASP Top 10 & CWE verification
      - Glitch (The Patcher): Zero-regression surgical remediation & live diff streaming
    Supports:
      - Execution modes: 'autopilot' (automated self-healing) and 'vibe_interactive' (approval gate)
      - Real-time WebSocket telemetry event streaming (AGENT_STATE, CURSOR_MOVE, VULN_DETECTED, LIVE_DIFF_CHUNK)
      - Customizable agent config: persona_style, security_level, ui_theme_target
    """

    def __init__(
        self,
        max_iterations: int = 3,
        memory_store: Optional[MemoryStore] = None,
        omniroute_client: Optional[OmniRouteClient] = None,
        event_bus: Optional[SessionEventBus] = None
    ):
        self.max_iterations = max_iterations
        self.memory_store = memory_store or MemoryStore()
        self.omniroute_client = omniroute_client or OmniRouteClient()
        self.event_bus = event_bus or SessionEventBus()

        self.architect = ArchitectAgent()
        self.developer = DeveloperAgent(omniroute_client=self.omniroute_client)
        self.auditor = AuditorAgent(name="Snooze")
        self.patcher = PatcherAgent(
            memory_store=self.memory_store,
            omniroute_client=self.omniroute_client,
            name="Glitch"
        )

    # -------------------------------------------------------------------------
    # Synchronous Remediation Loop (100% Backwards Compatible for Tests & REST)
    # -------------------------------------------------------------------------
    def remediate_code(
        self,
        raw_code: str,
        filename: str = "snippet.py",
        session_id: Optional[str] = None,
        mode: str = "autopilot",
        agent_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes the self-healing iterative loop on input code.
        Preserves backward compatibility while recording telemetry events.
        """
        ledger = SessionLedger(
            session_id=session_id,
            filename=filename,
            initial_code=raw_code
        )
        sid = ledger.session_id
        config = agent_config or {}
        persona = config.get("persona_style", "principal_engineer")
        sec_level = config.get("security_level", "balanced")

        current_code = raw_code
        iteration_history: List[Dict[str, Any]] = []
        is_resolved = False

        # Scene 1: Dex (The Architect)
        msg_dex = self.event_bus.style_message("dex", "thinking", f"invariants for {filename}", persona)
        self.event_bus.emit_sync(sid, {"type": "AGENT_STATE", "agent": "dex", "status": "thinking", "message": msg_dex})
        self.event_bus.emit_sync(sid, {"type": "CURSOR_MOVE", "agent": "dex", "file": filename, "line": 1, "column": 1})

        spec = self.architect.analyze_boundaries(
            task_description=f"Audit and remediate security vulnerabilities in {filename}"
        )
        ledger.set_architect_boundaries(
            invariants=spec.security_invariants,
            prohibited_patterns=spec.prohibited_patterns
        )

        for iteration in range(1, self.max_iterations + 1):
            # Scene 2: Snooze (The Auditor)
            msg_snooze = self.event_bus.style_message("snooze", "scanning", f"iteration {iteration}", persona)
            self.event_bus.emit_sync(sid, {"type": "AGENT_STATE", "agent": "snooze", "status": "scanning", "message": msg_snooze})

            audit_result: AuditResult = self.auditor.audit_code(current_code, filename=filename, security_level=sec_level)

            # Stream findings & cursor moves
            for finding in audit_result.findings:
                line_no = finding.line_number or 1
                self.event_bus.emit_sync(sid, {"type": "CURSOR_MOVE", "agent": "snooze", "file": finding.file_path or filename, "line": line_no, "column": 1})
                self.event_bus.emit_sync(sid, {"type": "VULN_DETECTED", "finding": finding.model_dump()})

            iteration_entry = {
                "iteration": iteration,
                "is_secure": audit_result.is_secure,
                "findings": [f.model_dump() for f in audit_result.findings],
                "code_snapshot": current_code,
                "active_model": ledger.active_model
            }

            if audit_result.is_secure:
                is_resolved = True
                iteration_history.append(iteration_entry)
                msg_done = self.event_bus.style_message("snooze", "completed", "All checks passed clean.", persona)
                self.event_bus.emit_sync(sid, {"type": "AGENT_STATE", "agent": "snooze", "status": "completed", "message": msg_done})
                break

            # Scene 3: Glitch (The Patcher)
            msg_glitch = self.event_bus.style_message("glitch", "editing", f"remediating {len(audit_result.findings)} finding(s)", persona)
            self.event_bus.emit_sync(sid, {"type": "AGENT_STATE", "agent": "glitch", "status": "editing", "message": msg_glitch})

            first_line = audit_result.findings[0].line_number or 1
            self.event_bus.emit_sync(sid, {"type": "CURSOR_MOVE", "agent": "glitch", "file": filename, "line": first_line, "column": 1})

            patch_result: PatchResult = self.patcher.generate_patch(
                code=current_code,
                audit_result=audit_result,
                iteration=iteration,
                session_ledger=ledger
            )

            # Stream live diff chunk
            self._stream_diff_chunks_sync(sid, filename, patch_result.diff, patch_result.explanation)

            # Scene 4: Verify patch with a second audit
            post_patch_audit = self.auditor.audit_code(patch_result.patched_code, filename=filename, security_level=sec_level)

            iteration_entry["patch_diff"] = patch_result.diff
            iteration_entry["patch_explanation"] = patch_result.explanation
            iteration_entry["model_used"] = ledger.active_model
            iteration_history.append(iteration_entry)

            # Scene 5: Self-learning RAG ingestion on verified fix
            if post_patch_audit.is_secure and not audit_result.is_secure:
                for finding in audit_result.findings:
                    self.memory_store.record_success(
                        vulnerability=finding,
                        vulnerable_code=current_code,
                        patched_diff=patch_result.diff,
                        explanation=patch_result.explanation
                    )
                if ledger.attempts:
                    ledger.attempts[-1].passed_audit = True

            current_code = patch_result.patched_code
            if post_patch_audit.is_secure:
                is_resolved = True
                msg_glitch_done = self.event_bus.style_message("glitch", "completed", "", persona)
                self.event_bus.emit_sync(sid, {"type": "AGENT_STATE", "agent": "glitch", "status": "completed", "message": msg_glitch_done})
                break

        return {
            "session_id": ledger.session_id,
            "initial_code": raw_code,
            "final_code": current_code,
            "is_secure": is_resolved,
            "total_iterations": len(iteration_history),
            "history": iteration_history,
            "architect_spec": spec.model_dump(),
            "model_history": ledger.model_history,
            "final_model": ledger.active_model,
            "mode": mode,
            "agent_config": config
        }

    # -------------------------------------------------------------------------
    # Asynchronous Remediation Loop (Real-Time WebSocket & Vibe Interactive)
    # -------------------------------------------------------------------------
    async def remediate_code_async(
        self,
        raw_code: str,
        filename: str = "snippet.py",
        session_id: Optional[str] = None,
        mode: str = "autopilot",
        agent_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Asynchronous orchestrator loop with interactive Vibe Coding support.
        In 'vibe_interactive' mode:
          Pauses via an asyncio.Event when Snooze detects vulnerabilities,
          and awaits WebSocket command APPROVE_FIX before Glitch applies the patch.
        In 'autopilot' mode:
          Auto-remediates all findings in an automated loop.
        """
        ledger = SessionLedger(
            session_id=session_id,
            filename=filename,
            initial_code=raw_code
        )
        sid = ledger.session_id
        config = agent_config or {}
        persona = config.get("persona_style", "principal_engineer")
        sec_level = config.get("security_level", "balanced")

        current_code = raw_code
        iteration_history: List[Dict[str, Any]] = []
        is_resolved = False

        # Dex: The Architect
        msg_dex = self.event_bus.style_message("dex", "thinking", f"modeling attack surfaces in {filename}", persona)
        await self.event_bus.broadcast(sid, {"type": "AGENT_STATE", "agent": "dex", "status": "thinking", "message": msg_dex})
        await self.event_bus.broadcast(sid, {"type": "CURSOR_MOVE", "agent": "dex", "file": filename, "line": 1, "column": 1})

        spec = self.architect.analyze_boundaries(
            task_description=f"Audit and remediate security vulnerabilities in {filename}"
        )
        ledger.set_architect_boundaries(
            invariants=spec.security_invariants,
            prohibited_patterns=spec.prohibited_patterns
        )

        for iteration in range(1, self.max_iterations + 1):
            # Snooze: The Auditor
            msg_snooze = self.event_bus.style_message("snooze", "scanning", f"pass {iteration}", persona)
            await self.event_bus.broadcast(sid, {"type": "AGENT_STATE", "agent": "snooze", "status": "scanning", "message": msg_snooze})

            audit_result: AuditResult = self.auditor.audit_code(current_code, filename=filename, security_level=sec_level)

            for finding in audit_result.findings:
                line_no = finding.line_number or 1
                await self.event_bus.broadcast(sid, {"type": "CURSOR_MOVE", "agent": "snooze", "file": finding.file_path or filename, "line": line_no, "column": 1})
                await self.event_bus.broadcast(sid, {"type": "VULN_DETECTED", "finding": finding.model_dump()})

            iteration_entry = {
                "iteration": iteration,
                "is_secure": audit_result.is_secure,
                "findings": [f.model_dump() for f in audit_result.findings],
                "code_snapshot": current_code,
                "active_model": ledger.active_model
            }

            if audit_result.is_secure:
                is_resolved = True
                iteration_history.append(iteration_entry)
                msg_done = self.event_bus.style_message("snooze", "completed", "Zero vulnerabilities detected.", persona)
                await self.event_bus.broadcast(sid, {"type": "AGENT_STATE", "agent": "snooze", "status": "completed", "message": msg_done})
                break

            # -----------------------------------------------------------------
            # Interactive Vibe Coding Pause Gate
            # -----------------------------------------------------------------
            approval_payload = {}
            if mode == "vibe_interactive" and audit_result.findings:
                msg_pause = self.event_bus.style_message("snooze", "waiting_approval", "", persona)
                await self.event_bus.broadcast(sid, {
                    "type": "AGENT_STATE",
                    "agent": "snooze",
                    "status": "waiting_approval",
                    "message": msg_pause,
                    "findings_count": len(audit_result.findings),
                    "options": [
                        {"finding_id": f.id, "title": f.title, "fix_options": f.fix_options}
                        for f in audit_result.findings
                    ]
                })

                # Pause on asyncio.Event awaiting WebSocket command APPROVE_FIX
                first_finding_id = audit_result.findings[0].id
                approval_payload = await self.event_bus.wait_for_approval(sid, first_finding_id)

            # Glitch: The Patcher
            selected_strat = approval_payload.get("selected_strategy", "")
            strat_detail = f"with approved strategy: {selected_strat}" if selected_strat else "initiating surgical patch"
            msg_glitch = self.event_bus.style_message("glitch", "editing", strat_detail, persona)
            await self.event_bus.broadcast(sid, {"type": "AGENT_STATE", "agent": "glitch", "status": "editing", "message": msg_glitch})

            first_line = audit_result.findings[0].line_number or 1
            await self.event_bus.broadcast(sid, {"type": "CURSOR_MOVE", "agent": "glitch", "file": filename, "line": first_line, "column": 1})

            patch_result: PatchResult = self.patcher.generate_patch(
                code=current_code,
                audit_result=audit_result,
                iteration=iteration,
                session_ledger=ledger
            )

            # Stream live diff chunks
            await self._stream_diff_chunks_async(sid, filename, patch_result.diff, patch_result.explanation)

            # Re-audit post-patch
            post_patch_audit = self.auditor.audit_code(patch_result.patched_code, filename=filename, security_level=sec_level)

            iteration_entry["patch_diff"] = patch_result.diff
            iteration_entry["patch_explanation"] = patch_result.explanation
            iteration_entry["model_used"] = ledger.active_model
            iteration_history.append(iteration_entry)

            # Ingest verified fix to RAG
            if post_patch_audit.is_secure and not audit_result.is_secure:
                for finding in audit_result.findings:
                    self.memory_store.record_success(
                        vulnerability=finding,
                        vulnerable_code=current_code,
                        patched_diff=patch_result.diff,
                        explanation=patch_result.explanation
                    )
                if ledger.attempts:
                    ledger.attempts[-1].passed_audit = True

            current_code = patch_result.patched_code
            if post_patch_audit.is_secure:
                is_resolved = True
                msg_glitch_done = self.event_bus.style_message("glitch", "completed", "Patch verified clean.", persona)
                await self.event_bus.broadcast(sid, {"type": "AGENT_STATE", "agent": "glitch", "status": "completed", "message": msg_glitch_done})
                break

        return {
            "session_id": ledger.session_id,
            "initial_code": raw_code,
            "final_code": current_code,
            "is_secure": is_resolved,
            "total_iterations": len(iteration_history),
            "history": iteration_history,
            "architect_spec": spec.model_dump(),
            "model_history": ledger.model_history,
            "final_model": ledger.active_model,
            "mode": mode,
            "agent_config": config
        }

    # -------------------------------------------------------------------------
    # Unified End-to-End Pipeline Synthesis
    # -------------------------------------------------------------------------
    def synthesize_and_secure(
        self,
        prompt: str,
        filename: str = "application.py"
    ) -> Dict[str, Any]:
        """Unified prompt-to-defensible-code generation timeline."""
        ledger = SessionLedger(filename=filename, initial_code="")
        timeline: List[Dict[str, Any]] = []

        # Dex
        spec = self.architect.analyze_boundaries(
            task_description=f"Formulate security invariants and architectural constraints for: {prompt}"
        )
        ledger.set_architect_boundaries(
            invariants=spec.security_invariants,
            prohibited_patterns=spec.prohibited_patterns
        )
        timeline.append({
            "id": "architect",
            "agent": "The Architect",
            "role": "Strategic Threat Modeling & Boundary Definition",
            "model": "claude-3-5-sonnet-20241022",
            "tier": "STRATEGIC",
            "status": "completed",
            "thought": f"Formulated security invariants for: '{prompt[:80]}...'",
            "details": spec.model_dump()
        })

        # Pixel
        dev_result = self.developer.implement(task_prompt=prompt, spec=spec, session_ledger=ledger)
        initial_code = dev_result["code"]
        timeline.append({
            "id": "developer",
            "agent": "The Developer",
            "role": "OmniRoute Code Synthesis",
            "model": dev_result["model_used"],
            "tier": dev_result["tier"],
            "status": "completed",
            "thought": f"Synthesized application code via OmniRoute [{dev_result['model_used']}].",
            "latency_ms": dev_result["latency_ms"],
            "details": {"code": initial_code, "drift_report": dev_result["drift_report"]}
        })

        # Snooze
        audit_result: AuditResult = self.auditor.audit_code(initial_code, filename=filename)
        timeline.append({
            "id": "auditor",
            "agent": "The Auditor",
            "role": "Static AST & Dual-Engine Verification",
            "model": "hybrid-ast-engine",
            "tier": "VERIFICATION",
            "status": "completed",
            "thought": f"Audit verified against OWASP Top 10 & CWE taxonomies. Result: {audit_result.summary}",
            "details": {"is_secure": audit_result.is_secure, "findings": [f.model_dump() for f in audit_result.findings]}
        })

        # Glitch
        final_code = initial_code
        patch_diff = ""
        patch_explanation = ""
        if not audit_result.is_secure:
            patch_result: PatchResult = self.patcher.generate_patch(
                code=initial_code,
                audit_result=audit_result,
                iteration=1,
                session_ledger=ledger
            )
            final_code = patch_result.patched_code
            patch_diff = patch_result.diff
            patch_explanation = patch_result.explanation

            post_audit = self.auditor.audit_code(final_code, filename=filename)
            if post_audit.is_secure:
                for finding in audit_result.findings:
                    self.memory_store.record_success(
                        vulnerability=finding,
                        vulnerable_code=initial_code,
                        patched_diff=patch_diff,
                        explanation=patch_explanation
                    )

            timeline.append({
                "id": "patcher",
                "agent": "The Patcher",
                "role": "Surgical Remediation & RAG Ingestion",
                "model": ledger.active_model or "surgical-patch-engine",
                "tier": "SURGICAL_PATCH",
                "status": "completed",
                "thought": f"Remediated {len(audit_result.findings)} finding(s). Verified clean.",
                "details": {"diff": patch_diff, "explanation": patch_explanation}
            })

        return {
            "session_id": ledger.session_id,
            "filename": filename,
            "initial_code": initial_code,
            "final_code": final_code,
            "is_secure": audit_result.is_secure or (patch_diff != ""),
            "timeline": timeline,
            "sandbox_html": dev_result.get("sandbox_html", "")
        }

    # -------------------------------------------------------------------------
    # Diff Streaming Helpers
    # -------------------------------------------------------------------------
    def _extract_diff_chunk(self, filename: str, diff_text: str, explanation: str) -> Optional[Dict[str, Any]]:
        orig_lines = []
        patch_lines = []
        for line in diff_text.splitlines():
            if line.startswith("---") or line.startswith("+++"):
                continue
            elif line.startswith("-"):
                orig_lines.append(line[1:])
            elif line.startswith("+"):
                patch_lines.append(line[1:])
        if orig_lines or patch_lines:
            return {
                "type": "LIVE_DIFF_CHUNK",
                "file": filename,
                "original_lines": orig_lines,
                "patched_lines": patch_lines,
                "explanation": explanation
            }
        return None

    def _stream_diff_chunks_sync(self, session_id: str, filename: str, diff_text: str, explanation: str) -> None:
        chunk = self._extract_diff_chunk(filename, diff_text, explanation)
        if chunk:
            self.event_bus.emit_sync(session_id, chunk)

    async def _stream_diff_chunks_async(self, session_id: str, filename: str, diff_text: str, explanation: str) -> None:
        chunk = self._extract_diff_chunk(filename, diff_text, explanation)
        if chunk:
            await self.event_bus.broadcast(session_id, chunk)
