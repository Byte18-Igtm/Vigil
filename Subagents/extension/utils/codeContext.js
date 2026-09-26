const vscode = require('vscode');

/**
 * Extracts rich context around the user's cursor or marked line.
 * Collects file path, language, selected line, selected code, nearby lines, and range.
 *
 * @param {vscode.TextEditor} editor
 * @param {number} [targetLine] 1-based line number (optional, defaults to active selection)
 * @returns {object} Extracted context
 */
function extractCodeContext(editor, targetLine) {
  if (!editor || !editor.document) {
    throw new Error('No active editor or document available.');
  }

  const document = editor.document;
  const totalLines = document.lineCount;

  // Determine target line (1-indexed)
  let line = targetLine;
  if (!line) {
    line = editor.selection.active.line + 1;
  }
  line = Math.max(1, Math.min(line, totalLines));

  const zeroBasedLine = line - 1;
  const lineText = document.lineAt(zeroBasedLine).text;

  // If there's an active non-empty selection on this line, use it
  let selectedCode = '';
  if (!editor.selection.isEmpty && editor.selection.contains(new vscode.Position(zeroBasedLine, 0))) {
    selectedCode = document.getText(editor.selection).trim();
  }
  if (!selectedCode) {
    selectedCode = lineText.trim();
  }

  // Extract surrounding context (15 lines before and after)
  const startLine = Math.max(0, zeroBasedLine - 15);
  const endLine = Math.min(totalLines - 1, zeroBasedLine + 15);
  const startPos = new vscode.Position(startLine, 0);
  const endPos = new vscode.Position(endLine, document.lineAt(endLine).text.length);
  const surroundingCode = document.getText(new vscode.Range(startPos, endPos));

  return {
    filePath: document.uri.fsPath,
    fileName: document.fileName.split(/[\\/]/).pop(),
    language: document.languageId || 'plaintext',
    line: line,
    column: editor.selection.active.character + 1,
    selectedCode: selectedCode,
    surroundingCode: surroundingCode,
    range: {
      startLine: startLine + 1,
      endLine: endLine + 1
    }
  };
}

module.exports = {
  extractCodeContext
};
