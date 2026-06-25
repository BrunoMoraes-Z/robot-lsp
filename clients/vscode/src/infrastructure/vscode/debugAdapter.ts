import * as vscode from "vscode";
import { buildDebugLaunchConfiguration } from "../../application/resolveLaunchConfig";
import type { SettingsReader } from "../../application/ports";

export interface DebugAdapterRegistration {
  dispose(): void;
}

export class RobotDebugAdapterRegistration implements DebugAdapterRegistration {
  private readonly registration: vscode.Disposable;

  public constructor(settings: SettingsReader) {
    this.registration = vscode.debug.registerDebugConfigurationProvider(
      "robot-lsp",
      new RobotDebugConfigurationProvider(settings),
    );
  }

  public dispose(): void {
    this.registration.dispose();
  }
}

class RobotDebugConfigurationProvider implements vscode.DebugConfigurationProvider {
  public constructor(private readonly settings: SettingsReader) {}

  public resolveDebugConfiguration(
    folder: vscode.WorkspaceFolder | undefined,
    config: vscode.DebugConfiguration,
  ): vscode.ProviderResult<vscode.DebugConfiguration> {
    const activeRobotDocument = vscode.window.activeTextEditor?.document.languageId === "robotframework"
      ? vscode.window.activeTextEditor.document
      : undefined;
    const target = stringOrStringArray(config.target)
      ?? activeRobotDocument?.uri.fsPath
      ?? "${file}";
    const cwd = typeof config.cwd === "string"
      ? config.cwd
      : folder?.uri.fsPath ?? "${workspaceFolder}";
    const generated = buildDebugLaunchConfiguration(this.settings.read(), {
      target,
      cwd,
    });

    return {
      ...generated,
      ...config,
      type: "robot-lsp",
      request: "launch",
      name: typeof config.name === "string" ? config.name : generated.name,
      target,
      cwd,
      noDebug: typeof config.noDebug === "boolean" ? config.noDebug : generated.noDebug,
    };
  }
}

function stringOrStringArray(value: unknown): string | readonly string[] | undefined {
  if (typeof value === "string") {
    return value;
  }
  if (Array.isArray(value) && value.every((item) => typeof item === "string")) {
    return value;
  }
  return undefined;
}
