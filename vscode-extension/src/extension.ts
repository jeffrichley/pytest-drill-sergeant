import * as vscode from 'vscode';
import * as path from 'path';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    TransportKind
} from 'vscode-languageclient/node';

let client: LanguageClient;

function findPythonCommand(): string {
    // Try different Python commands in order of preference
    const pythonCommands = [
        'uv',  // Use uv run for better dependency management
        'python3',
        'python', 
        'py'
    ];
    
    for (const cmd of pythonCommands) {
        try {
            // Check if command exists and can import our module
            const { execSync } = require('child_process');
            if (cmd === 'uv') {
                // For uv, test if it can run our module
                execSync(`uv run python -c "import pytest_drill_sergeant; print('OK')"`, { stdio: 'ignore' });
                console.log(`Using uv run for Python execution`);
                return 'uv';
            } else {
                execSync(`${cmd} -c "import pytest_drill_sergeant; print('OK')"`, { stdio: 'ignore' });
                console.log(`Using Python command: ${cmd}`);
                return cmd;
            }
        } catch (error) {
            // Command not found or module not available, try next one
            continue;
        }
    }
    
    // If no command works, show helpful error message
    vscode.window.showErrorMessage(
        'Drill Sergeant: Could not find Python with pytest-drill-sergeant installed. ' +
        'Please make sure pytest-drill-sergeant is installed: pip install pytest-drill-sergeant[lsp]'
    );
    
    // Fallback to python3 (most common on macOS/Linux)
    console.log('Using fallback Python command: python3');
    return 'python3';
}

export function activate(context: vscode.ExtensionContext) {
    console.log('Drill Sergeant extension is now active!');

    // Get configuration
    const config = vscode.workspace.getConfiguration('pytest-drill-sergeant');
    const enabled = config.get<boolean>('enabled', true);

    if (!enabled) {
        console.log('Drill Sergeant is disabled in configuration');
        return;
    }

    // Find Python executable
    const pythonCommand = findPythonCommand();
    
    // Server options - run our Python LSP server
    const serverOptions: ServerOptions = {
        run: {
            command: pythonCommand,
            args: pythonCommand === 'uv' 
                ? ['run', 'python', '-m', 'pytest_drill_sergeant.lsp.main']
                : ['-m', 'pytest_drill_sergeant.lsp.main'],
            transport: TransportKind.stdio,
            options: {
                env: {
                    ...process.env,
                    PYTHONPATH: context.extensionPath
                }
            }
        },
        debug: {
            command: pythonCommand,
            args: pythonCommand === 'uv' 
                ? ['run', 'python', '-m', 'pytest_drill_sergeant.lsp.main']
                : ['-m', 'pytest_drill_sergeant.lsp.main'],
            transport: TransportKind.stdio,
            options: {
                env: {
                    ...process.env,
                    PYTHONPATH: context.extensionPath
                }
            }
        }
    };

    // Client options
    const clientOptions: LanguageClientOptions = {
        // Register the server for Python files
        documentSelector: [
            { scheme: 'file', language: 'python' }
        ],
        synchronize: {
            // Notify the server about file changes
            fileEvents: vscode.workspace.createFileSystemWatcher('**/*.py')
        },
        diagnosticCollectionName: 'drill-sergeant',
        outputChannel: vscode.window.createOutputChannel('Drill Sergeant')
    };

    // Create the language client and start the client
    client = new LanguageClient(
        'drill-sergeant-lsp',
        'Drill Sergeant Language Server',
        serverOptions,
        clientOptions
    );

    // Start the client
    client.start();

    // Register commands
    const analyzeFileCommand = vscode.commands.registerCommand(
        'pytest-drill-sergeant.analyzeFile',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No active editor');
                return;
            }

            const document = editor.document;
            if (document.languageId !== 'python') {
                vscode.window.showWarningMessage('File is not a Python file');
                return;
            }

            // Trigger analysis by sending a didSave notification
            await client.sendNotification('textDocument/didSave', {
                textDocument: {
                    uri: document.uri.toString(),
                    version: document.version
                }
            });

            vscode.window.showInformationMessage('🔍 Drill Sergeant analysis triggered!');
        }
    );

    const showReportCommand = vscode.commands.registerCommand(
        'pytest-drill-sergeant.showReport',
        () => {
            // Show the output channel
            client.outputChannel.show();
        }
    );

    // Register commands
    context.subscriptions.push(analyzeFileCommand);
    context.subscriptions.push(showReportCommand);

    // Show welcome message
    vscode.window.showInformationMessage(
        '🎖️ Drill Sergeant is ready! Open a Python test file to see violations.',
        'Analyze Current File'
    ).then(selection => {
        if (selection === 'Analyze Current File') {
            vscode.commands.executeCommand('pytest-drill-sergeant.analyzeFile');
        }
    });
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}