import * as vscode from "vscode";
import type { ClientDiagnostic } from "../domain/diagnostics";

export function showClientDiagnostic(diagnostic: ClientDiagnostic): Thenable<string | undefined> {
  const detail = diagnostic.detail === undefined ? "" : ` ${diagnostic.detail}`;
  return vscode.window.showWarningMessage(`${diagnostic.message}${detail}`);
}
