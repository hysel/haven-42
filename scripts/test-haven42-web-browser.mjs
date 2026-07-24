#!/usr/bin/env node
import { spawn, spawnSync } from "node:child_process";
import { createServer } from "node:http";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const QWEN_DIGEST = "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7";
const TEST_PNG = Buffer.from("89504e470d0a1a0a0000000d494844520000020000000200", "hex");
let models = ["qwen3.5:9b", "unknown-model:latest"];
const loaded = new Set();
const requests = [];
const trace = (message) => {
  if (process.env.HAVEN42_BROWSER_TEST_TRACE === "1") process.stderr.write(`[browser-test] ${message}\n`);
};

function json(response, status, value) {
  const body = Buffer.from(JSON.stringify(value));
  response.writeHead(status, { "Content-Type": "application/json", "Content-Length": body.length });
  response.end(body);
}

const fake = createServer((request, response) => {
  requests.push(`${request.method} ${request.url}`);
  if (request.method === "GET" && request.url === "/api/version") return json(response, 200, { version: "browser-test" });
  if (request.method === "GET" && request.url === "/api/tags") return json(response, 200, {
    models: models.map((name) => ({
      name,
      digest: name === "qwen3.5:9b" ? QWEN_DIGEST : "1".repeat(64),
    })),
  });
  if (request.method === "GET" && request.url === "/api/ps") return json(response, 200, { models: [...loaded].map((name) => ({ name })) });
  if (request.method === "GET" && request.url === "/object_info/CheckpointLoaderSimple") return json(response, 200, {
    CheckpointLoaderSimple: { input: { required: { ckpt_name: [["sd_xl_base_1.0.safetensors"], {}] } } },
  });
  if (request.method === "GET" && request.url === "/history/browser-test-image") return json(response, 200, {
    "browser-test-image": {
      status: { status_str: "success" },
      outputs: { 9: { images: [{ filename: "test.png", subfolder: "haven-42", type: "output" }] } },
    },
  });
  if (request.method === "GET" && request.url.startsWith("/view?")) {
    response.writeHead(200, { "Content-Type": "image/png", "Content-Length": TEST_PNG.length });
    response.end(TEST_PNG);
    return;
  }
  let body = "";
  request.on("data", (chunk) => { body += chunk; });
  request.on("end", () => {
    const payload = body ? JSON.parse(body) : {};
    if (request.url === "/api/chat") {
      loaded.add(payload.model);
      if (payload.messages?.at(-1)?.content === "force browser failure") {
        return json(response, 502, { error: "forced-browser-provider-failure" });
      }
      return json(response, 200, {
        message: { role: "assistant", content: "LOCAL_BROWSER_OK" },
        prompt_eval_count: 30,
        eval_count: 10,
        total_duration: 7_500_000_000,
        load_duration: 500_000_000,
        prompt_eval_duration: 1_000_000_000,
        eval_duration: 5_000_000_000,
      });
    }
    if (request.url === "/api/generate" && payload.keep_alive === 0) {
      loaded.delete(payload.model);
      return json(response, 200, { done: true });
    }
    if (request.url === "/prompt") return json(response, 200, { prompt_id: "browser-test-image" });
    if (request.url === "/history" && payload.clear === true) return json(response, 200, { status: "cleared" });
    return json(response, 404, { error: "not-found" });
  });
});

function listen(server) {
  return new Promise((accept, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => accept(server.address().port));
  });
}

async function terminate(child) {
  if (!child || child.exitCode !== null) return;
  child.kill();
  await Promise.race([
    new Promise((accept) => child.once("close", accept)),
    delay(5000),
  ]);
}

function resolvePython() {
  for (const [command, prefix] of [["python3", []], ["python", []], ["py", ["-3"]]]) {
    const probe = spawnSync(command, [...prefix, "-c", "import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)"]);
    if (probe.status === 0) return { command, prefix };
  }
  throw new Error("working-python3-not-found");
}

function resolveBrowser() {
  const candidates = [
    process.env.HAVEN42_TEST_BROWSER,
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (existsSync(candidate)) return candidate;
  }
  throw new Error("supported-chromium-browser-not-found");
}

async function waitFor(getter, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const value = await getter();
      if (value) return value;
    } catch {}
    await delay(100);
  }
  throw new Error("browser-test-timeout");
}

class Cdp {
  constructor(url) {
    this.nextId = 1;
    this.pending = new Map();
    this.socket = new WebSocket(url);
    this.socket.onmessage = ({ data }) => {
      const message = JSON.parse(data);
      if (!message.id || !this.pending.has(message.id)) return;
      const { accept, reject } = this.pending.get(message.id);
      this.pending.delete(message.id);
      if (message.error) reject(new Error(message.error.message));
      else accept(message.result);
    };
  }
  async open() {
    if (this.socket.readyState === WebSocket.OPEN) return;
    await new Promise((accept, reject) => {
      const timer = setTimeout(() => reject(new Error("cdp-open-timeout")), 15000);
      this.socket.onopen = () => {
        clearTimeout(timer);
        accept();
      };
      this.socket.onerror = (error) => {
        clearTimeout(timer);
        reject(error);
      };
    });
  }
  call(method, params = {}) {
    const id = this.nextId++;
    return new Promise((accept, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`cdp-call-timeout:${method}:ready-state-${this.socket.readyState}`));
      }, 15000);
      this.pending.set(id, {
        accept: (value) => { clearTimeout(timer); accept(value); },
        reject: (error) => { clearTimeout(timer); reject(error); },
      });
      trace(`cdp-send:${method}`);
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }
  async evaluate(expression) {
    const result = await this.call("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
    return result.result.value;
  }
  close() { this.socket.close(); }
}

const fakePort = await listen(fake);
const debugProbe = createServer();
const debugPort = await listen(debugProbe);
await new Promise((accept) => debugProbe.close(accept));
const python = resolvePython();
const browserPath = resolveBrowser();
const profile = mkdtempSync(join(tmpdir(), "haven42-browser-"));
let haven;
let browser;
let cdp;
let checks = 0;
let browserLaunchError;

try {
  trace("launching-local-web");
  haven = spawn(python.command, [...python.prefix, "-u", join(ROOT, "web", "server.py"), "--port", "0", "--no-open"], {
    cwd: ROOT,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });
  let output = "";
  haven.stdout.on("data", (chunk) => { output += chunk.toString(); });
  const origin = await waitFor(() => output.match(/http:\/\/127\.0\.0\.1:\d+/)?.[0]);
  trace("local-web-ready");
  const browserArguments = [
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--remote-allow-origins=*",
    `--remote-debugging-port=${debugPort}`,
    `--user-data-dir=${profile}`,
    origin,
  ];
  browser = spawn(browserPath, browserArguments, {
    windowsHide: true,
    stdio: ["ignore", "ignore", "pipe"],
  });
  browser.stderr.on("data", (chunk) => {
    if (process.env.HAVEN42_BROWSER_TEST_TRACE === "1") {
      trace(`browser-stderr:${chunk.toString().trim().slice(0, 500)}`);
    }
  });
  browser.once("error", (error) => { browserLaunchError = error; });
  const pages = await waitFor(async () => {
    if (browserLaunchError) throw browserLaunchError;
    if (browser.exitCode !== null) throw new Error(`browser-exited-${browser.exitCode}`);
    const response = await fetch(`http://127.0.0.1:${debugPort}/json`);
    const value = await response.json();
    return value.find((item) => item.type === "page" && item.url.startsWith(origin)) ? value : null;
  });
  trace("browser-ready");
  const page = pages.find((item) => item.type === "page" && item.url.startsWith(origin));
  cdp = new Cdp(page.webSocketDebuggerUrl);
  trace("opening-cdp");
  await cdp.open();
  trace("cdp-open");
  await cdp.call("Runtime.enable");
  trace("runtime-enabled");
  await waitFor(() => cdp.evaluate("document.readyState === 'complete' && Boolean(document.querySelector('.wizard-card'))"));
  await waitFor(() => cdp.evaluate("document.activeElement.classList.contains('wizard-card')"));

  const initial = await cdp.evaluate(`({
    modal: document.querySelector('#setup-wizard').getAttribute('aria-modal'),
    current: document.querySelector('[aria-current="step"]').dataset.wizardProgress,
    focused: document.activeElement.classList.contains('wizard-card'),
    skip: Boolean(document.querySelector('.skip-link'))
  })`);
  if (initial.modal !== "true" || initial.current !== "welcome" || !initial.focused || !initial.skip) throw new Error("initial-accessibility-state");
  checks += 4;
  trace("welcome-verified");

  await cdp.evaluate("document.querySelector('#wizard-guided').click()");
  await waitFor(() => cdp.evaluate("!document.querySelector('#wizard-readiness-next').disabled"));
  const guided = await cdp.evaluate(`({
    current: document.querySelector('[aria-current="step"]').dataset.wizardProgress,
    facts: document.querySelectorAll('#wizard-system-readiness .readiness-fact').length,
    planActions: document.querySelectorAll('#wizard-setup-plan .plan-action').length,
    planText: document.querySelector('#wizard-setup-plan').textContent,
    status: document.querySelector('#wizard-scan-status').textContent
  })`);
  if (
    guided.current !== "readiness"
    || guided.facts !== 4
    || guided.planActions < 2
    || !guided.planText.includes("installation disabled")
    || !guided.status.includes("Nothing was installed")
  ) throw new Error(`guided-readiness:${JSON.stringify(guided)}`);
  checks += 4;
  await cdp.evaluate("document.querySelector('#wizard-readiness-back').click()");
  await waitFor(() => cdp.evaluate("document.querySelector('[aria-current=\"step\"]').dataset.wizardProgress === 'welcome'"));
  trace("guided-readiness-verified");

  await cdp.evaluate("document.querySelector('#wizard-existing').click()");
  const provider = await cdp.evaluate(`({
    visible: !document.querySelector('[data-wizard-step="provider"]').classList.contains('hidden'),
    focused: document.activeElement.id
  })`);
  if (!provider.visible || provider.focused !== "wizard-endpoint") throw new Error("provider-step-focus");
  checks += 2;
  trace("provider-step-verified");

  await cdp.evaluate(`(() => {
    const input = document.querySelector('#wizard-endpoint');
    input.value = 'http://127.0.0.1:${fakePort}';
    document.querySelector('#wizard-connection-form').requestSubmit();
  })()`);
  await waitFor(() => cdp.evaluate("!document.querySelector('[data-wizard-step=\"ready\"]').classList.contains('hidden')"));
  const ready = await cdp.evaluate(`({
    rows: document.querySelectorAll('#wizard-readiness .readiness-row').length,
    recommended: document.querySelectorAll('#wizard-readiness .readiness-state.recommended').length,
    finishDisabled: document.querySelector('#wizard-finish').disabled,
    capabilities: document.querySelectorAll('#capability-list .capability-item').length,
    health: document.querySelector('#provider-health').textContent
  })`);
  if (ready.rows !== 3 || ready.recommended !== 3 || ready.finishDisabled || ready.capabilities !== 5 || !ready.health.includes("healthy")) throw new Error("ready-step");
  checks += 5;
  trace("model-readiness-verified");

  await cdp.evaluate(`(() => {
    const first = document.querySelector('#wizard-back');
    const last = document.querySelector('#wizard-finish');
    last.focus();
    last.dispatchEvent(new KeyboardEvent('keydown', {key: 'Tab', bubbles: true, cancelable: true}));
    return document.activeElement === first;
  })()`).then((wrapped) => { if (!wrapped) throw new Error("focus-trap"); });
  checks += 1;

  await cdp.evaluate("document.querySelector('#wizard-finish').click()");
  const opened = await cdp.evaluate(`({
    hidden: document.querySelector('#setup-wizard').classList.contains('hidden'),
    promptEnabled: !document.querySelector('#prompt').disabled,
    model: document.querySelector('#model').value
  })`);
  if (!opened.hidden || !opened.promptEnabled || opened.model !== "automatic") throw new Error("chat-handoff");
  checks += 3;
  trace("chat-handoff-verified");

  models = ["unknown-model:latest"];
  await cdp.evaluate(`document.querySelector('#connection-form').requestSubmit()`);
  await waitFor(() => cdp.evaluate(`(
    !document.querySelector('#connect-button').disabled
    && document.querySelector('#text-status').textContent.includes('1 installed model found')
    && document.querySelector('#model option[value="manual:unknown-model:latest"]') !== null
  )`));
  const unknown = await cdp.evaluate(`(() => {
    const select = document.querySelector('#model');
    select.value = 'manual:unknown-model:latest';
    select.dispatchEvent(new Event('change', {bubbles: true}));
    return {
      state: document.querySelector('#model-state').textContent,
      promptEnabled: !document.querySelector('#prompt').disabled
    };
  })()`);
  if (!unknown.state.includes("unverified") || !unknown.promptEnabled) throw new Error("unknown-model-advanced-only");
  checks += 2;
  trace("advanced-model-verified");

  await cdp.evaluate(`(() => {
    document.querySelector('#prompt').value = 'browser flow';
    document.querySelector('#text-form').requestSubmit();
  })()`);
  try {
    await waitFor(() => cdp.evaluate(`(
      [...document.querySelectorAll('.message p')].some((item) => item.textContent === 'LOCAL_BROWSER_OK')
      || document.querySelector('#task-event').dataset.kind === 'error'
    )`));
  } catch (error) {
    const diagnostic = await cdp.evaluate(`({
      taskEvent: document.querySelector('#task-event').textContent,
      taskKind: document.querySelector('#task-event').dataset.kind || '',
      status: document.querySelector('#text-status').textContent,
      error: document.querySelector('#connection-error').textContent,
      promptDisabled: document.querySelector('#prompt').disabled,
      sendDisabled: document.querySelector('#send-button').disabled,
      selectedModel: document.querySelector('#model').value
    })`);
    throw new Error(`final-response-timeout:${JSON.stringify({ diagnostic, requests })}`, { cause: error });
  }
  const result = await cdp.evaluate(`({
    output: [...document.querySelectorAll('.message p')].some((item) => item.textContent === 'LOCAL_BROWSER_OK'),
    typed: document.querySelector('#task-event').textContent,
    kind: document.querySelector('#task-event').dataset.kind,
    status: document.querySelector('#text-status').textContent,
    error: document.querySelector('#connection-error').textContent,
    runDetailsVisible: !document.querySelector('#run-details').classList.contains('hidden'),
    runDetails: document.querySelector('#run-details-list').textContent
  })`);
  if (
    !result.output
    || !result.typed.includes("no file written")
    || !result.typed.includes("model evidence is unverified")
    || result.kind !== "warning"
    || !result.runDetailsVisible
    || !result.runDetails.includes("40")
    || !result.runDetails.includes("2 tokens/s")
  ) {
    throw new Error(`typed-result-rendering:${JSON.stringify(result)}`);
  }
  checks += 7;
  trace("typed-result-verified");

  await cdp.evaluate("document.querySelector('#software-nav').click()");
  await waitFor(() => cdp.evaluate("!document.querySelector('#workflow-select').disabled"));
  await cdp.evaluate("document.querySelector('#workflow-plan-button').click()");
  await waitFor(() => cdp.evaluate("!document.querySelector('#workflow-result').classList.contains('hidden')"));
  const workflow = await cdp.evaluate(`({
    title: document.querySelector('#workflow-result-title').textContent,
    policy: document.querySelector('#workflow-result-policy').textContent,
    textHidden: document.querySelector('#text-panel').classList.contains('hidden')
  })`);
  if (
    !workflow.title
    || !workflow.policy.includes("No process started")
    || !workflow.policy.includes("no file write")
    || !workflow.textHidden
  ) throw new Error(`workflow-plan-rendering:${JSON.stringify(workflow)}`);
  checks += 4;
  trace("workflow-plan-verified");

  await cdp.evaluate("document.querySelector('#image-nav').click()");
  await cdp.evaluate(`(() => {
    document.querySelector('#image-endpoint').value = 'http://127.0.0.1:${fakePort}';
    document.querySelector('#image-connect-button').click();
  })()`);
  await waitFor(() => cdp.evaluate("!document.querySelector('#image-run-button').disabled"));
  await cdp.evaluate(`(() => {
    document.querySelector('#image-prompt').value = 'synthetic browser image';
    document.querySelector('#image-size').value = '512';
    document.querySelector('#image-steps').value = '10';
    document.querySelector('#image-run-button').click();
  })()`);
  await waitFor(() => cdp.evaluate("!document.querySelector('#image-result').classList.contains('hidden')"));
  const imageResult = await cdp.evaluate(`({
    badge: document.querySelector('#image-provider-badge').textContent,
    summary: document.querySelector('#image-result-summary').textContent,
    source: document.querySelector('#image-preview').src,
    download: document.querySelector('#image-download').getAttribute('download')
  })`);
  if (
    !imageResult.badge.includes("loopback")
    || !imageResult.summary.includes("512 × 512")
    || !imageResult.summary.includes("provider copy retained")
    || !imageResult.source.startsWith("data:image/png;base64,")
    || imageResult.download !== "haven42-generated-image.png"
  ) throw new Error(`image-result-rendering:${JSON.stringify(imageResult)}`);
  checks += 5;
  trace("image-flow-verified");

  const hostileEvents = await cdp.evaluate(`(() => {
    const cases = [
      [],
      [{sequence: 2, type: 'result', code: 'TEXT_ARTIFACT_READY'}],
      [{sequence: 1, type: 'result', code: 'TEXT_ARTIFACT_READY'}],
      [{sequence: 1, type: 'result', code: 'TEXT_ARTIFACT_READY'}, {sequence: 2, type: 'progress', code: 'LATE'}],
      [{sequence: 1, type: 'result', code: 'TEXT_ARTIFACT_READY'}, {sequence: 2, type: 'error', code: 'SECOND_TERMINAL'}],
      [{sequence: 1, type: 'result', code: 'lowercase'}]
    ];
    return cases.every((events) => {
      try {
        validateExecutionEvents(events, 'result');
        return false;
      } catch {
        return true;
      }
    });
  })()`);
  if (!hostileEvents) throw new Error("hostile-event-envelope-accepted");
  checks += 6;
  trace("hostile-events-rejected");

  await cdp.evaluate(`(() => {
    document.querySelector('#prompt').value = 'force browser failure';
    document.querySelector('#text-form').requestSubmit();
  })()`);
  await waitFor(() => cdp.evaluate("document.querySelector('#task-event').dataset.kind === 'error'"));
  const recovery = await cdp.evaluate(`({
    prompt: document.querySelector('#prompt').value,
    task: document.querySelector('#task-event').textContent,
    failedUserMessageVisible: [...document.querySelectorAll('.message.user p')]
      .some((item) => item.textContent === 'force browser failure')
  })`);
  if (
    recovery.prompt !== "force browser failure"
    || !recovery.task.includes("retry creates a new request")
    || recovery.failedUserMessageVisible
    || loaded.size !== 0
  ) throw new Error(`failure-recovery:${JSON.stringify(recovery)}`);
  checks += 4;
  trace("failure-recovery-verified");
  console.log(`Haven 42 headless browser flow passed: ${checks} checks.`);
} finally {
  trace("cleanup-started");
  cdp?.close();
  await terminate(browser);
  await terminate(haven);
  fake.closeAllConnections();
  await new Promise((accept) => fake.close(accept));
  rmSync(profile, { recursive: true, force: true, maxRetries: 20, retryDelay: 100 });
  trace("cleanup-complete");
}
