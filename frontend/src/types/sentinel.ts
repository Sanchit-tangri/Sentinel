export type SeverityLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface Finding {
  id: string;
  cwe_id?: string;
  title: string;
  description: string;
  severity: SeverityLevel;
  file_path?: string;
  line_number?: number;
  line_start?: number;
  line_end?: number;
  snippet?: string;
  recommendation?: string;
  exploit_poc?: string;
  exploit_demo?: string;
  whitebox_trace?: {
    source: string;
    sanitizer?: string;
    sink: string;
  };
  fix_options?: string[];
  vibe_remediation_options?: string[];
}

export interface ProjectFile {
  path: string;
  original_content: string;
  current_content: string;
  is_modified: boolean;
  findings_count: number;
  diff: string;
  findings: Finding[];
}

export interface WorkspaceData {
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

export type PersonaStyle = "cyberpunk" | "principal_engineer" | "mentor";
export type SecurityLevel = "paranoid" | "balanced" | "mvp";
export type UIThemeTarget = "linear_dark" | "glass_minimal" | "neo_brutalist";
export type ExecutionMode = "autopilot" | "vibe_interactive";
export type TechStack = "mern" | "spring" | "fastapi" | "android";

export interface AgentConfig {
  persona_style: PersonaStyle;
  security_level: SecurityLevel;
  ui_theme_target: UIThemeTarget;
}

export interface AgentCursor {
  agent: "dex" | "pixel" | "snooze" | "glitch";
  file: string;
  line: number;
  column: number;
  message?: string;
}

export interface AgentTelemetryEvent {
  type: "AGENT_STATE" | "CURSOR_MOVE" | "VULN_DETECTED" | "LIVE_DIFF_CHUNK" | "CONNECTION_ESTABLISHED" | "APPROVAL_ACKNOWLEDGED";
  agent?: "dex" | "pixel" | "snooze" | "glitch";
  status?: "thinking" | "scanning" | "editing" | "waiting_approval" | "completed";
  message?: string;
  file?: string;
  line?: number;
  column?: number;
  finding?: Finding;
  original_lines?: string[];
  patched_lines?: string[];
  explanation?: string;
  timestamp?: string;
  session_id?: string;
  options?: any[];
}
