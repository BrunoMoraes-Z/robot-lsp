import * as vscode from "vscode";
import { findRobotTestAtLine } from "../../application/collectTests";
import { buildDebugLaunchConfiguration, buildRunLaunchConfiguration } from "../../application/resolveLaunchConfig";
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

  public async debugCurrentFile(): Promise<void> {
    const editor = this.activeRobotEditor();
    if (editor === undefined) {
      void vscode.window.showWarningMessage("Open a Robot Framework file to debug it.");
      return;
    }
    await this.debugFile(editor.document.uri);
  }

  public async runCurrentTest(): Promise<void> {
    const editor = this.activeRobotEditor();
    if (editor === undefined) {
      void vscode.window.showWarningMessage("Open a Robot Framework file to run a test.");
      return;
    }

    const test = this.currentTest(editor);
    if (test === undefined) {
      void vscode.window.showWarningMessage("Place the cursor inside a Robot Framework test or task.");
      return;
    }

    await this.runTest(test);
  }

  public async debugCurrentTest(): Promise<void> {
    const editor = this.activeRobotEditor();
    if (editor === undefined) {
      void vscode.window.showWarningMessage("Open a Robot Framework file to debug a test.");
      return;
    }

    const test = this.currentTest(editor);
    if (test === undefined) {
      void vscode.window.showWarningMessage("Place the cursor inside a Robot Framework test or task.");
      return;
    }

    await this.debugTest(test);
  }

  public async runFile(uri: vscode.Uri): Promise<boolean> {
    return this.start(uri, undefined, false);
  }

  public async runTest(test: RobotTestItem): Promise<boolean> {
    return this.start(vscode.Uri.parse(test.uri), test.name, false);
  }

  public async debugFile(uri: vscode.Uri): Promise<boolean> {
    return this.start(uri, undefined, true);
  }

  public async debugTest(test: RobotTestItem): Promise<boolean> {
    return this.start(vscode.Uri.parse(test.uri), test.name, true);
  }

  private async start(uri: vscode.Uri, testName: string | undefined, debug: boolean): Promise<boolean> {
    const workspaceFolder = vscode.workspace.getWorkspaceFolder(uri);
    const cwd = workspaceFolder?.uri.fsPath ?? uri.fsPath.replace(/[\\/][^\\/]*$/, "");
    const target = {
      target: uri.fsPath,
      cwd,
      testName,
    };
    const config = debug
      ? buildDebugLaunchConfiguration(this.settings.read(), target)
      : buildRunLaunchConfiguration(this.settings.read(), target);
    return vscode.debug.startDebugging(workspaceFolder, config);
  }

  private currentTest(editor: vscode.TextEditor): RobotTestItem | undefined {
    return findRobotTestAtLine(
      editor.document.uri.toString(),
      editor.document.getText(),
      editor.selection.active.line,
    );
  }

  private activeRobotEditor(): vscode.TextEditor | undefined {
    const editor = vscode.window.activeTextEditor;
    if (editor?.document.languageId !== "robotframework") {
      return undefined;
    }
    return editor;
  }
}
