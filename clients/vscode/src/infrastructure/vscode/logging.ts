import * as vscode from "vscode";
import type { Logger } from "../../application/ports";

export class OutputChannelLogger implements Logger {
  public constructor(private readonly channel: vscode.OutputChannel) {}

  public info(message: string): void {
    this.channel.appendLine(`[info] ${message}`);
  }

  public warn(message: string): void {
    this.channel.appendLine(`[warning] ${message}`);
  }

  public error(message: string): void {
    this.channel.appendLine(`[error] ${message}`);
  }
}
