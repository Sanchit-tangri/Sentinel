from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class VulnerabilityFinding(BaseModel):
    id: str
    cwe_id: Optional[str] = None
    title: str
    description: str
    severity: SeverityLevel
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    snippet: Optional[str] = None
    recommendation: Optional[str] = None
    exploit_poc: Optional[str] = None
    fix_options: List[str] = Field(default_factory=list)


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
