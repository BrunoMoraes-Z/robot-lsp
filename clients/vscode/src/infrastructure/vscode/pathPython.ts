import type { PythonExecutable } from "../../domain/models";
import type { PythonCandidateProvider } from "../../application/ports";

export class PathPythonProvider implements PythonCandidateProvider {
  public async candidate(): Promise<PythonExecutable> {
    return {
      path: process.platform === "win32" ? "python" : "python3",
      source: "path",
    };
  }
}
