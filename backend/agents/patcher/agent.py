import re
import difflib
from typing import Optional, List, Dict, Any
from schemas.models import PatchResult, AuditResult, VulnerabilityFinding
from rag.memory_store import MemoryStore

class PatcherAgent:
    """
    Patcher Agent (Remediation Layer).
    Queries past verified RAG memories and applies remediation patterns
    to surgically fix security vulnerabilities identified by the Auditor.
    """
    def __init__(self, memory_store: Optional[MemoryStore] = None, name: str = "The Patcher"):
        self.name = name
        self.memory_store = memory_store or MemoryStore()

    def generate_patch(
        self,
        code: str,
        audit_result: AuditResult,
        iteration: int = 1
    ) -> PatchResult:
        if audit_result.is_secure or not audit_result.findings:
            return PatchResult(
                task_id=audit_result.task_id,
                iteration=iteration,
                patched_code=code,
                diff="",
                explanation="No vulnerabilities found; code remains unchanged."
            )

        original_code = code
        patched_code = code
        applied_fixes = []

        for finding in audit_result.findings:
            # 1. RAG Query: Check if we have learned a solution for this vulnerability
            similar_memories = self.memory_store.search_similar_remediations(
                query=f"{finding.cwe_id} {finding.title} {finding.snippet or ''}",
                top_k=1
            )
            rag_context = f" (Guided by memory {similar_memories[0]['id']})" if similar_memories else ""

            # 2. Heuristic Remediation Rules
            if finding.cwe_id == "CWE-89":
                # Fix f-string SQL queries -> parameterized query
                new_code = re.sub(
                    r'execute\s*\(\s*f["\'](SELECT.*?WHERE\s+\w+\s*=\s*)\{([a-zA-Z0-9_]+)\}\s*["\']\s*\)',
                    r'execute("\1%s", (\2,))',
                    patched_code
                )
                if new_code != patched_code:
                    patched_code = new_code
                    applied_fixes.append(f"Parametrized SQL query for {finding.cwe_id}{rag_context}")

            elif finding.cwe_id == "CWE-78":
                # Fix os.system -> subprocess.run with argument list
                new_code = re.sub(
                    r'os\.system\s*\((.*?)\)',
                    r'subprocess.run([\1], check=True)',
                    patched_code
                )
                if new_code != patched_code:
                    patched_code = new_code
                    applied_fixes.append(f"Replaced os.system with safe subprocess.run{rag_context}")

            elif finding.cwe_id == "CWE-95":
                # Fix eval() -> ast.literal_eval()
                if "eval(" in patched_code:
                    new_code = patched_code.replace("eval(", "ast.literal_eval(")
                    if "import ast" not in new_code:
                        new_code = "import ast\n" + new_code
                    patched_code = new_code
                    applied_fixes.append(f"Replaced unsafe eval() with ast.literal_eval(){rag_context}")

        # Compute unified diff
        diff_lines = list(difflib.unified_diff(
            original_code.splitlines(keepends=True),
            patched_code.splitlines(keepends=True),
            fromfile="original.py",
            tofile="patched.py"
        ))
        diff_text = "".join(diff_lines)

        explanation = (
            "; ".join(applied_fixes)
            if applied_fixes
            else "Applied defensive sanitization refactoring based on security guidelines."
        )

        return PatchResult(
            task_id=audit_result.task_id,
            iteration=iteration,
            patched_code=patched_code,
            diff=diff_text,
            explanation=explanation
        )
