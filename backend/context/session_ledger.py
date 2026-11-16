import ast
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SymbolDefinition(BaseModel):
    name: str
    symbol_type: str  # "function", "async_function", "class", "import", "variable"
    args: List[str] = Field(default_factory=list)
    line_number: int = 0
    docstring: Optional[str] = None


class SymbolTable(BaseModel):
    imports: List[str] = Field(default_factory=list)
    functions: List[SymbolDefinition] = Field(default_factory=list)
    classes: List[SymbolDefinition] = Field(default_factory=list)
    global_variables: List[str] = Field(default_factory=list)


class RemediationAttempt(BaseModel):
    iteration: int
    model_id: str
    findings_addressed: List[str] = Field(default_factory=list)
    diff: str = ""
    explanation: str = ""
    passed_audit: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class SessionLedger:
    """
    Stateful, model-agnostic Session Ledger.
    Maintains the canonical state of a remediation task outside of individual LLM contexts.
    Ensures that when OmniRoute dynamically switches models mid-task, all critical
    architectural invariants, code AST symbols, historical attempts, and RAG memories
    are preserved without degradation.
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        filename: str = "snippet.py",
        initial_code: str = ""
    ):
        self.session_id: str = session_id or f"sess-{uuid.uuid4().hex[:10]}"
        self.filename: str = filename
        self.initial_code: str = initial_code
        self.active_code: str = initial_code
        self.architect_invariants: List[str] = []
        self.prohibited_patterns: List[str] = []
        self.symbol_table: SymbolTable = SymbolTable()
        self.attempts: List[RemediationAttempt] = []
        self.retrieved_rag_memories: List[Dict[str, Any]] = []
        self.active_model: Optional[str] = None
        self.model_history: List[str] = []

        if initial_code:
            self.refresh_symbols(initial_code)

    def set_architect_boundaries(
        self,
        invariants: List[str],
        prohibited_patterns: Optional[List[str]] = None
    ) -> None:
        """Establish immutable security invariants from the Architect Agent."""
        self.architect_invariants = list(invariants)
        if prohibited_patterns:
            self.prohibited_patterns = list(prohibited_patterns)

    def refresh_symbols(self, code: str) -> SymbolTable:
        """
        Parses source code AST into a structured SymbolTable.
        Tracks all imports, classes, functions, and arguments to prevent
        hallucinated or vanished symbols during model switches.
        """
        imports = []
        functions = []
        classes = []
        variables = []

        try:
            tree = ast.parse(code)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}" if module else alias.name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [arg.arg for arg in node.args.args]
                    docstring = ast.get_docstring(node)
                    functions.append(
                        SymbolDefinition(
                            name=node.name,
                            symbol_type="async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
                            args=args,
                            line_number=node.lineno,
                            docstring=docstring
                        )
                    )
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    classes.append(
                        SymbolDefinition(
                            name=node.name,
                            symbol_type="class",
                            args=methods,
                            line_number=node.lineno,
                            docstring=ast.get_docstring(node)
                        )
                    )
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables.append(target.id)
        except SyntaxError:
            # Code may have momentary syntax invalidity during intermediate generation
            pass

        self.symbol_table = SymbolTable(
            imports=list(set(imports)),
            functions=functions,
            classes=classes,
            global_variables=list(set(variables))
        )
        return self.symbol_table

    def update_active_code(self, new_code: str) -> None:
        """Updates the active working code and re-indexes AST symbols."""
        self.active_code = new_code
        self.refresh_symbols(new_code)

    def record_model_switch(self, new_model_id: str) -> bool:
        """
        Logs a model transition made by OmniRoute.
        Returns True if this is a model switch from a previous model.
        """
        is_switch = self.active_model is not None and self.active_model != new_model_id
        if is_switch:
            self.model_history.append(self.active_model)
        self.active_model = new_model_id
        return is_switch

    def record_attempt(
        self,
        iteration: int,
        model_id: str,
        findings_addressed: List[str],
        diff: str,
        explanation: str,
        passed_audit: bool
    ) -> RemediationAttempt:
        """Record an attempted remediation step in the session ledger."""
        attempt = RemediationAttempt(
            iteration=iteration,
            model_id=model_id,
            findings_addressed=findings_addressed,
            diff=diff,
            explanation=explanation,
            passed_audit=passed_audit
        )
        self.attempts.append(attempt)
        return attempt

    def record_rag_memories(self, memories: List[Dict[str, Any]]) -> None:
        """Persist retrieved RAG memories for context continuity."""
        self.retrieved_rag_memories = memories

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the complete session state to a dictionary."""
        return {
            "session_id": self.session_id,
            "filename": self.filename,
            "initial_code": self.initial_code,
            "active_code": self.active_code,
            "architect_invariants": self.architect_invariants,
            "prohibited_patterns": self.prohibited_patterns,
            "symbol_table": self.symbol_table.model_dump(),
            "attempts": [a.model_dump() for a in self.attempts],
            "retrieved_rag_memories": self.retrieved_rag_memories,
            "active_model": self.active_model,
            "model_history": self.model_history
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionLedger":
        """Reconstructs a SessionLedger from serialized dictionary."""
        ledger = cls(
            session_id=data.get("session_id"),
            filename=data.get("filename", "snippet.py"),
            initial_code=data.get("initial_code", "")
        )
        ledger.active_code = data.get("active_code", "")
        ledger.architect_invariants = data.get("architect_invariants", [])
        ledger.prohibited_patterns = data.get("prohibited_patterns", [])
        if "symbol_table" in data:
            ledger.symbol_table = SymbolTable(**data["symbol_table"])
        ledger.attempts = [RemediationAttempt(**a) for a in data.get("attempts", [])]
        ledger.retrieved_rag_memories = data.get("retrieved_rag_memories", [])
        ledger.active_model = data.get("active_model")
        ledger.model_history = data.get("model_history", [])
        return ledger
