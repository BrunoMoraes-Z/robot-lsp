import type { RobotLspSettings } from "../domain/settings";

export interface PlannedServerCommand {
  readonly command: string;
  readonly args: readonly string[];
  readonly cwd?: string;
  readonly env: Readonly<Record<string, string>>;
  readonly initializationOptions: Readonly<Record<string, unknown>>;
}

export function planServerCommand(settings: RobotLspSettings, fallbackPython: string): PlannedServerCommand {
  if (settings.languageServer.command.trim().length > 0) {
    return {
      command: settings.languageServer.command,
      args: settings.languageServer.args,
      cwd: settings.languageServer.cwd || undefined,
      env: settings.languageServer.env,
      initializationOptions: serverInitializationOptions(settings),
    };
  }

  const python = settings.languageServer.python.trim() || fallbackPython;
  return {
    command: python,
    args: ["-m", "robot_lsp", ...settings.languageServer.args],
    cwd: settings.languageServer.cwd || undefined,
    env: settings.languageServer.env,
    initializationOptions: serverInitializationOptions(settings),
  };
}

export function serverInitializationOptions(settings: RobotLspSettings): Readonly<Record<string, unknown>> {
  return {
    diagnostics: {
      enable: settings.diagnosticsEnable,
    },
    completion: {
      snippets: settings.completionSnippets,
    },
    logLevel: settings.logLevel,
    variables: settings.variables,
  };
}
