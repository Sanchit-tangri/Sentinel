import re
import os
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any, Tuple
from schemas.models import AuditResult, VulnerabilityFinding, SeverityLevel


class AuditorAgent:
    """
    Snooze - The Polyglot Security Auditor Agent.
    Scans codebases across MERN, Spring Boot Java, Android Kotlin/Java, and Python.
    Detects OWASP Top 10 and CWE vulnerabilities, generating conceptual exploit PoCs
    and multi-option architectural remediation strategies for Interactive Vibe Coding.
    """

    def __init__(self, name: str = "Snooze"):
        self.name = name

    def audit_code(
        self,
        code: str,
        filename: str = "snippet.py",
        security_level: str = "balanced"
    ) -> AuditResult:
        findings: List[VulnerabilityFinding] = []
        ext = os.path.splitext(filename)[1].lower()
        basename = os.path.basename(filename).lower()

        # 1. AndroidManifest.xml / XML analysis
        if basename == "androidmanifest.xml" or ext == ".xml":
            findings.extend(self._audit_android_xml(code, filename))

        # 2. MERN (JavaScript / TypeScript / React / Node / Mongo)
        if ext in [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]:
            findings.extend(self._audit_mern(code, filename))

        # 3. Spring Boot (Java)
        if ext in [".java", ".properties", ".yml", ".yaml"]:
            findings.extend(self._audit_spring_boot(code, filename))

        # 4. Android (Kotlin / Java)
        if ext in [".kt", ".kts", ".java"]:
            findings.extend(self._audit_android_code(code, filename))

        # 5. Python (Universal & existing CWE checks)
        if ext == ".py" or not findings:
            findings.extend(self._audit_python(code, filename))

        # Apply security_level filter
        # paranoid: all; balanced: CRITICAL, HIGH, MEDIUM; mvp: CRITICAL, HIGH
        if security_level == "mvp":
            findings = [f for f in findings if f.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)]
        elif security_level == "balanced":
            findings = [f for f in findings if f.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MEDIUM)]

        # Deduplicate findings by (cwe_id, line_number)
        seen = set()
        deduped: List[VulnerabilityFinding] = []
        for f in findings:
            key = (f.cwe_id, f.line_number, f.title)
            if key not in seen:
                seen.add(key)
                deduped.append(f)

        is_secure = len(deduped) == 0
        summary = (
            f"Code in {filename} passed security audit with 0 findings."
            if is_secure
            else f"Snooze detected {len(deduped)} vulnerability issue(s) across {filename}."
        )

        return AuditResult(
            task_id="audit-" + filename,
            is_secure=is_secure,
            findings=deduped,
            summary=summary
        )

    # -------------------------------------------------------------------------
    # Python Vulnerability Rules (CWE-89, CWE-78, CWE-95, CWE-502, CWE-798)
    # -------------------------------------------------------------------------
    def _audit_python(self, code: str, filename: str) -> List[VulnerabilityFinding]:
        findings: List[VulnerabilityFinding] = []
        lines = code.split("\n")

        sqli_patterns = [
            (r'f["\'].*(SELECT|INSERT|UPDATE|DELETE).*\{', "CWE-89", "Critical SQL Injection via f-string interpolation", SeverityLevel.CRITICAL,
             "Conceptual Exploit: An attacker passes SQL metacharacters (e.g. '1 OR 1=1') in string-interpolated query values, bypassing authentication or extracting database records.",
             [
                 "1. Use parameterized queries with db_connection.execute('SELECT ... WHERE id = %s', (user_id,)).",
                 "2. Use an ORM like SQLAlchemy or SQLModel with type-safe query expressions.",
                 "3. Enforce strict input type-casting (e.g. int(user_id)) before query construction."
             ]),
            (r'["\'].*(SELECT|INSERT|UPDATE|DELETE).*["\']\s*%\s*', "CWE-89", "Potential SQL Injection via % string formatting", SeverityLevel.CRITICAL,
             "Conceptual Exploit: Attacker injects raw SQL statements into unescaped % formatting parameters.",
             [
                 "1. Replace % formatting with database driver parameterized placeholders (e.g. '?' or '%s').",
                 "2. Utilize SQLAlchemy Core query builders.",
                 "3. Validate input parameters against strict allow-lists."
             ]),
            (r'["\'].*(SELECT|INSERT|UPDATE|DELETE).*\+\s*[a-zA-Z0-9_]', "CWE-89", "SQL Injection via string concatenation", SeverityLevel.CRITICAL,
             "Conceptual Exploit: Attacker appends arbitrary SQL commands to dynamically concatenated SQL strings.",
             [
                 "1. Use parameterized query execution with bound variables.",
                 "2. Migrate database queries to SQLAlchemy ORM models.",
                 "3. Implement input validation schemas using Pydantic."
             ]),
            (r'["\'].*(SELECT|INSERT|UPDATE|DELETE).*\.format\s*\(', "CWE-89", "SQL Injection via .format() interpolation", SeverityLevel.CRITICAL,
             "Conceptual Exploit: Attacker injects SQL payloads through .format() positional or keyword arguments.",
             [
                 "1. Use parameterized queries provided by the database driver.",
                 "2. Avoid string formatting for query assembly.",
                 "3. Use ORM filter expressions."
             ]),
        ]

        cmdi_patterns = [
            (r'os\.system\s*\(', "CWE-78", "Insecure os.system call susceptible to Command Injection", SeverityLevel.CRITICAL,
             "Conceptual Exploit: An attacker appends shell delimiters (e.g. '; rm -rf /') to user inputs, executing arbitrary OS commands.",
             [
                 "1. Replace os.system with subprocess.run(['cmd', arg], shell=False).",
                 "2. Use safe native Python library APIs (e.g. pathlib, shutil) instead of shell commands.",
                 "3. Sanitize inputs using shlex.quote() if shell execution cannot be avoided."
             ]),
            (r'subprocess\.(call|Popen|run)\s*\(.*shell\s*=\s*True', "CWE-78", "Subprocess execution with shell=True", SeverityLevel.HIGH,
             "Conceptual Exploit: Attacker passes command chaining operators (&, |, ;) to the invoked system shell.",
             [
                 "1. Set shell=False and pass arguments as an explicit tokenized list.",
                 "2. Restrict executable paths to a predefined allow-list.",
                 "3. Strip control characters from input arguments."
             ]),
        ]

        exec_patterns = [
            (r'\beval\s*\(', "CWE-95", "Dangerous eval() function call", SeverityLevel.CRITICAL,
             "Conceptual Exploit: Attacker passes Python code (e.g. \"__import__('os').system('id')\") evaluated directly by the Python runtime.",
             [
                 "1. Replace eval() with ast.literal_eval() for parsing safe literal data structures.",
                 "2. Use json.loads() or Pydantic schemas for data parsing.",
                 "3. Refactor logic to use dictionary dispatch tables."
             ]),
            (r'\bexec\s*\(', "CWE-95", "Dangerous exec() function call", SeverityLevel.CRITICAL,
             "Conceptual Exploit: Attacker injects multi-line Python statements executed with the permissions of the running process.",
             [
                 "1. Avoid dynamic Python code execution entirely.",
                 "2. Use predefined callable handlers or plugin architectures.",
                 "3. Sandbox execution in an isolated process if dynamic execution is necessary."
             ]),
            (r'pickle\.loads?\s*\(', "CWE-502", "Unsafe deserialization using pickle", SeverityLevel.HIGH,
             "Conceptual Exploit: Attacker crafts a serialized object with a malicious __reduce__ method that executes arbitrary code upon unpickling.",
             [
                 "1. Replace pickle with safe serialization formats like JSON, Protobuf, or MsgPack.",
                 "2. Cryptographically sign serialized payloads with HMAC-SHA256 before deserializing.",
                 "3. Implement an allow-listed custom Unpickler that overrides find_class."
             ]),
        ]

        secret_patterns = [
            (r'(?i)(password|secret|api_key|token)\s*=\s*["\'][a-zA-Z0-9_\-]{8,}["\']', "CWE-798", "Hardcoded credential/secret detected", SeverityLevel.HIGH,
             "Conceptual Exploit: An attacker reads the hardcoded secret from repository history and authenticates with unauthorized access.",
             [
                 "1. Move secret to an environment variable loaded via os.environ or python-dotenv.",
                 "2. Integrate a secrets manager (AWS Secrets Manager, HashiCorp Vault).",
                 "3. Add secret files to .gitignore and install pre-commit secret scanners."
             ]),
        ]

        all_rules = sqli_patterns + cmdi_patterns + exec_patterns + secret_patterns
        for line_idx, line in enumerate(lines, 1):
            for pattern, cwe, title, severity, exploit, fixes in all_rules:
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
                            recommendation="Sanitize user inputs and employ parameterized or safe standard library APIs.",
                            exploit_poc=exploit,
                            fix_options=fixes
                        )
                    )
        return findings

    # -------------------------------------------------------------------------
    # MERN Stack Vulnerability Rules (Node, Express, React, MongoDB)
    # -------------------------------------------------------------------------
    def _audit_mern(self, code: str, filename: str) -> List[VulnerabilityFinding]:
        findings: List[VulnerabilityFinding] = []
        lines = code.split("\n")

        # 1. NoSQL Operator Injection (CWE-943)
        nosql_patterns = [
            (r'\$where\s*:', "CWE-943", "MongoDB $where JavaScript evaluation injection", SeverityLevel.CRITICAL,
             "Conceptual Exploit: An attacker supplies arbitrary JavaScript inside the $where clause (e.g. \"this.password.match(/.*/)\"), bypassing authentication or locking the Mongo thread.",
             [
                 "1. Avoid $where operators completely; use standard BSON query selectors.",
                 "2. Sanitize incoming request objects using 'mongo-sanitize'.",
                 "3. Enforce strict Mongoose schema validation with explicit casting."
             ]),
            (r'\.(find|findOne|update|updateOne|updateMany|delete|deleteOne|deleteMany)\s*\(\s*(?:req\.body|req\.query)\b', "CWE-943", "Unsanitized req.body passed directly to MongoDB query", SeverityLevel.CRITICAL,
             "Conceptual Exploit: Attacker submits a JSON request with Mongo query operators (e.g. {\"password\": {\"$gt\": \"\"}}) to bypass authentication.",
             [
                 "1. Sanitize incoming request objects with 'mongo-sanitize' to strip $-prefixed keys.",
                 "2. Construct explicit query objects selecting only permitted fields (e.g. { username: req.body.username }).",
                 "3. Validate request payloads with Zod or Joi schemas before passing to database calls."
             ]),
            (r'\{[^\}]*(\$gt|\$ne|\$regex|\$or|\$nin)\s*:[^\}]*req\.(body|query|params)', "CWE-943", "Unchecked NoSQL operator injection in query filter", SeverityLevel.HIGH,
             "Conceptual Exploit: Attacker controls comparison operators to extract unintended records.",
             [
                 "1. Validate and cast input fields to expected types before querying.",
                 "2. Strip operator keys using middleware.",
                 "3. Use Mongoose typed model methods."
             ])
        ]

        # 2. XSS via dangerouslySetInnerHTML (CWE-79)
        xss_patterns = [
            (r'dangerouslySetInnerHTML\s*=\s*\{\s*\{\s*__html\s*:', "CWE-79", "Cross-Site Scripting (XSS) via dangerouslySetInnerHTML", SeverityLevel.HIGH,
             "Conceptual Exploit: An attacker injects malicious script tags via unsanitized user content, which executes in victim sessions.",
             [
                 "1. Sanitize raw HTML using DOMPurify.sanitize(content) before rendering.",
                 "2. Use standard JSX data binding which automatically HTML-escapes content.",
                 "3. Render rich text via safe Markdown parsers with strict sanitization plugins."
             ])
        ]

        # 3. JWT Secret Hardcoding (CWE-798)
        jwt_patterns = [
            (r'jwt\.(sign|verify)\s*\([^,]+,\s*["\'][^"\'\n]{3,}["\']', "CWE-798", "Hardcoded JSON Web Token (JWT) secret key", SeverityLevel.HIGH,
             "Conceptual Exploit: An attacker extracts the static secret from source code and forges valid authentication tokens with elevated claims.",
             [
                 "1. Load JWT secret from process.env.JWT_SECRET.",
                 "2. Store secrets in a centralized cloud secret manager.",
                 "3. Adopt asymmetric RS256/ES256 keypairs with public key verification."
             ])
        ]

        # 4. Missing Helmet / CORS Wildcard (CWE-942)
        cors_patterns = [
            (r'cors\s*\(\s*\{\s*origin\s*:\s*["\']\*["\']', "CWE-942", "Permissive CORS Wildcard Policy (origin: '*')", SeverityLevel.MEDIUM,
             "Conceptual Exploit: Any malicious website can initiate authenticated cross-origin requests and read sensitive response data.",
             [
                 "1. Specify an explicit whitelist of trusted origins in CORS configuration.",
                 "2. Add 'helmet()' middleware to enforce HTTP security headers.",
                 "3. Check the Origin header against authorized domain patterns."
             ]),
            (r'res\.setHeader\s*\(\s*["\']Access-Control-Allow-Origin["\']\s*,\s*["\']\*["\']', "CWE-942", "Access-Control-Allow-Origin wildcard header", SeverityLevel.MEDIUM,
             "Conceptual Exploit: Wildcard CORS allows untrusted origins to access API responses.",
             [
                 "1. Replace wildcard with the specific authorized origin.",
                 "2. Use express cors middleware with strict options.",
                 "3. Deny credentialed requests from wildcard origins."
             ])
        ]

        # 5. Prototype Pollution (CWE-1321)
        proto_patterns = [
            (r'__proto__', "CWE-1321", "Potential Prototype Pollution via __proto__ access", SeverityLevel.HIGH,
             "Conceptual Exploit: Attacker injects properties onto Object.prototype (e.g. __proto__.isAdmin = true), impacting all objects in the Node.js process.",
             [
                 "1. Freeze Object.prototype using Object.freeze(Object.prototype).",
                 "2. Use Object.create(null) or Map for dictionary key-value storage.",
                 "3. Strip '__proto__' and 'constructor' keys during object merge operations."
             ]),
            (r'Object\.assign\s*\([^,]+,\s*req\.body\)', "CWE-1321", "Unsafe Object.assign with unvalidated req.body", SeverityLevel.HIGH,
             "Conceptual Exploit: Attacker passes prototype modification keys in req.body.",
             [
                 "1. Pick only allowed fields explicitly instead of assigning raw req.body.",
                 "2. Validate payload schema with Zod/Joi before assignment.",
                 "3. Use Object.create(null) objects."
             ])
        ]

        mern_rules = nosql_patterns + xss_patterns + jwt_patterns + cors_patterns + proto_patterns
        for line_idx, line in enumerate(lines, 1):
            for pattern, cwe, title, severity, exploit, fixes in mern_rules:
                if re.search(pattern, line):
                    finding_id = f"VULN-{cwe}-{line_idx}"
                    findings.append(
                        VulnerabilityFinding(
                            id=finding_id,
                            cwe_id=cwe,
                            title=title,
                            description=f"MERN vulnerability detected on line {line_idx}.",
                            severity=severity,
                            file_path=filename,
                            line_number=line_idx,
                            snippet=line.strip(),
                            recommendation="Adopt secure coding guidelines for MERN stack components.",
                            exploit_poc=exploit,
                            fix_options=fixes
                        )
                    )
        return findings

    # -------------------------------------------------------------------------
    # Spring Boot (Java) Vulnerability Rules
    # -------------------------------------------------------------------------
    def _audit_spring_boot(self, code: str, filename: str) -> List[VulnerabilityFinding]:
        findings: List[VulnerabilityFinding] = []
        lines = code.split("\n")

        # 1. SQLi in @Query / JdbcTemplate (CWE-89)
        sqli_patterns = [
            (r'@Query\s*\([^)]*["\'][^"\'\n]*\+\s*[a-zA-Z0-9_]', "CWE-89", "SQL Injection via string concatenation in Spring Data @Query", SeverityLevel.CRITICAL,
             "Conceptual Exploit: Attacker injects SQL fragments (e.g. \"' OR '1'='1\") into the concatenated query, altering repository logic.",
             [
                 "1. Use named or indexed parameters in @Query (e.g. ':username' or '?1') instead of string concatenation.",
                 "2. Adopt Spring Data derived query methods (e.g. findByUsername(String username)).",
                 "3. Build dynamic queries using JPA CriteriaBuilder."
             ]),
            (r'jdbcTemplate\.(query|update|execute|queryForList|queryForObject)\s*\(\s*["\'][^"\'\n]*\+\s*', "CWE-89", "SQL Injection via string concatenation in JdbcTemplate", SeverityLevel.CRITICAL,
             "Conceptual Exploit: Attacker injects SQL payloads into unparameterized JdbcTemplate query strings.",
             [
                 "1. Pass SQL parameters as bound arguments: jdbcTemplate.query(sql, rowMapper, arg1, arg2).",
                 "2. Use NamedParameterJdbcTemplate with MapSqlParameterSource.",
                 "3. Use PreparedStatementCreator with parameter bindings."
             ]),
            (r'jdbcTemplate\.(query|update|execute)\s*\(\s*String\.format\s*\(', "CWE-89", "SQL Injection via String.format in JdbcTemplate", SeverityLevel.CRITICAL,
             "Conceptual Exploit: Dynamic query formatting leaves statement vulnerable to injection.",
             [
                 "1. Replace String.format with parameterized query placeholders (?).",
                 "2. Use Spring Data JPA Repositories.",
                 "3. Whitelist dynamic table and column identifiers."
             ])
        ]

        # 2. SpEL Injection (CWE-917)
        spel_patterns = [
            (r'SpelExpressionParser\s*\(\s*\)\.parseExpression\s*\(', "CWE-917", "Spring Expression Language (SpEL) Injection", SeverityLevel.CRITICAL,
             "Conceptual Exploit: Attacker submits an expression like \"T(java.lang.Runtime).getRuntime().exec('calc')\", achieving Remote Code Execution.",
             [
                 "1. Use SimpleEvaluationContext.forReadOnlyDataBinding().build() to disallow arbitrary Java class invocation.",
                 "2. Disallow evaluating untrusted user strings with SpelExpressionParser.",
                 "3. Whitelist allowed expression properties."
             ]),
            (r'parser\.parseExpression\s*\([^)]*\+\s*', "CWE-917", "Dynamic expression concatenation in SpEL parser", SeverityLevel.CRITICAL,
             "Conceptual Exploit: Attacker injects expression operators into concatenated SpEL expressions.",
             [
                 "1. Use static pre-compiled expressions with variables in evaluation context.",
                 "2. Use SimpleEvaluationContext.",
                 "3. Strictly validate expression input syntax."
             ])
        ]

        # 3. Actuator Exposure (CWE-215)
        actuator_patterns = [
            (r'management\.endpoints\.web\.exposure\.include\s*=\s*\*|\binclude:\s*["\']?\*["\']?', "CWE-215", "Overexposed Spring Boot Actuator Endpoints (*)", SeverityLevel.HIGH,
             "Conceptual Exploit: Attacker accesses /actuator/env or /actuator/heapdump to extract database credentials and memory secrets.",
             [
                 "1. Restrict exposed endpoints to necessary minimum (e.g. management.endpoints.web.exposure.include=health,info).",
                 "2. Secure actuator endpoints behind Spring Security requiring ADMIN role.",
                 "3. Bind actuator endpoints to an internal management port (management.server.port=8081)."
             ])
        ]

        # 4. CSRF Disabled (CWE-352)
        csrf_patterns = [
            (r'\.csrf\s*\(\s*\)\.disable\s*\(\s*\)|\.csrf\s*\(\s*csrf\s*->\s*csrf\.disable\s*\(\s*\)\s*\)', "CWE-352", "CSRF Protection Disabled in Spring Security Configuration", SeverityLevel.HIGH,
             "Conceptual Exploit: Attacker crafts cross-origin requests that execute state-changing actions using the victim's session cookie.",
             [
                 "1. Enable CSRF using CookieCsrfTokenRepository.withHttpOnlyFalse().",
                 "2. If stateless JWT authentication is used, document and enforce Bearer token headers with SameSite cookies.",
                 "3. Disable CSRF only on explicit non-browser stateless webhook endpoints."
             ])
        ]

        # 5. Unsafe ObjectInputStream Deserialization (CWE-502)
        deser_patterns = [
            (r'new\s+ObjectInputStream\s*\(|\.readObject\s*\(\s*\)', "CWE-502", "Unsafe Java ObjectInputStream Deserialization", SeverityLevel.CRITICAL,
             "Conceptual Exploit: Attacker provides a serialized gadget chain object, executing arbitrary code upon class deserialization.",
             [
                 "1. Replace Java serialization with JSON (Jackson) or Protocol Buffers.",
                 "2. Apply ObjectInputFilter (JEP 290) to enforce strict class allow-lists.",
                 "3. Verify cryptographic HMAC signature before deserializing."
             ])
        ]

        spring_rules = sqli_patterns + spel_patterns + actuator_patterns + csrf_patterns + deser_patterns
        for line_idx, line in enumerate(lines, 1):
            for pattern, cwe, title, severity, exploit, fixes in spring_rules:
                if re.search(pattern, line):
                    finding_id = f"VULN-{cwe}-{line_idx}"
                    findings.append(
                        VulnerabilityFinding(
                            id=finding_id,
                            cwe_id=cwe,
                            title=title,
                            description=f"Spring Boot security weakness on line {line_idx}.",
                            severity=severity,
                            file_path=filename,
                            line_number=line_idx,
                            snippet=line.strip(),
                            recommendation="Harden Spring Boot security configuration.",
                            exploit_poc=exploit,
                            fix_options=fixes
                        )
                    )
        return findings

    # -------------------------------------------------------------------------
    # Android (Kotlin / Java Code) Vulnerability Rules
    # -------------------------------------------------------------------------
    def _audit_android_code(self, code: str, filename: str) -> List[VulnerabilityFinding]:
        findings: List[VulnerabilityFinding] = []
        lines = code.split("\n")

        # 1. WebView JavaScript Interface (CWE-749)
        webview_patterns = [
            (r'addJavascriptInterface\s*\(', "CWE-749", "Dangerous WebView addJavascriptInterface invocation", SeverityLevel.CRITICAL,
             "Conceptual Exploit: Malicious web content loaded in WebView invokes exposed Java bridge methods to execute unauthorized device actions.",
             [
                 "1. Replace addJavascriptInterface with postMessage/WebMessagePorts.",
                 "2. Restrict WebView navigation strictly to authorized HTTPS internal domain origins.",
                 "3. Ensure all exposed methods are annotated with @JavascriptInterface and API >= 17."
             ]),
            (r'setJavaScriptEnabled\s*\(\s*true\s*\)', "CWE-749", "WebView JavaScript execution enabled without isolation", SeverityLevel.MEDIUM,
             "Conceptual Exploit: Script execution in WebView facilitates Cross-Site Scripting within the Android application context.",
             [
                 "1. Disable JavaScript if dynamic web execution is not strictly required.",
                 "2. Restrict allowed URL schemes and hosts in WebViewClient.shouldOverrideUrlLoading.",
                 "3. Disable file access: webSettings.setAllowFileAccess(false)."
             ])
        ]

        # 2. Cleartext HTTP Traffic in Code (CWE-319)
        cleartext_patterns = [
            (r'["\']http://(?!localhost|127\.0\.0\.1)[^"\'\n]+["\']', "CWE-319", "Cleartext HTTP URL used in mobile client", SeverityLevel.MEDIUM,
             "Conceptual Exploit: An adversary on the local network intercepts or alters unencrypted network traffic via Man-in-the-Middle (MitM).",
             [
                 "1. Upgrade all API and web endpoints to HTTPS.",
                 "2. Configure network_security_config.xml to forbid cleartext traffic.",
                 "3. Implement SSL Certificate Pinning for sensitive API endpoints."
             ])
        ]

        # 3. Hardcoded API Keys / Secrets in BuildConfig or Kotlin code (CWE-798)
        secret_patterns = [
            (r'(?:BuildConfig\.(?:API_KEY|SECRET|TOKEN)|const\s+val\s+(?:API_KEY|SECRET|TOKEN))\s*=\s*["\'][^"\'\n]{8,}["\']', "CWE-798", "Hardcoded API Key / Secret in Android source code", SeverityLevel.HIGH,
             "Conceptual Exploit: Attacker decompiles APK using jadx/apktool and extracts hardcoded credentials.",
             [
                 "1. Store API keys in local.properties and inject via Gradle BuildConfig during CI build.",
                 "2. Restrict API keys by Android package name and SHA-1 certificate fingerprint in Cloud Console.",
                 "3. Fetch transient session credentials from a protected backend proxy."
             ])
        ]

        android_code_rules = webview_patterns + cleartext_patterns + secret_patterns
        for line_idx, line in enumerate(lines, 1):
            for pattern, cwe, title, severity, exploit, fixes in android_code_rules:
                if re.search(pattern, line):
                    finding_id = f"VULN-{cwe}-{line_idx}"
                    findings.append(
                        VulnerabilityFinding(
                            id=finding_id,
                            cwe_id=cwe,
                            title=title,
                            description=f"Android code vulnerability detected on line {line_idx}.",
                            severity=severity,
                            file_path=filename,
                            line_number=line_idx,
                            snippet=line.strip(),
                            recommendation="Harden Android application code against mobile OWASP vulnerabilities.",
                            exploit_poc=exploit,
                            fix_options=fixes
                        )
                    )
        return findings

    # -------------------------------------------------------------------------
    # AndroidManifest.xml & Android XML Resources Rules
    # -------------------------------------------------------------------------
    def _audit_android_xml(self, code: str, filename: str) -> List[VulnerabilityFinding]:
        findings: List[VulnerabilityFinding] = []
        lines = code.split("\n")

        # 1. Component exported="true" without permission (CWE-926)
        # Parse XML or scan lines
        try:
            root = ET.fromstring(code)
            ns = "http://schemas.android.com/apk/res/android"
            for tag in ["activity", "service", "receiver", "provider"]:
                for elem in root.findall(f".//{tag}"):
                    name = elem.attrib.get(f"{{{ns}}}name", "Unnamed")
                    exported = elem.attrib.get(f"{{{ns}}}exported", "").lower()
                    permission = elem.attrib.get(f"{{{ns}}}permission", "")

                    if exported == "true" and not permission:
                        findings.append(
                            VulnerabilityFinding(
                                id=f"VULN-CWE-926-{name}",
                                cwe_id="CWE-926",
                                title=f"Android {tag.capitalize()} '{name}' exported without permission",
                                description=f"The {tag} is exported (android:exported='true') without requiring an android:permission guard.",
                                severity=SeverityLevel.HIGH,
                                file_path=filename,
                                line_number=1,
                                snippet=f"<{tag} android:name=\"{name}\" android:exported=\"true\">",
                                recommendation="Set android:exported='false' or require a signature-level permission.",
                                exploit_poc="Conceptual Exploit: A malicious third-party app invokes the exported component via an explicit Intent, bypassing app navigation or triggering privileged internal logic.",
                                fix_options=[
                                    "1. Set android:exported='false' for internal application components.",
                                    "2. Declare and require a custom signature permission (android:permission).",
                                    "3. Implement caller identity verification inside the component using Binder.getCallingUid()."
                                ]
                            )
                        )
            # Cleartext traffic
            app_elem = root.find(".//application")
            if app_elem is not None:
                cleartext = app_elem.attrib.get(f"{{{ns}}}usesCleartextTraffic", "").lower()
                if cleartext == "true":
                    findings.append(
                        VulnerabilityFinding(
                            id="VULN-CWE-319-manifest",
                            cwe_id="CWE-319",
                            title="Android application allows cleartext HTTP traffic",
                            description="android:usesCleartextTraffic='true' is enabled in AndroidManifest.xml.",
                            severity=SeverityLevel.MEDIUM,
                            file_path=filename,
                            line_number=1,
                            snippet='<application android:usesCleartextTraffic="true">',
                            recommendation="Set android:usesCleartextTraffic='false'.",
                            exploit_poc="Conceptual Exploit: Network eavesdroppers intercept plain text HTTP packets over insecure networks.",
                            fix_options=[
                                "1. Set android:usesCleartextTraffic='false' in <application> tag.",
                                "2. Enforce HTTPS across all remote endpoints.",
                                "3. Configure network_security_config.xml to pin certificates."
                            ]
                        )
                    )
        except Exception:
            # Fallback regex inspection
            for line_idx, line in enumerate(lines, 1):
                if 'android:exported="true"' in line and 'android:permission=' not in line:
                    findings.append(
                        VulnerabilityFinding(
                            id=f"VULN-CWE-926-{line_idx}",
                            cwe_id="CWE-926",
                            title="Android component exported without permission",
                            description=f"Exported component detected on line {line_idx}.",
                            severity=SeverityLevel.HIGH,
                            file_path=filename,
                            line_number=line_idx,
                            snippet=line.strip(),
                            recommendation="Set android:exported='false' or require permissions.",
                            exploit_poc="Conceptual Exploit: Malicious apps invoke exported component directly.",
                            fix_options=[
                                "1. Set android:exported='false'.",
                                "2. Declare custom android:permission.",
                                "3. Check caller UID."
                            ]
                        )
                    )
                if 'android:usesCleartextTraffic="true"' in line:
                    findings.append(
                        VulnerabilityFinding(
                            id=f"VULN-CWE-319-{line_idx}",
                            cwe_id="CWE-319",
                            title="Cleartext HTTP traffic enabled in manifest",
                            description=f"android:usesCleartextTraffic='true' on line {line_idx}.",
                            severity=SeverityLevel.MEDIUM,
                            file_path=filename,
                            line_number=line_idx,
                            snippet=line.strip(),
                            recommendation="Disable cleartext traffic in manifest.",
                            exploit_poc="Conceptual Exploit: MitM attacks over unencrypted traffic.",
                            fix_options=[
                                "1. Set android:usesCleartextTraffic='false'.",
                                "2. Use TLS for all endpoints.",
                                "3. Use network security config."
                            ]
                        )
                    )

        # Hardcoded secrets in strings.xml / Android XML
        secret_re = re.compile(r'<string\s+name=["\'](?:api_key|google_api_key|secret|aws_key|token)[^"\'\n]*["\'][^>]*>([^<]+)</string>', re.IGNORECASE)
        for line_idx, line in enumerate(lines, 1):
            m = secret_re.search(line)
            if m:
                findings.append(
                    VulnerabilityFinding(
                        id=f"VULN-CWE-798-xml-{line_idx}",
                        cwe_id="CWE-798",
                        title="Hardcoded API Key / Secret in strings.xml",
                        description=f"Potential static credential defined in XML resource on line {line_idx}.",
                        severity=SeverityLevel.HIGH,
                        file_path=filename,
                        line_number=line_idx,
                        snippet=line.strip(),
                        recommendation="Store API keys securely outside of compiled APK resources.",
                        exploit_poc="Conceptual Exploit: Decompiling the APK using apktool exposes the plain text string key in res/values/strings.xml.",
                        fix_options=[
                            "1. Store API key in local.properties and inject via Gradle BuildConfig.",
                            "2. Restrict API key by Android SHA-1 package signature in Cloud Console.",
                            "3. Delegate authenticated calls through a backend proxy."
                        ]
                    )
                )

        return findings
