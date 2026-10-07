import re
from typing import List
from schemas.models import AuditResult, VulnerabilityFinding, SeverityLevel

class AuditorAgent:
    """
    Auditor Agent (Verification Layer).
    Employs static analysis heuristics and OWASP/CWE pattern matchers
    to detect critical security vulnerabilities in code.
    """
    def __init__(self, name: str = "The Auditor"):
        self.name = name

    def audit_code(self, code: str, filename: str = "snippet.py") -> AuditResult:
        findings: List[VulnerabilityFinding] = []
        lines = code.split("\n")

        # 1. SQL Injection Detection (OWASP A03 / CWE-89)
        sqli_patterns = [
            (r'execute\s*\(\s*["\'].*(SELECT|INSERT|UPDATE|DELETE).*["\']\s*%\s*\(?', "CWE-89", "Potential SQL Injection via % string formatting", SeverityLevel.CRITICAL),
            (r'execute\s*\(\s*f["\'].*(SELECT|INSERT|UPDATE|DELETE).*\{', "CWE-89", "Critical SQL Injection via f-string interpolation", SeverityLevel.CRITICAL),
            (r'cursor\.execute\s*\(\s*["\'].*(SELECT|INSERT|UPDATE|DELETE).*\+\s*', "CWE-89", "SQL Injection via string concatenation", SeverityLevel.CRITICAL),
        ]

        # 2. Command Injection (CWE-78)
        cmdi_patterns = [
            (r'os\.system\s*\(', "CWE-78", "Insecure os.system call susceptible to Command Injection", SeverityLevel.CRITICAL),
            (r'subprocess\.(call|Popen|run)\s*\(.*shell\s*=\s*True', "CWE-78", "Subprocess execution with shell=True", SeverityLevel.HIGH),
        ]

        # 3. Insecure Deserialization / Execution (CWE-95 / CWE-502)
        exec_patterns = [
            (r'\beval\s*\(', "CWE-95", "Dangerous eval() function call", SeverityLevel.CRITICAL),
            (r'\bexec\s*\(', "CWE-95", "Dangerous exec() function call", SeverityLevel.CRITICAL),
            (r'pickle\.loads?\s*\(', "CWE-502", "Unsafe deserialization using pickle", SeverityLevel.HIGH),
        ]

        # 4. Hardcoded Secrets (CWE-798)
        secret_patterns = [
            (r'(?i)(password|secret|api_key|token)\s*=\s*["\'][a-zA-Z0-9_\-]{8,}["\']', "CWE-798", "Hardcoded credential/secret detected", SeverityLevel.HIGH),
        ]

        all_rules = sqli_patterns + cmdi_patterns + exec_patterns + secret_patterns

        for line_idx, line in enumerate(lines, 1):
            for pattern, cwe, title, severity in all_rules:
                if re.search(pattern, line):
                    finding_id = f"VULN-{cwe}-{line_idx}"
                    findings.append(
                        VulnerabilityFinding(
                            id=finding_id,
                            cwe_id=cwe,
                            title=title,
                            description=f"Pattern '{pattern}' matched on line {line_idx}.",
                            severity=severity,
                            file_path=filename,
                            line_number=line_idx,
                            snippet=line.strip(),
                            recommendation="Sanitize user inputs and employ parameterized or safe standard library APIs."
                        )
                    )

        is_secure = len(findings) == 0
        summary = (
            "Code passed security audit with 0 findings."
            if is_secure
            else f"Audit detected {len(findings)} vulnerability issue(s)."
        )

        return AuditResult(
            task_id="audit-" + filename,
            is_secure=is_secure,
            findings=findings,
            summary=summary
        )
