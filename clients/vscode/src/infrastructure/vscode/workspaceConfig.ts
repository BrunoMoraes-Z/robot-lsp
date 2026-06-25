import * as vscode from "vscode";
import type { LogLevel } from "../../domain/models";
import { defaultRobotLspSettings, type RobotLspSettings } from "../../domain/settings";
import type { SettingsReader } from "../../application/ports";

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
