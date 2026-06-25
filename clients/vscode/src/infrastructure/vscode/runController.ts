import * as vscode from "vscode";
import { findRobotTestAtLine } from "../../application/collectTests";
import { buildRunLaunchConfiguration } from "../../application/resolveLaunchConfig";
import type { RobotTestItem } from "../../domain/models";
import type { SettingsReader } from "../../application/ports";

export class RobotRunController {
  public constructor(private readonly settings: SettingsReader) {}

  public async runCurrentFile(): Promise<void> {
    const editor = this.activeRobotEditor();
    if (editor === undefined) {
      void vscode.window.showWarningMessage("Open a Robot Framework file to run it.");
      return;
    }
    await this.runFile(editor.document.uri);
  }

  public async runCurrentTest(): Promise<void> {
    const editor = this.activeRobotEditor();
    if (editor === undefined) {
      void vscode.window.showWarningMessage("Open a Robot Framework file to run a test.");
      return;
    }

    const test = findRobotTestAtLine(
      editor.document.uri.toString(),
      editor.document.getText(),
      editor.selection.active.line,
    );
    if (test === undefined) {
      void vscode.window.showWarningMessage("Place the cursor inside a Robot Framework test or task.");
      return;
    }

    await this.runTest(test);
  }

  public async runFile(uri: vscode.Uri): Promise<void> {
    await this.startRun(uri, undefined);
  }

  public async runTest(test: RobotTestItem): Promise<void> {
    await this.startRun(vscode.Uri.parse(test.uri), test.name);
  }

  private async startRun(uri: vscode.Uri, testName: string | undefined): Promise<boolean> {
    const workspaceFolder = vscode.workspace.getWorkspaceFolder(uri);
    const cwd = workspaceFolder?.uri.fsPath ?? uri.fsPath.replace(/[\\/][^\\/]*$/, "");
    const config = buildRunLaunchConfiguration(this.settings.read(), {
      target: uri.fsPath,
      cwd,
      testName,
    });
    return vscode.debug.startDebugging(workspaceFolder, config);
  }

  private activeRobotEditor(): vscode.TextEditor | undefined {
    const editor = vscode.window.activeTextEditor;
    if (editor?.document.languageId !== "robotframework") {
      return undefined;
    }
    return editor;
  }
}
