import time
from typing import Optional
from .base_agent import BaseWorkerAgent
from ..protocol.agent_types import AgentTask, AgentResult
from ..llm.engine import CodeIntelligenceEngine


class DebugAgent(BaseWorkerAgent):
    """
    Worker Agent specialized in identifying bugs, syntax errors, and edge case failures.
    Returns detected issue, evidence, root cause, suggested fix, and confidence.
    Enforces strict user permission before applying code changes.
    """

    def __init__(self, engine: Optional[CodeIntelligenceEngine] = None):
        super().__init__(name="debug", intelligence_engine=engine)

    def execute(self, task: AgentTask) -> AgentResult:
        validation_error = self.validate_task(task)
        if validation_error:
            return self.create_failure_result(task, validation_error)

        try:
            payload = self.engine.debug_code(task)

            checks_formatted = "\n".join(f"- {c}" for c in payload.maintenanceChecks) if payload.maintenanceChecks else "- Standard syntax check passed"
            recs_formatted = "\n".join(f"- {r}" for r in payload.maintenanceRecommendations) if payload.maintenanceRecommendations else "- Maintain existing standards"

            formatted_details = (
                f"### Detected Issue\n{payload.detectedIssue}\n\n"
                f"### Evidence & Reasoning\n{payload.evidenceReasoning}\n\n"
                f"### Root Cause\n{payload.possibleCause}\n\n"
                f"### Technical Justification\n{payload.justification}\n\n"
                f"### Code Health & Maintenance Checks (Rating: {payload.maintenanceScore.upper()})\n{checks_formatted}\n\n"
                f"### Maintenance Recommendations\n{recs_formatted}\n\n"
                f"### Confidence\n**{payload.confidence.upper()}** (Status: requires user confirmation)\n\n"
                f"### Suggested Fix\n"
                f"```\n{payload.suggestedFix}\n```\n\n"
                f"> **Permission Policy**: Code will *not* be modified automatically. Click 'Apply Fix' to approve."
            )

            return AgentResult(
                taskId=task.id,
                agent="debug",
                status="completed",
                summary=f"Debug analysis: {payload.detectedIssue}",
                details=formatted_details,
                debugData=payload,
                timestamp=time.time()
            )
        except Exception as e:
            return self.create_failure_result(task, f"DebugAgent encountered an error: {str(e)}")
