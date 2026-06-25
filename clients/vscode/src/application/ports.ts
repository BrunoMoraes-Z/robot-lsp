import type { PythonExecutable, PythonValidationResult } from "../domain/models";
import type { RobotLspSettings } from "../domain/settings";

export interface Logger {
  info(message: string): void;
  warn(message: string): void;
  error(message: string): void;
}

export interface SettingsReader {
  read(): RobotLspSettings;
}

export interface CommandRegistry {
  register(command: string, handler: () => void | Promise<void>): void;
}

export interface LanguageServerController {
  start(): Promise<void>;
  stop(): Promise<void>;
  restart(): Promise<void>;
}

export interface PythonCandidateProvider {
  candidate(): Promise<PythonExecutable | undefined>;
}

export interface PythonValidator {
  validate(executable: PythonExecutable): Promise<PythonValidationResult>;
}
