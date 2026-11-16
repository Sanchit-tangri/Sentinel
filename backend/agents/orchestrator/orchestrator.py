from typing import Dict, Any, List, Optional
from schemas.models import AuditResult, PatchResult, ArchitectSpecification
from agents.architect.agent import ArchitectAgent
from agents.developer.agent import DeveloperAgent
from agents.auditor.agent import AuditorAgent
from agents.patcher.agent import PatcherAgent
from rag.memory_store import MemoryStore
from routing.omniroute_client import OmniRouteClient
from context.session_ledger import SessionLedger


class RemediationOrchestrator:
    """
    Central loop orchestrator coordinating:
    Architect -> Developer -> Auditor -> Patcher -> Self-Learning RAG Ingestion.
    Preserves context through SessionLedger and routes LLM calls via OmniRoute.
    """

    def __init__(
        self,
        max_iterations: int = 3,
        memory_store: Optional[MemoryStore] = None,
        omniroute_client: Optional[OmniRouteClient] = None
    ):
        self.max_iterations = max_iterations
        self.memory_store = memory_store or MemoryStore()
        self.omniroute_client = omniroute_client or OmniRouteClient()

        self.architect = ArchitectAgent()
        self.developer = DeveloperAgent(omniroute_client=self.omniroute_client)
        self.auditor = AuditorAgent()
        self.patcher = PatcherAgent(
            memory_store=self.memory_store,
            omniroute_client=self.omniroute_client
        )

    def remediate_code(
        self,
        raw_code: str,
        filename: str = "snippet.py",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the self-healing iterative loop on input code.
        Maintains an immutable SessionLedger so if OmniRoute switches models
        mid-loop, context and symbol invariants remain rock-solid.
        """
        ledger = SessionLedger(
            session_id=session_id,
            filename=filename,
            initial_code=raw_code
        )

        current_code = raw_code
        iteration_history: List[Dict[str, Any]] = []
        is_resolved = False

        # Step 1: Architect boundaries check
        spec = self.architect.analyze_boundaries(
            task_description=f"Audit and remediate security vulnerabilities in {filename}"
        )
        ledger.set_architect_boundaries(
            invariants=spec.security_invariants,
            prohibited_patterns=spec.prohibited_patterns
        )

        for iteration in range(1, self.max_iterations + 1):
            # Step 2: Auditor scans current code
            audit_result: AuditResult = self.auditor.audit_code(current_code, filename=filename)

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
                break

            # Step 3: Patcher applies surgical fix via OmniRoute + RAG memories
            patch_result: PatchResult = self.patcher.generate_patch(
                code=current_code,
                audit_result=audit_result,
                iteration=iteration,
                session_ledger=ledger
            )

            # Step 4: Verify patch with a second audit
            post_patch_audit = self.auditor.audit_code(patch_result.patched_code, filename=filename)

            iteration_entry["patch_diff"] = patch_result.diff
            iteration_entry["patch_explanation"] = patch_result.explanation
            iteration_entry["model_used"] = ledger.active_model
            iteration_history.append(iteration_entry)

            # Step 5: Self-learning RAG ingestion on verified fix
            if post_patch_audit.is_secure and not audit_result.is_secure:
                for finding in audit_result.findings:
                    self.memory_store.record_success(
                        vulnerability=finding,
                        vulnerable_code=current_code,
                        patched_diff=patch_result.diff,
                        explanation=patch_result.explanation
                    )
                # Mark attempt as passed in ledger
                if ledger.attempts:
                    ledger.attempts[-1].passed_audit = True

            current_code = patch_result.patched_code
            if post_patch_audit.is_secure:
                is_resolved = True
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
            "final_model": ledger.active_model
        }
