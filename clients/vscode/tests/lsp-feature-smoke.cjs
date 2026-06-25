const assert = require("node:assert/strict");

const { robotDocumentSelector, robotFrameworkLanguageId } = require("../out/application/buildClientOptions.js");
const { planServerCommand, serverInitializationOptions } = require("../out/application/buildServerOptions.js");
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

testDocumentSelector();
testDefaultServerStartup();
testServerCommandOverride();
testConfigurationBridge();
testInitializationOptionsUseServerConfigurationShape();

console.log("lsp feature smoke ok");
