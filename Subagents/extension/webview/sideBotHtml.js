/**
 * Produces clean, professional HTML for the Supervisor Side Bot Webview.
 * Implements the Antigravity architecture with two worker models (Debugging & Testing)
 * receiving instructions from Developer or Supervisor and sending responses to Supervisor.
 */
function getSideBotContent(webview, extensionUri) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Supervisor Bot — AI Coding Assistant</title>
  <style>
    :root {
      --bg-color: var(--vscode-sideBar-background, #1e1e1e);
      --card-bg: var(--vscode-editor-background, #252526);
      --border-color: var(--vscode-widget-border, #333333);
      --text-main: var(--vscode-editor-foreground, #cccccc);
      --text-muted: var(--vscode-descriptionForeground, #858585);
      --accent-blue: #3b82f6;
      --accent-green: #10b981;
      --accent-red: #ef4444;
      --accent-amber: #f59e0b;
      --code-bg: var(--vscode-textCodeBlock-background, #181818);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background-color: var(--bg-color);
      color: var(--text-main);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      font-size: 12px;
      line-height: 1.4;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }

    /* Header */
    .bot-header {
      padding: 10px 12px;
      background: linear-gradient(180deg, rgba(59, 130, 246, 0.08) 0%, transparent 100%);
      border-bottom: 1px solid var(--border-color);
      flex-shrink: 0;
    }

    .bot-title {
      font-size: 13px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 6px;
      color: var(--text-main);
    }

    /* Antigravity Two-Model Constellation: Debugging <-> Supervisor <-> Testing */
    .constellation {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      margin: 8px 0 4px 0;
      padding: 6px;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 6px;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .node {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 3px;
      font-size: 10px;
      color: var(--text-muted);
      transition: all 0.3s ease;
    }

    .node-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #444;
      border: 2px solid #555;
      transition: all 0.3s ease;
    }

    .node.supervisor .node-dot {
      width: 18px;
      height: 18px;
      background: var(--accent-blue);
      border-color: #60a5fa;
      box-shadow: 0 0 10px rgba(59, 130, 246, 0.4);
    }

    .node.supervisor { font-weight: 600; color: #93c5fd; }

    .node.active .node-dot {
      background: var(--accent-green);
      border-color: #34d399;
      box-shadow: 0 0 10px rgba(16, 185, 129, 0.6);
      transform: scale(1.3);
    }
    .node.active { color: var(--accent-green); font-weight: 600; }

    .connector-line {
      height: 2px;
      width: 20px;
      background: #444;
    }

    /* Status Bar */
    .status-bar {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 4px;
    }

    .status-pulse {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--accent-green);
      flex-shrink: 0;
    }
    .status-pulse.running {
      background: var(--accent-blue);
      animation: pulse 1.2s infinite;
    }
    @keyframes pulse {
      0% { transform: scale(0.9); opacity: 0.7; }
      50% { transform: scale(1.3); opacity: 1; }
      100% { transform: scale(0.9); opacity: 0.7; }
    }

    /* Chat Messages Stream */
    .chat-container {
      flex: 1;
      overflow-y: auto;
      padding: 10px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .msg-card {
      border-radius: 6px;
      padding: 10px 12px;
      font-size: 12px;
      line-height: 1.45;
    }

    .msg-developer {
      align-self: flex-end;
      background: rgba(59, 130, 246, 0.2);
      border: 1px solid rgba(59, 130, 246, 0.4);
      color: #bfdbfe;
      max-width: 90%;
    }

    .msg-developer-header {
      font-size: 10px;
      color: #93c5fd;
      font-weight: 600;
      margin-bottom: 2px;
      text-transform: uppercase;
    }

    .msg-supervisor {
      align-self: flex-start;
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      width: 100%;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
    }

    .supervisor-card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
    }

    .model-badge {
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 700;
      text-transform: uppercase;
    }
    .badge-debug { background: rgba(239, 68, 68, 0.2); color: #f87171; }
    .badge-test { background: rgba(16, 185, 129, 0.2); color: #34d399; }

    .verdict-box {
      background: rgba(59, 130, 246, 0.08);
      border-left: 3px solid var(--accent-blue);
      padding: 6px 8px;
      font-style: italic;
      color: var(--text-main);
      margin-bottom: 8px;
      font-size: 11.5px;
    }

    /* Justification & Maintenance Boxes */
    .justification-box {
      background: rgba(139, 92, 246, 0.08);
      border-left: 3px solid #8b5cf6;
      padding: 6px 8px;
      font-size: 11px;
      color: #e9d5ff;
      margin-bottom: 8px;
      border-radius: 0 4px 4px 0;
      line-height: 1.4;
    }

    .maintenance-box {
      background: rgba(16, 185, 129, 0.06);
      border: 1px solid rgba(16, 185, 129, 0.2);
      border-radius: 6px;
      padding: 8px 10px;
      margin-bottom: 8px;
      font-size: 11px;
    }

    .health-pill {
      font-size: 9px;
      padding: 2px 6px;
      border-radius: 10px;
      font-weight: 700;
      letter-spacing: 0.5px;
    }
    .health-clean { background: rgba(16, 185, 129, 0.25); color: #34d399; }
    .health-moderate_debt { background: rgba(245, 158, 11, 0.25); color: #fbbf24; }
    .health-high_risk { background: rgba(239, 68, 68, 0.25); color: #f87171; }

    .maint-list {
      list-style: none;
      padding: 0;
      margin: 4px 0 0 0;
      display: flex;
      flex-direction: column;
      gap: 3px;
    }
    .maint-list li {
      font-size: 10.5px;
      color: #cbd5e1;
    }

    .content-box {
      font-size: 11px;
      white-space: pre-wrap;
      word-break: break-word;
      color: var(--text-main);
      background: var(--code-bg);
      padding: 8px;
      border-radius: 4px;
      max-height: 220px;
      overflow-y: auto;
      font-family: 'Consolas', monospace;
    }

    .btn-group {
      display: flex;
      gap: 6px;
      margin-top: 8px;
    }

    .btn {
      padding: 4px 8px;
      font-size: 11px;
      font-weight: 500;
      border-radius: 4px;
      border: none;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: all 0.2s;
    }
    .btn-primary { background: var(--accent-blue); color: #fff; }
    .btn-primary:hover { background: #2563eb; }
    .btn-green { background: #059669; color: #fff; }
    .btn-green:hover { background: #10b981; }
    .btn-secondary { background: #333; color: var(--text-main); }
    .btn-secondary:hover { background: #444; }

    /* Bottom Input Dock */
    .bot-dock {
      padding: 10px;
      background: var(--card-bg);
      border-top: 1px solid var(--border-color);
      flex-shrink: 0;
    }

    .quick-chips {
      display: flex;
      gap: 6px;
      margin-bottom: 8px;
      overflow-x: auto;
      padding-bottom: 2px;
    }

    .chip {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: var(--text-muted);
      border-radius: 12px;
      padding: 2px 8px;
      font-size: 10px;
      cursor: pointer;
      white-space: nowrap;
    }
    .chip:hover {
      background: rgba(59, 130, 246, 0.15);
      color: #93c5fd;
      border-color: rgba(59, 130, 246, 0.3);
    }

    .input-row {
      display: flex;
      gap: 6px;
    }

    select, input {
      background: #141414;
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 6px 8px;
      border-radius: 4px;
      font-size: 11px;
      outline: none;
    }
    select:focus, input:focus { border-color: var(--accent-blue); }

    .input-text {
      flex: 1;
    }

    .select-model {
      width: 95px;
    }
  </style>
</head>
<body>

  <!-- Bot Header -->
  <div class="bot-header">
    <div class="bot-title">
      <span>🔵</span> Supervisor Bot
    </div>

    <!-- Antigravity Constellation: Debugging <-> Supervisor <-> Testing -->
    <div class="constellation">
      <div class="node" id="node-debug">
        <div class="node-dot"></div>
        <span>Debugging</span>
      </div>
      <div class="connector-line"></div>
      <div class="node supervisor" id="node-supervisor">
        <div class="node-dot"></div>
        <span>Supervisor</span>
      </div>
      <div class="connector-line"></div>
      <div class="node" id="node-test">
        <div class="node-dot"></div>
        <span>Testing</span>
      </div>
    </div>

    <!-- Activity Status -->
    <div class="status-bar">
      <div class="status-pulse" id="status-pulse"></div>
      <div id="status-text">Supervisor ready for developer instructions</div>
    </div>
  </div>

  <!-- Chat Messages Stream -->
  <div class="chat-container" id="chat-stream">
    <!-- Initial welcome message -->
    <div class="msg-card msg-supervisor">
      <div class="supervisor-card-header">
        <span style="font-weight: 600; color: #60a5fa;">🔵 Supervisor Orchestrator</span>
      </div>
      <div class="verdict-text">
        "Hello Developer! I coordinate two specialized worker models: <strong>Debugging Model</strong> and <strong>Testing Model</strong>. Give instructions below or mark any line with 🔵 in your editor. Both models report their findings back to me, and I verbally report the conclusions to you."
      </div>
    </div>
  </div>

  <!-- Bottom Input Dock -->
  <div class="bot-dock">
    <div class="quick-chips">
      <div class="chip" onclick="quickAction('debug', 'Find bugs, zero-division, and edge case failures')">🐞 Debug Active Line</div>
      <div class="chip" onclick="quickAction('test', 'Generate comprehensive pytest suite with edge cases')">🧪 Test Active Line</div>
      <div class="chip" onclick="vscode.postMessage({ type: 'markLine' })">🔵 Mark Line</div>
      <div class="chip" onclick="vscode.postMessage({ type: 'clearHistory' })">⚡ Clear</div>
    </div>
    <div class="input-row">
      <select id="model-select" class="select-model">
        <option value="debug">🐞 Debug</option>
        <option value="test">🧪 Test</option>
      </select>
      <input type="text" id="instruction-input" class="input-text" placeholder="Type instruction for model..." />
      <button class="btn btn-primary" id="btn-send">Send</button>
    </div>
  </div>

  <script>
    const vscode = acquireVsCodeApi();

    const chatStream = document.getElementById('chat-stream');
    const instructionInput = document.getElementById('instruction-input');
    const modelSelect = document.getElementById('model-select');
    const btnSend = document.getElementById('btn-send');
    const statusPulse = document.getElementById('status-pulse');
    const statusText = document.getElementById('status-text');

    window.quickAction = function(model, prompt) {
      modelSelect.value = model;
      instructionInput.value = prompt;
      submitInstruction();
    };

    btnSend.addEventListener('click', submitInstruction);
    instructionInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') submitInstruction();
    });

    function submitInstruction() {
      const text = instructionInput.value.trim();
      const model = modelSelect.value;
      if (!text) return;
      instructionInput.value = '';

      // Append Developer message
      appendDeveloperMessage(text, model);

      // Send to VS Code Extension Host
      vscode.postMessage({
        type: 'developerInstruction',
        model: model,
        instruction: text
      });
    }

    function appendDeveloperMessage(text, model) {
      const div = document.createElement('div');
      div.className = 'msg-card msg-developer';
      div.innerHTML = \`
        <div class="msg-developer-header">Developer → \${model.toUpperCase()} MODEL</div>
        <div>\${escapeHtml(text)}</div>
      \`;
      chatStream.appendChild(div);
      chatStream.scrollTop = chatStream.scrollHeight;
    }

    // Handle messages from Extension Host
    window.addEventListener('message', (event) => {
      const msg = event.data;
      switch (msg.type) {
        case 'status':
          updateStatus(msg.status, msg.message, msg.activeAgent);
          break;
        case 'result':
          appendSupervisorResult(msg.result);
          break;
        case 'history':
          break;
      }
    });

    function updateStatus(status, text, agent) {
      statusPulse.className = 'status-pulse ' + (status || 'idle');
      statusText.textContent = text || 'Ready';

      const debugNode = document.getElementById('node-debug');
      const testNode = document.getElementById('node-test');

      if (agent === 'debug') {
        debugNode.classList.add('active');
        testNode.classList.remove('active');
      } else if (agent === 'test') {
        testNode.classList.add('active');
        debugNode.classList.remove('active');
      } else {
        debugNode.classList.remove('active');
        testNode.classList.remove('active');
      }
    }

    function appendSupervisorResult(result) {
      const div = document.createElement('div');
      div.className = 'msg-card msg-supervisor';

      const isDebug = result.agent === 'debug';
      const badgeClass = isDebug ? 'badge-debug' : 'badge-test';
      const badgeText = isDebug ? 'DEBUGGING MODEL' : 'TESTING MODEL';

      let actionsHtml = '';
      let debugExtraHtml = '';

      if (isDebug && result.debugData) {
        actionsHtml = \`
          <button class="btn btn-green" onclick="requestFix('\${result.taskId}', '\${escapeQuotes(result.debugData.suggestedFix)}')">
            ✓ Apply Fix (Permission Required)
          </button>
        \`;

        const justificationText = result.debugData.justification ? \`
          <div class="justification-box">
            <strong>💡 Technical Justification:</strong><br>\${escapeHtml(result.debugData.justification)}
          </div>
        \` : '';

        const checksList = (result.debugData.maintenanceChecks || []).map(c => \`<li>\${escapeHtml(c)}</li>\`).join('');
        const scoreClass = 'health-' + (result.debugData.maintenanceScore || 'clean');
        const scoreLabel = (result.debugData.maintenanceScore || 'clean').replace('_', ' ').toUpperCase();

        const recsList = (result.debugData.maintenanceRecommendations || []).map(r => \`<li>\${escapeHtml(r)}</li>\`).join('');
        const recsSection = recsList ? \`
          <div style="margin-top:6px; font-size:10px; color:#94a3b8;">
            <strong>Maintenance Recommendations:</strong>
            <ul style="padding-left:14px; margin-top:2px;">\${recsList}</ul>
          </div>
        \` : '';

        debugExtraHtml = \`
          \${justificationText}
          <div class="maintenance-box">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
              <span style="font-weight:600; color:#34d399;">🛡️ Code Maintenance Checks</span>
              <span class="health-pill \${scoreClass}">\${scoreLabel}</span>
            </div>
            <ul class="maint-list">\${checksList}</ul>
            \${recsSection}
          </div>
        \`;
      } else if (!isDebug && result.testData) {
        actionsHtml = \`
          <button class="btn btn-primary" onclick="copySnippet('\${escapeQuotes(result.testData.generatedTestCode)}')">
            📋 Copy Test Suite
          </button>
        \`;
      }

      div.innerHTML = \`
        <div class="supervisor-card-header">
          <span style="font-weight: 600; color: #60a5fa;">🔵 Supervisor</span>
          <span class="model-badge \${badgeClass}">Response from \${badgeText}</span>
        </div>
        <div class="verdict-text">
          🗣 "\${escapeHtml(result.supervisorVerdict || 'Analysis concluded.')}"
        </div>
        \${debugExtraHtml}
        <div class="content-box">\${escapeHtml(result.details || result.summary || '')}</div>
        <div class="btn-group">\${actionsHtml}</div>
      \`;

      chatStream.appendChild(div);
      chatStream.scrollTop = chatStream.scrollHeight;
    }

    window.requestFix = function(taskId, suggestedFix) {
      vscode.postMessage({
        type: 'applyFix',
        taskId: taskId,
        suggestedFix: suggestedFix
      });
    };

    window.copySnippet = function(code) {
      navigator.clipboard.writeText(code);
      vscode.postMessage({ type: 'notify', message: '✓ Test suite copied to clipboard!' });
    };

    function escapeHtml(s) {
      if (!s) return '';
      return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function escapeQuotes(s) {
      if (!s) return '';
      return s.replace(/\\\\/g, '\\\\\\\\').replace(/'/g, "\\\\'").replace(/"/g, '&quot;').replace(/\\n/g, '\\\\n');
    }
  </script>
</body>
</html>`;
}

module.exports = {
  getSideBotContent
};
