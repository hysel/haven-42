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
    || assurance.candidateRows !== 1
    || !assurance.activityDetails
    || assurance.wikiHref !== "https://github.com/hysel/haven-42/wiki/Evidence-Dashboard"
    || assurance.wikiTarget !== "_blank"
    || !assurance.wikiRel.includes("noopener")
    || !assurance.wikiRel.includes("noreferrer")
    || assurance.wikiReferrer !== "no-referrer"
    || !assurance.disclosure.includes("does not start AI")
  ) throw new Error(`assurance-view:${JSON.stringify(assurance)}`);
  checks += 17;
  trace("assurance-view-verified");

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
    nextDisabled: document.querySelector('#wizard-readiness-next').disabled,
    nextText: document.querySelector('#wizard-readiness-next').textContent,
    status: document.querySelector('#wizard-scan-status').textContent
  })`);
  const detectedAmd = /Accelerator\s*AMD\b/i.test(guided.factsText);
  const detectedNvidia = /Accelerator\s*NVIDIA\b/i.test(guided.factsText);
  const detectedIntel = /Accelerator\s*Intel\b/i.test(guided.factsText);
  const showsAmdTools = guided.factsText.includes("AMD ROCm tools");
  const showsNvidiaTools = guided.factsText.includes("NVIDIA tools");
  const showsIntelTools = guided.factsText.includes("Intel oneAPI tools");
  if (
    guided.current !== "middle"
    || guided.facts < 4
    || !/(Windows 10|Windows 11|Linux|macOS)/i.test(guided.factsText)
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
      || !guided.planText.includes("Components for this device")
      || !guided.planText.includes("Ollama local runtime")
      || !guided.planText.includes("Download:")
      || !guided.planText.includes("Required to run the selected text model locally")
      || !guided.planText.includes("Download and safety details")
      || (detectedAmd && !guided.planText.includes("AMD GPU acceleration · ROCm 7.1"))
      || (detectedAmd && !guided.planText.includes("Ollama 0.32.5 AMD support package"))
    )
  ) throw new Error(`guided-installation-progress:${JSON.stringify(guided)}`);
  if (!guided.installationPanel && (!guided.nextDisabled || guided.nextText !== "Local setup unavailable")) {
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
    ) throw new Error(`setup-reuse-presentation:${JSON.stringify(reusePresentation)}`);
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
  await cdp.evaluate("document.querySelector('#wizard-readiness-back').click()");
  await waitFor(() => cdp.evaluate("document.querySelector('[aria-current=\"step\"]').dataset.wizardProgress === 'welcome'"));
  trace("guided-readiness-verified");

  await cdp.evaluate("document.querySelector('#wizard-existing').click()");
  const provider = await cdp.evaluate(`({
    visible: !document.querySelector('[data-wizard-step="provider"]').classList.contains('hidden'),
    focused: document.activeElement.id,
    backVisible: !document.querySelector('#wizard-provider-back').classList.contains('hidden')
  })`);
  if (!provider.visible || provider.focused !== "wizard-endpoint" || !provider.backVisible) throw new Error("provider-step-focus");
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
  checks += 2;
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
    wizardControlSizing.endpoint !== 36
    || wizardControlSizing.timeout !== 36
    || wizardControlSizing.cleanup !== 36
    || wizardControlSizing.authentication !== 36
    || wizardControlSizing.endpointFont !== "13px"
    || wizardControlSizing.timeoutFont !== "13px"
    || wizardControlSizing.cleanupFont !== "13px"
    || wizardControlSizing.authenticationFont !== "13px"
    || wizardControlSizing.authenticationValue !== "none"
    || wizardControlSizing.authenticationText !== "Automatic (Recommended)"
    || !wizardControlSizing.keyDisabled
  ) throw new Error(`compact-wizard-controls:${JSON.stringify(wizardControlSizing)}`);
  checks += 11;

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
    authentication: document.querySelector('#auth-mode').getBoundingClientRect().height,
    endpointFont: getComputedStyle(document.querySelector('#endpoint')).fontSize,
    cleanupFont: getComputedStyle(document.querySelector('#system-idle-unload')).fontSize,
    timeoutFont: getComputedStyle(document.querySelector('#timeout')).fontSize,
    advancedCleanupFont: getComputedStyle(document.querySelector('#idle-unload')).fontSize,
    authenticationFont: getComputedStyle(document.querySelector('#auth-mode')).fontSize,
    authenticationText: document.querySelector('#auth-mode').selectedOptions[0].textContent,
    keyDisabled: document.querySelector('#api-key').disabled
  })`);
  if (
    Math.abs(compactControls.endpoint - compactControls.model) > 1
    || Math.abs(compactControls.cleanup - compactControls.model) > 1
    || Math.abs(compactControls.authentication - compactControls.model) > 1
    || compactControls.endpoint >= 44
    || compactControls.endpointFont !== "13px"
    || compactControls.cleanupFont !== "13px"
    || compactControls.timeoutFont !== "13px"
    || compactControls.advancedCleanupFont !== "13px"
    || compactControls.authenticationFont !== "13px"
    || compactControls.authenticationText !== "Automatic (Recommended)"
    || !compactControls.keyDisabled
  ) throw new Error(`compact-provider-controls:${JSON.stringify(compactControls)}`);
  checks += 11;

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
    key.value = '${browserAuthSecret}';
    key.dispatchEvent(new Event('input', {bubbles: true}));
    const before = {
      keyEnabled: !key.disabled,
      keyRequired: key.required,
      buttonText: document.querySelector('#connect-button').textContent,
      buttonEnabled: !document.querySelector('#connect-button').disabled,
    };
    document.querySelector('#connection-form').requestSubmit();
    return before;
  })()`);
  if (
    !authenticationDirty.keyEnabled
    || !authenticationDirty.keyRequired
    || authenticationDirty.buttonText !== "Apply changes"
    || !authenticationDirty.buttonEnabled
  ) throw new Error(`authentication-dirty-state:${JSON.stringify(authenticationDirty)}`);
  await waitFor(() => cdp.evaluate(`(
    document.querySelector('#connect-button').disabled
    && document.querySelector('#connect-button').textContent === 'Connected'
    && document.querySelector('#api-key').value === ''
    && document.querySelector('#wizard-api-key').value === ''
    && document.querySelector('#wizard-auth-mode').value === 'bearer'
    && document.querySelector('#connection-badge').textContent.includes('authenticated')
  )`));
  const authenticatedRequests = providerAuthorization.slice(authorizationStart);
  if (
    authenticatedRequests.length < 2
    || authenticatedRequests.some(([, , authorization]) => authorization !== `Bearer ${browserAuthSecret}`)
  ) throw new Error(`provider-authentication-headers:${JSON.stringify(authenticatedRequests)}`);
  checks += 11;

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
    || !modelsView.installedLabel.includes("Already available on your server")
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
    || !discovery.state.includes("cannot be used until you install it")
    || discovery.command !== "ollama pull candidate-writing:7b"
    || discovery.hidden
    || !discovery.searchStatus.includes("Nothing was downloaded")
    || discovery.currentModel !== "manual:unknown-model:latest"
  ) throw new Error("candidate-only-model-discovery");
  checks += 6;

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
  if (
    capabilityReset.query !== ""
    || capabilityReset.resultCount !== 2
    || !capabilityReset.desiredHidden
    || capabilityReset.resultName !== "unknown-model:latest"
    || !capabilityReset.status.includes("Conversation")
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
  const result = await cdp.evaluate(`({
    output: [...document.querySelectorAll('.message p')].some((item) => item.textContent === 'LOCAL_BROWSER_OK'),
    typed: document.querySelector('#task-event').textContent,
    kind: document.querySelector('#task-event').dataset.kind,
    status: document.querySelector('#text-status').textContent,
    error: document.querySelector('#connection-error').textContent,
    speed: document.querySelector('#alpha-speed').textContent,
    runDetailsVisible: !document.querySelector('#run-details').classList.contains('hidden'),
    runDetails: document.querySelector('#run-details-list').textContent
  })`);
  if (
    !result.output
    || !result.typed.includes("no file saved")
    || !result.typed.includes("has not tested this model")
    || result.kind !== "warning"
    || result.speed !== "2 tokens/s"
    || !result.runDetailsVisible
    || !result.runDetails.includes("40")
    || !result.runDetails.includes("2 tokens/s")
  ) {
    throw new Error(`typed-result-rendering:${JSON.stringify(result)}`);
  }
  checks += 8;
  trace("typed-result-verified");

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
  checks += 14;
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
      height: "36px",
      fontSize: "13px",
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
    !attachmentLayout.surfaceInsidePanel
    || !attachmentLayout.composerInsidePanel
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
      diagnosticStatus: document.querySelector('#diagnostics-status').textContent,
      diagnosticRows: document.querySelectorAll('#diagnostic-events li').length,
      diagnosticActions: document.querySelectorAll('#diagnostics-control button').length,
      diagnosticPrivacy: document.querySelector('#diagnostics-control').textContent,
      maintenanceHeading: document.querySelector('#local-ai-maintenance-title').textContent,
      localSetupLabel: document.querySelector('#setup-local-components').textContent,
      uninstallLabel: document.querySelector('#remove-managed-components').textContent,
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
  if (
    navigation.reducedMotion !== "auto"
    || !navigation.models.active
    || navigation.models.focused !== "models-title"
    || !navigation.models.visible
    || !navigation.models.imageHidden
    || navigation.models.installed !== 2
    || !navigation.system.active
    || navigation.system.focused !== "system-title"
    || navigation.system.diagnosticStatus.includes("Loading")
    || navigation.system.diagnosticRows < 1
    || navigation.system.diagnosticActions !== 4
    || !navigation.system.diagnosticPrivacy.includes("never recorded or uploaded")
    || navigation.system.maintenanceHeading !== "Local AI on this computer"
    || !navigation.system.localSetupLabel.includes("local AI")
    || !navigation.system.uninstallLabel.includes("local AI components")
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
  checks += 26;
  trace("accessible-navigation-verified");

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
