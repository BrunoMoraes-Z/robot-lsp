export interface LanguageClientAdapter {
  start(): Promise<void>;
  stop(): Promise<void>;
}

export class DeferredLanguageClientAdapter implements LanguageClientAdapter {
  public async start(): Promise<void> {
    return Promise.resolve();
  }

  public async stop(): Promise<void> {
    return Promise.resolve();
  }
}
