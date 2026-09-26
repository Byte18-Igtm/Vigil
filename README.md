🛡️ Vigil
Multi-agent bug fixing with human approval

AI finds the bug. AI proposes the fix. You decide. Nothing changes in your code until you approve it, and real tests prove it worked.

Built for the IBM Bob 2.0 Hackathon, with IBM Bob as our main builder.

🌐 Live demo: https://vigil-site.onrender.com · 🎥 Demo video: add link · 📊 Slides: add link

💡 The problem

AI coding assistants are fast, but they can change code on their own. That leaves teams with three hard questions:

Can we trust this change? Nobody reviewed it.
Did it actually fix anything? There's no proof.
Who approved it, and why? There's no record.

So teams face a choice: move fast with AI, or stay in control. Vigil removes that trade-off.

✨ What Vigil does
Step	What happens
🔍 Scan	Vigil runs the project's tests and finds the failing one on its own. No one needs to write a bug report.
🤖 Investigate	Two specialist AI agents work in parallel: a Debug Agent finds the root cause and proposes a fix, and a Test Agent independently analyses the failure.
🧠 Combine	The Supervisor cross-checks both agents, chooses one fix, and points at the exact line where the bug is.
⏸️ Pause	The full proposal is shown (diff, reasoning, evidence), marked "Proposed: nothing has been applied."
✅ Approve or reject	The developer decides. Approval is locked to the exact patch shown; if it changes, the approval is refused.
🧪 Prove it	Only after approval, Vigil applies the fix on a separate branch and runs the real tests: failing before, passing after.
📜 Record it	Every decision goes into an audit trail, exportable as Markdown or JSON.
🌟 What makes Vigil different
Two agents that check each other. A fix is chosen because the Test Agent's evidence corroborates the Debug Agent, not on confidence alone.
Approval you can trust. Each proposal has a unique fingerprint, so you can only approve the exact change you reviewed.
Proof, not promises. Real test runs, before and after, with the real output shown.
Honest by design. Broken or do-nothing fixes are rejected automatically, the offline demo mode is clearly labelled, and the UI never claims something happened when it didn't.
Points at the problem. The code view highlights the exact buggy line, like an editor would.
🏗️ How it works
text
             ┌───────────────────────────┐
             │   Web interface (React)   │
             └─────────────┬─────────────┘
                           │
             ┌─────────────▼─────────────┐
             │   Supervisor (FastAPI)    │
             │  state machine · approval │
             └──────┬─────────────┬──────┘
                    │  parallel   │
          ┌─────────▼───┐   ┌─────▼───────┐
          │ Debug Agent │   │ Test Agent  │
          └─────────┬───┘   └─────┬───────┘
                    └──────┬──────┘
             ┌─────────────▼─────────────┐
             │ One proposal + evidence   │
             │ "nothing has been applied"│
             └─────────────┬─────────────┘
                   Human approves?
                 ┌─────────┴─────────┐
               Yes                   No
     apply on vigil/<id> branch   nothing changes
        run real tests ✔           (logged)
🔐 Security & trust
🚫 Nothing is applied without approval, and approval must match the exact patch.
🌿 Fixes go onto a separate git branch, only on a clean working tree.
👀 Agents are read-only: they propose changes and never write files.
📁 Vigil only works inside allowed project folders. The public demo runs on an isolated sample project.
🙈 Secrets are redacted from logs and reports; keys are never stored in code.
📜 Every approval and rejection is recorded in an audit trail.
🧰 Built with
IBM Bob 2.0: our main builder of the supervisor, approval gate, agent integration, API and web interface
Python + FastAPI for the backend and orchestration
React + Vite + Tailwind for the web interface
Groq (gpt-oss-120b) powering the AI agents
Render for hosting the live demo
pytest: 271 automated tests, including the approval gate, concurrent approvals and patching against real git repositories
🌐 Try it online
Open https://vigil-site.onrender.com. The first load can take up to a minute while the free server wakes up.
Click Scan for bugs. Vigil finds the failing test in the sample project.
Tick the consent box and click Analyse.
Review the highlighted line, the diff and the agents' reasoning, then click Approve or Reject.

The live demo uses one shared sample project. If Scan reports "All tests pass", someone has already approved the fix, which shows it worked!

🚀 Run it locally

Requirements: Python 3.9+, Node.js 18+, git

Backend

bash
cd Supervisor
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/setup_demo_repo.py --force
.venv/bin/python scripts/run_api.py

Web interface (in a second terminal)

bash
cd ai-developer-assistant
npm install
VITE_DEMO_REPO_PATH="$(cd ../Supervisor/demo_target && pwd)" npm run dev

Open http://127.0.0.1:5173, then click Scan for bugs → Analyse → Approve or Reject.

It runs in a clearly labelled demo mode out of the box. Real AI mode uses Groq-powered agents; see Supervisor/STUBS.md for configuration.

🔭 What's next
💬 Ask Vigil: question the AI about a fix before approving it
🔄 Revise: redirect the agents to a different approach
👥 Team roles: control who can approve changes
📦 Safe project upload: analyse external projects in an isolated sandbox
👩‍💻 Team
Name	Role
Hannah Ahmed	Supervisor, integration & approval gate
Nancy S	Debug & Test agents
Sanmathi S Ambi	Frontend
Shamanth N	Research, presentation & testing
