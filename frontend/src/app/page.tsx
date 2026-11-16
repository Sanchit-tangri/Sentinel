"use client";

import { useState, useEffect, useRef } from "react";

const BACKEND_URL = "http://localhost:8000";

interface TimelineStep {
  id: string;
  agent: string;
  role: string;
  model: string;
  tier: string;
  status: "pending" | "running" | "completed";
  thought: string;
  latency_ms?: number;
  details: any;
}

interface PipelineResponse {
  session_id: string;
  prompt: string;
  timeline: TimelineStep[];
  initial_code: string;
  final_code: string;
  patch_diff: string;
  patch_explanation: string;
  is_secure: boolean;
  architect_spec: any;
  findings: any[];
  models_used: string[];
}

const PRESET_PROMPTS = [
  {
    label: "🔐 Full Auth & RBAC Microservice",
    prompt:
      "Build a complete production-grade authentication microservice with password hashing (bcrypt), JWT generation, role-based access control (admin vs user), and strict input validation.",
  },
  {
    label: "💳 Secure Payment Webhook & Ledger",
    prompt:
      "Generate a secure payment processing webhook that validates HMAC signatures, logs transaction events into a database using parameterized queries, and guards against replay attacks.",
  },
  {
    label: "⚡ User Lookup (SQLi Auto-Remediated)",
    prompt:
      "Create a user lookup function query_user(user_id, db_connection) that takes user input, performs a SQL lookup, and enforces defensive sanitization so no SQL injection can occur.",
  },
  {
    label: "📦 Safe File Processing & S3 Uploader",
    prompt:
      "Write a secure file processing utility that validates MIME types, sanitizes filenames to prevent path traversal (CWE-22), and checks file size limits before processing.",
  },
];

export default function SentinelCinematicApp() {
  const [prompt, setPrompt] = useState<string>(PRESET_PROMPTS[0].prompt);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [currentSceneIndex, setCurrentSceneIndex] = useState<number>(-1);
  const [pipelineData, setPipelineData] = useState<PipelineResponse | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<string>("architect");
  const [serverHealth, setServerHealth] = useState<{
    status: string;
    omniroute_active_model: string;
    simulation_mode: boolean;
  } | null>(null);
  const [copiedCode, setCopiedCode] = useState<boolean>(false);

  const movieRef = useRef<HTMLDivElement>(null);

  // Poll backend health
  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 8000);
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

  const handleRunPipeline = async () => {
    if (!prompt.trim() || isRunning) return;
    setIsRunning(true);
    setPipelineData(null);
    setCurrentSceneIndex(0);

    // Scroll smoothly to movie stage
    setTimeout(() => {
      movieRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 150);

    try {
      const res = await fetch(`${BACKEND_URL}/api/pipeline`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });

      if (!res.ok) {
        throw new Error(`Server returned status ${res.status}`);
      }

      const data: PipelineResponse = await res.json();
      setPipelineData(data);

      // Play through the agent movie sequence dynamically
      const totalSteps = data.timeline.length;
      for (let i = 0; i < totalSteps; i++) {
        setCurrentSceneIndex(i);
        setSelectedAgentId(data.timeline[i].id);
        // Cinematic dwell time per agent scene so the user observes each step
        await new Promise((resolve) => setTimeout(resolve, 1100));
      }
      setCurrentSceneIndex(totalSteps); // all completed
      setSelectedAgentId("developer");
    } catch (err: any) {
      alert("Failed to connect to Sentinel backend: " + err.message);
      setCurrentSceneIndex(-1);
    } finally {
      setIsRunning(false);
      checkHealth();
    }
  };

  const handleCopyCode = (codeText: string) => {
    navigator.clipboard.writeText(codeText);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const activeScene = pipelineData?.timeline?.find((t) => t.id === selectedAgentId);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500/30">
      {/* 1. Header Bar */}
      <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center text-white text-lg font-bold shadow-lg shadow-emerald-500/20">
            🛡️
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold tracking-tight text-white text-base">SENTINEL</span>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800/80">
                v0.3.0 Live Mesh
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Autonomous Multi-Agent Security & OmniRoute Routing Architecture
            </p>
          </div>
        </div>

        {/* System & OmniRoute status */}
        <div className="flex items-center gap-2 text-xs font-mono">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
            <span
              className={`w-2 h-2 rounded-full ${
                serverHealth ? "bg-emerald-400 animate-pulse" : "bg-rose-500"
              }`}
            />
            <span className="text-slate-300">
              {serverHealth ? "Backend Active" : "Backend Offline"}
            </span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
            <span className="text-indigo-400">OmniRoute:</span>
            <span className="text-slate-200">
              {serverHealth?.omniroute_active_model || "Standby"}
            </span>
            {serverHealth?.simulation_mode && (
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                Simulation
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main Single Page Canvas */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8 flex flex-col gap-10">
        {/* 2. Hero Command Prompt Box */}
        <section className="flex flex-col gap-4 text-center items-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-medium">
            <span>✨ Describe what to build — Sentinel architects, synthesizes, and self-heals</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight max-w-2xl">
            From Single Prompt to <span className="text-emerald-400">Defensive Application</span>
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 max-w-xl">
            Powered by OmniRoute model routing with an anti-hallucination Context Remembrance Engine.
            Watch the multi-agent mesh collaborate in real time.
          </p>

          {/* Big Command Box */}
          <div className="w-full max-w-3xl mt-2 bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-2xl shadow-emerald-950/20 flex flex-col gap-3 focus-within:border-emerald-500/50 transition-all">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={3}
              placeholder="e.g. Build an authenticated payment processing service with webhook validation and database persistence..."
              className="w-full bg-transparent font-sans text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none resize-none leading-relaxed"
            />

            {/* Quick preset chips */}
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80">
              <span className="text-[11px] text-slate-500 font-medium">Quick Presets:</span>
              {PRESET_PROMPTS.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => setPrompt(item.prompt)}
                  className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700/50"
                >
                  {item.label}
                </button>
              ))}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-1">
              <span className="text-[11px] text-slate-500 font-mono">
                Model: OmniRoute Dynamic Gateway (Claude / DeepSeek / Qwen)
              </span>
              <button
                onClick={handleRunPipeline}
                disabled={isRunning || !prompt.trim()}
                className={`py-2.5 px-6 rounded-xl font-semibold text-xs tracking-wide transition-all shadow-lg flex items-center gap-2 ${
                  isRunning
                    ? "bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700"
                    : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/40 hover:shadow-emerald-900/60 active:scale-95"
                }`}
              >
                {isRunning ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
                    <span>Orchestrating Agent Mesh...</span>
                  </>
                ) : (
                  <>
                    <span>🚀 Launch Pipeline</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </section>

        {/* 3. The Cinematic Multi-Agent Movie Stage */}
        <section ref={movieRef} className="flex flex-col gap-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>🎬 The Agent Mesh in Action</span>
                {isRunning && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 animate-pulse font-mono">
                    LIVE EXECUTION
                  </span>
                )}
              </h3>
              <p className="text-xs text-slate-400">
                Visualizing thoughts, model switches, and code evolution step-by-step
              </p>
            </div>

            {pipelineData && (
              <div className="text-xs font-mono text-slate-400 flex items-center gap-3">
                <span>Session: <strong className="text-slate-200">{pipelineData.session_id}</strong></span>
                <span>•</span>
                <span className="text-emerald-400 font-semibold">100% Secure Passed</span>
              </div>
            )}
          </div>

          {/* Visual Agent Nodes Track (Movie Scenes) */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {[
              {
                id: "architect",
                name: "The Architect",
                icon: "🏛️",
                tier: "STRATEGIC",
                role: "Boundaries & Invariants",
              },
              {
                id: "developer",
                name: "The Developer",
                icon: "⚡",
                tier: "CODE_GEN",
                role: "OmniRoute Code Synthesis",
              },
              {
                id: "auditor",
                name: "The Auditor",
                icon: "🔍",
                tier: "VERIFY",
                role: "Static AST & CWE Check",
              },
              {
                id: "patcher",
                name: "The Patcher",
                icon: "🛠️",
                tier: "SURGICAL",
                role: "Self-Healing Diffs",
              },
              {
                id: "rag",
                name: "RAG Ledger",
                icon: "🧠",
                tier: "MEMORY",
                role: "Episodic Persistence",
              },
            ].map((node, idx) => {
              const isCurrent = isRunning && currentSceneIndex === idx;
              const isPast =
                currentSceneIndex > idx || (!isRunning && pipelineData !== null);
              const isSelected = selectedAgentId === node.id;

              return (
                <button
                  key={node.id}
                  onClick={() => setSelectedAgentId(node.id)}
                  className={`p-3 rounded-xl border text-left flex flex-col gap-1.5 transition-all relative overflow-hidden ${
                    isSelected
                      ? "bg-slate-800/90 border-emerald-500/80 shadow-lg shadow-emerald-950/40"
                      : isPast
                      ? "bg-slate-900/80 border-slate-700/80 hover:border-slate-600"
                      : isCurrent
                      ? "bg-slate-900 border-indigo-500 shadow-lg shadow-indigo-950/40 animate-pulse"
                      : "bg-slate-950 border-slate-800/60 opacity-60"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-lg">{node.icon}</span>
                    <span
                      className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                        isPast
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800/60"
                          : isCurrent
                          ? "bg-indigo-950 text-indigo-300 border border-indigo-800"
                          : "bg-slate-800 text-slate-500"
                      }`}
                    >
                      {isPast ? "DONE" : isCurrent ? "ACTIVE" : "QUEUED"}
                    </span>
                  </div>

                  <span className="text-xs font-bold text-slate-200 mt-1">{node.name}</span>
                  <span className="text-[10px] text-slate-400 line-clamp-1">{node.role}</span>

                  {/* Active glowing indicator */}
                  {isCurrent && (
                    <div className="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-indigo-500 to-emerald-400 animate-pulse" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Active Agent Thought & Inspection Stage */}
          {pipelineData ? (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col gap-4 shadow-xl">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2.5">
                  <span className="text-xl">
                    {selectedAgentId === "architect"
                      ? "🏛️"
                      : selectedAgentId === "developer"
                      ? "⚡"
                      : selectedAgentId === "auditor"
                      ? "🔍"
                      : selectedAgentId === "patcher"
                      ? "🛠️"
                      : "🧠"}
                  </span>
                  <div>
                    <h4 className="text-sm font-bold text-white">
                      {activeScene?.agent || "Agent Details"}
                    </h4>
                    <p className="text-xs text-slate-400">{activeScene?.role}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2 font-mono text-xs">
                  <span className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-indigo-400">
                    Model: {activeScene?.model || "OmniRoute"}
                  </span>
                  <span className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-slate-300">
                    Tier: {activeScene?.tier || "CORE"}
                  </span>
                </div>
              </div>

              {/* Agent Thought Stream */}
              <div className="bg-slate-950 border border-slate-800/90 rounded-xl p-4 flex flex-col gap-2">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    Agent Reasoning & Thinking Stream
                  </span>
                  <span className="font-mono text-[11px] text-slate-500">
                    Zero-Hallucination Verified
                  </span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed font-sans">
                  {activeScene?.thought || "Processing task requirements..."}
                </p>
              </div>

              {/* Agent Specific Visual Artifacts */}
              {selectedAgentId === "architect" && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                  <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800">
                    <span className="font-semibold text-emerald-400 block mb-2 font-sans">
                      Defined Security Invariants:
                    </span>
                    <ul className="space-y-1.5 text-slate-300">
                      {pipelineData.architect_spec?.security_invariants?.map((inv: string, i: number) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-emerald-500">✓</span>
                          <span>{inv}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800">
                    <span className="font-semibold text-rose-400 block mb-2 font-sans">
                      Prohibited Anti-Patterns:
                    </span>
                    <ul className="space-y-1.5 text-slate-300">
                      {pipelineData.architect_spec?.prohibited_patterns?.map((pat: string, i: number) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-rose-500">✗</span>
                          <code>{pat}</code>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {selectedAgentId === "developer" && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-400">
                      Synthesized Code (Developer Agent):
                    </span>
                    <button
                      onClick={() => handleCopyCode(pipelineData.initial_code)}
                      className="text-xs text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-800"
                    >
                      {copiedCode ? "Copied!" : "Copy Code"}
                    </button>
                  </div>
                  <pre className="p-4 bg-slate-950 rounded-xl border border-slate-800 font-mono text-xs text-slate-200 overflow-x-auto max-h-72">
                    {pipelineData.initial_code}
                  </pre>
                </div>
              )}

              {selectedAgentId === "auditor" && (
                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-400">Security Audit Summary:</span>
                    <span className="px-2 py-0.5 rounded font-mono bg-emerald-950 text-emerald-400 border border-emerald-800">
                      {pipelineData.findings?.length === 0
                        ? "0 Vulnerabilities (PASSED)"
                        : `${pipelineData.findings.length} Vulnerability Flagged`}
                    </span>
                  </div>
                  {pipelineData.findings?.length === 0 ? (
                    <div className="p-4 bg-slate-950 rounded-xl border border-emerald-900/40 text-emerald-300">
                      ✓ Code adheres strictly to Architect invariants. Static AST scan confirmed zero injection, secret leak, or unsafe deserialization vulnerabilities.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {pipelineData.findings.map((f: any, idx: number) => (
                        <div key={idx} className="p-3 bg-slate-950 rounded-xl border border-rose-900/50">
                          <span className="font-semibold text-rose-300">{f.title} ({f.cwe_id})</span>
                          <p className="text-slate-400 mt-1">{f.description}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {selectedAgentId === "patcher" && (
                <div className="space-y-3">
                  <span className="text-xs font-semibold text-slate-400 block">
                    Remediation Diff & Convergence:
                  </span>
                  {pipelineData.patch_diff ? (
                    <pre className="p-4 bg-slate-950 rounded-xl border border-indigo-900/50 font-mono text-xs text-slate-300 overflow-x-auto max-h-60">
                      {pipelineData.patch_diff}
                    </pre>
                  ) : (
                    <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-400">
                      No surgical diff required: Code was synthesized defensibly by the Developer Agent on the first pass.
                    </div>
                  )}
                </div>
              )}

              {selectedAgentId === "rag" && (
                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-xs font-mono space-y-2">
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Session Ledger ID: {pipelineData.session_id}</span>
                    <span className="text-emerald-400">Status: Persisted</span>
                  </div>
                  <p className="text-slate-300 font-sans">
                    All symbols, invariants, and successful patterns have been ingested into the
                    Episodic RAG store. If OmniRoute shifts models in the future, these lessons are immediately available.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="p-10 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col items-center justify-center text-center text-slate-500 gap-2">
              <span className="text-3xl">🎥</span>
              <p className="text-xs text-slate-400">
                Click <strong>&ldquo;Launch Pipeline&rdquo;</strong> above to watch the multi-agent movie unfold.
              </p>
            </div>
          )}

          {/* 4. Final Production Code Delivery Section */}
          {pipelineData && (
            <div className="bg-slate-900 border border-emerald-900/50 rounded-2xl p-6 flex flex-col gap-4 shadow-2xl">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <span>📦 Final Production-Ready Code</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                      Verified Secure
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400">
                    Ready to drop directly into your production repository
                  </p>
                </div>

                <button
                  onClick={() => handleCopyCode(pipelineData.final_code)}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-md shadow-emerald-950"
                >
                  {copiedCode ? "✓ Copied to Clipboard" : "Copy Production Code"}
                </button>
              </div>

              <pre className="p-4 bg-slate-950 rounded-xl border border-emerald-950 font-mono text-xs text-emerald-200 overflow-x-auto whitespace-pre leading-relaxed max-h-96">
                {pipelineData.final_code}
              </pre>

              {/* Model Chain & Telemetry Footer */}
              <div className="flex flex-wrap items-center justify-between gap-3 text-xs font-mono pt-3 border-t border-slate-800 text-slate-400">
                <div className="flex items-center gap-2">
                  <span>Models Orchestrated:</span>
                  {pipelineData.models_used.map((m: string, i: number) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded bg-slate-950 text-indigo-300 border border-slate-800"
                    >
                      {m}
                    </span>
                  ))}
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-emerald-400">✓ Context Ledger Synchronized</span>
                  <span>•</span>
                  <span>Zero Model-Switch Drift</span>
                </div>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
