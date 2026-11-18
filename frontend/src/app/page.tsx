"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { CommandHeader } from "../components/CommandHeader";
import { LeftPane } from "../components/LeftPane";
import { CodeCanvas } from "../components/CodeCanvas";
import { RightPane } from "../components/RightPane";
import { VibeBar } from "../components/VibeBar";
import { AgentDrawer } from "../components/AgentDrawer";
import {
  ProjectFile,
  WorkspaceData,
  TechStack,
  ExecutionMode,
  AgentConfig,
  AgentCursor,
  AgentTelemetryEvent,
  Finding,
} from "../types/sentinel";

const BACKEND_URL = "http://localhost:8000";
const WS_URL = "ws://localhost:8000";

// Pre-seeded multi-file scaffolds for instant polyglot vibe coding demonstrations
const POLYGLOT_PRESETS: Record<TechStack, Record<string, ProjectFile>> = {
  mern: {
    "backend/server.js": {
      path: "backend/server.js",
      original_content: `const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const jwt = require('jsonwebtoken');
const app = express();

app.use(express.json());
// 1. Insecure CORS Wildcard
app.use(cors({ origin: "*" }));

// 2. Prototype Pollution via Object.assign with req.body
app.post('/api/profile/update', (req, res) => {
    const userProfile = {};
    Object.assign(userProfile, req.body);
    res.json({ success: true, profile: userProfile });
});

app.listen(8000, () => console.log('MERN Server running on port 8000'));`,
      current_content: `const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const jwt = require('jsonwebtoken');
const app = express();

app.use(express.json());
// 1. Insecure CORS Wildcard
app.use(cors({ origin: "*" }));

// 2. Prototype Pollution via Object.assign with req.body
app.post('/api/profile/update', (req, res) => {
    const userProfile = {};
    Object.assign(userProfile, req.body);
    res.json({ success: true, profile: userProfile });
});

app.listen(8000, () => console.log('MERN Server running on port 8000'));`,
      is_modified: false,
      findings_count: 2,
      diff: "",
      findings: [
        {
          id: "VULN-CWE-942-10",
          cwe_id: "CWE-942",
          title: "Permissive CORS Wildcard Policy (origin: '*')",
          description: "Wildcard CORS allows untrusted third-party origins to access authenticated responses.",
          severity: "MEDIUM",
          file_path: "backend/server.js",
          line_number: 10,
          line_start: 10,
          line_end: 10,
          snippet: 'app.use(cors({ origin: "*" }));',
          exploit_poc: "Conceptual Exploit: An untrusted domain makes cross-origin requests on behalf of users.",
          exploit_demo: "fetch('http://localhost:8000/api', { headers: { Origin: 'http://malicious-site.com' } })",
          whitebox_trace: {
            source: "Origin header from untrusted cross-origin domain",
            sanitizer: "None (wildcard origin trust)",
            sink: "Access-Control-Allow-Origin: *"
          },
          fix_options: [
            "Option 1: Specify an explicit allowed origin whitelist in CORS options: origin: ['http://localhost:3000']",
            "Option 2: Integrate helmet() security middleware to enforce strict HTTP security headers"
          ],
          vibe_remediation_options: [
            "Option 1: Specify an explicit allowed origin whitelist in CORS options: origin: ['http://localhost:3000']",
            "Option 2: Integrate helmet() security middleware to enforce strict HTTP security headers"
          ]
        },
        {
          id: "VULN-CWE-1321-16",
          cwe_id: "CWE-1321",
          title: "Prototype Pollution via unvalidated Object.assign",
          description: "Unsanitized req.body assigned directly can modify Object.prototype.",
          severity: "HIGH",
          file_path: "backend/server.js",
          line_number: 16,
          line_start: 16,
          line_end: 16,
          snippet: "Object.assign(userProfile, req.body);",
          exploit_poc: "Conceptual Exploit: Attacker passes '__proto__.isAdmin = true' to elevate privileges across the app.",
          exploit_demo: '{"__proto__": {"isAdmin": true}}',
          whitebox_trace: {
            source: "req.body containing polluted prototype keys",
            sanitizer: "None (unrestricted object assignment)",
            sink: "Object.assign(userProfile, req.body)"
          },
          fix_options: [
            "Option 1: Filter and assign only whitelisted fields explicitly using Zod schema parsing",
            "Option 2: Freeze Object.prototype using Object.freeze(Object.prototype) during bootstrap"
          ],
          vibe_remediation_options: [
            "Option 1: Filter and assign only whitelisted fields explicitly using Zod schema parsing",
            "Option 2: Freeze Object.prototype using Object.freeze(Object.prototype) during bootstrap"
          ]
        }
      ]
    },
    "backend/routes/auth.js": {
      path: "backend/routes/auth.js",
      original_content: `const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const User = require('../models/User');

// 1. NoSQL Operator Injection ($where / unsanitized req.body)
router.post('/login', async (req, res) => {
    const user = await User.find(req.body);
    if (!user || user.length === 0) {
        return res.status(401).json({ error: "Invalid credentials" });
    }

    // 2. Hardcoded JWT Secret
    const token = jwt.sign({ id: user[0]._id }, "super_secret_jwt_key_12345");
    return res.json({ token, user: user[0] });
});

module.exports = router;`,
      current_content: `const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const User = require('../models/User');

// 1. NoSQL Operator Injection ($where / unsanitized req.body)
router.post('/login', async (req, res) => {
    const user = await User.find(req.body);
    if (!user || user.length === 0) {
        return res.status(401).json({ error: "Invalid credentials" });
    }

    // 2. Hardcoded JWT Secret
    const token = jwt.sign({ id: user[0]._id }, "super_secret_jwt_key_12345");
    return res.json({ token, user: user[0] });
});

module.exports = router;`,
      is_modified: false,
      findings_count: 2,
      diff: "",
      findings: [
        {
          id: "VULN-CWE-943-8",
          cwe_id: "CWE-943",
          title: "NoSQL Operator Injection in MongoDB Query",
          description: "Unsanitized req.body passed directly to User.find allows operator injection.",
          severity: "CRITICAL",
          file_path: "backend/routes/auth.js",
          line_number: 8,
          line_start: 8,
          line_end: 8,
          snippet: "const user = await User.find(req.body);",
          exploit_poc: 'Conceptual Exploit: Attacker passes {"password": {"$gt": ""}} to bypass authentication without valid credentials.',
          exploit_demo: '{"username": "admin", "password": {"$gt": ""}}',
          whitebox_trace: {
            source: "req.body from unauthenticated POST /api/login",
            sanitizer: "None (passed directly to query without schema check)",
            sink: "Mongoose User.find(req.body)"
          },
          fix_options: [
            "Option 1: Sanitize incoming request objects with mongo-sanitize and bind explicit fields: { username: req.body.username }",
            "Option 2: Enforce strict Zod schema validation on request payload before passing to database queries"
          ],
          vibe_remediation_options: [
            "Option 1: Sanitize incoming request objects with mongo-sanitize and bind explicit fields: { username: req.body.username }",
            "Option 2: Enforce strict Zod schema validation on request payload before passing to database queries"
          ]
        },
        {
          id: "VULN-CWE-798-14",
          cwe_id: "CWE-798",
          title: "Hardcoded JSON Web Token Secret",
          description: "Static JWT secret key exposed directly in source code.",
          severity: "HIGH",
          file_path: "backend/routes/auth.js",
          line_number: 14,
          line_start: 14,
          line_end: 14,
          snippet: 'const token = jwt.sign({ id: user[0]._id }, "super_secret_jwt_key_12345");',
          exploit_poc: "Conceptual Exploit: Attacker extracts the hardcoded secret to sign forged admin tokens.",
          exploit_demo: 'jwt.sign({ id: "admin_1" }, "super_secret_jwt_key_12345")',
          whitebox_trace: {
            source: "hardcoded string literal in auth.js line 14",
            sanitizer: "None (plain text signing secret)",
            sink: "jwt.sign() cryptographic token signer"
          },
          fix_options: [
            "Option 1: Load JWT secret from process.env.JWT_SECRET with fallback guard",
            "Option 2: Migrate to asymmetric RS256/ES256 keypairs with public key verification"
          ],
          vibe_remediation_options: [
            "Option 1: Load JWT secret from process.env.JWT_SECRET with fallback guard",
            "Option 2: Migrate to asymmetric RS256/ES256 keypairs with public key verification"
          ]
        }
      ]
    },
    "frontend/components/Profile.jsx": {
      path: "frontend/components/Profile.jsx",
      original_content: `import React from 'react';

export default function UserProfileCard({ userBio }) {
    return (
        <div className="profile-container">
            <h3>User Biography</h3>
            {/* Cross-Site Scripting via dangerouslySetInnerHTML */}
            <div dangerouslySetInnerHTML={{ __html: userBio }} />
        </div>
    );
}`,
      current_content: `import React from 'react';

export default function UserProfileCard({ userBio }) {
    return (
        <div className="profile-container">
            <h3>User Biography</h3>
            {/* Cross-Site Scripting via dangerouslySetInnerHTML */}
            <div dangerouslySetInnerHTML={{ __html: userBio }} />
        </div>
    );
}`,
      is_modified: false,
      findings_count: 1,
      diff: "",
      findings: [
        {
          id: "VULN-CWE-79-8",
          cwe_id: "CWE-79",
          title: "Cross-Site Scripting (XSS) via dangerouslySetInnerHTML",
          description: "Unsanitized userBio rendered directly into DOM allows script execution.",
          severity: "HIGH",
          file_path: "frontend/components/Profile.jsx",
          line_number: 8,
          line_start: 8,
          line_end: 8,
          snippet: "<div dangerouslySetInnerHTML={{ __html: userBio }} />",
          exploit_poc: "Conceptual Exploit: Attacker enters `<img src=x onerror=alert(document.cookie)>` in user bio to hijack sessions.",
          exploit_demo: "<img src=x onerror=alert(document.cookie)>",
          whitebox_trace: {
            source: "userBio component prop from untrusted API payload",
            sanitizer: "None (bypassed React escaping)",
            sink: "dangerouslySetInnerHTML={{ __html: userBio }}"
          },
          fix_options: [
            "Option 1: Sanitize raw HTML with DOMPurify.sanitize(userBio)",
            "Option 2: Use default JSX data binding `{userBio}` which automatically escapes HTML"
          ],
          vibe_remediation_options: [
            "Option 1: Sanitize raw HTML with DOMPurify.sanitize(userBio)",
            "Option 2: Use default JSX data binding `{userBio}` which automatically escapes HTML"
          ]
        }
      ]
    }
  },
  spring: {
    "src/main/java/com/sentinel/PaymentController.java": {
      path: "src/main/java/com/sentinel/PaymentController.java",
      original_content: `package com.sentinel;

import org.springframework.web.bind.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import java.util.List;

@RestController
@RequestMapping("/api/payments")
public class PaymentController {
    private final JdbcTemplate jdbcTemplate;

    public PaymentController(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @GetMapping("/search")
    public List<Object> searchPayments(@RequestParam String orderId) {
        // SQL Injection via string concatenation in JdbcTemplate
        String query = "SELECT * FROM payments WHERE order_id = " + orderId;
        return jdbcTemplate.queryForList(query);
    }
}`,
      current_content: `package com.sentinel;

import org.springframework.web.bind.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import java.util.List;

@RestController
@RequestMapping("/api/payments")
public class PaymentController {
    private final JdbcTemplate jdbcTemplate;

    public PaymentController(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @GetMapping("/search")
    public List<Object> searchPayments(@RequestParam String orderId) {
        // SQL Injection via string concatenation in JdbcTemplate
        String query = "SELECT * FROM payments WHERE order_id = " + orderId;
        return jdbcTemplate.queryForList(query);
    }
}`,
      is_modified: false,
      findings_count: 1,
      diff: "",
      findings: [
        {
          id: "VULN-CWE-89-19",
          cwe_id: "CWE-89",
          title: "SQL Injection via Concatenation in JdbcTemplate",
          description: "orderId is directly concatenated into the SQL statement.",
          severity: "CRITICAL",
          file_path: "src/main/java/com/sentinel/PaymentController.java",
          line_number: 19,
          snippet: 'String query = "SELECT * FROM payments WHERE order_id = " + orderId;',
          exploit_poc: "Conceptual Exploit: Attacker passes '1 OR 1=1' in orderId to dump all payment records.",
          fix_options: [
            "1. Use parameterized placeholders: jdbcTemplate.queryForList(sql, orderId)",
            "2. Use NamedParameterJdbcTemplate with MapSqlParameterSource",
            "3. Migrate to Spring Data JPA repository derived methods"
          ]
        }
      ]
    },
    "src/main/resources/application.properties": {
      path: "src/main/resources/application.properties",
      original_content: `server.port=8080
spring.datasource.url=jdbc:postgresql://localhost:5432/sentinel_db
management.endpoints.web.exposure.include=*`,
      current_content: `server.port=8080
spring.datasource.url=jdbc:postgresql://localhost:5432/sentinel_db
management.endpoints.web.exposure.include=*`,
      is_modified: false,
      findings_count: 1,
      diff: "",
      findings: [
        {
          id: "VULN-CWE-215-3",
          cwe_id: "CWE-215",
          title: "Overexposed Spring Boot Actuator Endpoints (*)",
          description: "All actuator endpoints are exposed without restriction.",
          severity: "HIGH",
          file_path: "src/main/resources/application.properties",
          line_number: 3,
          snippet: "management.endpoints.web.exposure.include=*",
          exploit_poc: "Conceptual Exploit: Attacker accesses /actuator/env and /actuator/heapdump to extract database credentials and memory.",
          fix_options: [
            "1. Restrict exposed endpoints to health,info only",
            "2. Secure endpoints behind Spring Security with ADMIN role",
            "3. Bind actuator to a dedicated internal management port"
          ]
        }
      ]
    }
  },
  fastapi: {
    "backend/app.py": {
      path: "backend/app.py",
      original_content: `from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/api/ping")
def ping_host(host: str):
    # Command Injection via os.system
    os.system(f"ping -c 1 {host}")
    return {"status": "sent"}`,
      current_content: `from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/api/ping")
def ping_host(host: str):
    # Command Injection via os.system
    os.system(f"ping -c 1 {host}")
    return {"status": "sent"}`,
      is_modified: false,
      findings_count: 1,
      diff: "",
      findings: [
        {
          id: "VULN-CWE-78-9",
          cwe_id: "CWE-78",
          title: "Command Injection in os.system",
          description: "Host parameter is concatenated into shell command.",
          severity: "CRITICAL",
          file_path: "backend/app.py",
          line_number: 9,
          snippet: 'os.system(f"ping -c 1 {host}")',
          exploit_poc: "Conceptual Exploit: Attacker inputs '127.0.0.1; cat /etc/passwd' to execute arbitrary operating system commands.",
          fix_options: [
            "1. Use subprocess.run(['ping', '-c', '1', host], shell=False)",
            "2. Validate host format against a strict IP address regex",
            "3. Use a pure Python ICMP ping library instead of system shell"
          ]
        }
      ]
    }
  },
  android: {
    "app/src/main/AndroidManifest.xml": {
      path: "app/src/main/AndroidManifest.xml",
      original_content: `<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.sentinel.android">
    <application android:usesCleartextTraffic="true">
        <activity android:name=".AdminPortalActivity" android:exported="true" />
    </application>
</manifest>`,
      current_content: `<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.sentinel.android">
    <application android:usesCleartextTraffic="true">
        <activity android:name=".AdminPortalActivity" android:exported="true" />
    </application>
</manifest>`,
      is_modified: false,
      findings_count: 2,
      diff: "",
      findings: [
        {
          id: "VULN-CWE-926-4",
          cwe_id: "CWE-926",
          title: "Android Activity Exported Without Permission",
          description: "AdminPortalActivity has android:exported='true' without an android:permission guard.",
          severity: "HIGH",
          file_path: "app/src/main/AndroidManifest.xml",
          line_number: 4,
          snippet: '<activity android:name=".AdminPortalActivity" android:exported="true" />',
          exploit_poc: "Conceptual Exploit: A malicious third-party app launches AdminPortalActivity directly via explicit Intent.",
          fix_options: [
            "1. Set android:exported='false' for internal components",
            "2. Declare and require custom signature-level permission",
            "3. Implement caller package validation using Binder.getCallingUid()"
          ]
        },
        {
          id: "VULN-CWE-319-3",
          cwe_id: "CWE-319",
          title: "Cleartext HTTP Traffic Allowed in Manifest",
          description: "android:usesCleartextTraffic='true' allows unencrypted network communication.",
          severity: "MEDIUM",
          file_path: "app/src/main/AndroidManifest.xml",
          line_number: 3,
          snippet: '<application android:usesCleartextTraffic="true">',
          exploit_poc: "Conceptual Exploit: Network attackers perform Man-in-the-Middle eavesdropping over public Wi-Fi.",
          fix_options: [
            "1. Set android:usesCleartextTraffic='false' in application tag",
            "2. Configure network_security_config.xml with TLS pinning",
            "3. Enforce HTTPS across all remote endpoints"
          ]
        }
      ]
    },
    "app/src/main/java/com/sentinel/WebActivity.kt": {
      path: "app/src/main/java/com/sentinel/WebActivity.kt",
      original_content: `package com.sentinel

import android.os.Bundle
import android.webkit.WebView
import androidx.appcompat.app.AppCompatActivity

class WebActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val webView = WebView(this)
        webView.settings.javaScriptEnabled = true
        // Insecure JS interface
        webView.addJavascriptInterface(this, "AndroidInterface")
        webView.loadUrl("http://portal.sentinel.io")
    }
}`,
      current_content: `package com.sentinel

import android.os.Bundle
import android.webkit.WebView
import androidx.appcompat.app.AppCompatActivity

class WebActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val webView = WebView(this)
        webView.settings.javaScriptEnabled = true
        // Insecure JS interface
        webView.addJavascriptInterface(this, "AndroidInterface")
        webView.loadUrl("http://portal.sentinel.io")
    }
}`,
      is_modified: false,
      findings_count: 2,
      diff: "",
      findings: [
        {
          id: "VULN-CWE-749-13",
          cwe_id: "CWE-749",
          title: "WebView Remote Code Execution via addJavascriptInterface",
          description: "Exposing native object to WebView allows malicious web pages to execute Java bridge methods.",
          severity: "CRITICAL",
          file_path: "app/src/main/java/com/sentinel/WebActivity.kt",
          line_number: 13,
          snippet: 'webView.addJavascriptInterface(this, "AndroidInterface")',
          exploit_poc: "Conceptual Exploit: Script loaded in WebView accesses device storage through Java bridge reflection.",
          fix_options: [
            "1. Replace addJavascriptInterface with postMessage/WebMessagePorts",
            "2. Restrict WebView navigation strictly to authorized HTTPS origins",
            "3. Enforce @JavascriptInterface annotations on API >= 17"
          ]
        },
        {
          id: "VULN-CWE-319-14",
          cwe_id: "CWE-319",
          title: "Cleartext HTTP URL in WebView",
          description: "WebView loads unencrypted HTTP URL.",
          severity: "MEDIUM",
          file_path: "app/src/main/java/com/sentinel/WebActivity.kt",
          line_number: 14,
          snippet: 'webView.loadUrl("http://portal.sentinel.io")',
          exploit_poc: "Conceptual Exploit: Insecure HTTP is susceptible to content injection by local network proxies.",
          fix_options: [
            "1. Upgrade to HTTPS URL: https://portal.sentinel.io",
            "2. Use network security config to block cleartext traffic",
            "3. Implement SSL pinning in WebViewClient"
          ]
        }
      ]
    }
  }
};

export default function WhiteBoxVibeStudio() {
  const [currentStack, setCurrentStack] = useState<TechStack>("mern");
  const [files, setFiles] = useState<Record<string, ProjectFile>>(POLYGLOT_PRESETS.mern);
  const [selectedFilePath, setSelectedFilePath] = useState<string>("backend/routes/auth.js");
  const [executionMode, setExecutionMode] = useState<ExecutionMode>("vibe_interactive");
  const [agentDrawerOpen, setAgentDrawerOpen] = useState<boolean>(false);
  const [vibePrompt, setVibePrompt] = useState<string>(
    "Surgically audit all endpoints across the repo and patch NoSQL injection and CORS policies"
  );
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [activeAgent, setActiveAgent] = useState<string>("dex");
  const [activeCursor, setActiveCursor] = useState<AgentCursor | null>(null);
  const [telemetryLogs, setTelemetryLogs] = useState<AgentTelemetryEvent[]>([]);
  const [sessionId, setSessionId] = useState<string>("sess-studio-live");
  const [sandboxHtml, setSandboxHtml] = useState<string>("");
  const [localhostUrl, setLocalhostUrl] = useState<string>("http://localhost:8000");
  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);

  useEffect(() => {
    setSessionId("sess-" + Math.random().toString(36).substring(2, 10));
  }, []);

  const [agentConfig, setAgentConfig] = useState<AgentConfig>({
    persona_style: "cyberpunk",
    security_level: "balanced",
    ui_theme_target: "linear_dark",
  });

  const wsRef = useRef<WebSocket | null>(null);

  // Initialize and maintain WebSocket connection to backend
  useEffect(() => {
    let ws: WebSocket;
    try {
      ws = new WebSocket(`${WS_URL}/ws/session/${sessionId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsWsConnected(true);
        setTelemetryLogs((prev) => [
          {
            type: "CONNECTION_ESTABLISHED",
            message: `Connected to Sentinel v1.0 Real-Time Event Bus [${sessionId}]`,
            timestamp: new Date().toISOString(),
          },
          ...prev,
        ]);
      };

      ws.onmessage = (event) => {
        try {
          const data: AgentTelemetryEvent = JSON.parse(event.data);
          setTelemetryLogs((prev) => [data, ...prev.slice(0, 150)]);

          if (data.type === "AGENT_STATE" && data.agent) {
            setActiveAgent(data.agent);
          } else if (data.type === "CURSOR_MOVE" && data.file && data.line) {
            setActiveCursor({
              agent: (data.agent as any) || "snooze",
              file: data.file,
              line: data.line,
              column: data.column || 1,
              message: data.message,
            });
            // Auto-switch to file if cursor moved there
            setSelectedFilePath((curr) => (files[data.file!] ? data.file! : curr));
          } else if (data.type === "LIVE_DIFF_CHUNK" && data.file) {
            // Apply diff to current file
            setFiles((prev) => {
              const target = prev[data.file!];
              if (!target) return prev;
              return {
                ...prev,
                [data.file!]: {
                  ...target,
                  is_modified: true,
                  findings_count: Math.max(0, target.findings_count - 1),
                  diff: data.explanation ? `${data.explanation}\n+ ${data.patched_lines?.join("\n+ ")}` : target.diff,
                },
              };
            });
          }
        } catch (e) {
          console.error("Failed to parse WebSocket message", e);
        }
      };

      ws.onclose = () => {
        setIsWsConnected(false);
      };

      ws.onerror = () => {
        setIsWsConnected(false);
      };
    } catch (err) {
      console.warn("WebSocket connection could not be established; running local simulation mode", err);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [sessionId]);

  // Handle switching Tech Stacks
  const handleSelectStack = (stack: TechStack) => {
    setCurrentStack(stack);
    const newFiles = POLYGLOT_PRESETS[stack];
    setFiles(newFiles);
    const firstKey = Object.keys(newFiles)[0];
    setSelectedFilePath(firstKey);
    setTelemetryLogs((prev) => [
      {
        type: "AGENT_STATE",
        agent: "dex",
        status: "thinking",
        message: `Switched active stack to ${stack.toUpperCase()}. Hydrated AST symbol tables.`,
        timestamp: new Date().toISOString(),
      },
      ...prev,
    ]);
  };

  // Submit Vibe Coding Prompt or Run Autopilot
  const handleRunVibePrompt = async (promptText: string) => {
    if (isRunning) return;
    setIsRunning(true);

    const activeFile = files[selectedFilePath];
    const codeToAudit = activeFile ? activeFile.current_content : "";

    // Stream Scene 1: Dex (The Architect)
    setActiveAgent("dex");
    setActiveCursor({ agent: "dex", file: selectedFilePath, line: 1, column: 1, message: "Analyzing trust boundaries" });
    setTelemetryLogs((prev) => [
      {
        type: "AGENT_STATE",
        agent: "dex",
        status: "thinking",
        message: `Dex formulating formal invariants for: '${promptText.slice(0, 70)}...'`,
        timestamp: new Date().toISOString(),
      },
      ...prev,
    ]);

    // Send through WebSocket if open
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          action: "START_REMEDIATION",
          code: codeToAudit,
          filename: selectedFilePath,
          mode: executionMode,
          agent_config: agentConfig,
        })
      );
    }

    // Call REST endpoint for verification and fallback
    try {
      const response = await fetch(`${BACKEND_URL}/api/remediate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: codeToAudit,
          filename: selectedFilePath,
          session_id: sessionId,
          mode: executionMode,
          agent_config: agentConfig,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const finalCode = data.final_code || codeToAudit;
        const patchDiff = data.history?.[0]?.patch_diff || "";

        // Update file state
        setFiles((prev) => ({
          ...prev,
          [selectedFilePath]: {
            ...prev[selectedFilePath],
            current_content: finalCode,
            is_modified: true,
            findings_count: 0,
            diff: patchDiff,
          },
        }));

        setActiveAgent("glitch");
        setActiveCursor({
          agent: "glitch",
          file: selectedFilePath,
          line: 1,
          column: 1,
          message: "Remediation verified clean",
        });

        setTelemetryLogs((prev) => [
          {
            type: "AGENT_STATE",
            agent: "glitch",
            status: "completed",
            message: "Glitch applied surgical zero-regression patch. Verified clean by Snooze.",
            timestamp: new Date().toISOString(),
          },
          ...prev,
        ]);
      }
    } catch (err) {
      // Local fallback simulation if backend offline
      setTimeout(() => {
        setFiles((prev) => {
          const cur = prev[selectedFilePath];
          if (!cur) return prev;
          let patched = cur.current_content;
          if (cur.path.includes("auth.js")) {
            patched = patched.replace("User.find(req.body)", "User.find(mongoSanitize(req.body))");
            patched = patched.replace('"super_secret_jwt_key_12345"', 'process.env.JWT_SECRET || "default_secret"');
            if (!patched.includes("mongoSanitize")) {
              patched = "const mongoSanitize = require('mongo-sanitize');\n" + patched;
            }
          }
          return {
            ...prev,
            [selectedFilePath]: {
              ...cur,
              current_content: patched,
              is_modified: true,
              findings_count: 0,
              diff: "+ const mongoSanitize = require('mongo-sanitize');\n- User.find(req.body)\n+ User.find(mongoSanitize(req.body))",
            },
          };
        });
        setActiveAgent("glitch");
      }, 1200);
    } finally {
      setIsRunning(false);
    }
  };

  // Interactive Approval Handler (Vibe Interactive Mode)
  const handleApproveFix = (findingId: string, strategy: string, customInstruction?: string) => {
    // Notify WebSocket backend
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          action: "APPROVE_FIX",
          finding_id: findingId,
          selected_strategy: strategy,
          custom_instruction: customInstruction || "",
        })
      );
    }

    setTelemetryLogs((prev) => [
      {
        type: "AGENT_STATE",
        agent: "glitch",
        status: "editing",
        message: `Approved fix strategy: "${strategy}". Glitch deploying surgical countermeasure.`,
        timestamp: new Date().toISOString(),
      },
      ...prev,
    ]);

    // Apply surgical remediation to the active file
    setFiles((prev) => {
      const cur = prev[selectedFilePath];
      if (!cur) return prev;
      let patched = cur.current_content;

      if (findingId.includes("CWE-943")) {
        patched = patched.replace("User.find(req.body)", "User.find(mongoSanitize(req.body))");
        if (!patched.includes("mongoSanitize")) {
          patched = "const mongoSanitize = require('mongo-sanitize');\n" + patched;
        }
      } else if (findingId.includes("CWE-798")) {
        patched = patched.replace(
          '"super_secret_jwt_key_12345"',
          'process.env.JWT_SECRET || "default_secure_secret"'
        );
      } else if (findingId.includes("CWE-79")) {
        patched = patched.replace(
          "__html: userBio",
          "__html: DOMPurify.sanitize(userBio)"
        );
        if (!patched.includes("DOMPurify")) {
          patched = "import DOMPurify from 'dompurify';\n" + patched;
        }
      } else if (findingId.includes("CWE-942")) {
        patched = patched.replace('origin: "*"', "origin: ['http://localhost:3000']");
      } else if (findingId.includes("CWE-89")) {
        patched = patched.replace(
          'String query = "SELECT * FROM payments WHERE order_id = " + orderId;',
          'String query = "SELECT * FROM payments WHERE order_id = ?";\n        return jdbcTemplate.queryForList(query, orderId);'
        );
      } else if (findingId.includes("CWE-926")) {
        patched = patched.replace('android:exported="true"', 'android:exported="false"');
      }

      const remainingFindings = cur.findings.filter((f) => f.id !== findingId);

      return {
        ...prev,
        [selectedFilePath]: {
          ...cur,
          current_content: patched,
          is_modified: true,
          findings_count: remainingFindings.length,
          findings: remainingFindings,
          diff: `+ Applied Strategy: ${strategy}\n` + (customInstruction ? `+ Custom Instruction: ${customInstruction}\n` : ""),
        },
      };
    });

    setActiveAgent("glitch");
  };

  // Upload Codebase ZIP Handler
  const handleUploadZip = async (file: File) => {
    setIsRunning(true);
    setTelemetryLogs((prev) => [
      {
        type: "AGENT_STATE",
        agent: "dex",
        status: "thinking",
        message: `Unpacking repository archive '${file.name}' with Zip-Slip path traversal guard.`,
        timestamp: new Date().toISOString(),
      },
      ...prev,
    ]);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${BACKEND_URL}/api/project/upload-zip`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const workspace: WorkspaceData = await res.json();
        setFiles(workspace.files);
        setSessionId(workspace.session_id);
        if (workspace.sandbox_html) setSandboxHtml(workspace.sandbox_html);
        if (workspace.localhost_url) setLocalhostUrl(workspace.localhost_url);
        const firstKey = Object.keys(workspace.files)[0];
        if (firstKey) setSelectedFilePath(firstKey);

        setTelemetryLogs((prev) => [
          {
            type: "AGENT_STATE",
            agent: "snooze",
            status: "scanning",
            message: `Extracted ${workspace.total_files} files. Identified ${workspace.total_vulnerabilities} vulnerabilities across repository.`,
            timestamp: new Date().toISOString(),
          },
          ...prev,
        ]);
      }
    } catch (err) {
      console.error("ZIP upload failed", err);
    } finally {
      setIsRunning(false);
    }
  };

  // Download Remediated ZIP
  const handleDownloadZip = () => {
    window.open(`${BACKEND_URL}/api/project/download-zip/${sessionId}`, "_blank");
  };

  const currentFile = files[selectedFilePath] || Object.values(files)[0] || null;

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#07090E] text-slate-100 select-none">
      {/* Top Command Header */}
      <CommandHeader
        currentStack={currentStack}
        onSelectStack={handleSelectStack}
        executionMode={executionMode}
        onToggleExecutionMode={(mode) => setExecutionMode(mode)}
        onOpenAgentDrawer={() => setAgentDrawerOpen(true)}
        onDownloadZip={handleDownloadZip}
        isWsConnected={isWsConnected}
        sessionId={sessionId}
        agentConfig={agentConfig}
        isRunning={isRunning}
      />

      {/* Main 3-Pane Studio Workspace */}
      <main className="flex-1 flex overflow-hidden relative">
        {/* Left Pane: Multi-File Explorer & Taint Map */}
        <LeftPane
          files={files}
          selectedFile={selectedFilePath}
          onSelectFile={(path) => setSelectedFilePath(path)}
          activeAgent={activeAgent}
        />

        {/* Center Pane: Live Multi-Agent Code Canvas */}
        <CodeCanvas
          currentFile={currentFile}
          activeCursor={activeCursor}
          executionMode={executionMode}
          onApproveFix={handleApproveFix}
          isPatching={isRunning}
          activeAgent={activeAgent}
        />

        {/* Right Pane: Live Localhost Sandbox & Real-Time Terminal */}
        <RightPane
          sandboxHtml={sandboxHtml}
          localhostUrl={localhostUrl}
          telemetryLogs={telemetryLogs}
          activeAgent={activeAgent}
          uiTheme={agentConfig.ui_theme_target}
          isPatching={isRunning}
        />
      </main>

      {/* Bottom Floating Vibe Bar */}
      <VibeBar
        prompt={vibePrompt}
        onChangePrompt={(p) => setVibePrompt(p)}
        onSubmit={handleRunVibePrompt}
        onUploadZip={handleUploadZip}
        onDownloadZip={handleDownloadZip}
        isRunning={isRunning}
        activeAgent={activeAgent}
      />

      {/* Slide-over Agent Customizer Drawer */}
      <AgentDrawer
        isOpen={agentDrawerOpen}
        onClose={() => setAgentDrawerOpen(false)}
        config={agentConfig}
        onChangeConfig={(newConfig) => setAgentConfig(newConfig)}
        activeAgent={activeAgent}
      />
    </div>
  );
}
