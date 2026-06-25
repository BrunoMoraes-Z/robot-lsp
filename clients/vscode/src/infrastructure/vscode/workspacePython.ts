import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";
import type { PythonExecutable } from "../../domain/models";
import type { PythonCandidateProvider } from "../../application/ports";

export class WorkspacePythonProvider implements PythonCandidateProvider {
  public async candidate(): Promise<PythonExecutable | undefined> {
    for (const folder of vscode.workspace.workspaceFolders ?? []) {
      const candidate = firstExistingPython(folder.uri.fsPath);
      if (candidate !== undefined) {
        return { path: candidate, source: "workspace" };
      }
    }
    return undefined;
  }
}

function firstExistingPython(workspaceFolder: string): string | undefined {
  const candidates = process.platform === "win32"
    ? [
        path.join(workspaceFolder, ".venv", "Scripts", "python.exe"),
        path.join(workspaceFolder, "venv", "Scripts", "python.exe"),
        path.join(workspaceFolder, ".env", "Scripts", "python.exe"),
      ]
    : [
        path.join(workspaceFolder, ".venv", "bin", "python"),
        path.join(workspaceFolder, "venv", "bin", "python"),
        path.join(workspaceFolder, ".env", "bin", "python"),
      ];

  return candidates.find((candidate) => fs.existsSync(candidate));
}
