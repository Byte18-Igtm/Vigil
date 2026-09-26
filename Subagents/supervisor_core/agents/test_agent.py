import subprocess
import tempfile
import time
import os
from typing import Optional
from .base_agent import BaseWorkerAgent
from ..protocol.agent_types import AgentTask, AgentResult
from ..llm.engine import CodeIntelligenceEngine


class TestAgent(BaseWorkerAgent):
    """
    Worker Agent specialized in test generation, coverage analysis, and verification.
    Returns what should be tested, test cases, edge cases, expected behavior, and execution status.
    """
    __test__ = False

    def __init__(self, engine: Optional[CodeIntelligenceEngine] = None):
        super().__init__(name="test", intelligence_engine=engine)

    def execute(self, task: AgentTask) -> AgentResult:
        validation_error = self.validate_task(task)
        if validation_error:
            return self.create_failure_result(task, validation_error)

        try:
            payload = self.engine.test_code(task)

            # Test execution check
            exec_output = payload.executionResult
            if (task.language or "").lower() == "python" and payload.generatedTestCode:
                try:
                    # Validate syntax of generated test code
                    compile(payload.generatedTestCode, "<test>", "exec")
                    exec_output = "✓ Generated test code is valid Python syntax. Ready for pytest runner."
                except Exception as syntax_err:
                    exec_output = f"⚠ Test code syntax note: {syntax_err}"

            # Format test cases
            tc_blocks = []
            for tc in payload.testCases:
                tc_blocks.append(
                    f"- **{tc.name}**\n"
                    f"  - *Scenario*: {tc.description}\n"
                    f"  - *Inputs*: `{tc.inputs}`\n"
                    f"  - *Expected*: `{tc.expected}`"
                )
            tc_formatted = "\n".join(tc_blocks) if tc_blocks else "- General boundary validation"

            edge_cases_bulleted = "\n".join(f"- `{ec}`" for ec in payload.edgeCases) if payload.edgeCases else "- None specified"

            code_block = (
                f"```{task.language or 'python'}\n"
                f"{payload.generatedTestCode}\n"
                f"```"
            ) if payload.generatedTestCode else "*No code generated*"

            formatted_details = (
                f"### What Should Be Tested\n{payload.whatShouldBeTested}\n\n"
                f"### Test Cases\n{tc_formatted}\n\n"
                f"### Edge Cases & Boundaries\n{edge_cases_bulleted}\n\n"
                f"### Expected Behavior\n{payload.expectedBehavior}\n\n"
                f"### Generated Test Suite\n{code_block}\n\n"
                f"### Test Execution Status\n{exec_output or 'Ready for execution'}"
            )

            return AgentResult(
                taskId=task.id,
                agent="test",
                status="completed",
                summary=f"Test plan generated: {len(payload.testCases)} cases formulated",
                details=formatted_details,
                testData=payload,
                timestamp=time.time()
            )
        except Exception as e:
            return self.create_failure_result(task, f"TestAgent encountered an error: {str(e)}")
