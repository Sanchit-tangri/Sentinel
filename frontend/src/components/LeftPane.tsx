"use client";

import React, { useState } from "react";
import {
  Folder,
  FileCode,
  Search,
  Network,
  ListTree,
  AlertTriangle,
  CheckCircle2,
  ShieldCheck,
  ArrowRight,
  Database,
  Server,
  Layout,
  Layers,
} from "lucide-react";
import { ProjectFile } from "../types/sentinel";

interface LeftPaneProps {
  files: Record<string, ProjectFile>;
  selectedFile: string;
  onSelectFile: (path: string) => void;
  activeAgent: string;
  taintData?: {
    nodes: { id: string; label: string; type: string; isTainted: boolean; details: string }[];
    flows: { from: string; to: string; isTainted: boolean; vulnerability?: string }[];
  };
}

export const LeftPane: React.FC<LeftPaneProps> = ({
  files,
  selectedFile,
  onSelectFile,
  activeAgent,
  taintData,
}) => {
  const [viewMode, setViewMode] = useState<"files" | "taint">("files");
  const [searchQuery, setSearchQuery] = useState("");

  const fileList = Object.values(files);
  const filteredFiles = fileList.filter((f) =>
    f.path.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalFiles = fileList.length;
  const vulnerableFiles = fileList.filter((f) => f.findings_count > 0).length;
  const totalVulns = fileList.reduce((acc, f) => acc + f.findings_count, 0);
  const remediatedFiles = fileList.filter((f) => f.is_modified).length;

  const getFileIcon = (path: string) => {
    const ext = path.split(".").pop()?.toLowerCase();
    switch (ext) {
      case "tsx":
      case "jsx":
        return <span className="text-cyan-400 text-xs">⚛️</span>;
      case "ts":
      case "js":
        return <span className="text-amber-400 text-xs">📜</span>;
      case "java":
        return <span className="text-orange-400 text-xs">☕</span>;
      case "kt":
        return <span className="text-purple-400 text-xs">🟣</span>;
      case "xml":
        return <span className="text-emerald-400 text-xs">📑</span>;
      case "py":
        return <span className="text-blue-400 text-xs">🐍</span>;
      case "sql":
        return <span className="text-pink-400 text-xs">🗄️</span>;
      default:
        return <FileCode className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  return (
    <div className="w-80 h-full border-r border-white/[0.08] bg-[#07090E]/80 backdrop-blur-xl flex flex-col shrink-0 select-none">
      {/* Header View Switcher */}
      <div className="p-3 border-b border-white/[0.08] flex items-center justify-between gap-2">
        <div className="flex items-center gap-1 bg-black/40 p-1 rounded-xl border border-white/[0.06] w-full">
          <button
            onClick={() => setViewMode("files")}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
              viewMode === "files"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <ListTree className="w-3.5 h-3.5" />
            <span>Files ({totalFiles})</span>
          </button>
          <button
            onClick={() => setViewMode("taint")}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
              viewMode === "taint"
                ? "bg-purple-500/20 text-purple-300 border border-purple-500/30 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            <span>Taint Map</span>
          </button>
        </div>
      </div>

      {viewMode === "files" ? (
        <>
          {/* File Search */}
          <div className="p-3 border-b border-white/[0.06]">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Filter files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-black/40 border border-white/[0.06] text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/40"
              />
            </div>
          </div>

          {/* File Tree List */}
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {filteredFiles.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500 font-mono-code">
                No matching project files found
              </div>
            ) : (
              filteredFiles.map((file) => {
                const isSelected = selectedFile === file.path;
                const hasVulns = file.findings_count > 0;
                const isFixed = file.is_modified && !hasVulns;

                return (
                  <button
                    key={file.path}
                    onClick={() => onSelectFile(file.path)}
                    className={`w-full text-left px-2.5 py-2 rounded-xl text-xs flex items-center justify-between gap-2 transition-all cursor-pointer ${
                      isSelected
                        ? "bg-cyan-950/40 border border-cyan-500/40 text-white shadow-sm shadow-cyan-500/10"
                        : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] border border-transparent"
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      {getFileIcon(file.path)}
                      <span className="truncate font-mono-code text-[11px]">{file.path}</span>
                    </div>

                    {/* Security Status Badge */}
                    <div className="shrink-0 flex items-center gap-1">
                      {hasVulns ? (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                          {file.findings_count}
                        </span>
                      ) : isFixed ? (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                          fixed
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-0.5 text-emerald-400/70 text-[10px]">
                          <ShieldCheck className="w-3 h-3" />
                        </span>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>

          {/* Repository Health Metrics */}
          <div className="p-3 border-t border-white/[0.08] bg-black/30 grid grid-cols-2 gap-2 text-[10px] font-mono-code">
            <div className="p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
              <span className="text-slate-400">Vulnerable Files</span>
              <div className="text-sm font-bold text-rose-400 mt-0.5">{vulnerableFiles}</div>
            </div>
            <div className="p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
              <span className="text-slate-400">Total Vulnerabilities</span>
              <div className="text-sm font-bold text-amber-300 mt-0.5">{totalVulns}</div>
            </div>
            <div className="p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
              <span className="text-slate-400">Patched Diffs</span>
              <div className="text-sm font-bold text-emerald-400 mt-0.5">{remediatedFiles}</div>
            </div>
            <div className="p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
              <span className="text-slate-400">Total Lines Inspected</span>
              <div className="text-sm font-bold text-cyan-400 mt-0.5">
                {fileList.reduce((acc, f) => acc + (f.current_content?.split("\n").length || 0), 0)}
              </div>
            </div>
          </div>
        </>
      ) : (
        /* Architecture & Taint Map View */
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
          <div className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-purple-400" />
            <span>Multi-Tier Data Flow & Taint Analysis</span>
          </div>

          {/* Tier 1: Frontend Client */}
          <div className="p-3 rounded-xl border border-cyan-500/30 bg-cyan-950/20">
            <div className="flex items-center justify-between text-xs font-bold text-cyan-300">
              <span className="flex items-center gap-1.5">
                <Layout className="w-3.5 h-3.5 text-cyan-400" />
                Frontend Client / UI
              </span>
              <span className="text-[10px] text-cyan-400/80 font-mono-code">React / Next.js / Android</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Captures user input, form submissions, and JWT session authorization headers.
            </p>
          </div>

          <div className="flex justify-center text-slate-600">
            <ArrowRight className="w-4 h-4 rotate-90" />
          </div>

          {/* Tier 2: API Controller & Routes */}
          <div className="p-3 rounded-xl border border-rose-500/40 bg-rose-950/20 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-2 h-2 rounded-full bg-rose-400 animate-ping m-2" />
            <div className="flex items-center justify-between text-xs font-bold text-rose-300">
              <span className="flex items-center gap-1.5">
                <Server className="w-3.5 h-3.5 text-rose-400" />
                REST API Controller Layer
              </span>
              <span className="text-[10px] text-rose-400 font-mono-code">TAINTED INPUT</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Route handlers receiving raw <code className="text-rose-300 font-mono-code">req.body</code> or unvalidated params.
            </p>
            <div className="mt-2 p-1.5 bg-black/40 rounded-lg border border-rose-500/30 text-[10px] text-rose-300 font-mono-code flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 text-rose-400 shrink-0" />
              <span>Unsanitized operator injection detected in route</span>
            </div>
          </div>

          <div className="flex justify-center text-slate-600">
            <ArrowRight className="w-4 h-4 rotate-90" />
          </div>

          {/* Tier 3: Business Logic / Service Layer */}
          <div className="p-3 rounded-xl border border-amber-500/30 bg-amber-950/20">
            <div className="flex items-center justify-between text-xs font-bold text-amber-300">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                Security Invariant & Service Gate
              </span>
              <span className="text-[10px] text-amber-400/80 font-mono-code">AST DriftGuard</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Validates 1-hop cross-file dependencies and applies sanitization middleware.
            </p>
          </div>

          <div className="flex justify-center text-slate-600">
            <ArrowRight className="w-4 h-4 rotate-90" />
          </div>

          {/* Tier 4: Database / Persistence */}
          <div className="p-3 rounded-xl border border-emerald-500/30 bg-emerald-950/20">
            <div className="flex items-center justify-between text-xs font-bold text-emerald-300">
              <span className="flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-emerald-400" />
                Database / Models
              </span>
              <span className="text-[10px] text-emerald-400/80 font-mono-code">Mongo / JPA / Room</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Parameterized queries and typed Mongoose/Room entities safeguard database state.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
