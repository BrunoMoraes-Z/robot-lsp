import type { PythonExecutable } from "../domain/models";
import type { RobotLspSettings } from "../domain/settings";

export function configuredLanguageServerPython(settings: RobotLspSettings): PythonExecutable | undefined {
  const value = settings.languageServer.python.trim();
  if (value.length === 0) {
    return undefined;
  }
  return { path: value, source: "setting" };
}
