from typing import Dict, Any, List, Optional
from context.session_ledger import SessionLedger


class ContextNormalizer:
    """
    Context Normalizer & Envelope Generator.
    Serializes the state stored in SessionLedger and RAG memory into a standardized,
    model-agnostic prompt envelope.
    This guarantees that when OmniRoute routes or switches models, the destination
    LLM receives an identical, perfectly structured representation of:
      1. Security invariants & trust boundaries
      2. Scoped AST symbol tables (preventing hallucinated imports/functions)
      3. Past remediation history (preventing regression)
      4. RAG-retrieved lessons and proven patch diffs
    """

    @staticmethod
    def build_developer_prompt(
        task_prompt: str,
        ledger: SessionLedger,
        extra_guidelines: Optional[List[str]] = None
    ) -> str:
        """
        Builds a comprehensive context envelope for code generation tasks.
        """
        invariants_xml = "\n".join([f"    <invariant>{inv}</invariant>" for inv in ledger.architect_invariants]) or "    <invariant>Follow standard defensive programming practices.</invariant>"
        prohibited_xml = "\n".join([f"    <pattern>{pat}</pattern>" for pat in ledger.prohibited_patterns]) or "    <pattern>eval, exec, raw SQL string concatenation</pattern>"

        symbols = ledger.symbol_table
        funcs_repr = ", ".join([f"{f.name}({', '.join(f.args)})" for f in symbols.functions]) or "None"
        imports_repr = ", ".join(symbols.imports) or "Standard library only"
        classes_repr = ", ".join([f"{c.name}[methods: {', '.join(c.args)}]" for c in symbols.classes]) or "None"

        rag_snippets = []
        for idx, mem in enumerate(ledger.retrieved_rag_memories, 1):
            rag_snippets.append(
                f"    <memory id=\"{mem.get('id', idx)}\">\n"
                f"      <summary>{mem.get('document', '')}</summary>\n"
                f"    </memory>"
            )
        rag_xml = "\n".join(rag_snippets) if rag_snippets else "    <memory>No prior vulnerability history recorded for this pattern.</memory>"

        prompt = f"""<sentinel_context>
  <task_directive>
    You are the Developer Agent in the Sentinel Autonomous Security Framework.
    Generate clean, production-grade, defensible Python code fulfilling the task below.
  </task_directive>

  <task_prompt>
{task_prompt}
  </task_prompt>

  <architect_invariants>
{invariants_xml}
  </architect_invariants>

  <prohibited_patterns>
{prohibited_xml}
  </prohibited_patterns>

  <scoped_symbols>
    <imports>{imports_repr}</imports>
    <known_functions>{funcs_repr}</known_functions>
    <known_classes>{classes_repr}</known_classes>
  </scoped_symbols>

  <rag_remediation_memories>
{rag_xml}
  </rag_remediation_memories>

  <generation_instructions>
    1. Output ONLY executable Python code inside standard ```python ... ``` fences.
    2. Do NOT hallucinate third-party packages not in scoped imports unless strictly necessary.
    3. Respect every Architect Invariant without exception.
  </generation_instructions>
</sentinel_context>
"""
        return prompt

    @staticmethod
    def build_patcher_prompt(
        code: str,
        findings: List[Dict[str, Any]],
        ledger: SessionLedger,
        iteration: int
    ) -> str:
        """
        Builds a context-rich surgical patch prompt for the Patcher Agent.
        """
        invariants_xml = "\n".join([f"    <invariant>{inv}</invariant>" for inv in ledger.architect_invariants]) or "    <invariant>Preserve business logic while remediating vulnerabilities.</invariant>"

        findings_xml = []
        for f in findings:
            findings_xml.append(
                f"    <finding cwe=\"{f.get('cwe_id', 'UNKNOWN')}\" severity=\"{f.get('severity', 'HIGH')}\">\n"
                f"      <title>{f.get('title', '')}</title>\n"
                f"      <line>{f.get('line_number', '?')}</line>\n"
                f"      <snippet>{f.get('snippet', '')}</snippet>\n"
                f"      <recommendation>{f.get('recommendation', '')}</recommendation>\n"
                f"    </finding>"
            )
        findings_str = "\n".join(findings_xml)

        attempts_xml = []
        for att in ledger.attempts:
            attempts_xml.append(
                f"    <prior_attempt iteration=\"{att.iteration}\" model=\"{att.model_id}\">\n"
                f"      <explanation>{att.explanation}</explanation>\n"
                f"      <passed_audit>{att.passed_audit}</passed_audit>\n"
                f"    </prior_attempt>"
            )
        attempts_str = "\n".join(attempts_xml) if attempts_xml else "    <attempt>This is iteration 1. No prior attempts.</attempt>"

        rag_snippets = []
        for idx, mem in enumerate(ledger.retrieved_rag_memories, 1):
            rag_snippets.append(
                f"    <memory id=\"{mem.get('id', idx)}\">\n"
                f"      <solution>{mem.get('document', '')}</solution>\n"
                f"    </memory>"
            )
        rag_str = "\n".join(rag_snippets) if rag_snippets else "    <memory>No verified prior diffs retrieved.</memory>"

        symbols = ledger.symbol_table
        funcs_repr = ", ".join([f"{f.name}({', '.join(f.args)})" for f in symbols.functions]) or "None"

        prompt = f"""<sentinel_patch_context iteration="{iteration}">
  <directive>
    You are the Patcher Agent in Sentinel.
    Your objective is to surgically patch identified security vulnerabilities in the provided code.
    CRITICAL: Preserve existing functional business logic, function names, and argument signatures.
    Do NOT introduce regressions or hallucinate external dependencies.
  </directive>

  <active_vulnerabilities>
{findings_str}
  </active_vulnerabilities>

  <architect_invariants>
{invariants_xml}
  </architect_invariants>

  <existing_symbol_signatures>
    <functions>{funcs_repr}</functions>
    <valid_imports>{', '.join(symbols.imports) or 'standard library'}</valid_imports>
  </existing_symbol_signatures>

  <prior_attempts_in_session>
{attempts_str}
  </prior_attempts_in_session>

  <retrieved_rag_verified_solutions>
{rag_str}
  </retrieved_rag_verified_solutions>

  <target_source_code>
```python
{code}
```
  </target_source_code>

  <patch_instructions>
    1. Output the COMPLETE patched Python code enclosed inside ```python ... ``` fences.
    2. Follow with a brief 1-2 sentence explanation of changes.
    3. Ensure all vulnerable lines identified in <active_vulnerabilities> are sanitized.
  </patch_instructions>
</sentinel_patch_context>
"""
        return prompt
