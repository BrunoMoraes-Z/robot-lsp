const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const { robotDocumentSelector, robotFrameworkLanguageId } = require("../out/application/buildClientOptions.js");
const { planServerCommand, serverInitializationOptions } = require("../out/application/buildServerOptions.js");
const { collectRobotTestsFromText, findRobotTestAtLine } = require("../out/application/collectTests.js");
const { serverRobotLspConfiguration } = require("../out/application/configurationBridge.js");
const { buildDebugLaunchConfiguration, buildRunLaunchConfiguration } = require("../out/application/resolveLaunchConfig.js");
const { defaultRobotLspSettings } = require("../out/domain/settings.js");

function settings(overrides = {}) {
  return {
    ...defaultRobotLspSettings,
    ...overrides,
    languageServer: {
      ...defaultRobotLspSettings.languageServer,
      ...(overrides.languageServer ?? {}),
    },
    runtime: {
      ...defaultRobotLspSettings.runtime,
      ...(overrides.runtime ?? {}),
    },
    debug: {
      ...defaultRobotLspSettings.debug,
      ...(overrides.debug ?? {}),
    },
  };
}

function testDocumentSelector() {
  assert.equal(robotFrameworkLanguageId, "robotframework");
  assert.deepEqual(robotDocumentSelector, [
    { scheme: "file", language: "robotframework" },
    { scheme: "untitled", language: "robotframework" },
  ]);
}

function testDefaultServerStartup() {
  const planned = planServerCommand(settings(), "python3");
  assert.equal(planned.command, "python3");
  assert.deepEqual(planned.args, ["-m", "robot_lsp"]);
  assert.deepEqual(planned.env, {});
}

function testServerCommandOverride() {
  const planned = planServerCommand(settings({
    languageServer: {
      command: "robot-lsp-server",
      args: ["--stdio"],
      cwd: "C:/workspace",
      env: { ROBOT_SYSLOG_FILE: "NONE" },
    },
  }), "python3");

  assert.equal(planned.command, "robot-lsp-server");
  assert.deepEqual(planned.args, ["--stdio"]);
  assert.equal(planned.cwd, "C:/workspace");
  assert.deepEqual(planned.env, { ROBOT_SYSLOG_FILE: "NONE" });
}

function testConfigurationBridge() {
  const config = serverRobotLspConfiguration(settings({
    diagnosticsEnable: false,
    completionSnippets: false,
    logLevel: "debug",
    variables: { EXECDIR: "C:/workspace", ENV: "dev" },
  }));

  assert.deepEqual(config, {
    diagnostics: { enable: false },
    completion: { snippets: false },
    logLevel: "debug",
    variables: { EXECDIR: "C:/workspace", ENV: "dev" },
  });
}

function testInitializationOptionsUseServerConfigurationShape() {
  const input = settings({ variables: { ROOT: "C:/workspace" } });
  assert.deepEqual(serverInitializationOptions(input), serverRobotLspConfiguration(input));
}

function testRobotTestCollection() {
  const tests = collectRobotTestsFromText("file:///workspace/suite.robot", [
    "*** Settings ***",
    "Library    Collections",
    "*** Test Cases ***",
    "First Test",
    "    Log    hello",
    "# ignored comment",
    "Second Test",
    "    [Tags]    smoke",
    "*** Keywords ***",
    "Helper Keyword",
    "    No Operation",
    "*** Tasks ***",
    "Runnable Task",
  ].join("\n"));

  assert.deepEqual(tests.map((test) => [test.name, test.line]), [
    ["First Test", 3],
    ["Second Test", 6],
    ["Runnable Task", 12],
  ]);
  assert.ok(tests.every((test) => test.uri === "file:///workspace/suite.robot"));
}

function testFindRobotTestAtLine() {
  const text = [
    "*** Test Cases ***",
    "First Test",
    "    Log    hello",
    "Second Test",
    "    Log    world",
  ].join("\n");

  assert.equal(findRobotTestAtLine("file:///workspace/suite.robot", text, 2)?.name, "First Test");
  assert.equal(findRobotTestAtLine("file:///workspace/suite.robot", text, 4)?.name, "Second Test");
  assert.equal(findRobotTestAtLine("file:///workspace/suite.robot", text, 0), undefined);
}

function testRunLaunchConfigurationForFile() {
  const config = buildRunLaunchConfiguration(settings({
    runtime: {
      python: "C:/Python/python.exe",
      env: { ROBOT_ENV: "dev" },
      pythonPath: ["C:/workspace/libs"],
    },
    variables: { EXECDIR: "C:/workspace" },
  }), {
    target: "C:/workspace/suite.robot",
    cwd: "C:/workspace",
  });

  assert.deepEqual(config, {
    type: "robot-lsp",
    request: "launch",
    name: "Robot Framework: Current File",
    target: "C:/workspace/suite.robot",
    cwd: "C:/workspace",
    args: [],
    env: { ROBOT_ENV: "dev" },
    variables: { EXECDIR: "C:/workspace" },
    python: "C:/Python/python.exe",
    pythonPath: ["C:/workspace/libs"],
    terminal: "integrated",
    makeSuite: true,
    noDebug: true,
  });
}

function testRunLaunchConfigurationForTest() {
  const config = buildRunLaunchConfiguration(settings(), {
    target: "C:/workspace/suite.robot",
    cwd: "C:/workspace",
    testName: "Should Work",
  });

  assert.equal(config.name, "Robot Framework: Should Work");
  assert.deepEqual(config.args, ["--test", "Should Work"]);
  assert.equal(config.noDebug, true);
}

function testDebugLaunchConfiguration() {
  const config = buildDebugLaunchConfiguration(settings(), {
    target: "C:/workspace/suite.robot",
    cwd: "C:/workspace",
  });

  assert.equal(config.type, "robot-lsp");
  assert.equal(config.request, "launch");
  assert.equal(config.name, "Robot Framework: Debug Current File");
  assert.equal(config.noDebug, false);
}

function testDebugContribution() {
  const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "package.json"), "utf8"));
  const debuggerContribution = manifest.contributes.debuggers.find((item) => item.type === "robot-lsp");

  assert.ok(debuggerContribution);
  assert.equal(debuggerContribution.label, "Robot LSP");
  assert.deepEqual(debuggerContribution.languages, ["robotframework"]);
  assert.equal(debuggerContribution.initialConfigurations[0].type, "robot-lsp");
  assert.equal(debuggerContribution.initialConfigurations[0].target, "${file}");
  assert.equal(debuggerContribution.configurationSnippets[0].body.request, "launch");
}

testDocumentSelector();
testDefaultServerStartup();
testServerCommandOverride();
testConfigurationBridge();
testInitializationOptionsUseServerConfigurationShape();
testRobotTestCollection();
testFindRobotTestAtLine();
testRunLaunchConfigurationForFile();
testRunLaunchConfigurationForTest();
testDebugLaunchConfiguration();
testDebugContribution();

console.log("lsp feature smoke ok");
