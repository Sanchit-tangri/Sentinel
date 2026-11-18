"use client";

import React from "react";
import { Shield, Sparkles, Sliders, Zap, Radio, Download, Cpu } from "lucide-react";
import { TechStack, ExecutionMode, AgentConfig } from "../types/sentinel";

interface CommandHeaderProps {
  currentStack: TechStack;
  onSelectStack: (stack: TechStack) => void;
  executionMode: ExecutionMode;
  onToggleExecutionMode: (mode: ExecutionMode) => void;
  onOpenAgentDrawer: () => void;
  onDownloadZip: () => void;
  isWsConnected: boolean;
  sessionId: string;
  agentConfig: AgentConfig;
  isRunning: boolean;
}

const STACKS: { id: TechStack; label: string; icon: string; desc: string }[] = [
  { id: "mern", label: "MERN Stack", icon: "⚛️", desc: "Node + Express + Mongo" },
  { id: "spring", label: "Spring Boot + React", icon: "☕", desc: "Java 21 + JPA" },
  { id: "fastapi", label: "FastAPI + Next.js", icon: "⚡", desc: "Python 3.12 + Postgres" },
  { id: "android", label: "Android Kotlin", icon: "🤖", desc: "Kotlin + Room + Manifest" },
];

export const CommandHeader: React.FC<CommandHeaderProps> = ({
  currentStack,
  onSelectStack,
  executionMode,
  onToggleExecutionMode,
  onOpenAgentDrawer,
  onDownloadZip,
  isWsConnected,
  sessionId,
  agentConfig,
  isRunning,
}) => {
  return (
    <header className="relative z-30 h-16 border-b border-white/[0.08] bg-[#07090E]/90 backdrop-blur-xl px-4 flex items-center justify-between gap-4">
      {/* Left: Brand & Telemetry Status */}
      <div className="flex items-center gap-3 shrink-0">
        <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500/20 via-blue-500/10 to-purple-500/20 border border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.25)]">
          <Shield className="w-4 h-4 text-cyan-400" />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-cyan-400" />
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm tracking-wider text-white font-mono-code">SENTINEL</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-semibold uppercase tracking-wider bg-cyan-950/80 text-cyan-300 border border-cyan-500/40">
              v1.0 STUDIO
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <span className={`w-1.5 h-1.5 rounded-full ${isWsConnected ? "bg-emerald-400 animate-pulse" : "bg-amber-400"}`} />
            <span className="font-mono-code text-[10px] text-slate-400">
              {isWsConnected ? `WS CONNECTED • ${sessionId.slice(0, 10)}` : "CONNECTING WS..."}
            </span>
          </div>
        </div>
      </div>

      {/* Center: Stack Selector Pills */}
      <div className="hidden md:flex items-center gap-1 p-1 bg-black/40 rounded-xl border border-white/[0.06]">
        {STACKS.map((stack) => {
          const isActive = currentStack === stack.id;
          return (
            <button
              key={stack.id}
              onClick={() => onSelectStack(stack.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 cursor-pointer ${
                isActive
                  ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-200 border border-cyan-400/40 shadow-sm shadow-cyan-500/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]"
              }`}
              title={stack.desc}
            >
              <span>{stack.icon}</span>
              <span>{stack.label}</span>
            </button>
          );
        })}
      </div>

      {/* Right: Mode Switcher & Agent Drawer Trigger */}
      <div className="flex items-center gap-2 shrink-0">
        {/* Execution Mode Toggle */}
        <div className="flex items-center p-0.5 bg-black/40 rounded-xl border border-white/[0.06]">
          <button
            onClick={() => onToggleExecutionMode("autopilot")}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-medium transition-all cursor-pointer ${
              executionMode === "autopilot"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="Auto-remediates all findings in an automated loop"
          >
            <Zap className="w-3 h-3 text-cyan-400" />
            <span className="hidden sm:inline">Autopilot</span>
          </button>
          <button
            onClick={() => onToggleExecutionMode("vibe_interactive")}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-medium transition-all cursor-pointer ${
              executionMode === "vibe_interactive"
                ? "bg-purple-500/20 text-purple-300 border border-purple-500/30 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="Pauses on vulnerability detection for interactive approval & custom vibe prompts"
          >
            <Radio className="w-3 h-3 text-purple-400" />
            <span className="hidden sm:inline">Vibe Interactive</span>
          </button>
        </div>

        {/* Agent Drawer Button */}
        <button
          onClick={onOpenAgentDrawer}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium text-slate-300 bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] hover:border-cyan-500/30 transition-all cursor-pointer"
          title="Customize Agent Persona Style, Security Strictness, and Target UI Theme"
        >
          <Sliders className="w-3.5 h-3.5 text-cyan-400" />
          <span className="hidden lg:inline capitalize font-mono-code text-[11px] text-cyan-300">
            {agentConfig.persona_style.replace("_", " ")}
          </span>
        </button>

        {/* Download Remediated ZIP */}
        <button
          onClick={onDownloadZip}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-200 bg-gradient-to-r from-emerald-500/20 to-teal-500/20 hover:from-emerald-500/30 hover:to-teal-500/30 border border-emerald-500/40 shadow-sm shadow-emerald-500/20 transition-all cursor-pointer"
          title="Export complete sanitized and verified multi-file codebase as a ZIP"
        >
          <Download className="w-3.5 h-3.5 text-emerald-400" />
          <span className="hidden sm:inline">Export ZIP</span>
        </button>
      </div>
    </header>
  );
};
