"use client";

import React, { useState, useRef } from "react";
import {
  Send,
  Upload,
  Download,
  Sparkles,
  Zap,
  Shield,
  FileCode,
  Loader2,
  FolderArchive,
} from "lucide-react";

interface VibeBarProps {
  prompt: string;
  onChangePrompt: (prompt: string) => void;
  onSubmit: (prompt: string) => void;
  onUploadZip: (file: File) => void;
  onDownloadZip: () => void;
  isRunning: boolean;
  activeAgent: string;
}

export const VibeBar: React.FC<VibeBarProps> = ({
  prompt,
  onChangePrompt,
  onSubmit,
  onUploadZip,
  onDownloadZip,
  isRunning,
  activeAgent,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith(".zip")) {
        onUploadZip(file);
      }
    }
  };

  const quickPrompts = [
    "Add rate-limiting middleware to Express login route",
    "Replace concatenated @Query with parameterized JPA bindings",
    "Set android:exported=false and require signature permission in manifest",
    "Sanitize MongoDB req.body with mongo-sanitize and Zod schema",
  ];

  return (
    <div className="fixed bottom-4 inset-x-0 z-40 flex flex-col items-center pointer-events-none px-4">
      {/* Quick Prompt Suggestions Pills */}
      <div className="flex items-center gap-1.5 mb-2 overflow-x-auto max-w-3xl pointer-events-auto">
        {quickPrompts.map((qp, idx) => (
          <button
            key={idx}
            onClick={() => {
              onChangePrompt(qp);
              onSubmit(qp);
            }}
            disabled={isRunning}
            className="px-2.5 py-1 rounded-full text-[10px] font-mono-code bg-black/60 hover:bg-black/90 text-slate-400 hover:text-cyan-300 border border-white/[0.08] hover:border-cyan-500/40 backdrop-blur-xl transition-all truncate max-w-[240px] cursor-pointer"
          >
            {qp}
          </button>
        ))}
      </div>

      {/* Main Floating Glass Bar */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        className={`w-full max-w-3xl pointer-events-auto rounded-2xl bg-[#07090E]/95 border transition-all duration-300 shadow-2xl backdrop-blur-2xl p-2.5 flex items-center gap-3 ${
          isDragOver
            ? "border-cyan-400 shadow-[0_0_30px_rgba(6,182,212,0.4)] scale-[1.01]"
            : "border-white/[0.12] hover:border-cyan-500/30 shadow-[0_10px_40px_rgba(0,0,0,0.8)]"
        }`}
      >
        {/* Hidden File Input */}
        <input
          type="file"
          ref={fileInputRef}
          accept=".zip"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              onUploadZip(e.target.files[0]);
            }
          }}
        />

        {/* Upload ZIP Icon Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isRunning}
          className="p-2 rounded-xl text-slate-400 hover:text-cyan-300 bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.06] transition-all cursor-pointer shrink-0"
          title="Upload entire repository ZIP to scan & patch"
        >
          <FolderArchive className="w-4 h-4" />
        </button>

        {/* Prompt Input */}
        <div className="flex-1 relative flex items-center">
          <input
            type="text"
            value={prompt}
            onChange={(e) => onChangePrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !isRunning && prompt.trim()) {
                onSubmit(prompt);
              }
            }}
            placeholder={
              isDragOver
                ? "Drop ZIP archive here to audit whole codebase..."
                : "Type a vibe prompt (e.g. 'Audit MERN routes and patch NoSQL injection')..."
            }
            disabled={isRunning}
            className="w-full bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none font-mono-code pr-2"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-1.5 shrink-0">
          <button
            onClick={() => onSubmit(prompt)}
            disabled={isRunning || !prompt.trim()}
            className={`px-4 py-2 rounded-xl text-xs font-bold font-mono-code flex items-center gap-1.5 transition-all cursor-pointer ${
              isRunning
                ? "bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 cursor-wait"
                : "bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 shadow-md shadow-cyan-500/25"
            }`}
          >
            {isRunning ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>{activeAgent.toUpperCase()} ACTIVE...</span>
              </>
            ) : (
              <>
                <Zap className="w-3.5 h-3.5" />
                <span>RUN VIBE</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
