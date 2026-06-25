import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { createServer, type Server, type Socket, createConnection } from "node:net";
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

export function normalizePath(value: string): string {
  const normalized = path.resolve(path.normalize(value));
  return platform === "win32" ? normalized.toLowerCase() : normalized;
}

export function planRobotCommand(
  config: RobotLaunchConfiguration,
  runtimeBridge: RobotRuntimeBridgeEndpoint | undefined = undefined,
  debugpyPort: number | undefined = undefined,
): RobotCommandPlan {
  const command = config.python.trim() || (platform === "win32" ? "python" : "python3");
  const args: string[] = [];

  if (debugpyPort !== undefined) {
    args.push("-m", "debugpy", "--listen", `127.0.0.1:${debugpyPort}`, "--wait-for-client", "-m", "robot");
  } else {
    args.push("-m", "robot");
  }

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

function allocatePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const srv = createServer();
    srv.listen(0, "127.0.0.1", () => {
      const addr = srv.address();
      if (addr === null || typeof addr === "string") {
        reject(new Error("Could not allocate port"));
        return;
      }
      const { port } = addr;
      srv.close(() => resolve(port));
    });
    srv.once("error", reject);
  });
}

export class RobotDebugAdapterRuntime {
  private buffer = Buffer.alloc(0);
  private sequence = 1;
  private child: ChildProcessWithoutNullStreams | undefined;
  private runtimeBridge: RobotRuntimeBridge | undefined;
  private debugpyBridge: DebugpyBridge | undefined;
  private readonly breakpoints = new Map<string, SourceBreakpoint[]>();
  private readonly robotBreakpoints = new Map<string, RuntimeBreakpoint[]>();
  private pausedFrame: PausedPayload | undefined;
  private debugpyPausedThreadId: number | undefined;
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

  public tryReadMessage(): DapMessage | undefined {
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

  public handleMessage(message: DapMessage): void {
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
        void this.setBreakpoints(request);
        break;
      case "configurationDone":
        this.respond(request, true);
        break;
      case "launch":
        void this.launch(request);
        break;
      case "threads":
        this.threads(request);
        break;
      case "stackTrace":
        void this.stackTrace(request);
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
        void this.continueExecution(request);
        break;
      case "next":
        void this.step(request, "next");
        break;
      case "stepIn":
        void this.step(request, "step_in");
        break;
      case "stepOut":
        void this.step(request, "step_out");
        break;
      case "disconnect":
      case "terminate":
        this.child?.kill();
        this.runtimeBridge?.dispose();
        this.debugpyBridge?.dispose();
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
    this.runtimeBridge.setBreakpoints(this.allRobotBreakpoints());

    let debugpyPort: number | undefined;
    if (!config.noDebug) {
      try {
        debugpyPort = await allocatePort();
        this.debugpyBridge = new DebugpyBridge((threadId, reason) => {
          this.debugpyPausedThreadId = threadId;
          this.event("stopped", { reason, threadId, allThreadsStopped: false });
        });
      } catch {
        debugpyPort = undefined;
        this.debugpyBridge = undefined;
      }
    }

    const plan = planRobotCommand(config, endpoint, debugpyPort);
    this.output(`Running: ${plan.command} ${plan.args.join(" ")}\n`, "console");
    this.child = spawn(plan.command, [...plan.args], {
      cwd: plan.cwd,
      env: plan.env as NodeJS.ProcessEnv,
    });

    this.child.stdout.on("data", (chunk: Buffer) => this.output(chunk.toString("utf8"), "stdout"));
    this.child.stderr.on("data", (chunk: Buffer) => this.output(chunk.toString("utf8"), "stderr"));
    this.child.on("error", (error) => {
      this.output(`${error.message}\n`, "stderr");
      this.runtimeBridge?.dispose();
      this.debugpyBridge?.dispose();
      this.event("terminated");
    });
    this.child.on("close", (code) => {
      this.runtimeBridge?.dispose();
      this.debugpyBridge?.dispose();
      this.event("exited", { exitCode: code ?? 0 });
      this.event("terminated");
    });

    if (this.debugpyBridge !== undefined && debugpyPort !== undefined) {
      try {
        await this.debugpyBridge.connect(debugpyPort);
        await this.sendPythonBreakpoints();
        await this.debugpyBridge.configurationDone();
      } catch (error) {
        this.output(`debugpy connection failed: ${String(error)}\n`, "stderr");
        this.debugpyBridge = undefined;
      }
    }

    this.respond(request, true);
  }

  private async setBreakpoints(request: DapRequest): Promise<void> {
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
    this.breakpoints.set(normalized, [...requested]);

    if (sourcePath.endsWith(".py")) {
      if (this.debugpyBridge !== undefined) {
        await this.debugpyBridge.setBreakpoints(sourcePath, requested);
      }
      this.respond(request, true, {
        breakpoints: requested.map((bp) => ({
          verified: this.debugpyBridge !== undefined,
          source: { path: sourcePath },
          line: bp.line,
        })),
      });
      return;
    }

    const runtimeBreakpoints = requested.map((bp) => ({ source: normalized, line: bp.line }));
    this.robotBreakpoints.set(normalized, runtimeBreakpoints);
    this.runtimeBridge?.setBreakpoints(this.allRobotBreakpoints());
    this.respond(request, true, {
      breakpoints: runtimeBreakpoints.map((bp) => ({
        verified: true,
        source: { path: sourcePath },
        line: bp.line,
      })),
    });
  }

  private async sendPythonBreakpoints(): Promise<void> {
    for (const [normalized, bps] of this.breakpoints) {
      if (normalized.endsWith(".py")) {
        await this.debugpyBridge?.setBreakpoints(normalized, bps);
      }
    }
  }

  private threads(request: DapRequest): void {
    const threads: Array<{ id: number; name: string }> = [{ id: 1, name: "Robot Framework" }];
    if (this.debugpyBridge !== undefined) {
      threads.push({ id: 2, name: "Python (debugpy)" });
    }
    this.respond(request, true, { threads });
  }

  private async stackTrace(request: DapRequest): Promise<void> {
    const args = request.arguments as { readonly threadId?: number };
    if (args.threadId === 2 && this.debugpyBridge !== undefined) {
      const result = await this.debugpyBridge.stackTrace(this.debugpyPausedThreadId ?? 1);
      this.respond(request, true, result);
      return;
    }

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

  private async continueExecution(request: DapRequest): Promise<void> {
    const args = request.arguments as { readonly threadId?: number };
    if (args.threadId === 2 && this.debugpyBridge !== undefined && this.debugpyPausedThreadId !== undefined) {
      const tid = this.debugpyPausedThreadId;
      this.debugpyPausedThreadId = undefined;
      await this.debugpyBridge.continue(tid);
      this.respond(request, true, { allThreadsContinued: false });
      this.event("continued", { threadId: 2, allThreadsContinued: false });
      return;
    }
    this.pausedFrame = undefined;
    this.runtimeBridge?.continue();
    this.respond(request, true, { allThreadsContinued: true });
    this.event("continued", { threadId: 1, allThreadsContinued: true });
  }

  private async step(request: DapRequest, mode: "next" | "step_in" | "step_out"): Promise<void> {
    const args = request.arguments as { readonly threadId?: number };
    if (args.threadId === 2 && this.debugpyBridge !== undefined && this.debugpyPausedThreadId !== undefined) {
      const tid = this.debugpyPausedThreadId;
      this.debugpyPausedThreadId = undefined;
      if (mode === "next") {
        await this.debugpyBridge.next(tid);
      } else if (mode === "step_in") {
        await this.debugpyBridge.stepIn(tid);
      } else {
        await this.debugpyBridge.stepOut(tid);
      }
      this.respond(request, true);
      this.event("continued", { threadId: 2, allThreadsContinued: false });
      return;
    }
    this.pausedFrame = undefined;
    this.runtimeBridge?.step(mode);
    this.respond(request, true);
    this.event("continued", { threadId: 1, allThreadsContinued: false });
  }

  private acceptRuntimeEvent(event: RuntimeEventMessage): void {
    this.output(`Robot event: ${JSON.stringify(event)}\n`, "console");
    if (event.event === "listener_started") {
      this.runtimeBridge?.setBreakpoints(this.allRobotBreakpoints());
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

  private allRobotBreakpoints(): readonly RuntimeBreakpoint[] {
    return [...this.robotBreakpoints.values()].flat();
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

export class RobotRuntimeBridge {
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

  public step(mode: "next" | "step_in" | "step_out"): void {
    this.command({ command: mode });
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

interface DebugpyStoppedCallback {
  (threadId: number, reason: string): void;
}

export class DebugpyBridge {
  private socket: Socket | undefined;
  private dapBuffer = Buffer.alloc(0);
  private dapSequence = 1;
  private readonly pendingRequests = new Map<number, (body: unknown) => void>();

  public constructor(private readonly onStopped: DebugpyStoppedCallback) {}

  public async connect(port: number): Promise<void> {
    const socket = await new Promise<Socket>((resolve, reject) => {
      const sock = createConnection({ host: "127.0.0.1", port }, () => resolve(sock));
      sock.once("error", reject);
    });
    this.socket = socket;
    socket.on("data", (chunk: Buffer) => this.acceptDapData(chunk));

    await this.dapRequest("initialize", {
      adapterID: "robot-lsp-debugpy",
      linesStartAt1: true,
      columnsStartAt1: true,
      pathFormat: "path",
    });
    await this.dapRequest("attach", { connect: { host: "127.0.0.1", port } });
  }

  public async configurationDone(): Promise<void> {
    await this.dapRequest("configurationDone", {});
  }

  public async setBreakpoints(source: string, breakpoints: readonly SourceBreakpoint[]): Promise<void> {
    await this.dapRequest("setBreakpoints", {
      source: { path: source },
      breakpoints: breakpoints.map((bp) => ({ line: bp.line })),
    });
  }

  public async stackTrace(threadId: number): Promise<unknown> {
    return this.dapRequest("stackTrace", { threadId, startFrame: 0, levels: 20 });
  }

  public async next(threadId: number): Promise<void> {
    await this.dapRequest("next", { threadId });
  }

  public async stepIn(threadId: number): Promise<void> {
    await this.dapRequest("stepIn", { threadId });
  }

  public async stepOut(threadId: number): Promise<void> {
    await this.dapRequest("stepOut", { threadId });
  }

  public async continue(threadId: number): Promise<void> {
    await this.dapRequest("continue", { threadId });
  }

  public dispose(): void {
    this.socket?.destroy();
    this.socket = undefined;
  }

  private acceptDapData(chunk: Buffer): void {
    this.dapBuffer = Buffer.concat([this.dapBuffer, chunk]);
    while (true) {
      const msg = this.tryReadDap();
      if (msg === undefined) return;
      this.dispatchDap(msg);
    }
  }

  private tryReadDap(): Record<string, unknown> | undefined {
    const sep = this.dapBuffer.indexOf("\r\n\r\n");
    if (sep < 0) return undefined;
    const header = this.dapBuffer.subarray(0, sep).toString("ascii");
    const match = /Content-Length: (\d+)/i.exec(header);
    if (!match) return undefined;
    const len = Number.parseInt(match[1] ?? "0", 10);
    const start = sep + 4;
    if (this.dapBuffer.length < start + len) return undefined;
    const body = JSON.parse(this.dapBuffer.subarray(start, start + len).toString("utf8")) as Record<string, unknown>;
    this.dapBuffer = this.dapBuffer.subarray(start + len);
    return body;
  }

  private dispatchDap(msg: Record<string, unknown>): void {
    if (msg["type"] === "response") {
      const seq = msg["request_seq"];
      if (typeof seq === "number") {
        const cb = this.pendingRequests.get(seq);
        if (cb !== undefined) {
          this.pendingRequests.delete(seq);
          cb(msg["body"]);
        }
      }
      return;
    }
    if (msg["type"] === "event" && msg["event"] === "stopped") {
      const body = msg["body"] as { threadId?: number; reason?: string } | undefined;
      this.onStopped(body?.threadId ?? 1, body?.reason ?? "breakpoint");
    }
  }

  private dapRequest(command: string, args: object): Promise<unknown> {
    return new Promise((resolve) => {
      const seq = this.dapSequence;
      this.dapSequence += 1;
      this.pendingRequests.set(seq, resolve);
      const msg = JSON.stringify({ seq, type: "request", command, arguments: args });
      this.socket?.write(`Content-Length: ${Buffer.byteLength(msg, "utf8")}\r\n\r\n${msg}`);
    });
  }
}

if (require.main === module) {
  new RobotDebugAdapterRuntime().start();
}
