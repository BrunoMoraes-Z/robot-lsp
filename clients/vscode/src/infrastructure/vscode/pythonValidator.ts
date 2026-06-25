import { execFile } from "child_process";
import { delimiter } from "node:path";
import type { PythonExecutable, PythonValidationResult } from "../../domain/models";
import type { PythonValidator } from "../../application/ports";

const validationScript = [
  "import json, sys",
  "try:",
  "    import robot",
  "    from robot.version import VERSION",
  "    parts = [int(part) for part in VERSION.split('.')[:2]]",
  "    ok = tuple(parts) >= (7, 0)",
  "    print(json.dumps({'ok': ok, 'python': sys.version.split()[0], 'robot': VERSION, 'error': None if ok else 'Robot Framework >= 7.0 is required'}))",
  "except Exception as exc:",
  "    print(json.dumps({'ok': False, 'python': sys.version.split()[0], 'robot': None, 'error': str(exc)}))",
].join("\n");

export class ProcessPythonValidator implements PythonValidator {
  public constructor(private readonly bundledLibPath: string) {}

  public async validate(executable: PythonExecutable): Promise<PythonValidationResult> {
    const existing = process.env["PYTHONPATH"] ?? "";
    const pythonPath = existing
      ? `${this.bundledLibPath}${delimiter}${existing}`
      : this.bundledLibPath;
    const env = { ...process.env, PYTHONPATH: pythonPath };

    return new Promise((resolve) => {
      execFile(executable.path, ["-c", validationScript], { timeout: 8000, env }, (error, stdout, stderr) => {
        if (error !== null) {
          resolve({ ok: false, error: stderr.trim() || error.message });
          return;
        }

        try {
          const payload = JSON.parse(stdout.trim()) as ValidationPayload;
          resolve({
            ok: payload.ok,
            version: payload.python,
            robotFrameworkVersion: payload.robot ?? undefined,
            error: payload.error ?? undefined,
          });
        } catch (parseError) {
          resolve({ ok: false, error: parseError instanceof Error ? parseError.message : "Invalid validation output" });
        }
      });
    });
  }
}

interface ValidationPayload {
  readonly ok: boolean;
  readonly python?: string;
  readonly robot?: string | null;
  readonly error?: string | null;
}
