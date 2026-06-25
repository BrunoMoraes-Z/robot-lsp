const assert = require("node:assert/strict");

const { robotDocumentSelector, robotFrameworkLanguageId } = require("../out/application/buildClientOptions.js");
const { planServerCommand, serverInitializationOptions } = require("../out/application/buildServerOptions.js");
const { collectRobotTestsFromText } = require("../out/application/collectTests.js");
const { serverRobotLspConfiguration } = require("../out/application/configurationBridge.js");
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

testDocumentSelector();
testDefaultServerStartup();
testServerCommandOverride();
testConfigurationBridge();
testInitializationOptionsUseServerConfigurationShape();
testRobotTestCollection();

console.log("lsp feature smoke ok");
