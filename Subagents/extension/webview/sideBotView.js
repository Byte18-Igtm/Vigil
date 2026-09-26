const vscode = require('vscode');
const { getSideBotContent } = require('./sideBotHtml');

class SideBotViewProvider {
  static viewType = 'supervisor.sideBotView';

  constructor(extensionUri, supervisorClient, onDeveloperInstruction, onMarkLineRequested) {
    this._extensionUri = extensionUri;
    this.client = supervisorClient;
    this.onDeveloperInstruction = onDeveloperInstruction;
    this.onMarkLineRequested = onMarkLineRequested;
    this._view = null;
    this._pendingMessages = [];
  }

  resolveWebviewView(webviewView, context, token) {
    this._view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri]
    };

    webviewView.webview.html = getSideBotContent(webviewView.webview, this._extensionUri);

    // Handle messages coming from Webview Bot UI
    webviewView.webview.onDidReceiveMessage(async (message) => {
      switch (message.type) {
        case 'clearHistory':
          await this.client.clearHistory();
          this.postMessage({ type: 'history', events: [] });
          this.postMessage({ type: 'status', status: 'idle', message: 'History cleared' });
          break;

        case 'developerInstruction':
          if (this.onDeveloperInstruction) {
            this.onDeveloperInstruction(message.model, message.instruction);
          }
          break;

        case 'markLine':
          if (this.onMarkLineRequested) {
            this.onMarkLineRequested();
          }
          break;

        case 'notify':
          vscode.window.showInformationMessage(message.message);
          break;

        case 'applyFix':
          await this._handleApplyFix(message);
          break;
      }
    });

    // Send any queued messages
    while (this._pendingMessages.length > 0) {
      const msg = this._pendingMessages.shift();
      this.postMessage(msg);
    }
  }

  async _handleApplyFix(message) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showErrorMessage('No active editor to apply fix.');
      return;
    }

    const confirm = await vscode.window.showWarningMessage(
      'DebugAgent proposes applying a fix to this code. Do you grant permission to modify the file?',
      { modal: true },
      'Grant Permission & Apply Fix'
    );

    if (confirm === 'Grant Permission & Apply Fix') {
      try {
        const filePath = editor.document.uri.fsPath;
        const line = editor.selection.active.line + 1;
        const res = await this.client.applyFix(
          filePath,
          line,
          message.originalCode || '',
          message.suggestedFix,
          true
        );

        vscode.window.showInformationMessage(`✓ Fix applied successfully: ${res.message}`);
        this.postMessage({
          type: 'event',
          event: {
            id: 'fix_' + Date.now(),
            type: 'fix_applied',
            message: `✓ Fix applied to line ${line} (user approved)`,
            status: 'success'
          }
        });
      } catch (err) {
        vscode.window.showErrorMessage(`Failed to apply fix: ${err.message}`);
      }
    }
  }

  postMessage(message) {
    if (this._view && this._view.webview) {
      this._view.webview.postMessage(message);
    } else {
      this._pendingMessages.push(message);
    }
  }

  updateStatus(status, message, activeAgent, activeFile) {
    this.postMessage({
      type: 'status',
      status: status,
      message: message,
      activeAgent: activeAgent,
      activeFile: activeFile
    });
  }

  displayResult(result) {
    this.postMessage({
      type: 'result',
      result: result
    });
  }

  appendEvent(event) {
    this.postMessage({
      type: 'event',
      event: event
    });
  }

  syncHistory(events) {
    this.postMessage({
      type: 'history',
      events: events
    });
  }
}

module.exports = {
  SideBotViewProvider
};
