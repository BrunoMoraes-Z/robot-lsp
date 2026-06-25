import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { createServer, type Server, type Socket } from "node:net";
import path from "node:path";
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

interface SourceBreakpoint {
  readonly line: number;
}

interface RuntimeBreakpoint {
  readonly source: string;
  readonly line: number;
}

interface RuntimeEventMessage {
  readonly event: string;
  readonly payload?: unknown;
}

interface PausedPayload {
  readonly reason?: string;
  readonly source?: string;
  readonly line?: number;
  readonly name?: string;
}

interface EvaluateResponsePayload {
  readonly requestId?: unknown;
  readonly success?: boolean;
  readonly result?: string;
  readonly message?: string;
}

export interface RobotCommandPlan {
  readonly command: string;
  readonly args: readonly string[];
  readonly cwd: string;
  readonly env: Readonly<Record<string, string | undefined>>;
}

export interface RobotRuntimeBridgeEndpoint {
  readonly port: number;
  readonly token: string;
}

export function robotRuntimeListenerArgument(endpoint: RobotRuntimeBridgeEndpoint): string {
  return `robot_lsp.debug.listener.RobotLspDebugListener:${endpoint.port}:${endpoint.token}`;
}

export function planRobotCommand(
  config: RobotLaunchConfiguration,
  runtimeBridge: RobotRuntimeBridgeEndpoint | undefined = undefined,
): RobotCommandPlan {
  const command = config.python.trim() || (platform === "win32" ? "python" : "python3");
  const args = ["-m", "robot"];

  if (runtimeBridge !== undefined) {
    args.push("--listener", robotRuntimeListenerArgument(runtimeBridge));
  }
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
  private runtimeBridge: RobotRuntimeBridge | undefined;
  private readonly breakpoints = new Map<string, RuntimeBreakpoint[]>();
  private pausedFrame: PausedPayload | undefined;
  private nextVariablesReference = 1;
  private readonly variableHandles = new Map<number, PausedPayload>();
  private nextEvaluateRequestId = 1;
  private readonly pendingEvaluations = new Map<number, DapRequest>();

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
          supportsConfigurationDoneRequest: true,
          supportsEvaluateForHovers: true,
          supportsTerminateRequest: true,
        });
        this.event("initialized");
        break;
      case "setBreakpoints":
        this.setBreakpoints(request);
        break;
      case "configurationDone":
        this.respond(request, true);
        break;
      case "launch":
        void this.launch(request);
        break;
      case "threads":
        this.respond(request, true, { threads: [{ id: 1, name: "Robot Framework" }] });
        break;
      case "stackTrace":
        this.stackTrace(request);
        break;
      case "scopes":
        this.scopes(request);
        break;
      case "variables":
        this.variables(request);
        break;
      case "evaluate":
        this.evaluate(request);
        break;
      case "continue":
        this.continue(request);
        break;
      case "disconnect":
      case "terminate":
        this.child?.kill();
        this.runtimeBridge?.dispose();
        this.respond(request, true);
        this.event("terminated");
        break;
      default:
        this.respond(request, true);
        break;
    }
  }

  private async launch(request: DapRequest): Promise<void> {
    const config = request.arguments as RobotLaunchConfiguration;
    this.runtimeBridge = new RobotRuntimeBridge((event) => {
      this.acceptRuntimeEvent(event);
    });
    const endpoint = await this.runtimeBridge.start();
    this.runtimeBridge.setBreakpoints(this.allBreakpoints());
    const plan = planRobotCommand(config, endpoint);
    this.output(`Running: ${plan.command} ${plan.args.join(" ")}\n`, "console");
    this.child = spawn(plan.command, [...plan.args], {
      cwd: plan.cwd,
      env: plan.env,
    });

    this.child.stdout.on("data", (chunk: Buffer) => this.output(chunk.toString("utf8"), "stdout"));
    this.child.stderr.on("data", (chunk: Buffer) => this.output(chunk.toString("utf8"), "stderr"));
    this.child.on("error", (error) => {
      this.output(`${error.message}\n`, "stderr");
      this.runtimeBridge?.dispose();
      this.event("terminated");
    });
    this.child.on("close", (code) => {
      this.runtimeBridge?.dispose();
      this.event("exited", { exitCode: code ?? 0 });
      this.event("terminated");
    });

    this.respond(request, true);
  }

  private setBreakpoints(request: DapRequest): void {
    const args = request.arguments as {
      readonly source?: { readonly path?: string };
      readonly breakpoints?: readonly SourceBreakpoint[];
    };
    const sourcePath = args.source?.path;
    const requested = args.breakpoints ?? [];
    if (sourcePath === undefined) {
      this.respond(request, false, undefined, "Breakpoint source path is required.");
      return;
    }

    const normalized = normalizePath(sourcePath);
    const runtimeBreakpoints = requested.map((breakpoint) => ({ source: normalized, line: breakpoint.line }));
    this.breakpoints.set(normalized, runtimeBreakpoints);
    this.runtimeBridge?.setBreakpoints(this.allBreakpoints());
    this.respond(request, true, {
      breakpoints: runtimeBreakpoints.map((breakpoint) => ({
        verified: true,
        source: { path: sourcePath },
        line: breakpoint.line,
      })),
    });
  }

  private stackTrace(request: DapRequest): void {
    const frame = this.pausedFrame;
    if (frame === undefined) {
      this.respond(request, true, { stackFrames: [], totalFrames: 0 });
      return;
    }
    this.respond(request, true, {
      stackFrames: [{
        id: 1,
        name: frame.name ?? "Robot Framework",
        source: frame.source === undefined ? undefined : { path: frame.source },
        line: frame.line ?? 1,
        column: 1,
      }],
      totalFrames: 1,
    });
  }

  private scopes(request: DapRequest): void {
    const frame = this.pausedFrame;
    if (frame === undefined) {
      this.respond(request, true, { scopes: [] });
      return;
    }
    const handle = this.nextVariablesReference;
    this.nextVariablesReference += 1;
    this.variableHandles.set(handle, frame);
    this.respond(request, true, {
      scopes: [{ name: "Robot", variablesReference: handle, expensive: false }],
    });
  }

  private variables(request: DapRequest): void {
    const args = request.arguments as { readonly variablesReference?: number };
    const frame = args.variablesReference === undefined ? undefined : this.variableHandles.get(args.variablesReference);
    this.respond(request, true, {
      variables: frame === undefined ? [] : [
        { name: "source", value: frame.source ?? "", variablesReference: 0 },
        { name: "line", value: String(frame.line ?? 1), variablesReference: 0 },
        { name: "keyword", value: frame.name ?? "", variablesReference: 0 },
      ],
    });
  }

  private evaluate(request: DapRequest): void {
    const args = request.arguments as { readonly expression?: string };
    const expression = args.expression?.trim();
    if (expression === undefined || expression.length === 0) {
      this.respond(request, false, undefined, "Evaluate expression is required.");
      return;
    }
    if (this.pausedFrame === undefined || this.runtimeBridge === undefined) {
      this.respond(request, false, undefined, "Robot execution is not paused.");
      return;
    }

    const requestId = this.nextEvaluateRequestId;
    this.nextEvaluateRequestId += 1;
    this.pendingEvaluations.set(requestId, request);
    this.runtimeBridge.evaluate(requestId, expression);
  }

  private continue(request: DapRequest): void {
    this.pausedFrame = undefined;
    this.runtimeBridge?.continue();
    this.respond(request, true, { allThreadsContinued: true });
    this.event("continued", { threadId: 1, allThreadsContinued: true });
  }

  private acceptRuntimeEvent(event: RuntimeEventMessage): void {
    this.output(`Robot event: ${JSON.stringify(event)}\n`, "console");
    if (event.event === "listener_started") {
      this.runtimeBridge?.setBreakpoints(this.allBreakpoints());
      return;
    }
    if (event.event === "paused") {
      this.pausedFrame = event.payload as PausedPayload;
      this.event("stopped", { reason: this.pausedFrame.reason ?? "breakpoint", threadId: 1, allThreadsStopped: true });
      return;
    }
    if (event.event === "continued") {
      this.pausedFrame = undefined;
      return;
    }
    if (event.event === "evaluate_response") {
      this.acceptEvaluateResponse(event.payload as EvaluateResponsePayload);
    }
  }

  private acceptEvaluateResponse(payload: EvaluateResponsePayload): void {
    if (typeof payload.requestId !== "number") {
      return;
    }
    const request = this.pendingEvaluations.get(payload.requestId);
    if (request === undefined) {
      return;
    }
    this.pendingEvaluations.delete(payload.requestId);
    if (payload.success === false) {
      this.respond(request, false, undefined, payload.message ?? "Evaluate failed.");
      return;
    }
    this.respond(request, true, {
      result: payload.result ?? "None",
      variablesReference: 0,
    });
  }

  private allBreakpoints(): readonly RuntimeBreakpoint[] {
    return [...this.breakpoints.values()].flat();
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

class RobotRuntimeBridge {
  private readonly token = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  private readonly server: Server;
  private sockets: Socket[] = [];

  public constructor(private readonly onEvent: (event: RuntimeEventMessage) => void) {
    this.server = createServer((socket) => this.accept(socket));
  }

  public async start(): Promise<RobotRuntimeBridgeEndpoint> {
    await new Promise<void>((resolve, reject) => {
      this.server.once("error", reject);
      this.server.listen(0, "127.0.0.1", () => {
        this.server.off("error", reject);
        resolve();
      });
    });

    const address = this.server.address();
    if (address === null || typeof address === "string") {
      throw new Error("Unable to allocate Robot runtime listener port.");
    }
    return { port: address.port, token: this.token };
  }

  public dispose(): void {
    for (const socket of this.sockets) {
      socket.destroy();
    }
    this.sockets = [];
    this.server.close();
  }

  public setBreakpoints(breakpoints: readonly RuntimeBreakpoint[]): void {
    this.command({ command: "set_breakpoints", breakpoints });
  }

  public continue(): void {
    this.command({ command: "continue" });
  }

  public evaluate(requestId: number, expression: string): void {
    this.command({ command: "evaluate", requestId, expression });
  }

  private accept(socket: Socket): void {
    this.sockets.push(socket);
    socket.setEncoding("utf8");
    let buffer = "";
    socket.on("data", (chunk: string) => {
      buffer += chunk;
      while (true) {
        const newline = buffer.indexOf("\n");
        if (newline < 0) {
          break;
        }
        const line = buffer.slice(0, newline);
        buffer = buffer.slice(newline + 1);
        this.acceptLine(line);
      }
    });
    socket.on("close", () => {
      this.sockets = this.sockets.filter((item) => item !== socket);
    });
  }

  private acceptLine(line: string): void {
    if (line.trim().length === 0) {
      return;
    }
    const message = JSON.parse(line) as { readonly token?: string; readonly event?: string; readonly payload?: unknown };
    if (message.token !== this.token) {
      return;
    }
    if (typeof message.event === "string") {
      this.onEvent({ event: message.event, payload: message.payload });
    }
  }

  private command(payload: object): void {
    const message = `${JSON.stringify({ token: this.token, ...payload })}\n`;
    for (const socket of this.sockets) {
      socket.write(message);
    }
  }
}

function normalizePath(value: string): string {
  const normalized = path.resolve(path.normalize(value));
  return platform === "win32" ? normalized.toLowerCase() : normalized;
}

if (require.main === module) {
  new RobotDebugAdapterRuntime().start();
}
