import * as vscode from "vscode";
import { LanguageClient, type LanguageClientOptions, type ServerOptions } from "vscode-languageclient/node";
import { planServerCommand } from "../../application/buildServerOptions";
import { robotDocumentSelector } from "../../application/buildClientOptions";
import type { LanguageServerController, Logger, SettingsReader } from "../../application/ports";

const fallbackPython = process.platform === "win32" ? "python" : "python3";

export class RobotLanguageClientAdapter implements LanguageServerController {
  private client: LanguageClient | undefined;

  public constructor(
    private readonly settings: SettingsReader,
    private readonly logger: Logger,
    private readonly outputChannel: vscode.LogOutputChannel,
  ) {}

  public async start(): Promise<void> {
    if (this.client !== undefined) {
      this.logger.info("Robot LSP language client is already running.");
      return;
    }

    const settings = this.settings.read();
    const planned = planServerCommand(settings, fallbackPython);
    this.logger.info(`Starting Robot LSP server: ${planned.command} ${planned.args.join(" ")}`);

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
