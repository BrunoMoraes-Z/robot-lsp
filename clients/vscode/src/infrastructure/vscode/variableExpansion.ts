export function expandWorkspaceFolder(value: string, workspaceFolder: string | undefined): string {
  if (workspaceFolder === undefined) {
    return value;
  }
  return value.replaceAll("${workspaceFolder}", workspaceFolder);
}

export function expandStringRecord(
  values: Readonly<Record<string, string>>,
  workspaceFolder: string | undefined,
): Readonly<Record<string, string>> {
  return Object.fromEntries(
    Object.entries(values).map(([key, value]) => [key, expandWorkspaceFolder(value, workspaceFolder)]),
  );
}
