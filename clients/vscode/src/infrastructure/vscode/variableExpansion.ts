export function expandWorkspaceFolder(value: string, workspaceFolder: string | undefined): string {
  if (workspaceFolder === undefined) {
    return value;
  }
  return value.replaceAll("${workspaceFolder}", workspaceFolder);
}
