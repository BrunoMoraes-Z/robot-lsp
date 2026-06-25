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
