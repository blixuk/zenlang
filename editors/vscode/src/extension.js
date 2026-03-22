const vscode = require('vscode');
const cp = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('ZenLang extension is now active!');

    const collection = vscode.languages.createDiagnosticCollection('zenlang');
    context.subscriptions.push(collection);

    if (vscode.workspace.textDocuments.length > 0) {
        updateDiagnostics(vscode.workspace.textDocuments[0], collection);
    }

    context.subscriptions.push(vscode.workspace.onDidSaveTextDocument(document => {
        if (document.languageId === 'zenlang') {
            updateDiagnostics(document, collection);
        }
    }));

    context.subscriptions.push(vscode.workspace.onDidOpenTextDocument(document => {
        if (document.languageId === 'zenlang') {
            updateDiagnostics(document, collection);
        }
    }));

    // Basic Auto-complete for keywords
    const provider = vscode.languages.registerCompletionItemProvider('zenlang', {
        provideCompletionItems(document, position, token, context) {
            const keywords = [
                'let', 'set', 'function', 'class', 'structure', 'enumerator',
                'import', 'from', 'as', 'when', 'or', 'while', 'for', 'in',
                'return', 'break', 'continue', 'try', 'catch', 'throw', 'await', 'task',
                'True', 'False', 'Void', 'Nothing', 'self', 'parent',
            ];

            const types = [
                'Integer', 'Decimal', 'String', 'Boolean', 'List', 'Dictionary', 'Tuple',
                'Vector', 'Set', 'Iterable', 'Iterator', 'Object', 'Auto', 'Variant', 'Structure', 'Class', 'Enumerator', 'Function', 'Task'
            ];

            const completions = [];

            // Add keywords
            for (const kw of keywords) {
                completions.push(new vscode.CompletionItem(kw, vscode.CompletionItemKind.Keyword));
            }

            // Add types
            for (const type of types) {
                completions.push(new vscode.CompletionItem(type, vscode.CompletionItemKind.Class));
            }

            // Simple "word in document" completion
            const text = document.getText();
            const words = new Set(text.match(/[a-zA-Z_][a-zA-Z0-9_]*/g) || []);
            for (const word of words) {
                if (!keywords.includes(word) && !types.includes(word)) {
                    completions.push(new vscode.CompletionItem(word, vscode.CompletionItemKind.Text));
                }
            }

            return completions;
        }
    });

    context.subscriptions.push(provider);
}

function updateDiagnostics(document, collection) {
    if (document.languageId !== 'zenlang') {
        return;
    }

    const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);
    if (!workspaceFolder) {
        return;
    }

    // Assuming Zen.py is in the root of the workspace if the workspace is 'zen'
    // Or we can try to find it.
    // For this specific environment:
    const zenPyPath = path.join(workspaceFolder.uri.fsPath, 'bootstrap', 'Zen.py');
    const filePath = document.uri.fsPath;

    // Run the compiler
    // We only want to run the first stage (parsing) which Zen.py seems to do by default or we can look at arguments.
    // The previous run `python3 Zen.py src/compiler/CTranspiler.zl` failed at parsing, which is what we want (to see errors).

    cp.exec(`python3 "${zenPyPath}" "${filePath}"`, { cwd: workspaceFolder.uri.fsPath }, (err, stdout, stderr) => {
        if (err) {
            // Compiler returned error code, meaning there might be syntax errors
            // The output is in stderr or stdout? The previous tool output showed it in Output (stdout/stderr combined usually).
            // Let's check both.
        }

        const output = stdout + stderr;
        const diagnostics = [];

        // Parse output
        // Format: src/compiler/CTranspiler.zl:1:8
        // And also message lines before it.
        // Example:
        // [Parser] [ExpectTokenError] Expected path after import/from
        //     Token: Token(...)
        // src/compiler/CTranspiler.zl:1:8

        const lines = output.split('\n');
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const match = line.match(/(.+):(\d+):(\d+)/);
            if (match) {
                const file = match[1];
                // Check if this error belongs to the current file
                if (path.resolve(workspaceFolder.uri.fsPath, file) === filePath || file === filePath) {
                    const lineNum = parseInt(match[2]) - 1; // VSCode is 0-indexed
                    const colNum = parseInt(match[3]) - 1;

                    // Try to find the message from previous lines
                    let message = "Error";
                    if (i > 0) {
                        // Look backwards for a line starting with [Parser] or similar
                        for (let j = i - 1; j >= 0; j--) {
                            if (lines[j].trim().startsWith('[') || lines[j].trim().length > 0) {
                                message = lines[j].trim();
                                // If it's the token dump, go back one more
                                if (message.startsWith('Token:')) {
                                    continue;
                                }
                                break;
                            }
                        }
                    }

                    const range = new vscode.Range(lineNum, colNum, lineNum, colNum + 100); // Highlight next chars
                    const diagnostic = new vscode.Diagnostic(range, message, vscode.DiagnosticSeverity.Error);
                    diagnostics.push(diagnostic);
                }
            }
        }

        collection.set(document.uri, diagnostics);
    });
}

function deactivate() { }

module.exports = {
    activate,
    deactivate
};
