"use client";

import { useState, useRef } from "react";

const BACKEND_URL = "http://localhost:8000";

interface ProjectFile {
  path: string;
  original_content: string;
  current_content: string;
  is_modified: boolean;
  findings_count: number;
  diff: string;
  findings: any[];
}

interface WorkspaceData {
  session_id: string;
  project_name: string;
  files: Record<string, ProjectFile>;
  total_files: number;
  vulnerable_files_count: number;
  total_vulnerabilities: number;
  remediated_count: number;
  sandbox_html: string;
  localhost_url: string;
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
    soundEffect: "*MAPPING TOPOLOGY*",
    quote: "Scanning repository trust boundaries. Locking down multi-file attack surfaces.",
    avatar: (
      <div className="relative w-14 h-14 flex items-center justify-center animate-bob">
        <div className="w-12 h-12 rounded-2xl bg-slate-900 border-2 border-cyan-400 shadow-lg shadow-cyan-500/30 flex flex-col items-center justify-center relative overflow-hidden">
          <div className="absolute top-0 inset-x-0 h-3.5 bg-cyan-950/80 border-b border-cyan-500/40 rounded-t-xl" />
          <div className="flex gap-1.5 items-center mt-2 z-10">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
          </div>
          <div className="w-6 h-0.5 bg-cyan-300 rounded-full mt-1 shadow-sm shadow-cyan-400" />
        </div>
      </div>
    ),
  },
  {
    id: "developer",
    name: "Pixel",
    title: "Juice-Box Coder",
    tagline: "Fullstack Builder",
    color: "amber",
    accentBg: "from-amber-500/20 to-orange-500/10",
    borderActive: "border-amber-400 shadow-amber-500/30",
    textCol: "text-amber-400",
    soundEffect: "*SLURP*",
    quote: "Slurrrp! 🧃 OmniRoute routed! Synthesizing multi-file project files and live localhost!",
    avatar: (
      <div className="relative w-14 h-14 flex items-center justify-center animate-juice">
        <div className="w-12 h-12 rounded-2xl bg-slate-900 border-2 border-amber-400 shadow-lg shadow-amber-500/30 flex flex-col items-center justify-center relative">
          <div className="flex gap-2 items-center">
            <span className="w-2 h-2.5 rounded-full bg-amber-300" />
            <span className="w-2 h-2.5 rounded-full bg-amber-300" />
          </div>
          <span className="text-[9px] text-amber-200 font-bold mt-0.5">ᴗ</span>
          <div className="absolute -bottom-1 -right-1 text-xs">🧃</div>
        </div>
      </div>
    ),
  },
  {
    id: "auditor",
    name: "Snooze",
    title: "Sleepy Auditor",
    tagline: "Repo-Wide Scanner",
    color: "purple",
    accentBg: "from-purple-500/20 to-violet-500/10",
    borderActive: "border-purple-400 shadow-purple-500/30",
    textCol: "text-purple-400",
    soundEffect: "*SCANNING ALL FILES*",
    quote: "Yaaawn... 💤 Laser eyes scanning every route, query, and template across the repo!",
    avatar: (
      <div className="relative w-14 h-14 flex items-center justify-center animate-bob">
        <div className="absolute -top-2 right-0 text-[9px] font-bold text-purple-300 animate-zzz">Zzz</div>
        <div className="w-12 h-12 rounded-full bg-slate-900 border-2 border-purple-400 shadow-lg shadow-purple-500/30 flex flex-col items-center justify-center relative">
          <div className="flex gap-1.5 items-center mt-1">
            <span className="w-2.5 h-0.5 bg-purple-300 rounded-full" />
            <span className="w-2.5 h-0.5 bg-purple-300 rounded-full" />
          </div>
          <div className="w-2 h-2 rounded-full bg-rose-500 animate-ping mt-1" />
        </div>
      </div>
    ),
  },
  {
    id: "patcher",
    name: "Glitch",
    title: "Dancing Patcher",
    tagline: "Multi-File Fixer",
    color: "pink",
    accentBg: "from-pink-500/20 to-fuchsia-500/10",
    borderActive: "border-pink-400 shadow-pink-500/30",
    textCol: "text-pink-400",
    soundEffect: "*REMEDIATION DISCO*",
    quote: "Break it down! 🕺 Surgically patching files and packing a clean downloadable ZIP!",
    avatar: (
      <div className="relative w-14 h-14 flex items-center justify-center animate-dance">
        <div className="w-12 h-12 rounded-2xl bg-slate-900 border-2 border-pink-500 shadow-lg shadow-pink-500/40 flex flex-col items-center justify-center relative">
          <div className="w-8 h-2.5 bg-pink-500 rounded-sm flex items-center justify-center">
            <div className="w-6 h-0.5 bg-slate-950" />
          </div>
          <div className="w-3 h-1 bg-yellow-400 rounded-b-full mt-1" />
          <div className="absolute -bottom-1 -left-1 text-xs">🔧</div>
        </div>
      </div>
    ),
  },
];

export default function MultiFileSentinelStudio() {
  const [activeTab, setActiveTab] = useState<"generate" | "upload">("generate");
  const [prompt, setPrompt] = useState<string>(
    "Build a fullstack e-commerce application with product catalog, cart API, and PostgreSQL schema"
  );
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [workspace, setWorkspace] = useState<WorkspaceData | null>(null);
  const [selectedFile, setSelectedFile] = useState<string>("");
  const [viewMode, setViewMode] = useState<"sandbox" | "code">("sandbox");
  const [activeAgentIndex, setActiveAgentIndex] = useState<number>(0);
  const [screenRumble, setScreenRumble] = useState<boolean>(false);
  const [copiedCode, setCopiedCode] = useState<boolean>(false);
  const [dragOver, setDragOver] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);

  const triggerRumble = () => {
    setScreenRumble(true);
    setTimeout(() => setScreenRumble(false), 380);
  };

  const handleGenerateFullstack = async () => {
    if (!prompt.trim() || isRunning) return;
    setIsRunning(true);
    setWorkspace(null);
    triggerRumble();
    stageRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });

    try {
      // Animate bot squad working
      for (let i = 0; i < CREW.length; i++) {
        setActiveAgentIndex(i);
        await new Promise((r) => setTimeout(r, 650));
      }

      const res = await fetch(`${BACKEND_URL}/api/project/generate-fullstack`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
      const data: WorkspaceData = await res.json();
      setWorkspace(data);

      const firstKey = Object.keys(data.files)[0] || "";
      setSelectedFile(firstKey);
      triggerRumble();
    } catch (err: any) {
      alert("Error: " + err.message);
    } finally {
      setIsRunning(false);
    }
  };

  const handleZipUpload = async (file: File) => {
    if (!file || isRunning) return;
    setIsRunning(true);
    setWorkspace(null);
    triggerRumble();
    stageRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });

    const formData = new FormData();
    formData.append("file", file);

    try {
      for (let i = 0; i < CREW.length; i++) {
        setActiveAgentIndex(i);
        await new Promise((r) => setTimeout(r, 700));
      }

      const res = await fetch(`${BACKEND_URL}/api/project/upload-zip`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || `HTTP Error ${res.status}`);
      }

      const data: WorkspaceData = await res.json();
      setWorkspace(data);
      const firstKey = Object.keys(data.files)[0] || "";
      setSelectedFile(firstKey);
      triggerRumble();
    } catch (err: any) {
      alert("Upload failed: " + err.message);
    } finally {
      setIsRunning(false);
    }
  };

  const currentHero = CREW[activeAgentIndex];
  const activeFileObj = workspace && selectedFile ? workspace.files[selectedFile] : null;

  return (
    <div
      className={`min-h-screen text-slate-100 flex flex-col font-sans transition-all duration-300 animate-cyber-grid ${
        screenRumble ? "animate-screen-shake" : ""
      }`}
    >
      {/* Header */}
      <header className="relative z-10 px-6 py-4 flex items-center justify-between border-b border-slate-800/80 bg-slate-950/80 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-cyan-400 via-emerald-400 to-pink-500 flex items-center justify-center text-xl shadow-lg shadow-emerald-500/20 animate-bob">
            📦
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-amber-300 to-pink-400 text-lg">
                SENTINEL FULLSTACK STUDIO
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                MULTI-FILE + ZIP RUNTIME
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Autonomous Fullstack Multi-File Generator, Repo-Wide Scanner & Localhost Sandbox
            </p>
          </div>
        </div>

        {/* Download Remediated ZIP Button */}
        {workspace && (
          <a
            href={`${BACKEND_URL}/api/project/download-zip/${workspace.session_id}`}
            download
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-emerald-950 transition"
          >
            <span>⬇️ Download Fixed Project (.zip)</span>
          </a>
        )}
      </header>

      {/* Main Single-Page Canvas */}
      <main className="relative z-10 flex-1 max-w-5xl w-full mx-auto px-6 py-8 flex flex-col gap-8">
        {/* Mode Selector */}
        <section className="flex flex-col items-center text-center gap-4">
          <div className="flex bg-slate-900 p-1.5 rounded-2xl border border-slate-800 gap-2">
            <button
              onClick={() => setActiveTab("generate")}
              className={`px-5 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                activeTab === "generate"
                  ? "bg-emerald-600 text-white shadow-md shadow-emerald-900/40"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <span>⚡ Generate Fullstack App</span>
            </button>
            <button
              onClick={() => setActiveTab("upload")}
              className={`px-5 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                activeTab === "upload"
                  ? "bg-emerald-600 text-white shadow-md shadow-emerald-900/40"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <span>📁 Upload Existing Project (.ZIP)</span>
            </button>
          </div>

          {/* TAB 1: GENERATE FULLSTACK PROMPT */}
          {activeTab === "generate" && (
            <div className="w-full max-w-2xl bg-slate-900/90 border-2 border-slate-700/80 rounded-3xl p-4 shadow-2xl flex flex-col gap-3 focus-within:border-emerald-400 transition-all">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={2}
                placeholder="e.g. Build a fullstack e-commerce application with product catalog, cart API, and PostgreSQL schema..."
                className="w-full bg-transparent font-medium text-sm text-white placeholder:text-slate-500 focus:outline-none resize-none leading-relaxed"
              />

              <div className="flex justify-between items-center pt-1 border-t border-slate-800">
                <span className="text-[11px] font-mono text-slate-400">
                  Generates: backend/app.py • database/schema.sql • frontend/index.html • requirements.txt
                </span>
                <button
                  onClick={handleGenerateFullstack}
                  disabled={isRunning || !prompt.trim()}
                  className={`py-2.5 px-6 rounded-2xl font-bold text-xs tracking-wide transition shadow-lg flex items-center gap-2 ${
                    isRunning
                      ? "bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700"
                      : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/30 active:scale-95"
                  }`}
                >
                  {isRunning ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Bot Squad Generating Fullstack...</span>
                    </>
                  ) : (
                    <span>🚀 Generate Fullstack Project</span>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: UPLOAD ZIP FILE */}
          {activeTab === "upload" && (
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                if (e.dataTransfer.files?.[0]) handleZipUpload(e.dataTransfer.files[0]);
              }}
              className={`w-full max-w-2xl border-2 border-dashed rounded-3xl p-8 flex flex-col items-center justify-center text-center gap-3 transition-all ${
                dragOver
                  ? "border-emerald-400 bg-emerald-950/20 scale-102"
                  : "border-slate-700 bg-slate-900/80 hover:border-slate-600"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".zip"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files?.[0]) handleZipUpload(e.target.files[0]);
                }}
              />
              <span className="text-4xl animate-bounce">📦</span>
              <div>
                <h3 className="font-bold text-white text-base">
                  Drag and drop your project ZIP file here
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Sentinel will safely unpack, scan every file, remediate vulnerabilities, and simulate localhost!
                </p>
              </div>
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isRunning}
                className="mt-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs border border-slate-700 transition"
              >
                {isRunning ? "Scanning & Remediating..." : "Select .ZIP File from Computer"}
              </button>
            </div>
          )}
        </section>

        {/* 2. THE BOT SQUAD ARENA */}
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
                  <div className="my-1.5">{bot.avatar}</div>
                  <span className="font-black text-sm text-white mt-1">{bot.name}</span>
                  <span className={`text-[10px] font-bold ${bot.textCol}`}>{bot.title}</span>
                  {isActive && (
                    <span className="mt-1 text-[9px] font-mono px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-white animate-bounce">
                      {bot.soundEffect}
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Active Bot Dialogue Card */}
          <div
            className={`p-4 rounded-3xl border-2 transition-all bg-gradient-to-r ${currentHero.accentBg} ${currentHero.borderActive} flex items-center gap-4`}
          >
            <div className="hidden sm:block shrink-0">{currentHero.avatar}</div>
            <div className="flex-1">
              <span className="text-[10px] font-mono uppercase text-slate-400 block">
                {currentHero.name}&apos;s Live Broadcast:
              </span>
              <p className="text-xs font-semibold text-white italic mt-0.5">
                &ldquo;{currentHero.quote}&rdquo;
              </p>
            </div>
          </div>

          {/* 3. MULTI-FILE WORKSPACE & LOCALHOST SANDBOX */}
          {workspace && (
            <div className="flex flex-col gap-4">
              {/* Workspace Metrics Banner */}
              <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
                <div className="flex items-center gap-4">
                  <div>
                    <span className="text-slate-500">Project:</span>{" "}
                    <span className="text-white font-bold">{workspace.project_name}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Files:</span>{" "}
                    <span className="text-cyan-400 font-bold">{workspace.total_files}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Flaws Fixed:</span>{" "}
                    <span className="text-emerald-400 font-bold">
                      {workspace.remediated_count} / {workspace.total_vulnerabilities}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setViewMode("sandbox")}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                      viewMode === "sandbox"
                        ? "bg-emerald-600 text-white shadow"
                        : "bg-slate-800 text-slate-400 hover:text-white"
                    }`}
                  >
                    <span>🖥️ Localhost Sandbox</span>
                    <span className="w-2 h-2 rounded-full bg-emerald-300 animate-pulse" />
                  </button>

                  <button
                    onClick={() => setViewMode("code")}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
                      viewMode === "code"
                        ? "bg-emerald-600 text-white shadow"
                        : "bg-slate-800 text-slate-400 hover:text-white"
                    }`}
                  >
                    <span>📁 Project Files & Diffs</span>
                  </button>
                </div>
              </div>

              {/* VIEW 1: LOCALHOST SIMULATION SANDBOX */}
              {viewMode === "sandbox" && (
                <div className="rounded-3xl border-2 border-slate-700 bg-slate-950 shadow-2xl overflow-hidden flex flex-col">
                  {/* Browser Chrome Frame */}
                  <div className="px-4 py-3 bg-slate-900 border-b border-slate-800 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-1.5">
                      <span className="w-3 h-3 rounded-full bg-rose-500/80" />
                      <span className="w-3 h-3 rounded-full bg-amber-500/80" />
                      <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
                    </div>

                    <div className="flex-1 max-w-md mx-auto bg-slate-950 px-3 py-1 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 flex items-center justify-center gap-1.5">
                      <span className="text-emerald-400">🔒</span>
                      <span>http://localhost:8000</span>
                    </div>

                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                      LIVE LOCALHOST SIMULATOR
                    </span>
                  </div>

                  <div className="w-full h-[520px] bg-slate-950">
                    <iframe
                      title="Localhost Simulation Sandbox"
                      srcDoc={workspace.sandbox_html}
                      sandbox="allow-scripts allow-modals allow-forms allow-same-origin"
                      className="w-full h-full border-0"
                    />
                  </div>
                </div>
              )}

              {/* VIEW 2: MULTI-FILE EXPLORER & CODE DIFFS */}
              {viewMode === "code" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Left Sidebar: File Tree */}
                  <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col gap-1.5">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider px-2 py-1">
                      Project Files ({workspace.total_files})
                    </span>
                    <div className="space-y-1">
                      {Object.keys(workspace.files).map((filePath) => {
                        const file = workspace.files[filePath];
                        const isSelected = selectedFile === filePath;
                        return (
                          <button
                            key={filePath}
                            onClick={() => setSelectedFile(filePath)}
                            className={`w-full text-left px-3 py-2 rounded-xl text-xs font-mono flex items-center justify-between transition ${
                              isSelected
                                ? "bg-emerald-600 text-white font-bold"
                                : "text-slate-300 hover:bg-slate-800"
                            }`}
                          >
                            <span className="truncate">📄 {filePath}</span>
                            {file.is_modified && (
                              <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                                PATCHED
                              </span>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Right: Code Viewer & What Changed in this File */}
                  <div className="md:col-span-2 space-y-3">
                    {activeFileObj && (
                      <>
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-xs text-slate-300 font-bold">
                            Viewing: {activeFileObj.path}
                          </span>
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(activeFileObj.current_content);
                              setCopiedCode(true);
                              setTimeout(() => setCopiedCode(false), 2000);
                            }}
                            className="text-xs px-3 py-1 bg-slate-800 hover:bg-slate-700 text-white rounded-lg border border-slate-700 font-mono"
                          >
                            {copiedCode ? "✓ Copied" : "Copy File"}
                          </button>
                        </div>

                        {/* File Diff if modified */}
                        {activeFileObj.diff && (
                          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                            <span className="text-[11px] font-bold text-amber-400">
                              🔍 Glitch&apos;s Surgical Patch for {activeFileObj.path}:
                            </span>
                            <pre className="p-2.5 rounded bg-slate-950 font-mono text-[11px] text-slate-300 overflow-x-auto whitespace-pre max-h-40">
                              {activeFileObj.diff}
                            </pre>
                          </div>
                        )}

                        {/* Active File Content */}
                        <pre className="p-4 rounded-2xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-200 overflow-x-auto whitespace-pre leading-relaxed max-h-96">
                          {activeFileObj.current_content}
                        </pre>
                      </>
                    )}
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
