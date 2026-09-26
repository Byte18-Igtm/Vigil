import sys
import os
import uvicorn

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add workspace directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    port = int(os.getenv("SUPERVISOR_PORT", 8765))
    host = os.getenv("SUPERVISOR_HOST", "127.0.0.1")
    print(f"============================================================")
    print(f" Supervisor AI Agent Server - Antigravity Orchestrator")
    print(f" Port: {port} | Host: {host}")
    print(f" Workers: ExplainAgent, DebugAgent, TestAgent")
    print(f"============================================================")
    uvicorn.run("supervisor_core.server.api_server:app", host=host, port=port, log_level="info")
