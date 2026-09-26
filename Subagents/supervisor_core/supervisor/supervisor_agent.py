import os
import time
import uuid
from typing import Callable, Dict, List, Optional
from ..protocol.agent_types import AgentTask, AgentResult, SupervisorEvent
from ..agents.base_agent import BaseWorkerAgent
from ..agents.explain_agent import ExplainAgent
from ..agents.debug_agent import DebugAgent
from ..agents.test_agent import TestAgent
from ..llm.engine import CodeIntelligenceEngine
from .event_log import SupervisorEventLog
from .task_manager import TaskManager


class SupervisorAgent:
    """
    Central Orchestrator Agent.
    
    Principles:
    1. The Supervisor does NOT perform domain tasks itself.
    2. It assigns tasks to registered Worker Agents (ExplainAgent, DebugAgent, TestAgent).
    3. Worker Agents return structured results ONLY to the Supervisor.
    4. The Supervisor synthesizes the results and communicates verbally with the developer.
    5. Maintains full event logs and manages Side Bot Webview state.
    """

    def __init__(self, engine: Optional[CodeIntelligenceEngine] = None):
        self.engine = engine or CodeIntelligenceEngine()
        self.event_log = SupervisorEventLog()
        self.task_manager = TaskManager()
        self._workers: Dict[str, BaseWorkerAgent] = {}
        self._status_listeners: List[Callable[[str, Optional[str]], None]] = []

        # Register default specialized worker agents
        self.register_worker("explain", ExplainAgent(self.engine))
        self.register_worker("debug", DebugAgent(self.engine))
        self.register_worker("test", TestAgent(self.engine))

    def register_worker(self, agent_type: str, worker: BaseWorkerAgent):
        """Allows dynamic registration of workers (e.g. RefactorAgent, SecurityAgent)."""
        self._workers[agent_type.lower()] = worker

    def register_marker(self, file_path: str, line: int):
        """Called when user creates a 🔵 circle marker in the editor."""
        short_file = os.path.basename(file_path)
        self.event_log.record(
            event_type="marker_created",
            message=f"🔵 Marker created at {short_file}:{line}",
            file_path=file_path,
            line=line,
            status="info"
        )

    def dispatch_request(
        self,
        agent_type: str,
        file_path: str,
        line: int,
        column: int = 1,
        selected_code: str = "",
        surrounding_code: str = "",
        language: str = "plaintext",
        instruction: str = "",
        source: str = "supervisor"
    ) -> AgentResult:
        """
        Main entry point for handling an Explain, Debug, or Test request from the user/UI.
        Workers (models) receive instructions either from Supervisor or directly from Developer.
        """
        short_file = os.path.basename(file_path)
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        instruction_note = f" (Instruction: '{instruction[:40]}...')" if instruction else ""

        # 1. Log request received by Supervisor
        req_msg = f"{agent_type.capitalize()} requested for {short_file}:{line}{instruction_note} [Source: {source}]"
        self.event_log.record(
            event_type="request_received",
            message=req_msg,
            task_id=task_id,
            agent=agent_type,
            file_path=file_path,
            line=line,
            status="info"
        )

        # 2. Select Worker Model / Agent
        worker = self._workers.get(agent_type.lower())
        if not worker:
            err_msg = f"No worker model registered for task type '{agent_type}'."
            self.event_log.record(
                event_type="task_failed",
                message=f"Supervisor failed to route task: {err_msg}",
                task_id=task_id,
                agent=agent_type,
                file_path=file_path,
                line=line,
                status="error"
            )
            return AgentResult(
                taskId=task_id,
                agent=agent_type,
                status="failed",
                error=err_msg,
                instruction=instruction,
                source=source,
                timestamp=time.time()
            )

        # 3. Create structured AgentTask
        task = AgentTask(
            id=task_id,
            type=agent_type.lower(),
            filePath=file_path,
            line=line,
            column=column,
            instruction=instruction,
            source=source,
            selectedCode=selected_code,
            surroundingCode=surrounding_code,
            language=language,
            timestamp=time.time()
        )
        self.task_manager.register_task(task)

        # 4. Notify Side Bot that worker is executing
        self._notify_status("running", f"{worker.name.capitalize()}Agent is working...")
        self.event_log.record(
            event_type="worker_dispatched",
            message=f"Supervisor → {worker.name.capitalize()}Agent",
            task_id=task_id,
            agent=worker.name,
            file_path=file_path,
            line=line,
            status="running"
        )

        # 5. Worker executes task in isolation
        try:
            result = worker.execute(task)
        except Exception as e:
            result = worker.create_failure_result(task, f"Unexpected error in {worker.name}Agent: {str(e)}")

        # 6. Supervisor receives worker result
        result.instruction = task.instruction
        result.source = task.source

        if result.status == "completed":
            # Synthesize verbal message for developer
            payload_obj = result.explainData or result.debugData or result.testData
            verdict = self.engine.synthesize_supervisor_verdict(task, agent_type, payload_obj)
            result.supervisorVerdict = verdict

            # Record result in task manager
            self.task_manager.record_result(result)

            # Log completion event
            self.event_log.record(
                event_type="worker_completed",
                message=f"{worker.name.capitalize()}Agent completed analysis",
                task_id=task_id,
                agent=worker.name,
                file_path=file_path,
                line=line,
                status="success"
            )
            self._notify_status("completed", f"✓ {agent_type.capitalize()} ready")
        else:
            self.task_manager.record_result(result)
            self.event_log.record(
                event_type="worker_failed",
                message=f"⚠ {worker.name.capitalize()}Agent failed: {result.error}",
                task_id=task_id,
                agent=worker.name,
                file_path=file_path,
                line=line,
                status="error"
            )
            self._notify_status("error", f"⚠ {agent_type.capitalize()} failed")

        return result

    def get_event_history(self) -> List[SupervisorEvent]:
        return self.event_log.get_all()

    def get_all_results(self) -> List[AgentResult]:
        return self.task_manager.get_all_results()

    def clear_history(self):
        self.event_log.clear()
        self.task_manager.clear()
        self._notify_status("idle", "Ready")

    def subscribe_status(self, callback: Callable[[str, Optional[str]], None]):
        self._status_listeners.append(callback)

    def _notify_status(self, status: str, message: Optional[str] = None):
        for listener in self._status_listeners:
            try:
                listener(status, message)
            except Exception:
                pass
