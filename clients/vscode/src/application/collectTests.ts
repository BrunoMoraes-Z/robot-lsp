import type { RobotTestItem } from "../domain/models";

export function emptyTestCollection(): readonly RobotTestItem[] {
  return [];
}

const sectionHeaderPattern = /^\s*\*{2,}\s*([^*]+?)\s*\*{2,}\s*$/;

export function collectRobotTestsFromText(uri: string, text: string): readonly RobotTestItem[] {
  const tests: RobotTestItem[] = [];
  let inTestSection = false;
  const lines = text.split(/\r?\n/);

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index] ?? "";
    const header = sectionHeaderPattern.exec(line);
    if (header !== null) {
      const sectionName = normalizeSectionName(header[1] ?? "");
      inTestSection = sectionName === "test cases" || sectionName === "tasks";
      continue;
    }

    if (!inTestSection || !isTopLevelTestName(line)) {
      continue;
    }

    const name = line.trim();
    tests.push({
      id: `${uri}#${index}#${encodeURIComponent(name)}`,
      name,
      uri,
      line: index,
    });
  }

  return tests;
}

export function findRobotTestAtLine(uri: string, text: string, line: number): RobotTestItem | undefined {
  const tests = collectRobotTestsFromText(uri, text);
  let current: RobotTestItem | undefined;
  for (const test of tests) {
    if (test.line > line) {
      break;
    }
    current = test;
  }
  return current;
}

function normalizeSectionName(name: string): string {
  return name.trim().replace(/\s+/g, " ").toLowerCase();
}

function isTopLevelTestName(line: string): boolean {
  const trimmed = line.trim();
  if (trimmed.length === 0 || trimmed.startsWith("#")) {
    return false;
  }
  if (/^\s/.test(line)) {
    return false;
  }
  return !trimmed.startsWith("[");
}
