import type { RobotLspSettings } from "../domain/settings";

export interface ServerRobotLspConfiguration {
  readonly diagnostics: {
    readonly enable: boolean;
  };
  readonly completion: {
    readonly snippets: boolean;
  };
  readonly logLevel: string;
  readonly variables: Readonly<Record<string, string>>;
}

export function serverRobotLspConfiguration(settings: RobotLspSettings): ServerRobotLspConfiguration {
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
