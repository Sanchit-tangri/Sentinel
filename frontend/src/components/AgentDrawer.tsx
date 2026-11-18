"use client";

import React from "react";
import { X, Sparkles, ShieldAlert, Palette, CheckCircle2, Bot } from "lucide-react";
import { AgentConfig, PersonaStyle, SecurityLevel, UIThemeTarget } from "../types/sentinel";

interface AgentDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  config: AgentConfig;
  onChangeConfig: (config: AgentConfig) => void;
  activeAgent: string;
}

const CREW_MEMBERS = [
  {
    id: "dex",
    name: "Dex",
    title: "The Architect",
    role: "Threat Modeling & Invariant Engine",
    color: "cyan",
    model: "claude-3-5-sonnet",
    quote: "Formulating formal trust boundaries and scoping 1-hop dependencies.",
    avatar: "🧥",
  },
  {
    id: "pixel",
    name: "Pixel",
    title: "The Developer",
    role: "OmniRoute Polyglot Synthesis",
    color: "amber",
    model: "qwen-2.5-coder-32b",
    quote: "Slurrrp! Synthesizing multi-file project files and live localhost sandbox!",
    avatar: "🧃",
  },
  {
    id: "snooze",
    name: "Snooze",
    title: "The Auditor",
    role: "Polyglot OWASP / CWE Scanner",
    color: "purple",
    model: "hybrid-ast-engine",
    quote: "Yaaawn... 💤 Laser eyes scanning every route, query, and manifest across the repo!",
    avatar: "😴",
  },
  {
    id: "glitch",
    name: "Glitch",
    title: "The Patcher",
    role: "Surgical Remediation & Live Diff",
    color: "pink",
    model: "surgical-patcher",
    quote: "Break it down! 🕺 Surgically patching files and packing a clean downloadable ZIP!",
    avatar: "🕺",
  },
];

export const AgentDrawer: React.FC<AgentDrawerProps> = ({
  isOpen,
  onClose,
  config,
  onChangeConfig,
  activeAgent,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Container */}
      <div className="relative w-full max-w-md bg-[#07090E]/95 border-l border-white/[0.08] p-6 flex flex-col gap-6 overflow-y-auto shadow-2xl z-10 backdrop-blur-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
          <div className="flex items-center gap-2.5">
            <Bot className="w-5 h-5 text-cyan-400" />
            <div>
              <h2 className="text-sm font-bold text-white font-mono-code uppercase tracking-wider">
                Agent Studio Control Room
              </h2>
              <p className="text-xs text-slate-400">Configure multi-agent behavior and studio aesthetics</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.06] transition-all cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Section 1: Persona Style */}
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Agent Persona Style</span>
          </div>
          <div className="grid grid-cols-1 gap-2">
            {[
              {
                id: "cyberpunk",
                title: "Cyberpunk Netrunner",
                desc: "High-octane telemetry, ICE breach jargon, and zero-day patch alerts.",
              },
              {
                id: "principal_engineer",
                title: "Principal Engineer",
                desc: "Formal invariants, AST drift guards, and rigorous architecture post-mortems.",
              },
              {
                id: "mentor",
                title: "Security Mentor",
                desc: "Educational walk-throughs, friendly tips, and architectural trade-off guides.",
              },
            ].map((p) => {
              const selected = config.persona_style === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => onChangeConfig({ ...config, persona_style: p.id as PersonaStyle })}
                  className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                    selected
                      ? "bg-cyan-950/40 border-cyan-400/50 shadow-sm shadow-cyan-500/20 text-white"
                      : "bg-white/[0.02] border-white/[0.06] text-slate-400 hover:bg-white/[0.05]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-cyan-300 font-mono-code">{p.title}</span>
                    {selected && <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{p.desc}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Section 2: Security Strictness */}
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
            <ShieldAlert className="w-3.5 h-3.5 text-purple-400" />
            <span>Security Strictness Policy</span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: "paranoid", label: "Paranoid", sub: "All CWEs" },
              { id: "balanced", label: "Balanced", sub: "Enterprise" },
              { id: "mvp", label: "MVP", sub: "Blockers Only" },
            ].map((s) => {
              const selected = config.security_level === s.id;
              return (
                <button
                  key={s.id}
                  onClick={() => onChangeConfig({ ...config, security_level: s.id as SecurityLevel })}
                  className={`p-2.5 rounded-xl border text-center transition-all cursor-pointer ${
                    selected
                      ? "bg-purple-950/40 border-purple-400/50 text-purple-200 shadow-sm"
                      : "bg-white/[0.02] border-white/[0.06] text-slate-400 hover:bg-white/[0.05]"
                  }`}
                >
                  <div className="text-xs font-semibold font-mono-code">{s.label}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">{s.sub}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Section 3: Target UI Aesthetic */}
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
            <Palette className="w-3.5 h-3.5 text-amber-400" />
            <span>Target Preview UI Aesthetic</span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: "linear_dark", label: "Linear Dark" },
              { id: "glass_minimal", label: "Glass Minimal" },
              { id: "neo_brutalist", label: "Neo Brutalist" },
            ].map((theme) => {
              const selected = config.ui_theme_target === theme.id;
              return (
                <button
                  key={theme.id}
                  onClick={() => onChangeConfig({ ...config, ui_theme_target: theme.id as UIThemeTarget })}
                  className={`p-2.5 rounded-xl border text-center transition-all cursor-pointer ${
                    selected
                      ? "bg-amber-950/40 border-amber-400/50 text-amber-200 shadow-sm"
                      : "bg-white/[0.02] border-white/[0.06] text-slate-400 hover:bg-white/[0.05]"
                  }`}
                >
                  <div className="text-xs font-semibold">{theme.label}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Section 4: 4 Hero Crew Roster */}
        <div className="flex flex-col gap-2.5 pt-2 border-t border-white/[0.08]">
          <div className="text-xs font-semibold text-slate-300">Active Sentinel Crew Members</div>
          <div className="grid grid-cols-1 gap-2">
            {CREW_MEMBERS.map((c) => {
              const isWorking = activeAgent.toLowerCase() === c.id;
              return (
                <div
                  key={c.id}
                  className={`p-3 rounded-xl border transition-all ${
                    isWorking
                      ? "bg-slate-900/90 border-cyan-400 shadow-lg shadow-cyan-500/20"
                      : "bg-white/[0.02] border-white/[0.06]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="text-xl">{c.avatar}</span>
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-bold text-white">{c.name}</span>
                          <span className="text-[10px] text-slate-400">({c.title})</span>
                        </div>
                        <div className="text-[10px] text-cyan-400 font-mono-code">{c.role}</div>
                      </div>
                    </div>
                    <span className="text-[9px] px-2 py-0.5 rounded-full font-mono-code bg-black/40 text-slate-400 border border-white/[0.06]">
                      {c.model}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-2 italic bg-black/30 p-2 rounded-lg border border-white/[0.03]">
                    "{c.quote}"
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
