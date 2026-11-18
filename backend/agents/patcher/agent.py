import re
import difflib
import logging
from typing import Optional, List, Dict, Any
from schemas.models import PatchResult, AuditResult, VulnerabilityFinding
from rag.memory_store import MemoryStore
from routing.omniroute_client import OmniRouteClient, ModelTier, GenerationResult
from context.session_ledger import SessionLedger
from context.normalizer import ContextNormalizer
from context.drift_guard import DriftGuard, DriftReport

logger = logging.getLogger("Sentinel.PatcherAgent")


class PatcherAgent:
    """
    Patcher Agent (Remediation Layer).
    Surgically fixes vulnerabilities identified by the Auditor Agent.
    Leverages:
      - Episodic RAG memory retrieval of past successful remediations.
      - OmniRoute for dynamic multi-model patch synthesis.
      - Context Remembrance Engine to preserve function signatures and prevent hallucination.
      - Deterministic AST drift validation with heuristic fallback.
    """

    def __init__(
        self,
        memory_store: Optional[MemoryStore] = None,
        omniroute_client: Optional[OmniRouteClient] = None,
        name: str = "The Patcher"
    ):
        self.name = name
        self.memory_store = memory_store or MemoryStore()
        self.client = omniroute_client or OmniRouteClient()

    def generate_patch(
        self,
        code: str,
        audit_result: AuditResult,
        iteration: int = 1,
        session_ledger: Optional[SessionLedger] = None
    ) -> PatchResult:
        if audit_result.is_secure or not audit_result.findings:
            return PatchResult(
                task_id=audit_result.task_id,
                iteration=iteration,
                patched_code=code,
                diff="",
                explanation="No vulnerabilities found; code remains unchanged."
            )

        ledger = session_ledger or SessionLedger(
            initial_code=code,
            filename=audit_result.task_id.replace("audit-", "")
        )

        # 1. RAG Query: Retrieve past verified solutions for these findings
        query_terms = " ".join([f"{f.cwe_id} {f.title} {f.snippet or ''}" for f in audit_result.findings])
        similar_memories = self.memory_store.search_similar_remediations(query=query_terms, top_k=2)
        ledger.record_rag_memories(similar_memories)

        # 2. Try OmniRoute LLM-driven surgical patch
        findings_payload = [f.model_dump() for f in audit_result.findings]
        prompt = ContextNormalizer.build_patcher_prompt(
            code=code,
            findings=findings_payload,
            ledger=ledger,
            iteration=iteration
        )

        gen_result: GenerationResult = self.client.generate(
            prompt=prompt,
            system_prompt=(
                "You are an expert security patch engineer. "
                "Surgically remediate the security vulnerabilities without breaking existing business logic or mutating signatures."
            ),
            tier=ModelTier.SURGICAL_PATCH
        )

        ledger.record_model_switch(gen_result.model_used)
        candidate_code = self._extract_code(gen_result.content)

        # 3. Validate Candidate with DriftGuard
        drift_report: DriftReport = DriftGuard.validate(
            candidate_code=candidate_code,
            baseline_symbols=ledger.symbol_table,
            prohibited_patterns=ledger.prohibited_patterns
        )

        patched_code = candidate_code
        explanation = f"Surgically patched via OmniRoute ({gen_result.model_used})."

        # 4. If LLM patch failed drift validation, fall back to heuristic rules
        if not drift_report.is_valid:
            logger.warning(
                f"[PatcherAgent] LLM patch failed drift check: {drift_report.summary}. "
                f"Falling back to deterministic heuristic patcher."
            )
            heuristic_code, heuristic_fixes = self._apply_heuristic_patches(code, audit_result.findings, similar_memories)
            patched_code = heuristic_code
            explanation = (
                f"Fallback heuristic patch applied ({'; '.join(heuristic_fixes)}). "
                f"LLM patch rejected due to: {drift_report.summary}"
            )
        else:
            explanation_match = re.search(r"```(?:\w+)?\n[\s\S]*?```\s*(.*)", gen_result.content, re.DOTALL)
            if explanation_match and explanation_match.group(1).strip():
                explanation = f"[{gen_result.model_used}] " + explanation_match.group(1).strip()

        # Compute unified diff
        diff_lines = list(difflib.unified_diff(
            code.splitlines(keepends=True),
            patched_code.splitlines(keepends=True),
            fromfile="original.py",
            tofile="patched.py"
        ))
        diff_text = "".join(diff_lines)

        # Update ledger
        ledger.update_active_code(patched_code)
        ledger.record_attempt(
            iteration=iteration,
            model_id=gen_result.model_used,
            findings_addressed=[f.id for f in audit_result.findings],
            diff=diff_text,
            explanation=explanation,
            passed_audit=False  # will be verified by orchestrator
        )

        return PatchResult(
            task_id=audit_result.task_id,
            iteration=iteration,
            patched_code=patched_code,
            diff=diff_text,
            explanation=explanation
        )

    def _extract_code(self, response_text: str) -> str:
        pattern = r"```(?:python)?\s*([\s\S]*?)\s*```"
        match = re.search(pattern, response_text)
        if match:
            return match.group(1).strip()
        return response_text.strip()

    def _apply_heuristic_patches(
        self,
        code: str,
        findings: List[VulnerabilityFinding],
        similar_memories: List[Dict[str, Any]]
    ) -> tuple[str, List[str]]:
        """Deterministic heuristic fallback when LLM patch drifts or has syntax errors."""
        patched_code = code
        applied_fixes = []
        rag_context = f" (Guided by memory {similar_memories[0]['id']})" if similar_memories else ""

        for finding in findings:
            if finding.cwe_id == "CWE-89":
                # Pattern A: execute(f"SELECT... {var}")
                new_code = re.sub(
                    r'execute\s*\(\s*f["\'](SELECT.*?WHERE\s+\w+\s*=\s*)\{([a-zA-Z0-9_]+)\}\s*["\']\s*\)',
                    r'execute("\1%s", (\2,))',
                    patched_code
                )
                # Pattern B: query = f"SELECT... {var}"
                if new_code == patched_code:
                    var_match = re.search(r'f["\']SELECT.*?WHERE\s+\w+\s*=\s*\{([a-zA-Z0-9_]+)\}', patched_code)
                    var_name = var_match.group(1) if var_match else "param"
                    new_code = re.sub(
                        r'([a-zA-Z0-9_]+\s*=\s*)f["\'](SELECT.*?WHERE\s+\w+\s*=\s*)\{([a-zA-Z0-9_]+)\}\s*["\']',
                        r'\1"\2%s"',
                        patched_code
                    )
                    if new_code != patched_code:
                        new_code = re.sub(
                            r'execute\s*\(\s*([a-zA-Z0-9_]+)\s*\)',
                            rf'execute(\1, ({var_name},))',
                            new_code
                        )
                if new_code != patched_code:
                    patched_code = new_code
                    applied_fixes.append(f"Parametrized SQL query for {finding.cwe_id}{rag_context}")

            elif finding.cwe_id == "CWE-78":
                new_code = re.sub(
                    r'os\.system\s*\((.*?)\)',
                    r'subprocess.run([\1], check=True)',
                    patched_code
                )
                if new_code != patched_code:
                    if "import subprocess" not in new_code:
                        new_code = "import subprocess\n" + new_code
                    patched_code = new_code
                    applied_fixes.append(f"Replaced os.system with subprocess.run{rag_context}")

            elif finding.cwe_id == "CWE-95":
                if "eval(" in patched_code:
                    new_code = patched_code.replace("eval(", "ast.literal_eval(")
                    if "import ast" not in new_code:
                        new_code = "import ast\n" + new_code
                    patched_code = new_code
                    applied_fixes.append(f"Replaced eval() with ast.literal_eval(){rag_context}")

            elif finding.cwe_id == "CWE-943":  # MERN NoSQLi
                new_code = re.sub(r'\.find\s*\(\s*req\.body\s*\)', '.find(mongoSanitize(req.body))', patched_code)
                if new_code != patched_code:
                    if "mongoSanitize" not in new_code:
                        new_code = "const mongoSanitize = require('mongo-sanitize');\n" + new_code
                    patched_code = new_code
                    applied_fixes.append("Sanitized MongoDB req.body query parameters with mongo-sanitize")

            elif finding.cwe_id == "CWE-79":   # XSS
                new_code = re.sub(r'dangerouslySetInnerHTML=\{\{\s*__html:\s*([^\}]+)\s*\}\}', r'dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(\1) }}', patched_code)
                if new_code != patched_code:
                    if "DOMPurify" not in new_code:
                        new_code = "import DOMPurify from 'dompurify';\n" + new_code
                    patched_code = new_code
                    applied_fixes.append("Sanitized HTML injection via DOMPurify.sanitize()")

            elif finding.cwe_id == "CWE-942":  # CORS
                new_code = re.sub(r'origin\s*:\s*["\']\*["\']', "origin: ['http://localhost:3000']", patched_code)
                if new_code != patched_code:
                    patched_code = new_code
                    applied_fixes.append("Restricted wildcard CORS policy to authorized origins")

            elif finding.cwe_id == "CWE-798":  # Hardcoded Secrets
                new_code = re.sub(r'jwt\.sign\s*\(([^,]+),\s*["\'][^"\']+["\']', r'jwt.sign(\1, process.env.JWT_SECRET || "default_secure_secret"', patched_code)
                if new_code != patched_code:
                    patched_code = new_code
                    applied_fixes.append("Replaced hardcoded JWT secret with process.env.JWT_SECRET")

            elif finding.cwe_id == "CWE-926":  # Android exported component
                new_code = re.sub(r'android:exported=["\']true["\']', 'android:exported="false"', patched_code)
                if new_code != patched_code:
                    patched_code = new_code
                    applied_fixes.append("Set android:exported='false' for unprotected internal components")

            elif finding.cwe_id == "CWE-319":  # Cleartext traffic
                new_code = re.sub(r'android:usesCleartextTraffic=["\']true["\']', 'android:usesCleartextTraffic="false"', patched_code)
                if new_code != patched_code:
                    patched_code = new_code
                    applied_fixes.append("Enforced TLS by setting android:usesCleartextTraffic='false'")

        return patched_code, applied_fixes
