import type { CommandRegistry, LanguageServerController, Logger, SettingsReader } from "./ports";

export interface ActivateExtensionDependencies {
  readonly commands: CommandRegistry;
  readonly languageServer: LanguageServerController;
  readonly logger: Logger;
  readonly settings: SettingsReader;
}

export async function activateExtension(dependencies: ActivateExtensionDependencies): Promise<void> {
  const settings = dependencies.settings.read();
  dependencies.logger.info(`Robot LSP VS Code client activated with log level: ${settings.logLevel}`);

  dependencies.commands.register("robot-lsp.restartLanguageServer", async () => {
    dependencies.logger.info("Language server restart requested.");
    await dependencies.languageServer.restart();
  });

  dependencies.commands.register("robot-lsp.selectPythonInterpreter", () => {
    dependencies.logger.info("Python interpreter selection requested. Resolution will be implemented in Stage 03.");
  });

  await dependencies.languageServer.start();
}
