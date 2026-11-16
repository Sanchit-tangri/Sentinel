"use client";

import { useState, useEffect } from "react";

const BACKEND_URL = "http://localhost:8000";

const SAMPLE_SQLI = `def get_user_profile(user_id: int, db_connection):
    cursor = db_connection.cursor()
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()`;

const SAMPLE_CMDI = `import os

def ping_server(host: str):
    # Vulnerable to command injection
    cmd = "ping -c 1 " + host
    os.system(cmd)`;

const SAMPLE_EVAL = `def calculate_user_expression(expr: str):
    # Insecure code execution
    return eval(expr)`;

export default function SentinelDashboard() {
  const [activeTab, setActiveTab] = useState<"remediate" | "generate" | "rag">("remediate");
  const [serverHealth, setServerHealth] = useState<{
    status: string;
    omniroute_active_model: string;
    simulation_mode: boolean;
  } | null>(null);

  // Remediation Lab state
  const [inputCode, setInputCode] = useState<string>(SAMPLE_SQLI);
  const [isAuditing, setIsAuditing] = useState<boolean>(false);
  const [isRemediating, setIsRemediating] = useState<boolean>(false);
  const [auditResult, setAuditResult] = useState<any>(null);
  const [remediationResult, setRemediationResult] = useState<any>(null);

  // Generation Lab state
  const [genPrompt, setGenPrompt] = useState<string>(
    "Write a secure function to fetch user profile by ID using parameterized database queries."
  );
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [genResult, setGenResult] = useState<any>(null);

  // RAG Search state
  const [ragQuery, setRagQuery] = useState<string>("SQL Injection CWE-89");
  const [isSearchingRag, setIsSearchingRag] = useState<boolean>(false);
  const [ragResults, setRagResults] = useState<any[]>([]);

  // Check backend health on mount
  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/health`);
      if (res.ok) {
        const data = await res.json();
        setServerHealth(data);
      } else {
        setServerHealth(null);
      }
    } catch {
      setServerHealth(null);
    }
  };

  const handleAudit = async () => {
    setIsAuditing(true);
    setAuditResult(null);
    try {
      const res = await fetch(`${BACKEND_URL}/api/audit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: inputCode, filename: "module.py" }),
      });
      const data = await res.json();
      setAuditResult(data);
    } catch (err: any) {
      alert("Failed to connect to backend: " + err.message);
    } finally {
      setIsAuditing(false);
    }
  };

  const handleRemediate = async () => {
    setIsRemediating(true);
    setRemediationResult(null);
    try {
      const res = await fetch(`${BACKEND_URL}/api/remediate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: inputCode, filename: "module.py" }),
      });
      const data = await res.json();
      setRemediationResult(data);
      checkHealth();
    } catch (err: any) {
      alert("Failed to connect to backend: " + err.message);
    } finally {
      setIsRemediating(false);
    }
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    setGenResult(null);
    try {
      const res = await fetch(`${BACKEND_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: genPrompt }),
      });
      const data = await res.json();
      setGenResult(data);
      checkHealth();
    } catch (err: any) {
      alert("Failed to connect to backend: " + err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSearchRag = async () => {
    setIsSearchingRag(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/rag/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: ragQuery, top_k: 5 }),
      });
      const data = await res.json();
      setRagResults(data.results || []);
    } catch (err: any) {
      alert("Failed to connect to backend: " + err.message);
    } finally {
      setIsSearchingRag(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold text-lg">
            🛡️
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white">SENTINEL</h1>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-950 border border-emerald-800 text-emerald-300 font-mono">
                v0.3.0
              </span>
            </div>
            <p className="text-xs text-slate-400">Autonomous Multi-Agent Security & OmniRoute Gateway</p>
          </div>
        </div>

        {/* System & OmniRoute Status Badges */}
        <div className="flex items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700">
            <span
              className={`w-2 h-2 rounded-full ${
                serverHealth ? "bg-emerald-400 animate-pulse" : "bg-rose-500"
              }`}
            />
            <span className="text-slate-300">
              Backend: {serverHealth ? "Online (Port 8000)" : "Offline"}
            </span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700">
            <span className="text-indigo-400 font-semibold">OmniRoute:</span>
            <span className="text-slate-300">
              {serverHealth?.omniroute_active_model || "standby"}
            </span>
            {serverHealth?.simulation_mode && (
              <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/40">
                Simulation
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b border-slate-800 bg-slate-900/40 px-6 flex gap-4 text-sm font-medium">
        <button
          onClick={() => setActiveTab("remediate")}
          className={`py-3 border-b-2 transition-colors ${
            activeTab === "remediate"
              ? "border-emerald-400 text-emerald-300"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Iterative Remediation Lab
        </button>
        <button
          onClick={() => setActiveTab("generate")}
          className={`py-3 border-b-2 transition-colors ${
            activeTab === "generate"
              ? "border-emerald-400 text-emerald-300"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          OmniRoute Code Synthesis
        </button>
        <button
          onClick={() => setActiveTab("rag")}
          className={`py-3 border-b-2 transition-colors ${
            activeTab === "rag"
              ? "border-emerald-400 text-emerald-300"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Episodic RAG Memory
        </button>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
        {/* TAB 1: REMEDIATION LAB */}
        {activeTab === "remediate" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Input Code & Samples */}
            <div className="flex flex-col gap-4 bg-slate-900 border border-slate-800 rounded-xl p-5">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <span>Target Vulnerable Code</span>
                  <span className="text-xs font-normal text-slate-400 font-mono">module.py</span>
                </h2>
                {/* Sample Snippet Buttons */}
                <div className="flex items-center gap-1.5 text-xs">
                  <span className="text-slate-400 text-[11px] mr-1">Load sample:</span>
                  <button
                    onClick={() => setInputCode(SAMPLE_SQLI)}
                    className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
                  >
                    SQLi
                  </button>
                  <button
                    onClick={() => setInputCode(SAMPLE_CMDI)}
                    className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
                  >
                    Cmdi
                  </button>
                  <button
                    onClick={() => setInputCode(SAMPLE_EVAL)}
                    className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
                  >
                    Eval
                  </button>
                </div>
              </div>

              <textarea
                value={inputCode}
                onChange={(e) => setInputCode(e.target.value)}
                className="w-full h-80 bg-slate-950 border border-slate-800 rounded-lg p-3 font-mono text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50"
                placeholder="Paste Python code here..."
              />

              <div className="flex items-center gap-3">
                <button
                  onClick={handleAudit}
                  disabled={isAuditing}
                  className="flex-1 py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition-colors border border-slate-700"
                >
                  {isAuditing ? "Auditing Code..." : "1. Run Security Audit Only"}
                </button>
                <button
                  onClick={handleRemediate}
                  disabled={isRemediating}
                  className="flex-1 py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-emerald-900/30 transition-colors"
                >
                  {isRemediating
                    ? "Remediating with Agents..."
                    : "2. Autonomous Self-Healing Loop"}
                </button>
              </div>

              {/* Auditor Findings Panel */}
              {auditResult && (
                <div className="mt-2 p-4 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-300">Auditor Report</span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded font-mono ${
                        auditResult.is_secure
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : "bg-rose-950 text-rose-400 border border-rose-800"
                      }`}
                    >
                      {auditResult.is_secure ? "SECURE (0 FINDINGS)" : "VULNERABILITIES FOUND"}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mb-3">{auditResult.summary}</p>

                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {auditResult.findings?.map((f: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded bg-slate-900 border border-rose-900/40 text-xs flex flex-col gap-1"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-rose-300">{f.title}</span>
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-950 text-rose-400 font-mono">
                            {f.cwe_id}
                          </span>
                        </div>
                        <div className="font-mono text-[11px] text-slate-400">
                          Line {f.line_number}: <code className="text-slate-200">{f.snippet}</code>
                        </div>
                        <div className="text-[11px] text-slate-500">
                          Recommendation: {f.recommendation}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right: Orchestrator Loop & Patch Diff */}
            <div className="flex flex-col gap-4 bg-slate-900 border border-slate-800 rounded-xl p-5">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-200">
                  Self-Healing Loop Output & Diff
                </h2>
                {remediationResult && (
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-mono ${
                      remediationResult.is_secure
                        ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                        : "bg-amber-950 text-amber-400 border border-amber-800"
                    }`}
                  >
                    {remediationResult.is_secure
                      ? `Resolved in ${remediationResult.total_iterations} iteration(s)`
                      : "Unresolved"}
                  </span>
                )}
              </div>

              {!remediationResult ? (
                <div className="flex-1 flex flex-col items-center justify-center p-12 text-center text-slate-500 border border-dashed border-slate-800 rounded-lg">
                  <span className="text-3xl mb-2">⚡</span>
                  <p className="text-xs">
                    Click &ldquo;Autonomous Self-Healing Loop&rdquo; to trigger the
                    Architect → Auditor → Patcher → RAG pipeline.
                  </p>
                </div>
              ) : (
                <div className="space-y-4 flex-1 flex flex-col">
                  {/* Context Remembrance & Model Metadata Card */}
                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono grid grid-cols-2 gap-2">
                    <div>
                      <span className="text-slate-500">Session ID:</span>{" "}
                      <span className="text-slate-300">{remediationResult.session_id}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Active Model:</span>{" "}
                      <span className="text-indigo-400 font-semibold">
                        {remediationResult.final_model || "Heuristic Fallback"}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">Model History:</span>{" "}
                      <span className="text-slate-300">
                        {remediationResult.model_history?.length > 0
                          ? remediationResult.model_history.join(" → ")
                          : "Single Model"}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">RAG Ingestion:</span>{" "}
                      <span className="text-emerald-400">Persisted to Vector Store</span>
                    </div>
                  </div>

                  {/* Unified Diff */}
                  {remediationResult.history?.[0]?.patch_diff && (
                    <div className="flex-1 flex flex-col">
                      <span className="text-xs font-semibold text-slate-400 mb-1.5">
                        Generated Unified Diff:
                      </span>
                      <pre className="p-3 bg-slate-950 border border-slate-800 rounded-lg font-mono text-[11px] text-slate-300 overflow-x-auto whitespace-pre">
                        {remediationResult.history[0].patch_diff}
                      </pre>
                    </div>
                  )}

                  {/* Final Patched Code */}
                  <div className="flex-1 flex flex-col">
                    <span className="text-xs font-semibold text-emerald-400 mb-1.5">
                      Final Verified Secure Code:
                    </span>
                    <pre className="p-3 bg-slate-950 border border-emerald-900/40 rounded-lg font-mono text-[11px] text-emerald-200 overflow-x-auto whitespace-pre max-h-60">
                      {remediationResult.final_code}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: GENERATION LAB */}
        {activeTab === "generate" && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-4xl mx-auto space-y-5">
            <div>
              <h2 className="text-base font-semibold text-white mb-1">
                OmniRoute Defensive Code Synthesis
              </h2>
              <p className="text-xs text-slate-400">
                Generates new code conforming to strict Architect security invariants, verified by
                DriftGuard to prevent hallucinated imports and symbol mutations.
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-300">Feature Specification / Task Prompt:</label>
              <textarea
                value={genPrompt}
                onChange={(e) => setGenPrompt(e.target.value)}
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500/50"
              />
            </div>

            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="py-2.5 px-5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-indigo-900/30 transition-colors"
            >
              {isGenerating ? "Synthesizing with OmniRoute..." : "Synthesize Defensive Code"}
            </button>

            {genResult && (
              <div className="space-y-4 pt-4 border-t border-slate-800">
                {/* Telemetry card */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono p-3 bg-slate-950 rounded-lg border border-slate-800">
                  <div>
                    <span className="text-slate-500">Model:</span>{" "}
                    <span className="text-indigo-400">{genResult.model_used}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Tier:</span>{" "}
                    <span className="text-slate-300">{genResult.tier}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Latency:</span>{" "}
                    <span className="text-slate-300">{genResult.latency_ms}ms</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Drift Check:</span>{" "}
                    <span className="text-emerald-400">
                      {genResult.drift_report?.is_valid ? "Passed (No Drift)" : "Violations Detected"}
                    </span>
                  </div>
                </div>

                <div>
                  <span className="text-xs font-semibold text-slate-300 block mb-1.5">
                    Synthesized Python Implementation:
                  </span>
                  <pre className="p-4 bg-slate-950 border border-slate-800 rounded-lg font-mono text-xs text-slate-200 overflow-x-auto whitespace-pre">
                    {genResult.code}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: RAG MEMORY */}
        {activeTab === "rag" && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-4xl mx-auto space-y-5">
            <div>
              <h2 className="text-base font-semibold text-white mb-1">
                Episodic Self-Learning RAG Store
              </h2>
              <p className="text-xs text-slate-400">
                Query learned remediation patterns and verified surgical diffs stored during
                successful autonomous patching cycles.
              </p>
            </div>

            <div className="flex gap-3">
              <input
                type="text"
                value={ragQuery}
                onChange={(e) => setRagQuery(e.target.value)}
                placeholder="Query memories (e.g. CWE-89, SQL injection, eval)..."
                className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500/50"
              />
              <button
                onClick={handleSearchRag}
                disabled={isSearchingRag}
                className="py-2 px-5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg"
              >
                {isSearchingRag ? "Searching..." : "Search RAG"}
              </button>
            </div>

            <div className="space-y-3">
              {ragResults.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-lg">
                  No memories retrieved. Run the remediation loop to generate new lessons!
                </div>
              ) : (
                ragResults.map((item: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono space-y-2"
                  >
                    <div className="flex items-center justify-between text-emerald-400">
                      <span>Memory ID: {item.id}</span>
                      <span>{item.metadata?.cwe_id || "CWE"}</span>
                    </div>
                    <pre className="text-slate-300 whitespace-pre-wrap text-[11px] bg-slate-900 p-2.5 rounded border border-slate-800">
                      {item.document}
                    </pre>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
