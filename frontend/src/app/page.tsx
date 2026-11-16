"use client";

import { useState, useEffect, useRef } from "react";

const BACKEND_URL = "http://localhost:8000";

interface DiffItem {
  type: "removed" | "added";
  code: string;
  reason: string;
}

interface TimelineStep {
  id: string;
  agent: string;
  role: string;
  model: string;
  tier: string;
  thought: string;
  details: any;
}

interface PipelineResponse {
  session_id: string;
  prompt: string;
  timeline: TimelineStep[];
  initial_code: string;
  final_code: string;
  sandbox_html?: string;
  patch_diff: string;
  patch_explanation: string;
  diff_items?: DiffItem[];
  is_secure: boolean;
  findings: any[];
  models_used: string[];
}

// The 4 Hero Robot Crew Members
const CREW = [
  {
    id: "architect",
    name: "Dex",
    title: "The Hoodie Hacker",
    tagline: "Strategic Architect",
    color: "cyan",
    accentBg: "from-cyan-500/20 to-blue-500/10",
    borderActive: "border-cyan-400 shadow-cyan-500/30",
    textCol: "text-cyan-400",
    soundEffect: "*HACKING PERIMETER*",
    quote: "Yo! Pulling up my hoodie. Calculating zero-trust boundaries so hackers cry.",
    avatar: (
      <div className="relative w-16 h-16 flex items-center justify-center animate-bob">
        <div className="w-14 h-14 rounded-2xl bg-slate-900 border-2 border-cyan-400 shadow-lg shadow-cyan-500/30 flex flex-col items-center justify-center relative overflow-hidden">
          <div className="absolute top-0 inset-x-0 h-4 bg-cyan-950/80 border-b border-cyan-500/40 rounded-t-xl" />
          <div className="flex gap-2 items-center mt-2 z-10">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
          </div>
          <div className="w-7 h-1 bg-cyan-300 rounded-full mt-1.5 shadow-sm shadow-cyan-400" />
          <div className="absolute bottom-1 left-3 w-0.5 h-3 bg-cyan-400 rounded-full" />
          <div className="absolute bottom-1 right-3 w-0.5 h-3 bg-cyan-400 rounded-full" />
        </div>
        <span className="absolute -top-1.5 -right-1.5 text-xs bg-cyan-500 text-slate-950 px-1 py-0.2 rounded font-black font-mono">
          CAP
        </span>
      </div>
    ),
  },
  {
    id: "developer",
    name: "Pixel",
    title: "Juice-Box Coder",
    tagline: "OmniRoute Builder",
    color: "amber",
    accentBg: "from-amber-500/20 to-orange-500/10",
    borderActive: "border-amber-400 shadow-amber-500/30",
    textCol: "text-amber-400",
    soundEffect: "*SLURP*",
    quote: "Slurrrp! 🧃 OmniRoute routed me to DeepSeek! Typing at 260 WPM, let's ship it!",
    avatar: (
      <div className="relative w-16 h-16 flex items-center justify-center animate-juice">
        <div className="w-14 h-14 rounded-2xl bg-slate-900 border-2 border-amber-400 shadow-lg shadow-amber-500/30 flex flex-col items-center justify-center relative">
          <div className="flex gap-2.5 items-center">
            <span className="w-2.5 h-3 rounded-full bg-amber-300 transform scale-y-110" />
            <span className="w-2.5 h-3 rounded-full bg-amber-300 transform scale-y-110" />
          </div>
          <span className="text-[10px] text-amber-200 font-bold mt-0.5">ᴗ</span>
          <div className="absolute -bottom-1 -right-2 w-5 h-6 bg-rose-500 rounded border border-rose-300 flex items-center justify-center text-[7px] font-black text-white shadow">
            🧃
          </div>
        </div>
      </div>
    ),
  },
  {
    id: "auditor",
    name: "Snooze",
    title: "Sleepy-Head Auditor",
    tagline: "Vulnerability Hunter",
    color: "purple",
    accentBg: "from-purple-500/20 to-violet-500/10",
    borderActive: "border-purple-400 shadow-purple-500/30",
    textCol: "text-purple-400",
    soundEffect: "*LASER SCAN*",
    quote: "Yaaawn... 💤 Wait! *beep* My sleepy laser eye caught a security vulnerability!",
    avatar: (
      <div className="relative w-16 h-16 flex items-center justify-center animate-bob">
        <div className="absolute -top-3 right-0 text-[10px] font-bold text-purple-300 animate-zzz">
          Zzz
        </div>
        <div className="w-14 h-14 rounded-full bg-slate-900 border-2 border-purple-400 shadow-lg shadow-purple-500/30 flex flex-col items-center justify-center relative">
          <div className="absolute -top-2 left-2 w-5 h-4 bg-purple-600 rounded-t-full rotate-12 border border-purple-300" />
          <div className="flex gap-2 items-center mt-1">
            <span className="w-3 h-1 bg-purple-300 rounded-full" />
            <span className="w-3 h-1 bg-purple-300 rounded-full" />
          </div>
          <div className="w-2 h-2 rounded-full bg-rose-500 animate-ping mt-1.5" />
        </div>
      </div>
    ),
  },
  {
    id: "patcher",
    name: "Glitch",
    title: "The Dancing Patcher",
    tagline: "Remediation Dancer",
    color: "pink",
    accentBg: "from-pink-500/20 to-fuchsia-500/10",
    borderActive: "border-pink-400 shadow-pink-500/30",
    textCol: "text-pink-400",
    soundEffect: "*DISCO BEAT*",
    quote: "Ayyy! Break it down, fix it up! 🕺 Swapping the risky code for the secure groove!",
    avatar: (
      <div className="relative w-16 h-16 flex items-center justify-center animate-dance">
        <div className="w-14 h-14 rounded-2xl bg-slate-900 border-2 border-pink-500 shadow-lg shadow-pink-500/40 flex flex-col items-center justify-center relative">
          <div className="w-10 h-3 bg-pink-500 rounded-sm flex items-center justify-center shadow">
            <div className="w-8 h-1 bg-slate-950" />
          </div>
          <div className="w-4 h-1.5 bg-yellow-400 rounded-b-full mt-1.5" />
          <div className="absolute -bottom-1 -left-2 text-xs">🔧</div>
          <div className="absolute -top-2 -right-1 text-xs">✨</div>
        </div>
      </div>
    ),
  },
];

const FUN_PROMPT_SUGGESTIONS = [
  "Build an interactive retro arcade Snake Game with high-score tracking",
  "Build an interactive portfolio website for a senior software developer",
  "Create an authentication service with JWT and password hashing",
  "Write a safe user lookup query_user(id) protected against SQL injection",
];

export default function GameStudioSentinel() {
  const [prompt, setPrompt] = useState<string>(FUN_PROMPT_SUGGESTIONS[1]);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [activeAgentIndex, setActiveAgentIndex] = useState<number>(0);
  const [screenRumble, setScreenRumble] = useState<boolean>(false);
  const [pipelineData, setPipelineData] = useState<PipelineResponse | null>(null);
  const [viewMode, setViewMode] = useState<"sandbox" | "code">("sandbox");
  const [deviceMode, setDeviceMode] = useState<"desktop" | "mobile">("desktop");
  const [copiedCode, setCopiedCode] = useState<boolean>(false);
  const [iframeKey, setIframeKey] = useState<number>(0);

  const stageRef = useRef<HTMLDivElement>(null);

  const triggerRumble = () => {
    setScreenRumble(true);
    setTimeout(() => setScreenRumble(false), 380);
  };

  const handleLaunchPipeline = async () => {
    if (!prompt.trim() || isRunning) return;
    setIsRunning(true);
    setPipelineData(null);
    setActiveAgentIndex(0);

    triggerRumble();
    stageRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });

    try {
      const res = await fetch(`${BACKEND_URL}/api/pipeline`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });

      if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
      const data: PipelineResponse = await res.json();
      setPipelineData(data);

      for (let i = 0; i < CREW.length; i++) {
        setActiveAgentIndex(i);
        triggerRumble();
        await new Promise((resolve) => setTimeout(resolve, 1100));
      }
      setActiveAgentIndex(1); // highlight Pixel or Glitch
    } catch (err: any) {
      alert("Error contacting Sentinel: " + err.message);
    } finally {
      setIsRunning(false);
    }
  };

  const currentHero = CREW[activeAgentIndex];

  return (
    <div
      className={`min-h-screen text-slate-100 flex flex-col font-sans transition-all duration-300 animate-cyber-grid ${
        screenRumble ? "animate-screen-shake" : ""
      }`}
    >
      {/* Background Dynamic Ambient Glow */}
      <div
        className={`fixed inset-0 pointer-events-none opacity-20 transition-all duration-700 bg-radial ${
          activeAgentIndex === 0
            ? "from-cyan-600/30 via-transparent to-transparent"
            : activeAgentIndex === 1
            ? "from-amber-500/30 via-transparent to-transparent"
            : activeAgentIndex === 2
            ? "from-purple-600/30 via-transparent to-transparent"
            : "from-pink-600/30 via-transparent to-transparent"
        }`}
      />

      {/* Header */}
      <header className="relative z-10 px-6 py-4 flex items-center justify-between border-b border-slate-800/80 bg-slate-950/70 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-pink-500 via-amber-400 to-cyan-400 flex items-center justify-center text-xl shadow-lg shadow-pink-500/20 animate-bob">
            🤖
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-black tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-amber-300 to-pink-400 text-lg">
                SENTINEL STUDIO
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                LIVE SANDBOX READY
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Interactive Google AI Studio / Replit-Style Live Preview Runtime
            </p>
          </div>
        </div>

        {/* Crew Switcher */}
        <div className="hidden sm:flex items-center gap-2">
          {CREW.map((bot, idx) => (
            <button
              key={bot.id}
              onClick={() => setActiveAgentIndex(idx)}
              className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all flex items-center gap-1.5 ${
                activeAgentIndex === idx
                  ? `bg-slate-800 border-white text-white shadow-lg shadow-${bot.color}-500/30 scale-105`
                  : "bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              <span>{bot.name}</span>
            </button>
          ))}
        </div>
      </header>

      {/* Main Single-Page Stage */}
      <main className="relative z-10 flex-1 max-w-5xl w-full mx-auto px-6 py-8 flex flex-col gap-8">
        {/* 1. Prompt Command Bar */}
        <section className="flex flex-col items-center text-center gap-4">
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-white">
            What are we building today?
          </h1>
          <p className="text-sm text-slate-400 max-w-lg">
            Type anything. Sentinel architects the rules, writes the code, scans for flaws, and
            launches a <strong>live interactive sandbox you can play and use!</strong>
          </p>

          <div className="w-full max-w-2xl bg-slate-900/90 border-2 border-slate-700/80 rounded-3xl p-4 shadow-2xl flex flex-col gap-3 focus-within:border-cyan-400 transition-all">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={2}
              placeholder="e.g. Build an interactive portfolio website for a software developer..."
              className="w-full bg-transparent font-medium text-sm text-white placeholder:text-slate-500 focus:outline-none resize-none leading-relaxed"
            />

            {/* Quick Suggestion Pills */}
            <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-800">
              <span className="text-[11px] text-slate-500 font-bold self-center">Try:</span>
              {FUN_PROMPT_SUGGESTIONS.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => setPrompt(s)}
                  className="text-[11px] px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                >
                  {s.slice(0, 38)}...
                </button>
              ))}
            </div>

            <div className="flex justify-end pt-1">
              <button
                onClick={handleLaunchPipeline}
                disabled={isRunning || !prompt.trim()}
                className={`py-3 px-8 rounded-2xl font-black text-sm tracking-wide transition-all shadow-xl flex items-center gap-2 ${
                  isRunning
                    ? "bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700"
                    : "bg-gradient-to-r from-pink-500 via-purple-500 to-cyan-500 hover:opacity-90 text-white shadow-pink-500/20 active:scale-95"
                }`}
              >
                {isRunning ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>The Bot Squad is Working...</span>
                  </>
                ) : (
                  <>
                    <span>🎮 Launch Bot Squad & Live Sandbox</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </section>

        {/* 2. LIVE BOT SQUAD SPOTLIGHT */}
        <section ref={stageRef} className="flex flex-col gap-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {CREW.map((bot, idx) => {
              const isActive = activeAgentIndex === idx;
              return (
                <div
                  key={bot.id}
                  onClick={() => setActiveAgentIndex(idx)}
                  className={`cursor-pointer p-4 rounded-3xl border-2 transition-all duration-300 flex flex-col items-center text-center relative overflow-hidden ${
                    isActive
                      ? `bg-slate-900 ${bot.borderActive} scale-105 shadow-2xl`
                      : "bg-slate-950/70 border-slate-800/80 opacity-60 hover:opacity-90"
                  }`}
                >
                  {isActive && (
                    <div className="absolute top-0 inset-x-0 h-16 bg-gradient-to-b from-white/10 to-transparent pointer-events-none" />
                  )}
                  <div className="my-2">{bot.avatar}</div>
                  <span className="font-black text-base text-white mt-1">{bot.name}</span>
                  <span className={`text-[11px] font-bold ${bot.textCol}`}>{bot.title}</span>
                  {isActive && (
                    <span className="mt-2 text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-white animate-bounce">
                      {bot.soundEffect}
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Active Bot Dialogue Card */}
          <div
            className={`p-5 rounded-3xl border-2 transition-all bg-gradient-to-r ${currentHero.accentBg} ${currentHero.borderActive} flex items-start gap-4`}
          >
            <div className="hidden sm:block shrink-0">{currentHero.avatar}</div>
            <div className="flex-1 flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-black uppercase tracking-wider text-slate-300">
                  {currentHero.name}&apos;s Live Broadcast:
                </span>
                <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-slate-900 border border-slate-800 text-slate-200">
                  OmniRoute Model Switching Active
                </span>
              </div>
              <p className="text-sm font-semibold text-white leading-relaxed italic">
                &ldquo;{currentHero.quote}&rdquo;
              </p>
            </div>
          </div>

          {/* 3. GOOGLE AI STUDIO / REPLIT STYLE LIVE INTERACTIVE SANDBOX */}
          {pipelineData && (
            <div className="flex flex-col gap-4">
              {/* Sandbox Top Control Bar */}
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setViewMode("sandbox")}
                    className={`px-4 py-2 rounded-xl text-xs font-black transition-all flex items-center gap-2 ${
                      viewMode === "sandbox"
                        ? "bg-emerald-600 text-white shadow-lg shadow-emerald-900/40"
                        : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
                    }`}
                  >
                    <span>🖥️ Live Sandbox Preview</span>
                    <span className="w-2 h-2 rounded-full bg-emerald-300 animate-pulse" />
                  </button>

                  <button
                    onClick={() => setViewMode("code")}
                    className={`px-4 py-2 rounded-xl text-xs font-black transition-all flex items-center gap-2 ${
                      viewMode === "code"
                        ? "bg-emerald-600 text-white shadow-lg shadow-emerald-900/40"
                        : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
                    }`}
                  >
                    <span>💻 Code & What Changed</span>
                  </button>
                </div>

                {viewMode === "sandbox" && (
                  <div className="flex items-center gap-2 text-xs">
                    {/* Device Switcher */}
                    <div className="flex bg-slate-900 p-1 rounded-xl border border-slate-800">
                      <button
                        onClick={() => setDeviceMode("desktop")}
                        className={`px-2.5 py-1 rounded-lg text-xs font-bold ${
                          deviceMode === "desktop"
                            ? "bg-slate-800 text-white shadow"
                            : "text-slate-400 hover:text-white"
                        }`}
                      >
                        🖥️ Desktop
                      </button>
                      <button
                        onClick={() => setDeviceMode("mobile")}
                        className={`px-2.5 py-1 rounded-lg text-xs font-bold ${
                          deviceMode === "mobile"
                            ? "bg-slate-800 text-white shadow"
                            : "text-slate-400 hover:text-white"
                        }`}
                      >
                        📱 Mobile
                      </button>
                    </div>

                    {/* Reload Sandbox */}
                    <button
                      onClick={() => setIframeKey((k) => k + 1)}
                      className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 transition"
                      title="Reload Sandbox"
                    >
                      🔄
                    </button>
                  </div>
                )}
              </div>

              {/* VIEW 1: LIVE INTERACTIVE SANDBOX PREVIEW */}
              {viewMode === "sandbox" && (
                <div className="flex flex-col items-center">
                  {/* Browser Chrome Window Mockup */}
                  <div
                    className={`w-full transition-all duration-300 rounded-3xl border-2 border-slate-700 bg-slate-950 shadow-2xl overflow-hidden flex flex-col ${
                      deviceMode === "mobile" ? "max-w-sm" : "max-w-full"
                    }`}
                  >
                    {/* Browser Address Bar */}
                    <div className="px-4 py-3 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-1.5">
                        <span className="w-3 h-3 rounded-full bg-rose-500/80" />
                        <span className="w-3 h-3 rounded-full bg-amber-500/80" />
                        <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
                      </div>

                      <div className="flex-1 max-w-md mx-auto bg-slate-950 px-3 py-1 rounded-lg border border-slate-800 text-[11px] font-mono text-slate-400 flex items-center justify-center gap-1.5">
                        <span className="text-emerald-400">🔒</span>
                        <span>https://sentinel-preview.local/app</span>
                      </div>

                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                        LIVE RUNTIME
                      </span>
                    </div>

                    {/* Interactive Sandboxed IFrame */}
                    <div className="w-full h-[480px] bg-slate-950">
                      <iframe
                        key={iframeKey}
                        title="Sentinel Live Application Sandbox"
                        srcDoc={
                          pipelineData.sandbox_html ||
                          "<html><body style='color:#fff;background:#000;display:flex;align-items:center;justify-center;height:100vh;font-family:sans-serif;'><h1>Live Sandbox Ready</h1></body></html>"
                        }
                        sandbox="allow-scripts allow-modals allow-forms allow-same-origin"
                        className="w-full h-full border-0"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* VIEW 2: CODE & WHAT CHANGED */}
              {viewMode === "code" && (
                <div className="space-y-4">
                  {/* What Changed & Why Cards */}
                  {pipelineData.diff_items && pipelineData.diff_items.length > 0 ? (
                    <div className="space-y-3">
                      {pipelineData.diff_items.map((item, idx) => (
                        <div
                          key={idx}
                          className={`p-4 rounded-2xl border-2 flex flex-col gap-2 ${
                            item.type === "removed"
                              ? "bg-rose-950/30 border-rose-500/50 text-rose-200"
                              : "bg-emerald-950/30 border-emerald-500/50 text-emerald-200"
                          }`}
                        >
                          <div className="flex items-center justify-between text-xs font-bold font-mono">
                            <span>
                              {item.type === "removed"
                                ? "🚨 SNOOZE FLAGGED RISKY CODE (REMOVED):"
                                : "✨ GLITCH DANCED & REPLACED WITH (ADDED):"}
                            </span>
                            <span className="uppercase">{item.type}</span>
                          </div>

                          <pre className="font-mono text-xs p-2.5 rounded-xl bg-slate-950/80 overflow-x-auto">
                            {item.code}
                          </pre>

                          <div className="text-xs flex items-center gap-1.5 font-sans font-medium text-slate-300">
                            <span className="text-amber-400 font-bold">💡 WHY:</span> {item.reason}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 rounded-2xl bg-emerald-950/20 border-2 border-emerald-500/40 text-xs text-emerald-300 flex items-center gap-3">
                      <span className="text-2xl animate-dance">🕺</span>
                      <div>
                        <span className="font-bold block text-sm text-emerald-200">
                          Pixel&apos;s code passed 100% on the first pass!
                        </span>
                        Dex&apos;s security invariants were respected during generation. No
                        vulnerabilities detected; zero patching needed!
                      </div>
                    </div>
                  )}

                  {/* Complete Synthesized Code Box */}
                  <div className="bg-slate-900 border-2 border-slate-800 rounded-3xl p-5 flex flex-col gap-3 shadow-2xl">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">📦</span>
                        <span className="text-sm font-black text-white">
                          Synthesized Application Code
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-mono">
                          Verified Safe
                        </span>
                      </div>

                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(pipelineData.final_code);
                          setCopiedCode(true);
                          setTimeout(() => setCopiedCode(false), 2000);
                        }}
                        className="px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition-colors flex items-center gap-1"
                      >
                        {copiedCode ? "✓ Copied!" : "📋 Copy Code"}
                      </button>
                    </div>

                    <pre className="p-4 bg-slate-950 rounded-2xl border border-slate-800 font-mono text-xs text-slate-200 overflow-x-auto whitespace-pre leading-relaxed max-h-96">
                      {pipelineData.final_code}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
