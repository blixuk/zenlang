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
/** @type {ZenLspClient | null} */
let lspClient = null;

class ZenLspClient {
  constructor(serverPath, cwd, output) {
    this.serverPath = serverPath;
    this.cwd = cwd;
    this.output = output;
    this.proc = null;
    this.buffer = Buffer.alloc(0);
    this.nextId = 1;
    this.pending = new Map();
    this.isReady = false;
    this.changeTimers = new Map();
  }

  start() {
    try {
      this.output.appendLine(`[LSP] Spawning: ${this.serverPath} lsp in ${this.cwd}`);
      const env = {
        ...process.env,
        ZEN_PATH:
          process.env.ZEN_PATH ||
          `${this.cwd}${path.delimiter}${path.join(this.cwd, 'selfhost')}${path.delimiter}${path.join(this.cwd, 'lib')}`,
      };
      this.proc = cp.spawn(this.serverPath, ['lsp'], {
        cwd: this.cwd,
        env,
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      this.proc.stdout.on('data', (chunk) => this.handleData(chunk));
      this.proc.stderr.on('data', (chunk) => {
        this.output.appendLine(`[LSP stderr] ${chunk.toString()}`);
      });
      this.proc.on('error', (err) => {
        this.output.appendLine(`[LSP error] ${err.message}`);
        this.proc = null;
        this.isReady = false;
      });
      this.proc.on('exit', (code, sig) => {
        this.output.appendLine(`[LSP exit] code: ${code}, signal: ${sig}`);
        this.proc = null;
        this.isReady = false;
      });

      // Send initialize request with timeout
      this.sendRequest('initialize', {
        processId: process.pid,
        rootUri: this.cwd ? vscode.Uri.file(this.cwd).toString() : null,
        capabilities: {
          textDocument: {
            completion: { dynamicRegistration: false },
            hover: { dynamicRegistration: false },
            definition: { dynamicRegistration: false },
            documentSymbol: { dynamicRegistration: false },
          },
        },
      }, 3000).then(() => {
        this.isReady = true;
        this.output.appendLine('[LSP] Initialized and ready.');
        this.sendNotification('initialized', {});
        // Sync open documents
        for (const doc of vscode.workspace.textDocuments) {
          if (doc.languageId === 'zenlang') {
            this.notifyOpen(doc);
          }
        }
      }).catch((e) => {
        this.output.appendLine(`[LSP] Initialize failed: ${e.message}`);
      });
    } catch (e) {
      this.output.appendLine(`[LSP] Start failed: ${e.message}`);
    }
  }

  stop() {
    if (this.proc) {
      try {
        this.sendNotification('exit', {});
        this.proc.kill();
      } catch (e) {
        // ignore
      }
      this.proc = null;
      this.isReady = false;
    }
  }

  handleData(chunk) {
    this.buffer = Buffer.concat([this.buffer, chunk]);
    while (true) {
      const headerEnd = this.buffer.indexOf('\r\n\r\n');
      if (headerEnd === -1) break;
      const headerText = this.buffer.slice(0, headerEnd).toString('utf8');
      const match = headerText.match(/Content-Length:\s*(\d+)/i);
      if (!match) {
        // malformed header, discard
        this.buffer = this.buffer.slice(headerEnd + 4);
        continue;
      }
      const contentLength = parseInt(match[1], 10);
      const totalMsgLength = headerEnd + 4 + contentLength;
      if (this.buffer.length < totalMsgLength) {
        // wait for rest of message body
        break;
      }
      const bodyBytes = this.buffer.slice(headerEnd + 4, totalMsgLength);
      this.buffer = this.buffer.slice(totalMsgLength);
      try {
        const msg = JSON.parse(bodyBytes.toString('utf8'));
        this.handleMessage(msg);
      } catch (e) {
        this.output.appendLine(`[LSP] JSON parse error: ${e.message}`);
      }
    }
  }

  handleMessage(msg) {
    if (msg.id !== undefined && this.pending.has(msg.id)) {
      const { resolve, reject, timer } = this.pending.get(msg.id);
      if (timer) clearTimeout(timer);
      this.pending.delete(msg.id);
      if (msg.error) {
        reject(new Error(msg.error.message || 'LSP RPC error'));
      } else {
        resolve(msg.result);
      }
      return;
    }

    if (msg.method === 'textDocument/publishDiagnostics') {
      const params = msg.params || {};
      const uri = vscode.Uri.parse(params.uri);
      const items = (params.diagnostics || []).map((d) => {
        const r = d.range || {};
        const start = r.start || { line: 0, character: 0 };
        const end = r.end || { line: 0, character: 10 };
        const range = new vscode.Range(start.line, start.character, end.line, end.character);
        const sev = d.severity === 1 ? vscode.DiagnosticSeverity.Error
                  : d.severity === 2 ? vscode.DiagnosticSeverity.Warning
                  : vscode.DiagnosticSeverity.Information;
        return new vscode.Diagnostic(range, d.message || '', sev);
      });
      diagnostics.set(uri, items);
    }
  }

  sendRequest(method, params, timeoutMs = 800) {
    if (!this.proc) return Promise.reject(new Error('LSP server not running'));
    const id = this.nextId++;
    const payload = JSON.stringify({ jsonrpc: '2.0', id, method, params });
    const header = `Content-Length: ${Buffer.byteLength(payload, 'utf8')}\r\n\r\n`;
    return new Promise((resolve, reject) => {
      let timer = null;
      if (timeoutMs > 0) {
        timer = setTimeout(() => {
          if (this.pending.has(id)) {
            this.pending.delete(id);
            reject(new Error(`LSP request ${method} timed out after ${timeoutMs}ms`));
          }
        }, timeoutMs);
      }
      this.pending.set(id, { resolve, reject, timer });
      this.proc.stdin.write(header + payload);
    });
  }

  sendNotification(method, params) {
    if (!this.proc) return;
    const payload = JSON.stringify({ jsonrpc: '2.0', method, params });
    const header = `Content-Length: ${Buffer.byteLength(payload, 'utf8')}\r\n\r\n`;
    this.proc.stdin.write(header + payload);
  }

  notifyOpen(doc) {
    this.sendNotification('textDocument/didOpen', {
      textDocument: {
        uri: doc.uri.toString(),
        languageId: doc.languageId,
        version: doc.version,
        text: doc.getText(),
      },
    });
  }

  notifyChange(doc) {
    const uriStr = doc.uri.toString();
    if (this.changeTimers.has(uriStr)) {
      clearTimeout(this.changeTimers.get(uriStr));
    }
    const timer = setTimeout(() => {
      this.changeTimers.delete(uriStr);
      this.sendNotification('textDocument/didChange', {
        textDocument: {
          uri: uriStr,
          version: doc.version,
        },
        contentChanges: [
          { text: doc.getText() },
        ],
      });
    }, 200);
    this.changeTimers.set(uriStr, timer);
  }

  notifySave(doc) {
    this.sendNotification('textDocument/didSave', {
      textDocument: {
        uri: doc.uri.toString(),
      },
    });
  }

  notifyClose(doc) {
    const uriStr = doc.uri.toString();
    if (this.changeTimers.has(uriStr)) {
      clearTimeout(this.changeTimers.get(uriStr));
      this.changeTimers.delete(uriStr);
    }
    this.sendNotification('textDocument/didClose', {
      textDocument: {
        uri: uriStr,
      },
    });
  }
}

/**
 * Resolve LSP executable path (bin/zen or bin/zen-selfhost).
 * @param {vscode.TextDocument} [document]
 * @returns {{ binPath: string, cwd: string } | null}
 */
function resolveLspBin(document) {
  const cfg = vscode.workspace.getConfiguration('zenlang');
  const custom = (cfg.get('lsp.path') || '').trim();
  const folder = document ? vscode.workspace.getWorkspaceFolder(document.uri) : (vscode.workspace.workspaceFolders?.[0]);

  const candidates = [];
  if (custom) {
    if (path.isAbsolute(custom)) {
      candidates.push({ binPath: custom, cwd: path.dirname(path.dirname(custom)) });
    } else if (folder) {
      candidates.push({
        binPath: path.join(folder.uri.fsPath, custom),
        cwd: folder.uri.fsPath,
      });
    }
  }
  if (folder) {
    candidates.push({
      binPath: path.join(folder.uri.fsPath, 'bin', 'zen-selfhost'),
      cwd: folder.uri.fsPath,
    });
    candidates.push({
      binPath: path.join(folder.uri.fsPath, 'bin', 'zen'),
      cwd: folder.uri.fsPath,
    });
  }
  if (document) {
    let dir = path.dirname(document.uri.fsPath);
    for (let i = 0; i < 8; i++) {
      candidates.push({ binPath: path.join(dir, 'bin', 'zen-selfhost'), cwd: dir });
      candidates.push({ binPath: path.join(dir, 'bin', 'zen'), cwd: dir });
      const parent = path.dirname(dir);
      if (parent === dir) break;
      dir = parent;
    }
  }

  for (const c of candidates) {
    if (fs.existsSync(c.binPath)) return c;
  }
  return null;
}

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

const HOVERS = {
  '->': '**Bind / assign** — data flows into a name, member, or index.\n\n`let x -> 1`',
  '<-': '**Return** — data flows out of a function or task.\n\n`<- value`',
  ':>': '**Infer-and-lock** type on binding.\n\n`let x :> 42`',
  '..': '**Half-open range** `a..b` → sequence from a inclusive to b exclusive.',
  '..=': '**Closed range** `a..=b` → sequence including both ends.',
  when: '**Branching / Pattern Matching** — conditional execution and destructuring.\n\n`when cond { ... } or { ... }`',
  check: '**Check Statement** — multi-case pattern matching with optional guard conditions and fallbacks.\n\n`check expr { case pat [when guard] { ... } } or { ... }`',
  task: '**Task** — lightweight unified asynchronous concurrency unit.\n\n`task { ... }`',
  is: '**Pattern Match / Type Inspection** — inspects shape, destructures fields, and binds variables.\n\n`when x is [first, ...rest] { ... }`',
  and: 'Logical and (prefer over `&&`).',
  or: 'Logical or, or the else-branch keyword after `when`.',
  not: 'Logical not.',
  let: '**Mutable variable** binding introducer.\n\n`let count -> 0`',
  set: '**Immutable constant** binding introducer.\n\n`set PI -> 3.14159`',
  function: '**Function declaration** or anonymous lambda introducer.\n\n`function add(a, b) { <- a + b }`',
  class: '**Class declaration** — blueprint for state and methods with inheritance.\n\n`class Animal extends Organism { ... }`',
  structure: '**Structure declaration** — named record shape with typed fields.\n\n`structure Point { x, y }`',
  enumerator: '**Enumerator declaration** — algebraic data type variants.\n\n`enumerator Status { Active, Inactive, Pending(Reason) }`',
  defer: '**Defer Statement** — executes block when exiting current scope.',
  scope: '**Scope Block** — creates an isolated named lexical scope.',
  do: 'Loop introducer: `do while`, `do for`, `do { } while`.',
  Nothing: '**Nothing** — canonical literal representing the absence of a value.',
  Default: '**Default** — canonical literal materializing the type\'s natural zero/empty state (`0`, `[]`, `""`, `False`).',
  True: 'Boolean True literal.',
  False: 'Boolean False literal.',
};

function buildCompletions(document) {
  const keywords = [
    'let', 'set', 'function', 'class', 'structure', 'enumerator',
    'import', 'use', 'from', 'as', 'export', 'when', 'or', 'and', 'not',
    'do', 'while', 'until', 'for', 'in', 'return', 'break', 'continue',
    'check', 'raise', 'assert', 'defer', 'task', 'is', 'type', 'object',
    'scope', 'extends', 'extend', 'True', 'False', 'Nothing', 'Default',
    'self', 'parent', 'auto',
  ];
  const types = [
    'Integer', 'Decimal', 'String', 'Boolean', 'List', 'Map', 'Dictionary',
    'Tuple', 'Vector', 'Set', 'Void', 'Variant', 'Error', 'Task', 'Function',
    'Structure', 'Class', 'Enumerator', 'Option', 'Result', 'Auto', 'Rune',
  ];
  const modules = [
    'zen.io.io', 'zen.io.file', 'zen.io.path',
    'zen.text.string', 'zen.sys.sys', 'zen.sys.process', 'zen.sys.term',
    'zen.test', 'zen.collections.list', 'zen.collections.map', 'zen.data.json', 'zen.math.math',
    'zen.crypto.hash', 'zen.net.http',
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

  const arrow = new vscode.CompletionItem('->', vscode.CompletionItemKind.Operator);
  arrow.detail = 'bind / assign';
  items.push(arrow);
  const ret = new vscode.CompletionItem('<-', vscode.CompletionItemKind.Operator);
  ret.detail = 'return';
  items.push(ret);
  const inf = new vscode.CompletionItem(':>', vscode.CompletionItemKind.Operator);
  inf.detail = 'infer and lock type';
  items.push(inf);

  const text = document.getText();
  const words = new Set(text.match(/[A-Za-z_][A-Za-z0-9_]*/g) || []);
  for (const word of words) {
    if (!keywords.includes(word) && !types.includes(word)) {
      items.push(new vscode.CompletionItem(word, vscode.CompletionItemKind.Text));
    }
  }
  return items;
}

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
        output.appendLine(combined);
        vscode.window.showErrorMessage('Zenlang: check failed (see Zenlang output)');
      }
    }
  });
}

function parseDiagnostics(outputText, filePath, cwd) {
  const lines = outputText.split(/\r?\n/);
  /** @type {vscode.Diagnostic[]} */
  const diags = [];
  const base = path.resolve(filePath);

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
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

function scheduleDiagnostics(document) {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => updateDiagnostics(document, false), 300);
}

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
  const q = (s) => `"${s.replace(/"/g, '\\"')}"`;
  term.sendText(`${q(python)} ${args.map(q).join(' ')}`);
}

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  output = vscode.window.createOutputChannel('Zenlang');
  diagnostics = vscode.languages.createDiagnosticCollection('zenlang');
  context.subscriptions.push(diagnostics, output);

  function tryStartLsp() {
    const cfg = vscode.workspace.getConfiguration('zenlang');
    if (!cfg.get('lsp.enabled')) return;
    const lspInfo = resolveLspBin();
    if (lspInfo) {
      if (lspClient) lspClient.stop();
      lspClient = new ZenLspClient(lspInfo.binPath, lspInfo.cwd, output);
      lspClient.start();
    }
  }
  tryStartLsp();

  context.subscriptions.push(
    vscode.commands.registerCommand('zenlang.restartLsp', () => {
      tryStartLsp();
      vscode.window.showInformationMessage('Zenlang: LSP Server restarted.');
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('zenlang.checkFile', () => {
      const doc = vscode.window.activeTextEditor?.document;
      if (doc && doc.languageId === 'zenlang') {
        if (lspClient && lspClient.isReady) {
          lspClient.notifySave(doc);
        } else {
          updateDiagnostics(doc, true);
        }
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
      if (lspClient && lspClient.isReady) {
        lspClient.notifySave(document);
      } else {
        const cfg = vscode.workspace.getConfiguration('zenlang');
        if (cfg.get('diagnostics.enabled') && cfg.get('diagnostics.onSave')) {
          scheduleDiagnostics(document);
        }
      }
    })
  );

  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument((event) => {
      const document = event.document;
      if (document.languageId !== 'zenlang') return;
      if (lspClient && lspClient.isReady) {
        lspClient.notifyChange(document);
      }
    })
  );

  context.subscriptions.push(
    vscode.workspace.onDidOpenTextDocument((document) => {
      if (document.languageId !== 'zenlang') return;
      if (lspClient && lspClient.isReady) {
        lspClient.notifyOpen(document);
      } else {
        const cfg = vscode.workspace.getConfiguration('zenlang');
        if (cfg.get('diagnostics.enabled') && cfg.get('diagnostics.onOpen')) {
          scheduleDiagnostics(document);
        }
      }
    })
  );

  context.subscriptions.push(
    vscode.workspace.onDidCloseTextDocument((document) => {
      if (document.languageId !== 'zenlang') return;
      if (lspClient && lspClient.isReady) {
        lspClient.notifyClose(document);
      }
    })
  );

  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration('zenlang')) {
        tryStartLsp();
      }
    })
  );

  // Completions provider (LSP with local fallback)
  context.subscriptions.push(
    vscode.languages.registerCompletionItemProvider('zenlang', {
      async provideCompletionItems(document, position) {
        if (lspClient && lspClient.isReady) {
          try {
            const res = await lspClient.sendRequest('textDocument/completion', {
              textDocument: { uri: document.uri.toString() },
              position: { line: position.line, character: position.character },
            }, 400);
            if (Array.isArray(res) && res.length > 0) {
              return res.map((item) => {
                const ci = new vscode.CompletionItem(item.label, item.kind || vscode.CompletionItemKind.Text);
                if (item.detail) ci.detail = item.detail;
                return ci;
              });
            }
          } catch (e) {
            // fallback
          }
        }
        return buildCompletions(document);
      },
    }, '.', '->', ':>')
  );

  // Hover provider (LSP with local fallback)
  context.subscriptions.push(
    vscode.languages.registerHoverProvider('zenlang', {
      async provideHover(document, position) {
        if (lspClient && lspClient.isReady) {
          try {
            const res = await lspClient.sendRequest('textDocument/hover', {
              textDocument: { uri: document.uri.toString() },
              position: { line: position.line, character: position.character },
            }, 300);
            if (res && res.contents) {
              const val = res.contents.value || res.contents;
              return new vscode.Hover(new vscode.MarkdownString(val));
            }
          } catch (e) {
            // fallback
          }
        }
        const range = document.getWordRangeAtPosition(position, /->|<-|:>|\.\.=|\.\.|[A-Za-z_][A-Za-z0-9_]*/);
        if (!range) return;
        const word = document.getText(range);
        const tip = HOVERS[word];
        if (!tip) return;
        return new vscode.Hover(new vscode.MarkdownString(tip));
      },
    })
  );

  // Definition provider (LSP)
  context.subscriptions.push(
    vscode.languages.registerDefinitionProvider('zenlang', {
      async provideDefinition(document, position) {
        if (lspClient && lspClient.isReady) {
          try {
            const res = await lspClient.sendRequest('textDocument/definition', {
              textDocument: { uri: document.uri.toString() },
              position: { line: position.line, character: position.character },
            }, 400);
            if (res && res.uri && res.range) {
              const start = res.range.start || { line: 0, character: 0 };
              const end = res.range.end || { line: 0, character: 10 };
              return new vscode.Location(
                vscode.Uri.parse(res.uri),
                new vscode.Range(start.line, start.character, end.line, end.character)
              );
            }
          } catch (e) {
            // ignore
          }
        }
        return null;
      },
    })
  );

  // Document Symbol provider (LSP)
  context.subscriptions.push(
    vscode.languages.registerDocumentSymbolProvider('zenlang', {
      async provideDocumentSymbols(document) {
        if (lspClient && lspClient.isReady) {
          try {
            const res = await lspClient.sendRequest('textDocument/documentSymbol', {
              textDocument: { uri: document.uri.toString() },
            }, 500);
            if (Array.isArray(res)) {
              return res.map((s) => {
                const r = s.range || { start: { line: 0, character: 0 }, end: { line: 0, character: 10 } };
                const sr = s.selectionRange || r;
                const range = new vscode.Range(r.start.line, r.start.character, r.end.line, r.end.character);
                const selRange = new vscode.Range(sr.start.line, sr.start.character, sr.end.line, sr.end.character);
                return new vscode.DocumentSymbol(s.name, s.detail || '', s.kind || vscode.SymbolKind.Variable, range, selRange);
              });
            }
          } catch (e) {
            // ignore
          }
        }
        return [];
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

function deactivate() {
  if (debounceTimer) clearTimeout(debounceTimer);
  if (lspClient) lspClient.stop();
}

module.exports = {
  activate,
  deactivate,
};
