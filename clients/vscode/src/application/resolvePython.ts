import type { PythonExecutable, ResolvedPython } from "../domain/models";
import type { RobotLspSettings } from "../domain/settings";
import type { Logger, PythonCandidateProvider, PythonValidator } from "./ports";

export function configuredLanguageServerPython(settings: RobotLspSettings): PythonExecutable | undefined {
  const value = settings.languageServer.python.trim();
  if (value.length === 0) {
    return undefined;
  }
  return { path: value, source: "setting" };
}

export interface ResolveLanguageServerPythonDependencies {
  readonly logger: Logger;
  readonly pythonExtension: PythonCandidateProvider;
  readonly workspace: PythonCandidateProvider;
  readonly pathFallback: PythonCandidateProvider;
  readonly validator: PythonValidator;
}

export async function resolveLanguageServerPython(
  settings: RobotLspSettings,
  dependencies: ResolveLanguageServerPythonDependencies,
): Promise<ResolvedPython> {
  const candidates = [
    configuredLanguageServerPython(settings),
    await dependencies.pythonExtension.candidate(),
    await dependencies.workspace.candidate(),
    await dependencies.pathFallback.candidate(),
  ].filter((candidate): candidate is PythonExecutable => candidate !== undefined);

  const failures: string[] = [];
  for (const candidate of candidates) {
    const result = await dependencies.validator.validate(candidate);
    if (result.ok) {
      dependencies.logger.info(`Resolved Python from ${candidate.source}: ${candidate.path}`);
      return {
        executable: candidate,
        version: result.version,
        robotFrameworkVersion: result.robotFrameworkVersion,
      };
    }
    failures.push(`${candidate.source} (${candidate.path}): ${result.error ?? "validation failed"}`);
  }

  throw new Error(
    [
      "Unable to resolve a Python interpreter that can run robot_lsp and robotframework>=7.0.",
      ...failures,
    ].join("\n"),
  );
}
