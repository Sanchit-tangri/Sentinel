"use client";

import React, { useState } from "react";
import {
  Monitor,
  Tablet,
  Smartphone,
  Terminal,
  Activity,
  Cpu,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  Search,
  ShoppingCart,
  TrendingUp,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import { AgentTelemetryEvent, UIThemeTarget } from "../types/sentinel";

interface RightPaneProps {
  sandboxHtml?: string;
  localhostUrl?: string;
  telemetryLogs: AgentTelemetryEvent[];
  activeAgent: string;
  uiTheme: UIThemeTarget;
  isPatching: boolean;
}

export const RightPane: React.FC<RightPaneProps> = ({
  sandboxHtml,
  localhostUrl = "http://localhost:8000",
  telemetryLogs,
  activeAgent,
  uiTheme,
  isPatching,
}) => {
  const [activeTab, setActiveTab] = useState<"sandbox" | "terminal">("sandbox");
  const [deviceViewport, setDeviceViewport] = useState<"desktop" | "tablet" | "mobile" | "android">("desktop");
  const [cartCount, setCartCount] = useState(2);
  const [demoSearch, setDemoSearch] = useState("");
  const [demoFilter, setDemoFilter] = useState("all");

  const sampleProducts = [
    { id: 1, name: "Quantum Security Enclave", category: "hardware", price: "$2,499", stock: "In Stock" },
    { id: 2, name: "OmniRoute Neural Tokenizer", category: "software", price: "$499/mo", stock: "Instant" },
    { id: 3, name: "Zero-Drift Invariant Sentinel", category: "security", price: "$1,200", stock: "Verified" },
    { id: 4, name: "Android Taint Shield SDK", category: "mobile", price: "$750", stock: "v1.0" },
  ];

  const filteredProducts = sampleProducts.filter(
    (p) =>
      (demoFilter === "all" || p.category === demoFilter) &&
      p.name.toLowerCase().includes(demoSearch.toLowerCase())
  );

  return (
    <div className="w-[480px] xl:w-[540px] h-full border-l border-white/[0.08] bg-[#07090E]/90 backdrop-blur-xl flex flex-col shrink-0 select-none overflow-hidden">
      {/* Pane Tab Switcher */}
      <div className="h-12 p-2 border-b border-white/[0.08] flex items-center justify-between gap-2 shrink-0 bg-black/40">
        <div className="flex items-center gap-1 bg-black/50 p-1 rounded-xl border border-white/[0.06] w-full">
          <button
            onClick={() => setActiveTab("sandbox")}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "sandbox"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Monitor className="w-3.5 h-3.5" />
            <span>Live Sandbox</span>
          </button>
          <button
            onClick={() => setActiveTab("terminal")}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "terminal"
                ? "bg-purple-500/20 text-purple-300 border border-purple-500/30 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Agent Brain & Log</span>
          </button>
        </div>
      </div>

      {activeTab === "sandbox" ? (
        /* TAB 1: LIVE APP SANDBOX */
        <div className="flex-1 flex flex-col overflow-hidden bg-black/60">
          {/* Viewport Control Bar */}
          <div className="h-10 px-4 border-b border-white/[0.06] flex items-center justify-between gap-3 shrink-0 bg-slate-950/60">
            <div className="flex items-center gap-1.5 text-[11px] font-mono-code text-cyan-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>{localhostUrl}</span>
            </div>

            <div className="flex items-center gap-1 p-0.5 bg-black/40 rounded-lg border border-white/[0.06]">
              <button
                onClick={() => setDeviceViewport("desktop")}
                className={`p-1 rounded text-xs transition-all cursor-pointer ${
                  deviceViewport === "desktop" ? "bg-cyan-500/30 text-cyan-300" : "text-slate-400 hover:text-white"
                }`}
                title="Desktop (100%)"
              >
                <Monitor className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setDeviceViewport("tablet")}
                className={`p-1 rounded text-xs transition-all cursor-pointer ${
                  deviceViewport === "tablet" ? "bg-cyan-500/30 text-cyan-300" : "text-slate-400 hover:text-white"
                }`}
                title="Tablet View (768px)"
              >
                <Tablet className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setDeviceViewport("mobile")}
                className={`p-1 rounded text-xs transition-all cursor-pointer ${
                  deviceViewport === "mobile" ? "bg-cyan-500/30 text-cyan-300" : "text-slate-400 hover:text-white"
                }`}
                title="Mobile View (375px)"
              >
                <Smartphone className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setDeviceViewport("android")}
                className={`px-2 py-0.5 rounded text-[10px] font-bold transition-all cursor-pointer ${
                  deviceViewport === "android"
                    ? "bg-purple-500/30 text-purple-300 border border-purple-400/40"
                    : "text-slate-400 hover:text-white"
                }`}
                title="Android Phone Frame (Kotlin / Mobile)"
              >
                🤖 Android Frame
              </button>
            </div>
          </div>

          {/* Sandbox Canvas */}
          <div className="flex-1 overflow-y-auto p-4 flex items-center justify-center bg-gradient-to-b from-[#07090e] to-slate-950">
            {deviceViewport === "android" ? (
              /* Android Phone Chassis Simulation */
              <div className="w-[320px] h-[580px] rounded-[38px] border-4 border-slate-700 bg-slate-950 p-2.5 shadow-2xl relative flex flex-col overflow-hidden">
                {/* Top Notch & Camera */}
                <div className="absolute top-2 inset-x-0 flex justify-center z-20">
                  <div className="w-24 h-4 bg-slate-900 rounded-full flex items-center justify-center gap-2 border border-slate-700">
                    <span className="w-2 h-2 rounded-full bg-slate-950 border border-slate-600" />
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-900" />
                  </div>
                </div>

                {/* Android Status Bar */}
                <div className="h-6 flex items-center justify-between px-4 text-[9px] text-slate-400 font-mono-code pt-1 z-10 shrink-0">
                  <span>09:41</span>
                  <span>5G • 98%</span>
                </div>

                {/* App Screen Content */}
                <div className="flex-1 rounded-[24px] bg-[#0A0D16] p-3 overflow-y-auto flex flex-col gap-2.5 text-white">
                  <div className="flex items-center justify-between border-b border-white/[0.08] pb-2">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm">🛡️</span>
                      <span className="text-xs font-bold text-cyan-300 font-mono-code">SentinelApp</span>
                    </div>
                    <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold">
                      VERIFIED
                    </span>
                  </div>

                  <div className="p-2.5 rounded-xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-500/30">
                    <span className="text-[10px] text-slate-400">Secured Invariants</span>
                    <div className="text-base font-bold text-white mt-0.5">Zero Taint Leak</div>
                    <div className="text-[10px] text-emerald-400 mt-1 flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" /> +99.98% Tamper Resistance
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <div className="text-[10px] font-bold text-slate-400 uppercase">Recent Events</div>
                    {sampleProducts.slice(0, 3).map((p) => (
                      <div key={p.id} className="p-2 rounded-lg bg-white/[0.03] border border-white/[0.05] flex items-center justify-between text-[11px]">
                        <span className="truncate max-w-[140px] text-slate-300">{p.name}</span>
                        <span className="font-mono-code text-cyan-400 font-bold">{p.price}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Bottom Android Gesture Pill */}
                <div className="h-4 flex items-center justify-center shrink-0">
                  <div className="w-20 h-1 bg-slate-600 rounded-full" />
                </div>
              </div>
            ) : (
              /* Desktop / Tablet / Mobile Responsive Window */
              <div
                className={`transition-all duration-300 rounded-2xl border border-white/[0.1] bg-[#090C16] shadow-2xl p-4 flex flex-col gap-4 overflow-hidden ${
                  deviceViewport === "tablet" ? "w-[440px]" : deviceViewport === "mobile" ? "w-[340px]" : "w-full"
                }`}
              >
                {/* Agency Designer App Header */}
                <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-slate-950 font-bold text-xs shadow-md">
                      ⚡
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-white tracking-wide">Aura Enterprise Platform</h4>
                      <p className="text-[10px] text-slate-400">Synthesized by Pixel • Verified by Snooze</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <button
                        onClick={() => setCartCount(cartCount + 1)}
                        className="p-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-slate-300 text-xs flex items-center gap-1 cursor-pointer"
                      >
                        <ShoppingCart className="w-3.5 h-3.5 text-cyan-400" />
                        <span className="font-mono-code text-[10px]">{cartCount}</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* KPI Metrics Sparklines */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-950/30 to-black border border-cyan-500/20">
                    <div className="text-[10px] text-slate-400">Total Transactions</div>
                    <div className="text-lg font-bold text-white mt-0.5 font-mono-code">$48,240</div>
                    <div className="text-[10px] text-emerald-400 flex items-center gap-1 mt-1">
                      <TrendingUp className="w-3 h-3" /> +14.2% this week
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-gradient-to-br from-purple-950/30 to-black border border-purple-500/20">
                    <div className="text-[10px] text-slate-400">Active Sessions</div>
                    <div className="text-lg font-bold text-white mt-0.5 font-mono-code">1,824</div>
                    <div className="text-[10px] text-purple-400 flex items-center gap-1 mt-1">
                      <ShieldCheck className="w-3 h-3" /> 100% Sanitized
                    </div>
                  </div>
                </div>

                {/* Search & Category Filter */}
                <div className="flex flex-col gap-2">
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      placeholder="Search inventory & APIs..."
                      value={demoSearch}
                      onChange={(e) => setDemoSearch(e.target.value)}
                      className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-black/40 border border-white/[0.08] text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/40"
                    />
                  </div>

                  <div className="flex items-center gap-1 text-[10px] overflow-x-auto pb-1">
                    {["all", "hardware", "software", "security", "mobile"].map((cat) => (
                      <button
                        key={cat}
                        onClick={() => setDemoFilter(cat)}
                        className={`px-2 py-0.5 rounded-md font-mono-code capitalize cursor-pointer transition-all ${
                          demoFilter === cat
                            ? "bg-cyan-500/30 text-cyan-200 border border-cyan-400/50"
                            : "bg-white/[0.02] text-slate-400 hover:text-white"
                        }`}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Product / Service Catalog List */}
                <div className="space-y-1.5 max-h-[160px] overflow-y-auto">
                  {filteredProducts.map((p) => (
                    <div
                      key={p.id}
                      className="p-2 rounded-xl bg-white/[0.02] hover:bg-white/[0.05] border border-white/[0.05] flex items-center justify-between transition-all"
                    >
                      <div>
                        <div className="text-xs font-semibold text-slate-200">{p.name}</div>
                        <div className="text-[10px] text-slate-500 capitalize">{p.category} • {p.stock}</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono-code text-xs font-bold text-cyan-400">{p.price}</span>
                        <button
                          onClick={() => setCartCount(cartCount + 1)}
                          className="px-2 py-1 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 text-[10px] font-bold border border-cyan-500/30 cursor-pointer"
                        >
                          + Add
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* TAB 2: WHITE-BOX AGENT BRAIN & TERMINAL */
        <div className="flex-1 flex flex-col overflow-hidden bg-black/80 font-mono-code text-xs">
          {/* Telemetry Metrics Header */}
          <div className="p-3 border-b border-white/[0.08] bg-slate-950/80 grid grid-cols-3 gap-2 text-[10px]">
            <div className="p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
              <span className="text-slate-400">Context Budget</span>
              <div className="text-cyan-400 font-bold mt-0.5">4,280 / 32k</div>
            </div>
            <div className="p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
              <span className="text-slate-400">AST DriftGuard</span>
              <div className="text-emerald-400 font-bold mt-0.5 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> 0 Drift
              </div>
            </div>
            <div className="p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
              <span className="text-slate-400">OmniRoute Tier</span>
              <div className="text-purple-400 font-bold mt-0.5">SURGICAL_PATCH</div>
            </div>
          </div>

          {/* Real-Time Terminal Log Stream */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2 select-text leading-relaxed">
            {telemetryLogs.length === 0 ? (
              <div className="p-8 text-center text-slate-500">
                Awaiting telemetry stream from WebSocket connection...
              </div>
            ) : (
              telemetryLogs.map((log, idx) => {
                const isVuln = log.type === "VULN_DETECTED";
                const isDiff = log.type === "LIVE_DIFF_CHUNK";
                const isCursor = log.type === "CURSOR_MOVE";

                return (
                  <div
                    key={idx}
                    className={`p-2 rounded-lg border text-[11px] ${
                      isVuln
                        ? "bg-rose-950/30 border-rose-500/40 text-rose-300"
                        : isDiff
                        ? "bg-emerald-950/30 border-emerald-500/40 text-emerald-300"
                        : isCursor
                        ? "bg-cyan-950/20 border-cyan-500/20 text-cyan-300"
                        : "bg-white/[0.02] border-white/[0.04] text-slate-300"
                    }`}
                  >
                    <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                      <div className="flex items-center gap-1.5">
                        <span className="px-1.5 py-0.2 rounded font-bold uppercase tracking-wider text-[9px] bg-black/50 border border-white/[0.08]">
                          {log.agent || log.type}
                        </span>
                        <span>{log.status || log.type}</span>
                      </div>
                      <span className="text-slate-500 text-[9px]">
                        {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : "live"}
                      </span>
                    </div>

                    {log.message && <p className="leading-snug">{log.message}</p>}

                    {log.finding && (
                      <div className="mt-1 font-bold text-rose-400">
                        🚨 {log.finding.cwe_id}: {log.finding.title} (line {log.finding.line_number})
                      </div>
                    )}

                    {log.line && (
                      <div className="text-[10px] text-cyan-400/80">
                        📍 Cursor moved to {log.file || "file"} @ line {log.line}:{log.column || 1}
                      </div>
                    )}

                    {log.explanation && (
                      <div className="mt-1 text-emerald-300 font-semibold">
                        ✨ {log.explanation}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};
