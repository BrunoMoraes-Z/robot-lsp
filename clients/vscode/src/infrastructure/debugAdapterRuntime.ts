import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { platform } from "node:process";
import type { RobotLaunchConfiguration } from "../domain/models";

interface DapMessage {
  readonly seq?: number;
  readonly type: string;
  readonly command?: string;
  readonly arguments?: unknown;
}

interface DapRequest extends DapMessage {
  readonly seq: number;
  readonly type: "request";
  readonly command: string;
}

export interface RobotCommandPlan {
  readonly command: string;
  readonly args: readonly string[];
  readonly cwd: string;
  readonly env: Readonly<Record<string, string | undefined>>;
}

export function planRobotCommand(config: RobotLaunchConfiguration): RobotCommandPlan {
  const command = config.python.trim() || (platform === "win32" ? "python" : "python3");
  const args = ["-m", "robot"];

  for (const entry of config.pythonPath) {
    args.push("--pythonpath", entry);
  }
  for (const [name, value] of Object.entries(config.variables)) {
    args.push("--variable", `${name}:${value}`);
  }
  args.push(...config.args);
  if (typeof config.target === "string") {
    args.push(config.target);
  } else {
    args.push(...config.target);
  }

  return {
    command,
    args,
    cwd: config.cwd,
    env: { ...process.env, ...config.env },
  };
}

class RobotDebugAdapterRuntime {
  private buffer = Buffer.alloc(0);
  private sequence = 1;
  private child: ChildProcessWithoutNullStreams | undefined;

  public start(): void {
    process.stdin.on("data", (chunk: Buffer) => this.accept(chunk));
  }

  private accept(chunk: Buffer): void {
    this.buffer = Buffer.concat([this.buffer, chunk]);
    while (true) {
      const parsed = this.tryReadMessage();
      if (parsed === undefined) {
        return;
      }
      this.handleMessage(parsed);
    }
  }

  private tryReadMessage(): DapMessage | undefined {
    const headerEnd = this.buffer.indexOf("\r\n\r\n");
    if (headerEnd < 0) {
      return undefined;
    }

    const header = this.buffer.subarray(0, headerEnd).toString("ascii");
    const lengthMatch = /Content-Length: (\d+)/i.exec(header);
    if (lengthMatch === null) {
      throw new Error("Missing DAP Content-Length header.");
    }

    const contentLength = Number.parseInt(lengthMatch[1] ?? "0", 10);
    const messageStart = headerEnd + 4;
    const messageEnd = messageStart + contentLength;
    if (this.buffer.length < messageEnd) {
      return undefined;
    }

    const payload = this.buffer.subarray(messageStart, messageEnd).toString("utf8");
    this.buffer = this.buffer.subarray(messageEnd);
    return JSON.parse(payload) as DapMessage;
  }

  private handleMessage(message: DapMessage): void {
    if (message.type !== "request") {
      return;
    }

    const request = message as DapRequest;
    switch (request.command) {
      case "initialize":
        this.respond(request, true, {
          supportsConfigurationDoneRequest: false,
          supportsTerminateRequest: true,
        });
        this.event("initialized");
        break;
      case "launch":
        this.launch(request);
        break;
      case "disconnect":
      case "terminate":
        this.child?.kill();
        this.respond(request, true);
        this.event("terminated");
        break;
      default:
        this.respond(request, true);
        break;
    }
  }

  private launch(request: DapRequest): void {
    const config = request.arguments as RobotLaunchConfiguration;
    if (!config.noDebug) {
      this.respond(request, false, undefined, "Robot LSP Debug Adapter MVP only supports noDebug run sessions.");
      this.event("terminated");
      return;
    }

    const plan = planRobotCommand(config);
    this.output(`Running: ${plan.command} ${plan.args.join(" ")}\n`, "console");
    this.child = spawn(plan.command, [...plan.args], {
      cwd: plan.cwd,
      env: plan.env,
    });

    this.child.stdout.on("data", (chunk: Buffer) => this.output(chunk.toString("utf8"), "stdout"));
    this.child.stderr.on("data", (chunk: Buffer) => this.output(chunk.toString("utf8"), "stderr"));
    this.child.on("error", (error) => {
      this.output(`${error.message}\n`, "stderr");
      this.event("terminated");
    });
    this.child.on("close", (code) => {
      this.event("exited", { exitCode: code ?? 0 });
      this.event("terminated");
    });

    this.respond(request, true);
  }

  private respond(request: DapRequest, success: boolean, body?: unknown, message?: string): void {
    this.write({
      seq: this.sequence,
      type: "response",
      request_seq: request.seq,
      success,
      command: request.command,
      message,
      body,
    });
  }

  private event(event: string, body?: unknown): void {
    this.write({
      seq: this.sequence,
      type: "event",
      event,
      body,
    });
  }

  private output(output: string, category: "console" | "stdout" | "stderr"): void {
    this.event("output", { category, output });
  }

  private write(message: object): void {
    const payload = JSON.stringify({ ...message, seq: this.sequence });
    this.sequence += 1;
    process.stdout.write(`Content-Length: ${Buffer.byteLength(payload, "utf8")}\r\n\r\n${payload}`);
  }
}

if (require.main === module) {
  new RobotDebugAdapterRuntime().start();
}
