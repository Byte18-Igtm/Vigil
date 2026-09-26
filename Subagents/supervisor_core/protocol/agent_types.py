import time
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field


class AgentTask(BaseModel):
    """
    Structured task payload created by Supervisor or Developer and assigned to a worker model.
    """
    id: str = Field(description="Unique task identifier")
    type: Literal["debug", "test", "explain"] = Field(description="Target model/agent kind")
    filePath: str = Field(description="Path to the source file")
    line: int = Field(description="1-based line number targeted by the user")
    column: Optional[int] = Field(default=1, description="1-based column number")
    instruction: Optional[str] = Field(default="", description="Custom instruction from Developer or Supervisor")
    source: Literal["supervisor", "developer"] = Field(default="supervisor", description="Originator of the instruction")
    selectedCode: Optional[str] = Field(default="", description="The specific code on or around the marked line")
    surroundingCode: Optional[str] = Field(default="", description="Broader document context (e.g. 15 lines before and after)")
    language: Optional[str] = Field(default="plaintext", description="Language id, e.g. python, typescript, etc.")
    timestamp: float = Field(default_factory=lambda: time.time(), description="Creation timestamp in epoch seconds")


class DebugAgentPayload(BaseModel):
    """Specific structured payload returned by Debugging Model"""
    detectedIssue: str = Field(description="Identification of the bug, edge case or risk")
    evidenceReasoning: str = Field(description="Why this is problematic and how it fails")
    possibleCause: str = Field(description="Root cause or underlying mechanism")
    justification: str = Field(default="", description="Technical justification for diagnosis and why this fix is the optimal approach")
    maintenanceChecks: List[str] = Field(default_factory=list, description="Automated maintenance checks (antipatterns, technical debt, typing, complexity)")
    maintenanceScore: Literal["clean", "moderate_debt", "high_risk"] = Field(default="clean", description="Overall health rating of inspected code")
    maintenanceRecommendations: List[str] = Field(default_factory=list, description="Preventative maintenance recommendations")
    suggestedFix: str = Field(description="Precise replacement code or proposed diff")
    originalCodeSnippet: Optional[str] = Field(default=None, description="Exact snippet to be replaced")
    confidence: Literal["high", "medium", "low"] = Field(default="high", description="Confidence level of detection")
    requiresPermission: bool = Field(default=True, description="Strict rule: user permission required before applying")


class TestCaseItem(BaseModel):
    name: str
    description: str
    inputs: Optional[str] = ""
    expected: Optional[str] = ""


class TestAgentPayload(BaseModel):
    """Specific structured payload returned by Testing Model"""
    whatShouldBeTested: str = Field(description="Summary of critical behaviors to verify")
    testCases: List[TestCaseItem] = Field(default_factory=list, description="Concrete unit test scenarios")
    edgeCases: List[str] = Field(default_factory=list, description="Edge cases, boundaries, error cases")
    expectedBehavior: str = Field(description="Expected behavior specification")
    generatedTestCode: Optional[str] = Field(default="", description="Ready-to-run test function or suite")
    executionResult: Optional[str] = Field(default=None, description="Test runner output if executed")


class ExplainAgentPayload(BaseModel):
    """Specific structured payload returned by ExplainAgent"""
    summary: str = Field(description="Concise overview of the code")
    detailedExplanation: str = Field(description="Step-by-step breakdown")
    importantConcepts: List[str] = Field(default_factory=list, description="Core programming concepts")
    relevantDependencies: List[str] = Field(default_factory=list, description="Dependencies")
    learningPoints: List[str] = Field(default_factory=list, description="Learning points")


class AgentResult(BaseModel):
    """
    Standardized worker response returned strictly to the Supervisor.
    """
    taskId: str
    agent: Literal["debug", "test", "explain"]
    status: Literal["running", "completed", "failed"]
    summary: Optional[str] = None
    details: Optional[str] = None
    error: Optional[str] = None
    instruction: Optional[str] = None
    source: Optional[str] = "supervisor"
    timestamp: float = Field(default_factory=lambda: time.time())
    
    # Typed payload objects corresponding to agent type
    debugData: Optional[DebugAgentPayload] = None
    testData: Optional[TestAgentPayload] = None
    explainData: Optional[ExplainAgentPayload] = None
    
    # Supervisor verbal message synthesized for the developer
    supervisorVerdict: Optional[str] = None


class SupervisorEvent(BaseModel):
    """
    Structured timeline event maintained in the Supervisor event history.
    """
    id: str
    type: str = Field(description="Event category: e.g. marker_created, task_dispatched, task_completed, task_failed")
    timestamp: float = Field(default_factory=lambda: time.time())
    taskId: Optional[str] = None
    agent: Optional[str] = None
    filePath: Optional[str] = None
    line: Optional[int] = None
    message: str
    status: Literal["info", "running", "success", "error"] = "info"
    metadata: Dict[str, Any] = Field(default_factory=dict)
