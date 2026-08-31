#!/usr/bin/env node
import { spawn, spawnSync } from "node:child_process";
import { createServer } from "node:http";
import { existsSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";
import { deflateSync } from "node:zlib";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const QWEN_DIGEST = "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7";

function crc32(data) {
  let crc = 0xffffffff;
  for (const byte of data) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit += 1) {
      crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function pngChunk(type, payload) {
  const typeBytes = Buffer.from(type, "ascii");
  const length = Buffer.alloc(4);
  length.writeUInt32BE(payload.length);
  const checksum = Buffer.alloc(4);
  checksum.writeUInt32BE(crc32(Buffer.concat([typeBytes, payload])));
  return Buffer.concat([length, typeBytes, payload, checksum]);
}

function testPng(width, height) {
  const header = Buffer.alloc(13);
  header.writeUInt32BE(width, 0);
  header.writeUInt32BE(height, 4);
  header.set([8, 0, 0, 0, 0], 8);
  const scanlines = Buffer.alloc((width + 1) * height);
  return Buffer.concat([
    Buffer.from("89504e470d0a1a0a", "hex"),
    pngChunk("IHDR", header),
    pngChunk("IDAT", deflateSync(scanlines)),
    pngChunk("IEND", Buffer.alloc(0)),
  ]);
}

const TEST_PNG = testPng(512, 512);
const LOCAL_WEB_STARTUP_TIMEOUT_MS = 45000;
let models = ["qwen3.5:9b", "unknown-model:latest"];
const loaded = new Set();
const requests = [];
const chatPayloads = [];
let cancelledChatConnections = 0;
const providerAuthorization = [];
let requiredOllamaAuthorization = null;
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
  if (["/api/version", "/api/tags", "/api/ps", "/api/chat", "/api/generate"].includes(request.url)) {
    providerAuthorization.push([request.method, request.url, request.headers.authorization || null]);
    if (requiredOllamaAuthorization !== null && request.headers.authorization !== requiredOllamaAuthorization) {
      return json(response, 401, { error: "authentication-required" });
    }
  }
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
      if (payload.messages?.at(-1)?.content === "stop browser generation") {
        response.writeHead(200, { "Content-Type": "application/x-ndjson" });
        response.write(`${JSON.stringify({ message: { role: "assistant", content: "partial" }, done: false })}\n`);
        const completion = setTimeout(() => {
          if (!response.destroyed) response.end(`${JSON.stringify({ message: { role: "assistant", content: "late" }, done: true })}\n`);
        }, 10000);
        completion.unref();
        response.once("close", () => {
          clearTimeout(completion);
          cancelledChatConnections += 1;
        });
        return;
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

function resolveBrowserProfileRoot(browserPath) {
  if (
    process.platform === "linux"
    && ["/usr/bin/chromium-browser", "/snap/bin/chromium"].includes(browserPath)
    && existsSync("/snap/bin/chromium")
  ) {
    const snapCommon = join(homedir(), "snap", "chromium", "common");
    if (existsSync(snapCommon)) return snapCommon;
  }
  return tmpdir();
}

async function waitFor(getter, timeoutMs = 45000) {
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

async function trustedClick(cdp, selector) {
  const point = await cdp.evaluate(`(() => {
    const element = document.querySelector(${JSON.stringify(selector)});
    const rect = element.getBoundingClientRect();
    return {x: rect.left + rect.width / 2, y: rect.top + rect.height / 2};
  })()`);
  await cdp.call("Input.dispatchMouseEvent", {
    type: "mouseMoved", x: point.x, y: point.y,
    button: "none", buttons: 0, pointerType: "mouse",
  });
  await cdp.call("Input.dispatchMouseEvent", {
    type: "mousePressed", x: point.x, y: point.y,
    button: "left", buttons: 1, clickCount: 1, pointerType: "mouse",
  });
  await cdp.call("Input.dispatchMouseEvent", {
    type: "mouseReleased", x: point.x, y: point.y,
    button: "left", buttons: 0, clickCount: 1, pointerType: "mouse",
  });
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
// Strictly confined Snap Chromium sees a private /tmp. Keep its disposable
// profile in Snap's user-owned common directory so the host test process can
// read DevToolsActivePort, then remove the profile in the normal cleanup path.
const profile = mkdtempSync(join(resolveBrowserProfileRoot(browserPath), "haven42-browser-"));
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
    : [...python.prefix, "-u", join(ROOT, "scripts", "run-haven42-web-browser-test.py")];
  haven = spawn(havenCommand, havenArguments, {
    cwd: packagedExecutable ? dirname(packagedExecutable) : ROOT,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });
  let output = "";
  let errorOutput = "";
  let havenLaunchError;
  haven.stdout.on("data", (chunk) => { output += chunk.toString(); });
  haven.stderr.on("data", (chunk) => {
    errorOutput = `${errorOutput}${chunk.toString()}`.slice(-4000);
  });
  haven.once("error", (error) => { havenLaunchError = error; });
  const startup = await waitFor(() => {
    const origin = output.match(/http:\/\/127\.0\.0\.1:\d+/)?.[0];
    if (origin) return { origin };
    if (havenLaunchError) return { error: `local-web-launch-error:${havenLaunchError.message}` };
    if (haven.exitCode !== null) {
      const detail = errorOutput.trim().replace(/\s+/g, " ").slice(-1000) || "no-stderr";
      return { error: `local-web-exited-${haven.exitCode}:${detail}` };
    }
    return null;
  }, LOCAL_WEB_STARTUP_TIMEOUT_MS);
  if (startup.error) throw new Error(startup.error);
  const { origin } = startup;
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
    progressMarkers: document.querySelectorAll('[data-wizard-progress]').length,
    focused: document.activeElement.classList.contains('wizard-card'),
    skip: Boolean(document.querySelector('.skip-link'))
  })`);
  if (initial.modal !== "true" || initial.current !== "welcome" || initial.progressMarkers !== 3 || !initial.focused || !initial.skip) throw new Error("initial-accessibility-state");
  checks += 5;
  const accessibility = await cdp.evaluate(`(() => {
    const guided = document.querySelector('#wizard-guided');
    guided.focus();
    const focusedStyle = getComputedStyle(guided);
    return {
      navLandmarks: document.querySelectorAll('nav').length,
      mainLandmarks: document.querySelectorAll('main').length,
      complementaryLandmarks: document.querySelectorAll('aside').length,
      pageHeadings: document.querySelectorAll('h1').length,
      skipTarget: document.querySelector('.skip-link').getAttribute('href'),
      targetHeight: guided.getBoundingClientRect().height,
      focusOutlineWidth: focusedStyle.outlineWidth,
      focusOutlineStyle: focusedStyle.outlineStyle,
      endpointDescription: document.querySelector('#endpoint').getAttribute('aria-describedby'),
      wizardEndpointDescription: document.querySelector('#wizard-endpoint').getAttribute('aria-describedby'),
      hiddenFileTabIndex: document.querySelector('#context-files').tabIndex,
      liveMetricsRole: document.querySelector('#resource-status-announcement').getAttribute('role'),
      liveMetricsMode: document.querySelector('#resource-status-announcement').getAttribute('aria-live'),
      statusAtomic: document.querySelector('#connection-badge').getAttribute('aria-atomic'),
    };
  })()`);
  if (
    accessibility.navLandmarks !== 1
    || accessibility.mainLandmarks !== 1
    || accessibility.complementaryLandmarks !== 1
    || accessibility.pageHeadings !== 1
    || accessibility.skipTarget !== "#main-content"
    || accessibility.targetHeight < 44
    || Number.parseFloat(accessibility.focusOutlineWidth) < 3
    || accessibility.focusOutlineStyle === "none"
    || !accessibility.endpointDescription.includes("connection-error")
    || !accessibility.wizardEndpointDescription.includes("wizard-error")
    || accessibility.hiddenFileTabIndex !== -1
    || accessibility.liveMetricsRole !== "status"
    || accessibility.liveMetricsMode !== "polite"
    || accessibility.statusAtomic !== "true"
  ) throw new Error(`wcag-structure:${JSON.stringify(accessibility)}`);
  checks += 14;
  const escapeDismissal = await cdp.evaluate(`(() => {
    const card = document.querySelector('.wizard-card');
    card.focus();
    card.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true, cancelable: true}));
    const result = {
      hidden: document.querySelector('#setup-wizard').classList.contains('hidden'),
      focus: document.activeElement.id,
    };
    document.querySelector('#setup-wizard').classList.remove('hidden');
    showWizardStep('welcome');
    document.querySelector('.wizard-card').focus();
    return result;
  })()`);
  if (!escapeDismissal.hidden || escapeDismissal.focus !== "home-nav") {
    throw new Error(`escape-dismissal:${JSON.stringify(escapeDismissal)}`);
  }
  checks += 2;
  trace("welcome-verified");

  await waitFor(() => cdp.evaluate("document.querySelector('#assurance-badge').textContent === 'Committed evidence'"));
  const assurance = await cdp.evaluate(`({
    badge: document.querySelector('#assurance-badge').textContent,
    records: Number(document.querySelector('#assurance-record-count').textContent),
    models: Number(document.querySelector('#assurance-model-count').textContent),
    surfaces: Number(document.querySelector('#assurance-surface-count').textContent),
    live: document.querySelector('#assurance-live-status').textContent,
    statusRows: document.querySelectorAll('#assurance-status-list .assurance-status-item').length,
    statusTotal: [...document.querySelectorAll('#assurance-status-list .assurance-status-item strong')].reduce((total, item) => total + Number(item.textContent), 0),
    rows: document.querySelectorAll('#assurance-surface-list .assurance-item').length,
    candidateRows: document.querySelectorAll('#assurance-surface-list .assurance-state.candidate').length,
    activityDetails: [...document.querySelectorAll('#assurance-surface-list .assurance-item > div small')].every((item) => item.textContent.includes('supported') && item.textContent.includes('validated') && item.textContent.includes('blocked')),
    wikiHref: document.querySelector('.assurance-wiki-link').href,
    wikiTarget: document.querySelector('.assurance-wiki-link').target,
    wikiRel: document.querySelector('.assurance-wiki-link').rel,
    wikiReferrer: document.querySelector('.assurance-wiki-link').referrerPolicy,
    disclosure: document.querySelector('#assurance-panel .field-help').textContent
  })`);
  if (
    assurance.badge !== "Committed evidence"
    || assurance.records < 1
    || assurance.models < 1
    || assurance.surfaces !== 4
    || assurance.live !== "Not run · read-only summary"
    || assurance.statusRows < 1
    || assurance.statusTotal !== assurance.records
    || assurance.rows !== assurance.surfaces
    || assurance.candidateRows !== 2
    || !assurance.activityDetails
    || assurance.wikiHref !== "https://github.com/hysel/haven-42/wiki/Model-And-Hardware-Test-Status"
    || assurance.wikiTarget !== "_blank"
    || !assurance.wikiRel.includes("noopener")
    || !assurance.wikiRel.includes("noreferrer")
    || assurance.wikiReferrer !== "no-referrer"
    || !assurance.disclosure.includes("does not start AI")
  ) throw new Error(`assurance-view:${JSON.stringify(assurance)}`);
  checks += 17;
  trace("assurance-view-verified");

  const macosGuidedPresentation = await cdp.evaluate(`(() => {
    const originalPlatform = state.platformFamily;
    state.platformFamily = 'macos';
    const snapshot = {
      platform: {
        operatingSystem: 'macos', architecture: 'arm64', logicalProcessors: 10,
        systemMemoryGiB: 16, availableStorageGiB: 160,
        productName: 'Mac mini · Apple M4', buildNumber: null,
      },
      accelerators: [{vendor: 'Apple', model: 'Apple M4', memoryGiB: null, driverName: null, driverVersion: null}],
      software: [
        {componentId: 'python', state: 'validated', version: '3.14.6'},
        {componentId: 'ollama', state: 'not-detected', version: null},
      ],
    };
    const plan = {
      hardwareAssessment: {candidateModel: 'qwen3.5:9b'},
      actions: [],
      alphaCandidate: {
        modelSelection: {selected: {name: 'qwen3.5:9b'}, automaticExecutionAllowed: false},
        managedSetupCandidateAvailable: false,
        runtimeCompatibility: null,
        driverGuidance: [],
      },
    };
    renderSystemReadiness('wizard-system-readiness', snapshot);
    renderSetupPlan(plan);
    updateReadinessNextControl(false, false);
    const link = document.querySelector('#wizard-setup-plan a[href="https://ollama.com/download/mac"]');
    const result = {
      facts: document.querySelector('#wizard-system-readiness').textContent,
      explanation: document.querySelector('#wizard-setup-plan').textContent,
      linkText: link?.textContent,
      linkTarget: link?.target,
      linkRel: link?.rel,
      linkReferrer: link?.referrerPolicy,
      nextDisabled: document.querySelector('#wizard-readiness-next').disabled,
      nextText: document.querySelector('#wizard-readiness-next').textContent,
    };
    state.platformFamily = originalPlatform;
    return result;
  })()`);
  if (
    !macosGuidedPresentation.facts.includes('Operating systemmacOS · arm64')
    || !macosGuidedPresentation.facts.includes('Mac modelMac mini · Apple M4')
    || !macosGuidedPresentation.facts.includes('System Ollamanot-detected')
    || !macosGuidedPresentation.explanation.includes('did not find an official Ollama app it could verify')
    || macosGuidedPresentation.linkText !== 'Install Ollama for macOS'
    || macosGuidedPresentation.linkTarget !== '_blank'
    || !macosGuidedPresentation.linkRel.includes('noopener')
    || !macosGuidedPresentation.linkRel.includes('noreferrer')
    || macosGuidedPresentation.linkReferrer !== 'no-referrer'
    || macosGuidedPresentation.nextDisabled
    || macosGuidedPresentation.nextText !== "I've installed Ollama — check again"
  ) throw new Error(`macos-guided-setup:${JSON.stringify(macosGuidedPresentation)}`);
  checks += 10;
  trace("macos-guided-setup-verified");

  const macosInstalledPresentation = await cdp.evaluate(`(() => {
    const originalPlatform = state.platformFamily;
    state.platformFamily = 'macos';
    const effects = [
      "Verify the installed Ollama app's code signature and Gatekeeper approval.",
      "Start its local AI engine on this computer for this Haven 42 session only.",
      "Use the current macOS user's existing Ollama model storage; do not download a model yet.",
    ];
    renderSetupPlan({
      hardwareAssessment: {candidateModel: 'qwen3.5:9b'},
      actions: [],
      alphaCandidate: {
        modelSelection: {selected: {name: 'qwen3.5:9b'}, automaticExecutionAllowed: false},
        managedSetupCandidateAvailable: false,
        runtimeCompatibility: null,
        driverGuidance: [],
        macosInstalledRuntime: {
          available: true,
          plan: {planId: 'fixed-test-plan', version: '0.33.2', effects},
        },
      },
    });
    updateReadinessNextControl(false, true);
    const review = [...document.querySelectorAll('#wizard-setup-plan button')]
      .find((item) => item.textContent === 'Review and start local AI');
    review.click();
    const approval = document.querySelector('#wizard-setup-plan .setup-approval');
    const result = {
      explanation: document.querySelector('#wizard-setup-plan').textContent,
      reviewText: review.textContent,
      approvalVisible: !approval.classList.contains('hidden'),
      effectCount: approval.querySelectorAll('li').length,
      consentText: approval.querySelector('.setup-consent').textContent,
      approveDisabled: [...approval.querySelectorAll('button')]
        .find((item) => item.textContent === 'Approve and start').disabled,
      installLinkPresent: Boolean(document.querySelector('#wizard-setup-plan a[href="https://ollama.com/download/mac"]')),
      nextDisabled: document.querySelector('#wizard-readiness-next').disabled,
      nextText: document.querySelector('#wizard-readiness-next').textContent,
    };
    state.platformFamily = originalPlatform;
    return result;
  })()`);
  if (
    !macosInstalledPresentation.explanation.includes('found Ollama 0.33.2 in Applications')
    || !macosInstalledPresentation.explanation.includes('No app or model will be downloaded')
    || macosInstalledPresentation.reviewText !== 'Review and start local AI'
    || !macosInstalledPresentation.approvalVisible
    || macosInstalledPresentation.effectCount !== 3
    || !macosInstalledPresentation.consentText.includes('allow Haven 42 to start')
    || !macosInstalledPresentation.approveDisabled
    || macosInstalledPresentation.installLinkPresent
    || !macosInstalledPresentation.nextDisabled
    || macosInstalledPresentation.nextText !== 'Start local AI above'
  ) throw new Error(`macos-installed-setup:${JSON.stringify(macosInstalledPresentation)}`);
  checks += 10;
  trace("macos-installed-setup-verified");

  const setupPlanningHost = ["win32", "linux", "darwin"].includes(process.platform);
  if (setupPlanningHost) {
  await cdp.evaluate("document.querySelector('#wizard-guided').click()");
  await waitFor(() => cdp.evaluate("document.querySelectorAll('#wizard-setup-plan .plan-action').length >= 2"));
  await waitFor(() => cdp.evaluate(`
    !document.querySelector('#alpha-installation-panel')
    || document.querySelectorAll('#alpha-installation-components .installation-component').length >= 2
  `));
  const guided = await cdp.evaluate(`({
    current: document.querySelector('[aria-current="step"]').dataset.wizardProgress,
    facts: document.querySelectorAll('#wizard-system-readiness .readiness-fact').length,
    factsText: document.querySelector('#wizard-system-readiness').textContent,
    planActions: document.querySelectorAll('#wizard-setup-plan .plan-action').length,
    planText: document.querySelector('#wizard-setup-plan').textContent,
    installationPanel: Boolean(document.querySelector('#alpha-installation-panel')),
    installationRows: document.querySelectorAll('#alpha-installation-components .installation-component').length,
    installationProgressBars: document.querySelectorAll('#alpha-installation-panel progress').length,
    macosInstallLink: Boolean(document.querySelector('#wizard-setup-plan a[href="https://ollama.com/download/mac"]')),
    nextDisabled: document.querySelector('#wizard-readiness-next').disabled,
    nextText: document.querySelector('#wizard-readiness-next').textContent,
    status: document.querySelector('#wizard-scan-status').textContent
  })`);
  const detectedAmd = /Accelerator\s*AMD\b/i.test(guided.factsText);
  const detectedNvidia = /Accelerator\s*NVIDIA\b/i.test(guided.factsText);
  const detectedIntel = /Accelerator\s*Intel\b/i.test(guided.factsText);
  const showsAmdTools = guided.factsText.includes("AMD graphics tools");
  const showsNvidiaTools = guided.factsText.includes("NVIDIA tools");
  const showsIntelTools = guided.factsText.includes("Intel oneAPI tools");
  const storageBoundaryText = process.platform === "win32"
    ? "Does not use Program Files or AppData"
    : "Does not use system application folders";
  if (
    guided.current !== "middle"
    || guided.facts < 4
    || !/^Operating system\S+/i.test(guided.factsText)
    || !guided.factsText.includes("Embedded Python runtime")
    || showsAmdTools !== detectedAmd
    || showsNvidiaTools !== detectedNvidia
    || showsIntelTools !== detectedIntel
    || guided.planActions < 2
    || !guided.planText.includes("Haven 42 checked your computer")
    || !guided.status.includes("Nothing was installed")
  ) throw new Error(`guided-readiness:${JSON.stringify(guided)}`);
  if (
    guided.installationPanel
    && (
      !guided.nextDisabled
      || guided.nextText !== "Complete setup above"
      || guided.installationRows < 2
      || guided.installationProgressBars !== guided.installationRows + 1
      || !guided.planText.includes("What Haven 42 needs")
      || !guided.planText.includes("local AI model for chat, writing, and summaries")
      || !guided.planText.includes("Technical model name")
      || !guided.planText.includes("Install location")
      || !guided.planText.includes("stored beside the app")
      || !guided.planText.includes("Haven42-Data")
      || !guided.planText.includes(storageBoundaryText)
      || !(
        guided.planText.includes("Ollama local AI engine")
        || guided.planText.includes("Ollama local runtime")
      )
      || !guided.planText.includes("Download:")
      || !guided.planText.includes("Required to run the selected text model locally")
      || !guided.planText.includes("Download and safety details")
      || (detectedAmd && !guided.planText.includes("AMD GPU acceleration · ROCm 7.1"))
      || (detectedAmd && !guided.planText.includes("Ollama 0.32.14 AMD support package"))
    )
  ) throw new Error(`guided-installation-progress:${JSON.stringify(guided)}`);
  if (
    process.platform === "darwin"
    && guided.macosInstallLink
    && (
      guided.nextDisabled
      || guided.nextText !== "I've installed Ollama — check again"
    )
  ) {
    throw new Error(`guided-macos-external-setup:${JSON.stringify(guided)}`);
  }
  if (
    process.platform === "darwin"
    && !guided.macosInstallLink
    && (
      !guided.nextDisabled
      || guided.nextText !== "Local setup unavailable"
      || !guided.planText.includes("could not safely choose a local AI model")
    )
  ) {
    throw new Error(`guided-macos-no-fitting-model:${JSON.stringify(guided)}`);
  }
  if (
    process.platform !== "darwin"
    && !guided.installationPanel
    && (!guided.nextDisabled || guided.nextText !== "Local setup unavailable")
  ) {
    throw new Error(`guided-manual-connection:${JSON.stringify(guided)}`);
  }
  if (guided.installationPanel) {
    const reusePresentation = await cdp.evaluate(`(async () => {
      const response = await fetch('/api/alpha/setup-status', {credentials: 'same-origin', cache: 'no-store'});
      const status = await response.json();
      const reusable = {
        ...status,
        completedSetupCandidate: true,
        components: status.components.map((item) => ({...item, state: 'present', progressPercent: 100})),
      };
      renderAlphaSetupProgress(reusable);
      updateManagedSetupAvailability(reusable);
      const result = {
        buttonText: document.querySelector('#alpha-setup-review').textContent,
        buttonMode: document.querySelector('#alpha-setup-review').dataset.mode,
        manualHidden: document.querySelector('#alpha-setup-manual').hidden,
        disclosure: document.querySelector('#alpha-setup-storage-summary').textContent,
        progress: document.querySelector('#alpha-setup-progress').textContent,
        approvalHidden: document.querySelector('#alpha-setup-approval').classList.contains('hidden'),
        installedChecks: document.querySelectorAll('.installation-component-check').length,
      };
      await refreshAlphaSetupProgress();
      return result;
    })()`);
    if (
      reusePresentation.buttonText !== "Try starting local AI"
      || reusePresentation.buttonMode !== "resume"
      || !reusePresentation.manualHidden
      || !reusePresentation.disclosure.includes("already installed")
      || !reusePresentation.progress.includes("Nothing will be downloaded, installed, or replaced")
      || !reusePresentation.approvalHidden
      || reusePresentation.installedChecks < 2
    ) throw new Error(`setup-reuse-presentation:${JSON.stringify(reusePresentation)}`);
    const interruptedDownloadPresentation = await cdp.evaluate(`(async () => {
      const response = await fetch('/api/alpha/setup-status', {credentials: 'same-origin', cache: 'no-store'});
      const status = await response.json();
      const interrupted = {
        ...status,
        phase: 'failed',
        progressPercent: 66,
        error: 'model-download-failed',
        components: status.components.map((item) => item.kind === 'runtime'
          ? {...item, state: 'ready', progressPercent: 100, downloadedBytes: item.sizeBytes, bytesPerSecond: 0, etaSeconds: 0, progressActive: false}
          : {...item, state: 'failed', progressPercent: 4, downloadedBytes: Math.min(item.sizeBytes, 32 * 1024 * 1024), bytesPerSecond: 0, etaSeconds: null, progressActive: false}),
      };
      renderAlphaSetupProgress(interrupted);
      updateManagedSetupAvailability(interrupted);
      const result = {
        buttonText: document.querySelector('#alpha-setup-review').textContent,
        buttonMode: document.querySelector('#alpha-setup-review').dataset.mode,
        disclosure: document.querySelector('#alpha-setup-storage-summary').textContent,
        progress: document.querySelector('#alpha-setup-progress').textContent,
        installedChecks: document.querySelectorAll('.installation-component-check').length,
        failedChecks: document.querySelectorAll('.installation-component.state-failed .installation-component-check').length,
        troubleshootingVisible: !document.querySelector('#alpha-setup-troubleshooting').hidden,
        stoppedProgress: document.querySelector('.installation-component.state-failed .installation-component-live-progress').textContent,
      };
      document.querySelector('#alpha-setup-review').click();
      result.approvalVisible = !document.querySelector('#alpha-setup-approval').classList.contains('hidden');
      result.approvalText = document.querySelector('#alpha-setup-approval-description').textContent;
      document.querySelector('#alpha-setup-approval .button.secondary').click();
      await refreshAlphaSetupProgress();
      return result;
    })()`);
    if (
      interruptedDownloadPresentation.buttonText !== 'Retry model download'
      || interruptedDownloadPresentation.buttonMode !== 'retry-download'
      || !interruptedDownloadPresentation.disclosure.includes('internet connection was lost')
      || !interruptedDownloadPresentation.progress.includes('ask for permission')
      || interruptedDownloadPresentation.installedChecks < 1
      || interruptedDownloadPresentation.failedChecks !== 0
      || !interruptedDownloadPresentation.troubleshootingVisible
      || !interruptedDownloadPresentation.stoppedProgress.includes('Existing local download data was kept')
      || !interruptedDownloadPresentation.approvalVisible
      || !interruptedDownloadPresentation.approvalText.includes('retry only the missing local AI model')
    ) throw new Error(`setup-interrupted-download:${JSON.stringify(interruptedDownloadPresentation)}`);
    const liveDownloadPresentation = await cdp.evaluate(`(async () => {
      const response = await fetch('/api/alpha/setup-status', {credentials: 'same-origin', cache: 'no-store'});
      const status = await response.json();
      const downloading = {
        ...status,
        phase: 'model-download',
        progressPercent: 72,
        error: null,
        components: status.components.map((item) => item.kind === 'runtime'
          ? {...item, state: 'ready', progressPercent: 100, downloadedBytes: item.sizeBytes, bytesPerSecond: 0, etaSeconds: 0, progressActive: false}
          : {...item, state: 'downloading', progressPercent: 25, downloadedBytes: Math.min(item.sizeBytes, 256 * 1024 * 1024), bytesPerSecond: 8 * 1024 * 1024, etaSeconds: 95, progressActive: true}),
      };
      renderAlphaSetupProgress(downloading);
      updateManagedSetupAvailability(downloading);
      const result = {
        progress: document.querySelector('.installation-component.state-downloading .installation-component-live-progress').textContent,
        cancelVisible: !document.querySelector('#alpha-setup-cancel').hidden,
        cancelText: document.querySelector('#alpha-setup-cancel').textContent,
        troubleshootingHidden: document.querySelector('#alpha-setup-troubleshooting').hidden,
      };
      await refreshAlphaSetupProgress();
      return result;
    })()`);
    if (
      !liveDownloadPresentation.progress.includes('of')
      || !liveDownloadPresentation.progress.includes('8.0 MiB/s')
      || !liveDownloadPresentation.progress.includes('About 2 minutes remaining')
      || !liveDownloadPresentation.cancelVisible
      || liveDownloadPresentation.cancelText !== 'Cancel model download'
      || !liveDownloadPresentation.troubleshootingHidden
    ) throw new Error(`setup-live-download:${JSON.stringify(liveDownloadPresentation)}`);
    const failedValidationPresentation = await cdp.evaluate(`(async () => {
      const response = await fetch('/api/alpha/setup-status', {credentials: 'same-origin', cache: 'no-store'});
      const status = await response.json();
      const failed = {
        ...status,
        phase: 'failed',
        progressPercent: 95,
        error: 'managed-inference-request-failed',
        components: status.components.map((item) => item.kind === 'runtime'
          ? {...item, state: 'ready', progressPercent: 100, downloadedBytes: item.sizeBytes, bytesPerSecond: 0, etaSeconds: 0, progressActive: false}
          : {...item, state: 'failed', progressPercent: 95, downloadedBytes: item.sizeBytes, bytesPerSecond: 0, etaSeconds: null, progressActive: false}),
      };
      renderAlphaSetupProgress(failed);
      updateManagedSetupAvailability(failed);
      const result = {
        buttonText: document.querySelector('#alpha-setup-review').textContent,
        buttonMode: document.querySelector('#alpha-setup-review').dataset.mode,
        disclosure: document.querySelector('#alpha-setup-storage-summary').textContent,
        progress: document.querySelector('#alpha-setup-progress').textContent,
        componentProgress: document.querySelector('.installation-component.state-failed .installation-component-live-progress').textContent,
        troubleshootingVisible: !document.querySelector('#alpha-setup-troubleshooting').hidden,
      };
      await refreshAlphaSetupProgress();
      return result;
    })()`);
    if (
      failedValidationPresentation.buttonText !== 'Retry local AI test'
      || failedValidationPresentation.buttonMode !== 'retry-validation'
      || !failedValidationPresentation.disclosure.includes('model is downloaded')
      || !failedValidationPresentation.progress.includes('stopped responding during its private test')
      || !failedValidationPresentation.progress.includes('reuse the downloaded model')
      || !failedValidationPresentation.componentProgress.includes('Model download complete')
      || !failedValidationPresentation.troubleshootingVisible
    ) throw new Error(`setup-failed-validation:${JSON.stringify(failedValidationPresentation)}`);
    const setupDetailsPersistence = await cdp.evaluate(`(async () => {
      const response = await fetch('/api/alpha/setup-status', {credentials: 'same-origin', cache: 'no-store'});
      const status = await response.json();
      renderAlphaSetupProgress(status);
      const first = document.querySelector('#alpha-installation-components .installation-component-details');
      const componentId = first.closest('[data-component-id]').dataset.componentId;
      first.open = true;
      renderAlphaSetupProgress(status);
      const refreshed = document.querySelector(
        '#alpha-installation-components [data-component-id="' + componentId + '"] .installation-component-details'
      );
      return {componentId, open: refreshed.open};
    })()`);
    if (!setupDetailsPersistence.componentId || !setupDetailsPersistence.open) {
      throw new Error(`setup-details-persistence:${JSON.stringify(setupDetailsPersistence)}`);
    }
    const approvalInitial = await cdp.evaluate(`(() => {
      document.querySelector('#alpha-setup-review').click();
      return {
        visible: !document.querySelector('#alpha-setup-approval').classList.contains('hidden'),
        checked: document.querySelector('#alpha-setup-consent').checked,
        approveDisabled: document.querySelector('#alpha-setup-approval .button.primary').disabled,
        focused: document.activeElement.id,
        text: document.querySelector('#alpha-setup-approval').textContent
      };
    })()`);
    if (
      !approvalInitial.visible || approvalInitial.checked || !approvalInitial.approveDisabled
      || approvalInitial.focused !== "alpha-setup-consent"
      || !approvalInitial.text.includes("Your permission is required")
      || !approvalInitial.text.includes("allow Haven 42")
    ) throw new Error(`setup-approval-initial:${JSON.stringify(approvalInitial)}`);
    const approvalEnabled = await cdp.evaluate(`(() => {
      const consent = document.querySelector('#alpha-setup-consent');
      consent.checked = true;
      consent.dispatchEvent(new Event('change', {bubbles: true}));
      return !document.querySelector('#alpha-setup-approval .button.primary').disabled;
    })()`);
    if (!approvalEnabled) throw new Error("setup-approval-not-enabled");
    await cdp.evaluate("document.querySelector('#alpha-setup-approval .button.secondary').click()");
    const approvalCancelled = await cdp.evaluate(`({
      hidden: document.querySelector('#alpha-setup-approval').classList.contains('hidden'),
      checked: document.querySelector('#alpha-setup-consent').checked,
      focused: document.activeElement.id
    })`);
    if (!approvalCancelled.hidden || approvalCancelled.checked || approvalCancelled.focused !== "alpha-setup-review") {
      throw new Error(`setup-approval-cancel:${JSON.stringify(approvalCancelled)}`);
    }
    checks += 22;
  }
  checks += 4;
  } else {
    await cdp.evaluate("document.querySelector('#wizard-guided').click()");
    await waitFor(() => cdp.evaluate(
      "document.querySelector('#wizard-scan-status').textContent.includes('safely stopped')"
    ));
    const unsupportedSetup = await cdp.evaluate(`({
      current: document.querySelector('[aria-current="step"]').dataset.wizardProgress,
      planActions: document.querySelectorAll('#wizard-setup-plan .plan-action').length,
      nextDisabled: document.querySelector('#wizard-readiness-next').disabled,
      status: document.querySelector('#wizard-scan-status').textContent,
    })`);
    if (
      unsupportedSetup.current !== "middle"
      || unsupportedSetup.planActions !== 0
      || !unsupportedSetup.nextDisabled
      || !unsupportedSetup.status.includes("safely stopped")
    ) throw new Error(`unsupported-managed-setup:${JSON.stringify(unsupportedSetup)}`);
    checks += 4;
  }
  await cdp.evaluate("document.querySelector('#wizard-readiness-back').click()");
  await waitFor(() => cdp.evaluate("document.querySelector('[aria-current=\"step\"]').dataset.wizardProgress === 'welcome'"));
  trace("guided-readiness-verified");

  await cdp.evaluate("document.querySelector('#wizard-existing').click()");
  const provider = await cdp.evaluate(`({
    visible: !document.querySelector('[data-wizard-step="provider"]').classList.contains('hidden'),
    focused: document.activeElement.id,
    backVisible: !document.querySelector('#wizard-provider-back').classList.contains('hidden'),
    networkHelp: document.querySelector('#wizard-macos-network-help').textContent,
    describedBy: document.querySelector('#wizard-endpoint').getAttribute('aria-describedby')
  })`);
  if (
    !provider.visible
    || provider.focused !== "wizard-endpoint"
    || !provider.backVisible
    || !provider.networkHelp.includes("Local Network access")
    || !provider.networkHelp.includes("does not scan for nearby devices")
    || !provider.describedBy.split(/\s+/).includes("wizard-macos-network-help")
  ) throw new Error(`provider-step-focus:${JSON.stringify(provider)}`);
  await cdp.evaluate("document.querySelector('#wizard-provider-back').click()");
  const providerBackTarget = await cdp.evaluate(`({
    progress: document.querySelector('[aria-current="step"]').dataset.wizardProgress,
    readinessVisible: !document.querySelector('[data-wizard-step="readiness"]').classList.contains('hidden')
  })`);
  if (providerBackTarget.progress !== "middle" || !providerBackTarget.readinessVisible) throw new Error(`provider-back-target:${JSON.stringify(providerBackTarget)}`);
  await cdp.evaluate("document.querySelector('#wizard-existing').click()");
  if (!await cdp.evaluate("!document.querySelector('[data-wizard-step=\"provider\"]').classList.contains('hidden')")) {
    throw new Error("provider-reopen-after-back");
  }
  checks += 5;
  checks += 2;
  trace("provider-step-verified");

  const wizardControlSizing = await cdp.evaluate(`({
    endpoint: document.querySelector('#wizard-endpoint').getBoundingClientRect().height,
    timeout: document.querySelector('#wizard-timeout').getBoundingClientRect().height,
    cleanup: document.querySelector('#wizard-idle-unload').getBoundingClientRect().height,
    authentication: document.querySelector('#wizard-auth-mode').getBoundingClientRect().height,
    endpointFont: getComputedStyle(document.querySelector('#wizard-endpoint')).fontSize,
    timeoutFont: getComputedStyle(document.querySelector('#wizard-timeout')).fontSize,
    cleanupFont: getComputedStyle(document.querySelector('#wizard-idle-unload')).fontSize,
    authenticationFont: getComputedStyle(document.querySelector('#wizard-auth-mode')).fontSize,
    authenticationValue: document.querySelector('#wizard-auth-mode').value,
    authenticationText: document.querySelector('#wizard-auth-mode').selectedOptions[0].textContent,
    keyDisabled: document.querySelector('#wizard-api-key').disabled
  })`);
  if (
    wizardControlSizing.endpoint < 44
    || wizardControlSizing.timeout < 44
    || wizardControlSizing.cleanup < 44
    || wizardControlSizing.authentication < 44
    || wizardControlSizing.endpointFont !== "13px"
    || wizardControlSizing.timeoutFont !== "14px"
    || wizardControlSizing.cleanupFont !== "14px"
    || wizardControlSizing.authenticationFont !== "14px"
    || wizardControlSizing.authenticationValue !== "none"
    || wizardControlSizing.authenticationText !== "Automatic (Recommended)"
    || !wizardControlSizing.keyDisabled
  ) throw new Error(`compact-wizard-controls:${JSON.stringify(wizardControlSizing)}`);
  checks += 11;

  const dropdownTypography = await cdp.evaluate(`(() => ({
    controls: [...document.querySelectorAll('select')].map((item) => getComputedStyle(item).fontSize),
    choices: [...document.querySelectorAll('select option, select optgroup')].map((item) => getComputedStyle(item).fontSize),
  }))()`);
  if (
    dropdownTypography.controls.length === 0
    || dropdownTypography.choices.length === 0
    || dropdownTypography.controls.some((size) => size !== "14px")
    || dropdownTypography.choices.some((size) => size !== "14px")
  ) throw new Error(`dropdown-typography:${JSON.stringify(dropdownTypography)}`);
  checks += 2;

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
    health: document.querySelector('#provider-health').textContent,
    transportWarningVisible: !document.querySelector('#wizard-transport-warning').classList.contains('hidden'),
    transportWarningLoopback: document.querySelector('#wizard-transport-warning').classList.contains('loopback'),
    transportWarning: document.querySelector('#wizard-transport-warning').textContent
  })`);
  if (
    ready.rows !== 3
    || ready.recommended !== 3
    || ready.finishDisabled
    || ready.capabilities !== 3
    || !ready.health.includes("Working")
    || !ready.transportWarningVisible
    || !ready.transportWarningLoopback
    || !ready.transportWarning.includes("on this computer")
  ) throw new Error(`ready-step:${JSON.stringify(ready)}`);
  checks += 8;
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
  await waitFor(() => cdp.evaluate(`(
    !document.querySelector('#section-tour-layer').classList.contains('hidden')
    && document.activeElement.id === 'section-tour-next'
    && document.querySelector('#section-tour-spotlight').getBoundingClientRect().width > 4
  )`));
  const chatTour = await cdp.evaluate(`({
    dialogRole: document.querySelector('#section-tour-dialog').getAttribute('role'),
    modal: document.querySelector('#section-tour-dialog').getAttribute('aria-modal'),
    label: document.querySelector('#section-tour-dialog').getAttribute('aria-label'),
    progress: document.querySelector('#section-tour-progress').textContent,
    title: document.querySelector('#section-tour-title').textContent,
    dots: document.querySelectorAll('#section-tour-dots .section-tour-dot').length,
    focused: document.activeElement.id,
    spotlightWidth: document.querySelector('#section-tour-spotlight').getBoundingClientRect().width,
    skipVisible: document.querySelector('#section-tour-skip').getBoundingClientRect().width > 0,
    closeLabel: document.querySelector('#section-tour-close').getAttribute('aria-label'),
    backDisabled: document.querySelector('#section-tour-back').disabled,
    backgroundInert: document.querySelector('.shell').inert,
  })`);
  if (
    chatTour.dialogRole !== "dialog"
    || chatTour.modal !== "true"
    || !chatTour.label.includes("Chat help, step 1 of 6")
    || !chatTour.progress.includes("Step 1 of 6")
    || chatTour.title !== "Move around Haven 42"
    || chatTour.dots !== 6
    || chatTour.focused !== "section-tour-next"
    || chatTour.spotlightWidth <= 0
    || !chatTour.skipVisible
    || chatTour.closeLabel !== "Close this section tour"
    || !chatTour.backDisabled
    || !chatTour.backgroundInert
  ) throw new Error(`chat-section-tour:${JSON.stringify(chatTour)}`);
  const tourNavigation = await cdp.evaluate(`(() => {
    document.querySelector('#section-tour-next').click();
    const forward = {
      progress: document.querySelector('#section-tour-progress').textContent,
      title: document.querySelector('#section-tour-title').textContent,
      backEnabled: !document.querySelector('#section-tour-back').disabled,
    };
    document.querySelector('#section-tour-back').click();
    const back = document.querySelector('#section-tour-progress').textContent;
    const last = document.querySelector('#section-tour-next');
    last.focus();
    last.dispatchEvent(new KeyboardEvent('keydown', {key: 'Tab', bubbles: true, cancelable: true}));
    return {...forward, back, trappedFocus: document.activeElement.id};
  })()`);
  if (
    !tourNavigation.progress.includes("Step 2 of 6")
    || tourNavigation.title !== "See the model or change settings"
    || !tourNavigation.backEnabled
    || !tourNavigation.back.includes("Step 1 of 6")
    || tourNavigation.trappedFocus !== "section-tour-close"
  ) throw new Error(`section-tour-navigation:${JSON.stringify(tourNavigation)}`);
  await cdp.evaluate("document.querySelector('#section-tour-dialog').dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true, cancelable: true}))");
  await waitFor(() => cdp.evaluate("document.querySelector('#section-tour-layer').classList.contains('hidden')"));
  const dismissedTour = await cdp.evaluate(`({
    state: JSON.parse(localStorage.getItem('haven42.section-tours.v1')),
    focused: document.activeElement.id,
    backgroundInert: document.querySelector('.shell').inert,
  })`);
  if (dismissedTour.state.chat !== 11 || dismissedTour.focused !== "capability-title" || dismissedTour.backgroundInert) {
    throw new Error(`section-tour-dismissal:${JSON.stringify(dismissedTour)}`);
  }
  const sectionTourCounts = {models: 5, system: 6, technical: 4, about: 4};
  const sectionTourNavigation = {models: "models-nav", system: "system-nav", technical: "assurance-nav", about: "about-nav"};
  for (const [section, expectedSteps] of Object.entries(sectionTourCounts)) {
    await cdp.evaluate(`document.querySelector('#${sectionTourNavigation[section]}').click()`);
    await waitFor(() => cdp.evaluate("!document.querySelector('#section-tour-layer').classList.contains('hidden')"));
    const result = await cdp.evaluate(`({
      label: document.querySelector('#section-tour-dialog').getAttribute('aria-label'),
      dots: document.querySelectorAll('#section-tour-dots .section-tour-dot').length,
      description: document.querySelector('#section-tour-description').textContent,
    })`);
    if (!result.label.includes(`step 1 of ${expectedSteps}`) || result.dots !== expectedSteps || !result.description) {
      throw new Error(`section-tour-${section}:${JSON.stringify(result)}`);
    }
    await cdp.evaluate("document.querySelector('#section-tour-skip').click()");
    await waitFor(() => cdp.evaluate("document.querySelector('#section-tour-layer').classList.contains('hidden')"));
  }
  await cdp.evaluate("document.querySelector('#home-nav').click()");
  await new Promise((resolve) => setTimeout(resolve, 30));
  if (!await cdp.evaluate("document.querySelector('#section-tour-layer').classList.contains('hidden')")) {
    throw new Error("completed-section-tour-retriggered");
  }
  const manualTour = await cdp.evaluate(`(() => {
    const button = document.querySelector('[data-tour-section="chat"]');
    button.click();
    const visible = !document.querySelector('#section-tour-layer').classList.contains('hidden');
    document.querySelector('#section-tour-close').click();
    return {visible, focused: document.activeElement === button};
  })()`);
  if (!manualTour.visible || !manualTour.focused) throw new Error(`manual-section-tour:${JSON.stringify(manualTour)}`);
  const allTourState = await cdp.evaluate("JSON.parse(localStorage.getItem('haven42.section-tours.v1'))");
  if (
    Object.values(allTourState).length !== 5
    || allTourState.chat !== 11
    || allTourState.models !== 5
    || allTourState.system !== 5
    || allTourState.technical !== 2
    || allTourState.about !== 2
  ) {
    throw new Error(`section-tour-state:${JSON.stringify(allTourState)}`);
  }
  const helpAlignment = await cdp.evaluate(`(() => {
    const navigation = {
      chat: 'home-nav',
      models: 'models-nav',
      system: 'system-nav',
      technical: 'assurance-nav',
      about: 'about-nav',
    };
    return Object.entries(navigation).map(([section, navigationId]) => {
      document.querySelector('#' + navigationId).click();
      const button = document.querySelector('[data-tour-section="' + section + '"]');
      const header = button.closest('.panel-heading');
      const buttonRect = button.getBoundingClientRect();
      const headerRect = header.getBoundingClientRect();
      return {
        section,
        rightDelta: Math.abs(headerRect.right - buttonRect.right),
        insideHeader: buttonRect.top >= headerRect.top && buttonRect.bottom <= headerRect.bottom,
      };
    });
  })()`);
  const expectedHelpInset = helpAlignment[0].rightDelta;
  // Chromium reports a small platform-dependent inset difference when the
  // active Chat surface owns the vertical scrollbar. Keep the controls
  // visually aligned while allowing that native scrollbar-width variance.
  if (helpAlignment.some((item) => Math.abs(item.rightDelta - expectedHelpInset) > 4 || !item.insideHeader)) {
    throw new Error(`section-tour-help-alignment:${JSON.stringify(helpAlignment)}`);
  }
  await cdp.evaluate(`(() => {
    sectionTourState.chat = true;
    document.querySelector('#home-nav').click();
  })()`);
  await waitFor(() => cdp.evaluate("!document.querySelector('#section-tour-layer').classList.contains('hidden')"));
  const staleBooleanTour = await cdp.evaluate(`(() => {
    const visible = !document.querySelector('#section-tour-layer').classList.contains('hidden');
    document.querySelector('#section-tour-close').click();
    return {
      visible,
      stored: JSON.parse(localStorage.getItem('haven42.section-tours.v1')).chat,
    };
  })()`);
  if (!staleBooleanTour.visible || staleBooleanTour.stored !== 11) {
    throw new Error(`stale-boolean-section-tour:${JSON.stringify(staleBooleanTour)}`);
  }
  checks += 41;
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
    conversationHeading: document.querySelector('#capability-title').textContent,
    conversationModelLabel: document.querySelector('#model-label').textContent,
    heroCount: document.querySelectorAll('#chat-hero').length,
    settingsClosed: !document.querySelector('#conversation-settings').open,
    settingsExpanded: document.querySelector('#conversation-settings-trigger').getAttribute('aria-expanded'),
    currentModel: document.querySelector('#current-model-name').textContent,
    toolbarHeight: document.querySelector('.conversation-toolbar').getBoundingClientRect().height,
    chatHeight: document.querySelector('#text-panel').getBoundingClientRect().height,
    messagesHeight: document.querySelector('#messages').getBoundingClientRect().height,
    emptyState: document.querySelector('#messages').classList.contains('empty-conversation')
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
    || opened.conversationHeading !== "Private conversation"
    || opened.conversationModelLabel !== "Conversation model"
    || opened.heroCount !== 0
    || !opened.settingsClosed
    || opened.settingsExpanded !== "false"
    || opened.currentModel !== "qwen3.5:9b"
    || opened.toolbarHeight > 84
    || opened.chatHeight < 560
    || opened.messagesHeight < opened.toolbarHeight * 2
    || !opened.emptyState
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

  await cdp.evaluate("document.querySelector('#system-nav').click()");
  const compactControls = await cdp.evaluate(`(() => {
    const simulatedLastPassControl = document.createElement('div');
    simulatedLastPassControl.setAttribute('data-lastpass-icon-root', '');
    document.body.append(simulatedLastPassControl);
    const result = {
      endpoint: document.querySelector('#endpoint').getBoundingClientRect().height,
      cleanup: document.querySelector('#system-idle-unload').getBoundingClientRect().height,
      model: document.querySelector('#model').getBoundingClientRect().height,
      authentication: document.querySelector('#auth-mode').getBoundingClientRect().height,
      endpointFont: getComputedStyle(document.querySelector('#endpoint')).fontSize,
      cleanupFont: getComputedStyle(document.querySelector('#system-idle-unload')).fontSize,
      timeoutFont: getComputedStyle(document.querySelector('#timeout')).fontSize,
      advancedCleanupFont: getComputedStyle(document.querySelector('#idle-unload')).fontSize,
      authenticationFont: getComputedStyle(document.querySelector('#auth-mode')).fontSize,
      authenticationText: document.querySelector('#auth-mode').selectedOptions[0].textContent,
      keyDisabled: document.querySelector('#api-key').disabled,
      keyToggleDisabled: document.querySelector('#api-key-visibility').disabled,
      keyToggleNeutral: !document.querySelector('#api-key-visibility').classList.contains('danger'),
      keyToggleLabel: document.querySelector('#api-key-visibility').textContent.trim(),
      keyType: document.querySelector('#api-key').type,
      keyToggleCount: document.querySelectorAll('#connection-form #api-key-visibility').length,
      keyAutocomplete: document.querySelector('#api-key').autocomplete,
      keyPasswordManagerIgnored: document.querySelector('#api-key').dataset.lpignore === 'true'
        && document.querySelector('#api-key').dataset.bwignore === 'true'
        && document.querySelector('#api-key').hasAttribute('data-1p-ignore'),
      injectedLastPassControlHidden: getComputedStyle(simulatedLastPassControl).display === 'none'
    };
    simulatedLastPassControl.remove();
    return result;
  })()`);
  if (
    compactControls.endpoint < 44
    || Math.abs(compactControls.cleanup - compactControls.endpoint) > 1
    || Math.abs(compactControls.authentication - compactControls.endpoint) > 1
    || compactControls.endpointFont !== "13px"
    || compactControls.cleanupFont !== "14px"
    || compactControls.timeoutFont !== "14px"
    || compactControls.advancedCleanupFont !== "14px"
    || compactControls.authenticationFont !== "14px"
    || compactControls.authenticationText !== "Automatic (Recommended)"
    || !compactControls.keyDisabled
    || !compactControls.keyToggleDisabled
    || !compactControls.keyToggleNeutral
    || compactControls.keyToggleLabel !== "Show"
    || compactControls.keyType !== "password"
    || compactControls.keyToggleCount !== 1
    || compactControls.keyAutocomplete !== "off"
    || !compactControls.keyPasswordManagerIgnored
    || !compactControls.injectedLastPassControlHidden
  ) throw new Error(`compact-provider-controls:${JSON.stringify(compactControls)}`);
  checks += 19;

  await cdp.evaluate("document.querySelector('#check-software-updates').click()");
  const managedRuntimeUpdateSupported = process.platform === "win32" || process.platform === "linux";
  if (packagedExecutable || !managedRuntimeUpdateSupported) {
    await waitFor(() => cdp.evaluate(
      "document.querySelector('#check-software-updates').textContent === 'Check official releases again'",
    ));
    const packagedSoftwareUpdate = await cdp.evaluate(`({
      result: document.querySelector('#software-update-result').textContent,
      status: document.querySelector('#update-status').textContent,
      updateDisabled: document.querySelector('#use-software-update').disabled,
      releaseHidden: document.querySelector('#software-update-release-link').classList.contains('hidden')
    })`);
    const verified = packagedSoftwareUpdate.result.includes('Ollama')
      && packagedSoftwareUpdate.status.startsWith('Checked · Ollama')
      && !packagedSoftwareUpdate.releaseHidden;
    const failedClosed = packagedSoftwareUpdate.result.startsWith(
      'The official release could not be verified. Nothing was downloaded or changed.',
    )
      && packagedSoftwareUpdate.status === 'Check failed · no changes'
      && packagedSoftwareUpdate.updateDisabled
      && packagedSoftwareUpdate.releaseHidden;
    if (!verified && !failedClosed) {
      throw new Error(`packaged-software-update-review:${JSON.stringify(packagedSoftwareUpdate)}`);
    }
    checks += 4;
  } else {
    await waitFor(() => cdp.evaluate(`(
      document.querySelector('#software-update-result').textContent.includes('Ollama 0.32.15')
      && !document.querySelector('#software-update-release-link').classList.contains('hidden')
    )`));
    const softwareUpdateReview = await cdp.evaluate(`(() => {
      const preference = document.querySelector('#software-update-preference');
      const update = document.querySelector('#use-software-update');
      const initial = {
        status: document.querySelector('#software-update-result').textContent,
        updateText: update.textContent,
        release: document.querySelector('#software-update-release-link').href,
        persisted: document.querySelector('#software-update-privacy').textContent,
      };
      const certifiedActive = update.disabled;
      preference.value = 'latest';
      preference.dispatchEvent(new Event('change', {bubbles: true}));
      const latestEnabled = !update.disabled;
      const latestText = update.textContent;
      preference.value = 'certified';
      preference.dispatchEvent(new Event('change', {bubbles: true}));
      return {...initial, certifiedActive, latestEnabled, latestText, certifiedDisabledAgain: update.disabled};
    })()`);
    if (
      !softwareUpdateReview.status.includes('newest official stable release')
      || softwareUpdateReview.updateText !== 'Certified Ollama 0.32.14 is active'
      || softwareUpdateReview.release !== 'https://github.com/ollama/ollama/releases/tag/v0.32.15'
      || !softwareUpdateReview.persisted.includes('stay in memory')
      || !softwareUpdateReview.certifiedActive
      || !softwareUpdateReview.latestEnabled
      || softwareUpdateReview.latestText !== 'Review and install Ollama 0.32.15'
      || !softwareUpdateReview.certifiedDisabledAgain
    ) throw new Error(`software-update-review:${JSON.stringify(softwareUpdateReview)}`);
    await cdp.evaluate(`(() => {
      const preference = document.querySelector('#software-update-preference');
      preference.value = 'latest';
      preference.dispatchEvent(new Event('change', {bubbles: true}));
      document.querySelector('#use-software-update').click();
    })()`);
    await waitFor(() => cdp.evaluate(
      "!document.querySelector('#software-update-review').classList.contains('hidden')",
    ));
    const unverifiedReview = await cdp.evaluate(`({
      title: document.querySelector('#software-update-review-title').textContent,
      warning: document.querySelector('#software-update-review-warning').textContent,
      warningVisible: !document.querySelector('#software-update-review-warning').classList.contains('hidden'),
      consentVisible: !document.querySelector('#software-update-unverified-consent-row').classList.contains('hidden'),
      consentChecked: document.querySelector('#software-update-unverified-consent').checked,
      effects: document.querySelectorAll('#software-update-review-effects li').length,
      focused: document.activeElement === document.querySelector('#software-update-review')
    })`);
    if (
      unverifiedReview.title !== 'Install Ollama 0.32.15'
      || !unverifiedReview.warning.includes('not yet been compatibility-tested')
      || !unverifiedReview.warningVisible || !unverifiedReview.consentVisible
      || unverifiedReview.consentChecked || unverifiedReview.effects !== 4
      || !unverifiedReview.focused
    ) throw new Error(`software-update-unverified-review:${JSON.stringify(unverifiedReview)}`);
    await cdp.evaluate("document.querySelector('#cancel-software-update-review').click()");
    checks += 15;
  }

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

  const browserAuthSecret = "synthetic-browser-bearer";
  requiredOllamaAuthorization = `Bearer ${browserAuthSecret}`;
  const authorizationStart = providerAuthorization.length;
  const authenticationDirty = await cdp.evaluate(`(() => {
    const mode = document.querySelector('#auth-mode');
    const key = document.querySelector('#api-key');
    mode.value = 'bearer';
    mode.dispatchEvent(new Event('change', {bubbles: true}));
    const visibility = document.querySelector('#api-key-visibility');
    visibility.click();
    const reveal = {
      enabled: !visibility.disabled,
      type: key.type,
      pressed: visibility.getAttribute('aria-pressed'),
      label: visibility.textContent.trim(),
    };
    visibility.click();
    key.value = '${browserAuthSecret}';
    key.dispatchEvent(new Event('input', {bubbles: true}));
    const before = {
      keyEnabled: !key.disabled,
      keyRequired: key.required,
      buttonText: document.querySelector('#connect-button').textContent,
      buttonEnabled: !document.querySelector('#connect-button').disabled,
    };
    document.querySelector('#connection-form').requestSubmit();
    return {...before, reveal, hiddenAgain: key.type === 'password' && visibility.getAttribute('aria-pressed') === 'false'};
  })()`);
  if (
    !authenticationDirty.keyEnabled
    || !authenticationDirty.keyRequired
    || authenticationDirty.buttonText !== "Apply changes"
    || !authenticationDirty.buttonEnabled
    || !authenticationDirty.reveal.enabled
    || authenticationDirty.reveal.type !== "text"
    || authenticationDirty.reveal.pressed !== "true"
    || authenticationDirty.reveal.label !== "Hide"
    || !authenticationDirty.hiddenAgain
  ) throw new Error(`authentication-dirty-state:${JSON.stringify(authenticationDirty)}`);
  await waitFor(() => cdp.evaluate(`(
    document.querySelector('#connect-button').disabled
    && document.querySelector('#connect-button').textContent === 'Connected'
    && document.querySelector('#api-key').value === ''
    && document.querySelector('#wizard-api-key').value === ''
    && document.querySelector('#wizard-auth-mode').value === 'bearer'
    && document.querySelector('#connection-badge').textContent.includes('authenticated')
    && !document.querySelector('#text-panel').classList.contains('hidden')
    && document.querySelector('#system-panel').classList.contains('hidden')
    && document.querySelector('#home-nav').classList.contains('active')
    && document.activeElement.id === 'prompt'
  )`));
  const authenticatedRequests = providerAuthorization.slice(authorizationStart);
  if (
    authenticatedRequests.length < 2
    || authenticatedRequests.some(([, , authorization]) => authorization !== `Bearer ${browserAuthSecret}`)
  ) throw new Error(`provider-authentication-headers:${JSON.stringify(authenticatedRequests)}`);
  checks += 20;

  await cdp.evaluate(`(() => {
    const key = document.querySelector('#api-key');
    key.value = 'synthetic-browser-wrong-key';
    key.dispatchEvent(new Event('input', {bubbles: true}));
    document.querySelector('#connection-form').requestSubmit();
  })()`);
  await waitFor(() => cdp.evaluate(`(
    !document.querySelector('#connection-error').classList.contains('hidden')
    && document.querySelector('#connection-error').textContent.includes('could not reach Ollama')
    && document.querySelector('#connect-button').textContent === 'Apply changes'
    && !document.querySelector('#prompt').disabled
    && document.querySelector('#connection-badge').textContent.includes('Connected')
  )`));
  await cdp.evaluate(`(() => {
    const key = document.querySelector('#api-key');
    key.value = '${browserAuthSecret}';
    key.dispatchEvent(new Event('input', {bubbles: true}));
    document.querySelector('#connection-form').requestSubmit();
  })()`);
  await waitFor(() => cdp.evaluate(`(
    document.querySelector('#connect-button').disabled
    && document.querySelector('#connect-button').textContent === 'Connected'
    && document.querySelector('#api-key').value === ''
    && !document.querySelector('#prompt').disabled
  )`));
  checks += 7;

  const transportWarnings = await cdp.evaluate(`(() => {
    renderProviderTransportWarning("trusted-lan", "http");
    const privateHttp = {
      mainVisible: !document.querySelector('#connection-transport-warning').classList.contains('hidden'),
      wizardVisible: !document.querySelector('#wizard-transport-warning').classList.contains('hidden'),
      loopbackStyle: document.querySelector('#connection-transport-warning').classList.contains('loopback'),
      text: document.querySelector('#connection-transport-warning').textContent,
    };
    renderProviderTransportWarning("trusted-lan", "https");
    const httpsHidden = (
      document.querySelector('#connection-transport-warning').classList.contains('hidden')
      && document.querySelector('#wizard-transport-warning').classList.contains('hidden')
    );
    renderProviderTransportWarning("loopback", "http");
    return {privateHttp, httpsHidden};
  })()`);
  if (
    !transportWarnings.privateHttp.mainVisible
    || !transportWarnings.privateHttp.wizardVisible
    || transportWarnings.privateHttp.loopbackStyle
    || !transportWarnings.privateHttp.text.includes("could read or change")
    || !transportWarnings.httpsHidden
  ) throw new Error(`transport-warnings:${JSON.stringify(transportWarnings)}`);
  checks += 5;

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
  if (!unknown.state.includes("not tested for this task") || !unknown.promptEnabled) throw new Error("unknown-model-advanced-only");
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
  const testedManualModel = await cdp.evaluate(`(() => ({
    option: document.querySelector('#model option[value="manual:qwen3.5:9b"]')?.textContent || '',
    automatic: document.querySelector('#model option[value="automatic"]')?.textContent || '',
    mode: document.querySelector('#model-selection-mode').textContent,
  }))()`);
  if (
    !testedManualModel.option.includes('tested for this task')
    || !testedManualModel.automatic.includes('Recommended')
    || testedManualModel.mode !== 'Manual'
  ) throw new Error(`tested-model-label:${JSON.stringify(testedManualModel)}`);
  checks += 3;
  const requestsBeforeUnchangedSubmit = requests.length;
  await cdp.evaluate("document.querySelector('#connection-form').requestSubmit()");
  await delay(150);
  if (requests.length !== requestsBeforeUnchangedSubmit) throw new Error("unchanged-provider-reconnected");
  checks += 1;

  await cdp.evaluate("document.querySelector('#conversation-settings-trigger').click()");
  await waitFor(() => cdp.evaluate("document.querySelector('#conversation-settings-trigger').getAttribute('aria-expanded') === 'true'"));
  const modelLibraryAction = await cdp.evaluate(`(() => {
    const action = document.querySelector('#open-models-from-chat');
    const label = document.querySelector('label[for="model"]');
    const settings = document.querySelector('#conversation-settings');
    const trigger = document.querySelector('#conversation-settings-trigger');
    return {
      text: action.textContent.trim(),
      visible: action.getBoundingClientRect().width > 0 && action.getBoundingClientRect().height >= 44,
      label: label?.textContent.trim() || '',
      heading: action.closest('.model-picker-heading') !== null,
      settingsOpen: settings.open,
      expanded: trigger.getAttribute('aria-expanded'),
      triggerHeight: trigger.getBoundingClientRect().height,
    };
  })()`);
  if (
    modelLibraryAction.text !== "Browse models →"
    || !modelLibraryAction.visible
    || modelLibraryAction.label !== "Conversation model"
    || !modelLibraryAction.heading
    || !modelLibraryAction.settingsOpen
    || modelLibraryAction.expanded !== "true"
    || modelLibraryAction.triggerHeight < 44
  ) throw new Error(`model-library-action:${JSON.stringify(modelLibraryAction)}`);
  await cdp.evaluate("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true, cancelable: true}))");
  await waitFor(() => cdp.evaluate("!document.querySelector('#conversation-settings').open && document.querySelector('#conversation-settings-trigger').getAttribute('aria-expanded') === 'false'"));
  const settingsDismissal = await cdp.evaluate(`({
    focused: document.activeElement.id,
    label: document.querySelector('#conversation-settings-trigger').getAttribute('aria-label'),
  })`);
  if (settingsDismissal.focused !== "conversation-settings-trigger" || settingsDismissal.label !== "Open conversation settings") {
    throw new Error(`conversation-settings-dismissal:${JSON.stringify(settingsDismissal)}`);
  }
  await cdp.evaluate("document.querySelector('#conversation-settings-trigger').click()");
  await waitFor(() => cdp.evaluate("document.querySelector('#conversation-settings').open"));
  checks += 9;

  const remainingDesignFixes = await cdp.evaluate(`(() => {
    const research = document.querySelector('#research-tools');
    const technical = document.querySelector('#run-details');
    technical.classList.remove('hidden');
    const assistant = document.querySelector('.message.assistant');
    const navLabel = document.querySelector('#assurance-nav .nav-label').getBoundingClientRect();
    const navTag = document.querySelector('#assurance-nav .nav-tag');
    const navTagRect = navTag.getBoundingClientRect();
    const researchStyle = getComputedStyle(research);
    const assistantStyle = getComputedStyle(assistant);
    const researchRect = research.getBoundingClientRect();
    const technicalRect = technical.getBoundingClientRect();
    const researchSummaryHeight = research.querySelector('summary').getBoundingClientRect().height;
    const technicalSummaryHeight = technical.querySelector('summary').getBoundingClientRect().height;
    technical.classList.add('hidden');
    return {
      researchBorder: researchStyle.borderTopWidth,
      researchRadius: researchStyle.borderRadius,
      assistantBackground: assistantStyle.backgroundColor,
      assistantRadius: assistantStyle.borderRadius,
      navTagText: navTag.textContent.trim(),
      navTagBorder: getComputedStyle(navTag).borderTopWidth,
      navTagBelowLabel: navTagRect.top >= navLabel.bottom,
      utilityControlsShareRow: Math.abs(researchRect.top - technicalRect.top) < 2,
      researchSummaryHeight,
      technicalSummaryHeight,
    };
  })()`);
  if (
    remainingDesignFixes.researchBorder === "0px"
    || remainingDesignFixes.researchRadius === "0px"
    || remainingDesignFixes.assistantBackground === "rgba(0, 0, 0, 0)"
    || remainingDesignFixes.assistantRadius === "0px"
    || remainingDesignFixes.navTagText !== "Advanced"
    || remainingDesignFixes.navTagBorder === "0px"
    || !remainingDesignFixes.navTagBelowLabel
    || !remainingDesignFixes.utilityControlsShareRow
    || remainingDesignFixes.researchSummaryHeight < 44
    || remainingDesignFixes.researchSummaryHeight > 46
    || remainingDesignFixes.technicalSummaryHeight < 44
    || remainingDesignFixes.technicalSummaryHeight > 46
  ) throw new Error(`remaining-design-fixes:${JSON.stringify(remainingDesignFixes)}`);
  checks += 10;

  const dashboardTypography = await cdp.evaluate(`(() => {
    const size = (selector) => getComputedStyle(document.querySelector(selector)).fontSize;
    return {
      sectionTitle: size('#capability-title'),
      currentModel: size('#current-model-name'),
      taskLabel: size('.task-mode-select > span'),
      modelLabel: size('.model-picker-heading label'),
      modelState: size('#model-state'),
      modelAction: size('#open-models-from-chat'),
      telemetryLabel: size('.alpha-metrics strong'),
      telemetryValue: size('.alpha-metrics output'),
      researchDisclosure: size('.research-tools > summary small'),
      composerHelp: size('.composer-help'),
      footer: size('.chat-footer'),
      status: size('.status-glance-connection .status-indicator'),
      statusTitle: size('.status-glance-connection strong'),
      statusDetail: size('.status-glance-connection small'),
      statusMetric: size('.status-glance-stats output'),
    };
  })()`);
  if (JSON.stringify(dashboardTypography) !== JSON.stringify({
    sectionTitle: "18px",
    currentModel: "12px",
    taskLabel: "11px",
    modelLabel: "11px",
    modelState: "12px",
    modelAction: "13px",
    telemetryLabel: "11px",
    telemetryValue: "12px",
    researchDisclosure: "12px",
    composerHelp: "12px",
    footer: "12px",
    status: "12px",
    statusTitle: "14px",
    statusDetail: "12px",
    statusMetric: "12px",
  })) throw new Error(`dashboard-typography:${JSON.stringify(dashboardTypography)}`);
  checks += 16;

  const modelsView = await cdp.evaluate(`(() => {
    document.querySelector('#open-models-from-chat').click();
    return {
      active: document.querySelector('#models-nav').classList.contains('active'),
      visible: !document.querySelector('#models-panel').classList.contains('hidden'),
      textHidden: document.querySelector('#text-panel').classList.contains('hidden'),
      imageHidden: document.querySelector('#image-panel').classList.contains('hidden'),
      settingsClosed: !document.querySelector('#conversation-settings').open,
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
    || !modelsView.settingsClosed
    || modelsView.focused !== "models-title"
    || modelsView.installed !== 2
    || !modelsView.installedLabel.includes("Already available on your server")
  ) throw new Error(`dedicated-models-view:${JSON.stringify(modelsView)}`);
  checks += 8;

  await cdp.evaluate(`(() => {
    const original = window.fetch;
    let modelInstallProgressPolls = 0;
    window.__havenOriginalFetch = original;
    window.fetch = (input, init) => {
      if (input === "/api/model-search") return Promise.resolve(new Response(JSON.stringify({
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
        }), {status: 200, headers: {"Content-Type": "application/json"}}));
      if (input === "/api/model-install/prepare") return Promise.resolve(new Response(JSON.stringify({
        schemaVersion: 1,
        kind: "model-install-approval",
        approvalToken: "a".repeat(32),
        expiresInSeconds: 300,
        singleUse: true,
        persisted: false,
        model: "candidate-writing:7b",
        destination: "This computer",
        downloadStarted: false,
        licenseStatus: "review-required",
        hardwareFit: "unknown"
      }), {status: 200, headers: {"Content-Type": "application/json"}}));
      if (input === "/api/model-install/execute") return Promise.resolve(new Response(JSON.stringify({
        schemaVersion: 1,
        kind: "model-install-result",
        status: "installed",
        model: "candidate-writing:7b",
        verifiedByProviderCatalog: true,
        selectedAutomatically: false,
        modelOption: {
          name: "candidate-writing:7b",
          digestVerified: false,
          capabilityStatus: Object.fromEntries(Object.keys(CAPABILITIES).map((id) => [id, "unverified"]))
        }
      }), {status: 200, headers: {"Content-Type": "application/json"}}));
      if (input === "/api/model-install/status") {
        modelInstallProgressPolls += 1;
        const complete = modelInstallProgressPolls > 1;
        return Promise.resolve(new Response(JSON.stringify({
          schemaVersion: 1,
          kind: "model-install-progress",
          model: "candidate-writing:7b",
          phase: complete ? "complete" : "downloading",
          progressPercent: complete ? 100 : 45,
          completedBytes: complete ? 1000 : 450,
          totalBytes: 1000,
          status: complete ? "Model downloaded and verified" : "Downloading model files",
          terminal: complete
        }), {status: 200, headers: {"Content-Type": "application/json"}}));
      }
      return original(input, init);
    };
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
    inlineAfterCandidate: document.querySelector('#desired-model').previousElementSibling?.classList.contains('model-search-result') === true,
    searchStatus: document.querySelector('#model-search-status').textContent,
    currentModel: document.querySelector('#model').value
  })`);
  if (
    discovery.desired !== "candidate-writing:7b"
    || !discovery.state.includes("review this model before downloading")
    || discovery.command !== "ollama pull candidate-writing:7b"
    || discovery.hidden
    || !discovery.inlineAfterCandidate
    || !discovery.searchStatus.includes("Nothing was downloaded")
    || discovery.currentModel !== "manual:unknown-model:latest"
  ) throw new Error(`candidate-only-model-discovery:${JSON.stringify(discovery)}`);
  checks += 7;

  await cdp.evaluate("document.querySelector('#install-model-button').click()");
  await waitFor(() => cdp.evaluate("!document.querySelector('#model-install-review-layer').classList.contains('hidden')"));
  const installReview = await cdp.evaluate(`({
    role: document.querySelector('#model-install-review-dialog').getAttribute('role'),
    modal: document.querySelector('#model-install-review-dialog').getAttribute('aria-modal'),
    model: document.querySelector('#model-install-review-name').textContent,
    destination: document.querySelector('#model-install-review-destination').textContent,
    focused: document.activeElement.id,
    backgroundInert: document.querySelector('.shell').inert,
  })`);
  if (
    installReview.role !== "dialog"
    || installReview.modal !== "true"
    || installReview.model !== "candidate-writing:7b"
    || installReview.destination !== "This computer"
    || installReview.focused !== "model-install-review-dialog"
    || !installReview.backgroundInert
  ) throw new Error(`model-install-review:${JSON.stringify(installReview)}`);
  await cdp.evaluate("document.querySelector('#model-install-review-dialog').dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true, cancelable: true}))");
  await waitFor(() => cdp.evaluate("document.querySelector('#model-install-review-layer').classList.contains('hidden')"));
  const installCancel = await cdp.evaluate(`({
    focused: document.activeElement.id,
    backgroundInert: document.querySelector('.shell').inert,
    status: document.querySelector('#model-install-status').textContent,
  })`);
  if (installCancel.focused !== "install-model-button" || installCancel.backgroundInert || !installCancel.status.includes("Nothing was downloaded")) {
    throw new Error(`model-install-cancel:${JSON.stringify(installCancel)}`);
  }
  await cdp.evaluate("document.querySelector('#install-model-button').click()");
  await waitFor(() => cdp.evaluate("!document.querySelector('#model-install-review-layer').classList.contains('hidden')"));
  await trustedClick(cdp, "#model-install-review-approve");
  await waitFor(() => cdp.evaluate("document.querySelector('#model-install-progress-bar').value === 45"));
  const activeInstallProgress = await cdp.evaluate(`({
    visible: !document.querySelector('#model-install-progress').classList.contains('hidden'),
    value: document.querySelector('#model-install-progress-bar').value,
    percent: document.querySelector('#model-install-progress-percent').textContent,
    label: document.querySelector('#model-install-progress-label').textContent,
    detail: document.querySelector('#model-install-progress-detail').textContent,
  })`);
  if (
    !activeInstallProgress.visible
    || activeInstallProgress.value !== 45
    || activeInstallProgress.percent !== "45%"
    || activeInstallProgress.label !== "Downloading model"
    || !activeInstallProgress.detail.includes("Downloading model files")
  ) throw new Error(`model-install-progress:${JSON.stringify(activeInstallProgress)}`);
  await waitFor(() => cdp.evaluate("document.querySelector('#desired-model').classList.contains('hidden')"));
  const installedCandidate = await cdp.evaluate(`({
    selected: document.querySelector('#model').value,
    status: document.querySelector('#model-search-status').textContent,
    reviewHidden: document.querySelector('#model-install-review-layer').classList.contains('hidden'),
    backgroundInert: document.querySelector('.shell').inert,
  })`);
  if (
    installedCandidate.selected !== "manual:candidate-writing:7b"
    || !installedCandidate.status.includes("downloaded and verified")
    || !installedCandidate.reviewHidden
    || installedCandidate.backgroundInert
  ) throw new Error(`model-install-complete:${JSON.stringify(installedCandidate)}`);
  checks += 21;
  await cdp.evaluate(`(() => {
    state.modelOptions = state.modelOptions.filter((item) => item.name !== "candidate-writing:7b");
    state.modelSelections[document.querySelector('#model-search-capability').value] = {mode: 'manual', model: 'unknown-model:latest'};
    state.modelSearchResults = [];
    renderModelSelect();
  })()`);

  const capabilityReset = await cdp.evaluate(`(() => {
    const capability = document.querySelector('#model-search-capability');
    capability.value = 'general.chat';
    capability.dispatchEvent(new Event('change', {bubbles: true}));
    return {
      query: document.querySelector('#model-search-query').value,
      resultCount: document.querySelectorAll('#model-search-results .model-search-result').length,
      desiredHidden: document.querySelector('#desired-model').classList.contains('hidden'),
      resultName: document.querySelector('#model-search-results strong')?.textContent || '',
      status: document.querySelector('#model-search-status').textContent
    };
  })()`);
  const expectedFixtureProfile = (
    capabilityReset.resultCount >= 14
    && capabilityReset.status.includes("AMD Radeon RX 7800 XT 16 GB")
  );
  const expectedUnpromotedPhysicalProfile = (
    Boolean(packagedExecutable)
    && capabilityReset.resultCount >= 1
    && capabilityReset.status.includes("No matching qualification profile exists")
  );
  if (
    capabilityReset.query !== ""
    || !capabilityReset.desiredHidden
    || capabilityReset.resultName !== "unknown-model:latest"
    || (!expectedFixtureProfile && !expectedUnpromotedPhysicalProfile)
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

  await cdp.evaluate("document.querySelector('#home-nav').click()");
  await waitFor(() => cdp.evaluate("!document.querySelector('#text-panel').classList.contains('hidden')"));
  await cdp.evaluate(`(() => {
    const messages = document.querySelector('#messages');
    messages.scrollTop = messages.scrollHeight;
    messages.dispatchEvent(new Event('scroll'));
  })()`);
  await waitFor(() => cdp.evaluate(`(() => {
    const messages = document.querySelector('#messages');
    return messages.scrollHeight - messages.scrollTop - messages.clientHeight <= 8;
  })()`));
  const keyboardSubmit = await cdp.evaluate(`(() => {
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
      (
        [...document.querySelectorAll('.message p')].some((item) => item.textContent === 'LOCAL_BROWSER_OK')
        || document.querySelector('#task-event').dataset.kind === 'error'
      )
      && !document.querySelector('#prompt').disabled
      && !document.querySelector('#send-button').disabled
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
  try {
    await waitFor(() => cdp.evaluate(`(() => {
      const messages = document.querySelector('#messages');
      const latest = messages.querySelector('.message:last-child');
      if (!latest) return false;
      const viewport = messages.getBoundingClientRect();
      const reply = latest.getBoundingClientRect();
      return reply.bottom >= viewport.top && reply.bottom <= viewport.bottom + 2;
    })()`));
  } catch (error) {
    const diagnostic = await cdp.evaluate(`(() => {
      const messages = document.querySelector('#messages');
      const latest = messages.querySelector('.message:last-child');
      const viewport = messages.getBoundingClientRect();
      const reply = latest?.getBoundingClientRect();
      return {scrollHeight: messages.scrollHeight, scrollTop: messages.scrollTop,
        clientHeight: messages.clientHeight,
        viewport: {top: viewport.top, bottom: viewport.bottom},
        reply: reply ? {top: reply.top, bottom: reply.bottom} : null};
    })()`);
    throw new Error(`message-auto-follow:${JSON.stringify(diagnostic)}`, {cause: error});
  }
  const result = await cdp.evaluate(`(() => {
    const latestMessage = [...document.querySelectorAll('#messages .message')].at(-1);
    return ({
    output: [...document.querySelectorAll('.message p')].some((item) => item.textContent === 'LOCAL_BROWSER_OK'),
    typed: document.querySelector('#task-event').textContent,
    kind: document.querySelector('#task-event').dataset.kind,
    status: document.querySelector('#text-status').textContent,
    error: document.querySelector('#connection-error').textContent,
    cpu: document.querySelector('#alpha-cpu').textContent,
    ram: document.querySelector('#alpha-ram').textContent,
    gpu: document.querySelector('#alpha-gpu').textContent,
    speed: document.querySelector('#alpha-speed').textContent,
    sidebarCpu: document.querySelector('#sidebar-cpu').textContent,
    sidebarRam: document.querySelector('#sidebar-ram').textContent,
    sidebarGpu: document.querySelector('#sidebar-gpu').textContent,
    sidebarSpeed: document.querySelector('#sidebar-speed').textContent,
    sidebarConnection: document.querySelector('#sidebar-connection-status').textContent,
    sidebarModel: document.querySelector('#sidebar-model-name').textContent,
    sidebarForms: document.querySelectorAll('.configuration-column form').length,
    runDetailsVisible: !document.querySelector('#run-details').classList.contains('hidden'),
    runDetails: document.querySelector('#run-details-list').textContent,
    runDetailsSummary: document.querySelector('#run-details-summary').textContent,
    messageActions: [...latestMessage.querySelectorAll('.message-action')].map((item) => item.textContent),
    messageActionIcons: [...latestMessage.querySelectorAll('.message-action-icon')].map((item) => ({
      ariaHidden: item.getAttribute('aria-hidden'),
      focusable: item.getAttribute('focusable'),
      paths: item.querySelectorAll('path').length,
    })),
    assistantBackground: getComputedStyle(latestMessage).backgroundColor,
    followGap: document.querySelector('#messages').scrollHeight - document.querySelector('#messages').scrollTop - document.querySelector('#messages').clientHeight,
    emptyConversation: document.querySelector('#messages').classList.contains('empty-conversation'),
    });
  })()`);
  if (
    !result.output
    || !result.typed.includes("no file saved")
    || !result.typed.includes("has not tested this model")
    || result.kind !== "warning"
    || result.sidebarCpu !== result.cpu
    || result.sidebarRam !== result.ram
    || result.sidebarGpu !== result.gpu
    || result.speed !== "2 tokens/s"
    || result.sidebarSpeed !== "2 tokens/s"
    || result.sidebarConnection !== "Connected"
    || !result.sidebarModel.includes("unknown-model:latest")
    || result.sidebarForms !== 0
    || !result.runDetailsVisible
    || !result.runDetails.includes("40")
    || !result.runDetails.includes("2 tokens/s")
    || !result.runDetailsSummary.includes("Response completed in")
    || result.messageActions.join('|') !== "Copy answer|Try again|Report this answer"
    || result.messageActionIcons.length !== 3
    || result.messageActionIcons.some((item) => item.ariaHidden !== "true" || item.focusable !== "false" || item.paths < 1)
    || result.assistantBackground === "rgba(0, 0, 0, 0)"
    || result.followGap > 48
    || result.emptyConversation
  ) {
    throw new Error(`typed-result-rendering:${JSON.stringify(result)}`);
  }
  checks += 18;
  trace("typed-result-verified");

  const answerReportDisclosure = await cdp.evaluate(`(() => {
    const report = [...document.querySelectorAll('.message-action')].at(-1);
    if (!report) return null;
    report.click();
    return {
      label: report.textContent,
      panelVisible: !document.querySelector('#answer-report-panel').classList.contains('hidden'),
      disclosure: document.querySelector('#answer-report-description').textContent,
      status: document.querySelector('#answer-report-status').textContent,
    };
  })()`);
  if (
    !answerReportDisclosure
    || answerReportDisclosure.label !== "Report this answer"
    || !answerReportDisclosure.panelVisible
    || !answerReportDisclosure.disclosure.includes("never includes the question, answer, or attachments")
    || !answerReportDisclosure.disclosure.includes("nothing is uploaded")
    || !answerReportDisclosure.status.includes("stays in Haven42-Logs")
  ) throw new Error(`answer-report-disclosure:${JSON.stringify(answerReportDisclosure)}`);
  await cdp.evaluate(`(() => {
    document.querySelector('#answer-report-category').value = 'incorrect';
    document.querySelector('#answer-report-note').value = 'The result appears factually incorrect.';
    document.querySelector('#save-answer-report').click();
  })()`);
  await waitFor(() => cdp.evaluate(`(
    document.querySelector('#answer-report-panel').classList.contains('hidden')
    && document.querySelector('#task-event').textContent.includes('nothing uploaded')
  )`));
  checks += 7;
  trace("answer-report-privacy-flow-verified");

  const manualScroll = await cdp.evaluate(`(() => {
    const messages = document.querySelector('#messages');
    messages.scrollTop = 0;
    messages.dispatchEvent(new Event('scroll'));
    return messages.scrollHeight - messages.clientHeight;
  })()`);
  if (manualScroll <= 48) throw new Error(`manual-scroll-fixture-too-short:${manualScroll}`);
  await cdp.evaluate(`(() => {
    document.querySelector('#prompt').value = 'markdown showcase';
    document.querySelector('#text-form').requestSubmit();
  })()`);
  try {
    await waitFor(() => cdp.evaluate(
      "document.querySelector('.message:last-child .message-content h5')?.textContent.includes('Clear answer')",
    ));
  } catch (error) {
    const diagnostic = await cdp.evaluate(`({
      taskEvent: document.querySelector('#task-event').textContent,
      taskKind: document.querySelector('#task-event').dataset.kind || '',
      status: document.querySelector('#text-status').textContent,
      error: document.querySelector('#connection-error').textContent,
      promptDisabled: document.querySelector('#prompt').disabled,
      sendDisabled: document.querySelector('#send-button').disabled,
      lastMessage: document.querySelector('.message:last-child')?.textContent || ''
    })`);
    throw new Error(`markdown-response-timeout:${JSON.stringify({ diagnostic, requests })}`, { cause: error });
  }
  const preservedManualScroll = await cdp.evaluate("document.querySelector('#messages').scrollTop");
  if (preservedManualScroll !== 0) throw new Error(`manual-scroll-not-preserved:${preservedManualScroll}`);
  checks += 2;
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

  const boundedMarkdown = await cdp.evaluate(`(() => {
    const content = document.createElement('div');
    appendMarkdown(
      content,
      Array.from({ length: 3000 }, (_, index) => '- **bounded-' + index + '**').join('\\n'),
    );
    const fallback = content.querySelector('.markdown-render-limit');
    return {
      elements: content.querySelectorAll('*').length,
      fallbackPresent: Boolean(fallback),
      finalContentPreserved: fallback?.textContent.includes('bounded-2999') || false,
      scripts: content.querySelectorAll('script, img').length,
    };
  })()`);
  if (
    boundedMarkdown.elements > 2049
    || !boundedMarkdown.fallbackPresent
    || !boundedMarkdown.finalContentPreserved
    || boundedMarkdown.scripts !== 0
  ) throw new Error(`bounded-markdown-rendering:${JSON.stringify(boundedMarkdown)}`);
  checks += 4;

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
      status: document.querySelector('#prompt-history-status').textContent,
      inComposer: select.closest('#text-form') !== null,
      outsideSystemSettings: select.closest('.system-setting') === null
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
    || !configurableHistory.inComposer
    || !configurableHistory.outsideSystemSettings
  ) throw new Error(`configurable-prompt-history:${JSON.stringify(configurableHistory)}`);
  checks += 10;
  trace("prompt-history-verified");

  const chatTextSize = await cdp.evaluate(`(() => {
    const panel = document.querySelector('#text-panel');
    const message = document.querySelector('.message-content');
    const prompt = document.querySelector('#prompt');
    const smaller = document.querySelector('#decrease-chat-text');
    const larger = document.querySelector('#increase-chat-text');
    const result = {
      defaultState: state.chatTextSize,
      defaultDataset: panel.dataset.chatTextSize,
      defaultMessageSize: getComputedStyle(message).fontSize,
      defaultPromptSize: getComputedStyle(prompt).fontSize,
      defaultScale: document.querySelector('#chat-text-size-value').textContent,
      labels: [smaller.getAttribute('aria-label'), larger.getAttribute('aria-label')],
      defaultBounds: [smaller.disabled, larger.disabled],
    };
    smaller.click();
    result.smallState = state.chatTextSize;
    result.smallBound = smaller.disabled;
    result.smallScale = document.querySelector('#chat-text-size-value').textContent;
    larger.click();
    larger.click();
    result.largeState = state.chatTextSize;
    result.largeDataset = panel.dataset.chatTextSize;
    result.largeMessageSize = getComputedStyle(message).fontSize;
    result.largePromptSize = getComputedStyle(prompt).fontSize;
    result.largeScale = document.querySelector('#chat-text-size-value').textContent;
    larger.click();
    result.maximumState = state.chatTextSize;
    result.maximumBound = larger.disabled;
    result.maximumScale = document.querySelector('#chat-text-size-value').textContent;
    result.invalidRejected = applyChatTextSize('unsupported') === false
      && state.chatTextSize === 'extra-large';
    result.restored = applyChatTextSize('default')
      && state.chatTextSize === 'default'
      && panel.dataset.chatTextSize === 'default'
      && !smaller.disabled
      && !larger.disabled;
    return result;
  })()`);
  if (
    chatTextSize.defaultState !== "default"
    || chatTextSize.defaultDataset !== "default"
    || chatTextSize.defaultMessageSize !== "14px"
    || chatTextSize.defaultPromptSize !== "16px"
    || chatTextSize.defaultScale !== "100%"
    || JSON.stringify(chatTextSize.labels) !== JSON.stringify(["Make chat text smaller", "Make chat text larger"])
    || JSON.stringify(chatTextSize.defaultBounds) !== JSON.stringify([false, false])
    || chatTextSize.smallState !== "small"
    || !chatTextSize.smallBound
    || chatTextSize.smallScale !== "90%"
    || chatTextSize.largeState !== "large"
    || chatTextSize.largeDataset !== "large"
    || chatTextSize.largeMessageSize !== "16px"
    || chatTextSize.largePromptSize !== "18px"
    || chatTextSize.largeScale !== "115%"
    || chatTextSize.maximumState !== "extra-large"
    || !chatTextSize.maximumBound
    || chatTextSize.maximumScale !== "130%"
    || !chatTextSize.invalidRejected
    || !chatTextSize.restored
  ) throw new Error(`chat-text-size:${JSON.stringify(chatTextSize)}`);
  checks += 16;
  trace("chat-text-size-verified");

  const messagesBeforeStop = await cdp.evaluate("state.messages.length");
  await cdp.evaluate(`(() => {
    document.querySelector('#prompt').value = 'stop browser generation';
    document.querySelector('#text-form').requestSubmit();
  })()`);
  await waitFor(() => cdp.evaluate(
    "!document.querySelector('#stop-generation').classList.contains('hidden') && document.querySelector('#send-button').classList.contains('hidden')",
  ));
  await cdp.evaluate("document.querySelector('#stop-generation').click()");
  await waitFor(() => cdp.evaluate(
    "document.querySelector('#text-status').textContent === 'Generation stopped'",
  ));
  const stoppedGeneration = await cdp.evaluate(`({
    prompt: document.querySelector('#prompt').value,
    messages: state.messages.length,
    stopHidden: document.querySelector('#stop-generation').classList.contains('hidden'),
    sendVisible: !document.querySelector('#send-button').classList.contains('hidden'),
    taskEvent: document.querySelector('#task-event').textContent,
    connectionErrorHidden: document.querySelector('#connection-error').classList.contains('hidden')
  })`);
  if (
    stoppedGeneration.prompt !== "stop browser generation"
    || stoppedGeneration.messages !== messagesBeforeStop
    || !stoppedGeneration.stopHidden
    || !stoppedGeneration.sendVisible
    || !stoppedGeneration.taskEvent.includes("Generation stopped")
    || !stoppedGeneration.connectionErrorHidden
    || cancelledChatConnections !== 1
  ) throw new Error(`stop-generation:${JSON.stringify(stoppedGeneration)}:${cancelledChatConnections}`);
  checks += 7;
  trace("stop-generation-verified");

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
  checks += 10;

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
  const explicitModes = await cdp.evaluate(`(() => {
    const select = document.querySelector('#text-mode');
    const result = {options: select.options.length};
    select.value = 'content.write';
    select.dispatchEvent(new Event('change', {bubbles: true}));
    result.writingTitle = document.querySelector('#capability-title').textContent;
    result.writingCapability = state.capabilityId;
    select.value = 'content.summarize';
    select.dispatchEvent(new Event('change', {bubbles: true}));
    result.summaryTitle = document.querySelector('#capability-title').textContent;
    result.summaryCapability = state.capabilityId;
    select.value = 'automatic';
    select.dispatchEvent(new Event('change', {bubbles: true}));
    result.automaticTitle = document.querySelector('#capability-title').textContent;
    result.automaticCapability = state.capabilityId;
    return result;
  })()`);
  if (
    explicitModes.options !== 4
    || explicitModes.writingTitle !== "Draft content"
    || explicitModes.writingCapability !== "content.write"
    || explicitModes.summaryTitle !== "Summarize text"
    || explicitModes.summaryCapability !== "content.summarize"
    || explicitModes.automaticTitle !== "Private conversation"
    || explicitModes.automaticCapability !== "general.chat"
  ) throw new Error(`explicit-text-modes:${JSON.stringify(explicitModes)}`);
  const taskModePicker = await cdp.evaluate(`(() => {
    document.querySelector('#conversation-settings').open = true;
    const button = document.querySelector('#text-mode-button');
    const menu = document.querySelector('#text-mode-options');
    button.click();
    const opened = button.getAttribute('aria-expanded') === 'true' && !menu.classList.contains('hidden');
    const initiallyFocused = document.activeElement?.dataset.value;
    document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {key: 'ArrowDown', bubbles: true}));
    const arrowFocused = document.activeElement?.dataset.value;
    document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
    const selected = document.querySelector('#text-mode').value;
    const buttonLabel = document.querySelector('#text-mode-button-label').textContent;
    const closedAfterSelection = button.getAttribute('aria-expanded') === 'false' && menu.classList.contains('hidden');
    button.click();
    document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
    const escapeReturnedFocus = document.activeElement === button && menu.classList.contains('hidden');
    chooseTaskMode('automatic');
    document.querySelector('#conversation-settings').open = false;
    return {
      opened, initiallyFocused, arrowFocused, selected, buttonLabel,
      closedAfterSelection, escapeReturnedFocus,
      hasListbox: menu.getAttribute('role') === 'listbox',
      optionCount: menu.querySelectorAll('[role="option"]').length
    };
  })()`);
  if (
    !taskModePicker.opened
    || taskModePicker.initiallyFocused !== "automatic"
    || taskModePicker.arrowFocused !== "general.chat"
    || taskModePicker.selected !== "general.chat"
    || taskModePicker.buttonLabel !== "Chat"
    || !taskModePicker.closedAfterSelection
    || !taskModePicker.escapeReturnedFocus
    || !taskModePicker.hasListbox
    || taskModePicker.optionCount !== 4
  ) throw new Error(`task-mode-picker:${JSON.stringify(taskModePicker)}`);
  checks += 23;
  trace("alpha-unified-text-conversation-verified");

  const contextSelection = await cdp.evaluate(`(async () => {
    await addContextFiles([
      new File(
        ['# Browser context\\nThe project codename is Meadow.\\n<img src=x onerror=alert(1)>'],
        'A. Budin (#12) – 2026 Season Stats.txt',
        {type: 'text/plain'}
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
    || contextSelection.name !== "A. Budin (#12) – 2026 Season Stats.txt"
    || !contextSelection.status.includes("1 text file")
    || !contextSelection.status.includes("tokens")
    || !contextSelection.networkWarningHidden
    || !contextSelection.policy.includes("never runs attached code")
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
  const bidiContextNameBlocked = await cdp.evaluate(`(async () => {
    try {
      await addContextFiles([new File(['text'], 'notes\\u202etxt.txt', {type: 'text/plain'})]);
      return false;
    } catch (error) {
      return error.message === 'invalid-context-file-name' && state.contextFiles.length === 1;
    }
  })()`);
  if (!bidiContextNameBlocked) throw new Error("bidi-context-filename-not-blocked");
  checks += 1;
  const contextErrorRouting = await cdp.evaluate(`(async () => {
    clearError();
    clearContextError();
    const input = document.querySelector('#context-files');
    const transfer = new DataTransfer();
    transfer.items.add(new File(['blocked fixture'], 'blocked.sh', {type: 'text/plain'}));
    input.files = transfer.files;
    input.dispatchEvent(new Event('change', {bubbles: true}));
    await new Promise((resolve) => setTimeout(resolve, 0));
    const box = document.querySelector('#context-error');
    const result = {
      visible: !box.classList.contains('hidden'),
      message: box.textContent,
      focused: document.activeElement?.id || '',
      connectionErrorHidden: document.querySelector('#connection-error').classList.contains('hidden'),
      fileCount: state.contextFiles.length,
    };
    clearContextError();
    result.cleared = box.classList.contains('hidden') && box.textContent === '';
    return result;
  })()`);
  if (
    !contextErrorRouting.visible
    || contextErrorRouting.message !== "That file type isn't supported yet. Choose a text, CSV, JSON, source code, or PNG file."
    || contextErrorRouting.focused !== "context-error"
    || !contextErrorRouting.connectionErrorHidden
    || contextErrorRouting.fileCount !== 1
    || !contextErrorRouting.cleared
  ) throw new Error(`context-error-routing:${JSON.stringify(contextErrorRouting)}`);
  const structuredContext = await cdp.evaluate(`(async () => {
    await addContextAttachments([
      new File(['name,note\\nalpha,"quoted, inert formula =CMD()"\\n'], 'records.csv', {type: 'text/csv'}),
      new File(['{"enabled":false,"instruction":"rm -rf is inert text"}'], 'settings.json', {type: 'application/json'})
    ]);
    const result = {
      count: state.contextFiles.length,
      mediaTypes: state.contextFiles.map((item) => item.mediaType),
      metadata: [...document.querySelectorAll('.context-file-meta')].map((item) => item.textContent),
      summaries: [...document.querySelectorAll('.context-preview summary')].map((item) => item.textContent),
      previewLabels: [...document.querySelectorAll('.context-preview summary')].map((item) => item.getAttribute('aria-label'))
    };
    state.contextFiles.splice(-2, 2);
    renderContextFiles();
    result.remaining = state.contextFiles.length;
    return result;
  })()`);
  if (
    structuredContext.count !== 3
    || structuredContext.remaining !== 1
    || structuredContext.mediaTypes.at(-2) !== "text/csv"
    || structuredContext.mediaTypes.at(-1) !== "application/json"
    || !structuredContext.metadata.some((value) => value.startsWith("CSV ·"))
    || !structuredContext.metadata.some((value) => value.startsWith("JSON ·"))
    || structuredContext.summaries.filter((value) => value === "Preview").length < 2
    || !structuredContext.previewLabels.includes("Preview selected CSV")
    || !structuredContext.previewLabels.includes("Preview selected JSON")
  ) throw new Error(`structured-context:${JSON.stringify(structuredContext)}`);
  const sourceContext = await cdp.evaluate(`(async () => {
    await addContextAttachments([
      new File(['import os\\nos.system("must remain inert")\\n'], 'worker.py', {type: 'text/x-python'}),
      new File(['export const Panel = () => <script>{"inert"}</script>;\\n'], 'panel.tsx', {type: 'text/typescript'})
    ]);
    const result = {
      count: state.contextFiles.length,
      mediaTypes: state.contextFiles.map((item) => item.mediaType),
      metadata: [...document.querySelectorAll('.context-file-meta')].map((item) => item.textContent),
      summaries: [...document.querySelectorAll('.context-preview summary')].map((item) => item.textContent),
      previewLabels: [...document.querySelectorAll('.context-preview summary')].map((item) => item.getAttribute('aria-label')),
      previews: [...document.querySelectorAll('.context-preview pre')].map((item) => item.textContent),
      activeElements: document.querySelectorAll('.context-preview script, .context-preview img').length
    };
    state.contextFiles.splice(-2, 2);
    renderContextFiles();
    result.remaining = state.contextFiles.length;
    return result;
  })()`);
  if (
    sourceContext.count !== 3
    || sourceContext.remaining !== 1
    || sourceContext.mediaTypes.at(-2) !== "text/plain"
    || sourceContext.mediaTypes.at(-1) !== "text/plain"
    || sourceContext.metadata.filter((value) => value.startsWith("Source ·")).length !== 2
    || sourceContext.summaries.filter((value) => value === "Preview").length < 2
    || sourceContext.previewLabels.filter((value) => value === "Preview selected Source").length !== 2
    || !sourceContext.previews.some((value) => value.includes('os.system("must remain inert")'))
    || !sourceContext.previews.some((value) => value.includes('<script>{"inert"}</script>'))
    || sourceContext.activeElements !== 0
  ) throw new Error(`source-context:${JSON.stringify(sourceContext)}`);
  const hostileSourceBlocked = await cdp.evaluate(`(async () => {
    const before = state.contextFiles.map((item) => item.name);
    const errors = [];
    for (const file of [
      new File(['echo hostile'], 'script.sh', {type: 'text/plain'}),
      new File(['Write-Host hostile'], 'script.ps1', {type: 'text/plain'})
    ]) {
      try {
        await addContextAttachments([file]);
      } catch (error) {
        errors.push(error.message);
      }
    }
    return {
      before,
      after: state.contextFiles.map((item) => item.name),
      errors
    };
  })()`);
  if (
    JSON.stringify(hostileSourceBlocked.before) !== JSON.stringify(hostileSourceBlocked.after)
    || hostileSourceBlocked.errors.length !== 2
    || hostileSourceBlocked.errors.some((value) => value !== "invalid-context-file-type")
  ) throw new Error(`hostile-source-context:${JSON.stringify(hostileSourceBlocked)}`);
  const masqueradedContentBlocked = await cdp.evaluate(`(async () => {
    const before = state.contextFiles.map((item) => item.name);
    const errors = [];
    const hostile = [
      new File(['#Requires -Version 7.0\\nWrite-Host hostile\\n'], 'renamed-powershell.txt', {type: 'text/plain'}),
      new File(['Write-Host hostile\\n'], 'renamed-simple-powershell.txt', {type: 'text/plain'}),
      new File(['#!/usr/bin/env bash\\necho hostile\\n'], 'renamed-shell.md', {type: 'text/markdown'}),
      new File(['@echo off\\necho hostile\\n'], 'renamed-batch.txt', {type: 'text/plain'}),
      new File([new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x2d, 0x31, 0x2e, 0x37])], 'renamed-pdf.txt', {type: 'text/plain'}),
    ];
    for (const file of hostile) {
      try {
        await addContextAttachments([file]);
      } catch (error) {
        errors.push(error.message);
      }
    }
    const friendly = humanError(new Error("context-file-content-type-mismatch"));
    await addContextAttachments([
      new File(['PowerShell example for review only:\\nWrite-Host remains inert text.\\n'], 'benign-notes.txt', {type: 'text/plain'}),
      new File(['#!/usr/bin/env python3\\nprint("inert")\\n'], 'valid-shebang.py', {type: 'text/x-python'}),
    ]);
    const accepted = state.contextFiles.slice(-2).map((item) => item.name);
    state.contextFiles.splice(-2, 2);
    renderContextFiles();
    return {
      before,
      after: state.contextFiles.map((item) => item.name),
      errors,
      friendly,
      accepted,
    };
  })()`);
  if (
    JSON.stringify(masqueradedContentBlocked.before) !== JSON.stringify(masqueradedContentBlocked.after)
    || masqueradedContentBlocked.errors.length !== 5
    || masqueradedContentBlocked.errors.some((value) => value !== "context-file-content-type-mismatch")
    || masqueradedContentBlocked.friendly !== "This file's contents do not match its name. For safety, attach the original supported text, source-code, CSV, JSON, or PNG file."
    || JSON.stringify(masqueradedContentBlocked.accepted) !== JSON.stringify(["benign-notes.txt", "valid-shebang.py"])
  ) throw new Error(`masqueraded-context:${JSON.stringify(masqueradedContentBlocked)}`);
  checks += 5;
  const invalidStructuredBlocked = await cdp.evaluate(`(async () => {
    const before = state.contextFiles.length;
    const errors = [];
    for (const file of [
      new File(['{"open":'], 'broken.json', {type: 'application/json'}),
      new File(['header\\n"unterminated'], 'broken.csv', {type: 'text/csv'})
    ]) {
      try {
        await addContextAttachments([file]);
      } catch (error) {
        errors.push(error.message);
      }
    }
    const friendly = [
      "invalid-context-file-type",
      "invalid-context-json",
      "context-json-too-complex",
      "invalid-context-csv",
      "context-csv-too-complex",
    ].map((code) => humanError(new Error(code)));
    return {before, after: state.contextFiles.length, errors, friendly};
  })()`);
  if (
    invalidStructuredBlocked.before !== invalidStructuredBlocked.after
    || invalidStructuredBlocked.errors[0] !== "invalid-context-json"
    || invalidStructuredBlocked.errors[1] !== "invalid-context-csv"
    || invalidStructuredBlocked.friendly[0] !== "That file type isn't supported yet. Choose a text, CSV, JSON, source code, or PNG file."
    || invalidStructuredBlocked.friendly[1] !== "The selected JSON file is malformed."
    || invalidStructuredBlocked.friendly[2] !== "That JSON file is too deeply nested or complex for this version of Haven 42."
    || invalidStructuredBlocked.friendly[3] !== "The selected CSV file is malformed."
    || invalidStructuredBlocked.friendly[4] !== "That CSV file has too many rows or columns, or contains a cell that is too large."
  ) throw new Error(`invalid-structured-context:${JSON.stringify(invalidStructuredBlocked)}`);
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
  checks += 28;

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
    result.screenshotLimitLockedDuringTask = document.querySelector('#context-image-limit').disabled;
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
  const browseRestoredAfterTask = await cdp.evaluate(`(
    !document.querySelector('#context-files').disabled
    && !document.querySelector('#browse-context').disabled
    && !document.querySelector('#context-image-limit').disabled
  )`);
  if (
    !disclosureSubmit.warningVisible
    || !disclosureSubmit.warning.includes("will be sent")
    || !disclosureSubmit.warning.includes("Only continue if you trust that server")
    || !disclosureSubmit.checkboxAbsent
    || !disclosureSubmit.browseLockedDuringTask
    || !disclosureSubmit.browseButtonLockedDuringTask
    || !disclosureSubmit.screenshotLimitLockedDuringTask
    || !browseRestoredAfterTask
    || chatPayloads.length !== chatRequestsBeforeDisclosure + 1
  ) throw new Error(`private-context-disclosure:${JSON.stringify(disclosureSubmit)}`);
  checks += 9;
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
    || !screenshotUi.warning.includes("has not confirmed")
  ) throw new Error(`screenshot-paste:${JSON.stringify({screenshotPaste, screenshotUi})}`);
  const advancedScreenshotLimit = await cdp.evaluate(`(async () => {
    const select = document.querySelector('#context-image-limit');
    const initial = {
      selected: select.value,
      stateLimit: state.contextImageLimit,
      status: document.querySelector('#context-image-limit-status').textContent,
      style: {
        height: getComputedStyle(select).height,
        fontSize: getComputedStyle(select).fontSize,
        paddingLeft: getComputedStyle(select).paddingLeft,
        paddingRight: getComputedStyle(select).paddingRight,
      },
    };
    select.value = '4';
    select.dispatchEvent(new Event('change', {bubbles: true}));
    const encoded = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=';
    const bytes = Uint8Array.from(atob(encoded), (value) => value.charCodeAt(0));
    await addContextImages([
      new Blob([bytes], {type: 'image/png'}),
      new Blob([bytes], {type: 'image/png'}),
      new Blob([bytes], {type: 'image/png'}),
    ]);
    let fifthBlocked = false;
    try {
      await addContextImage(new Blob([bytes], {type: 'image/png'}));
    } catch (error) {
      fifthBlocked = error.message === 'invalid-context-image-count';
    }
    select.value = '2';
    select.dispatchEvent(new Event('change', {bubbles: true}));
    const rejectedLowering = {
      selected: select.value,
      stateLimit: state.contextImageLimit,
      error: document.querySelector('#context-error').textContent,
    };
    state.contextImages.splice(1);
    renderContextFiles();
    return {
      initial,
      selected: select.value,
      stateLimit: state.contextImageLimit,
      count: state.contextImages.length,
      fifthBlocked,
      rejectedLowering,
    };
  })()`);
  if (
    advancedScreenshotLimit.initial.selected !== "2"
    || advancedScreenshotLimit.initial.stateLimit !== 2
    || !advancedScreenshotLimit.initial.status.includes("Up to 2 screenshots")
    || JSON.stringify(advancedScreenshotLimit.initial.style) !== JSON.stringify({
      height: "44px",
      fontSize: "14px",
      paddingLeft: "10px",
      paddingRight: "34px",
    })
    || advancedScreenshotLimit.selected !== "4"
    || advancedScreenshotLimit.stateLimit !== 4
    || advancedScreenshotLimit.count !== 1
    || !advancedScreenshotLimit.fifthBlocked
    || advancedScreenshotLimit.rejectedLowering.selected !== "4"
    || advancedScreenshotLimit.rejectedLowering.stateLimit !== 4
    || !advancedScreenshotLimit.rejectedLowering.error.includes("Remove screenshots")
  ) throw new Error(`advanced-screenshot-limit:${JSON.stringify(advancedScreenshotLimit)}`);
  const unsupportedScreenshotBlocked = await cdp.evaluate(`(async () => {
    try {
      await addContextImage(new Blob(['jpeg'], {type: 'image/jpeg'}));
      return false;
    } catch (error) {
      return error.message === 'invalid-context-image-type' && state.contextImages.length === 1;
    }
  })()`);
  if (!unsupportedScreenshotBlocked) throw new Error("unsupported-screenshot-not-blocked");
  checks += 19;

  const chatRequestsBeforeScreenshot = chatPayloads.length;
  await cdp.evaluate(`(() => {
    document.querySelector('#prompt').value = 'Describe the pasted screenshot.';
    document.querySelector('#text-form').requestSubmit();
  })()`);
  await waitFor(() => chatPayloads.length === chatRequestsBeforeScreenshot + 1);
  await waitFor(() => cdp.evaluate(
    "document.querySelector('#task-event').textContent.includes('has not confirmed that this model can understand screenshots')",
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
    screenshotBrowseControl.accept !== ".txt,.md,.csv,.json,.cs,.py,.js,.jsx,.ts,.tsx,.java,.go,.rs,.sql,.tf,.png,text/plain,text/markdown,text/csv,application/json,image/png"
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
    const surface = document.querySelector('.composer-surface');
    const surfaceBox = surface.getBoundingClientRect();
    const context = document.querySelector('.context-panel');
    const contextBox = context.getBoundingClientRect();
    const composer = document.querySelector('#text-form').getBoundingClientRect();
    return {
      surfaceInsidePanel: surfaceBox.top >= panel.top && surfaceBox.bottom <= panel.bottom + 1,
      composerInsidePanel: composer.top >= panel.top && composer.bottom <= panel.bottom + 1,
      panelTop: panel.top,
      panelBottom: panel.bottom,
      surfaceTop: surfaceBox.top,
      surfaceBottom: surfaceBox.bottom,
      surfaceBottomOverflow: Math.max(0, surfaceBox.bottom - panel.bottom),
      composerBottomOverflow: Math.max(0, composer.bottom - panel.bottom),
      composerIntegrated: document.querySelector('#text-form') === surface,
      contextIntegrated: context.parentElement === surface,
      contextHeight: contextBox.height,
      contextScrollable: context.scrollHeight > context.clientHeight,
      contextOverflow: getComputedStyle(context).overflowY,
      messageMinHeight: getComputedStyle(document.querySelector('#messages')).minHeight,
      policyInsideSettings: document.querySelector('.context-settings').contains(document.querySelector('.context-policy'))
    };
  })()`);
  await cdp.call("Emulation.clearDeviceMetricsOverride");
  if (
    attachmentLayout.surfaceBottomOverflow > 24
    || attachmentLayout.composerBottomOverflow > 24
    || !attachmentLayout.composerIntegrated
    || !attachmentLayout.contextIntegrated
    || attachmentLayout.contextHeight > 97
    || !attachmentLayout.contextScrollable
    || attachmentLayout.contextOverflow !== "auto"
    || attachmentLayout.messageMinHeight !== "0px"
    || !attachmentLayout.policyInsideSettings
  ) throw new Error(`attachment-layout:${JSON.stringify(attachmentLayout)}`);
  const documentContextBrowseCleanup = await cdp.evaluate(`(() => {
    document.querySelector('#clear-context').click();
    return {
      files: state.contextFiles.length,
      images: state.contextImages.length,
      emptyContextHeight: document.querySelector('.context-panel').getBoundingClientRect().height,
    };
  })()`);
  if (
    documentContextBrowseCleanup.files !== 0
    || documentContextBrowseCleanup.images !== 0
    || documentContextBrowseCleanup.emptyContextHeight > 80
  ) {
    throw new Error(`screenshot-browse-cleanup:${JSON.stringify(documentContextBrowseCleanup)}`);
  }
  checks += 17;
  trace("document-context-verified");

  const alphaHiddenCapabilities = await cdp.evaluate(`({
    softwareNavHidden: document.querySelector('#software-nav').classList.contains('hidden'),
    softwareNavAriaHidden: document.querySelector('#software-nav').getAttribute('aria-hidden'),
    softwareNavTabIndex: document.querySelector('#software-nav').tabIndex,
    imageNavHidden: document.querySelector('#image-nav').classList.contains('hidden'),
    imageNavAriaHidden: document.querySelector('#image-nav').getAttribute('aria-hidden'),
    imageNavTabIndex: document.querySelector('#image-nav').tabIndex,
    modelCapabilityOptions: document.querySelectorAll('#model-search-capability option').length
  })`);
  if (
    !alphaHiddenCapabilities.softwareNavHidden
    || alphaHiddenCapabilities.softwareNavAriaHidden !== "true"
    || alphaHiddenCapabilities.softwareNavTabIndex !== -1
    || !alphaHiddenCapabilities.imageNavHidden
    || alphaHiddenCapabilities.imageNavAriaHidden !== "true"
    || alphaHiddenCapabilities.imageNavTabIndex !== -1
    || alphaHiddenCapabilities.modelCapabilityOptions !== 3
  ) throw new Error(`alpha-hidden-capabilities:${JSON.stringify(alphaHiddenCapabilities)}`);
  checks += 8;
  trace("alpha-hidden-capabilities-verified");

  await cdp.call("Emulation.setEmulatedMedia", {
    media: "screen",
    features: [{name: "prefers-reduced-motion", value: "reduce"}],
  });
  await cdp.evaluate(`(() => {
    const originalFetch = window.fetch.bind(window);
    window.__haven42DiagnosticFetchCount = 0;
    window.fetch = (...args) => {
      const target = typeof args[0] === 'string' ? args[0] : args[0]?.url;
      if (target === '/api/alpha/diagnostics') window.__haven42DiagnosticFetchCount += 1;
      return originalFetch(...args);
    };
  })()`);
  const navigation = await cdp.evaluate(`(async () => {
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
    for (let attempt = 0; attempt < 100; attempt += 1) {
      const setupLabel = document.querySelector('#setup-local-components').textContent;
      const uninstallLabel = document.querySelector('#remove-managed-components').textContent;
      if (!setupLabel.startsWith('Checking') && !uninstallLabel.startsWith('Checking')) break;
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
    const system = {
      active: document.querySelector('#system-nav').classList.contains('active'),
      focused: document.activeElement.id,
      visible: !document.querySelector('#system-panel').classList.contains('hidden'),
      sidebarForms: document.querySelectorAll('.configuration-column form').length,
      sidebarStatus: document.querySelector('#sidebar-connection-status').textContent,
      sidebarDetailsAction: document.querySelector('#view-system-details').textContent,
      diagnosticStatus: document.querySelector('#diagnostics-status').textContent,
      diagnosticRows: document.querySelectorAll('#diagnostic-events li').length,
      diagnosticActions: document.querySelectorAll('#diagnostics-control button').length,
      diagnosticPrivacy: document.querySelector('#diagnostics-control').textContent,
      maintenanceHeading: document.querySelector('#local-ai-maintenance-title').textContent,
      localSetupLabel: document.querySelector('#setup-local-components').textContent,
      localSetupDisabled: document.querySelector('#setup-local-components').disabled,
      uninstallLabel: document.querySelector('#remove-managed-components').textContent,
      uninstallDisabled: document.querySelector('#remove-managed-components').disabled,
    };
    document.querySelector('#assurance-nav').click();
    const assurance = {
      active: document.querySelector('#assurance-nav').classList.contains('active'),
      visible: !document.querySelector('#assurance-panel').classList.contains('hidden'),
      modelsHidden: document.querySelector('#models-panel').classList.contains('hidden'),
      focused: document.activeElement.id,
      rows: document.querySelectorAll('#assurance-surface-list .assurance-item').length,
    };
    document.querySelector('#about-nav').click();
    const about = {
      active: document.querySelector('#about-nav').classList.contains('active'),
      visible: !document.querySelector('#about-panel').classList.contains('hidden'),
      modelsHidden: document.querySelector('#models-panel').classList.contains('hidden'),
      assuranceHidden: document.querySelector('#assurance-panel').classList.contains('hidden'),
      focused: document.activeElement.id,
      version: document.querySelector('#about-version').textContent,
    };
    return {reducedMotion, models, system, assurance, about};
  })()`);
  const localSetupUnavailable = navigation.system.localSetupLabel === "Local setup unavailable on this system";
  const localSetupChecking = navigation.system.localSetupLabel === "Checking local setup…"
    && navigation.system.localSetupDisabled
    && navigation.system.uninstallLabel === "Checking installed components…"
    && navigation.system.uninstallDisabled;
  const localSetupControlsValid = localSetupChecking || (localSetupUnavailable
    ? navigation.system.localSetupDisabled
      && navigation.system.uninstallLabel === "Uninstall unavailable on this system"
      && navigation.system.uninstallDisabled
    : navigation.system.localSetupLabel.includes("local AI")
      && navigation.system.uninstallLabel.includes("local AI components"));
  if (
    navigation.reducedMotion !== "auto"
    || !navigation.models.active
    || navigation.models.focused !== "models-title"
    || !navigation.models.visible
    || !navigation.models.imageHidden
    || navigation.models.installed !== 2
    || !navigation.system.active
    || navigation.system.focused !== "system-workspace-title"
    || !navigation.system.visible
    || navigation.system.sidebarForms !== 0
    || !navigation.system.sidebarStatus
    || !navigation.system.sidebarDetailsAction.includes("View system details")
    || navigation.system.diagnosticStatus.includes("Loading")
    || navigation.system.diagnosticRows < 1
    || navigation.system.diagnosticActions !== 4
    || !navigation.system.diagnosticPrivacy.includes("never recorded or uploaded")
    || navigation.system.maintenanceHeading !== "Local AI on this computer"
    || !localSetupControlsValid
    || !navigation.assurance.active
    || !navigation.assurance.visible
    || !navigation.assurance.modelsHidden
    || navigation.assurance.focused !== "assurance-title"
    || navigation.assurance.rows !== 4
    || !navigation.about.active
    || !navigation.about.visible
    || !navigation.about.modelsHidden
    || !navigation.about.assuranceHidden
    || navigation.about.focused !== "about-title"
    || !navigation.about.version.startsWith("v")
  ) throw new Error(`accessible-navigation:${JSON.stringify(navigation)}`);
  checks += 30;
  trace("accessible-navigation-verified");

  await cdp.evaluate("document.querySelector('#prepare-problem-report').click()");
  await waitFor(async () => (
    await cdp.evaluate(`(() => {
      const status = document.querySelector('#problem-report-status').textContent;
      return status && !status.includes('Checking general computer details');
    })()`)
  ));
  const problemReport = await cdp.evaluate(`(() => ({
    details: document.querySelector('#problem-report-details').value,
    status: document.querySelector('#problem-report-status').textContent,
    formUrl: document.querySelector('.alpha-reporting a').href,
  }))()`);
  if (
    !problemReport.details.includes("Haven 42:")
    || !problemReport.details.includes("Operating system:")
    || !problemReport.details.includes("Memory:")
    || !problemReport.details.includes("Graphics:")
    || !problemReport.details.includes("no hostname, username, address, local path, prompt, response, or file name included")
    || !problemReport.status.includes("details")
    || problemReport.formUrl !== "https://github.com/hysel/haven-42/issues/new?template=alpha-bug-report.yml"
  ) throw new Error(`problem-report-helper:${JSON.stringify(problemReport)}`);
  checks += 7;
  trace("problem-report-helper-verified");

  await waitFor(async () => (
    await cdp.evaluate("window.__haven42DiagnosticFetchCount >= 1")
  ));
  await delay(200);
  const diagnosticsBeforeDisclosure = await cdp.evaluate("window.__haven42DiagnosticFetchCount");
  await cdp.evaluate(`(() => {
    document.querySelector('#system-nav').click();
    const disclosure = document.querySelector('#diagnostics-control');
    disclosure.open = false;
    disclosure.open = true;
    disclosure.dispatchEvent(new Event('toggle'));
  })()`);
  await waitFor(async () => (
    await cdp.evaluate(`window.__haven42DiagnosticFetchCount > ${diagnosticsBeforeDisclosure}`)
  ));
  checks += 2;
  trace("diagnostics-auto-refresh-verified");

  if (localSetupUnavailable) {
    const unavailableLocalSetup = await cdp.evaluate(`(async () => {
      const response = await fetch('/api/alpha/setup-status', {credentials: 'same-origin', cache: 'no-store'});
      const body = await response.json();
      return {
        status: response.status,
        error: body.error,
        setupDisabled: document.querySelector('#setup-local-components').disabled,
        uninstallDisabled: document.querySelector('#remove-managed-components').disabled,
      };
    })()`);
    if (
      unavailableLocalSetup.status !== 404
      || !/^(windows|linux)-alpha-setup-unavailable$/.test(unavailableLocalSetup.error)
      || !unavailableLocalSetup.setupDisabled
      || !unavailableLocalSetup.uninstallDisabled
    ) throw new Error(`unavailable-local-setup:${JSON.stringify(unavailableLocalSetup)}`);
    checks += 4;
    trace("unavailable-local-setup-verified");
  } else {
  const localSetupReturn = await cdp.evaluate(`(async () => {
    document.querySelector('#system-nav').click();
    const response = await fetch('/api/alpha/setup-status', {credentials: 'same-origin', cache: 'no-store'});
    const status = await response.json();
    renderManagedStorageStatus({
      ...status,
      managedComponentsState: 'empty',
      managedComponentsPresent: false,
      legacyManagedComponentsPresent: false,
      completedSetupCandidate: false,
    });
    const connectedBefore = state.connected;
    document.querySelector('#setup-local-components').click();
    await new Promise((resolve) => setTimeout(resolve, 50));
    const wizardVisible = !document.querySelector('#setup-wizard').classList.contains('hidden');
    const readinessVisible = !document.querySelector('[data-wizard-step="readiness"]').classList.contains('hidden');
    document.querySelector('#wizard-readiness-back').click();
    return {
      connectedBefore,
      connectedAfter: state.connected,
      wizardVisible,
      readinessVisible,
      wizardClosed: document.querySelector('#setup-wizard').classList.contains('hidden'),
      promptEnabled: !document.querySelector('#prompt').disabled,
      focused: document.activeElement.id,
    };
  })()`);
  if (
    !localSetupReturn.connectedBefore || !localSetupReturn.connectedAfter
    || !localSetupReturn.wizardVisible || !localSetupReturn.readinessVisible
    || !localSetupReturn.wizardClosed || !localSetupReturn.promptEnabled
    || localSetupReturn.focused !== "setup-local-components"
  ) throw new Error(`local-setup-return:${JSON.stringify(localSetupReturn)}`);
  checks += 7;
  trace("local-setup-return-verified");

  await cdp.evaluate(`(async () => {
    const response = await fetch('/api/alpha/setup-status', {credentials: 'same-origin', cache: 'no-store'});
    const status = await response.json();
    renderManagedStorageStatus({
      ...status,
      managedComponentsState: 'managed',
      managedComponentsPresent: true,
      legacyManagedComponentsPresent: false,
      completedSetupCandidate: true,
    });
    document.querySelector('#setup-local-components').click();
  })()`);
  await waitFor(() => cdp.evaluate(`(
    !document.querySelector('#setup-wizard').classList.contains('hidden')
    && !document.querySelector('[data-wizard-step="readiness"]').classList.contains('hidden')
    && document.querySelector('#local-setup-action-status').textContent.includes('current AI connection was kept unchanged')
  )`));
  const missingLocalRecovery = await cdp.evaluate(`({
    connected: state.connected,
    promptEnabled: !document.querySelector('#prompt').disabled,
    wizardVisible: !document.querySelector('#setup-wizard').classList.contains('hidden'),
    readinessVisible: !document.querySelector('[data-wizard-step="readiness"]').classList.contains('hidden'),
    recoveryText: document.querySelector('#local-setup-action-status').textContent,
  })`);
  if (
    !missingLocalRecovery.connected || !missingLocalRecovery.promptEnabled
    || !missingLocalRecovery.wizardVisible || !missingLocalRecovery.readinessVisible
    || !missingLocalRecovery.recoveryText.includes("review or repair")
  ) throw new Error(`missing-local-recovery:${JSON.stringify(missingLocalRecovery)}`);
  await cdp.evaluate("document.querySelector('#wizard-readiness-back').click()");
  await waitFor(() => cdp.evaluate("document.querySelector('#setup-wizard').classList.contains('hidden')"));
  checks += 5;
  trace("missing-local-recovery-verified");
  }

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

  const postRemoval = await cdp.evaluate(`(() => {
    state.contextFiles = [{name: 'temporary.txt', mediaType: 'text/plain', sizeBytes: 4, content: 'test'}];
    state.promptHistory = ['private prompt'];
    showPostRemovalExperience();
    return {
      connected: state.connected,
      providerConfig: state.providerConfig,
      messages: state.messages.length,
      contextFiles: state.contextFiles.length,
      promptHistory: state.promptHistory.length,
      wizardVisible: !document.querySelector('#setup-wizard').classList.contains('hidden'),
      removedVisible: !document.querySelector('[data-wizard-step="removed"]').classList.contains('hidden'),
      progressHidden: document.querySelector('.wizard-progress').classList.contains('hidden'),
      focused: document.activeElement.id,
      promptDisabled: document.querySelector('#prompt').disabled,
      actionCount: document.querySelectorAll('#removed-actions button').length,
      heading: document.querySelector('#removed-title').textContent,
      detail: document.querySelector('[data-wizard-step="removed"]').textContent,
    };
  })()`);
  if (
    postRemoval.connected
    || postRemoval.providerConfig !== null
    || postRemoval.messages !== 0
    || postRemoval.contextFiles !== 0
    || postRemoval.promptHistory !== 0
    || !postRemoval.wizardVisible
    || !postRemoval.removedVisible
    || !postRemoval.progressHidden
    || postRemoval.focused !== "removed-guided"
    || !postRemoval.promptDisabled
    || postRemoval.actionCount !== 3
    || !postRemoval.heading.includes("removed successfully")
    || !postRemoval.detail.includes("Haven42-Logs")
  ) throw new Error(`post-removal-experience:${JSON.stringify(postRemoval)}`);
  await cdp.evaluate("document.querySelector('#removed-existing').click()");
  const postRemovalExternal = await cdp.evaluate(`({
    providerVisible: !document.querySelector('[data-wizard-step="provider"]').classList.contains('hidden'),
    progressVisible: !document.querySelector('.wizard-progress').classList.contains('hidden'),
    focused: document.activeElement.id
  })`);
  if (!postRemovalExternal.providerVisible || !postRemovalExternal.progressVisible || postRemovalExternal.focused !== "wizard-endpoint") {
    throw new Error(`post-removal-external:${JSON.stringify(postRemovalExternal)}`);
  }
  const diagnosticCleanup = await cdp.evaluate(`fetch('/api/alpha/diagnostics/remove', {
    method: 'POST',
    credentials: 'same-origin',
    headers: {'Content-Type': 'application/json', 'X-Haven-Token': state.token},
    body: JSON.stringify({confirmed: true})
  }).then(async (response) => ({status: response.status, body: await response.json()}))`);
  if (
    diagnosticCleanup.status !== 200
    || diagnosticCleanup.body.removed !== true
    || diagnosticCleanup.body.directoryName !== "Haven42-Logs"
  ) throw new Error(`diagnostic-cleanup:${JSON.stringify(diagnosticCleanup)}`);
  checks += 16;
  trace("post-removal-experience-verified");

  const managedDefaultHandoff = await cdp.evaluate(`(() => {
    state.modelSelections = Object.fromEntries(
      Object.keys(CAPABILITIES).map((capabilityId) => [capabilityId, {mode: 'none', model: null}])
    );
    const recommendations = Object.fromEntries(
      Object.keys(CAPABILITIES).map((capabilityId) => [capabilityId, {
        status: 'validated', model: 'qwen3.5:0.8b', automatic: true,
        digestVerified: true, hardwareFit: 'validated-on-this-device',
        evidenceId: 'windows-alpha-qwen35-08b-q8-managed-self-test'
      }])
    );
    applyProviderConnection({
      models: ['qwen3.5:0.8b'],
      modelOptions: [{
        name: 'qwen3.5:0.8b', digestVerified: true,
        capabilityStatus: Object.fromEntries(
          Object.keys(CAPABILITIES).map((capabilityId) => [capabilityId, 'validated'])
        )
      }],
      manualModelCandidates: [{
        name: 'candidate-chat:7b', automatic: false, downloadRequiresApproval: true,
        hardwareFit: 'matched-tested-hardware-profile',
        profileId: 'windows-amd-radeon-rx7800xt-16gib', minimumOllamaVersion: '0.32.9',
        capabilityStatus: Object.fromEntries(
          Object.keys(CAPABILITIES).map((capabilityId) => [capabilityId, 'validated-on-matching-hardware'])
        )
      }],
      recommendations,
      authentication: {mode: 'none', configured: false, persisted: false},
      trustScope: 'loopback', transportScheme: 'http', version: '0.32.5',
      idleUnloadSeconds: 300,
      providerHealth: {status: 'healthy'},
      evidenceBoundary: {
        catalogStatus: 'ready', immutableDigestBound: true,
        hardwareFitMeasured: true, unknownModelsGainAuthority: false
      }
    }, 'http://127.0.0.1:11435', 120, 300);
    return {
      selections: Object.values(state.modelSelections).map((item) => item.mode),
      selected: document.querySelector('#model').value,
      label: document.querySelector('#model').selectedOptions[0]?.textContent || '',
      candidateLabel: [...document.querySelector('#model').options]
        .find((option) => option.value === 'candidate:candidate-chat:7b')?.textContent || '',
      candidateGroup: [...document.querySelector('#model').querySelectorAll('optgroup')]
        .find((group) => group.label.includes('download requires approval'))?.label || '',
      status: document.querySelector('#model-state').textContent,
      promptEnabled: !document.querySelector('#prompt').disabled
    };
  })()`);
  if (
    managedDefaultHandoff.selections.some((mode) => mode !== "automatic")
    || managedDefaultHandoff.selected !== "automatic"
    || !managedDefaultHandoff.label.includes("qwen3.5:0.8b")
    || !managedDefaultHandoff.candidateLabel.includes("not installed")
    || !managedDefaultHandoff.candidateGroup.includes("Tested on matching hardware")
    || !managedDefaultHandoff.status.includes("qwen3.5:0.8b")
    || !managedDefaultHandoff.promptEnabled
  ) throw new Error(`managed-default-handoff:${JSON.stringify(managedDefaultHandoff)}`);
  checks += 7;
  trace("managed-default-handoff-verified");
  await cdp.evaluate(`(() => {
    state.qualifiedModelCandidates = [];
    renderModelSelect();
    renderModelDiscovery();
  })()`);
  const trustedCitationRendering = await cdp.evaluate(`(() => {
    const citation = (suffix, title, page) => ({
      citationId: 'source-' + suffix.repeat(20),
      title,
      displayDomain: 'en.wikipedia.org',
      destination: 'https://en.wikipedia.org/?curid=' + page,
      destinationDisclosureRequired: true,
      activeNavigationAllowed: false,
    });
    const bundle = (citations) => ({
      schemaVersion: 1,
      citations,
      exactSourceAccounting: true,
      modelSuppliedLinksAccepted: false,
      runtimeAdmissionGranted: true,
    });
    const valid = bundle([
      citation('a', 'Local artificial intelligence', 12345),
      citation('b', 'Private computing & safety', 67890),
    ]);
    const accepted = window.Haven42TrustedCitationRenderer.render(valid);
    const region = document.querySelector('#research-sources');
    const first = region.querySelector('.trusted-citation');
    const validState = {
      frozenApi: Object.isFrozen(window.Haven42TrustedCitationRenderer),
      accepted,
      hidden: region.classList.contains('hidden'),
      role: region.getAttribute('role'),
      labelledBy: region.getAttribute('aria-labelledby'),
      describedBy: region.getAttribute('aria-describedby'),
      itemCount: region.querySelectorAll('.trusted-citation').length,
      activeElements: region.querySelectorAll('a,button,img,script,style,iframe,object,embed').length,
      firstText: first.textContent,
      firstDestination: first.querySelector('code').textContent,
      status: document.querySelector('#research-sources-status').textContent,
    };
    const invalidBundles = [
      {...valid, unexpected: true},
      {...valid, modelSuppliedLinksAccepted: true},
      {...valid, runtimeAdmissionGranted: false},
      bundle([]),
      bundle(Array.from({length: 11}, (_, index) => citation((index % 10).toString(16), 'Source ' + index, index + 1))),
      bundle([{...citation('c', 'Active', 3), activeNavigationAllowed: true}]),
      bundle([{...citation('c', 'Wrong domain', 3), displayDomain: 'example.com'}]),
      bundle([{...citation('c', 'Wrong destination', 3), destination: 'https://example.com/'}]),
      bundle([citation('c', '<img src=x onerror=alert(1)>', 3)]),
      bundle([citation('c', 'Direction \\u202e confusion', 3)]),
      bundle([citation('c', 'Duplicate', 3), citation('c', 'Duplicate again', 4)]),
      bundle([citation('c', 'Same destination', 3), citation('d', 'Same destination again', 3)]),
    ];
    const rejected = invalidBundles.map((candidate) => window.Haven42TrustedCitationRenderer.render(candidate));
    const rejectedState = {
      rejected: rejected.every((result) => result.accepted === false && result.rendered === 0),
      hidden: region.classList.contains('hidden'),
      itemCount: region.querySelectorAll('.trusted-citation').length,
      status: document.querySelector('#research-sources-status').textContent,
    };
    window.Haven42TrustedCitationRenderer.render(valid);
    resetTask();
    const clearedByNewTask = region.classList.contains('hidden')
      && region.querySelectorAll('.trusted-citation').length === 0
      && document.querySelector('#research-sources-status').textContent === '';
    return {validState, rejectedState, clearedByNewTask};
  })()`);
  if (
    !trustedCitationRendering.validState.frozenApi
    || trustedCitationRendering.validState.accepted.accepted !== true
    || trustedCitationRendering.validState.accepted.rendered !== 2
    || trustedCitationRendering.validState.hidden
    || trustedCitationRendering.validState.role !== "region"
    || trustedCitationRendering.validState.labelledBy !== "research-sources-title"
    || trustedCitationRendering.validState.describedBy !== "research-sources-disclosure"
    || trustedCitationRendering.validState.itemCount !== 2
    || trustedCitationRendering.validState.activeElements !== 0
    || !trustedCitationRendering.validState.firstText.includes("Local artificial intelligence")
    || !trustedCitationRendering.validState.firstText.includes("Source: en.wikipedia.org")
    || trustedCitationRendering.validState.firstDestination !== "Destination: https://en.wikipedia.org/?curid=12345"
    || !trustedCitationRendering.validState.status.includes("2 trusted research sources")
    || !trustedCitationRendering.validState.status.includes("inactive")
    || !trustedCitationRendering.rejectedState.rejected
    || !trustedCitationRendering.rejectedState.hidden
    || trustedCitationRendering.rejectedState.itemCount !== 0
    || trustedCitationRendering.rejectedState.status !== ""
    || !trustedCitationRendering.clearedByNewTask
  ) throw new Error(`trusted-citation-renderer:${JSON.stringify(trustedCitationRendering)}`);
  checks += 19;
  trace("trusted-citation-renderer-verified");
  const researchReviewInitial = await cdp.evaluate(`(() => {
    if (!document.querySelector('#section-tour-layer').classList.contains('hidden')) {
      document.querySelector('#section-tour-close').click();
    }
    document.querySelector('#setup-wizard').classList.add('hidden');
    const passiveTrigger = document.createElement('button');
    passiveTrigger.type = 'button';
    passiveTrigger.textContent = 'Passive cleanup focus target';
    document.body.append(passiveTrigger);
    passiveTrigger.focus();
    window.Haven42ResearchApprovalReview.clear();
    const passiveFocusPreserved = document.activeElement === passiveTrigger;
    passiveTrigger.remove();
    const trigger = document.querySelector('#home-nav');
    trigger.focus();
    const queryReview = {
      schemaVersion: 1,
      reviewId: 'review-' + 'a'.repeat(20),
      kind: 'query',
      normalizedQuery: 'local artificial intelligence',
      providerId: 'wikipedia',
      citation: null,
      exactReviewRequired: true,
      modelApprovalAccepted: false,
      networkAuthorityGranted: false,
      runtimeAdmissionGranted: false,
      persistenceAllowed: false,
      automaticFollowUpAllowed: false,
    };
    const opened = window.Haven42ResearchApprovalReview.open(queryReview, trigger);
    const layer = document.querySelector('#research-review-layer');
    const dialog = document.querySelector('#research-review-dialog');
    document.querySelector('#research-review-approve').click();
    return {
      frozenApi: Object.isFrozen(window.Haven42ResearchApprovalReview),
      passiveFocusPreserved,
      opened,
      visible: !layer.classList.contains('hidden'),
      ariaHidden: layer.getAttribute('aria-hidden'),
      role: dialog.getAttribute('role'),
      ariaModal: dialog.getAttribute('aria-modal'),
      labelledBy: dialog.getAttribute('aria-labelledby'),
      describedBy: dialog.getAttribute('aria-describedby'),
      focused: document.activeElement === dialog,
      backgroundInert: [...document.body.children]
        .filter((element) => element.id !== 'research-review-layer' && element.tagName !== 'SCRIPT')
        .every((element) => element.inert),
      kind: document.querySelector('#research-review-kind').textContent,
      query: document.querySelector('#research-review-query').textContent,
      pageRowsHidden: document.querySelector('#research-review-source-row').classList.contains('hidden')
        && document.querySelector('#research-review-destination-row').classList.contains('hidden'),
      status: document.querySelector('#research-review-status').textContent,
      syntheticDecision: window.Haven42ResearchApprovalReview.consumeDecision(),
    };
  })()`);
  if (
    !researchReviewInitial.frozenApi
    || !researchReviewInitial.passiveFocusPreserved
    || researchReviewInitial.opened.accepted !== true
    || researchReviewInitial.opened.opened !== true
    || !researchReviewInitial.visible
    || researchReviewInitial.ariaHidden !== "false"
    || researchReviewInitial.role !== "dialog"
    || researchReviewInitial.ariaModal !== "true"
    || researchReviewInitial.labelledBy !== "research-review-title"
    || researchReviewInitial.describedBy !== "research-review-description research-review-privacy"
    || !researchReviewInitial.focused
    || !researchReviewInitial.backgroundInert
    || researchReviewInitial.kind !== "Search Wikipedia"
    || researchReviewInitial.query !== "local artificial intelligence"
    || !researchReviewInitial.pageRowsHidden
    || !researchReviewInitial.status.includes("direct user action")
    || researchReviewInitial.syntheticDecision !== null
  ) throw new Error(`research-review-initial:${JSON.stringify(researchReviewInitial)}`);
  checks += 17;
  await cdp.call("Input.dispatchKeyEvent", {
    type: "keyDown", key: "Tab", code: "Tab", modifiers: 8,
  });
  await cdp.call("Input.dispatchKeyEvent", {
    type: "keyUp", key: "Tab", code: "Tab", modifiers: 8,
  });
  const researchReviewReverseTrap = await cdp.evaluate(
    `document.activeElement === document.querySelector('#research-review-approve')`,
  );
  await cdp.call("Input.dispatchKeyEvent", {type: "keyDown", key: "Tab", code: "Tab"});
  await cdp.call("Input.dispatchKeyEvent", {type: "keyUp", key: "Tab", code: "Tab"});
  const researchReviewForwardTrap = await cdp.evaluate(
    `document.activeElement === document.querySelector('#research-review-close')`,
  );
  if (!researchReviewReverseTrap || !researchReviewForwardTrap) {
    throw new Error(`research-review-focus-trap:${JSON.stringify({researchReviewReverseTrap, researchReviewForwardTrap})}`);
  }
  checks += 2;
  await cdp.call("Input.dispatchKeyEvent", {type: "keyDown", key: "Escape", code: "Escape"});
  await cdp.call("Input.dispatchKeyEvent", {type: "keyUp", key: "Escape", code: "Escape"});
  const researchReviewEscape = await cdp.evaluate(`(() => {
    const decision = window.Haven42ResearchApprovalReview.consumeDecision();
    const second = window.Haven42ResearchApprovalReview.consumeDecision();
    return {
      hidden: document.querySelector('#research-review-layer').classList.contains('hidden'),
      ariaHidden: document.querySelector('#research-review-layer').getAttribute('aria-hidden'),
      backgroundRestored: [...document.body.children]
        .filter((element) => element.id !== 'research-review-layer' && element.tagName !== 'SCRIPT')
        .every((element) => !element.inert),
      focusReturned: document.activeElement === document.querySelector('#home-nav'),
      decision,
      second,
    };
  })()`);
  if (
    !researchReviewEscape.hidden
    || researchReviewEscape.ariaHidden !== "true"
    || !researchReviewEscape.backgroundRestored
    || !researchReviewEscape.focusReturned
    || researchReviewEscape.decision?.decision !== "cancelled"
    || researchReviewEscape.decision?.networkStarted !== false
    || researchReviewEscape.decision?.singleUse !== true
    || researchReviewEscape.second !== null
  ) throw new Error(`research-review-escape:${JSON.stringify(researchReviewEscape)}`);
  checks += 8;
  const researchPageReview = await cdp.evaluate(`(() => {
    const trigger = document.querySelector('#home-nav');
    const citation = {
      citationId: 'source-' + 'b'.repeat(20),
      title: 'Local artificial intelligence',
      displayDomain: 'en.wikipedia.org',
      destination: 'https://en.wikipedia.org/?curid=42',
      destinationDisclosureRequired: true,
      activeNavigationAllowed: false,
    };
    const pageReview = {
      schemaVersion: 1,
      reviewId: 'review-' + 'c'.repeat(20),
      kind: 'page',
      normalizedQuery: 'local artificial intelligence',
      providerId: 'wikipedia',
      citation,
      exactReviewRequired: true,
      modelApprovalAccepted: false,
      networkAuthorityGranted: false,
      runtimeAdmissionGranted: false,
      persistenceAllowed: false,
      automaticFollowUpAllowed: false,
    };
    const rejected = window.Haven42ResearchApprovalReview.open({...pageReview, unexpected: true}, trigger);
    const opened = window.Haven42ResearchApprovalReview.open(pageReview, trigger);
    pageReview.reviewId = 'review-' + 'f'.repeat(20);
    pageReview.kind = 'query';
    pageReview.citation.title = 'Mutated after review opened';
    const button = document.querySelector('#research-review-approve');
    button.focus();
    const rect = button.getBoundingClientRect();
    return {
      rejected,
      opened,
      source: document.querySelector('#research-review-source').textContent,
      destination: document.querySelector('#research-review-destination').textContent,
      pageRowsVisible: !document.querySelector('#research-review-source-row').classList.contains('hidden')
        && !document.querySelector('#research-review-destination-row').classList.contains('hidden'),
      approveFocused: document.activeElement === button,
      x: rect.left + rect.width / 2,
      y: rect.top + rect.height / 2,
    };
  })()`);
  if (
    researchPageReview.rejected.accepted !== false
    || researchPageReview.rejected.opened !== false
    || researchPageReview.opened.accepted !== true
    || researchPageReview.source !== "Local artificial intelligence"
    || researchPageReview.destination !== "https://en.wikipedia.org/?curid=42"
    || !researchPageReview.pageRowsVisible
    || !researchPageReview.approveFocused
  ) throw new Error(`research-page-review:${JSON.stringify(researchPageReview)}`);
  checks += 7;
  await cdp.call("Input.dispatchMouseEvent", {
    type: "mouseMoved", x: researchPageReview.x, y: researchPageReview.y,
    button: "none", buttons: 0, pointerType: "mouse",
  });
  await cdp.call("Input.dispatchMouseEvent", {
    type: "mousePressed", x: researchPageReview.x, y: researchPageReview.y,
    button: "left", buttons: 1, clickCount: 1, pointerType: "mouse",
  });
  await cdp.call("Input.dispatchMouseEvent", {
    type: "mouseReleased", x: researchPageReview.x, y: researchPageReview.y,
    button: "left", buttons: 0, clickCount: 1, pointerType: "mouse",
  });
  const researchReviewApproval = await cdp.evaluate(`(() => {
    const before = {
      hidden: document.querySelector('#research-review-layer').classList.contains('hidden'),
      status: document.querySelector('#research-review-status').textContent,
      activeId: document.activeElement?.id || document.activeElement?.tagName,
    };
    const decision = window.Haven42ResearchApprovalReview.consumeDecision();
    const singleUse = window.Haven42ResearchApprovalReview.consumeDecision();
    const queryReview = {
      schemaVersion: 1, reviewId: 'review-' + 'd'.repeat(20), kind: 'query',
      normalizedQuery: 'privacy preserving local AI', providerId: 'wikipedia', citation: null,
      exactReviewRequired: true, modelApprovalAccepted: false,
      networkAuthorityGranted: false, runtimeAdmissionGranted: false,
      persistenceAllowed: false, automaticFollowUpAllowed: false,
    };
    window.Haven42ResearchApprovalReview.open(queryReview, document.querySelector('#home-nav'));
    resetTask();
    return {
      before,
      decision,
      singleUse,
      hiddenAfterNewTask: document.querySelector('#research-review-layer').classList.contains('hidden'),
      decisionClearedByNewTask: window.Haven42ResearchApprovalReview.consumeDecision() === null,
      noWikipediaResources: performance.getEntriesByType('resource').every((entry) => !entry.name.includes('wikipedia.org')),
    };
  })()`);
  if (
    researchReviewApproval.decision?.decision !== "approved"
    || researchReviewApproval.decision?.reviewId !== `review-${"c".repeat(20)}`
    || researchReviewApproval.decision?.kind !== "page"
    || researchReviewApproval.decision?.networkStarted !== false
    || researchReviewApproval.decision?.singleUse !== true
    || researchReviewApproval.singleUse !== null
    || !researchReviewApproval.hiddenAfterNewTask
    || !researchReviewApproval.decisionClearedByNewTask
    || !researchReviewApproval.noWikipediaResources
  ) throw new Error(`research-review-approval:${JSON.stringify(researchReviewApproval)}`);
  checks += 9;
  trace("research-approval-review-verified");
  if (!packagedExecutable) {
    await cdp.evaluate(`(() => {
      document.querySelector('#home-nav').click();
      document.querySelector('#research-tools').open = true;
      document.querySelector('#research-query').value = 'local artificial intelligence';
      document.querySelector('#research-query-form').requestSubmit();
    })()`);
    await waitFor(() => cdp.evaluate("!document.querySelector('#research-review-layer').classList.contains('hidden')"));
    const preparedResearch = await cdp.evaluate(`({
      kind: document.querySelector('#research-review-kind').textContent,
      query: document.querySelector('#research-review-query').textContent,
      focused: document.activeElement.id,
      backgroundInert: document.querySelector('.shell').inert,
      status: document.querySelector('#research-review-status').textContent,
      resultsHidden: document.querySelector('#research-results').classList.contains('hidden'),
    })`);
    if (
      preparedResearch.kind !== "Search Wikipedia"
      || preparedResearch.query !== "local artificial intelligence"
      || preparedResearch.focused !== "research-review-dialog"
      || !preparedResearch.backgroundInert
      || !preparedResearch.status.includes("Nothing has been sent")
      || !preparedResearch.resultsHidden
    ) throw new Error(`product-research-preparation:${JSON.stringify(preparedResearch)}`);
    await cdp.evaluate("document.querySelector('#research-review-cancel').click()");
    await waitFor(() => cdp.evaluate("document.querySelector('#research-review-layer').classList.contains('hidden')"));
    const cancelledResearch = await cdp.evaluate(`({
      status: document.querySelector('#research-query-status').textContent,
      resultsHidden: document.querySelector('#research-results').classList.contains('hidden'),
    })`);
    if (!cancelledResearch.status.includes("cancelled") || !cancelledResearch.resultsHidden) {
      throw new Error(`product-research-cancel:${JSON.stringify(cancelledResearch)}`);
    }
    await cdp.evaluate("document.querySelector('#research-query-form').requestSubmit()");
    await waitFor(() => cdp.evaluate("!document.querySelector('#research-review-layer').classList.contains('hidden')"));
    await trustedClick(cdp, "#research-review-approve");
    await waitFor(() => cdp.evaluate("!document.querySelector('#research-results').classList.contains('hidden')"));
    const queryResearch = await cdp.evaluate(`({
      resultCount: document.querySelectorAll('#research-result-list .research-result').length,
      activeLinks: document.querySelectorAll('#research-results a').length,
      reviewButtons: document.querySelectorAll('#research-result-list button').length,
      title: document.querySelector('#research-result-list strong').textContent,
      destination: document.querySelector('#research-result-list code').textContent,
      status: document.querySelector('#research-query-status').textContent,
      sourceCount: document.querySelectorAll('#research-source-list .trusted-citation').length,
      pageHidden: document.querySelector('#research-page').classList.contains('hidden'),
    })`);
    if (
      queryResearch.resultCount !== 1
      || queryResearch.activeLinks !== 0
      || queryResearch.reviewButtons !== 1
      || queryResearch.title !== "Local artificial intelligence"
      || queryResearch.destination !== "Destination: https://en.wikipedia.org/?curid=42"
      || !queryResearch.status.includes("Page contents have not been requested")
      || queryResearch.sourceCount !== 1
      || !queryResearch.pageHidden
    ) throw new Error(`product-research-query:${JSON.stringify(queryResearch)}`);
    await cdp.evaluate("document.querySelector('#research-result-list button').click()");
    await waitFor(() => cdp.evaluate("!document.querySelector('#research-review-layer').classList.contains('hidden')"));
    const preparedPage = await cdp.evaluate(`({
      kind: document.querySelector('#research-review-kind').textContent,
      source: document.querySelector('#research-review-source').textContent,
      destination: document.querySelector('#research-review-destination').textContent,
      rowsVisible: !document.querySelector('#research-review-source-row').classList.contains('hidden')
        && !document.querySelector('#research-review-destination-row').classList.contains('hidden'),
    })`);
    if (
      preparedPage.kind !== "Read one selected Wikipedia page"
      || preparedPage.source !== "Local artificial intelligence"
      || preparedPage.destination !== "https://en.wikipedia.org/?curid=42"
      || !preparedPage.rowsVisible
    ) throw new Error(`product-research-page-preparation:${JSON.stringify(preparedPage)}`);
    const pageApprovalTarget = await cdp.evaluate(`(() => {
      const element = document.querySelector('#research-review-approve');
      const rect = element.getBoundingClientRect();
      const x = rect.left + rect.width / 2;
      const y = rect.top + rect.height / 2;
      return {
        disabled: element.disabled,
        inert: element.inert,
        rect: {left: rect.left, top: rect.top, width: rect.width, height: rect.height},
        topElement: document.elementFromPoint(x, y)?.id || null,
        viewport: {width: innerWidth, height: innerHeight},
      };
    })()`);
    if (
      pageApprovalTarget.disabled
      || pageApprovalTarget.inert
      || pageApprovalTarget.topElement !== "research-review-approve"
    ) throw new Error(`product-research-page-approval-target:${JSON.stringify(pageApprovalTarget)}`);
    await trustedClick(cdp, "#research-review-approve");
    await waitFor(() => cdp.evaluate("document.querySelector('#research-review-layer').classList.contains('hidden')"));
    await waitFor(() => cdp.evaluate(`(
      !document.querySelector('#research-page').classList.contains('hidden')
      || document.querySelector('#research-query-status').dataset.state === 'error'
    )`));
    const pageResearch = await cdp.evaluate(`({
      hidden: document.querySelector('#research-page').classList.contains('hidden'),
      title: document.querySelector('#research-page-title').textContent,
      focused: document.activeElement.id,
      paragraphs: [...document.querySelectorAll('#research-page-content p')].map((item) => item.textContent),
      activeElements: document.querySelectorAll('#research-page-content :is(a, img, script, style, iframe, object, embed)').length,
      destination: document.querySelector('#research-page-destination').textContent,
      status: document.querySelector('#research-query-status').textContent,
    })`);
    if (
      pageResearch.hidden
      || pageResearch.title !== "Local artificial intelligence"
      || pageResearch.focused !== "research-page-title"
      || pageResearch.paragraphs.length !== 2
      || !pageResearch.paragraphs[0].includes("user's device")
      || pageResearch.activeElements !== 0
      || !pageResearch.destination.includes("https://en.wikipedia.org/?curid=42")
      || !pageResearch.status.includes("remain in memory")
    ) throw new Error(`product-research-page:${JSON.stringify(pageResearch)}`);
    await cdp.evaluate("document.querySelector('#new-task-button').click()");
    await waitFor(() => cdp.evaluate(`(
      document.querySelector('#research-results').classList.contains('hidden')
      && document.querySelector('#research-page').classList.contains('hidden')
      && document.querySelector('#research-query').value === ''
    )`));
    await cdp.evaluate(`(() => {
      document.querySelector('#research-tools').open = true;
      const source = document.querySelector('#research-source');
      source.value = 'general-web';
      source.dispatchEvent(new Event('change', {bubbles: true}));
      state.modelOptions.push({name: 'qwen3.5:9b'});
      state.modelSelections['general.chat'] = {mode: 'manual', model: 'qwen3.5:9b'};
      document.querySelector('#research-api-key').value = '${"g".repeat(32)}';
      document.querySelector('#research-query').value = 'recent local AI models';
      document.querySelector('#research-query-form').requestSubmit();
    })()`);
    await waitFor(() => cdp.evaluate(`(
      !document.querySelector('#research-review-layer').classList.contains('hidden')
      || document.querySelector('#research-query-status').dataset.state === 'error'
    )`));
    const citedWebPreparation = await cdp.evaluate(`({
      reviewHidden: document.querySelector('#research-review-layer').classList.contains('hidden'),
      status: document.querySelector('#research-query-status').textContent,
      model: document.querySelector('#model').value,
      selectedModel: selectedModel('general.chat'),
      modelOptions: state.modelOptions.map((item) => item.name),
    })`);
    if (citedWebPreparation.reviewHidden) {
      throw new Error(`cited-web-preparation:${JSON.stringify(citedWebPreparation)}`);
    }
    const citedWebReview = await cdp.evaluate(`({
      keyVisible: !document.querySelector('#research-api-key-row').classList.contains('hidden'),
      keyRequired: document.querySelector('#research-api-key').required,
      kind: document.querySelector('#research-review-kind').textContent,
      query: document.querySelector('#research-review-query').textContent,
      source: document.querySelector('#research-review-source').textContent,
      destination: document.querySelector('#research-review-destination').textContent,
      description: document.querySelector('#research-review-description').textContent,
    })`);
    if (
      !citedWebReview.keyVisible
      || !citedWebReview.keyRequired
      || citedWebReview.kind !== 'Search selected public pages and create a cited local answer'
      || citedWebReview.query !== 'recent local AI models'
      || citedWebReview.source !== 'Brave Search API and selected public pages'
      || citedWebReview.destination !== 'https://api.search.brave.com/res/v1/web/search'
      || !citedWebReview.description.includes('selected local model')
    ) throw new Error(`cited-web-review:${JSON.stringify(citedWebReview)}`);
    await cdp.evaluate("document.querySelector('#research-review-cancel').click()");
    await waitFor(() => cdp.evaluate("document.querySelector('#research-review-layer').classList.contains('hidden')"));
    const citedWebCancelled = await cdp.evaluate(`({
      status: document.querySelector('#research-query-status').textContent,
      keyCleared: document.querySelector('#research-api-key').value === '',
      answerHidden: document.querySelector('#research-answer').classList.contains('hidden'),
      sourcesHidden: document.querySelector('#research-sources').classList.contains('hidden'),
    })`);
    if (
      !citedWebCancelled.status.includes('cancelled')
      || !citedWebCancelled.keyCleared
      || !citedWebCancelled.answerHidden
      || !citedWebCancelled.sourcesHidden
    ) throw new Error(`cited-web-cancel:${JSON.stringify(citedWebCancelled)}`);
    checks += 11;
    await cdp.evaluate(`(() => {
      document.querySelector('#research-tools').open = true;
      const source = document.querySelector('#research-source');
      source.value = 'web';
      source.dispatchEvent(new Event('change', {bubbles: true}));
      document.querySelector('#research-query').value = 'local GPU models';
      document.querySelector('#research-query-form').requestSubmit();
    })()`);
    await waitFor(() => cdp.evaluate("!document.querySelector('#research-review-layer').classList.contains('hidden')"));
    const webReview = await cdp.evaluate(`({
      kind: document.querySelector('#research-review-kind').textContent,
      query: document.querySelector('#research-review-query').textContent,
      source: document.querySelector('#research-review-source').textContent,
      destination: document.querySelector('#research-review-destination').textContent,
    })`);
    if (
      webReview.kind !== 'Open a wider-web search in your browser'
      || webReview.query !== 'local GPU models'
      || webReview.source !== 'Brave Search'
      || webReview.destination !== 'https://search.brave.com/search?q=local+GPU+models'
    ) throw new Error(`wider-web-review:${JSON.stringify(webReview)}`);
    await trustedClick(cdp, '#research-review-approve');
    await waitFor(() => cdp.evaluate("!document.querySelector('#research-web-link').classList.contains('hidden')"));
    const widerWeb = await cdp.evaluate(`(() => {
      const link = document.querySelector('#research-web-link');
      const before = {
        href: link.href,
        target: link.target,
        rel: link.rel,
        referrerPolicy: link.referrerPolicy,
        status: document.querySelector('#research-query-status').textContent,
      };
      link.addEventListener('click', (event) => event.preventDefault(), {once: true});
      link.click();
      return {...before, researchOpen: document.querySelector('#research-tools').open};
    })()`);
    if (
      widerWeb.href !== 'https://search.brave.com/search?q=local+GPU+models'
      || widerWeb.target !== '_blank'
      || !widerWeb.rel.includes('noopener')
      || widerWeb.referrerPolicy !== 'no-referrer'
      || !widerWeb.status.includes('Haven 42 will not read')
      || widerWeb.researchOpen
    ) throw new Error(`wider-web-handoff:${JSON.stringify(widerWeb)}`);
    checks += 43;
    trace("product-research-runtime-verified");
  }
  await waitFor(() => cdp.evaluate(`(
    connectProvider('http://127.0.0.1:${fakePort}', 30, 300, 'bearer', '${browserAuthSecret}')
      .then(() => true)
      .catch(() => false)
  )`));
  await cdp.evaluate("document.querySelector('#models-nav').click()");
  await waitFor(() => cdp.evaluate("!document.querySelector('#models-panel').classList.contains('hidden')"));
  await cdp.evaluate("location.reload()");
  await waitFor(() => cdp.evaluate("document.readyState === 'complete' && Boolean(document.querySelector('#models-panel'))"));
  await delay(1000);
  const restoredSection = await cdp.evaluate(`({
    stored: localStorage.getItem('haven42.last-section.v1'),
    modelsActive: document.querySelector('#models-nav').classList.contains('active'),
    modelsHidden: document.querySelector('#models-panel').classList.contains('hidden'),
    setupHidden: document.querySelector('#setup-wizard').classList.contains('hidden'),
    conversationPersisted: localStorage.getItem('haven42.conversation'),
    visibleError: document.querySelector('#connection-error').textContent,
    wizardDescription: document.querySelector('#wizard-description').textContent,
  })`);
  if (
    restoredSection.stored !== 'models-panel'
    || !restoredSection.modelsActive
    || restoredSection.modelsHidden
    || !restoredSection.setupHidden
    || restoredSection.conversationPersisted !== null
  ) throw new Error(`last-section-restore:${JSON.stringify(restoredSection)}`);
  checks += 4;
  const aboutAccessibilityLink = await cdp.evaluate(`(() => {
    const link = document.querySelector('#about-panel a[href="/accessibility"]');
    return link ? {text: link.textContent.trim(), href: link.getAttribute('href')} : null;
  })()`);
  if (!aboutAccessibilityLink || aboutAccessibilityLink.text !== "Open the accessibility statement" || aboutAccessibilityLink.href !== "/accessibility") {
    throw new Error(`about-accessibility-link:${JSON.stringify(aboutAccessibilityLink)}`);
  }
  await cdp.evaluate("location.href = '/accessibility'");
  await waitFor(() => cdp.evaluate("document.readyState === 'complete' && Boolean(document.querySelector('.statement-content'))"));
  const accessibilityStatement = await cdp.evaluate(`(() => {
    const action = document.querySelector('.statement-action');
    action.focus();
    const style = getComputedStyle(action);
    return {
      title: document.title,
      h1: document.querySelectorAll('h1').length,
      main: document.querySelectorAll('main').length,
      navigation: document.querySelectorAll('nav').length,
      lastReviewed: document.querySelector('.statement-updated').textContent,
      implemented: document.querySelector('#completed-work').parentElement.textContent,
      limitation: document.querySelector('#known-limitations').parentElement.textContent,
      targetHeight: action.getBoundingClientRect().height,
      outlineWidth: style.outlineWidth,
      externalTarget: action.target,
      externalRel: action.rel,
      scripts: document.querySelectorAll('script').length,
    };
  })()`);
  if (
    accessibilityStatement.title !== "Accessibility Statement · Haven 42"
    || accessibilityStatement.h1 !== 1
    || accessibilityStatement.main !== 1
    || accessibilityStatement.navigation !== 1
    || !accessibilityStatement.lastReviewed.includes("August 22, 2026")
    || !accessibilityStatement.implemented.includes("Manually scrolling up pauses that behavior")
    || !accessibilityStatement.limitation.includes("not yet been manually tested")
    || accessibilityStatement.targetHeight < 44
    || Number.parseFloat(accessibilityStatement.outlineWidth) < 3
    || accessibilityStatement.externalTarget !== "_blank"
    || !accessibilityStatement.externalRel.includes("noopener")
    || !accessibilityStatement.externalRel.includes("noreferrer")
    || accessibilityStatement.scripts !== 0
  ) throw new Error(`accessibility-statement:${JSON.stringify(accessibilityStatement)}`);
  checks += 15;
  trace("accessibility-statement-verified");
  console.log("Haven 42 browser evidence gates passed: bounded-attachments, automated-accessibility, local-privacy-boundary.");
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
