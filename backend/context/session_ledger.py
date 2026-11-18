import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from context.polyglot_ast import (
    SymbolDefinition,
    RouteDefinition,
    DatabaseModelDefinition,
    CrossFileImport,
    SymbolTable,
    PolyglotASTEngine,
)


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
    Stateful, model-agnostic Polyglot Session Ledger.
    Maintains the canonical state of a remediation task outside of individual LLM contexts.
    Features:
      - Polyglot SymbolTable parsing for Python, JS/TS, Java, Kotlin, and Android XML.
      - In-memory cross-file dependency graph tracking 1-hop imports.
      - Architectural invariants & prohibited patterns preservation.
      - Historical remediation attempts and RAG memories.
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

        # Multi-file dependency graph
        self.file_symbols: Dict[str, SymbolTable] = {}
        self.dependency_graph: Dict[str, List[str]] = {}

        if initial_code:
            self.refresh_symbols(initial_code, filename=self.filename)

    def set_architect_boundaries(
        self,
        invariants: List[str],
        prohibited_patterns: Optional[List[str]] = None
    ) -> None:
        """Establish immutable security invariants from the Architect Agent."""
        self.architect_invariants = list(invariants)
        if prohibited_patterns:
            self.prohibited_patterns = list(prohibited_patterns)

    def refresh_symbols(self, code: str, filename: Optional[str] = None) -> SymbolTable:
        """
        Parses source code into a structured polyglot SymbolTable.
        Tracks all imports, classes, functions, arguments, routes, and models.
        """
        target_file = filename or self.filename
        self.symbol_table = PolyglotASTEngine.parse(code, filename=target_file)
        self.file_symbols[target_file] = self.symbol_table
        self._rebuild_dependency_graph()
        return self.symbol_table

    def register_file(self, path: str, code: str) -> SymbolTable:
        """Registers or updates a file in the multi-file ledger workspace."""
        table = PolyglotASTEngine.parse(code, filename=path)
        self.file_symbols[path] = table
        if path == self.filename:
            self.symbol_table = table
            self.active_code = code
        self._rebuild_dependency_graph()
        return table

    def _rebuild_dependency_graph(self) -> None:
        """
        Constructs the directed dependency graph across all registered files.
        Maps each file to the exact list of internal files it imports.
        """
        known_files = list(self.file_symbols.keys())
        new_graph: Dict[str, List[str]] = {}

        for file_path, table in self.file_symbols.items():
            deps: List[str] = []
            dir_name = os.path.dirname(file_path).replace("\\", "/")

            # Check cross-file imports
            for imp in table.cross_file_imports:
                raw_src = imp.source_path.replace("\\", "/")

                # 1. Direct path match
                if raw_src in known_files and raw_src != file_path:
                    deps.append(raw_src)
                    continue

                # 2. Relative resolution: e.g. ./utils -> dir_name/utils[.js/.ts/.py]
                if imp.is_relative or raw_src.startswith("."):
                    resolved = os.path.normpath(os.path.join(dir_name, raw_src)).replace("\\", "/")
                    match = self._find_matching_file(resolved, known_files)
                    if match and match != file_path:
                        deps.append(match)
                        continue

                # 3. Module / Package resolution (e.g. Java/Kotlin package com.example.service.UserService)
                match = self._find_matching_file(raw_src, known_files)
                if match and match != file_path:
                    deps.append(match)

            new_graph[file_path] = list(dict.fromkeys(deps))

        self.dependency_graph = new_graph

    def _find_matching_file(self, candidate_path: str, known_files: List[str]) -> Optional[str]:
        """Finds matching known file path taking file extensions into account."""
        norm_candidate = candidate_path.replace("\\", "/")
        extensions = ["", ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".kt"]
        for ext in extensions:
            test_path = norm_candidate + ext
            if test_path in known_files:
                return test_path
            # Also check base name matches for Java/Kotlin packages
            base_name = os.path.basename(test_path)
            for k in known_files:
                if os.path.basename(k) == base_name or k.endswith("/" + test_path):
                    return k
        return None

    def get_1_hop_imported_symbols(self, file_path: Optional[str] = None) -> Dict[str, SymbolTable]:
        """
        Returns the exact SymbolTables of all 1-hop dependencies imported by the specified file.
        This provides ContextNormalizer with exact signatures, eliminating cross-file hallucinations.
        """
        target = file_path or self.filename
        deps = self.dependency_graph.get(target, [])
        result: Dict[str, SymbolTable] = {}

        for dep in deps:
            if dep in self.file_symbols:
                result[dep] = self.file_symbols[dep]

        # If no registered internal files match yet, synthesize 1-hop signatures from CrossFileImports
        if not result and target in self.file_symbols:
            current_table = self.file_symbols[target]
            for imp in current_table.cross_file_imports:
                if imp.imported_symbols:
                    synthetic_funcs = [
                        SymbolDefinition(name=sym, symbol_type="function", args=[], file_path=imp.source_path)
                        for sym in imp.imported_symbols
                    ]
                    result[imp.source_path] = SymbolTable(
                        imports=[imp.source_path],
                        functions=synthetic_funcs,
                        classes=[]
                    )

        return result

    def update_active_code(self, new_code: str) -> None:
        """Updates the active working code and re-indexes AST symbols."""
        self.active_code = new_code
        self.refresh_symbols(new_code, filename=self.filename)

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
            "model_history": self.model_history,
            "file_symbols": {k: v.model_dump() for k, v in self.file_symbols.items()},
            "dependency_graph": self.dependency_graph
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

        if "file_symbols" in data:
            ledger.file_symbols = {k: SymbolTable(**v) for k, v in data["file_symbols"].items()}
        if "dependency_graph" in data:
            ledger.dependency_graph = data["dependency_graph"]

        return ledger
