import time
import uuid
from typing import Callable, List, Optional
from ..protocol.agent_types import SupervisorEvent


class SupervisorEventLog:
    """
    Maintains a structured, chronological event log of all supervisor actions,
    marker occurrences, agent dispatches, and completions.
    """

    def __init__(self):
        self._events: List[SupervisorEvent] = []
        self._subscribers: List[Callable[[SupervisorEvent], None]] = []

    def record(
        self,
        event_type: str,
        message: str,
        task_id: Optional[str] = None,
        agent: Optional[str] = None,
        file_path: Optional[str] = None,
        line: Optional[int] = None,
        status: str = "info",
        metadata: Optional[dict] = None
    ) -> SupervisorEvent:
        event = SupervisorEvent(
            id=str(uuid.uuid4())[:8],
            type=event_type,
            timestamp=time.time(),
            taskId=task_id,
            agent=agent,
            filePath=file_path,
            line=line,
            message=message,
            status=status,
            metadata=metadata or {}
        )
        self._events.append(event)
        self._notify_subscribers(event)
        return event

    def subscribe(self, callback: Callable[[SupervisorEvent], None]):
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[SupervisorEvent], None]):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _notify_subscribers(self, event: SupervisorEvent):
        for sub in self._subscribers:
            try:
                sub(event)
            except Exception:
                pass

    def get_all(self) -> List[SupervisorEvent]:
        return list(self._events)

    def clear(self):
        self._events.clear()
