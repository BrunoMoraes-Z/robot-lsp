import type { PythonExecutable } from "../../domain/models";

export interface PythonExtensionAdapter {
  selectedInterpreter(): Promise<PythonExecutable | undefined>;
}

export class NoopPythonExtensionAdapter implements PythonExtensionAdapter {
  public async selectedInterpreter(): Promise<PythonExecutable | undefined> {
    return undefined;
  }
}
