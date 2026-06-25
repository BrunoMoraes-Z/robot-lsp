export interface ClientDiagnostic {
  readonly message: string;
  readonly detail?: string;
  readonly source: "activation" | "configuration" | "python" | "languageClient";
}
