export interface StatusBarController {
  dispose(): void;
}

export class DeferredStatusBarController implements StatusBarController {
  public dispose(): void {
    return undefined;
  }
}
