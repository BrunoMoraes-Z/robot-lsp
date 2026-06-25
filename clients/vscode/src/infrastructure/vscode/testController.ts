import * as vscode from "vscode";
import { collectRobotTestsFromText } from "../../application/collectTests";
import type { RobotTestItem } from "../../domain/models";

export interface TestControllerAdapter {
  refresh(): Promise<void>;
  dispose(): void;
}

export class RobotTestControllerAdapter implements TestControllerAdapter {
  private readonly controller: vscode.TestController;

  public constructor() {
    this.controller = vscode.tests.createTestController("robot-lsp.testController", "Robot Framework");
    this.controller.refreshHandler = async () => this.refresh();
  }

  public async refresh(): Promise<void> {
    this.controller.items.replace([]);
    const files = await vscode.workspace.findFiles("**/*.robot", "**/{.venv,venv,node_modules,out}/**");

    for (const file of files) {
      const bytes = await vscode.workspace.fs.readFile(file);
      const text = Buffer.from(bytes).toString("utf8");
      const tests = collectRobotTestsFromText(file.toString(), text);
      if (tests.length > 0) {
        this.controller.items.add(this.createFileItem(file, tests));
      }
    }
  }

  private createFileItem(file: vscode.Uri, tests: readonly RobotTestItem[]): vscode.TestItem {
    const fileItem = this.controller.createTestItem(file.toString(), this.labelForFile(file), file);
    fileItem.canResolveChildren = false;

    for (const test of tests) {
      const range = new vscode.Range(test.line, 0, test.line, test.name.length);
      const testItem = this.controller.createTestItem(test.id, test.name, file);
      testItem.range = range;
      fileItem.children.add(testItem);
    }

    return fileItem;
  }

  private labelForFile(file: vscode.Uri): string {
    const workspaceFolder = vscode.workspace.getWorkspaceFolder(file);
    if (workspaceFolder === undefined) {
      return file.path.split("/").pop() ?? file.toString();
    }
    return vscode.workspace.asRelativePath(file, false);
  }

  public dispose(): void {
    this.controller.dispose();
  }
}
