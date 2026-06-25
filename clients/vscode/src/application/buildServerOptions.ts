import { delimiter } from "node:path";
import type { RobotLspSettings } from "../domain/settings";
import { serverRobotLspConfiguration, type ServerRobotLspConfiguration } from "./configurationBridge";

export interface PlannedServerCommand {
  readonly command: string;
  readonly args: readonly string[];
  readonly cwd?: string;
  readonly env: Readonly<Record<string, string>>;
  readonly initializationOptions: ServerRobotLspConfiguration;
}

export function planServerCommand(
  settings: RobotLspSettings,
  fallbackPython: string,
  bundledLibPath: string = "",
): PlannedServerCommand {
  const baseEnv = settings.languageServer.env;
  const env = bundledLibPath.length > 0 ? withBundledPath(baseEnv, bundledLibPath) : { ...baseEnv };

  if (settings.languageServer.command.trim().length > 0) {
    return {
      command: settings.languageServer.command,
      args: settings.languageServer.args,
      cwd: settings.languageServer.cwd || undefined,
      env,
      initializationOptions: serverInitializationOptions(settings),
    };
  }

  const python = settings.languageServer.python.trim() || fallbackPython;
  return {
    command: python,
    args: ["-m", "robot_lsp", ...settings.languageServer.args],
    cwd: settings.languageServer.cwd || undefined,
    env,
    initializationOptions: serverInitializationOptions(settings),
  };
}

function withBundledPath(
  base: Readonly<Record<string, string>>,
  bundledLibPath: string,
): Record<string, string> {
  const existing = base["PYTHONPATH"] ?? "";
  const pythonPath = existing ? `${bundledLibPath}${delimiter}${existing}` : bundledLibPath;
  return { ...base, PYTHONPATH: pythonPath };
}

export function serverInitializationOptions(settings: RobotLspSettings): ServerRobotLspConfiguration {
  return serverRobotLspConfiguration(settings);
}
