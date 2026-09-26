const vscode = require('vscode');

class CodeMarkerProvider {
  constructor(context, supervisorClient, onActionRequested) {
    this.context = context;
    this.client = supervisorClient;
    this.onActionRequested = onActionRequested;

    // Map: fileUri -> Set of 1-based line numbers
    this.markedLines = new Map();

    // Create subtle 🔵 marker decoration type (shows in gutter and after line)
    this.markerDecorationType = vscode.window.createTextEditorDecorationType({
      gutterIconPath: this._createCircleIconUri(),
      gutterIconSize: 'contain',
      overviewRulerColor: '#3b82f6',
      overviewRulerLane: vscode.OverviewRulerLane.Right,
      after: {
        contentText: ' 🔵',
        color: '#3b82f6',
        margin: '0 0 0 10px'
      }
    });

    this._codeLensChangeEmitter = new vscode.EventEmitter();
    this.onDidChangeCodeLenses = this._codeLensChangeEmitter.event;

    this._registerListeners();
  }

  _registerListeners() {
    // Re-apply decorations whenever active editor changes or document updates
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      if (editor) {
        this.updateDecorations(editor);
      }
    }, null, this.context.subscriptions);

    vscode.workspace.onDidChangeTextDocument((event) => {
      const activeEditor = vscode.window.activeTextEditor;
      if (activeEditor && activeEditor.document.uri.toString() === event.document.uri.toString()) {
        this.updateDecorations(activeEditor);
      }
    }, null, this.context.subscriptions);
  }

  /**
   * Generates a small SVG circle URI for the gutter icon.
   */
  _createCircleIconUri() {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">
      <circle cx="8" cy="8" r="5" fill="#3b82f6" />
    </svg>`;
    return vscode.Uri.parse(`data:image/svg+xml;utf8,${encodeURIComponent(svg)}`);
  }

  /**
   * Toggle 🔵 marker on the current line or specified line.
   */
  async toggleMarker(editor, lineNum) {
    if (!editor) return;
    const uri = editor.document.uri.toString();
    const line = lineNum || editor.selection.active.line + 1;

    if (!this.markedLines.has(uri)) {
      this.markedLines.set(uri, new Set());
    }

    const set = this.markedLines.get(uri);
    if (set.has(line)) {
      // If already marked, prompt for action or removal
      await this.showMarkerMenu(editor, line);
      return;
    } else {
      set.add(line);
      // Log to Supervisor
      if (this.client) {
        this.client.recordMarker(editor.document.uri.fsPath, line).catch(() => {});
      }
      vscode.window.showInformationMessage(`🔵 Marker placed on line ${line}`);
    }

    this.updateDecorations(editor);
    this._codeLensChangeEmitter.fire();

    // Automatically prompt with Explain / Debug / Test actions
    await this.showMarkerMenu(editor, line);
  }

  /**
   * Display interactive action menu when user interacts with 🔵 marker.
   */
  async showMarkerMenu(editor, line) {
    const items = [
      {
        label: '$(bug) Debugging Model',
        description: `Inspect bugs, boundary errors & suggest fix for line ${line}`,
        action: 'debug'
      },
      {
        label: '$(beaker) Testing Model',
        description: `Formulate unit tests & edge cases for line ${line}`,
        action: 'test'
      },
      {
        label: '$(comment) Custom Instruction for Model...',
        description: `Type specific instruction for line ${line}`,
        action: 'custom'
      },
      {
        label: '$(trash) Remove Marker',
        description: `Clear 🔵 marker from line ${line}`,
        action: 'remove'
      }
    ];

    const selected = await vscode.window.showQuickPick(items, {
      placeHolder: `🔵 Line ${line} marked — Choose Model Action:`
    });

    if (!selected) return;

    if (selected.action === 'remove') {
      const uri = editor.document.uri.toString();
      if (this.markedLines.has(uri)) {
        this.markedLines.get(uri).delete(line);
      }
      this.updateDecorations(editor);
      this._codeLensChangeEmitter.fire();
    } else if (selected.action === 'custom') {
      const instruction = await vscode.window.showInputBox({
        prompt: `Enter instruction for Supervisor and Worker Model on line ${line}:`,
        placeHolder: `e.g. Check if this code handles empty list inputs`
      });
      if (!instruction) return;

      const modelPick = await vscode.window.showQuickPick([
        { label: '$(bug) Debugging Model', model: 'debug' },
        { label: '$(beaker) Testing Model', model: 'test' }
      ], { placeHolder: 'Select target worker model:' });

      if (!modelPick) return;

      if (this.onActionRequested) {
        this.onActionRequested(modelPick.model, editor, line, instruction, 'developer');
      }
    } else {
      // Dispatch action to Supervisor
      if (this.onActionRequested) {
        this.onActionRequested(selected.action, editor, line, '', 'supervisor');
      }
    }
  }

  /**
   * Render 🔵 decorations on all marked lines for the editor's document.
   */
  updateDecorations(editor) {
    if (!editor || !editor.document) return;
    const uri = editor.document.uri.toString();
    const lines = this.markedLines.get(uri);

    if (!lines || lines.size === 0) {
      editor.setDecorations(this.markerDecorationType, []);
      return;
    }

    const ranges = [];
    for (const line of lines) {
      const zeroLine = line - 1;
      if (zeroLine >= 0 && zeroLine < editor.document.lineCount) {
        const lineObj = editor.document.lineAt(zeroLine);
        ranges.push({
          range: new vscode.Range(zeroLine, lineObj.text.length, zeroLine, lineObj.text.length)
        });
      }
    }
    editor.setDecorations(this.markerDecorationType, ranges);
  }

  clearAllMarkers() {
    this.markedLines.clear();
    const activeEditor = vscode.window.activeTextEditor;
    if (activeEditor) {
      this.updateDecorations(activeEditor);
    }
    this._codeLensChangeEmitter.fire();
  }

  // --- CodeLens Provider Implementation ---
  provideCodeLenses(document) {
    const uri = document.uri.toString();
    const lines = this.markedLines.get(uri);
    if (!lines || lines.size === 0) return [];

    const lenses = [];
    for (const line of lines) {
      const zeroLine = line - 1;
      if (zeroLine >= 0 && zeroLine < document.lineCount) {
        const range = new vscode.Range(zeroLine, 0, zeroLine, 0);
        lenses.push(
          new vscode.CodeLens(range, {
            title: `🔵 Supervisor: Debug | Test`,
            tooltip: `Click to choose Debugging or Testing model for line ${line}`,
            command: 'supervisor.markLine',
            arguments: [line]
          })
        );
      }
    }
    return lenses;
  }

  // --- Hover Provider Implementation ---
  provideHover(document, position) {
    const uri = document.uri.toString();
    const lines = this.markedLines.get(uri);
    const line = position.line + 1;

    if (lines && lines.has(line)) {
      const md = new vscode.MarkdownString();
      md.isTrusted = true;
      md.supportHtml = true;
      md.appendMarkdown(`### 🔵 Supervisor Marked Line (${line})\n\n`);
      md.appendMarkdown(`Coordinate specialized worker models:\n\n`);
      md.appendMarkdown(`[🐞 Debugging Model](command:supervisor.debugLine?${encodeURIComponent(JSON.stringify({ line }))}) | `);
      md.appendMarkdown(`[🧪 Testing Model](command:supervisor.testLine?${encodeURIComponent(JSON.stringify({ line }))})\n\n`);
      return new vscode.Hover(md);
    }
    return null;
  }
}

module.exports = {
  CodeMarkerProvider
};
