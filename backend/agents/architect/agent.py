from typing import Dict, Any, List
from schemas.models import ArchitectSpecification

class ArchitectAgent:
    """
    Architect Agent (Strategic Layer).
    Analyzes code or specifications to establish security boundaries, trust invariants,
    and anti-patterns before generation/patching proceeds.
    """
    def __init__(self, name: str = "The Architect"):
        self.name = name

    def analyze_boundaries(self, task_description: str, target_tech_stack: str = "python") -> ArchitectSpecification:
        invariants = [
            "All untrusted external user inputs must pass strict type/schema validation.",
            "Raw string concatenation in SQL or shell executions is strictly prohibited.",
            "Sensitive credentials and tokens must never be hardcoded in application logic."
        ]
        
        prohibited_patterns = [
            "eval()",
            "exec()",
            "os.system()",
            "subprocess.call(..., shell=True)",
            "SELECT * FROM ... WHERE id = " + "{user_input}"
        ]

        rules = [
            "Enforce parameterized queries or ORM sanitization.",
            "Enforce context-aware output encoding (XSS prevention).",
            "Require principle of least privilege for filesystem and database access."
        ]

        return ArchitectSpecification(
            task_id="task-initial",
            trust_boundaries=["User HTTP payload", "External database interface", "Filesystem writes"],
            security_invariants=invariants,
            input_validation_rules=rules,
            prohibited_patterns=prohibited_patterns
        )
