import * as vscode from "vscode";
import { activateExtension } from "./application/activateExtension";
import { VsCodeCommandRegistry } from "./infrastructure/vscode/commandRegistry";
import { RobotLanguageClientAdapter } from "./infrastructure/vscode/languageClient";
import { OutputChannelLogger } from "./infrastructure/vscode/logging";
import { VsCodeSettingsReader } from "./infrastructure/vscode/workspaceConfig";

let languageServer: RobotLanguageClientAdapter | undefined;

export async function activate(context: vscode.ExtensionContext): Promise<void> {
  const output = vscode.window.createOutputChannel("Robot LSP", { log: true });
  context.subscriptions.push(output);
  const logger = new OutputChannelLogger(output);
  const settings = new VsCodeSettingsReader();
  languageServer = new RobotLanguageClientAdapter(settings, logger, output);

  await activateExtension({
    commands: new VsCodeCommandRegistry(context.subscriptions),
    languageServer,
    logger,
    settings,
  });
}

export async function deactivate(): Promise<void> {
  await languageServer?.stop();
}
