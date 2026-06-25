import {
  planRobotCommand,
  robotRuntimeListenerArgument,
  normalizePath,
  RobotRuntimeBridge,
  RobotDebugAdapterRuntime,
} from "../../src/infrastructure/debugAdapterRuntime";
import type { RobotLaunchConfiguration } from "../../src/domain/models";

const BASE_CONFIG: RobotLaunchConfiguration = {
  type: "robot-lsp",
  request: "launch",
  name: "Test",
  target: "/workspace/suite.robot",
  cwd: "/workspace",
  args: [],
  env: {},
  variables: {},
  python: "",
  pythonPath: [],
  terminal: "integrated",
  makeSuite: true,
  noDebug: false,
};

describe("robotRuntimeListenerArgument", () => {
  it("formats listener argument with port and token", () => {
    expect(robotRuntimeListenerArgument({ port: 4444, token: "abc123" })).toBe(
      "robot_lsp.debug.listener.RobotLspDebugListener:4444:abc123",
    );
  });

  it("uses exact port and token values", () => {
    expect(robotRuntimeListenerArgument({ port: 0, token: "x" })).toBe(
      "robot_lsp.debug.listener.RobotLspDebugListener:0:x",
    );
  });
});

describe("planRobotCommand", () => {
  it("uses python3 or python depending on platform", () => {
    const plan = planRobotCommand(BASE_CONFIG);
    expect(["python", "python3"]).toContain(plan.command);
  });

  it("uses explicit python when set", () => {
    const config = { ...BASE_CONFIG, python: "/usr/bin/python3.11" };
    const plan = planRobotCommand(config);
    expect(plan.command).toBe("/usr/bin/python3.11");
  });

  it("includes -m robot in args without bridge", () => {
    const plan = planRobotCommand(BASE_CONFIG);
    expect(plan.args.slice(0, 2)).toEqual(["-m", "robot"]);
  });

  it("includes listener arg when runtimeBridge is provided", () => {
    const plan = planRobotCommand(BASE_CONFIG, { port: 9000, token: "tok" });
    expect(plan.args).toContain("--listener");
    expect(plan.args).toContain("robot_lsp.debug.listener.RobotLspDebugListener:9000:tok");
  });

  it("includes debugpy args before -m robot when debugpyPort is set", () => {
    const plan = planRobotCommand(BASE_CONFIG, undefined, 5678);
    expect(plan.args[0]).toBe("-m");
    expect(plan.args[1]).toBe("debugpy");
    expect(plan.args).toContain("--listen");
    expect(plan.args).toContain("--wait-for-client");
    expect(plan.args).toContain("-m");
    expect(plan.args).toContain("robot");
  });

  it("includes pythonPath entries as --pythonpath args", () => {
    const config = { ...BASE_CONFIG, pythonPath: ["/lib/mylib", "/lib/other"] };
    const plan = planRobotCommand(config);
    expect(plan.args).toContain("--pythonpath");
    expect(plan.args).toContain("/lib/mylib");
    expect(plan.args).toContain("/lib/other");
  });

  it("includes variables as --variable args", () => {
    const config = { ...BASE_CONFIG, variables: { FOO: "bar", X: "1" } };
    const plan = planRobotCommand(config);
    expect(plan.args).toContain("--variable");
    expect(plan.args).toContain("FOO:bar");
  });

  it("appends extra args", () => {
    const config = { ...BASE_CONFIG, args: ["--dryrun", "--loglevel", "DEBUG"] };
    const plan = planRobotCommand(config);
    expect(plan.args).toContain("--dryrun");
    expect(plan.args).toContain("--loglevel");
    expect(plan.args).toContain("DEBUG");
  });

  it("appends single target at end", () => {
    const plan = planRobotCommand(BASE_CONFIG);
    expect(plan.args[plan.args.length - 1]).toBe("/workspace/suite.robot");
  });

  it("appends multiple targets", () => {
    const config = { ...BASE_CONFIG, target: ["a.robot", "b.robot"] };
    const plan = planRobotCommand(config);
    expect(plan.args.slice(-2)).toEqual(["a.robot", "b.robot"]);
  });

  it("merges env with process.env", () => {
    const config = { ...BASE_CONFIG, env: { MY_VAR: "hello" } };
    const plan = planRobotCommand(config);
    expect(plan.env["MY_VAR"]).toBe("hello");
  });

  it("returns the specified cwd", () => {
    const plan = planRobotCommand(BASE_CONFIG);
    expect(plan.cwd).toBe("/workspace");
  });
});

describe("normalizePath", () => {
  it("returns a string", () => {
    expect(typeof normalizePath("/some/path")).toBe("string");
  });

  it("resolves to absolute path", () => {
    const result = normalizePath("relative/path");
    expect(result.length).toBeGreaterThan("relative/path".length);
  });
});

describe("RobotDebugAdapterRuntime DAP framing", () => {
  it("tryReadMessage returns undefined when buffer is empty", () => {
    const runtime = new RobotDebugAdapterRuntime();
    expect(runtime.tryReadMessage()).toBeUndefined();
  });

  it("tryReadMessage parses a complete DAP message", () => {
    const runtime = new RobotDebugAdapterRuntime();
    const body = JSON.stringify({ seq: 1, type: "request", command: "initialize" });
    const raw = `Content-Length: ${Buffer.byteLength(body, "utf8")}\r\n\r\n${body}`;
    (runtime as unknown as { buffer: Buffer }).buffer = Buffer.from(raw, "utf8");
    const msg = runtime.tryReadMessage();
    expect(msg).toMatchObject({ type: "request", command: "initialize" });
  });

  it("tryReadMessage returns undefined for incomplete message", () => {
    const runtime = new RobotDebugAdapterRuntime();
    (runtime as unknown as { buffer: Buffer }).buffer = Buffer.from(
      "Content-Length: 100\r\n\r\n{}",
      "utf8",
    );
    expect(runtime.tryReadMessage()).toBeUndefined();
  });

  it("handleMessage ignores non-request messages", () => {
    const runtime = new RobotDebugAdapterRuntime();
    const written: string[] = [];
    jest
      .spyOn(process.stdout, "write")
      .mockImplementation((data) => {
        written.push(String(data));
        return true;
      });
    runtime.handleMessage({ type: "event", event: "initialized" } as unknown as { type: string });
    expect(written).toHaveLength(0);
    jest.restoreAllMocks();
  });

  it("handleMessage responds to initialize with capabilities", () => {
    const runtime = new RobotDebugAdapterRuntime();
    const written: Buffer[] = [];
    jest
      .spyOn(process.stdout, "write")
      .mockImplementation((data) => {
        written.push(Buffer.from(String(data), "utf8"));
        return true;
      });
    runtime.handleMessage({ seq: 1, type: "request", command: "initialize" });
    jest.restoreAllMocks();
    // initialize sends two messages (response + initialized event); extract first by Content-Length
    const output = written.map((b) => b.toString("utf8")).join("");
    const headerEnd = output.indexOf("\r\n\r\n");
    const header = output.slice(0, headerEnd);
    const lenMatch = /Content-Length: (\d+)/i.exec(header);
    const len = Number.parseInt(lenMatch?.[1] ?? "0", 10);
    const bodyStart = headerEnd + 4;
    const parsed = JSON.parse(output.slice(bodyStart, bodyStart + len)) as {
      type: string;
      command: string;
      body: { supportsConfigurationDoneRequest: boolean };
    };
    expect(parsed.type).toBe("response");
    expect(parsed.command).toBe("initialize");
    expect(parsed.body.supportsConfigurationDoneRequest).toBe(true);
  });

  it("handleMessage responds to unknown commands with success", () => {
    const runtime = new RobotDebugAdapterRuntime();
    const written: string[] = [];
    jest
      .spyOn(process.stdout, "write")
      .mockImplementation((data) => {
        written.push(String(data));
        return true;
      });
    runtime.handleMessage({ seq: 5, type: "request", command: "unknownCmd" });
    jest.restoreAllMocks();
    expect(written.some((w) => w.includes('"success":true'))).toBe(true);
  });
});

describe("RobotRuntimeBridge", () => {
  it("start() allocates a port and returns an endpoint", async () => {
    const bridge = new RobotRuntimeBridge(() => {});
    const endpoint = await bridge.start();
    expect(endpoint.port).toBeGreaterThan(0);
    expect(typeof endpoint.token).toBe("string");
    bridge.dispose();
  });

  it("step commands do not throw when no client connected", async () => {
    const bridge = new RobotRuntimeBridge(() => {});
    await bridge.start();
    expect(() => bridge.step("next")).not.toThrow();
    expect(() => bridge.step("step_in")).not.toThrow();
    expect(() => bridge.step("step_out")).not.toThrow();
    bridge.dispose();
  });

  it("setBreakpoints does not throw when no client connected", async () => {
    const bridge = new RobotRuntimeBridge(() => {});
    await bridge.start();
    expect(() => bridge.setBreakpoints([{ source: "/a.robot", line: 5 }])).not.toThrow();
    bridge.dispose();
  });
});
