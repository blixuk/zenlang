const vscode = require('vscode');
const cp = require('child_process');
const path = require('path');
const fs = require('fs');

/** @type {vscode.DiagnosticCollection} */
let diagnostics;
/** @type {vscode.OutputChannel} */
let output;
/** @type {NodeJS.Timeout | undefined} */
let debounceTimer;

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  output = vscode.window.createOutputChannel('Zenlang');
  diagnostics = vscode.languages.createDiagnosticCollection('zenlang');
  context.subscriptions.push(diagnostics, output);

  context.subscriptions.push(
    vscode.commands.registerCommand('zenlang.checkFile', () => {
      const doc = vscode.window.activeTextEditor?.document;
      if (doc && doc.languageId === 'zenlang') {
        updateDiagnostics(doc, true);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('zenlang.runFile', () => runCurrentFile(false))
  );
  context.subscriptions.push(
    vscode.commands.registerCommand('zenlang.runFileNative', () => runCurrentFile(true))
  );

  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((document) => {
      if (document.languageId !== 'zenlang') return;
      const cfg = vscode.workspace.getConfiguration('zenlang');
      if (cfg.get('diagnostics.enabled') && cfg.get('diagnostics.onSave')) {
        scheduleDiagnostics(document);
      }
    })
  );

  context.subscriptions.push(
    vscode.workspace.onDidOpenTextDocument((document) => {
      if (document.languageId !== 'zenlang') return;
      const cfg = vscode.workspace.getConfiguration('zenlang');
      if (cfg.get('diagnostics.enabled') && cfg.get('diagnostics.onOpen')) {
        scheduleDiagnostics(document);
      }
    })
  );

  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration('zenlang')) {
        // no-op; next save/open picks up settings
      }
    })
  );

  // Completions
  context.subscriptions.push(
    vscode.languages.registerCompletionItemProvider('zenlang', {
      provideCompletionItems(document) {
        return buildCompletions(document);
      },
    })
  );

  // Hover for common operators / keywords
  context.subscriptions.push(
    vscode.languages.registerHoverProvider('zenlang', {
      provideHover(document, position) {
        const range = document.getWordRangeAtPosition(position, /->|<-|:>|\.\.=|\.\.|[A-Za-z_][A-Za-z0-9_]*/);
        if (!range) return;
        const word = document.getText(range);
        const tip = HOVERS[word];
        if (!tip) return;
        return new vscode.Hover(new vscode.MarkdownString(tip));
      },
    })
  );

  // Initial pass
  for (const doc of vscode.workspace.textDocuments) {
    if (doc.languageId === 'zenlang') {
      const cfg = vscode.workspace.getConfiguration('zenlang');
      if (cfg.get('diagnostics.enabled') && cfg.get('diagnostics.onOpen')) {
        scheduleDiagnostics(doc);
      }
    }
  }
}

/**
 * @param {vscode.TextDocument} document
 */
function scheduleDiagnostics(document) {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => updateDiagnostics(document, false), 300);
}

/**
 * @param {vscode.TextDocument} document
 */
function buildCompletions(document) {
  const keywords = [
    'let', 'set', 'function', 'class', 'structure', 'enumerator',
    'import', 'use', 'from', 'as', 'export', 'when', 'or', 'and', 'not',
    'do', 'while', 'until', 'for', 'in', 'return', 'break', 'continue',
    'check', 'raise', 'assert', 'defer', 'task', 'is', 'type', 'object',
    'scope', 'extends', 'extend', 'True', 'False', 'Nothing', 'nothing',
    'self', 'parent', 'auto',
  ];
  const types = [
    'Integer', 'Decimal', 'String', 'Boolean', 'List', 'Map', 'Dictionary',
    'Tuple', 'Vector', 'Set', 'Void', 'Variant', 'Error', 'Task', 'Function',
    'Structure', 'Class', 'Enumerator', 'Auto', 'Rune',
  ];
  const modules = [
    'zen.io.io', 'zen.io.file', 'zen.io.path',
    'zen.text.string', 'zen.sys.sys', 'zen.sys.process', 'zen.sys.term',
    'zen.test', 'zen.collections.list', 'zen.data.json', 'zen.math.math',
  ];

  /** @type {vscode.CompletionItem[]} */
  const items = [];
  for (const kw of keywords) {
    items.push(new vscode.CompletionItem(kw, vscode.CompletionItemKind.Keyword));
  }
  for (const t of types) {
    items.push(new vscode.CompletionItem(t, vscode.CompletionItemKind.Class));
  }
  for (const m of modules) {
    const item = new vscode.CompletionItem(m, vscode.CompletionItemKind.Module);
    item.insertText = m;
    item.detail = 'stdlib module path';
    items.push(item);
  }

  // Snippet-like operators
  const arrow = new vscode.CompletionItem('->', vscode.CompletionItemKind.Operator);
  arrow.detail = 'bind / assign';
  items.push(arrow);
  const ret = new vscode.CompletionItem('<-', vscode.CompletionItemKind.Operator);
  ret.detail = 'return';
  items.push(ret);

  const text = document.getText();
  const words = new Set(text.match(/[A-Za-z_][A-Za-z0-9_]*/g) || []);
  for (const word of words) {
    if (!keywords.includes(word) && !types.includes(word)) {
      items.push(new vscode.CompletionItem(word, vscode.CompletionItemKind.Text));
    }
  }
  return items;
}

const HOVERS = {
  '->': '**Bind / assign** — data flows into a name or field.\n\n`let x -> 1`',
  '<-': '**Return** — data flows out of a function.\n\n`<- value`',
  ':>': '**Infer-and-lock** type on binding.',
  '..': '**Half-open range** `a..b` → list from a inclusive to b exclusive.',
  '..=': '**Closed range** `a..=b` → list including both ends.',
  when: 'Branching: `when cond { } or when other { } or { }` (no `if`).',
  and: 'Logical and (prefer over `&&`).',
  or: 'Logical or, or the else-branch keyword after `when`.',
  not: 'Logical not.',
  let: 'Mutable binding.',
  set: 'Immutable constant binding.',
  function: 'Function or anonymous lambda: `function(x) { <- x }`',
  do: 'Loop introducer: `do while`, `do for`, `do { } while`.',
  nothing: 'Explicit empty value.',
  True: 'Boolean true.',
  False: 'Boolean false.',
};

/**
 * Resolve bootstrap/Zen.py path.
 * @param {vscode.TextDocument} document
 * @returns {{ zenPy: string, cwd: string } | null}
 */
function resolveBootstrap(document) {
  const cfg = vscode.workspace.getConfiguration('zenlang');
  const custom = (cfg.get('bootstrapPath') || '').trim();
  const folder = vscode.workspace.getWorkspaceFolder(document.uri);

  const candidates = [];
  if (custom) {
    if (path.isAbsolute(custom)) {
      candidates.push({ zenPy: custom, cwd: path.dirname(path.dirname(custom)) });
    } else if (folder) {
      candidates.push({
        zenPy: path.join(folder.uri.fsPath, custom),
        cwd: folder.uri.fsPath,
      });
    }
  }
  if (folder) {
    candidates.push({
      zenPy: path.join(folder.uri.fsPath, 'bootstrap', 'Zen.py'),
      cwd: folder.uri.fsPath,
    });
  }
  // Walk up from file for monorepo / nested opens
  let dir = path.dirname(document.uri.fsPath);
  for (let i = 0; i < 8; i++) {
    candidates.push({
      zenPy: path.join(dir, 'bootstrap', 'Zen.py'),
      cwd: dir,
    });
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }

  for (const c of candidates) {
    if (fs.existsSync(c.zenPy)) return c;
  }
  return null;
}

/**
 * @param {vscode.TextDocument} document
 * @param {boolean} showMessage
 */
function updateDiagnostics(document, showMessage) {
  if (document.languageId !== 'zenlang') return;

  const cfg = vscode.workspace.getConfiguration('zenlang');
  if (!cfg.get('diagnostics.enabled') && !showMessage) {
    diagnostics.delete(document.uri);
    return;
  }

  const resolved = resolveBootstrap(document);
  if (!resolved) {
    if (showMessage) {
      vscode.window.showWarningMessage(
        'Zenlang: could not find bootstrap/Zen.py. Set zenlang.bootstrapPath or open the repo root.'
      );
    }
    return;
  }

  const python = cfg.get('pythonPath') || 'python3';
  const filePath = document.uri.fsPath;
  const env = {
    ...process.env,
    ZEN_PATH:
      process.env.ZEN_PATH ||
      `${resolved.cwd}${path.delimiter}${path.join(resolved.cwd, 'selfhost')}${path.delimiter}${path.join(resolved.cwd, 'lib')}`,
  };

  // --check: typecheck without executing main
  const args = [resolved.zenPy, '--check', filePath];
  cp.execFile(python, args, { cwd: resolved.cwd, env, maxBuffer: 4 * 1024 * 1024 }, (err, stdout, stderr) => {
    const combined = `${stdout || ''}\n${stderr || ''}`;
    const diags = parseDiagnostics(combined, filePath, resolved.cwd);
    diagnostics.set(document.uri, diags);

    if (showMessage) {
      if (diags.length === 0 && !err) {
        vscode.window.showInformationMessage('Zenlang: check ok');
      } else if (diags.length > 0) {
        vscode.window.showWarningMessage(`Zenlang: ${diags.length} diagnostic(s)`);
      } else if (err) {
        // Compiler may exit non-zero without parseable locations
        output.appendLine(combined);
        vscode.window.showErrorMessage('Zenlang: check failed (see Zenlang output)');
      }
    }
  });
}

/**
 * @param {string} outputText
 * @param {string} filePath
 * @param {string} cwd
 * @returns {vscode.Diagnostic[]}
 */
function parseDiagnostics(outputText, filePath, cwd) {
  const lines = outputText.split(/\r?\n/);
  /** @type {vscode.Diagnostic[]} */
  const diags = [];
  const base = path.resolve(filePath);

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    // path:line:col  or  path:line:col: message
    const match = line.match(/^(.+?):(\d+):(\d+)(?::\s*(.*))?$/);
    if (!match) continue;

    const locFile = match[1];
    const resolvedLoc = path.isAbsolute(locFile)
      ? path.resolve(locFile)
      : path.resolve(cwd, locFile);
    if (resolvedLoc !== base && path.basename(resolvedLoc) !== path.basename(base)) {
      continue;
    }

    const lineNum = Math.max(0, parseInt(match[2], 10) - 1);
    const colNum = Math.max(0, parseInt(match[3], 10) - 1);
    let message = (match[4] || '').trim();
    if (!message) {
      for (let j = i - 1; j >= Math.max(0, i - 6); j--) {
        const prev = lines[j].trim();
        if (!prev || prev.startsWith('Token:')) continue;
        message = prev;
        break;
      }
    }
    if (!message) message = 'Error';

    const range = new vscode.Range(lineNum, colNum, lineNum, colNum + 80);
    const severity = /warning/i.test(message)
      ? vscode.DiagnosticSeverity.Warning
      : vscode.DiagnosticSeverity.Error;
    diags.push(new vscode.Diagnostic(range, message, severity));
  }

  // Fallback: Type check failed / Parser without location
  if (diags.length === 0) {
    for (const line of lines) {
      if (/Type check failed|Parse error|\[Parser\]|\[Checker\]/i.test(line)) {
        diags.push(
          new vscode.Diagnostic(
            new vscode.Range(0, 0, 0, 1),
            line.trim(),
            vscode.DiagnosticSeverity.Error
          )
        );
        break;
      }
    }
  }
  return diags;
}

/**
 * @param {boolean} native
 */
function runCurrentFile(native) {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.languageId !== 'zenlang') {
    vscode.window.showWarningMessage('Zenlang: open a .zl / .zs file first');
    return;
  }
  const document = editor.document;
  const resolved = resolveBootstrap(document);
  if (!resolved) {
    vscode.window.showWarningMessage('Zenlang: bootstrap/Zen.py not found');
    return;
  }
  const cfg = vscode.workspace.getConfiguration('zenlang');
  const python = cfg.get('pythonPath') || 'python3';
  const filePath = document.uri.fsPath;
  const args = native
    ? [resolved.zenPy, '-g', filePath]
    : [resolved.zenPy, filePath];

  const term = vscode.window.createTerminal({
    name: native ? 'Zenlang -g' : 'Zenlang',
    cwd: resolved.cwd,
    env: {
      ZEN_PATH:
        process.env.ZEN_PATH ||
        `${resolved.cwd}${path.delimiter}${path.join(resolved.cwd, 'selfhost')}${path.delimiter}${path.join(resolved.cwd, 'lib')}`,
    },
  });
  term.show();
  // Quote paths for the shell
  const q = (s) => `"${s.replace(/"/g, '\\"')}"`;
  term.sendText(`${q(python)} ${args.map(q).join(' ')}`);
}

function deactivate() {
  if (debounceTimer) clearTimeout(debounceTimer);
}

module.exports = {
  activate,
  deactivate,
};
