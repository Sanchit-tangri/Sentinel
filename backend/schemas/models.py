from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any
from enum import Enum


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class WhiteboxTrace(BaseModel):
    source: str
    sanitizer: str = "None (Missing / Ineffective)"
    sink: str


class VulnerabilityFinding(BaseModel):
    id: str
    cwe_id: Optional[str] = None
    title: str
    description: str
    severity: SeverityLevel
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    snippet: Optional[str] = None
    recommendation: Optional[str] = None
    exploit_poc: Optional[str] = None
    exploit_demo: Optional[str] = None
    whitebox_trace: Optional[Dict[str, str]] = None
    fix_options: List[str] = Field(default_factory=list)
    vibe_remediation_options: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def sync_legacy_and_v1_fields(self) -> "VulnerabilityFinding":
        # Synchronize line numbers
        if self.line_number is not None and self.line_start is None:
            self.line_start = self.line_number
        elif self.line_start is not None and self.line_number is None:
            self.line_number = self.line_start
        if self.line_end is None:
            self.line_end = self.line_start or self.line_number or 1

        # Synchronize exploit demonstrations
        if self.exploit_poc and not self.exploit_demo:
            self.exploit_demo = self.exploit_poc
        elif self.exploit_demo and not self.exploit_poc:
            self.exploit_poc = self.exploit_demo

        # Synchronize remediation options
        if self.fix_options and not self.vibe_remediation_options:
            self.vibe_remediation_options = list(self.fix_options)
        elif self.vibe_remediation_options and not self.fix_options:
            self.fix_options = list(self.vibe_remediation_options)

        return self


class ArchitectSpecification(BaseModel):
    task_id: str
    trust_boundaries: List[str] = Field(default_factory=list)
    security_invariants: List[str] = Field(default_factory=list)
    input_validation_rules: List[str] = Field(default_factory=list)
    prohibited_patterns: List[str] = Field(default_factory=list)


class AuditResult(BaseModel):
    task_id: str
    is_secure: bool
    findings: List[VulnerabilityFinding] = Field(default_factory=list)
    summary: str


class PatchResult(BaseModel):
    task_id: str
    iteration: int
    patched_code: str
    diff: str
    explanation: str


class RemediationMemory(BaseModel):
    memory_id: str
    cwe_id: Optional[str] = None
    vulnerability_title: str
    vulnerable_pattern: str
    patched_diff: str
    explanation: str
    timestamp: str


class AgentConfig(BaseModel):
    persona_style: str = "principal_engineer"  # "cyberpunk", "principal_engineer", "mentor"
    security_level: str = "balanced"  # "paranoid", "balanced", "mvp"
    ui_theme_target: str = "linear_dark"  # "linear_dark", "glass_minimal", "neo_brutalist"


class VibeInteractiveCommand(BaseModel):
    action: str = "APPROVE_FIX"  # APPROVE_FIX, REJECT_FIX, START_REMEDIATION, etc.
    finding_id: Optional[str] = None
    selected_strategy: Optional[str] = None
    custom_instruction: Optional[str] = None
