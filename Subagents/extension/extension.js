const vscode = require('vscode');
const path = require('path');
const { extractCodeContext } = require('./utils/codeContext');
const { SupervisorClient } = require('./client/supervisorClient');
const { CodeMarkerProvider } = require('./decorations/codeMarkerProvider');
const { SideBotViewProvider } = require('./webview/sideBotView');

/**
 * Extension activation callback.
 * @param {vscode.ExtensionContext} context
 */
async function activate(context) {
  console.log('[Supervisor Agent Extension] Activating...');

  const config = vscode.workspace.getConfiguration('supervisor');
  const port = config.get('serverPort', 8765);
  const client = new SupervisorClient(port);

  // Central dispatch handler
  const executeSupervisorAction = async (agentType, editor, targetLine, instruction = '', source = 'supervisor') => {
    if (!editor) {
      editor = vscode.window.activeTextEditor;
    }
    if (!editor) {
      vscode.window.showErrorMessage('Please open a code file to run Supervisor Agent.');
      return;
    }

    try {
      const codeCtx = extractCodeContext(editor, targetLine);
      const shortFile = codeCtx.fileName;
      const lineNum = codeCtx.line;

      // Update Side Bot with running state
      const modelName = agentType === 'debug' ? 'Debugging Model' : (agentType === 'test' ? 'Testing Model' : `${agentType.charAt(0).toUpperCase() + agentType.slice(1)}Agent`);
      sideBotProvider.updateStatus(
        'running',
        `Analyzing ${shortFile}... ${modelName} is working on instruction...`,
        agentType,
        `${shortFile}:${lineNum}`
      );

      // Focus sidebar
      vscode.commands.executeCommand('supervisor.sideBotView.focus');

      // Ensure server
      const ready = await ensureBackend();
      if (!ready) {
        sideBotProvider.updateStatus('error', 'Supervisor backend not reachable.');
        return;
      }

      // Dispatch request to Supervisor (which delegates to subagent and receives response)
      const result = await client.dispatchTask(agentType, codeCtx, instruction, source);

      // Update Side Bot with completed result
      sideBotProvider.displayResult(result);
      sideBotProvider.updateStatus('completed', `✓ ${modelName} delivered response to Supervisor`);

      // Refresh event timeline
      const eventsRes = await client.getEvents();
      if (eventsRes && eventsRes.events) {
        sideBotProvider.syncHistory(eventsRes.events);
      }
    } catch (err) {
      sideBotProvider.updateStatus('error', `⚠ ${agentType.toUpperCase()} analysis failed: ${err.message}`);
      vscode.window.showErrorMessage(`Supervisor Agent error: ${err.message}`);
    }
  };

  // Initialize Side Bot Webview Provider with developer instruction handler
  const sideBotProvider = new SideBotViewProvider(
    context.extensionUri,
    client,
    (model, instruction) => {
      executeSupervisorAction(model, null, null, instruction, 'developer');
    },
    () => {
      vscode.commands.executeCommand('supervisor.markLine');
    }
  );
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(SideBotViewProvider.viewType, sideBotProvider)
  );

  // Initialize Code Marker Provider
  const markerProvider = new CodeMarkerProvider(context, client, (action, editor, line) => {
    executeSupervisorAction(action, editor, line, '', 'supervisor');
  });

  // Register CodeLens & Hover providers
  context.subscriptions.push(
    vscode.languages.registerCodeLensProvider({ scheme: 'file' }, markerProvider),
    vscode.languages.registerHoverProvider({ scheme: 'file' }, markerProvider)
  );

  // Command: Mark Line 🔵
  context.subscriptions.push(
    vscode.commands.registerCommand('supervisor.markLine', async (lineArg) => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showWarningMessage('No active editor found.');
        return;
      }
      const targetLine = typeof lineArg === 'number' ? lineArg : (editor.selection.active.line + 1);
      await markerProvider.toggleMarker(editor, targetLine);
    })
  );

  // Command: Explain Line
  context.subscriptions.push(
    vscode.commands.registerCommand('supervisor.explainLine', async (args) => {
      const editor = vscode.window.activeTextEditor;
      const line = args?.line;
      await executeSupervisorAction('explain', editor, line);
    })
  );

  // Command: Debug Line
  context.subscriptions.push(
    vscode.commands.registerCommand('supervisor.debugLine', async (args) => {
      const editor = vscode.window.activeTextEditor;
      const line = args?.line;
      await executeSupervisorAction('debug', editor, line);
    })
  );

  // Command: Test Line
  context.subscriptions.push(
    vscode.commands.registerCommand('supervisor.testLine', async (args) => {
      const editor = vscode.window.activeTextEditor;
      const line = args?.line;
      await executeSupervisorAction('test', editor, line);
    })
  );

  // Command: Clear Markers
  context.subscriptions.push(
    vscode.commands.registerCommand('supervisor.clearMarkers', () => {
      markerProvider.clearAllMarkers();
      vscode.window.showInformationMessage('All 🔵 markers cleared.');
    })
  );

  // Command: Clear History
  context.subscriptions.push(
    vscode.commands.registerCommand('supervisor.clearHistory', async () => {
      await client.clearHistory();
      sideBotProvider.syncHistory([]);
      sideBotProvider.updateStatus('idle', 'History cleared.');
      vscode.window.showInformationMessage('Supervisor history cleared.');
    })
  );

  // Command: Start Python Agent Server
  context.subscriptions.push(
    vscode.commands.registerCommand('supervisor.startServer', async () => {
      const wsFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || path.resolve(__dirname, '..');
      const started = await client.ensureServerRunning(wsFolder);
      if (started) {
        vscode.window.showInformationMessage('Supervisor Agent Server is running on port ' + port);
      } else {
        vscode.window.showErrorMessage('Failed to start Supervisor Agent Server.');
      }
    })
  );

  // Auto-start backend if configured
  if (config.get('autoStartServer', true)) {
    const wsFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || path.resolve(__dirname, '..');
    client.ensureServerRunning(wsFolder).catch((e) => console.log('Auto-start check:', e.message));
  }

  console.log('[Supervisor Agent Extension] Activated successfully.');
}

function deactivate() {
  console.log('[Supervisor Agent Extension] Deactivated.');
}

module.exports = {
  activate,
  deactivate
};
