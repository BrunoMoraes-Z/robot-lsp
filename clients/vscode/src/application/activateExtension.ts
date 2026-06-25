import type { CommandRegistry, Logger, SettingsReader } from "./ports";

export interface ActivateExtensionDependencies {
  readonly commands: CommandRegistry;
  readonly logger: Logger;
  readonly settings: SettingsReader;
}

export function activateExtension(dependencies: ActivateExtensionDependencies): void {
  const settings = dependencies.settings.read();
  dependencies.logger.info(`Robot LSP VS Code client activated with log level: ${settings.logLevel}`);

  dependencies.commands.register("robot-lsp.restartLanguageServer", () => {
    dependencies.logger.info("Language server restart requested. Startup will be implemented in Stage 02.");
  });

  dependencies.commands.register("robot-lsp.selectPythonInterpreter", () => {
    dependencies.logger.info("Python interpreter selection requested. Resolution will be implemented in Stage 03.");
  });
}
