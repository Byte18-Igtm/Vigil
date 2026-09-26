import time
import os
from typing import Optional
from .base_agent import BaseWorkerAgent
from ..protocol.agent_types import AgentTask, AgentResult
from ..llm.engine import CodeIntelligenceEngine


class ExplainAgent(BaseWorkerAgent):
    """
    Worker Agent specialized in explaining marked code regions.
    Extracts summary, detailed breakdown, core concepts, dependencies, and learning points.
    """

    def __init__(self, engine: Optional[CodeIntelligenceEngine] = None):
        super().__init__(name="explain", intelligence_engine=engine)

    def execute(self, task: AgentTask) -> AgentResult:
        validation_error = self.validate_task(task)
        if validation_error:
            return self.create_failure_result(task, validation_error)

        try:
            payload = self.engine.explain_code(task)
            
            # Format high-level details for readability
            concepts_bulleted = "\n".join(f"- **{c}**" for c in payload.importantConcepts)
            deps_bulleted = "\n".join(f"- `{d}`" for d in payload.relevantDependencies) if payload.relevantDependencies else "- None detected"
            learning_bulleted = "\n".join(f"- {lp}" for lp in payload.learningPoints)

            formatted_details = (
                f"{payload.detailedExplanation}\n\n"
                f"### Important Concepts\n{concepts_bulleted}\n\n"
                f"### Dependencies & Context\n{deps_bulleted}\n\n"
                f"### Potential Learning Points\n{learning_bulleted}"
            )

            return AgentResult(
                taskId=task.id,
                agent="explain",
                status="completed",
                summary=payload.summary,
                details=formatted_details,
                explainData=payload,
                timestamp=time.time()
            )
        except Exception as e:
            return self.create_failure_result(task, f"ExplainAgent encountered an error: {str(e)}")
