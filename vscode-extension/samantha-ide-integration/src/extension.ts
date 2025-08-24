// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import fetch from 'node-fetch';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "samantha-ide-integration" is now active!');

	// The command has been defined in the package.json file
	// Now provide the implementation of the command with registerCommand
	// The commandId parameter must match the command field in package.json
	const disposable = vscode.commands.registerCommand('samantha-ide-integration.helloWorld', () => {
		// The code you place here will be executed every time your command is executed
		// Display a message box to the user
		vscode.window.showInformationMessage('Hello World from samantha!');
	});

	context.subscriptions.push(disposable);

	let readDisposable = vscode.commands.registerCommand('samantha-ide-integration.readFile', async () => {
		const editor = vscode.window.activeTextEditor;
		if (!editor) {
			vscode.window.showWarningMessage('No active text editor found.');
			return;
		}

		const filePath = editor.document.uri.fsPath;
		try {
			const response = await fetch('http://localhost:8004/read_file', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ file_path: filePath })
			});
			const data = await response.json();

			if (data.success) {
				vscode.window.showInformationMessage(`File content: ${data.content.substring(0, 100)}...`);
			} else {
				vscode.window.showErrorMessage(`Failed to read file: ${data.error}`);
			}
		} catch (error: any) {
			vscode.window.showErrorMessage(`Error communicating with IDE Integration Server: ${error.message}`);
		}
	});

	context.subscriptions.push(readDisposable);

	let editDisposable = vscode.commands.registerCommand('samantha-ide-integration.editFile', async () => {
		const editor = vscode.window.activeTextEditor;
		if (!editor) {
			vscode.window.showWarningMessage('No active text editor found.');
			return;
		}

		const filePath = editor.document.uri.fsPath;
		const content = await vscode.window.showInputBox({ prompt: 'Enter content to write to file' });
		if (content === undefined) {
			return; // User cancelled input
		}

		try {
			const response = await fetch('http://localhost:8004/edit_file', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ file_path: filePath, content: content, operation: 'write' })
			});
			const data = await response.json();

			if (data.success) {
				vscode.window.showInformationMessage(`File edited successfully: ${data.file_path}`);
			} else {
				vscode.window.showErrorMessage(`Failed to edit file: ${data.error}`);
			}
		} catch (error: any) {
			vscode.window.showErrorMessage(`Error communicating with IDE Integration Server: ${error.message}`);
		}
	});

	context.subscriptions.push(editDisposable);

	let gitStatusDisposable = vscode.commands.registerCommand('samantha-ide-integration.gitStatus', async () => {
		const workspaceFolders = vscode.workspace.workspaceFolders;
		if (!workspaceFolders || workspaceFolders.length === 0) {
			vscode.window.showWarningMessage('No workspace folder open.');
			return;
		}

		const repoPath = workspaceFolders[0].uri.fsPath;
		try {
			const response = await fetch('http://localhost:8004/git_status', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ repo_path: repoPath })
			});
			const data = await response.json();

			if (data.success) {
				vscode.window.showInformationMessage(`Git Status: Branch - ${data.branch}, Status - ${data.status}, Modified - ${data.modified_files.length}`);
			} else {
				vscode.window.showErrorMessage(`Failed to get Git status: ${data.error}`);
			}
		} catch (error: any) {
			vscode.window.showErrorMessage(`Error communicating with IDE Integration Server: ${error.message}`);
		}
	});

	context.subscriptions.push(gitStatusDisposable);

	let gitCommitDisposable = vscode.commands.registerCommand('samantha-ide-integration.gitCommit', async () => {
		const workspaceFolders = vscode.workspace.workspaceFolders;
		if (!workspaceFolders || workspaceFolders.length === 0) {
			vscode.window.showWarningMessage('No workspace folder open.');
			return;
		}

		const repoPath = workspaceFolders[0].uri.fsPath;
		const commitMessage = await vscode.window.showInputBox({ prompt: 'Enter commit message' });
		if (commitMessage === undefined) {
			return; // User cancelled input
		}

		try {
			const response = await fetch('http://localhost:8004/git_commit', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ repo_path: repoPath, message: commitMessage, add_all: true })
			});
			const data = await response.json();

			if (data.success) {
				vscode.window.showInformationMessage(`Git Commit successful: ${data.message}`);
			} else {
				vscode.window.showErrorMessage(`Failed to commit: ${data.error}`);
			}
		} catch (error: any) {
			vscode.window.showErrorMessage(`Error communicating with IDE Integration Server: ${error.message}`);
		}
	});

	context.subscriptions.push(gitCommitDisposable);

	let gitPushDisposable = vscode.commands.registerCommand('samantha-ide-integration.gitPush', async () => {
		const workspaceFolders = vscode.workspace.workspaceFolders;
		if (!workspaceFolders || workspaceFolders.length === 0) {
			vscode.window.showWarningMessage('No workspace folder open.');
			return;
		}

		const repoPath = workspaceFolders[0].uri.fsPath;
		try {
			const response = await fetch('http://localhost:8004/git_push', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ repo_path: repoPath })
			});
			const data = await response.json();

			if (data.success) {
				vscode.window.showInformationMessage(`Git Push successful: ${data.message}`);
			} else {
				vscode.window.showErrorMessage(`Failed to push: ${data.error}`);
			}
		} catch (error: any) {
			vscode.window.showErrorMessage(`Error communicating with IDE Integration Server: ${error.message}`);
		}
	});

	context.subscriptions.push(gitPushDisposable);

	let runCommandDisposable = vscode.commands.registerCommand('samantha-ide-integration.runCommand', async () => {
		const command = await vscode.window.showInputBox({ prompt: 'Enter command to run' });
		if (command === undefined) {
			return; // User cancelled input
		}

		try {
			const response = await fetch('http://localhost:8004/run_command', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ command: command })
			});
			const data = await response.json();

			if (data.success) {
				vscode.window.showInformationMessage(`Command output: ${data.output}`);
			} else {
				vscode.window.showErrorMessage(`Failed to run command: ${data.error}`);
			}
		} catch (error: any) {
			vscode.window.showErrorMessage(`Error communicating with IDE Integration Server: ${error.message}`);
		}
	});

	context.subscriptions.push(runCommandDisposable);

	let debugCommandDisposable = vscode.commands.registerCommand('samantha-ide-integration.debugCommand', async () => {
		const debugCommand = await vscode.window.showInputBox({ prompt: 'Enter debug command to run' });
		if (debugCommand === undefined) {
			return; // User cancelled input
		}

		try {
			const response = await fetch('http://localhost:8004/run_command', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ command: debugCommand })
			});
			const data = await response.json();

			if (data.success) {
				vscode.window.showInformationMessage(`Debug command output: ${data.output}`);
			} else {
				vscode.window.showErrorMessage(`Failed to run debug command: ${data.error}`);
			}
		} catch (error: any) {
			vscode.window.showErrorMessage(`Error communicating with IDE Integration Server: ${error.message}`);
		}
	});

	context.subscriptions.push(debugCommandDisposable);

	let installExtensionDisposable = vscode.commands.registerCommand('samantha-ide-integration.installExtension', async () => {
		const extensionId = await vscode.window.showInputBox({ prompt: 'Enter extension ID to install' });
		if (extensionId === undefined) {
			return; // User cancelled input
		}

		try {
			const response = await fetch('http://localhost:8004/install_extension', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ extension_id: extensionId })
			});
			const data = await response.json();

			if (data.success) {
				vscode.window.showInformationMessage(`Extension installed: ${data.extension}`);
			} else {
				vscode.window.showErrorMessage(`Failed to install extension: ${data.error}`);
			}
		} catch (error: any) {
			vscode.window.showErrorMessage(`Error communicating with IDE Integration Server: ${error.message}`);
		}
	});

	context.subscriptions.push(installExtensionDisposable);
}

// This method is called when your extension is deactivated
export function deactivate() {}
