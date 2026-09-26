from typing import Dict, List, Optional
from ..protocol.agent_types import AgentTask, AgentResult


class TaskManager:
    """
    Tracks tasks dispatched by the Supervisor Agent to Worker Agents.
    Stores task states and corresponding worker results.
    """

    def __init__(self):
        self._tasks: Dict[str, AgentTask] = {}
        self._results: Dict[str, AgentResult] = {}

    def register_task(self, task: AgentTask):
        self._tasks[task.id] = task

    def record_result(self, result: AgentResult):
        self._results[result.taskId] = result

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        return self._tasks.get(task_id)

    def get_result(self, task_id: str) -> Optional[AgentResult]:
        return self._results.get(task_id)

    def get_all_results(self) -> List[AgentResult]:
        return list(self._results.values())

    def clear(self):
        self._tasks.clear()
        self._results.clear()
