import * as vscode from "vscode";
import { buildDebugLaunchConfiguration } from "../../application/resolveLaunchConfig";
import type { SettingsReader } from "../../application/ports";

export interface DebugAdapterRegistration {
  dispose(): void;
}

export class RobotDebugAdapterRegistration implements DebugAdapterRegistration {
  private readonly registrations: readonly vscode.Disposable[];

  public constructor(context: vscode.ExtensionContext, settings: SettingsReader) {
    this.registrations = [
      vscode.debug.registerDebugConfigurationProvider("robot-lsp", new RobotDebugConfigurationProvider(settings)),
      vscode.debug.registerDebugAdapterDescriptorFactory("robot-lsp", new RobotDebugAdapterDescriptorFactory(context)),
    ];
  }

  public dispose(): void {
    for (const registration of this.registrations) {
      registration.dispose();
    }
  }
}

class RobotDebugAdapterDescriptorFactory implements vscode.DebugAdapterDescriptorFactory {
  public constructor(private readonly context: vscode.ExtensionContext) {}

  public createDebugAdapterDescriptor(): vscode.ProviderResult<vscode.DebugAdapterDescriptor> {
    return new vscode.DebugAdapterExecutable(process.execPath, [
      this.context.asAbsolutePath("out/infrastructure/debugAdapterRuntime.js"),
    ]);
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
