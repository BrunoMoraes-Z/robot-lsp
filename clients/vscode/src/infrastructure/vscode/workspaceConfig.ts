import * as vscode from "vscode";
import { serverRobotLspConfiguration, type ServerRobotLspConfiguration } from "../../application/configurationBridge";
import type { LogLevel } from "../../domain/models";
import { defaultRobotLspSettings, type RobotLspSettings } from "../../domain/settings";
import type { SettingsReader } from "../../application/ports";
import { expandStringRecord, expandWorkspaceFolder } from "./variableExpansion";

export class VsCodeSettingsReader implements SettingsReader {
  public read(): RobotLspSettings {
    const config = vscode.workspace.getConfiguration("robot-lsp");
    return {
      languageServer: {
        python: config.get("languageServer.python", defaultRobotLspSettings.languageServer.python),
        command: config.get("languageServer.command", defaultRobotLspSettings.languageServer.command),
        args: config.get("languageServer.args", [...defaultRobotLspSettings.languageServer.args]),
        cwd: config.get("languageServer.cwd", defaultRobotLspSettings.languageServer.cwd),
        env: config.get("languageServer.env", defaultRobotLspSettings.languageServer.env),
      },
      runtime: {
        python: config.get("runtime.python", defaultRobotLspSettings.runtime.python),
        env: config.get("runtime.env", defaultRobotLspSettings.runtime.env),
        pythonPath: config.get("runtime.pythonPath", [...defaultRobotLspSettings.runtime.pythonPath]),
      },
      variables: config.get("variables", defaultRobotLspSettings.variables),
      diagnosticsEnable: config.get("diagnostics.enable", defaultRobotLspSettings.diagnosticsEnable),
      completionSnippets: config.get("completion.snippets", defaultRobotLspSettings.completionSnippets),
      logLevel: config.get("logLevel", defaultRobotLspSettings.logLevel) as LogLevel,
      testExplorerEnabled: config.get("testExplorer.enabled", defaultRobotLspSettings.testExplorerEnabled),
      debug: {
        allowKeywordEvaluate: config.get(
          "debug.allowKeywordEvaluate",
          defaultRobotLspSettings.debug.allowKeywordEvaluate,
        ),
        breakOnFailure: config.get("debug.breakOnFailure", defaultRobotLspSettings.debug.breakOnFailure),
        breakOnError: config.get("debug.breakOnError", defaultRobotLspSettings.debug.breakOnError),
      },
    };
  }
}

export class VsCodeConfigurationBridge {
  public constructor(private readonly settings: SettingsReader) {}

  public robotLspConfiguration(scopeUri: string | undefined): ServerRobotLspConfiguration {
    const workspaceFolder = workspaceFolderPath(scopeUri);
    const settings = expandSettings(this.settings.read(), workspaceFolder);
    return serverRobotLspConfiguration(settings);
  }
}

function expandSettings(settings: RobotLspSettings, workspaceFolder: string | undefined): RobotLspSettings {
  return {
    ...settings,
    languageServer: {
      ...settings.languageServer,
      python: expandWorkspaceFolder(settings.languageServer.python, workspaceFolder),
      command: expandWorkspaceFolder(settings.languageServer.command, workspaceFolder),
      cwd: expandWorkspaceFolder(settings.languageServer.cwd, workspaceFolder),
      args: settings.languageServer.args.map((item) => expandWorkspaceFolder(item, workspaceFolder)),
      env: expandStringRecord(settings.languageServer.env, workspaceFolder),
    },
    runtime: {
      ...settings.runtime,
      python: expandWorkspaceFolder(settings.runtime.python, workspaceFolder),
      env: expandStringRecord(settings.runtime.env, workspaceFolder),
      pythonPath: settings.runtime.pythonPath.map((item) => expandWorkspaceFolder(item, workspaceFolder)),
    },
    variables: expandStringRecord(settings.variables, workspaceFolder),
  };
}

function workspaceFolderPath(scopeUri: string | undefined): string | undefined {
  if (scopeUri !== undefined) {
    const folder = vscode.workspace.getWorkspaceFolder(vscode.Uri.parse(scopeUri));
    if (folder !== undefined) {
      return folder.uri.fsPath;
    }
  }
  return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
}
