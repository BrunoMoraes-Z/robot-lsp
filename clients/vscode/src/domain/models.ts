export type LogLevel = "debug" | "info" | "warning" | "error";

export interface PythonExecutable {
  readonly path: string;
  readonly source: "setting" | "pythonExtension" | "workspace" | "path";
}

export interface ResolvedPython {
  readonly executable: PythonExecutable;
  readonly version?: string;
  readonly robotFrameworkVersion?: string;
}

export interface PythonValidationResult {
  readonly ok: boolean;
  readonly version?: string;
  readonly robotFrameworkVersion?: string;
  readonly error?: string;
}

export interface LaunchTarget {
  readonly target: string | readonly string[];
  readonly cwd: string;
  readonly testName?: string;
}

export interface RobotLaunchConfiguration {
  readonly type: "robot-lsp";
  readonly request: "launch";
  readonly name: string;
  readonly target: string | readonly string[];
  readonly cwd: string;
  readonly args: readonly string[];
  readonly env: Readonly<Record<string, string>>;
  readonly variables: Readonly<Record<string, string>>;
  readonly python: string;
  readonly pythonPath: readonly string[];
  readonly terminal: "integrated";
  readonly makeSuite: boolean;
  readonly noDebug: boolean;
}

export interface RobotTestItem {
  readonly id: string;
  readonly name: string;
  readonly uri: string;
  readonly line: number;
}
