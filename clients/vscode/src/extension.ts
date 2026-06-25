import * as vscode from "vscode";
import { activateExtension } from "./application/activateExtension";
import { VsCodeCommandRegistry } from "./infrastructure/vscode/commandRegistry";
import { RobotLanguageClientAdapter } from "./infrastructure/vscode/languageClient";
import { OutputChannelLogger } from "./infrastructure/vscode/logging";
import { PathPythonProvider } from "./infrastructure/vscode/pathPython";
import { ProcessPythonValidator } from "./infrastructure/vscode/pythonValidator";
import { VsCodePythonExtensionProvider } from "./infrastructure/vscode/pythonExtension";
import { RobotTestControllerAdapter } from "./infrastructure/vscode/testController";
import { WorkspacePythonProvider } from "./infrastructure/vscode/workspacePython";
import { VsCodeConfigurationBridge, VsCodeSettingsReader } from "./infrastructure/vscode/workspaceConfig";

let languageServer: RobotLanguageClientAdapter | undefined;

export async function activate(context: vscode.ExtensionContext): Promise<void> {
  const output = vscode.window.createOutputChannel("Robot LSP", { log: true });
  context.subscriptions.push(output);
  const logger = new OutputChannelLogger(output);
  const settings = new VsCodeSettingsReader();
  if (settings.read().testExplorerEnabled) {
    const testController = new RobotTestControllerAdapter();
    context.subscriptions.push(testController);
    void testController.refresh();
  }
  const configurationBridge = new VsCodeConfigurationBridge(settings);
  languageServer = new RobotLanguageClientAdapter(
    settings,
    logger,
    output,
    new VsCodePythonExtensionProvider(),
    new WorkspacePythonProvider(),
    new PathPythonProvider(),
    new ProcessPythonValidator(),
    configurationBridge,
  );

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
