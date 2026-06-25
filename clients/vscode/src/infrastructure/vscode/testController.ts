export interface TestControllerAdapter {
  dispose(): void;
}

export class DeferredTestControllerAdapter implements TestControllerAdapter {
  public dispose(): void {
    return undefined;
  }
}
