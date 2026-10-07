from typing import Dict, Any, List, Optional
from schemas.models import AuditResult, PatchResult, ArchitectSpecification
from agents.architect.agent import ArchitectAgent
from agents.developer.agent import DeveloperAgent
from agents.auditor.agent import AuditorAgent
from agents.patcher.agent import PatcherAgent
from rag.memory_store import MemoryStore

class RemediationOrchestrator:
    """
    Central loop orchestrator coordinating:
    Architect -> Developer -> Auditor -> Patcher -> Self-Learning RAG Ingestion.
    """
    def __init__(
        self,
        max_iterations: int = 3,
        memory_store: Optional[MemoryStore] = None
    ):
        self.max_iterations = max_iterations
        self.memory_store = memory_store or MemoryStore()
        self.architect = ArchitectAgent()
        self.developer = DeveloperAgent()
        self.auditor = AuditorAgent()
        self.patcher = PatcherAgent(memory_store=self.memory_store)

    def remediate_code(self, raw_code: str, filename: str = "snippet.py") -> Dict[str, Any]:
        """
        Executes the self-healing iterative loop on input code.
        If patches succeed and are validated by the Auditor, they are ingested
        into the RAG memory store for future autonomous learning.
        """
        current_code = raw_code
        iteration_history: List[Dict[str, Any]] = []
        is_resolved = False

        # Step 1: Architect boundaries check
        spec = self.architect.analyze_boundaries(task_description="Audit and remediate input code")

        for iteration in range(1, self.max_iterations + 1):
            # Step 2: Auditor scans current code
            audit_result: AuditResult = self.auditor.audit_code(current_code, filename=filename)

            iteration_entry = {
                "iteration": iteration,
                "is_secure": audit_result.is_secure,
                "findings": [f.model_dump() for f in audit_result.findings],
                "code_snapshot": current_code
            }

            if audit_result.is_secure:
                is_resolved = True
                iteration_history.append(iteration_entry)
                break

            # Step 3: Patcher applies fix based on heuristics & RAG memory
            patch_result: PatchResult = self.patcher.generate_patch(
                code=current_code,
                audit_result=audit_result,
                iteration=iteration
            )

            # Step 4: Verify patch with a second audit
            post_patch_audit = self.auditor.audit_code(patch_result.patched_code, filename=filename)

            iteration_entry["patch_diff"] = patch_result.diff
            iteration_entry["patch_explanation"] = patch_result.explanation
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

            current_code = patch_result.patched_code
            if post_patch_audit.is_secure:
                is_resolved = True
                break

        return {
            "initial_code": raw_code,
            "final_code": current_code,
            "is_secure": is_resolved,
            "total_iterations": len(iteration_history),
            "history": iteration_history,
            "architect_spec": spec.model_dump()
        }
