from typing import Dict, Any, List, Optional
from context.session_ledger import SessionLedger


class ContextNormalizer:
    """
    Context Normalizer & Envelope Generator.
    Serializes the state stored in SessionLedger, multi-file dependency graph,
    and RAG memory into a standardized, model-agnostic prompt envelope.
    This guarantees that when OmniRoute routes or switches models, the destination
    LLM receives an identical, perfectly structured representation of:
      1. Security invariants & trust boundaries
      2. Scoped AST symbol tables (preventing hallucinated imports/functions)
      3. Exact signatures of all 1-hop imported files from the dependency graph
      4. Past remediation history (preventing regression)
      5. RAG-retrieved lessons and proven patch diffs
    """

    @staticmethod
    def _format_1_hop_dependencies(ledger: SessionLedger) -> str:
        """Formats 1-hop cross-file dependency signatures into structured XML."""
        one_hop_deps = ledger.get_1_hop_imported_symbols(ledger.filename)
        if not one_hop_deps:
            return "    <dependency>None</dependency>"

        xml_parts = []
        for dep_file, dep_table in one_hop_deps.items():
            funcs = ", ".join([f"{f.name}({', '.join(f.args)})" for f in dep_table.functions]) or "None"
            classes = ", ".join([f"{c.name}[methods: {', '.join(c.args)}]" for c in dep_table.classes]) or "None"
            routes = ", ".join([f"{r.method} {r.path}" for r in dep_table.routes]) or "None"
            models = ", ".join([m.name for m in dep_table.database_models]) or "None"
            xml_parts.append(
                f"    <dependency file=\"{dep_file}\">\n"
                f"      <functions>{funcs}</functions>\n"
                f"      <classes>{classes}</classes>\n"
                f"      <routes>{routes}</routes>\n"
                f"      <models>{models}</models>\n"
                f"    </dependency>"
            )
        return "\n".join(xml_parts)

    @classmethod
    def build_developer_prompt(
        cls,
        task_prompt: str,
        ledger: SessionLedger,
        extra_guidelines: Optional[List[str]] = None
    ) -> str:
        """
        Builds a comprehensive context envelope for code generation tasks.
        Includes 1-hop imported file signatures to eliminate cross-file hallucination.
        """
        invariants_xml = "\n".join([f"    <invariant>{inv}</invariant>" for inv in ledger.architect_invariants]) or "    <invariant>Follow standard defensive programming practices.</invariant>"
        prohibited_xml = "\n".join([f"    <pattern>{pat}</pattern>" for pat in ledger.prohibited_patterns]) or "    <pattern>eval, exec, raw SQL string concatenation</pattern>"

        symbols = ledger.symbol_table
        funcs_repr = ", ".join([f"{f.name}({', '.join(f.args)})" for f in symbols.functions]) or "None"
        imports_repr = ", ".join(symbols.imports) or "Standard library only"
        classes_repr = ", ".join([f"{c.name}[methods: {', '.join(c.args)}]" for c in symbols.classes]) or "None"
        one_hop_xml = cls._format_1_hop_dependencies(ledger)

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
    Generate clean, production-grade, defensible code fulfilling the task below.
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

  <one_hop_imported_dependencies>
{one_hop_xml}
  </one_hop_imported_dependencies>

  <rag_remediation_memories>
{rag_xml}
  </rag_remediation_memories>

  <generation_instructions>
    1. Output ONLY executable code inside standard markdown fences (e.g. ```python, ```javascript, ```java, etc.).
    2. Do NOT hallucinate third-party packages or symbols not in scoped imports or 1-hop dependencies.
    3. Respect every Architect Invariant without exception.
  </generation_instructions>
</sentinel_context>
"""
        return prompt

    @classmethod
    def build_patcher_prompt(
        cls,
        code: str,
        findings: List[Dict[str, Any]],
        ledger: SessionLedger,
        iteration: int
    ) -> str:
        """
        Builds a context-rich surgical patch prompt for the Patcher Agent.
        Injects verified 1-hop imported dependency signatures into the envelope.
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
                f"      <exploit_poc>{f.get('exploit_poc', 'N/A')}</exploit_poc>\n"
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
        one_hop_xml = cls._format_1_hop_dependencies(ledger)

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

  <one_hop_imported_dependencies>
{one_hop_xml}
  </one_hop_imported_dependencies>

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
    1. Output the COMPLETE patched code enclosed inside standard markdown code fences.
    2. Follow with a brief 1-2 sentence explanation of changes.
    3. Ensure all vulnerable lines identified in <active_vulnerabilities> are sanitized.
  </patch_instructions>
</sentinel_patch_context>
"""
        return prompt
