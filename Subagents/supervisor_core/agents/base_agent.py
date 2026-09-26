from abc import ABC, abstractmethod
import time
from typing import Optional
from ..protocol.agent_types import AgentTask, AgentResult
from ..llm.engine import CodeIntelligenceEngine


class BaseWorkerAgent(ABC):
    """
    Abstract base class for all specialized worker agents.
    Enforces standardized execution, context processing, and error handling.
    Workers communicate ONLY with the Supervisor Agent.
    """

    def __init__(self, name: str, intelligence_engine: Optional[CodeIntelligenceEngine] = None):
        self.name = name
        self.engine = intelligence_engine or CodeIntelligenceEngine()

    @abstractmethod
    def execute(self, task: AgentTask) -> AgentResult:
        """
        Executes the worker's domain-specific task and returns a structured AgentResult.
        """
        pass

    def validate_task(self, task: AgentTask) -> Optional[str]:
        """
        Performs defensive validation of incoming task context.
        Returns an error message if invalid, or None if valid.
        """
        if not task.filePath:
            return "Task filePath cannot be empty."
        if task.line < 1:
            return f"Invalid line number {task.line}. Line numbers must be 1-indexed."
        if not task.selectedCode and not task.surroundingCode:
            return "No code context provided for analysis."
        return None

    def create_failure_result(self, task: AgentTask, error_msg: str) -> AgentResult:
        return AgentResult(
            taskId=task.id,
            agent=task.type,
            status="failed",
            error=error_msg,
            timestamp=time.time()
        )
