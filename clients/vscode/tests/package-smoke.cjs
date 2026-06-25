const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.join(__dirname, "..");

function exists(relativePath) {
  return fs.existsSync(path.join(root, relativePath));
}

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(root, relativePath), "utf8"));
}

function testManifest() {
  const manifest = readJson("package.json");
  assert.equal(manifest.main, "./out/extension.js");
  assert.ok(manifest.dependencies["vscode-languageclient"]);
  assert.ok(manifest.devDependencies["@vscode/vsce"]);
  assert.equal(manifest.repository.directory, "clients/vscode");
  assert.ok(manifest.scripts.package.includes("vsce package"));
}

function testRequiredFilesExistAfterCompile() {
  assert.equal(exists("out/extension.js"), true);
  assert.equal(exists("out/infrastructure/debugAdapterRuntime.js"), true);
  assert.equal(exists("language-configuration.json"), true);
  assert.equal(exists("syntaxes/robot.tmLanguage.json"), true);
  assert.equal(exists("README.md"), true);
  assert.equal(exists("CHANGELOG.md"), true);
  assert.equal(exists("LICENSE"), true);
}

function testVsCodeIgnoreDoesNotExcludeRuntimeDependencies() {
  const ignore = fs.readFileSync(path.join(root, ".vscodeignore"), "utf8");
  assert.equal(ignore.includes("node_modules/**"), false);
  assert.equal(ignore.includes("src/**"), true);
  assert.equal(ignore.includes("tests/**"), true);
}

function testWorkflowExists() {
  const workflow = path.join(root, "..", "..", ".github", "workflows", "vscode-extension.yml");
  assert.equal(fs.existsSync(workflow), true);
}

testManifest();
testRequiredFilesExistAfterCompile();
testVsCodeIgnoreDoesNotExcludeRuntimeDependencies();
testWorkflowExists();

console.log("package smoke ok");
