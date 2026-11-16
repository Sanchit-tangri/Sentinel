import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from context.session_ledger import SessionLedger
from context.normalizer import ContextNormalizer
from context.drift_guard import DriftGuard
from routing.omniroute_client import OmniRouteClient, ModelTier
from agents.developer.agent import DeveloperAgent
from agents.auditor.agent import AuditorAgent
from agents.patcher.agent import PatcherAgent
from agents.orchestrator.orchestrator import RemediationOrchestrator
from rag.memory_store import MemoryStore


def test_session_ledger_ast_extraction():
    sample_code = """import os
import subprocess
from datetime import datetime

GLOBAL_CONFIG = {"debug": False}

class UserManager:
    def __init__(self, db_conn):
        self.db = db_conn

    def fetch_user(self, user_id):
        pass

def process_order(order_id: int, user_email: str):
    return {"order": order_id, "email": user_email}
"""
    ledger = SessionLedger(filename="test_sample.py", initial_code=sample_code)
    symbols = ledger.symbol_table

    assert "os" in symbols.imports
    assert "subprocess" in symbols.imports
    assert any(f.name == "process_order" for f in symbols.functions)
    
    order_fn = next(f for f in symbols.functions if f.name == "process_order")
    assert "order_id" in order_fn.args
    assert "user_email" in order_fn.args

    assert any(c.name == "UserManager" for c in symbols.classes)
    user_mgr = next(c for c in symbols.classes if c.name == "UserManager")
    assert "fetch_user" in user_mgr.args

    # Test serialization round-trip
    data = ledger.to_dict()
    restored = SessionLedger.from_dict(data)
    assert restored.session_id == ledger.session_id
    assert len(restored.symbol_table.functions) == len(ledger.symbol_table.functions)
    print("PASS: test_session_ledger_ast_extraction")


def test_context_normalizer():
    sample_code = "def handle_request(req): pass"
    ledger = SessionLedger(initial_code=sample_code)
    ledger.set_architect_boundaries(
        invariants=["All inputs must be typed and validated."],
        prohibited_patterns=["eval()", "os.system()"]
    )
    ledger.record_rag_memories([{"id": "mem-101", "document": "Use parameterized queries for SQL."}])

    dev_prompt = ContextNormalizer.build_developer_prompt("Build user auth endpoint", ledger)
    assert "<sentinel_context>" in dev_prompt
    assert "<invariant>All inputs must be typed and validated.</invariant>" in dev_prompt
    assert "<pattern>eval()</pattern>" in dev_prompt
    assert "mem-101" in dev_prompt

    findings = [{"cwe_id": "CWE-89", "title": "SQLi", "line_number": 2, "snippet": "exec()", "recommendation": "fix"}]
    patch_prompt = ContextNormalizer.build_patcher_prompt(sample_code, findings, ledger, iteration=1)
    assert "<sentinel_patch_context" in patch_prompt
    assert "CWE-89" in patch_prompt
    print("PASS: test_context_normalizer")


def test_drift_guard():
    # 1. Syntax Error Detection
    broken_code = "def foo(a: return a +"
    report = DriftGuard.validate(broken_code)
    assert not report.is_valid
    assert not report.syntax_valid
    assert "SyntaxError" in (report.syntax_error or "")

    # 2. Missing Function / Signature Mutation
    baseline_code = "def authenticate_user(username: str, token: str): pass"
    baseline_ledger = SessionLedger(initial_code=baseline_code)

    mutated_code = "def completely_different_function(data): pass"
    report_mutated = DriftGuard.validate(mutated_code, baseline_symbols=baseline_ledger.symbol_table)
    assert not report_mutated.is_valid
    assert "authenticate_user" in report_mutated.missing_functions

    # 3. Prohibited Pattern Detection
    prohibited_code = """def run_cmd(x):
    eval(x)
    return True
"""
    report_prohibited = DriftGuard.validate(prohibited_code, prohibited_patterns=["eval()", "os.system()"])
    assert not report_prohibited.is_valid
    assert "eval()" in report_prohibited.prohibited_violations

    # 4. Clean Valid Code
    clean_code = """def authenticate_user(username: str, token: str):
    if not username or not token:
        raise ValueError("Invalid parameters")
    return True
"""
    report_clean = DriftGuard.validate(clean_code, baseline_symbols=baseline_ledger.symbol_table, prohibited_patterns=["eval()"])
    assert report_clean.is_valid
    assert report_clean.syntax_valid
    print("PASS: test_drift_guard")


def test_omniroute_routing_and_model_switching():
    client = OmniRouteClient(force_simulation=True)
    ledger = SessionLedger(initial_code="def query(user_id): pass")

    # Call 1: Strategic Tier
    res1 = client.generate("Plan security boundary", tier=ModelTier.STRATEGIC)
    assert res1.success
    assert res1.model_used is not None
    ledger.record_model_switch(res1.model_used)

    # Call 2: Code Gen Tier (Simulate model switch)
    res2 = client.generate("Generate SQL query handler", tier=ModelTier.CODE_GEN)
    assert res2.success
    switched = ledger.record_model_switch(res2.model_used)
    
    # Model switch should be detected and tracked
    assert len(ledger.model_history) > 0 or switched
    assert ledger.active_model == res2.model_used
    print(f"PASS: test_omniroute_routing_and_model_switching (Switched: {ledger.model_history} -> {ledger.active_model})")


def test_developer_agent_synthesis():
    developer = DeveloperAgent()
    ledger = SessionLedger(initial_code="")
    
    result = developer.implement(
        task_prompt="Create a database lookup function for user profile by id",
        session_ledger=ledger
    )
    assert "def " in result["code"]
    assert result["drift_report"]["is_valid"]
    assert ledger.active_model == result["model_used"]
    print("PASS: test_developer_agent_synthesis")


def test_complete_remediation_orchestrator_loop():
    vulnerable_sql_code = """def get_user_profile(user_id: int, db_connection):
    cursor = db_connection.cursor()
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()
"""
    # Verify Auditor flags SQLi
    auditor = AuditorAgent()
    initial_audit = auditor.audit_code(vulnerable_sql_code)
    assert not initial_audit.is_secure
    assert any(f.cwe_id == "CWE-89" for f in initial_audit.findings)

    # Run complete remediation loop
    memory_store = MemoryStore()
    orchestrator = RemediationOrchestrator(memory_store=memory_store)
    result = orchestrator.remediate_code(vulnerable_sql_code, filename="vulnerable_user.py")

    assert result["is_secure"]
    assert result["total_iterations"] >= 1
    assert "diff" in result["history"][0] or "patch_diff" in result["history"][0]
    assert "SELECT" in result["final_code"]
    
    # Verify memory store received the verified fix
    memories = memory_store.search_similar_remediations("CWE-89 SQL injection", top_k=1)
    assert len(memories) > 0
    print("PASS: test_complete_remediation_orchestrator_loop (Remediated & Persisted to RAG)")


def test_project_manager_zip_flow():
    import io
    import zipfile
    from workspace.project_manager import ProjectManager

    manager = ProjectManager()
    
    # Create test zip in-memory with 2 vulnerable files
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w") as z:
        z.writestr("backend/api.py", "import os\nos.system('ping ' + host)")
        z.writestr("backend/db.py", "query = f'SELECT * FROM users WHERE id = {uid}'\ncursor.execute(query)")
        z.writestr("frontend/index.html", "<h1>My App</h1>")

    files = manager.extract_zip(zbuf.getvalue())
    assert len(files) == 3
    assert "backend/api.py" in files
    assert "frontend/index.html" in files

    workspace = manager.process_project(files, project_name="Test Zip App")
    assert workspace.total_files == 3
    assert workspace.vulnerable_files_count == 2
    assert workspace.remediated_count >= 2
    assert workspace.files["backend/api.py"].is_modified
    assert workspace.files["backend/db.py"].is_modified

    # Verify download zip creation
    clean_zip = manager.get_cached_zip(workspace.session_id)
    assert clean_zip is not None
    assert len(clean_zip) > 0
    print("PASS: test_project_manager_zip_flow (ZIP Extracted, Scanned, Remediated & Packaged)")


if __name__ == "__main__":
    print("=== Running Sentinel Context Remembrance & OmniRoute Test Suite ===")
    test_session_ledger_ast_extraction()
    test_context_normalizer()
    test_drift_guard()
    test_omniroute_routing_and_model_switching()
    test_developer_agent_synthesis()
    test_complete_remediation_orchestrator_loop()
    test_project_manager_zip_flow()
    print("=== ALL TESTS PASSED SUCCESSFULLY! ===")
