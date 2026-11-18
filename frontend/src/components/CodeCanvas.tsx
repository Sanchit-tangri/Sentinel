"use client";

import React, { useState } from "react";
import {
  Copy,
  Check,
  AlertOctagon,
  Sparkles,
  Shield,
  Send,
  Zap,
  GitCompare,
  Code2,
  FileCheck,
} from "lucide-react";
import { Finding, ProjectFile, AgentCursor, ExecutionMode } from "../types/sentinel";

interface CodeCanvasProps {
  currentFile: ProjectFile | null;
  activeCursor: AgentCursor | null;
  executionMode: ExecutionMode;
  onApproveFix: (findingId: string, strategy: string, customInstruction?: string) => void;
  isPatching: boolean;
  activeAgent: string;
}

export const CodeCanvas: React.FC<CodeCanvasProps> = ({
  currentFile,
  activeCursor,
  executionMode,
  onApproveFix,
  isPatching,
  activeAgent,
}) => {
  const [copied, setCopied] = useState(false);
  const [showDiff, setShowDiff] = useState(true);
  const [customPromptOpen, setCustomPromptOpen] = useState<string | null>(null);
  const [customPromptText, setCustomPromptText] = useState("");

  if (!currentFile) {
    return (
      <div className="flex-1 h-full flex flex-col items-center justify-center p-8 bg-[#07090E] text-slate-500 font-mono-code">
        <Code2 className="w-12 h-12 text-slate-600 mb-3 animate-pulse" />
        <p className="text-sm">Select a file from the explorer to inspect live multi-agent canvas</p>
      </div>
    );
  }

  const code = currentFile.current_content || currentFile.original_content || "";
  const lines = code.split("\n");
  const findings = currentFile.findings || [];

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getAgentCursorPill = (lineNum: number) => {
    if (!activeCursor || activeCursor.line !== lineNum) return null;

    const agent = activeCursor.agent.toLowerCase();
    let bg = "bg-cyan-500/20 border-cyan-400 text-cyan-300";
    let icon = "🧥";
    let name = "Dex";

    if (agent === "pixel") {
      bg = "bg-amber-500/20 border-amber-400 text-amber-300";
      icon = "🧃";
      name = "Pixel";
    } else if (agent === "snooze") {
      bg = "bg-purple-500/20 border-purple-400 text-purple-300";
      icon = "😴";
      name = "Snooze";
    } else if (agent === "glitch") {
      bg = "bg-pink-500/20 border-pink-400 text-pink-300";
      icon = "🕺";
      name = "Glitch";
    }

    return (
      <div className={`absolute right-4 -top-3.5 z-20 flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[10px] font-bold shadow-lg backdrop-blur-md transition-all duration-300 animate-bob ${bg}`}>
        <span>{icon}</span>
        <span className="font-mono-code uppercase tracking-wider">{name}</span>
        <span className="text-[9px] opacity-80 max-w-[180px] truncate">
          {activeCursor.message || "Active on line"}
        </span>
      </div>
    );
  };

  return (
    <div className="flex-1 h-full flex flex-col bg-[#07090E] overflow-hidden select-text relative">
      {/* Canvas Top Bar */}
      <div className="h-10 px-4 border-b border-white/[0.08] bg-black/40 backdrop-blur-md flex items-center justify-between gap-4 z-10 shrink-0">
        <div className="flex items-center gap-2">
          <span className="font-mono-code text-xs text-slate-300 font-semibold">{currentFile.path}</span>
          {currentFile.is_modified && (
            <span className="inline-flex items-center gap-1 text-[10px] font-mono-code px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              <FileCheck className="w-3 h-3 text-emerald-400" />
              Remediated
            </span>
          )}
          {currentFile.findings_count > 0 && (
            <span className="inline-flex items-center gap-1 text-[10px] font-mono-code px-1.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
              <AlertOctagon className="w-3 h-3 text-rose-400" />
              {currentFile.findings_count} Vulnerability Finding(s)
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {currentFile.diff && (
            <button
              onClick={() => setShowDiff(!showDiff)}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-mono-code border transition-all cursor-pointer ${
                showDiff
                  ? "bg-purple-500/20 border-purple-500/40 text-purple-300"
                  : "bg-white/[0.03] border-white/[0.06] text-slate-400 hover:text-slate-200"
              }`}
            >
              <GitCompare className="w-3 h-3" />
              <span>{showDiff ? "Hide Diff Overlay" : "Show Diff"}</span>
            </button>
          )}

          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-mono-code text-slate-400 hover:text-slate-200 bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.06] transition-all cursor-pointer"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>
        </div>
      </div>

      {/* Code Editor Body */}
      <div className="flex-1 overflow-y-auto font-mono-code text-xs leading-relaxed p-4 bg-[#07090E]/95">
        <div className="relative min-w-full">
          {lines.map((lineText, idx) => {
            const lineNum = idx + 1;
            const lineFindings = findings.filter((f) => f.line_number === lineNum);
            const isVulnerable = lineFindings.length > 0;
            const cursorPill = getAgentCursorPill(lineNum);

            return (
              <React.Fragment key={lineNum}>
                <div
                  className={`relative flex items-start group py-0.5 px-2 rounded-md transition-colors ${
                    isVulnerable
                      ? "bg-rose-950/30 border-l-2 border-rose-500"
                      : "hover:bg-white/[0.02]"
                  }`}
                >
                  {/* Floating Agent Cursor Pill */}
                  {cursorPill}

                  {/* Line Number */}
                  <span className="w-10 select-none text-right pr-4 text-slate-600 group-hover:text-slate-400 shrink-0 font-mono text-[11px]">
                    {lineNum}
                  </span>

                  {/* Line Content */}
                  <span className={`flex-1 font-mono-code text-[12px] whitespace-pre break-all ${
                    isVulnerable ? "text-rose-200 font-semibold" : "text-slate-200"
                  }`}>
                    {lineText || " "}
                  </span>
                </div>

                {/* Inline White-Box Loophole Inspector Card */}
                {isVulnerable &&
                  lineFindings.map((finding) => (
                    <div
                      key={finding.id}
                      className="my-2 ml-12 mr-4 p-4 rounded-xl border border-rose-500/40 bg-gradient-to-br from-rose-950/40 via-black/60 to-purple-950/30 shadow-xl backdrop-blur-md"
                    >
                      {/* Finding Header */}
                      <div className="flex items-center justify-between gap-2 border-b border-rose-500/20 pb-2.5">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500 text-slate-950 uppercase tracking-wider">
                            {finding.severity}
                          </span>
                          <span className="text-xs font-bold text-rose-300 font-mono-code">
                            {finding.cwe_id || "OWASP"}: {finding.title}
                          </span>
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono-code">Line {lineNum}</span>
                      </div>

                      {/* Description & Exploit PoC */}
                      <div className="mt-2.5 space-y-2 text-xs">
                        <p className="text-slate-300 text-[11px] leading-relaxed">
                          {finding.description}
                        </p>

                        {/* White-Box Taint Flow Trace */}
                        {finding.whitebox_trace && (
                          <div className="p-2.5 rounded-lg bg-black/60 border border-purple-500/20 text-[11px] font-mono-code flex flex-col gap-1">
                            <span className="font-bold text-purple-400">White-Box Taint Flow Trace:</span>
                            <div className="flex items-center gap-1.5 flex-wrap text-[10px]">
                              <span className="px-2 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-500/30">
                                <b>Source:</b> {finding.whitebox_trace.source}
                              </span>
                              <span className="text-slate-500">→</span>
                              <span className="px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-500/30">
                                <b>Sanitizer:</b> {finding.whitebox_trace.sanitizer || "None (Missing / Ineffective)"}
                              </span>
                              <span className="text-slate-500">→</span>
                              <span className="px-2 py-0.5 rounded bg-cyan-950/60 text-cyan-300 border border-cyan-500/30">
                                <b>Sink:</b> {finding.whitebox_trace.sink}
                              </span>
                            </div>
                          </div>
                        )}

                        {(finding.exploit_demo || finding.exploit_poc) && (
                          <div className="p-2.5 rounded-lg bg-black/50 border border-rose-500/20 text-[11px] text-rose-300/90 font-mono-code">
                            <span className="font-bold text-rose-400">Exploit Demo Payload: </span>
                            <code className="text-rose-200 bg-rose-950/40 px-1.5 py-0.5 rounded">{finding.exploit_demo || finding.exploit_poc}</code>
                          </div>
                        )}
                      </div>

                      {/* Interactive Vibe Coding Remediation Buttons */}
                      <div className="mt-3.5 pt-3 border-t border-rose-500/20 flex flex-col gap-2">
                        <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                          Vibe Remediation Architectural Options:
                        </div>

                        <div className="flex flex-wrap gap-2">
                          {(finding.vibe_remediation_options && finding.vibe_remediation_options.length > 0
                            ? finding.vibe_remediation_options
                            : finding.fix_options && finding.fix_options.length > 0
                            ? finding.fix_options
                            : ["Option 1: Parameterized Prepared Statement with strict bindings", "Option 2: Schema Validation via ORM filter allow-list"]
                          ).map((opt, oIdx) => (
                            <button
                              key={oIdx}
                              onClick={() => onApproveFix(finding.id, opt)}
                              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-200 border border-cyan-400/40 transition-all flex items-center gap-1.5 cursor-pointer shadow-sm shadow-cyan-500/10 text-left"
                            >
                              <Sparkles className="w-3 h-3 text-cyan-400 shrink-0" />
                              <span>{opt}</span>
                            </button>
                          ))}

                          {/* Custom Vibe Prompt Button */}
                          <button
                            onClick={() =>
                              setCustomPromptOpen(customPromptOpen === finding.id ? null : finding.id)
                            }
                            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-purple-500/20 hover:bg-purple-500/30 text-purple-200 border border-purple-400/40 transition-all flex items-center gap-1.5 cursor-pointer"
                          >
                            <span>💬 Custom Vibe Prompt...</span>
                          </button>
                        </div>

                        {/* Inline Custom Vibe Prompt Input */}
                        {customPromptOpen === finding.id && (
                          <div className="mt-2 flex items-center gap-2 p-2 bg-black/60 rounded-xl border border-purple-500/40">
                            <input
                              type="text"
                              value={customPromptText}
                              onChange={(e) => setCustomPromptText(e.target.value)}
                              placeholder="e.g. Sanitize using mongo-sanitize and add Joi validation..."
                              className="flex-1 bg-transparent text-xs text-purple-200 placeholder-purple-400/50 focus:outline-none"
                              onKeyDown={(e) => {
                                if (e.key === "Enter" && customPromptText.trim()) {
                                  onApproveFix(finding.id, "Custom Strategy", customPromptText);
                                  setCustomPromptText("");
                                  setCustomPromptOpen(null);
                                }
                              }}
                            />
                            <button
                              onClick={() => {
                                if (customPromptText.trim()) {
                                  onApproveFix(finding.id, "Custom Strategy", customPromptText);
                                  setCustomPromptText("");
                                  setCustomPromptOpen(null);
                                }
                              }}
                              className="px-3 py-1 bg-purple-500 text-slate-950 font-bold rounded-lg text-xs flex items-center gap-1 hover:bg-purple-400 cursor-pointer"
                            >
                              <Send className="w-3 h-3" />
                              <span>Apply</span>
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
              </React.Fragment>
            );
          })}
        </div>

        {/* Surgical Diff Overlay (When present) */}
        {showDiff && currentFile.diff && (
          <div className="mt-6 p-4 rounded-xl border border-emerald-500/30 bg-black/60 backdrop-blur-md">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-white/[0.08]">
              <span className="text-xs font-bold text-emerald-400 font-mono-code flex items-center gap-1.5">
                <Check className="w-3.5 h-3.5" />
                Glitch Surgical Diff & Remediated Transformation
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                ZERO REGRESSIONS CERTIFIED
              </span>
            </div>
            <pre className="font-mono-code text-[11px] leading-relaxed overflow-x-auto text-slate-300">
              {currentFile.diff.split("\n").map((line, i) => {
                if (line.startsWith("+") && !line.startsWith("+++")) {
                  return (
                    <div key={i} className="text-emerald-300 bg-emerald-950/30 px-1 py-0.5 rounded">
                      {line}
                    </div>
                  );
                } else if (line.startsWith("-") && !line.startsWith("---")) {
                  return (
                    <div key={i} className="text-rose-300 bg-rose-950/30 px-1 py-0.5 rounded">
                      {line}
                    </div>
                  );
                }
                return <div key={i} className="text-slate-400">{line}</div>;
              })}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
