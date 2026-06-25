import * as vscode from "vscode";
import type { CommandRegistry } from "../../application/ports";

export class VsCodeCommandRegistry implements CommandRegistry {
  public constructor(private readonly subscriptions: vscode.Disposable[]) {}

  public register(command: string, handler: () => void | Promise<void>): void {
    this.subscriptions.push(vscode.commands.registerCommand(command, handler));
  }
}
