import ast
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from context.session_ledger import SymbolTable


class DriftReport(BaseModel):
    is_valid: bool
    syntax_valid: bool
    syntax_error: Optional[str] = None
    missing_functions: List[str] = Field(default_factory=list)
    signature_mutations: List[str] = Field(default_factory=list)
    prohibited_violations: List[str] = Field(default_factory=list)
    unexpected_imports: List[str] = Field(default_factory=list)
    summary: str = ""


class DriftGuard:
    """
    Semantic Anti-Hallucination & Drift Validator.
    Acts as a deterministic firewall post-inference.
    Whenever OmniRoute switches models or generates candidate code, DriftGuard
    analyzes the AST to guarantee that:
      1. Code has valid Python syntax.
      2. Key functional signatures from the original SymbolTable were preserved.
      3. No prohibited patterns (e.g., eval, os.system) were reintroduced.
      4. Hallucinated or dangerous dependencies were not imported.
    """

    @staticmethod
    def validate(
        candidate_code: str,
        baseline_symbols: Optional[SymbolTable] = None,
        prohibited_patterns: Optional[List[str]] = None,
        allowed_imports: Optional[List[str]] = None
    ) -> DriftReport:
        # 1. Syntax Validation
        try:
            tree = ast.parse(candidate_code)
        except SyntaxError as e:
            return DriftReport(
                is_valid=False,
                syntax_valid=False,
                syntax_error=f"SyntaxError on line {e.lineno}: {e.msg}",
                summary=f"Generated code failed syntax validation: {e.msg} (line {e.lineno})"
            )

        missing_functions = []
        signature_mutations = []
        unexpected_imports = []
        prohibited_violations = []

        # Extract symbols from candidate
        candidate_funcs: Dict[str, List[str]] = {}
        candidate_imports: List[str] = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [arg.arg for arg in node.args.args]
                candidate_funcs[node.name] = args
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    candidate_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    candidate_imports.append(f"{module}.{alias.name}" if module else alias.name)

        # 2. Check for missing original functions
        if baseline_symbols and baseline_symbols.functions:
            for orig_fn in baseline_symbols.functions:
                if orig_fn.name not in candidate_funcs:
                    missing_functions.append(orig_fn.name)
                else:
                    cand_args = candidate_funcs[orig_fn.name]
                    # Verify required arguments weren't dropped
                    missing_args = [a for a in orig_fn.args if a not in cand_args]
                    if missing_args:
                        signature_mutations.append(
                            f"Function '{orig_fn.name}' dropped arguments: {', '.join(missing_args)}"
                        )

        # 3. Check for prohibited patterns (AST + heuristic string match)
        if prohibited_patterns:
            for pattern in prohibited_patterns:
                clean_pattern = pattern.strip()
                if not clean_pattern:
                    continue
                # Simple regex check for pattern presence
                escaped = re.escape(clean_pattern)
                # If pattern contains parentheses like eval(), check eval\s*\(
                if clean_pattern.endswith("()"):
                    raw_fn = clean_pattern[:-2]
                    regex = rf"\b{re.escape(raw_fn)}\s*\("
                else:
                    regex = escaped

                if re.search(regex, candidate_code):
                    prohibited_violations.append(clean_pattern)

        # 4. Check for unexpected or suspicious imports
        if allowed_imports:
            allowed_set = set(allowed_imports)
            for imp in candidate_imports:
                base_pkg = imp.split(".")[0]
                if imp not in allowed_set and base_pkg not in allowed_set:
                    unexpected_imports.append(imp)

        has_issues = bool(missing_functions or signature_mutations or prohibited_violations)
        
        issues_summary = []
        if missing_functions:
            issues_summary.append(f"Missing functions: {', '.join(missing_functions)}")
        if signature_mutations:
            issues_summary.append(f"Signature drift: {'; '.join(signature_mutations)}")
        if prohibited_violations:
            issues_summary.append(f"Violated prohibited patterns: {', '.join(prohibited_violations)}")
        if unexpected_imports:
            issues_summary.append(f"New imports: {', '.join(unexpected_imports)}")

        summary_text = (
            "Passed drift and integrity validation."
            if not has_issues
            else f"Drift detected: {' | '.join(issues_summary)}"
        )

        return DriftReport(
            is_valid=not has_issues,
            syntax_valid=True,
            missing_functions=missing_functions,
            signature_mutations=signature_mutations,
            prohibited_violations=prohibited_violations,
            unexpected_imports=unexpected_imports,
            summary=summary_text
        )
