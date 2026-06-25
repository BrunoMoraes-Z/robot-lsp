import * as vscode from "vscode";
import { LanguageClient, type LanguageClientOptions, type ServerOptions } from "vscode-languageclient/node";
import { planServerCommand } from "../../application/buildServerOptions";
import { robotDocumentSelector } from "../../application/buildClientOptions";
import type { LanguageServerController, Logger, PythonCandidateProvider, PythonValidator, SettingsReader } from "../../application/ports";
import { resolveLanguageServerPython } from "../../application/resolvePython";

export class RobotLanguageClientAdapter implements LanguageServerController {
  private client: LanguageClient | undefined;

  public constructor(
    private readonly settings: SettingsReader,
    private readonly logger: Logger,
    private readonly outputChannel: vscode.LogOutputChannel,
    private readonly pythonExtension: PythonCandidateProvider,
    private readonly workspacePython: PythonCandidateProvider,
    private readonly pathPython: PythonCandidateProvider,
    private readonly pythonValidator: PythonValidator,
  ) {}

  public async start(): Promise<void> {
    if (this.client !== undefined) {
      this.logger.info("Robot LSP language client is already running.");
      return;
    }

    const settings = this.settings.read();
    const planned = await this.planStartup(settings);

    const serverOptions: ServerOptions = {
      command: planned.command,
      args: [...planned.args],
      options: {
        cwd: planned.cwd,
        env: { ...process.env, ...planned.env },
      },
    };

    const clientOptions: LanguageClientOptions = {
      documentSelector: [...robotDocumentSelector],
      initializationOptions: planned.initializationOptions,
      outputChannel: this.outputChannel,
      synchronize: {
        configurationSection: "robot-lsp",
      },
    };

    this.client = new LanguageClient("robot-lsp", "Robot LSP", serverOptions, clientOptions);
    await this.client.start();
    this.logger.info("Robot LSP language client started.");
  }

  private async planStartup(settings: ReturnType<SettingsReader["read"]>) {
    try {
      const fallbackPython = settings.languageServer.command.trim().length > 0
        ? process.platform === "win32" ? "python" : "python3"
        : (await resolveLanguageServerPython(settings, {
            logger: this.logger,
            pythonExtension: this.pythonExtension,
            workspace: this.workspacePython,
            pathFallback: this.pathPython,
            validator: this.pythonValidator,
          })).executable.path;
      const planned = planServerCommand(settings, fallbackPython);
      this.logger.info(`Starting Robot LSP server: ${planned.command} ${planned.args.join(" ")}`);
      return planned;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown Python resolution error";
      this.logger.error(message);
      void vscode.window.showErrorMessage(
        "Robot LSP could not start. Configure robot-lsp.languageServer.python or install robot-lsp and robotframework>=7.0 in the selected Python environment.",
      );
      throw error;
    }
  }

  public async stop(): Promise<void> {
    const client = this.client;
    this.client = undefined;
    if (client === undefined) {
      return;
    }
    await client.stop();
    this.logger.info("Robot LSP language client stopped.");
  }

  public async restart(): Promise<void> {
    await this.stop();
    await this.start();
  }
}
