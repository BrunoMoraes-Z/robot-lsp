import * as vscode from "vscode";
import { activateExtension } from "./application/activateExtension";
import { VsCodeCommandRegistry } from "./infrastructure/vscode/commandRegistry";
import { OutputChannelLogger } from "./infrastructure/vscode/logging";
import { VsCodeSettingsReader } from "./infrastructure/vscode/workspaceConfig";

export function activate(context: vscode.ExtensionContext): void {
  const output = vscode.window.createOutputChannel("Robot LSP");
  context.subscriptions.push(output);

  activateExtension({
    commands: new VsCodeCommandRegistry(context.subscriptions),
    logger: new OutputChannelLogger(output),
    settings: new VsCodeSettingsReader(),
  });
}

export function deactivate(): void {
  return undefined;
}
