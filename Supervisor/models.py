from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional


# ---------------------------------------------------------------------------
# Sub-agent contracts
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    file: str
    claim: str
    confidence: float  # 0.0–1.0
    evidence_ids: List[str]
    line: Optional[int] = None


@dataclass
class EvidenceItem:
    id: str
    type: Literal["code_ref", "log", "test_output", "reasoning"]
    source: str   # agent name, e.g. "debug"
    content: str


@dataclass
class SubAgentInput:
    session_id: str
    repo_path: str          # read-only for agents
    bug_report: str
    understanding_summary: str


@dataclass
class SubAgentResult:
    agent: Literal["debug", "test", "maintenance"]
    status: Literal["ok", "failed", "timeout", "skipped"]
    summary: str
    findings: List[Finding]
    proposed_patch: Optional[str]       # unified diff or None
    evidence: List[EvidenceItem]
    error: Optional[str]
    started_at: datetime
    finished_at: datetime


# ---------------------------------------------------------------------------
# Supervisor output
# ---------------------------------------------------------------------------

@dataclass
class ConflictRecord:
    description: str
    agents_involved: List[str]
    resolution: str   # "picked_<agent>" | "open"


@dataclass
class AgentStatusEntry:
    agent: str
    status: Literal["ok", "failed", "timeout", "skipped"]
    error: Optional[str]


@dataclass
class TestRunResult:
    __test__ = False  # prevent pytest from collecting this class
    ran: bool
    passed: bool                # True only when ran=True and exit_code==0
    command: Optional[str]
    exit_code: Optional[int]
    output_tail: str            # last ~100 lines, secrets redacted
    duration: Optional[float]  # seconds


@dataclass
class SupervisorReport:
    session_id: str
    state: str
    explanation: str
    root_cause: str
    patch: Optional[str]                  # single unified diff or None
    patch_hash: Optional[str]             # SHA-256 hex of patch, or None
    evidence: List[EvidenceItem]
    agent_statuses: List[AgentStatusEntry]
    conflicts: List[ConflictRecord]
    confidence: float
    limitations: List[str]
    patch_source_agents: List[str]        # agents that proposed chosen patch
    selection_reason: Optional[str]
    failure_reason: Optional[str]
    branch: Optional[str]                 # patchpermit/<session_id[:8]> once applied
    test_result: Optional[TestRunResult] = None
    location: Optional[Dict[str, Any]] = None  # {"file", "line", "code"} of highest-confidence finding


# ---------------------------------------------------------------------------
# Approval
# ---------------------------------------------------------------------------

@dataclass
class ApprovalDecision:
    session_id: str
    patch_hash: str
    decision: Literal["approve", "reject"]
    approver: str
    timestamp: datetime
    comment: Optional[str] = None


# ---------------------------------------------------------------------------
# Aggregation internals (returned by aggregation.py, consumed by supervisor)
# ---------------------------------------------------------------------------

@dataclass
class AggregationOutcome:
    """Pure result of the aggregation pipeline; no state transitions here."""
    chosen_patch: Optional[str]
    patch_hash: Optional[str]
    patch_source_agents: List[str]
    selection_reason: Optional[str]
    root_cause: str
    confidence: float
    evidence: List[EvidenceItem]
    conflicts: List[ConflictRecord]
    limitations: List[str]
    agent_statuses: List[AgentStatusEntry]
    # "no_patch" or "failed" or None (meaning a patch was chosen)
    terminal_reason: Optional[Literal["no_patch", "failed"]] = None
    failure_reason: Optional[str] = None
