export interface DebugAdapterRegistration {
  dispose(): void;
}

export class DeferredDebugAdapterRegistration implements DebugAdapterRegistration {
  public dispose(): void {
    return undefined;
  }
}
