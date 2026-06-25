import * as vscode from "vscode";
import { collectRobotTestsFromText } from "../../application/collectTests";
import type { RobotTestItem } from "../../domain/models";
import type { RobotRunController } from "./runController";

export interface TestControllerAdapter {
  refresh(): Promise<void>;
  dispose(): void;
}

export class RobotTestControllerAdapter implements TestControllerAdapter {
  private readonly controller: vscode.TestController;

  public constructor(private readonly runController: RobotRunController | undefined) {
    this.controller = vscode.tests.createTestController("robot-lsp.testController", "Robot Framework");
    this.controller.refreshHandler = async () => this.refresh();
    if (this.runController !== undefined) {
      this.controller.createRunProfile("Run", vscode.TestRunProfileKind.Run, async (request, token) => {
        await this.runFromRequest(request, token);
      });
    }
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
      testItem.sortText = test.line.toString().padStart(8, "0");
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

  private async runFromRequest(request: vscode.TestRunRequest, token: vscode.CancellationToken): Promise<void> {
    if (this.runController === undefined) {
      return;
    }

    const run = this.controller.createTestRun(request);
    try {
      for (const item of this.selectedRunnableItems(request)) {
        if (token.isCancellationRequested) {
          run.skipped(item);
          continue;
        }
        run.started(item);
        const started = await this.runController.runTest({
          id: item.id,
          name: item.label,
          uri: item.uri?.toString() ?? "",
          line: item.range?.start.line ?? 0,
        });
        if (started === undefined) {
          run.enqueued(item);
        }
      }
    } finally {
      run.end();
    }
  }

  private selectedRunnableItems(request: vscode.TestRunRequest): readonly vscode.TestItem[] {
    const selected = request.include ?? [...this.controller.items].flatMap(([, item]) => this.childItems(item));
    return selected.flatMap((item) => this.childItems(item));
  }

  private childItems(item: vscode.TestItem): readonly vscode.TestItem[] {
    const children = [...item.children].map(([, child]) => child);
    return children.length === 0 ? [item] : children.flatMap((child) => this.childItems(child));
  }

  public dispose(): void {
    this.controller.dispose();
  }
}
