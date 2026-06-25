export type LogLevel = "debug" | "info" | "warning" | "error";

export interface PythonExecutable {
  readonly path: string;
  readonly source: "setting" | "pythonExtension" | "workspace" | "path";
}

export interface ResolvedPython {
  readonly executable: PythonExecutable;
  readonly version?: string;
}

export interface LaunchTarget {
  readonly target: string | readonly string[];
  readonly cwd: string;
}

export interface RobotTestItem {
  readonly id: string;
  readonly name: string;
  readonly uri: string;
  readonly line: number;
}
