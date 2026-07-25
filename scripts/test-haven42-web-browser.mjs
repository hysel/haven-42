#!/usr/bin/env node
import { spawn, spawnSync } from "node:child_process";
import { createServer } from "node:http";
import { existsSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
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
const chatPayloads = [];
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
      chatPayloads.push(payload);
      loaded.add(payload.model);
      if (payload.messages?.at(-1)?.content === "force browser failure") {
        return json(response, 502, { error: "forced-browser-provider-failure" });
      }
      if (payload.messages?.at(-1)?.content === "markdown showcase") {
        return json(response, 200, {
          message: {
            role: "assistant",
            content: [
              "### Clear answer 😀",
              "",
              "- **Strong point** with *emphasis*",
              "- Safe `inline code`",
              "",
              "> A useful note",
              "",
              "```js",
              "const value = '<img src=x onerror=alert(1)>';",
              "```",
              "",
              "<script>window.hostile = true</script>",
            ].join("\n"),
          },
          prompt_eval_count: 30,
          eval_count: 10,
          total_duration: 7_500_000_000,
          load_duration: 500_000_000,
          prompt_eval_duration: 1_000_000_000,
          eval_duration: 5_000_000_000,
        });
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
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
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
    this.socket.onclose = () => {
      for (const { reject } of this.pending.values()) reject(new Error("cdp-target-closed"));
      this.pending.clear();
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

async function connectPageCdp(debugPort, origin, browser, browserLaunchError) {
  return waitFor(async () => {
    if (browserLaunchError()) throw browserLaunchError();
    if (browser.exitCode !== null) throw new Error(`browser-exited-${browser.exitCode}`);
    const response = await fetch(`http://127.0.0.1:${debugPort}/json`);
    const pages = (await response.json())
      .filter((item) => item.type === "page")
      .sort((left, right) => Number(right.url.startsWith(origin)) - Number(left.url.startsWith(origin)));
    for (const page of pages) {
      const candidate = new Cdp(page.webSocketDebuggerUrl);
      try {
        await candidate.open();
        await candidate.call("Runtime.enable");
        if (!page.url.startsWith(origin)) {
          await candidate.call("Page.enable");
          await candidate.call("Page.navigate", { url: origin });
        }
        return candidate;
      } catch {
        candidate.close();
      }
    }
    return null;
  }, 30000);
}

const fakePort = await listen(fake);
const packagedExecutable = process.env.HAVEN42_TEST_EXECUTABLE
  ? resolve(ROOT, process.env.HAVEN42_TEST_EXECUTABLE)
  : "";
const python = packagedExecutable ? null : resolvePython();
const browserPath = resolveBrowser();
const profile = mkdtempSync(join(tmpdir(), "haven42-browser-"));
let haven;
let browser;
let cdp;
let checks = 0;
let browserLaunchError;

try {
  trace("launching-local-web");
  const havenCommand = packagedExecutable || python.command;
  const havenArguments = packagedExecutable
    ? ["--port", "0", "--no-open"]
    : [...python.prefix, "-u", join(ROOT, "web", "server.py"), "--port", "0", "--no-open"];
  haven = spawn(havenCommand, havenArguments, {
    cwd: packagedExecutable ? dirname(packagedExecutable) : ROOT,
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
    "--disable-gpu-sandbox",
    "--disable-background-networking",
    "--host-resolver-rules=MAP * 0.0.0.0, EXCLUDE 127.0.0.1",
    "--no-first-run",
    "--remote-allow-origins=*",
    "--remote-debugging-port=0",
    `--user-data-dir=${profile}`,
    origin,
  ];
  if (process.platform === "win32" || process.env.HAVEN42_BROWSER_TEST_NO_SANDBOX === "1") {
    // Managed Windows hosts can deny Chromium's disposable test sandbox. This
    // isolated profile resolves every non-loopback host to 0.0.0.0 and serves
    // synthetic content only; Haven 42 never adds this flag to a user's browser.
    browserArguments.splice(2, 0, "--no-sandbox");
  }
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
  const debugPort = await waitFor(() => {
    if (browserLaunchError) throw browserLaunchError;
    if (browser.exitCode !== null) throw new Error(`browser-exited-${browser.exitCode}`);
    const activePortPath = join(profile, "DevToolsActivePort");
    if (!existsSync(activePortPath)) return null;
    const port = Number(readFileSync(activePortPath, "utf8").split(/\r?\n/, 1)[0]);
    return Number.isInteger(port) && port > 0 && port <= 65535 ? port : null;
  }, 30000);
  trace("opening-cdp");
  cdp = await connectPageCdp(debugPort, origin, browser, () => browserLaunchError);
  trace("browser-ready");
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

  const wizardControlSizing = await cdp.evaluate(`({
    endpoint: document.querySelector('#wizard-endpoint').getBoundingClientRect().height,
    timeout: document.querySelector('#wizard-timeout').getBoundingClientRect().height,
    cleanup: document.querySelector('#wizard-idle-unload').getBoundingClientRect().height,
    endpointFont: getComputedStyle(document.querySelector('#wizard-endpoint')).fontSize,
    timeoutFont: getComputedStyle(document.querySelector('#wizard-timeout')).fontSize,
    cleanupFont: getComputedStyle(document.querySelector('#wizard-idle-unload')).fontSize
  })`);
  if (
    wizardControlSizing.endpoint !== 36
    || wizardControlSizing.timeout !== 36
    || wizardControlSizing.cleanup !== 36
    || wizardControlSizing.endpointFont !== "13px"
    || wizardControlSizing.timeoutFont !== "13px"
    || wizardControlSizing.cleanupFont !== "13px"
  ) throw new Error(`compact-wizard-controls:${JSON.stringify(wizardControlSizing)}`);
  checks += 6;

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

  const requestsBeforeWizardContinue = requests.length;
  const wizardConnectedState = await cdp.evaluate(`(() => {
    document.querySelector('#wizard-back').click();
    const state = {
      providerVisible: !document.querySelector('[data-wizard-step="provider"]').classList.contains('hidden'),
      text: document.querySelector('#wizard-connect').textContent,
      enabled: !document.querySelector('#wizard-connect').disabled
    };
    document.querySelector('#wizard-connection-form').requestSubmit();
    return state;
  })()`);
  await waitFor(() => cdp.evaluate("!document.querySelector('[data-wizard-step=\"ready\"]').classList.contains('hidden')"));
  if (
    !wizardConnectedState.providerVisible
    || wizardConnectedState.text !== "Continue"
    || !wizardConnectedState.enabled
    || requests.length !== requestsBeforeWizardContinue
  ) throw new Error(`wizard-connected-state:${JSON.stringify(wizardConnectedState)}`);
  checks += 4;

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
    model: document.querySelector('#model').value,
    browseEnabled: !document.querySelector('#context-files').disabled,
    browseCursor: getComputedStyle(document.querySelector('.context-picker')).cursor,
    browseControlCount: document.querySelectorAll('.context-picker').length,
    browseTag: document.querySelector('.context-picker').tagName,
    browseFocusable: document.querySelector('.context-picker').tabIndex === 0,
    chatNavigationLabel: document.querySelector('#home-nav').textContent,
    legacyTextNavigationCount: document.querySelectorAll('.capability-nav').length,
    modeTabCount: document.querySelectorAll('.mode-tab').length,
    conversationHeading: document.querySelector('#capability-eyebrow').textContent,
    conversationModelLabel: document.querySelector('#model-label').textContent
  })`);
  if (
    !opened.hidden
    || !opened.promptEnabled
    || opened.model !== "automatic"
    || !opened.browseEnabled
    || opened.browseCursor !== "pointer"
    || opened.browseControlCount !== 1
    || opened.browseTag !== "BUTTON"
    || !opened.browseFocusable
    || !opened.chatNavigationLabel.includes("Chat")
    || opened.legacyTextNavigationCount !== 0
    || opened.modeTabCount !== 0
    || opened.conversationHeading !== "CONVERSATION"
    || opened.conversationModelLabel !== "Conversation model"
  ) throw new Error(`chat-handoff:${JSON.stringify(opened)}`);
  const browseActivation = await cdp.evaluate(`(() => {
    const input = document.querySelector('#context-files');
    const original = input.click;
    let activations = 0;
    input.click = () => { activations += 1; };
    document.querySelector('#browse-context').click();
    input.click = original;
    return activations;
  })()`);
  if (browseActivation !== 1) throw new Error("browse-button-did-not-activate-picker");
  checks += 14;
  trace("chat-handoff-verified");

  const compactControls = await cdp.evaluate(`({
    endpoint: document.querySelector('#endpoint').getBoundingClientRect().height,
    cleanup: document.querySelector('#system-idle-unload').getBoundingClientRect().height,
    model: document.querySelector('#model').getBoundingClientRect().height,
    endpointFont: getComputedStyle(document.querySelector('#endpoint')).fontSize,
    cleanupFont: getComputedStyle(document.querySelector('#system-idle-unload')).fontSize,
    timeoutFont: getComputedStyle(document.querySelector('#timeout')).fontSize,
    advancedCleanupFont: getComputedStyle(document.querySelector('#idle-unload')).fontSize
  })`);
  if (
    Math.abs(compactControls.endpoint - compactControls.model) > 1
    || Math.abs(compactControls.cleanup - compactControls.model) > 1
    || compactControls.endpoint >= 44
    || compactControls.endpointFont !== "13px"
    || compactControls.cleanupFont !== "13px"
    || compactControls.timeoutFont !== "13px"
    || compactControls.advancedCleanupFont !== "13px"
  ) throw new Error(`compact-provider-controls:${JSON.stringify(compactControls)}`);
  checks += 7;

  const connectedControls = await cdp.evaluate(`({
    connectionText: document.querySelector('#connect-button').textContent,
    connectionDisabled: document.querySelector('#connect-button').disabled,
    cleanupText: document.querySelector('#apply-cleanup-policy').textContent,
    cleanupDisabled: document.querySelector('#apply-cleanup-policy').disabled
  })`);
  if (
    connectedControls.connectionText !== "Connected"
    || !connectedControls.connectionDisabled
    || connectedControls.cleanupText !== "Applied"
    || !connectedControls.cleanupDisabled
  ) throw new Error(`connected-controls:${JSON.stringify(connectedControls)}`);
  checks += 4;

  models = ["unknown-model:latest"];
  const dirtyConnection = await cdp.evaluate(`(() => {
    const timeout = document.querySelector('#timeout');
    timeout.value = '60';
    timeout.dispatchEvent(new Event('change', {bubbles: true}));
    const state = {
      text: document.querySelector('#connect-button').textContent,
      enabled: !document.querySelector('#connect-button').disabled
    };
    document.querySelector('#connection-form').requestSubmit();
    return state;
  })()`);
  if (dirtyConnection.text !== "Apply changes" || !dirtyConnection.enabled) {
    throw new Error(`dirty-connection:${JSON.stringify(dirtyConnection)}`);
  }
  checks += 2;
  await waitFor(() => cdp.evaluate(`(
    document.querySelector('#connect-button').disabled
    && document.querySelector('#connect-button').textContent === 'Connected'
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

  models = ["qwen3.5:9b", "unknown-model:latest"];
  await cdp.evaluate(`(() => {
    const timeout = document.querySelector('#timeout');
    timeout.value = '120';
    timeout.dispatchEvent(new Event('change', {bubbles: true}));
    document.querySelector('#connection-form').requestSubmit();
  })()`);
  await waitFor(() => cdp.evaluate(`(
    document.querySelector('#connect-button').disabled
    && document.querySelector('#connect-button').textContent === 'Connected'
    && document.querySelector('#text-status').textContent.includes('2 installed models found')
  )`));
  const requestsBeforeUnchangedSubmit = requests.length;
  await cdp.evaluate("document.querySelector('#connection-form').requestSubmit()");
  await delay(150);
  if (requests.length !== requestsBeforeUnchangedSubmit) throw new Error("unchanged-provider-reconnected");
  checks += 1;

  const modelsView = await cdp.evaluate(`(() => {
    document.querySelector('#models-nav').click();
    return {
      active: document.querySelector('#models-nav').classList.contains('active'),
      visible: !document.querySelector('#models-panel').classList.contains('hidden'),
      textHidden: document.querySelector('#text-panel').classList.contains('hidden'),
      imageHidden: document.querySelector('#image-panel').classList.contains('hidden'),
      focused: document.activeElement.id,
      installed: document.querySelectorAll('#model-search-results .model-search-result').length,
      installedLabel: document.querySelector('#model-search-results small')?.textContent || ''
    };
  })()`);
  if (
    !modelsView.active
    || !modelsView.visible
    || !modelsView.textHidden
    || !modelsView.imageHidden
    || modelsView.focused !== "models-title"
    || modelsView.installed !== 2
    || !modelsView.installedLabel.includes("Already installed on connected Ollama server")
  ) throw new Error(`dedicated-models-view:${JSON.stringify(modelsView)}`);
  checks += 7;

  await cdp.evaluate(`(() => {
    const original = window.fetch;
    window.__havenOriginalFetch = original;
    window.fetch = (input, init) => input === "/api/model-search"
      ? Promise.resolve(new Response(JSON.stringify({
          schemaVersion: 1,
          kind: "model-catalog-search",
          query: "writing",
          source: "ollama-public-catalog",
          networkUsed: true,
          queryPersisted: false,
          repositoryContentSent: false,
          hardwareProfileSent: false,
          downloadsPerformed: false,
          configurationChanged: false,
          results: [{
            name: "candidate-writing:7b",
            source: "ollama-public-catalog",
            status: "not-installed",
            validationStatus: "candidate-only",
            capabilityEvidence: "unverified",
            hardwareFit: "unknown",
            licenseStatus: "review-required",
            executionAllowed: false,
            installCommand: "ollama pull candidate-writing:7b"
          }]
        }), {status: 200, headers: {"Content-Type": "application/json"}}))
      : original(input, init);
    const query = document.querySelector('#model-search-query');
    query.value = "writing";
    query.dispatchEvent(new Event('input', {bubbles: true}));
    document.querySelector('#model-search-form').requestSubmit();
  })()`);
  await waitFor(() => cdp.evaluate("document.querySelectorAll('#model-search-results .model-search-result').length === 1"));
  await cdp.evaluate("document.querySelector('#model-search-results button').click()");
  const discovery = await cdp.evaluate(`({
    desired: document.querySelector('#desired-model-name').textContent,
    state: document.querySelector('#desired-model-state').textContent,
    command: document.querySelector('#desired-model-command').textContent,
    hidden: document.querySelector('#desired-model').classList.contains('hidden'),
    searchStatus: document.querySelector('#model-search-status').textContent,
    currentModel: document.querySelector('#model').value
  })`);
  if (
    discovery.desired !== "candidate-writing:7b"
    || !discovery.state.includes("execution disabled")
    || discovery.command !== "ollama pull candidate-writing:7b"
    || discovery.hidden
    || !discovery.searchStatus.includes("Nothing was downloaded")
    || discovery.currentModel !== "manual:unknown-model:latest"
  ) throw new Error("candidate-only-model-discovery");
  checks += 6;

  const capabilityReset = await cdp.evaluate(`(() => {
    const capability = document.querySelector('#model-search-capability');
    capability.value = 'content.write';
    capability.dispatchEvent(new Event('change', {bubbles: true}));
    return {
      query: document.querySelector('#model-search-query').value,
      resultCount: document.querySelectorAll('#model-search-results .model-search-result').length,
      desiredHidden: document.querySelector('#desired-model').classList.contains('hidden'),
      resultName: document.querySelector('#model-search-results strong')?.textContent || '',
      status: document.querySelector('#model-search-status').textContent
    };
  })()`);
  if (
    capabilityReset.query !== ""
    || capabilityReset.resultCount !== 2
    || !capabilityReset.desiredHidden
    || capabilityReset.resultName !== "qwen3.5:9b"
    || !capabilityReset.status.includes("Writing")
  ) throw new Error(`model-capability-reset:${JSON.stringify(capabilityReset)}`);
  checks += 5;

  const hostileCatalogRejected = await cdp.evaluate(`(() => {
    try {
      validateModelSearch({
        schemaVersion: 1,
        kind: "model-catalog-search",
        query: "safe",
        source: "ollama-public-catalog",
        networkUsed: true,
        queryPersisted: false,
        repositoryContentSent: false,
        hardwareProfileSent: false,
        downloadsPerformed: false,
        configurationChanged: false,
        results: [{
          name: "safe:7b",
          source: "ollama-public-catalog",
          status: "not-installed",
          validationStatus: "candidate-only",
          capabilityEvidence: "unverified",
          hardwareFit: "unknown",
          licenseStatus: "review-required",
          executionAllowed: false,
          installCommand: "ollama pull safe:7b && hostile"
        }]
      });
      return false;
    } catch {
      return true;
    }
  })()`);
  if (!hostileCatalogRejected) throw new Error("hostile-catalog-command-accepted");
  checks += 1;
  await cdp.evaluate("window.fetch = window.__havenOriginalFetch");
  trace("candidate-model-discovery-verified");

  const dirtyCleanup = await cdp.evaluate(`(() => {
    const policy = document.querySelector('#system-idle-unload');
    policy.value = '900';
    policy.dispatchEvent(new Event('change', {bubbles: true}));
    const state = {
      text: document.querySelector('#apply-cleanup-policy').textContent,
      enabled: !document.querySelector('#apply-cleanup-policy').disabled
    };
    document.querySelector('#cleanup-policy-form').requestSubmit();
    return state;
  })()`);
  if (dirtyCleanup.text !== "Apply changes" || !dirtyCleanup.enabled) {
    throw new Error(`dirty-cleanup:${JSON.stringify(dirtyCleanup)}`);
  }
  checks += 2;
  await waitFor(() => cdp.evaluate(`(
    document.querySelector('#apply-cleanup-policy').disabled
    && document.querySelector('#apply-cleanup-policy').textContent === 'Applied'
  )`));
  const cleanupPolicy = await cdp.evaluate(`({
    status: document.querySelector('#cleanup-status').textContent,
    systemValue: document.querySelector('#system-idle-unload').value,
    advancedValue: document.querySelector('#idle-unload').value,
    wizardValue: document.querySelector('#wizard-idle-unload').value,
    buttonText: document.querySelector('#apply-cleanup-policy').textContent,
    buttonDisabled: document.querySelector('#apply-cleanup-policy').disabled,
    errorHidden: document.querySelector('#connection-error').classList.contains('hidden')
  })`);
  if (
    cleanupPolicy.status !== "Unload after 15 minutes idle"
    || cleanupPolicy.systemValue !== "900"
    || cleanupPolicy.advancedValue !== "900"
    || cleanupPolicy.wizardValue !== "900"
    || cleanupPolicy.buttonText !== "Applied"
    || !cleanupPolicy.buttonDisabled
    || !cleanupPolicy.errorHidden
  ) throw new Error(`cleanup-policy:${JSON.stringify(cleanupPolicy)}`);
  checks += 7;
  const requestsBeforeUnchangedCleanup = requests.length;
  await cdp.evaluate("document.querySelector('#cleanup-policy-form').requestSubmit()");
  await delay(150);
  if (requests.length !== requestsBeforeUnchangedCleanup) throw new Error("unchanged-cleanup-reconnected");
  checks += 1;
  trace("cleanup-policy-verified");

  const keyboardSubmit = await cdp.evaluate(`(() => {
    document.querySelector('#home-nav').click();
    document.querySelector('#prompt').value = 'browser flow';
    const shiftNotPrevented = document.querySelector('#prompt').dispatchEvent(
      new KeyboardEvent('keydown', {key: 'Enter', shiftKey: true, bubbles: true, cancelable: true})
    );
    const enterNotPrevented = document.querySelector('#prompt').dispatchEvent(
      new KeyboardEvent('keydown', {key: 'Enter', bubbles: true, cancelable: true})
    );
    return {shiftNotPrevented, enterNotPrevented};
  })()`);
  if (!keyboardSubmit.shiftNotPrevented || keyboardSubmit.enterNotPrevented) {
    throw new Error(`enter-submit-contract:${JSON.stringify(keyboardSubmit)}`);
  }
  checks += 2;
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

  await cdp.evaluate(`(() => {
    document.querySelector('#prompt').value = 'markdown showcase';
    document.querySelector('#text-form').requestSubmit();
  })()`);
  await waitFor(() => cdp.evaluate(
    "document.querySelector('.message:last-child .message-content h5')?.textContent.includes('Clear answer')",
  ));
  const markdown = await cdp.evaluate(`(() => {
    const content = document.querySelector('.message:last-child .message-content');
    return {
      heading: content.querySelector('h5')?.textContent || '',
      listItems: content.querySelectorAll('ul > li').length,
      strong: content.querySelector('strong')?.textContent || '',
      emphasis: content.querySelector('em')?.textContent || '',
      inlineCode: content.querySelector(':not(pre) > code')?.textContent || '',
      blockCode: content.querySelector('pre > code')?.textContent || '',
      language: content.querySelector('pre > code')?.dataset.language || '',
      quote: content.querySelector('blockquote')?.textContent || '',
      scripts: content.querySelectorAll('script, img').length,
      rawHtmlVisible: content.textContent.includes('<script>window.hostile = true</script>')
    };
  })()`);
  if (
    !markdown.heading.includes("😀")
    || markdown.listItems !== 2
    || markdown.strong !== "Strong point"
    || markdown.emphasis !== "emphasis"
    || markdown.inlineCode !== "inline code"
    || !markdown.blockCode.includes("<img src=x onerror=alert(1)>")
    || markdown.language !== "js"
    || markdown.quote !== "A useful note"
    || markdown.scripts !== 0
    || !markdown.rawHtmlVisible
  ) throw new Error(`safe-markdown-rendering:${JSON.stringify(markdown)}`);
  checks += 10;
  await cdp.call("Emulation.setDeviceMetricsOverride", {
    width: 540,
    height: 900,
    deviceScaleFactor: 1,
    mobile: false,
  });
  const responsiveMarkdown = await cdp.evaluate(`(() => {
    const content = document.querySelector('.message:last-child .message-content');
    const pre = content.querySelector('pre');
    return {
      contentWithinViewport: content.getBoundingClientRect().right <= window.innerWidth,
      codeWithinContent: pre.getBoundingClientRect().width <= content.getBoundingClientRect().width,
      codeOverflow: getComputedStyle(pre).overflowX
    };
  })()`);
  if (
    !responsiveMarkdown.contentWithinViewport
    || !responsiveMarkdown.codeWithinContent
    || responsiveMarkdown.codeOverflow !== "auto"
  ) throw new Error(`responsive-markdown:${JSON.stringify(responsiveMarkdown)}`);
  checks += 3;
  await cdp.call("Emulation.clearDeviceMetricsOverride");
  trace("safe-markdown-verified");

  const promptRecall = await cdp.evaluate(`(() => {
    const prompt = document.querySelector('#prompt');
    const key = (value) => prompt.dispatchEvent(
      new KeyboardEvent('keydown', {key: value, bubbles: true, cancelable: true})
    );
    prompt.value = 'unfinished draft';
    prompt.dispatchEvent(new Event('input', {bubbles: true}));
    prompt.setSelectionRange(0, 0);
    const firstUpPrevented = !key('ArrowUp');
    const first = prompt.value;
    const secondUpPrevented = !key('ArrowUp');
    const second = prompt.value;
    const firstDownPrevented = !key('ArrowDown');
    const newer = prompt.value;
    const secondDownPrevented = !key('ArrowDown');
    const draft = prompt.value;
    prompt.value = 'first line\\nsecond line';
    prompt.dispatchEvent(new Event('input', {bubbles: true}));
    prompt.setSelectionRange(prompt.value.length, prompt.value.length);
    const multilineUpNotPrevented = key('ArrowUp');
    const multiline = prompt.value;
    return {
      firstUpPrevented, first, secondUpPrevented, second,
      firstDownPrevented, newer, secondDownPrevented, draft,
      multilineUpNotPrevented, multiline
    };
  })()`);
  if (
    !promptRecall.firstUpPrevented
    || promptRecall.first !== "markdown showcase"
    || !promptRecall.secondUpPrevented
    || promptRecall.second !== "browser flow"
    || !promptRecall.firstDownPrevented
    || promptRecall.newer !== "markdown showcase"
    || !promptRecall.secondDownPrevented
    || promptRecall.draft !== "unfinished draft"
    || !promptRecall.multilineUpNotPrevented
    || promptRecall.multiline !== "first line\nsecond line"
  ) throw new Error(`prompt-recall:${JSON.stringify(promptRecall)}`);
  checks += 10;

  const configurableHistory = await cdp.evaluate(`(() => {
    const select = document.querySelector('#prompt-history-limit');
    const defaultValue = select.value;
    select.value = '50';
    select.dispatchEvent(new Event('change', {bubbles: true}));
    for (let index = 0; index < 55; index += 1) recordPromptHistory('bulk-' + index);
    const retained = state.promptHistory.length;
    const oldest = state.promptHistory[0];
    const newest = state.promptHistory.at(-1);
    const model = document.querySelector('#model');
    model.value = 'automatic';
    model.dispatchEvent(new Event('change', {bubbles: true}));
    return {
      defaultValue,
      configured: select.value,
      retained,
      oldest,
      newest,
      cleared: state.promptHistory.length,
      limitRetained: state.promptHistoryLimit,
      status: document.querySelector('#prompt-history-status').textContent
    };
  })()`);
  if (
    configurableHistory.defaultValue !== "20"
    || configurableHistory.configured !== "50"
    || configurableHistory.retained !== 50
    || configurableHistory.oldest !== "bulk-5"
    || configurableHistory.newest !== "bulk-54"
    || configurableHistory.cleared !== 0
    || configurableHistory.limitRetained !== 50
    || !configurableHistory.status.includes("0 of 50 prompts retained")
  ) throw new Error(`configurable-prompt-history:${JSON.stringify(configurableHistory)}`);
  checks += 8;
  trace("prompt-history-verified");

  const writingRequestsBefore = chatPayloads.length;
  const writingSuggestion = await cdp.evaluate(`(() => {
    state.modelSelections['content.write'] = {mode: 'manual', model: 'unknown-model:latest'};
    const conversationBefore = state.messages.length;
    const visibleMessagesBefore = document.querySelectorAll('#messages .message').length;
    document.querySelector('#prompt').value = 'Write a short welcome note.';
    document.querySelector('#text-form').requestSubmit();
    return {
      conversationBefore,
      visibleMessagesBefore,
      promptVisible: !document.querySelector('#model-switch-prompt').classList.contains('hidden'),
      description: document.querySelector('#model-switch-description').textContent,
      focused: document.activeElement.id,
      requestsUnchanged: ${writingRequestsBefore} === ${writingRequestsBefore}
    };
  })()`);
  await delay(100);
  if (
    !writingSuggestion.promptVisible
    || !writingSuggestion.description.includes("unknown-model:latest")
    || !writingSuggestion.description.includes("Nothing has been sent")
    || writingSuggestion.focused !== "use-recommended-model"
    || chatPayloads.length !== writingRequestsBefore
  ) throw new Error(`writing-model-suggestion:${JSON.stringify(writingSuggestion)}`);
  await cdp.evaluate("document.querySelector('#keep-current-model').click()");
  await waitFor(() => chatPayloads.length === writingRequestsBefore + 1);
  await waitFor(() => cdp.evaluate(
    "document.querySelector('#text-status').textContent.includes('response complete')",
  ));
  const writingPayload = chatPayloads.at(-1);
  const writingContinuity = await cdp.evaluate(`({
    conversationAfter: state.messages.length,
    visibleMessagesAfter: document.querySelectorAll('#messages .message').length,
    suggestionHidden: document.querySelector('#model-switch-prompt').classList.contains('hidden'),
    currentModel: document.querySelector('#model').value
  })`);
  if (
    writingPayload.model !== "qwen3.5:9b"
    || !writingPayload.messages[0].content.includes("Create the requested general-purpose content")
    || writingPayload.messages.length < writingSuggestion.conversationBefore + 2
    || writingContinuity.conversationAfter !== writingSuggestion.conversationBefore + 2
    || writingContinuity.visibleMessagesAfter !== writingSuggestion.visibleMessagesBefore + 2
    || !writingContinuity.suggestionHidden
    || writingContinuity.currentModel !== "automatic"
  ) throw new Error(`writing-conversation-continuity:${JSON.stringify(writingContinuity)}`);
  checks += 11;

  const summaryRequestsBefore = chatPayloads.length;
  await cdp.evaluate(`(() => {
    state.modelSelections['content.summarize'] = {mode: 'manual', model: 'unknown-model:latest'};
    document.querySelector('#prompt').value = 'Summarize the discussion so far.';
    document.querySelector('#text-form').requestSubmit();
  })()`);
  await delay(100);
  const summarySuggestion = await cdp.evaluate(`({
    visible: !document.querySelector('#model-switch-prompt').classList.contains('hidden'),
    conversationBefore: state.messages.length,
    visibleMessagesBefore: document.querySelectorAll('#messages .message').length
  })`);
  if (!summarySuggestion.visible || chatPayloads.length !== summaryRequestsBefore) {
    throw new Error(`summary-model-suggestion:${JSON.stringify(summarySuggestion)}`);
  }
  await cdp.evaluate("document.querySelector('#use-recommended-model').click()");
  await waitFor(() => chatPayloads.length === summaryRequestsBefore + 1);
  await waitFor(() => cdp.evaluate(
    "document.querySelector('#text-status').textContent.includes('response complete')",
  ));
  const summaryPayload = chatPayloads.at(-1);
  const summaryContinuity = await cdp.evaluate(`({
    conversationAfter: state.messages.length,
    visibleMessagesAfter: document.querySelectorAll('#messages .message').length,
    currentModel: document.querySelector('#model').value,
    suggestionHidden: document.querySelector('#model-switch-prompt').classList.contains('hidden')
  })`);
  if (
    summaryPayload.model !== "unknown-model:latest"
    || !summaryPayload.messages[0].content.includes("Summarize only the material supplied")
    || summaryPayload.messages.length < summarySuggestion.conversationBefore + 2
    || summaryContinuity.conversationAfter !== summarySuggestion.conversationBefore + 2
    || summaryContinuity.visibleMessagesAfter !== summarySuggestion.visibleMessagesBefore + 2
    || summaryContinuity.currentModel !== "manual:unknown-model:latest"
    || !summaryContinuity.suggestionHidden
  ) throw new Error(`summary-conversation-continuity:${JSON.stringify(summaryContinuity)}`);
  checks += 8;
  trace("unified-text-conversation-verified");

  const contextSelection = await cdp.evaluate(`(async () => {
    await addContextFiles([
      new File(
        ['# Browser context\\nThe project codename is Meadow.\\n<img src=x onerror=alert(1)>'],
        'notes.md',
        {type: 'text/markdown'}
      )
    ]);
    return {
      count: state.contextFiles.length,
      name: document.querySelector('.context-file-name')?.textContent || '',
      status: document.querySelector('#context-status').textContent,
      networkWarningHidden: document.querySelector('#context-network-warning').classList.contains('hidden'),
      policy: document.querySelector('.context-policy').textContent,
      preview: document.querySelector('.context-preview pre')?.textContent || '',
      activePreviewElements: document.querySelectorAll('.context-preview img, .context-preview script').length
    };
  })()`).then((value) => value);
  if (
    contextSelection.count !== 1
    || contextSelection.name !== "notes.md"
    || !contextSelection.status.includes("1 text file")
    || !contextSelection.status.includes("tokens")
    || !contextSelection.networkWarningHidden
    || !contextSelection.policy.includes("no paths")
    || !contextSelection.preview.includes("<img src=x onerror=alert(1)>")
    || contextSelection.activePreviewElements !== 0
  ) throw new Error(`context-selection:${JSON.stringify(contextSelection)}`);
  checks += 8;

  const invalidContextBlocked = await cdp.evaluate(`(async () => {
    try {
      await addContextAttachments([new File(['pdf'], 'unsafe.pdf', {type: 'application/pdf'})]);
      return false;
    } catch (error) {
      return error.message === 'invalid-context-file-type' && state.contextFiles.length === 1;
    }
  })()`);
  if (!invalidContextBlocked) throw new Error("invalid-context-file-not-blocked");
  const invalidUtf8Blocked = await cdp.evaluate(`(async () => {
    try {
      await addContextFiles([
        new File([new Uint8Array([0xff, 0xfe, 0xff])], 'invalid.txt', {type: 'text/plain'})
      ]);
      return false;
    } catch (error) {
      return error.message === 'invalid-context-file-content' && state.contextFiles.length === 1;
    }
  })()`);
  if (!invalidUtf8Blocked) throw new Error("invalid-context-utf8-not-blocked");
  const atomicMixedSelectionBlocked = await cdp.evaluate(`(async () => {
    const before = {
      files: state.contextFiles.map((item) => item.name),
      images: state.contextImages.map((item) => item.name)
    };
    try {
      await addContextAttachments([
        new File(['valid but must roll back'], 'rollback.md', {type: 'text/markdown'}),
        new File(['not really png'], 'hostile.png', {type: 'image/jpeg'})
      ]);
      return false;
    } catch (error) {
      return error.message === 'invalid-context-image-type'
        && JSON.stringify(before.files) === JSON.stringify(state.contextFiles.map((item) => item.name))
        && JSON.stringify(before.images) === JSON.stringify(state.contextImages.map((item) => item.name));
    }
  })()`);
  if (!atomicMixedSelectionBlocked) throw new Error("mixed-context-selection-not-atomic");
  const textLimitBlocked = await cdp.evaluate(`(async () => {
    const files = Array.from({length: 5}, (_, index) => (
      new File(['bounded'], 'extra-' + index + '.txt', {type: 'text/plain'})
    ));
    try {
      await addContextAttachments(files);
      return false;
    } catch (error) {
      return error.message === 'invalid-context-file-count'
        && state.contextFiles.length === 1
        && state.contextImages.length === 0;
    }
  })()`);
  if (!textLimitBlocked) throw new Error("unified-picker-text-limit-not-enforced");
  const duplicateSelectionBlocked = await cdp.evaluate(`(async () => {
    try {
      await addContextAttachments([
        new File(['duplicate'], state.contextFiles[0].name, {type: 'text/plain'})
      ]);
      return false;
    } catch (error) {
      return error.message === 'duplicate-context-file-name'
        && state.contextFiles.length === 1
        && state.contextImages.length === 0;
    }
  })()`);
  if (!duplicateSelectionBlocked) throw new Error("unified-picker-duplicate-not-enforced");
  checks += 5;

  const chatRequestsBeforeDisclosure = chatPayloads.length;
  const disclosureSubmit = await cdp.evaluate(`(() => {
    state.providerTrustScope = 'trusted-lan';
    renderContextFiles();
    const result = {
      warningVisible: !document.querySelector('#context-network-warning').classList.contains('hidden'),
      warning: document.querySelector('#context-network-warning').textContent,
      checkboxAbsent: document.querySelector('#context-consent') === null
    };
    document.querySelector('#prompt').value = 'Use the attached project notes.';
    document.querySelector('#text-form').requestSubmit();
    result.browseLockedDuringTask = document.querySelector('#context-files').disabled;
    result.browseButtonLockedDuringTask = document.querySelector('#browse-context').disabled;
    // The fixture provider is loopback; server-side trusted-LAN enforcement is
    // covered by the source integration suite. The request has already captured
    // submit-as-confirmation before this response-validation state is restored.
    state.providerTrustScope = 'loopback';
    return result;
  })()`);
  await waitFor(() => chatPayloads.length === chatRequestsBeforeDisclosure + 1);
  await waitFor(() => cdp.evaluate(
    "document.querySelector('#text-status').textContent.includes('response complete')",
  ));
  const browseRestoredAfterTask = await cdp.evaluate(
    "!document.querySelector('#context-files').disabled && !document.querySelector('#browse-context').disabled",
  );
  if (
    !disclosureSubmit.warningVisible
    || !disclosureSubmit.warning.includes("Pressing Send")
    || !disclosureSubmit.warning.includes("private-network Ollama server")
    || !disclosureSubmit.checkboxAbsent
    || !disclosureSubmit.browseLockedDuringTask
    || !disclosureSubmit.browseButtonLockedDuringTask
    || !browseRestoredAfterTask
    || chatPayloads.length !== chatRequestsBeforeDisclosure + 1
  ) throw new Error(`private-context-disclosure:${JSON.stringify(disclosureSubmit)}`);
  checks += 8;
  const contextPayload = chatPayloads.at(-1);
  if (
    !contextPayload.messages.at(-1).content.includes("untrusted reference material")
    || !contextPayload.messages.at(-1).content.includes("project codename is Meadow")
  ) throw new Error("context-provider-payload");
  const contextAfterSend = await cdp.evaluate(`(() => {
    const beforeRemove = state.contextFiles.length;
    document.querySelector('.remove-context-file').click();
    const afterRemove = state.contextFiles.length;
    const status = document.querySelector('#context-status').textContent;
    state.providerTrustScope = 'loopback';
    renderContextFiles();
    return {beforeRemove, afterRemove, status};
  })()`);
  if (
    contextAfterSend.beforeRemove !== 1
    || contextAfterSend.afterRemove !== 0
    || !contextAfterSend.status.includes("No files or screenshots selected")
  ) throw new Error(`context-cleanup:${JSON.stringify(contextAfterSend)}`);
  checks += 3;

  const screenshotPaste = await cdp.evaluate(`(() => {
    const encoded = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=';
    const bytes = Uint8Array.from(atob(encoded), (value) => value.charCodeAt(0));
    const clipboard = new DataTransfer();
    clipboard.items.add(new File([bytes], 'clipboard.png', {type: 'image/png'}));
    const notPrevented = document.dispatchEvent(
      new ClipboardEvent('paste', {clipboardData: clipboard, bubbles: true, cancelable: true})
    );
    return {notPrevented};
  })()`);
  await waitFor(() => cdp.evaluate("state.contextImages.length === 1"));
  const screenshotUi = await cdp.evaluate(`({
    count: state.contextImages.length,
    name: document.querySelector('.context-image-meta strong')?.textContent || '',
    thumbnail: document.querySelector('.context-image img')?.src || '',
    alt: document.querySelector('.context-image img')?.alt || '',
    status: document.querySelector('#context-status').textContent,
    warning: document.querySelector('#context-image-warning').textContent,
    warningVisible: !document.querySelector('#context-image-warning').classList.contains('hidden')
  })`);
  if (
    screenshotPaste.notPrevented
    || screenshotUi.count !== 1
    || screenshotUi.name !== "clipboard-screenshot-1.png"
    || !screenshotUi.thumbnail.startsWith("data:image/png;base64,")
    || screenshotUi.alt !== "Screenshot 1: clipboard-screenshot-1.png"
    || !screenshotUi.status.includes("1 screenshot")
    || !screenshotUi.warningVisible
    || !screenshotUi.warning.includes("unverified")
  ) throw new Error(`screenshot-paste:${JSON.stringify({screenshotPaste, screenshotUi})}`);
  const unsupportedScreenshotBlocked = await cdp.evaluate(`(async () => {
    try {
      await addContextImage(new Blob(['jpeg'], {type: 'image/jpeg'}));
      return false;
    } catch (error) {
      return error.message === 'invalid-context-image-type' && state.contextImages.length === 1;
    }
  })()`);
  if (!unsupportedScreenshotBlocked) throw new Error("unsupported-screenshot-not-blocked");
  checks += 9;

  const chatRequestsBeforeScreenshot = chatPayloads.length;
  await cdp.evaluate(`(() => {
    document.querySelector('#prompt').value = 'Describe the pasted screenshot.';
    document.querySelector('#text-form').requestSubmit();
  })()`);
  await waitFor(() => chatPayloads.length === chatRequestsBeforeScreenshot + 1);
  await waitFor(() => cdp.evaluate(
    "document.querySelector('#task-event').textContent.includes('screenshot understanding is unverified')",
  ));
  const screenshotPayload = chatPayloads.at(-1);
  if (
    !Array.isArray(screenshotPayload.messages.at(-1).images)
    || screenshotPayload.messages.at(-1).images.length !== 1
    || !screenshotPayload.messages.at(-1).images[0].startsWith("iVBOR")
  ) throw new Error("screenshot-provider-payload");
  const screenshotCleanup = await cdp.evaluate(`(() => {
    document.querySelector('.remove-context-image').click();
    return {
      count: state.contextImages.length,
      thumbnailCount: document.querySelectorAll('.context-image img').length,
      status: document.querySelector('#context-status').textContent
    };
  })()`);
  if (
    screenshotCleanup.count !== 0
    || screenshotCleanup.thumbnailCount !== 0
    || !screenshotCleanup.status.includes("No files or screenshots selected")
  ) throw new Error(`screenshot-cleanup:${JSON.stringify(screenshotCleanup)}`);
  checks += 4;

  const screenshotBrowseControl = await cdp.evaluate(`(() => {
    const encoded = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=';
    const bytes = Uint8Array.from(atob(encoded), (value) => value.charCodeAt(0));
    const transfer = new DataTransfer();
    transfer.items.add(new File(['mixed context'], 'selected-notes.md', {type: 'text/markdown'}));
    transfer.items.add(new File([bytes], 'selected-screen.png', {type: 'image/png'}));
    const input = document.querySelector('#context-files');
    input.files = transfer.files;
    input.dispatchEvent(new Event('change', {bubbles: true}));
    return {accept: input.accept, multiple: input.multiple};
  })()`);
  await waitFor(() => cdp.evaluate("state.contextFiles.length === 1 && state.contextImages.length === 1"));
  const screenshotBrowse = await cdp.evaluate(`({
    fileCount: state.contextFiles.length,
    fileName: document.querySelector('.context-file-name')?.textContent || '',
    count: state.contextImages.length,
    name: document.querySelector('.context-image-meta strong')?.textContent || '',
    alt: document.querySelector('.context-image img')?.alt || '',
    thumbnail: document.querySelector('.context-image img')?.src || ''
  })`);
  if (
    screenshotBrowseControl.accept !== ".txt,.md,.png,text/plain,text/markdown,image/png"
    || !screenshotBrowseControl.multiple
    || screenshotBrowse.fileCount !== 1
    || screenshotBrowse.fileName !== "selected-notes.md"
    || screenshotBrowse.count !== 1
    || screenshotBrowse.name !== "selected-screen.png"
    || screenshotBrowse.alt !== "Screenshot 1: selected-screen.png"
    || !screenshotBrowse.thumbnail.startsWith("data:image/png;base64,")
  ) throw new Error(`screenshot-browse:${JSON.stringify({screenshotBrowseControl, screenshotBrowse})}`);
  await cdp.call("Emulation.setDeviceMetricsOverride", {
    width: 1400,
    height: 580,
    deviceScaleFactor: 1,
    mobile: false,
  });
  await delay(50);
  const attachmentLayout = await cdp.evaluate(`(() => {
    const panel = document.querySelector('#text-panel').getBoundingClientRect();
    const context = document.querySelector('.context-panel');
    const contextBox = context.getBoundingClientRect();
    const composer = document.querySelector('#text-form').getBoundingClientRect();
    return {
      composerInsidePanel: composer.top >= panel.top && composer.bottom <= panel.bottom + 1,
      contextHeight: contextBox.height,
      contextScrollable: context.scrollHeight > context.clientHeight,
      contextOverflow: getComputedStyle(context).overflowY,
      messageMinHeight: getComputedStyle(document.querySelector('#messages')).minHeight
    };
  })()`);
  await cdp.call("Emulation.clearDeviceMetricsOverride");
  if (
    !attachmentLayout.composerInsidePanel
    || attachmentLayout.contextHeight > 191
    || !attachmentLayout.contextScrollable
    || attachmentLayout.contextOverflow !== "auto"
    || attachmentLayout.messageMinHeight !== "0px"
  ) throw new Error(`attachment-layout:${JSON.stringify(attachmentLayout)}`);
  const documentContextBrowseCleanup = await cdp.evaluate(`(() => {
    document.querySelector('#clear-context').click();
    return {files: state.contextFiles.length, images: state.contextImages.length};
  })()`);
  if (documentContextBrowseCleanup.files !== 0 || documentContextBrowseCleanup.images !== 0) {
    throw new Error("screenshot-browse-cleanup");
  }
  checks += 13;
  trace("document-context-verified");

  await cdp.evaluate("document.querySelector('#software-nav').click()");
  await waitFor(() => cdp.evaluate("!document.querySelector('#workflow-select').disabled"));
  await cdp.evaluate("document.querySelector('#workflow-plan-button').click()");
  await waitFor(() => cdp.evaluate("!document.querySelector('#workflow-result').classList.contains('hidden')"));
  const workflow = await cdp.evaluate(`({
    title: document.querySelector('#workflow-result-title').textContent,
    policy: document.querySelector('#workflow-result-policy').textContent,
    textHidden: document.querySelector('#text-panel').classList.contains('hidden'),
    active: document.querySelector('#software-nav').classList.contains('active'),
    focused: document.activeElement.id,
    busy: document.querySelector('#software-panel').getAttribute('aria-busy'),
    visiblePanels: [...document.querySelectorAll('.chat-panel')].filter((item) => getComputedStyle(item).display !== 'none').length,
    headingInside: document.querySelector('#software-panel .panel-heading').getBoundingClientRect().top
      >= document.querySelector('#software-panel').getBoundingClientRect().top
  })`);
  if (
    !workflow.title
    || !workflow.policy.includes("No process started")
    || !workflow.policy.includes("no file write")
    || !workflow.textHidden
    || !workflow.active
    || workflow.focused !== "workflow-result-title"
    || workflow.busy !== "false"
    || workflow.visiblePanels !== 1
    || !workflow.headingInside
  ) throw new Error(`workflow-plan-rendering:${JSON.stringify(workflow)}`);
  checks += 9;
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
    download: document.querySelector('#image-download').getAttribute('download'),
    active: document.querySelector('#image-nav').classList.contains('active'),
    focused: document.activeElement.id,
    busy: document.querySelector('#image-panel').getAttribute('aria-busy'),
    visiblePanels: [...document.querySelectorAll('.chat-panel')].filter((item) => getComputedStyle(item).display !== 'none').length,
    headingInside: document.querySelector('#image-panel .panel-heading').getBoundingClientRect().top
      >= document.querySelector('#image-panel').getBoundingClientRect().top
  })`);
  if (
    !imageResult.badge.includes("loopback")
    || !imageResult.summary.includes("512 × 512")
    || !imageResult.summary.includes("provider copy retained")
    || !imageResult.source.startsWith("data:image/png;base64,")
    || imageResult.download !== "haven42-generated-image.png"
    || !imageResult.active
    || imageResult.focused !== "image-preview"
    || imageResult.busy !== "false"
    || imageResult.visiblePanels !== 1
    || !imageResult.headingInside
  ) throw new Error(`image-result-rendering:${JSON.stringify(imageResult)}`);
  checks += 10;
  trace("image-flow-verified");

  await cdp.call("Emulation.setEmulatedMedia", {
    media: "screen",
    features: [{name: "prefers-reduced-motion", value: "reduce"}],
  });
  const navigation = await cdp.evaluate(`(() => {
    const reducedMotion = motionBehavior();
    document.querySelector('#models-nav').click();
    const models = {
      active: document.querySelector('#models-nav').classList.contains('active'),
      focused: document.activeElement.id,
      visible: !document.querySelector('#models-panel').classList.contains('hidden'),
      imageHidden: document.querySelector('#image-panel').classList.contains('hidden'),
      installed: document.querySelectorAll('#model-search-results .model-search-result').length,
    };
    document.querySelector('#system-nav').click();
    const system = {
      active: document.querySelector('#system-nav').classList.contains('active'),
      focused: document.activeElement.id,
    };
    document.querySelector('#about-nav').click();
    const about = {
      active: document.querySelector('#about-nav').classList.contains('active'),
      visible: !document.querySelector('#about-panel').classList.contains('hidden'),
      modelsHidden: document.querySelector('#models-panel').classList.contains('hidden'),
      focused: document.activeElement.id,
      version: document.querySelector('#about-version').textContent,
    };
    return {reducedMotion, models, system, about};
  })()`);
  if (
    navigation.reducedMotion !== "auto"
    || !navigation.models.active
    || navigation.models.focused !== "models-title"
    || !navigation.models.visible
    || !navigation.models.imageHidden
    || navigation.models.installed !== 2
    || !navigation.system.active
    || navigation.system.focused !== "system-title"
    || !navigation.about.active
    || !navigation.about.visible
    || !navigation.about.modelsHidden
    || navigation.about.focused !== "about-title"
    || !navigation.about.version.startsWith("v")
  ) throw new Error(`accessible-navigation:${JSON.stringify(navigation)}`);
  checks += 13;
  trace("accessible-navigation-verified");

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
      .some((item) => item.textContent === 'force browser failure'),
    focused: document.activeElement.id
  })`);
  if (
    recovery.prompt !== "force browser failure"
    || !recovery.task.includes("retry creates a new request")
    || recovery.failedUserMessageVisible
    || recovery.focused !== "connection-error"
    || loaded.size !== 0
  ) throw new Error(`failure-recovery:${JSON.stringify(recovery)}`);
  checks += 5;
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
