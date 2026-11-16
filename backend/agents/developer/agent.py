import re
import logging
from typing import Optional, Dict, Any
from schemas.models import ArchitectSpecification
from routing.omniroute_client import OmniRouteClient, ModelTier, GenerationResult
from context.session_ledger import SessionLedger
from context.normalizer import ContextNormalizer
from context.drift_guard import DriftGuard, DriftReport

logger = logging.getLogger("Sentinel.DeveloperAgent")


class DeveloperAgent:
    """
    Developer Agent (Implementation Layer).
    Generates production-grade, defensive code implementations satisfying
    architectural security invariants.
    Integrates with OmniRoute for dynamic multi-model code generation and
    the Context Remembrance Engine to prevent hallucination during model transitions.
    """

    def __init__(
        self,
        name: str = "The Developer",
        omniroute_client: Optional[OmniRouteClient] = None
    ):
        self.name = name
        self.client = omniroute_client or OmniRouteClient()

    def implement(
        self,
        task_prompt: str,
        spec: Optional[ArchitectSpecification] = None,
        session_ledger: Optional[SessionLedger] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes defensive code using OmniRoute.
        Preserves context continuity and validates against AST drift.
        """
        ledger = session_ledger or SessionLedger(initial_code="", filename="generated_module.py")

        # Synchronize architect specification with the ledger
        if spec:
            ledger.set_architect_boundaries(
                invariants=spec.security_invariants,
                prohibited_patterns=spec.prohibited_patterns
            )

        # Build normalized model-agnostic prompt envelope
        prompt = ContextNormalizer.build_developer_prompt(
            task_prompt=task_prompt,
            ledger=ledger
        )

        # Dispatch to OmniRoute Code Generation Tier
        gen_result: GenerationResult = self.client.generate(
            prompt=prompt,
            system_prompt=(
                "You are an elite, defensive security software engineer. "
                "Write clean, resilient Python code adhering strictly to all security invariants."
            ),
            tier=ModelTier.CODE_GEN
        )

        # Track model switch in the session ledger
        was_switched = ledger.record_model_switch(gen_result.model_used)
        if was_switched:
            logger.info(
                f"[DeveloperAgent] OmniRoute model switched to '{gen_result.model_used}'. "
                f"Context Remembrance active."
            )

        # Extract code from response
        extracted_code = self._extract_code(gen_result.content)

        # Anti-Drift and Semantic Integrity Check
        drift_report: DriftReport = DriftGuard.validate(
            candidate_code=extracted_code,
            baseline_symbols=ledger.symbol_table if ledger.symbol_table.functions else None,
            prohibited_patterns=ledger.prohibited_patterns
        )

        # Update ledger with generated code
        ledger.update_active_code(extracted_code)

        return {
            "code": extracted_code,
            "raw_response": gen_result.content,
            "sandbox_html": gen_result.sandbox_html,
            "model_used": gen_result.model_used,
            "tier": gen_result.tier.value,
            "latency_ms": gen_result.latency_ms,
            "switched_model": gen_result.switched_model or was_switched,
            "drift_report": drift_report.model_dump(),
            "session_id": ledger.session_id
        }

    def _extract_code(self, response_text: str) -> str:
        """Extracts python code from markdown block or returns raw string."""
        pattern = r"```(?:python)?\s*([\s\S]*?)\s*```"
        match = re.search(pattern, response_text)
        if match:
            return match.group(1).strip()
        return response_text.strip()
