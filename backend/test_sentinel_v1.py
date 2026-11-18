import sys
import os
import asyncio
# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from context.polyglot_ast import PolyglotASTEngine, SymbolTable
from context.session_ledger import SessionLedger
from context.normalizer import ContextNormalizer
from agents.auditor.agent import AuditorAgent
from agents.orchestrator.orchestrator import RemediationOrchestrator
from agents.orchestrator.event_bus import SessionEventBus
from schemas.models import SeverityLevel, AgentConfig


def test_polyglot_ast_javascript_typescript():
    js_code = """
import { calculateTax, formatCurrency } from './utils/math';
import UserService from '../services/userService';
const express = require('express');
const router = express.Router();

const UserModel = mongoose.model('User', new mongoose.Schema({ name: String }));

export class OrderController extends BaseController {
    async createOrder(req, res) {
        return res.json({ status: "created" });
    }
}

export function validatePayload(data) {
    return true;
}

router.get('/api/orders/:id', (req, res) => {
    res.send("Order details");
});

router.post('/api/orders', function handleNewOrder(req, res) {
    res.json({ id: 101 });
});
"""
    table = PolyglotASTEngine.parse(js_code, filename="controllers/OrderController.ts")

    assert any("./utils/math" in imp for imp in table.imports)
    assert any("../services/userService" in imp for imp in table.imports)
    assert any(f.name == "validatePayload" for f in table.functions)
    assert any(c.name == "OrderController" for c in table.classes)
    
    order_ctrl = next(c for c in table.classes if c.name == "OrderController")
    assert "createOrder" in order_ctrl.args

    # Check routes
    assert any(r.path == "/api/orders/:id" and r.method == "GET" for r in table.routes)
    assert any(r.path == "/api/orders" and r.method == "POST" for r in table.routes)

    # Check database models
    assert any(m.name == "UserModel" for m in table.database_models)
    print("PASS: test_polyglot_ast_javascript_typescript")


def test_polyglot_ast_java_spring_boot():
    java_code = """
package com.sentinel.demo;

import org.springframework.web.bind.annotation.*;
import com.sentinel.service.PaymentService;
import javax.persistence.Entity;
import javax.persistence.Table;

@Entity
@Table(name = "payments")
public class PaymentRecord {
    public Long getId() { return 1L; }
    public void processPayment() {}
}

@RestController
@RequestMapping("/api/payments")
public class PaymentController {
    @GetMapping("/{id}")
    public PaymentRecord getPaymentById(@PathVariable Long id) {
        return null;
    }

    @PostMapping("/charge")
    public String executeCharge(@RequestBody String payload) {
        return "success";
    }
}
"""
    table = PolyglotASTEngine.parse(java_code, filename="PaymentController.java")

    assert any("PaymentService" in imp for imp in table.imports)
    assert any(c.name == "PaymentRecord" for c in table.classes)
    assert any(c.name == "PaymentController" for c in table.classes)

    # Check database models
    assert any(m.name == "PaymentRecord" and m.model_type == "jpa/hibernate" for m in table.database_models)

    # Check Spring routes
    assert any(r.path == "/{id}" and r.method == "GET" for r in table.routes)
    assert any(r.path == "/charge" and r.method == "POST" for r in table.routes)
    print("PASS: test_polyglot_ast_java_spring_boot")


def test_polyglot_ast_kotlin_and_android_manifest():
    # 1. Kotlin Code
    kt_code = """
package com.sentinel.mobile

import androidx.room.Entity
import io.ktor.server.routing.*

@Entity(tableName = "cached_users")
data class CachedUser(val id: Int, val username: String) {
    fun getDisplayName(): String = username
}

fun fetchRemoteProfile(userId: Int): String {
    return "profile"
}

fun configureRouting() {
    get("/api/mobile/feed") {
        // handler
    }
}
"""
    kt_table = PolyglotASTEngine.parse(kt_code, filename="ProfileRepository.kt")
    assert any(c.name == "CachedUser" for c in kt_table.classes)
    assert any(f.name == "fetchRemoteProfile" for f in kt_table.functions)
    assert any(m.name == "CachedUser" for m in kt_table.database_models)
    assert any(r.path == "/api/mobile/feed" and r.method == "GET" for r in kt_table.routes)

    # 2. AndroidManifest.xml
    manifest_xml = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.sentinel.android">
    <uses-permission android:name="android.permission.INTERNET" />
    <application android:usesCleartextTraffic="true">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <data android:scheme="https" android:host="app.sentinel.io" android:pathPrefix="/auth" />
            </intent-filter>
        </activity>
        <service android:name=".SyncService" android:exported="false" />
    </application>
</manifest>
"""
    xml_table = PolyglotASTEngine.parse(manifest_xml, filename="AndroidManifest.xml")
    assert "com.sentinel.android" in xml_table.imports
    assert any("android.permission.INTERNET" in v for v in xml_table.global_variables)
    assert any(c.name == ".MainActivity" and c.is_exported for c in xml_table.classes)
    assert any(r.path == "https://app.sentinel.io/auth" and r.method == "INTENT" for r in xml_table.routes)
    print("PASS: test_polyglot_ast_kotlin_and_android_manifest")


def test_dependency_graph_and_context_normalizer():
    ledger = SessionLedger(filename="routes/auth.js", initial_code="// Auth route placeholder")

    # Register helper utility file
    utils_code = """
export function hashPassword(raw) { return "hash"; }
export function verifyToken(token) { return true; }
"""
    ledger.register_file("utils/crypto.js", utils_code)

    # Register dependent auth file with cross-file import
    auth_code = """
import { hashPassword, verifyToken } from '../utils/crypto';
export function login(username, password) {
    return hashPassword(password);
}
"""
    ledger.register_file("routes/auth.js", auth_code)

    # Verify dependency graph created the edge: routes/auth.js -> utils/crypto.js
    assert "routes/auth.js" in ledger.dependency_graph
    deps = ledger.dependency_graph["routes/auth.js"]
    assert any("utils/crypto" in d for d in deps)

    # Verify 1-hop symbols retrieval
    one_hop = ledger.get_1_hop_imported_symbols("routes/auth.js")
    assert len(one_hop) > 0
    first_dep_table = list(one_hop.values())[0]
    assert any(f.name == "hashPassword" for f in first_dep_table.functions)
    assert any(f.name == "verifyToken" for f in first_dep_table.functions)

    # Verify ContextNormalizer injects exact 1-hop signatures into prompt envelope
    dev_prompt = ContextNormalizer.build_developer_prompt("Implement JWT refresh logic", ledger)
    assert "<one_hop_imported_dependencies>" in dev_prompt
    assert "hashPassword" in dev_prompt
    assert "verifyToken" in dev_prompt
    print("PASS: test_dependency_graph_and_context_normalizer")


def test_polyglot_auditor_mern():
    auditor = AuditorAgent(name="Snooze")

    mern_code = """
const express = require('express');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const app = express();

app.use(cors({ origin: "*" }));

app.post('/api/login', async (req, res) => {
    // 1. NoSQL operator injection
    const user = await User.find(req.body);
    const complex = await User.find({ $where: "this.password == '" + req.body.pwd + "'" });
    
    // 2. JWT hardcoded secret
    const token = jwt.sign({ id: user.id }, "static_secret_12345");

    // 3. Prototype pollution
    Object.assign(targetObj, req.body);
    const p = req.body.__proto__;

    return res.json({ token });
});

function UserAvatar({ bio }) {
    // 4. XSS
    return <div dangerouslySetInnerHTML={{ __html: bio }} />;
}
"""
    audit = auditor.audit_code(mern_code, filename="server.js")
    assert not audit.is_secure

    # Verify all MERN vulnerability categories detected
    cwe_ids = {f.cwe_id for f in audit.findings}
    assert "CWE-943" in cwe_ids  # NoSQL injection
    assert "CWE-79" in cwe_ids   # XSS
    assert "CWE-798" in cwe_ids  # JWT hardcoded secret
    assert "CWE-942" in cwe_ids  # CORS wildcard
    assert "CWE-1321" in cwe_ids # Prototype pollution

    # Verify Exploit PoC and 2-3 Architectural Fix Options are generated
    for f in audit.findings:
        assert f.exploit_poc is not None and len(f.exploit_poc) > 10
        assert len(f.fix_options) >= 2
    print("PASS: test_polyglot_auditor_mern")


def test_polyglot_auditor_spring_boot_and_android():
    auditor = AuditorAgent(name="Snooze")

    # 1. Spring Boot Java
    spring_code = """
package com.example.demo;
import org.springframework.data.jpa.repository.Query;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.expression.spel.standard.SpelExpressionParser;
import java.io.ObjectInputStream;

public class VulnerableSpringService {
    @Query("SELECT u FROM User u WHERE u.username = '" + input + "'")
    public void queryByStringConcat(String input) {}

    public void runDynamicJdbc(JdbcTemplate jdbcTemplate, String id) {
        jdbcTemplate.query("SELECT * FROM accounts WHERE id = " + id, (rs, n) -> null);
    }

    public void evaluateSpel(String userExpression) {
        new SpelExpressionParser().parseExpression(userExpression).getValue();
    }

    public void disableCsrf(org.springframework.security.config.annotation.web.builders.HttpSecurity http) throws Exception {
        http.csrf().disable();
    }

    public void deserializeData(java.io.InputStream in) throws Exception {
        ObjectInputStream ois = new ObjectInputStream(in);
        ois.readObject();
    }
}
"""
    spring_audit = auditor.audit_code(spring_code, filename="VulnerableSpringService.java")
    assert not spring_audit.is_secure
    spring_cwes = {f.cwe_id for f in spring_audit.findings}
    assert "CWE-89" in spring_cwes   # SQLi in @Query / JdbcTemplate
    assert "CWE-917" in spring_cwes  # SpEL injection
    assert "CWE-352" in spring_cwes  # CSRF disabled
    assert "CWE-502" in spring_cwes  # Insecure ObjectInputStream

    # 2. Android Manifest & Kotlin
    android_manifest = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.mobile.vuln">
    <application android:usesCleartextTraffic="true">
        <activity android:name=".SecretActivity" android:exported="true" />
    </application>
</manifest>
"""
    manifest_audit = auditor.audit_code(android_manifest, filename="AndroidManifest.xml")
    assert not manifest_audit.is_secure
    manifest_cwes = {f.cwe_id for f in manifest_audit.findings}
    assert "CWE-926" in manifest_cwes # Exported without permission
    assert "CWE-319" in manifest_cwes # Cleartext traffic enabled

    android_code = """
package com.mobile.vuln
import android.webkit.WebView

class WebContainer(val webView: WebView) {
    fun setup() {
        webView.settings.javaScriptEnabled = true
        webView.addJavascriptInterface(this, "AndroidNativeBridge")
        val endpoint = "http://api.insecure-external.com/v1/auth"
        val API_KEY = "AIzaSyD-TEST-HARDCODED-KEY-99999"
    }
}
"""
    android_audit = auditor.audit_code(android_code, filename="WebContainer.kt")
    assert not android_audit.is_secure
    android_cwes = {f.cwe_id for f in android_audit.findings}
    assert "CWE-749" in android_cwes # WebView JS interface
    assert "CWE-319" in android_cwes # Cleartext HTTP URL
    print("PASS: test_polyglot_auditor_spring_boot_and_android")


def test_websocket_telemetry_and_vibe_interactive_mode():
    client = TestClient(app)
    session_id = "test-ws-session-001"

    # Test WebSocket connection and telemetry streaming
    with client.websocket_connect(f"/ws/session/{session_id}") as websocket:
        init_data = websocket.receive_json()
        assert init_data["type"] == "CONNECTION_ESTABLISHED"
        assert init_data["session_id"] == session_id

        # Ping-Pong test
        websocket.send_json({"action": "PING"})
        pong_data = websocket.receive_json()
        assert pong_data["type"] == "PONG"

    # Test Orchestrator vibe_interactive mode with event bus
    async def run_vibe_interactive_test():
        event_bus = SessionEventBus()
        orchestrator = RemediationOrchestrator(event_bus=event_bus)

        vulnerable_code = """def get_account(user_id, db):
    query = f"SELECT * FROM accounts WHERE id = {user_id}"
    db.execute(query)
"""
        agent_config = {
            "persona_style": "cyberpunk",
            "security_level": "balanced",
            "ui_theme_target": "neo_brutalist"
        }

        # Launch vibe_interactive remediation task
        remediation_task = asyncio.create_task(
            orchestrator.remediate_code_async(
                raw_code=vulnerable_code,
                filename="accounts.py",
                session_id=session_id,
                mode="vibe_interactive",
                agent_config=agent_config
            )
        )

        # Allow orchestrator to analyze and enter waiting_approval state
        await asyncio.sleep(0.15)

        # Submit APPROVE_FIX command
        approval_cmd = {
            "action": "APPROVE_FIX",
            "finding_id": "VULN-CWE-89-2",
            "selected_strategy": "1. Parameterized SQL query placeholder",
            "custom_instruction": "Ensure type hints are preserved"
        }
        res = event_bus.submit_approval(session_id, approval_cmd)
        assert res is True

        # Wait for remediation to complete
        result = await remediation_task
        assert result["is_secure"] is True
        assert result["mode"] == "vibe_interactive"
        assert "SELECT" in result["final_code"]

        # Check recorded event history for required structured events
        events = event_bus.event_history.get(session_id, [])
        event_types = [e.get("type") for e in events]
        assert "AGENT_STATE" in event_types
        assert "CURSOR_MOVE" in event_types
        assert "VULN_DETECTED" in event_types
        assert "LIVE_DIFF_CHUNK" in event_types

        # Verify cyberpunk persona formatting
        cyber_messages = [e.get("message", "") for e in events if e.get("type") == "AGENT_STATE"]
        assert any("Dex jacked into" in m or "Dex formulating" in m or "Snooze" in m for m in cyber_messages)

    asyncio.run(run_vibe_interactive_test())
    print("PASS: test_websocket_telemetry_and_vibe_interactive_mode")


def run_all_v1_tests():
    print("=== Running Sentinel v1.0 Polyglot Studio Test Suite ===")
    test_polyglot_ast_javascript_typescript()
    test_polyglot_ast_java_spring_boot()
    test_polyglot_ast_kotlin_and_android_manifest()
    test_dependency_graph_and_context_normalizer()
    test_polyglot_auditor_mern()
    test_polyglot_auditor_spring_boot_and_android()
    test_websocket_telemetry_and_vibe_interactive_mode()
    print("=== ALL SENTINEL v1.0 TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    run_all_v1_tests()
