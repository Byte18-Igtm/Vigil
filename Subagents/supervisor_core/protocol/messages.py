from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field
from .agent_types import AgentResult, AgentTask, SupervisorEvent


class RunAgentMessage(BaseModel):
    type: Literal["runAgent"] = "runAgent"
    agent: Literal["explain", "debug", "test"]
    task: AgentTask


class ClearHistoryMessage(BaseModel):
    type: Literal["clearHistory"] = "clearHistory"


class ApplyFixMessage(BaseModel):
    type: Literal["applyFix"] = "applyFix"
    taskId: str
    filePath: str
    line: int
    originalCode: str
    suggestedFix: str


class RunTestCodeMessage(BaseModel):
    type: Literal["runTestCode"] = "runTestCode"
    taskId: str
    filePath: str
    testCode: str
    language: str


WebviewMessage = Union[RunAgentMessage, ClearHistoryMessage, ApplyFixMessage, RunTestCodeMessage]


class EventExtensionMessage(BaseModel):
    type: Literal["event"] = "event"
    event: SupervisorEvent


class ResultExtensionMessage(BaseModel):
    type: Literal["result"] = "result"
    result: AgentResult


class StatusExtensionMessage(BaseModel):
    type: Literal["status"] = "status"
    status: Literal["idle", "running", "completed", "error"]
    activeAgent: Optional[str] = None
    activeFile: Optional[str] = None
    activeLine: Optional[int] = None
    message: Optional[str] = None


class HistoryExtensionMessage(BaseModel):
    type: Literal["history"] = "history"
    events: List[SupervisorEvent]
    results: List[AgentResult]


ExtensionMessage = Union[
    EventExtensionMessage,
    ResultExtensionMessage,
    StatusExtensionMessage,
    HistoryExtensionMessage,
]
