import * as vscode from "vscode";
import type { PythonExecutable } from "../../domain/models";
import type { PythonCandidateProvider } from "../../application/ports";

export class VsCodePythonExtensionProvider implements PythonCandidateProvider {
  public async candidate(): Promise<PythonExecutable | undefined> {
    const extension = vscode.extensions.getExtension("ms-python.python");
    if (extension === undefined) {
      return undefined;
    }

    const api = (await extension.activate()) as PythonExtensionApi;
    const executionDetails = api.settings?.getExecutionDetails?.(vscode.window.activeTextEditor?.document.uri);
    const command = executionDetails?.execCommand?.[0];
    if (typeof command === "string" && command.length > 0) {
      return { path: command, source: "pythonExtension" };
    }

    const legacyPath = api.settings?.getExecutionDetails?.()?.execCommand?.[0];
    if (typeof legacyPath === "string" && legacyPath.length > 0) {
      return { path: legacyPath, source: "pythonExtension" };
    }

    return undefined;
  }
}

interface PythonExtensionApi {
  readonly settings?: {
    getExecutionDetails?(resource?: vscode.Uri): {
      readonly execCommand?: readonly string[];
    };
  };
}
