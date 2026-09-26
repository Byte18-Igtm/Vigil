import os
import pytest
from supervisor_core.protocol.agent_types import AgentTask
from supervisor_core.supervisor.supervisor_agent import SupervisorAgent
from supervisor_core.agents.explain_agent import ExplainAgent
from supervisor_core.agents.debug_agent import DebugAgent
from supervisor_core.agents.test_agent import TestAgent


@pytest.fixture
def supervisor():
    return SupervisorAgent()


@pytest.fixture
def sample_file_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "sample_code.py"))


def test_supervisor_registration(supervisor):
    assert "explain" in supervisor._workers
    assert "debug" in supervisor._workers
    assert "test" in supervisor._workers


def test_explain_agent_execution(supervisor, sample_file_path):
    supervisor.register_marker(sample_file_path, 8)
    result = supervisor.dispatch_request(
        agent_type="explain",
        file_path=sample_file_path,
        line=8,
        selected_code="final_price = price - (price * discount_percent)",
        surrounding_code="def calculate_discount(price, discount_percent=0.1):\n    final_price = price - (price * discount_percent)\n    return round(final_price, 2)",
        language="python"
    )

    assert result.status == "completed"
    assert result.agent == "explain"
    assert result.explainData is not None
    assert "final_price" in result.summary or "Line 8" in result.summary
    assert len(result.explainData.importantConcepts) > 0
    assert result.supervisorVerdict is not None
    assert "ExplainAgent" in result.supervisorVerdict


def test_debug_agent_execution(supervisor, sample_file_path):
    supervisor.register_marker(sample_file_path, 13)
    result = supervisor.dispatch_request(
        agent_type="debug",
        file_path=sample_file_path,
        line=13,
        selected_code="result = a / b",
        surrounding_code="def risky_divide(a, b):\n    result = a / b\n    return result",
        language="python"
    )

    assert result.status == "completed"
    assert result.agent == "debug"
    assert result.debugData is not None
    assert result.debugData.suggestedFix is not None
    assert result.debugData.requiresPermission is True
    # Verify justification is provided
    assert len(result.debugData.justification) > 10
    # Verify maintenance checks are performed
    assert len(result.debugData.maintenanceChecks) > 0
    assert result.debugData.maintenanceScore in ["clean", "moderate_debt", "high_risk"]
    assert "DebugAgent" in result.supervisorVerdict
    assert "Health:" in result.supervisorVerdict or "Code Health:" in result.supervisorVerdict


def test_test_agent_execution(supervisor, sample_file_path):
    supervisor.register_marker(sample_file_path, 5)
    result = supervisor.dispatch_request(
        agent_type="test",
        file_path=sample_file_path,
        line=5,
        selected_code="def calculate_discount(price, discount_percent=0.1):",
        surrounding_code="def calculate_discount(price, discount_percent=0.1):\n    return price",
        language="python"
    )

    assert result.status == "completed"
    assert result.agent == "test"
    assert result.testData is not None
    assert len(result.testData.testCases) > 0
    assert len(result.testData.edgeCases) > 0
    assert "def test_" in result.testData.generatedTestCode
    assert "TestAgent" in result.supervisorVerdict


def test_event_history_tracking(supervisor, sample_file_path):
    supervisor.register_marker(sample_file_path, 10)
    supervisor.dispatch_request(
        agent_type="debug",
        file_path=sample_file_path,
        line=10,
        selected_code="print('test')",
        surrounding_code="print('test')",
        language="python"
    )

    events = supervisor.get_event_history()
    assert len(events) >= 3
    event_types = [e.type for e in events]
    assert "marker_created" in event_types
    assert "request_received" in event_types
    assert "worker_completed" in event_types


def test_developer_instruction_to_debugging_model(supervisor, sample_file_path):
    result = supervisor.dispatch_request(
        agent_type="debug",
        file_path=sample_file_path,
        line=13,
        selected_code="result = a / b",
        surrounding_code="def risky_divide(a, b):\n    result = a / b",
        language="python",
        instruction="Verify division by zero boundary handling",
        source="developer"
    )

    assert result.status == "completed"
    assert result.agent == "debug"
    assert result.debugData is not None
    assert result.instruction == "Verify division by zero boundary handling"
    assert result.source == "developer"
    assert "DebugAgent" in result.supervisorVerdict
    assert "Verify division by zero" in result.supervisorVerdict


def test_developer_instruction_to_testing_model(supervisor, sample_file_path):
    result = supervisor.dispatch_request(
        agent_type="test",
        file_path=sample_file_path,
        line=5,
        selected_code="def calculate_discount(price, discount_percent=0.1):",
        surrounding_code="def calculate_discount(price, discount_percent=0.1):\n    return price",
        language="python",
        instruction="Generate tests with negative price values",
        source="developer"
    )

    assert result.status == "completed"
    assert result.agent == "test"
    assert result.testData is not None
    assert result.instruction == "Generate tests with negative price values"
    assert result.source == "developer"
    assert any("negative price values" in tc.description for tc in result.testData.testCases)
    assert "TestAgent" in result.supervisorVerdict
