import type { LaunchTarget, RobotLaunchConfiguration } from "../domain/models";
import type { RobotLspSettings } from "../domain/settings";

export function normalizeLaunchTarget(target: LaunchTarget): LaunchTarget {
  return {
    target: Array.isArray(target.target) ? [...target.target] : target.target,
    cwd: target.cwd,
    testName: target.testName?.trim() || undefined,
  };
}

export function buildRunLaunchConfiguration(
  settings: RobotLspSettings,
  target: LaunchTarget,
): RobotLaunchConfiguration {
  const normalized = normalizeLaunchTarget(target);
  const args = normalized.testName === undefined ? [] : ["--test", normalized.testName];

  return {
    type: "robot-lsp",
    request: "launch",
    name: normalized.testName === undefined ? "Robot Framework: Current File" : `Robot Framework: ${normalized.testName}`,
    target: normalized.target,
    cwd: normalized.cwd,
    args,
    env: settings.runtime.env,
    variables: settings.variables,
    python: settings.runtime.python,
    pythonPath: settings.runtime.pythonPath,
    terminal: "integrated",
    makeSuite: true,
    noDebug: true,
  };
}

export function buildDebugLaunchConfiguration(
  settings: RobotLspSettings,
  target: LaunchTarget,
): RobotLaunchConfiguration {
  return {
    ...buildRunLaunchConfiguration(settings, target),
    name: target.testName === undefined ? "Robot Framework: Debug Current File" : `Robot Framework: Debug ${target.testName}`,
    noDebug: false,
  };
}
