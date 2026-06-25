import type { LogLevel } from "./models";

export interface ProcessSettings {
  readonly python: string;
  readonly command: string;
  readonly args: readonly string[];
  readonly cwd: string;
  readonly env: Readonly<Record<string, string>>;
}

export interface RuntimeSettings {
  readonly python: string;
  readonly env: Readonly<Record<string, string>>;
  readonly pythonPath: readonly string[];
}

export interface DebugSettings {
  readonly allowKeywordEvaluate: boolean;
  readonly breakOnFailure: boolean;
  readonly breakOnError: boolean;
}

export interface RobotLspSettings {
  readonly languageServer: ProcessSettings;
  readonly runtime: RuntimeSettings;
  readonly variables: Readonly<Record<string, string>>;
  readonly diagnosticsEnable: boolean;
  readonly completionSnippets: boolean;
  readonly logLevel: LogLevel;
  readonly testExplorerEnabled: boolean;
  readonly debug: DebugSettings;
}

export const defaultRobotLspSettings: RobotLspSettings = {
  languageServer: {
    python: "",
    command: "",
    args: [],
    cwd: "",
    env: {},
  },
  runtime: {
    python: "",
    env: {},
    pythonPath: [],
  },
  variables: {},
  diagnosticsEnable: true,
  completionSnippets: true,
  logLevel: "warning",
  testExplorerEnabled: true,
  debug: {
    allowKeywordEvaluate: false,
    breakOnFailure: true,
    breakOnError: true,
  },
};
