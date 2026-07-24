"use strict";

const CAPABILITIES = {
  "general.chat": {
    eyebrow: "03 · CHAT",
    title: "Private conversation",
    promptLabel: "Message",
    placeholder: "Ask anything…",
    busy: "Model is thinking locally…",
    welcome: "Ask a question and continue the conversation. Context stays in memory until you start a new task or close Haven 42.",
    resultLabel: "Haven 42",
    modelLabel: "Chat model",
    artifactType: "chat-message",
  },
  "content.write": {
    eyebrow: "03 · WRITING",
    title: "Draft content",
    promptLabel: "Writing request",
    placeholder: "Describe what you want written…",
    busy: "Drafting locally…",
    welcome: "Describe the audience, purpose, tone, and key points. Haven 42 returns a Markdown draft without writing files.",
    resultLabel: "Draft",
    modelLabel: "Writing model",
    artifactType: "markdown-document",
  },
  "content.summarize": {
    eyebrow: "03 · SUMMARY",
    title: "Summarize text",
    promptLabel: "Material to summarize",
    placeholder: "Paste the material you want summarized…",
    busy: "Summarizing locally…",
    welcome: "Paste source material below. The model is instructed to summarize only what you provide and preserve uncertainty.",
    resultLabel: "Summary",
    modelLabel: "Summarization model",
    artifactType: "markdown-document",
  },
};

const state = {
  token: "",
  connected: false,
  capabilityId: "general.chat",
  messages: [],
  modelSelections: {},
  recommendations: {},
  modelOptions: [],
  capabilities: [],
  readinessSnapshot: null,
  setupPlan: null,
  workflows: [],
  imageConnected: false,
  lastFocusBeforeWizard: null,
};

const byId = (id) => document.getElementById(id);

function showError(message) {
  const box = byId("connection-error");
  box.textContent = message;
  box.classList.remove("hidden");
}

function clearError() {
  byId("connection-error").classList.add("hidden");
}

function setTaskEvent(message, kind = "progress") {
  const event = byId("task-event");
  event.textContent = message;
  if (message) event.dataset.kind = kind;
  else delete event.dataset.kind;
  event.classList.toggle("error", kind === "error");
  event.classList.toggle("hidden", !message);
}

function renderCapabilities() {
  const container = byId("capability-list");
  container.replaceChildren();
  const labels = {
    available: "Available",
    "configuration-required": "Connect provider",
    "not-admitted-in-web": "Not admitted",
    "provider-profile-required": "Provider required",
  };
  for (const capability of state.capabilities) {
    const row = document.createElement("div");
    row.className = "capability-item";
    const detail = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = capability.label;
    const execution = document.createElement("small");
    execution.textContent = capability.execution === "local"
      ? "Local execution"
      : "Unavailable in this web runtime";
    detail.append(title, execution);
    const status = document.createElement("small");
    status.className = `capability-state ${
      capability.state === "available" ? "" : capability.state.includes("required") ? "required" : "unavailable"
    }`;
    status.textContent = labels[capability.state] || "Unavailable";
    row.append(detail, status);
    container.append(row);
  }
}

function validateWorkflowCatalog(result) {
  if (
    !result
    || typeof result !== "object"
    || Array.isArray(result)
    || Object.keys(result).sort().join(",") !== [
      "arbitraryCommandsAllowed", "executionMode", "kind",
      "rendererArgumentsAllowed", "schemaVersion", "workflows",
    ].sort().join(",")
    || result.schemaVersion !== 1
    || result.kind !== "workflow-catalog"
    || result.executionMode !== "plan-only"
    || result.arbitraryCommandsAllowed !== false
    || result.rendererArgumentsAllowed !== false
    || !Array.isArray(result.workflows)
  ) throw new Error("invalid-workflow-catalog");
  const ids = new Set();
  result.workflows.forEach((workflow) => {
    if (
      !workflow
      || typeof workflow !== "object"
      || Array.isArray(workflow)
      || Object.keys(workflow).sort().join(",") !== [
        "category", "executionMode", "id", "name", "purpose",
        "rendererArgumentsAllowed", "safetyLevel",
      ].sort().join(",")
      || !/^[a-z][a-z0-9-]{0,127}$/.test(workflow.id)
      || ids.has(workflow.id)
      || typeof workflow.name !== "string"
      || typeof workflow.purpose !== "string"
      || workflow.safetyLevel !== "read-only"
      || workflow.executionMode !== "plan-only"
      || workflow.rendererArgumentsAllowed !== false
    ) throw new Error("invalid-workflow-catalog");
    ids.add(workflow.id);
  });
  return result.workflows;
}

async function loadWorkflows() {
  const result = await api("/api/workflows", {});
  state.workflows = validateWorkflowCatalog(result);
  const select = byId("workflow-select");
  select.replaceChildren();
  state.workflows.forEach((workflow) => {
    const option = document.createElement("option");
    option.value = workflow.id;
    option.textContent = `${workflow.name} · ${workflow.category}`;
    select.append(option);
  });
  select.disabled = state.workflows.length === 0;
  byId("workflow-plan-button").disabled = state.workflows.length === 0;
}

function openSoftware() {
  document.querySelectorAll(".nav-item").forEach((button) => button.classList.remove("active"));
  byId("software-nav").classList.add("active");
  byId("text-panel").classList.add("hidden");
  byId("image-panel").classList.add("hidden");
  byId("software-panel").classList.remove("hidden");
  byId("software-panel").scrollIntoView({ behavior: "smooth" });
}

function openImages() {
  document.querySelectorAll(".nav-item").forEach((button) => button.classList.remove("active"));
  byId("image-nav").classList.add("active");
  byId("text-panel").classList.add("hidden");
  byId("software-panel").classList.add("hidden");
  byId("image-panel").classList.remove("hidden");
  byId("image-panel").scrollIntoView({ behavior: "smooth" });
}

function setTaskControlsDisabled(disabled) {
  document.querySelectorAll(".mode-tab, .capability-nav").forEach((button) => {
    button.disabled = disabled;
  });
  byId("new-task-button").disabled = disabled;
}

function setProviderReady(ready) {
  byId("model").disabled = !ready;
  byId("prompt").disabled = !ready;
  byId("send-button").disabled = !ready;
}

async function api(path, body) {
  const response = await fetch(path, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-Haven-Token": state.token,
    },
    body: JSON.stringify(body),
  });
  const result = await response.json().catch(() => ({ error: "invalid-server-response" }));
  if (!response.ok) {
    const error = new Error(result.error || `request-failed-${response.status}`);
    error.details = result;
    throw error;
  }
  return result;
}

function humanError(error) {
  const messages = {
    "provider-host-must-be-ip-literal": "Enter a literal IP address; hostnames are not accepted.",
    "loopback-provider-required": "Enter the loopback address of an Ollama server on this computer.",
    "trusted-lan-provider-required": "The selected address is not a private local-network address.",
    "ollama-connection-failed": "Haven 42 could not reach Ollama at that address.",
    "ollama-chat-failed": "Ollama did not complete the text request.",
    "empty-model-response": "The model returned an empty response.",
    "capability-not-admitted": "That capability is not available in this Haven 42 release.",
  };
  return messages[error.message] || `Request blocked: ${error.message}`;
}

function showWizardStep(step) {
  document.querySelectorAll("[data-wizard-step]").forEach((panel) => {
    panel.classList.toggle("hidden", panel.dataset.wizardStep !== step);
  });
  document.querySelectorAll("[data-wizard-progress]").forEach((marker) => {
    marker.classList.toggle("active", marker.dataset.wizardProgress === step);
    if (marker.dataset.wizardProgress === step) marker.setAttribute("aria-current", "step");
    else marker.removeAttribute("aria-current");
  });
  const panel = document.querySelector(`[data-wizard-step="${step}"]`);
  const focusTarget = panel.querySelector("input, button, select, summary, [tabindex]");
  (focusTarget || byId("setup-wizard").querySelector(".wizard-card")).focus();
}

function readinessFacts(snapshot) {
  const memory = snapshot.platform.systemMemoryGiB == null
    ? "Unknown"
    : `${snapshot.platform.systemMemoryGiB} GiB`;
  const accelerator = snapshot.accelerators.length
    ? snapshot.accelerators.map((item) => `${item.vendor} ${item.model}${item.memoryGiB ? ` · ${item.memoryGiB} GiB` : ""}`).join(", ")
    : "Not detected or permission limited";
  const software = snapshot.software
    .filter((item) => ["python", "ollama"].includes(item.componentId))
    .map((item) => `${item.componentId === "python" ? "Python" : "Ollama"}: ${item.state}`)
    .join(" · ");
  return [
    ["Platform", `${snapshot.platform.operatingSystem} · ${snapshot.platform.architecture}`],
    ["Memory", memory],
    ["Accelerator", accelerator],
    ["Core software", software || "Unknown"],
  ];
}

function renderSystemReadiness(containerId, snapshot) {
  const container = byId(containerId);
  container.replaceChildren();
  container.classList.remove("hidden");
  for (const [label, value] of readinessFacts(snapshot)) {
    const row = document.createElement("div");
    row.className = "readiness-fact";
    const title = document.createElement("strong");
    title.textContent = label;
    const detail = document.createElement("span");
    detail.textContent = value;
    row.append(title, detail);
    container.append(row);
  }
}

function renderSetupPlan(plan) {
  const container = byId("wizard-setup-plan");
  container.replaceChildren();
  const heading = document.createElement("strong");
  heading.textContent = "Review-only setup plan";
  const summary = document.createElement("p");
  summary.textContent = plan.summary;
  const fit = document.createElement("p");
  fit.textContent = plan.hardwareAssessment.candidateModel
    ? `Hardware guidance: evaluate ${plan.hardwareAssessment.candidateModel} · planning confidence ${plan.hardwareAssessment.confidence}`
    : "Hardware guidance: no safe automatic model recommendation from the known capacity.";
  container.append(heading, summary, fit);
  for (const action of plan.actions) {
    const row = document.createElement("div");
    row.className = "plan-action";
    const label = document.createElement("strong");
    label.textContent = action.componentId;
    const stateLabel = document.createElement("span");
    stateLabel.textContent = `${action.state} · installation disabled`;
    row.append(label, stateLabel);
    container.append(row);
  }
}

async function runReadiness() {
  showWizardStep("readiness");
  byId("wizard-scan-status").textContent = "Scanning registered read-only facts…";
  byId("wizard-readiness-next").disabled = true;
  try {
    const snapshot = await api("/api/readiness", { force: true });
    state.readinessSnapshot = snapshot;
    renderSystemReadiness("wizard-system-readiness", snapshot);
    renderSystemReadiness("system-readiness", snapshot);
    const plan = await api("/api/setup-plan", {
      snapshotId: snapshot.snapshotId,
      intent: "guided-setup",
    });
    state.setupPlan = plan;
    renderSetupPlan(plan);
    byId("wizard-scan-status").textContent = "Read-only scan complete. Nothing was installed, downloaded, or saved.";
    byId("wizard-readiness-next").disabled = false;
  } catch (error) {
    byId("wizard-scan-status").textContent = humanError(error);
  }
}

function selectedModel(capabilityId) {
  const selection = state.modelSelections[capabilityId];
  if (!selection) return "";
  if (selection.mode === "automatic") {
    const recommendation = state.recommendations[capabilityId];
    return recommendation?.automatic ? recommendation.model : "";
  }
  return state.modelOptions.some((item) => item.name === selection.model)
    ? selection.model
    : "";
}

function renderModelSelect() {
  const select = byId("model");
  const capabilityId = state.capabilityId;
  const recommendation = state.recommendations[capabilityId];
  let selection = state.modelSelections[capabilityId];
  if (!selection || (
    selection.mode === "manual"
    && !state.modelOptions.some((item) => item.name === selection.model)
  )) {
    selection = { mode: recommendation?.automatic ? "automatic" : "none", model: null };
    state.modelSelections[capabilityId] = selection;
  }

  select.replaceChildren();
  const automatic = document.createElement("option");
  automatic.value = "automatic";
  automatic.textContent = recommendation?.automatic
    ? `Automatic — ${recommendation.model} (Recommended)`
    : "Automatic — no validated model installed";
  automatic.disabled = !recommendation?.automatic;
  select.append(automatic);

  if (state.modelOptions.length > 0) {
    const advanced = document.createElement("optgroup");
    advanced.label = "Advanced manual selection";
    for (const item of state.modelOptions) {
      const option = document.createElement("option");
      const status = item.capabilityStatus[capabilityId] || "unverified";
      option.value = `manual:${item.name}`;
      option.textContent = `${item.name} — ${status}`;
      advanced.append(option);
    }
    select.append(advanced);
  }

  if (selection.mode === "automatic" && recommendation?.automatic) {
    select.value = "automatic";
  } else if (selection.mode === "manual") {
    select.value = `manual:${selection.model}`;
  } else {
    select.selectedIndex = recommendation?.automatic ? 0 : -1;
  }
  const model = selectedModel(capabilityId);
  const status = selection.mode === "manual"
    ? state.modelOptions.find((item) => item.name === model)?.capabilityStatus[capabilityId]
    : recommendation?.status;
  byId("model-state").textContent = model
    ? `${status || "unverified"} · hardware fit not yet measured`
    : `Missing · install ${recommendation?.model || "a validated model"} manually, then reconnect`;
  byId("reset-model-button").classList.toggle(
    "hidden",
    selection.mode !== "manual" || !recommendation?.automatic,
  );
  const ready = state.connected && Boolean(model);
  select.disabled = !state.connected || state.modelOptions.length === 0;
  byId("prompt").disabled = !ready;
  byId("send-button").disabled = !ready;
  byId("prompt").placeholder = ready
    ? CAPABILITIES[capabilityId].placeholder
    : "Choose an installed model in Advanced to continue…";
}

function renderWizardReadiness() {
  const container = byId("wizard-readiness");
  container.replaceChildren();
  let automaticCount = 0;
  for (const [capabilityId, capability] of Object.entries(CAPABILITIES)) {
    const recommendation = state.recommendations[capabilityId] || {
      status: "missing",
      model: null,
      automatic: false,
    };
    if (recommendation.automatic) automaticCount += 1;
    const row = document.createElement("div");
    row.className = "readiness-row";
    const detail = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = capability.modelLabel;
    const model = document.createElement("span");
    model.textContent = recommendation.model || "No validated candidate";
    detail.append(title, model);
    const status = document.createElement("span");
    status.className = `readiness-state ${recommendation.status}`;
    status.textContent = recommendation.status;
    row.append(detail, status);
    container.append(row);
  }
  const usable = automaticCount > 0;
  byId("wizard-ready-title").textContent = usable ? "Your local AI is ready" : "A model is still needed";
  byId("wizard-ready-summary").textContent = usable
    ? `${automaticCount} capability-specific automatic selection${automaticCount === 1 ? " is" : "s are"} ready. Advanced users can override each model after setup.`
    : "No validated model is installed. Haven 42 did not download anything; install the listed model with Ollama, then check again. Installed unknown models remain available as explicit advanced choices.";
  byId("wizard-finish").disabled = !usable;
}

function validateExecutionEvents(events, expectedTerminal) {
  const allowedTypes = new Set(["accepted", "progress", "warning", "result", "error"]);
  if (!Array.isArray(events) || events.length === 0) throw new Error("invalid-execution-events");
  let terminalCount = 0;
  let terminalType = "";
  events.forEach((event, index) => {
    if (
      !event
      || typeof event !== "object"
      || Array.isArray(event)
      || Object.keys(event).sort().join(",") !== "code,sequence,type"
      || event.sequence !== index + 1
      || !allowedTypes.has(event.type)
      || typeof event.code !== "string"
      || !/^[A-Z][A-Z0-9_]{0,127}$/.test(event.code)
    ) {
      throw new Error("invalid-execution-events");
    }
    if (terminalCount > 0) throw new Error("event-after-terminal");
    if (event.type === "result" || event.type === "error") {
      terminalCount += 1;
      terminalType = event.type;
    }
  });
  if (terminalCount !== 1 || terminalType !== expectedTerminal) {
    throw new Error("invalid-terminal-event");
  }
  if (expectedTerminal === "result" && events[0].type !== "accepted") {
    throw new Error("missing-accepted-event");
  }
  return events.filter((event) => event.type === "warning");
}

function validateRecovery(recovery) {
  if (
    !recovery
    || typeof recovery !== "object"
    || Array.isArray(recovery)
    || Object.keys(recovery).sort().join(",") !== "automaticRetryAttempted,inputMayBeRestored,retryAllowed,retryRequiresNewRequest"
    || recovery.automaticRetryAttempted !== false
    || typeof recovery.retryAllowed !== "boolean"
    || recovery.retryRequiresNewRequest !== true
    || recovery.inputMayBeRestored !== true
  ) {
    throw new Error("invalid-recovery-envelope");
  }
  return recovery;
}

function validateFailureDetails(error, expectedKind) {
  const details = error?.details;
  if (
    !details
    || details.schemaVersion !== 1
    || details.kind !== `${expectedKind}-execution-error`
    || details.status !== "failed"
  ) throw new Error("invalid-server-response");
  validateExecutionEvents(details.events, "error");
  return validateRecovery(details.recovery);
}

function renderRunDetails(details) {
  const panel = byId("run-details");
  const list = byId("run-details-list");
  panel.classList.add("hidden");
  panel.open = false;
  list.replaceChildren();
  const expected = [
    "generationDurationMs", "inputTokens", "loadDurationMs", "outputTokens",
    "promptDurationMs", "providerReported", "tokensPerSecond", "totalDurationMs", "totalTokens",
  ];
  if (
    !details
    || typeof details !== "object"
    || Array.isArray(details)
    || Object.keys(details).sort().join(",") !== expected.sort().join(",")
    || details.providerReported !== true
  ) throw new Error("invalid-run-details");
  const numericFields = expected.filter((key) => key !== "providerReported");
  if (numericFields.some((key) => (
    details[key] !== null
    && (typeof details[key] !== "number" || !Number.isFinite(details[key]) || details[key] < 0)
  ))) throw new Error("invalid-run-details");
  const rows = [
    ["Input tokens", details.inputTokens],
    ["Output tokens", details.outputTokens],
    ["Total tokens", details.totalTokens],
    ["Generation speed", details.tokensPerSecond == null ? null : `${details.tokensPerSecond} tokens/s`],
    ["Elapsed", details.totalDurationMs == null ? null : `${details.totalDurationMs} ms`],
  ];
  rows.forEach(([label, value]) => {
    const row = document.createElement("div");
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value == null ? "Not reported" : String(value);
    row.append(term, description);
    list.append(row);
  });
  panel.classList.remove("hidden");
}

function renderTypedResult(result, capability) {
  if (
    !result.artifact
    || result.artifact.schemaVersion !== 1
    || result.artifact.sourceCapabilityId !== state.capabilityId
    || result.artifact.status !== "succeeded"
    || result.artifact.artifactType !== capability.artifactType
    || result.kind !== capability.artifactType
    || result.capabilityId !== state.capabilityId
    || typeof result.artifact.content?.text !== "string"
    || !result.artifact.content.text.trim()
    || result.artifact.policy?.fileWrite !== false
    || result.artifact.policy?.repositoryRead !== false
    || result.artifact.policy?.networkAccess !== false
    || result.artifact.policy?.modelDownload !== false
    || result.artifact.policy?.externalProvider !== false
    || typeof result.modelDigestVerified !== "boolean"
    || !Array.isArray(result.events)
  ) {
    throw new Error("invalid-typed-artifact");
  }
  const warnings = validateExecutionEvents(result.events, "result");
  const summary = `${capability.resultLabel} ready · typed ${result.artifact.artifactType} · no file written`;
  if (warnings.some((event) => event.code === "MODEL_SELECTION_UNVERIFIED_FOR_CAPABILITY")) {
    setTaskEvent(`Warning · model evidence is unverified for this capability · ${summary}`, "warning");
  } else {
    setTaskEvent(summary, "result");
  }
  renderRunDetails(result.runDetails);
  addMessage("assistant", result.artifact.content.text, capability.resultLabel);
}

function addMessage(role, content, label) {
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "assistant" ? "42" : "You";
  const body = document.createElement("div");
  const heading = document.createElement("strong");
  heading.textContent = label || (role === "assistant" ? "Haven 42" : "You");
  const text = document.createElement("p");
  text.textContent = content;
  body.append(heading, text);
  article.append(avatar, body);
  byId("messages").append(article);
  article.scrollIntoView({ behavior: "smooth", block: "end" });
  return article;
}

function resetTask() {
  state.messages = [];
  const capability = CAPABILITIES[state.capabilityId];
  const messages = byId("messages");
  messages.replaceChildren();
  addMessage("assistant", capability.welcome, "Haven 42");
  byId("prompt").value = "";
  byId("run-details").classList.add("hidden");
  byId("run-details-list").replaceChildren();
  byId("text-status").textContent = state.connected ? "Ready · nothing saved" : "Provider not connected";
}

function selectCapability(capabilityId) {
  if (!Object.hasOwn(CAPABILITIES, capabilityId)) return;
  state.capabilityId = capabilityId;
  byId("software-panel").classList.add("hidden");
  byId("image-panel").classList.add("hidden");
  byId("text-panel").classList.remove("hidden");
  const capability = CAPABILITIES[capabilityId];
  byId("capability-eyebrow").textContent = capability.eyebrow;
  byId("capability-title").textContent = capability.title;
  byId("prompt-label").textContent = capability.promptLabel;
  byId("model-label").textContent = capability.modelLabel;
  if (state.connected) renderModelSelect();
  document.querySelectorAll(".mode-tab").forEach((button) => {
    const active = button.dataset.capability === capabilityId;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  document.querySelectorAll(".capability-nav").forEach((button) => {
    button.classList.toggle("active", button.dataset.capability === capabilityId);
  });
  byId("home-nav").classList.remove("active");
  resetTask();
}

async function connectProvider(endpoint, timeoutSeconds, idleUnloadSeconds) {
  const result = await api("/api/connect", { endpoint, timeoutSeconds, idleUnloadSeconds });
  state.connected = true;
  state.recommendations = result.recommendations || {};
  state.modelOptions = result.modelOptions || [];
  state.capabilities = state.capabilities.map((capability) => (
    Object.hasOwn(CAPABILITIES, capability.id)
      ? { ...capability, state: "available" }
      : capability
  ));
  renderCapabilities();
  for (const capabilityId of Object.keys(CAPABILITIES)) {
    const selection = state.modelSelections[capabilityId];
    if (!selection || (
      selection.mode === "manual"
      && !state.modelOptions.some((item) => item.name === selection.model)
    )) {
      state.modelSelections[capabilityId] = {
        mode: state.recommendations[capabilityId]?.automatic ? "automatic" : "none",
        model: null,
      };
    }
  }
  renderModelSelect();
  const badge = byId("connection-badge");
  const location = result.trustScope === "loopback" ? "this computer" : "private network";
  badge.textContent = `Connected · ${location} · Ollama ${result.version}`;
  badge.classList.add("good");
  byId("endpoint").value = endpoint;
  byId("wizard-endpoint").value = endpoint;
  byId("timeout").value = String(timeoutSeconds);
  byId("wizard-timeout").value = String(timeoutSeconds);
  byId("idle-unload").value = String(idleUnloadSeconds);
  byId("wizard-idle-unload").value = String(idleUnloadSeconds);
  resetTask();
  byId("text-status").textContent = `${result.models.length} installed model${result.models.length === 1 ? "" : "s"} found`;
  byId("cleanup-status").textContent = result.idleUnloadSeconds === 0
    ? "Unload after every response"
    : `Unload after ${result.idleUnloadSeconds / 60} minutes idle`;
  byId("health-badge").textContent = "Healthy";
  byId("health-badge").classList.add("good");
  byId("provider-health").textContent = `${result.providerHealth.status} · ${result.providerHealth.trustScope}`;
  byId("evidence-status").textContent = result.evidenceBoundary.catalogStatus === "ready"
    ? "Capability evidence matched"
    : "Catalog unavailable";
  byId("digest-status").textContent = result.evidenceBoundary.immutableDigestBound
    ? "Bound"
    : "Not yet bound";
  return result;
}

async function bootstrap() {
  try {
    const response = await fetch("/api/bootstrap", { credentials: "same-origin" });
    if (!response.ok) throw new Error("bootstrap-failed");
    const result = await response.json();
    state.token = result.sessionToken;
    byId("app-version").textContent = `v${result.version}`;
    byId("host-status").textContent = `${result.runtime.platform} · ${result.runtime.architecture}`;
    state.capabilities = result.capabilities || [];
    renderCapabilities();
    await loadWorkflows();
    byId("update-status").textContent = result.updates?.mode === "disabled"
      ? "Disabled · no network"
      : "Unknown";
    state.lastFocusBeforeWizard = document.activeElement;
    byId("setup-wizard").querySelector(".wizard-card").focus();
  } catch (_error) {
    showError("Haven 42 could not initialize its secure local session.");
  }
}

byId("connection-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  const button = byId("connect-button");
  const wasConnected = state.connected;
  button.disabled = true;
  setProviderReady(false);
  button.textContent = "Checking…";
  try {
    await connectProvider(
      byId("endpoint").value.trim(),
      Number(byId("timeout").value),
      Number(byId("idle-unload").value),
    );
  } catch (error) {
    if (error.message === "ollama-connection-failed") {
      state.connected = false;
      byId("connection-badge").textContent = "Not connected";
      byId("connection-badge").classList.remove("good");
      byId("prompt").placeholder = "Reconnect Ollama to begin…";
      byId("text-status").textContent = "Provider not connected";
    } else {
      state.connected = wasConnected;
      setProviderReady(wasConnected);
    }
    showError(humanError(error));
  } finally {
    button.disabled = false;
    button.textContent = state.connected ? "Reconnect" : "Connect";
  }
});

byId("text-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  const prompt = byId("prompt");
  const content = prompt.value.trim();
  if (!content || !state.connected) return;
  const capability = CAPABILITIES[state.capabilityId];
  const capabilityId = state.capabilityId;
  const send = byId("send-button");
  send.disabled = true;
  prompt.disabled = true;
  setTaskControlsDisabled(true);
  prompt.value = "";
  const requestMessages = capabilityId === "general.chat"
    ? [...state.messages, { role: "user", content }].slice(-20)
    : [{ role: "user", content }];
  const previousMessages = [...state.messages];
  if (capabilityId === "general.chat") state.messages = requestMessages;
  const userMessage = addMessage("user", content, capabilityId === "content.summarize" ? "Source" : "You");
  byId("text-status").textContent = capability.busy;
  setTaskEvent("Accepted · bounded local request in progress");
  try {
    const model = selectedModel(capabilityId);
    if (!model) throw new Error("no-model-selected");
    const result = await api("/api/text", {
      capabilityId,
      model,
      messages: requestMessages,
    });
    if (capabilityId === "general.chat") {
      state.messages.push({ role: "assistant", content: result.content });
    }
    renderTypedResult(result, capability);
    byId("text-status").textContent = result.modelUnloaded
      ? `${result.model} · response complete · model unloaded`
      : `${result.model} · response complete · kept warm until idle timeout`;
  } catch (error) {
    let displayedError = error;
    let recovery = null;
    if (error.details?.events || error.details?.recovery) {
      try {
        validateExecutionEvents(error.details.events, "error");
        recovery = validateRecovery(error.details.recovery);
      } catch {
        displayedError = new Error("invalid-server-response");
      }
    }
    if (capabilityId === "general.chat") state.messages = previousMessages;
    userMessage.remove();
    prompt.value = content;
    showError(humanError(displayedError));
    const retry = recovery?.retryAllowed === true
      ? " · input restored; retry creates a new request"
      : " · input restored for review";
    setTaskEvent(`${humanError(displayedError)}${retry}`, "error");
    byId("text-status").textContent = "Text request failed";
  } finally {
    send.disabled = false;
    prompt.disabled = false;
    setTaskControlsDisabled(false);
    prompt.focus();
  }
});

document.querySelectorAll("[data-capability]").forEach((button) => {
  button.addEventListener("click", () => {
    selectCapability(button.dataset.capability);
    byId("text-panel").scrollIntoView({ behavior: "smooth" });
  });
});
byId("model").addEventListener("change", () => {
  const value = byId("model").value;
  state.modelSelections[state.capabilityId] = value === "automatic"
    ? { mode: "automatic", model: null }
    : { mode: "manual", model: value.slice("manual:".length) };
  renderModelSelect();
});
byId("reset-model-button").addEventListener("click", () => {
  state.modelSelections[state.capabilityId] = { mode: "automatic", model: null };
  renderModelSelect();
});
byId("new-task-button").addEventListener("click", async () => {
  setTaskControlsDisabled(true);
  let cleanupStatus = "";
  try {
    if (state.connected) {
      const result = await api("/api/unload", {});
      cleanupStatus = result.modelUnloaded
        ? "New task · active model unloaded"
        : "New task · model cleanup needs attention";
    }
  } catch (error) {
    showError(humanError(error));
  } finally {
    resetTask();
    setTaskEvent("");
    if (cleanupStatus) byId("text-status").textContent = cleanupStatus;
    setTaskControlsDisabled(false);
  }
});
byId("home-nav").addEventListener("click", () => {
  document.querySelectorAll(".nav-item").forEach((button) => button.classList.remove("active"));
  byId("home-nav").classList.add("active");
  window.scrollTo({ top: 0, behavior: "smooth" });
});
byId("software-nav").addEventListener("click", openSoftware);
byId("image-nav").addEventListener("click", openImages);
byId("workflow-plan-button").addEventListener("click", async () => {
  clearError();
  const button = byId("workflow-plan-button");
  button.disabled = true;
  try {
    const workflowId = byId("workflow-select").value;
    const result = await api("/api/workflow-plan", { workflowId });
    if (
      result.schemaVersion !== 1
      || result.kind !== "workflow-execution"
      || result.status !== "planned"
      || result.workflow?.id !== workflowId
      || result.workflow?.safetyLevel !== "read-only"
      || result.result?.invoked !== false
      || result.result?.processStarted !== false
      || result.result?.argumentsAccepted !== false
      || result.artifact?.artifactType !== "engineering-report"
      || result.artifact?.status !== "planned"
      || result.artifact?.policy?.repositoryRead !== false
      || result.artifact?.policy?.fileWrite !== false
      || result.artifact?.policy?.networkAccess !== false
    ) throw new Error("invalid-workflow-plan");
    validateExecutionEvents(result.events, "result");
    byId("workflow-result-title").textContent = result.artifact.content.title;
    byId("workflow-result-summary").textContent = result.artifact.content.summary;
    byId("workflow-result-policy").textContent = "No process started · no arguments · no repository read · no file write · no network";
    byId("workflow-result").classList.remove("hidden");
  } catch (error) {
    let displayedError = error;
    try {
      validateFailureDetails(error, "workflow");
    } catch {
      displayedError = new Error("invalid-server-response");
    }
    showError(humanError(displayedError));
  } finally {
    button.disabled = state.workflows.length === 0;
  }
});
byId("image-connect-button").addEventListener("click", async () => {
  clearError();
  const button = byId("image-connect-button");
  button.disabled = true;
  try {
    const result = await api("/api/image/connect", {
      endpoint: byId("image-endpoint").value.trim(),
      timeoutSeconds: 300,
    });
    if (
      result.schemaVersion !== 1
      || result.kind !== "image-provider-connection"
      || result.connected !== true
      || result.providerId !== "comfyui.local-image"
      || result.trustScope !== "loopback"
      || result.profile !== "linux-comfyui-sdxl-promoted"
      || result.configurationPersisted !== false
      || result.customNodesAllowed !== false
      || result.externalApiNodesAllowed !== false
      || result.providerRetainsOutput !== true
    ) throw new Error("invalid-image-provider-connection");
    state.imageConnected = true;
    ["image-prompt", "image-size", "image-steps", "image-run-button"].forEach((id) => {
      byId(id).disabled = false;
    });
    byId("image-provider-badge").textContent = "Connected · loopback";
    byId("image-provider-badge").classList.add("good");
    state.capabilities = state.capabilities.map((capability) => (
      capability.id === "media.image.create"
        ? { ...capability, state: "available", execution: "local" }
        : capability
    ));
    renderCapabilities();
  } catch (error) {
    state.imageConnected = false;
    showError(humanError(error));
  } finally {
    button.disabled = false;
  }
});
byId("image-run-button").addEventListener("click", async () => {
  clearError();
  const button = byId("image-run-button");
  const prompt = byId("image-prompt").value.trim();
  if (!state.imageConnected || !prompt) return;
  button.disabled = true;
  button.textContent = "Generating locally…";
  try {
    const size = Number(byId("image-size").value);
    const result = await api("/api/image/run", {
      prompt,
      width: size,
      height: size,
      steps: Number(byId("image-steps").value),
      seed: 424242,
    });
    if (
      result.schemaVersion !== 1
      || result.kind !== "image"
      || result.capabilityId !== "media.image.create"
      || result.status !== "succeeded"
      || result.promptPersisted !== false
      || result.endpointPersisted !== false
      || typeof result.imageBase64 !== "string"
      || !/^[A-Za-z0-9+/]+={0,2}$/.test(result.imageBase64)
      || result.artifact?.artifactType !== "image"
      || result.artifact?.status !== "succeeded"
      || result.artifact?.content?.delivery !== "browser-memory"
      || result.artifact?.policy?.fileWrite !== false
      || result.artifact?.policy?.repositoryRead !== false
      || result.artifact?.policy?.providerRetainedOutput !== true
    ) throw new Error("invalid-image-result");
    validateExecutionEvents(result.events, "result");
    const source = `data:image/png;base64,${result.imageBase64}`;
    byId("image-preview").src = source;
    byId("image-download").href = source;
    byId("image-result-summary").textContent = `${result.artifact.content.width} × ${result.artifact.content.height} PNG · browser memory only · provider copy retained`;
    byId("image-result").classList.remove("hidden");
  } catch (error) {
    let displayedError = error;
    try {
      validateFailureDetails(error, "image");
    } catch {
      displayedError = new Error("invalid-server-response");
    }
    showError(humanError(displayedError));
  } finally {
    button.disabled = !state.imageConnected;
    button.textContent = "Generate with disclosed retention";
  }
});
byId("models-nav").addEventListener("click", () => {
  byId("connection-panel").scrollIntoView({ behavior: "smooth" });
});
byId("system-nav").addEventListener("click", () => {
  byId("status-panel").scrollIntoView({ behavior: "smooth" });
});
document.querySelectorAll(".availability-nav").forEach((button) => {
  button.addEventListener("click", () => {
    byId("capability-panel").scrollIntoView({ behavior: "smooth" });
  });
});

byId("wizard-guided").addEventListener("click", runReadiness);
byId("wizard-existing").addEventListener("click", () => {
  showWizardStep("provider");
  byId("wizard-endpoint").focus();
});
byId("wizard-explore").addEventListener("click", () => {
  byId("setup-wizard").classList.add("hidden");
  byId("welcome-message").textContent = "Explore Chat, Writing, Summarization, Models, and System. Connect an existing Ollama provider whenever you are ready.";
  byId("connection-panel").scrollIntoView({ behavior: "smooth" });
});
byId("wizard-readiness-back").addEventListener("click", () => showWizardStep("welcome"));
byId("wizard-readiness-next").addEventListener("click", () => showWizardStep("provider"));
byId("scan-system-button").addEventListener("click", async () => {
  const button = byId("scan-system-button");
  button.disabled = true;
  button.textContent = "Scanning…";
  try {
    const snapshot = await api("/api/readiness", { force: true });
    state.readinessSnapshot = snapshot;
    renderSystemReadiness("system-readiness", snapshot);
    button.textContent = "Scan again";
  } catch (error) {
    showError(humanError(error));
    button.textContent = "Scan system readiness";
  } finally {
    button.disabled = false;
  }
});
byId("wizard-connection-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const errorBox = byId("wizard-error");
  errorBox.classList.add("hidden");
  const button = byId("wizard-connect");
  button.disabled = true;
  button.textContent = "Checking…";
  try {
    await connectProvider(
      byId("wizard-endpoint").value.trim(),
      Number(byId("wizard-timeout").value),
      Number(byId("wizard-idle-unload").value),
    );
    renderWizardReadiness();
    showWizardStep("ready");
  } catch (error) {
    state.connected = false;
    setProviderReady(false);
    errorBox.textContent = humanError(error);
    errorBox.classList.remove("hidden");
  } finally {
    button.disabled = false;
    button.textContent = "Check connection";
  }
});
byId("wizard-back").addEventListener("click", () => showWizardStep("provider"));
byId("wizard-finish").addEventListener("click", () => {
  byId("setup-wizard").classList.add("hidden");
  byId("prompt").focus();
});
byId("setup-wizard").addEventListener("keydown", (event) => {
  if (event.key !== "Tab") return;
  const focusable = [...byId("setup-wizard").querySelectorAll(
    'button:not([disabled]), input:not([disabled]), select:not([disabled]), summary, [tabindex]:not([tabindex="-1"])',
  )].filter((item) => !item.closest(".hidden"));
  if (focusable.length === 0) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
});

bootstrap();
