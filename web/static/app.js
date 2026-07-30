"use strict";

const CAPABILITIES = {
  "general.chat": {
    eyebrow: "CONVERSATION",
    title: "Private conversation",
    promptLabel: "Message",
    placeholder: "Ask anything…",
    busy: "Model is thinking locally…",
    welcome: "Ask a question, draft content, or summarize material here. The conversation stays in memory until you start a new task or close Haven 42.",
    resultLabel: "Haven 42",
    modelLabel: "Conversation model",
    artifactType: "chat-message",
  },
  "content.write": {
    eyebrow: "WRITING",
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
    eyebrow: "SUMMARY",
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

const DEFAULT_CONTEXT_IMAGE_LIMIT = 2;
const MAX_CONTEXT_IMAGE_LIMIT = 4;
const MAX_CONTEXT_IMAGE_TOTAL_BYTES = 8388608;
const MAX_CONTEXT_IMAGE_TOTAL_PIXELS = 33554432;
const CONTEXT_TEXT_MEDIA_TYPES = Object.freeze({
  ".cs": "text/plain",
  ".csv": "text/csv",
  ".go": "text/plain",
  ".java": "text/plain",
  ".js": "text/plain",
  ".jsx": "text/plain",
  ".json": "application/json",
  ".md": "text/markdown",
  ".py": "text/plain",
  ".rs": "text/plain",
  ".sql": "text/plain",
  ".tf": "text/plain",
  ".ts": "text/plain",
  ".tsx": "text/plain",
  ".txt": "text/plain",
});
const CONTEXT_SOURCE_EXTENSIONS = new Set([
  ".cs", ".go", ".java", ".js", ".jsx", ".py", ".rs", ".sql", ".tf", ".ts", ".tsx",
]);
const CHAT_TEXT_SIZES = ["small", "default", "large", "extra-large"];
const CHAT_TEXT_SIZE_LABELS = {
  small: "Small",
  default: "Default",
  large: "Large",
  "extra-large": "Extra large",
};
const CHAT_TEXT_SIZE_PERCENTAGES = {
  small: "90%",
  default: "100%",
  large: "115%",
  "extra-large": "130%",
};

const state = {
  token: "",
  connected: false,
  capabilityId: "general.chat",
  messages: [],
  promptHistory: [],
  promptHistoryLimit: 20,
  promptHistoryIndex: 0,
  promptHistoryDraft: "",
  chatTextSize: "default",
  contextFiles: [],
  contextImages: [],
  contextImageSequence: 0,
  contextImageLimit: DEFAULT_CONTEXT_IMAGE_LIMIT,
  providerTrustScope: null,
  providerTransportScheme: null,
  modelSelections: {},
  recommendations: {},
  modelOptions: [],
  modelSearchResults: [],
  desiredModel: null,
  idleUnloadSeconds: 300,
  providerConfig: null,
  capabilities: [],
  readinessSnapshot: null,
  setupPlan: null,
  workflows: [],
  assurance: null,
  imageConnected: false,
  lastFocusBeforeWizard: null,
  pendingTextRequest: null,
  approvedTextRequest: null,
};

const byId = (id) => document.getElementById(id);

function showError(message) {
  const box = byId("connection-error");
  box.textContent = message;
  box.tabIndex = -1;
  box.classList.remove("hidden");
  box.focus({ preventScroll: true });
}

function clearError() {
  const box = byId("connection-error");
  box.classList.add("hidden");
  box.removeAttribute("tabindex");
}

function showContextError(message) {
  const box = byId("context-error");
  box.textContent = message;
  box.tabIndex = -1;
  box.classList.remove("hidden");
  box.focus({ preventScroll: true });
}

function clearContextError() {
  const box = byId("context-error");
  box.textContent = "";
  box.classList.add("hidden");
  box.removeAttribute("tabindex");
}

function renderProviderTransportWarning(trustScope, transportScheme) {
  const boxes = [
    byId("connection-transport-warning"),
    byId("wizard-transport-warning"),
  ];
  const isHttp = transportScheme === "http";
  const message = !isHttp
    ? ""
    : trustScope === "loopback"
      ? "HTTP connection: traffic is not encrypted, but this Ollama endpoint is on this computer. Use HTTPS if your local threat model requires transport encryption."
      : "Security warning: this private-network Ollama connection uses unencrypted HTTP. Chat messages and attachments could be read or changed by someone able to observe that network. Use a trusted HTTPS endpoint or a loopback tunnel.";
  for (const box of boxes) {
    box.textContent = message;
    box.classList.toggle("hidden", !message);
    box.classList.toggle("loopback", isHttp && trustScope === "loopback");
  }
}

function motionBehavior() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
}

function activateNavigation(buttonId, targetId, focusId) {
  document.querySelectorAll(".nav-item").forEach((button) => button.classList.remove("active"));
  byId(buttonId).classList.add("active");
  const target = byId(targetId);
  target.scrollIntoView({ behavior: motionBehavior(), block: "start" });
  byId(focusId).focus({ preventScroll: true });
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

function validateAssuranceSummary(result) {
  const exactKeys = (value, fields) => (
    value
    && typeof value === "object"
    && !Array.isArray(value)
    && Object.keys(value).sort().join(",") === [...fields].sort().join(",")
  );
  const effects = [
    "filesystemWrite", "machineModification", "networkAccess",
    "processCreation", "providerInvocation", "repositoryRead",
  ];
  if (
    !exactKeys(result, [
      "disclosures", "effects", "evidence", "kind", "schemaVersion",
      "sources", "status", "surfaces",
    ])
    || result.schemaVersion !== 1
    || result.kind !== "read-only-assurance-summary"
    || result.status !== "ready"
    || !exactKeys(result.sources, ["evidenceCatalog", "surfaceMatrix", "surfaceSolutions"])
    || result.sources.evidenceCatalog !== "config/evidence-catalog.tsv"
    || result.sources.surfaceMatrix !== "config/agent-surface-capabilities.json"
    || result.sources.surfaceSolutions !== "config/agent-surface-solutions.json"
    || !exactKeys(result.evidence, ["modelCount", "recordCount", "statusCounts"])
    || !Number.isSafeInteger(result.evidence.recordCount)
    || result.evidence.recordCount < 1
    || result.evidence.recordCount > 10000
    || !Number.isSafeInteger(result.evidence.modelCount)
    || result.evidence.modelCount < 0
    || result.evidence.modelCount > result.evidence.recordCount
    || !Array.isArray(result.evidence.statusCounts)
    || result.evidence.statusCounts.length > 32
    || !Array.isArray(result.surfaces)
    || result.surfaces.length > 16
    || !exactKeys(result.effects, effects)
    || effects.some((field) => result.effects[field] !== false)
    || !exactKeys(result.disclosures, [
      "committedSanitizedEvidenceOnly", "liveValidationPerformed",
      "productionReadinessClaimed", "providerContacted",
      "repositoryInspected",
    ])
    || result.disclosures.committedSanitizedEvidenceOnly !== true
    || result.disclosures.liveValidationPerformed !== false
    || result.disclosures.productionReadinessClaimed !== false
    || result.disclosures.providerContacted !== false
    || result.disclosures.repositoryInspected !== false
  ) throw new Error("invalid-assurance-summary");
  const statuses = new Set();
  result.evidence.statusCounts.forEach((item) => {
    if (
      !exactKeys(item, ["count", "status"])
      || !/^[a-z][a-z0-9-]{0,63}$/.test(item.status)
      || statuses.has(item.status)
      || !Number.isSafeInteger(item.count)
      || item.count < 1
      || item.count > result.evidence.recordCount
    ) throw new Error("invalid-assurance-summary");
    statuses.add(item.status);
  });
  const surfaceIds = new Set();
  result.surfaces.forEach((surface) => {
    if (
      !exactKeys(surface, [
        "blockedActivities", "configureStatus", "id", "installStatus", "name",
        "supportTier", "supportedActivities", "testStatus", "validatedActivities",
        "validationLevel",
      ])
      || !/^[a-z][a-z0-9-]{0,63}$/.test(surface.id)
      || surfaceIds.has(surface.id)
      || typeof surface.name !== "string"
      || surface.name.length < 1
      || surface.name.length > 80
      || !["supported", "candidate"].includes(surface.supportTier)
      || !/^[a-z][a-z0-9-]{0,63}$/.test(surface.validationLevel)
      || !["supported", "validated", "planned", "scaffolded", "blocked", "retired"].includes(surface.installStatus)
      || !["supported", "validated", "planned", "scaffolded", "blocked", "retired"].includes(surface.configureStatus)
      || !["supported", "validated", "planned", "scaffolded", "blocked", "retired"].includes(surface.testStatus)
      || ["supportedActivities", "validatedActivities", "blockedActivities"].some(
        (field) => !Number.isSafeInteger(surface[field]) || surface[field] < 0 || surface[field] > 32,
      )
    ) throw new Error("invalid-assurance-summary");
    surfaceIds.add(surface.id);
  });
  return result;
}

function renderAssuranceSummary(result) {
  state.assurance = validateAssuranceSummary(result);
  byId("assurance-badge").textContent = "Committed evidence";
  byId("assurance-badge").classList.add("good");
  byId("assurance-record-count").textContent = String(result.evidence.recordCount);
  byId("assurance-model-count").textContent = String(result.evidence.modelCount);
  byId("assurance-surface-count").textContent = String(result.surfaces.length);
  byId("assurance-live-status").textContent = "Not run · read-only summary";
  const statuses = byId("assurance-status-list");
  statuses.replaceChildren();
  result.evidence.statusCounts.forEach((item) => {
    const row = document.createElement("div");
    row.className = "assurance-status-item";
    const label = document.createElement("span");
    label.textContent = item.status.replaceAll("-", " ");
    const count = document.createElement("strong");
    count.textContent = String(item.count);
    row.append(label, count);
    statuses.append(row);
  });
  const container = byId("assurance-surface-list");
  container.replaceChildren();
  result.surfaces.forEach((surface) => {
    const row = document.createElement("div");
    row.className = "assurance-item";
    const identity = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = surface.name;
    const detail = document.createElement("small");
    detail.textContent = `${surface.validationLevel} · ${surface.supportTier} · ${surface.supportedActivities} supported · ${surface.validatedActivities} validated · ${surface.blockedActivities} blocked`;
    identity.append(title, detail);
    const status = document.createElement("small");
    status.className = `assurance-state${surface.supportTier === "candidate" ? " candidate" : ""}`;
    status.textContent = `Install ${surface.installStatus} · Configure ${surface.configureStatus} · Test ${surface.testStatus}`;
    row.append(identity, status);
    container.append(row);
  });
}

function renderAssuranceUnavailable() {
  state.assurance = null;
  byId("assurance-badge").textContent = "Unavailable";
  byId("assurance-badge").classList.remove("good");
  byId("assurance-record-count").textContent = "Unavailable";
  byId("assurance-model-count").textContent = "Unavailable";
  byId("assurance-surface-count").textContent = "Unavailable";
  byId("assurance-live-status").textContent = "Not run";
  byId("assurance-status-list").replaceChildren();
  byId("assurance-surface-list").replaceChildren();
}

async function loadAssurance() {
  const result = await api("/api/assurance", {});
  renderAssuranceSummary(result);
}

function showPrimaryPanel(panelId, navigationId, focusId) {
  ["text-panel", "software-panel", "image-panel", "models-panel", "assurance-panel", "about-panel"].forEach((id) => {
    byId(id).classList.toggle("hidden", id !== panelId);
  });
  activateNavigation(navigationId, panelId, focusId);
}

function openSoftware() {
  showPrimaryPanel("software-panel", "software-nav", "software-title");
}

function openImages() {
  showPrimaryPanel("image-panel", "image-nav", "image-title");
}

function openModels() {
  byId("model-search-capability").value = state.capabilityId;
  updateModelChoiceStatus();
  renderModelDiscovery();
  showPrimaryPanel("models-panel", "models-nav", "models-title");
}

function openAbout() {
  showPrimaryPanel("about-panel", "about-nav", "about-title");
}

function openAssurance() {
  showPrimaryPanel("assurance-panel", "assurance-nav", "assurance-title");
}

function setTaskControlsDisabled(disabled) {
  byId("new-task-button").disabled = disabled;
  byId("keep-current-model").disabled = disabled;
  byId("use-recommended-model").disabled = disabled;
  byId("context-files").disabled = disabled || !state.connected;
  byId("browse-context").disabled = disabled || !state.connected;
  byId("clear-context").disabled = disabled;
  byId("context-image-limit").disabled = disabled;
  document.querySelectorAll(".remove-context-file, .remove-context-image").forEach((button) => {
    button.disabled = disabled;
  });
}

function setProviderReady(ready) {
  byId("model").disabled = !ready;
  byId("prompt").disabled = !ready;
  byId("send-button").disabled = !ready;
  byId("context-files").disabled = !ready;
  byId("browse-context").disabled = !ready;
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
    "explicit-online-search-consent-required": "Use “Search public catalog” to explicitly start an online search.",
    "invalid-model-search-query": "Use 1–64 letters, numbers, spaces, or model-name punctuation.",
    "model-catalog-search-failed": "The public Ollama catalog could not be reached.",
    "invalid-model-catalog-response": "The public catalog returned an invalid response, so Haven 42 rejected it.",
    "private-context-confirmation-required": "Confirm that the attached content may be sent to your private-network Ollama server.",
    "invalid-context-file-count": "Attach no more than five text files.",
    "invalid-context-file-name": "A selected filename is not supported.",
    "invalid-context-file-type": "That file type isn't supported yet. Choose a text, CSV, JSON, source code, or PNG file.",
    "invalid-context-file-content": "A selected file is empty or is not supported text.",
    "context-file-content-type-mismatch": "This file's contents do not match its name. For safety, attach the original supported text, source-code, CSV, JSON, or PNG file.",
    "invalid-context-json": "The selected JSON file is malformed.",
    "context-json-too-complex": "The selected JSON file exceeds the supported depth or structure limit.",
    "invalid-context-csv": "The selected CSV file is malformed.",
    "context-csv-too-complex": "The selected CSV file exceeds the supported row, column, or cell limit.",
    "context-file-too-large": "Each attached file must be no larger than 64 KiB.",
    "context-total-too-large": "Attached files must total no more than 128 KiB.",
    "duplicate-context-file-name": "Remove the duplicate attached filename.",
    "invalid-context-image-count": "The screenshot limit selected for this task has been reached.",
    "invalid-context-image": "The selected screenshot is not a valid PNG image.",
    "invalid-context-image-name": "The screenshot name is not supported.",
    "invalid-context-image-type": "Only PNG screenshots can be selected or pasted in this initial version.",
    "context-image-too-large": "Each selected screenshot must be no larger than 4 MiB.",
    "context-image-total-too-large": "Selected screenshots must total no more than 8 MiB.",
    "context-image-total-pixels-too-large": "Selected screenshots must total no more than 33.5 million decoded pixels.",
    "context-image-dimensions-too-large": "Screenshots must be at most 4096×4096 and 16.7 million pixels.",
    "invalid-context-image-dimensions": "The screenshot dimensions could not be verified.",
    "duplicate-context-image-name": "Remove the duplicate screenshot filename.",
  };
  return messages[error.message] || `Request blocked: ${error.message}`;
}

function modelMatchesQuery(name, query) {
  return !query || name.toLocaleLowerCase().includes(query.toLocaleLowerCase());
}

function cleanupPolicyLabel(seconds) {
  return seconds === 0
    ? "Unload after every response"
    : `Unload after ${seconds / 60} minutes idle`;
}

function applyChatTextSize(size) {
  if (!Object.hasOwn(CHAT_TEXT_SIZE_LABELS, size)) return false;
  state.chatTextSize = size;
  byId("text-panel").dataset.chatTextSize = size;
  byId("chat-text-size-status").textContent = (
    `${CHAT_TEXT_SIZE_LABELS[size]} chat text size · session only`
  );
  byId("chat-text-size-value").value = CHAT_TEXT_SIZE_PERCENTAGES[size];
  byId("chat-text-size-value").textContent = CHAT_TEXT_SIZE_PERCENTAGES[size];
  const index = CHAT_TEXT_SIZES.indexOf(size);
  byId("decrease-chat-text").disabled = index === 0;
  byId("increase-chat-text").disabled = index === CHAT_TEXT_SIZES.length - 1;
  return true;
}

function adjustChatTextSize(direction) {
  const index = CHAT_TEXT_SIZES.indexOf(state.chatTextSize);
  const nextIndex = Math.min(
    CHAT_TEXT_SIZES.length - 1,
    Math.max(0, index + direction),
  );
  applyChatTextSize(CHAT_TEXT_SIZES[nextIndex]);
}

function providerFormConfig(prefix = "") {
  return {
    endpoint: byId(`${prefix}endpoint`).value.trim(),
    timeoutSeconds: Number(byId(`${prefix}timeout`).value),
    idleUnloadSeconds: Number(byId(`${prefix}idle-unload`).value),
  };
}

function providerConfigChanged(config) {
  return !state.providerConfig
    || config.endpoint !== state.providerConfig.endpoint
    || config.timeoutSeconds !== state.providerConfig.timeoutSeconds
    || config.idleUnloadSeconds !== state.providerConfig.idleUnloadSeconds;
}

function updateProviderConnectionControl() {
  const button = byId("connect-button");
  if (!state.connected) {
    button.disabled = false;
    button.textContent = "Connect";
    return;
  }
  const changed = providerConfigChanged(providerFormConfig());
  button.disabled = !changed;
  button.textContent = changed ? "Apply changes" : "Connected";
}

function updateWizardConnectionControl() {
  const button = byId("wizard-connect");
  if (!state.connected) {
    button.disabled = false;
    button.textContent = "Check connection";
    return;
  }
  const changed = providerConfigChanged(providerFormConfig("wizard-"));
  button.disabled = false;
  button.textContent = changed ? "Apply changes" : "Continue";
}

function updateCleanupPolicyControl() {
  const button = byId("apply-cleanup-policy");
  const changed = Number(byId("system-idle-unload").value) !== state.idleUnloadSeconds;
  button.disabled = !changed;
  button.textContent = changed ? "Apply changes" : (state.connected ? "Applied" : "Selected");
}

function validateModelSearch(result) {
  const expected = [
    "configurationChanged", "downloadsPerformed", "hardwareProfileSent", "kind",
    "networkUsed", "query", "queryPersisted", "repositoryContentSent", "results",
    "schemaVersion", "source",
  ];
  if (
    !result
    || typeof result !== "object"
    || Array.isArray(result)
    || Object.keys(result).sort().join(",") !== expected.sort().join(",")
    || result.schemaVersion !== 1
    || result.kind !== "model-catalog-search"
    || result.source !== "ollama-public-catalog"
    || result.networkUsed !== true
    || result.downloadsPerformed !== false
    || result.configurationChanged !== false
    || result.queryPersisted !== false
    || result.repositoryContentSent !== false
    || result.hardwareProfileSent !== false
    || !Array.isArray(result.results)
    || result.results.length > 20
  ) throw new Error("invalid-model-catalog-response");
  const names = new Set();
  result.results.forEach((item) => {
    const installed = item?.status === "installed";
    if (
      !item
      || typeof item !== "object"
      || Array.isArray(item)
      || Object.keys(item).sort().join(",") !== [
        "capabilityEvidence", "executionAllowed", "hardwareFit", "installCommand",
        "licenseStatus", "name", "source", "status", "validationStatus",
      ].sort().join(",")
      || !/^[A-Za-z0-9][A-Za-z0-9._/:+-]{0,255}$/.test(item.name)
      || names.has(item.name)
      || item.source !== "ollama-public-catalog"
      || !["installed", "not-installed"].includes(item.status)
      || item.validationStatus !== "candidate-only"
      || item.capabilityEvidence !== "unverified"
      || item.hardwareFit !== "unknown"
      || item.licenseStatus !== "review-required"
      || item.executionAllowed !== installed
      || item.installCommand !== (installed ? null : `ollama pull ${item.name}`)
    ) throw new Error("invalid-model-catalog-response");
    names.add(item.name);
  });
  return result;
}

function chooseDiscoveredModel(item) {
  const capabilityId = byId("model-search-capability").value;
  if (item.status === "installed") {
    state.modelSelections[capabilityId] = { mode: "manual", model: item.name };
    state.desiredModel = null;
    if (capabilityId === state.capabilityId) renderModelSelect();
    byId("model-choice-status").textContent = `${item.name} selected for ${CAPABILITIES[capabilityId].modelLabel.toLocaleLowerCase()}.`;
  } else {
    state.desiredModel = item;
    byId("model-choice-status").textContent = `${item.name} is not installed. Execution remains disabled.`;
  }
  renderModelDiscovery();
}

function updateModelChoiceStatus() {
  const capabilityId = byId("model-search-capability").value;
  const model = selectedModel(capabilityId);
  byId("model-choice-status").textContent = model
    ? `${model} is configured for ${CAPABILITIES[capabilityId].modelLabel.toLocaleLowerCase()}.`
    : state.connected
      ? `No model is selected for ${CAPABILITIES[capabilityId].modelLabel.toLocaleLowerCase()}.`
      : "Connect Ollama to discover installed models.";
}

function renderModelDiscovery() {
  const query = byId("model-search-query").value.trim();
  const capabilityId = byId("model-search-capability").value;
  const installed = state.modelOptions
    .filter((item) => modelMatchesQuery(item.name, query))
    .map((item) => ({
      name: item.name,
      status: "installed",
      validationStatus: item.capabilityStatus[capabilityId] || "unverified",
      installCommand: null,
    }));
  const merged = new Map(installed.map((item) => [item.name, item]));
  state.modelSearchResults.forEach((item) => {
    if (modelMatchesQuery(item.name, query) && !merged.has(item.name)) merged.set(item.name, item);
  });
  const validationPriority = { recommended: 0, compatible: 1, unverified: 2 };
  const configuredModel = selectedModel(capabilityId);
  const results = [...merged.values()].sort((left, right) => {
    const leftConfigured = left.status === "installed" && left.name === configuredModel;
    const rightConfigured = right.status === "installed" && right.name === configuredModel;
    if (leftConfigured !== rightConfigured) return leftConfigured ? -1 : 1;
    if (left.status !== right.status) return left.status === "installed" ? -1 : 1;
    const validationDifference = (validationPriority[left.validationStatus] ?? 3)
      - (validationPriority[right.validationStatus] ?? 3);
    return validationDifference || left.name.localeCompare(right.name);
  });
  const container = byId("model-search-results");
  container.replaceChildren();
  results.forEach((item) => {
    const row = document.createElement("div");
    row.className = "model-search-result";
    const detail = document.createElement("div");
    const name = document.createElement("strong");
    name.textContent = item.name;
    const status = document.createElement("small");
    const configured = item.status === "installed" && selectedModel(capabilityId) === item.name;
    status.textContent = item.status === "installed"
      ? `Already installed on connected Ollama server · ${item.validationStatus}${configured ? " · selected" : ""}`
      : "Not installed on connected Ollama server · candidate only · evidence unverified · hardware fit unknown · license review required";
    detail.append(name, status);
    const choose = document.createElement("button");
    choose.className = "button secondary";
    choose.type = "button";
    const capabilityLabel = CAPABILITIES[capabilityId].modelLabel.replace(" model", "");
    choose.textContent = configured
      ? "Selected"
      : item.status === "installed"
        ? `Use for ${capabilityLabel}`
        : "Select candidate";
    choose.disabled = configured;
    choose.addEventListener("click", () => chooseDiscoveredModel(item));
    row.append(detail, choose);
    container.append(row);
  });
  if (results.length === 0 && !byId("model-search-status").textContent.includes("Searching")) {
    byId("model-search-status").textContent = "No installed or catalog matches yet.";
  } else if (installed.length > 0) {
    const capabilityLabel = CAPABILITIES[capabilityId].modelLabel.replace(" model", "");
    byId("model-search-status").textContent = `${installed.length} installed match${installed.length === 1 ? "" : "es"} shown for ${capabilityLabel}, with the most relevant options first.`;
  }
  const desired = byId("desired-model");
  desired.classList.toggle("hidden", !state.desiredModel);
  if (state.desiredModel) {
    byId("desired-model-name").textContent = state.desiredModel.name;
    byId("desired-model-state").textContent = "Desired model · not installed · execution disabled";
    byId("desired-model-command").textContent = state.desiredModel.installCommand;
  }
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

function suggestedCapability(content) {
  const normalized = content.trimStart().toLocaleLowerCase();
  if (/^(?:please\s+)?(?:summari[sz]e|condense|give me (?:a )?summary|tl;dr)\b/.test(normalized)) {
    return "content.summarize";
  }
  if (/^(?:please\s+)?(?:write|draft|compose|rewrite)\b/.test(normalized)) {
    return "content.write";
  }
  return "general.chat";
}

function hideModelSwitchPrompt() {
  state.pendingTextRequest = null;
  byId("model-switch-prompt").classList.add("hidden");
}

function showModelSwitchPrompt(request) {
  state.pendingTextRequest = request;
  const taskLabel = request.capabilityId === "content.write" ? "writing" : "summarization";
  byId("model-switch-description").textContent =
    `${request.recommendedModel} is the configured model for ${taskLabel}. ` +
    `Nothing has been sent. Choose whether to use it for this request or continue with ${request.currentModel}.`;
  byId("model-switch-prompt").classList.remove("hidden");
  byId("use-recommended-model").focus({ preventScroll: true });
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
  byId("context-files").disabled = !state.connected;
  byId("browse-context").disabled = !state.connected;
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

function renderTypedResult(result, capability, capabilityId) {
  if (
    !result.artifact
    || result.artifact.schemaVersion !== 1
    || result.artifact.sourceCapabilityId !== capabilityId
    || result.artifact.status !== "succeeded"
    || result.artifact.artifactType !== capability.artifactType
    || result.kind !== capability.artifactType
    || result.capabilityId !== capabilityId
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
  if (warnings.some((event) => event.code === "MODEL_IMAGE_INPUT_UNVERIFIED")) {
    setTaskEvent(`Warning · screenshot understanding is unverified for this model · ${summary}`, "warning");
  } else if (warnings.some((event) => event.code === "MODEL_SELECTION_UNVERIFIED_FOR_CAPABILITY")) {
    setTaskEvent(`Warning · model evidence is unverified for this capability · ${summary}`, "warning");
  } else {
    setTaskEvent(summary, "result");
  }
  renderRunDetails(result.runDetails);
  addMessage("assistant", result.artifact.content.text, capability.resultLabel);
}

function appendInlineMarkdown(container, source) {
  let buffer = "";
  const flush = () => {
    if (!buffer) return;
    container.append(document.createTextNode(buffer));
    buffer = "";
  };
  const markers = [
    { marker: "**", tag: "strong" },
    { marker: "__", tag: "strong" },
    { marker: "`", tag: "code" },
    { marker: "*", tag: "em" },
  ];
  for (let index = 0; index < source.length;) {
    if (source[index] === "\\" && index + 1 < source.length) {
      buffer += source[index + 1];
      index += 2;
      continue;
    }
    const match = markers.find(({ marker }) => source.startsWith(marker, index));
    if (!match) {
      buffer += source[index];
      index += 1;
      continue;
    }
    const end = source.indexOf(match.marker, index + match.marker.length);
    if (end <= index + match.marker.length) {
      buffer += match.marker;
      index += match.marker.length;
      continue;
    }
    flush();
    const element = document.createElement(match.tag);
    element.textContent = source.slice(index + match.marker.length, end);
    container.append(element);
    index = end + match.marker.length;
  }
  flush();
}

function markdownBlockKind(line) {
  if (/^```[A-Za-z0-9_+-]{0,32}\s*$/.test(line)) return "fence";
  if (/^#{1,4}\s+/.test(line)) return "heading";
  if (/^\s{0,3}[-*+]\s+/.test(line)) return "unordered";
  if (/^\s{0,3}\d{1,3}[.)]\s+/.test(line)) return "ordered";
  if (/^\s{0,3}>\s?/.test(line)) return "quote";
  if (/^\s{0,3}([-*_])(?:\s*\1){2,}\s*$/.test(line)) return "rule";
  return "";
}

function appendMarkdown(container, source) {
  const lines = source.replace(/\r\n?/g, "\n").split("\n");
  for (let index = 0; index < lines.length;) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }
    const kind = markdownBlockKind(line);
    if (kind === "fence") {
      const language = line.slice(3).trim();
      const codeLines = [];
      index += 1;
      while (index < lines.length && lines[index].trim() !== "```") {
        codeLines.push(lines[index]);
        index += 1;
      }
      if (index < lines.length) index += 1;
      const pre = document.createElement("pre");
      const code = document.createElement("code");
      if (language) code.dataset.language = language;
      code.textContent = codeLines.join("\n");
      pre.append(code);
      container.append(pre);
      continue;
    }
    if (kind === "heading") {
      const match = line.match(/^(#{1,4})\s+(.+)$/);
      const heading = document.createElement(`h${Math.min(5, match[1].length + 2)}`);
      appendInlineMarkdown(heading, match[2]);
      container.append(heading);
      index += 1;
      continue;
    }
    if (kind === "unordered" || kind === "ordered") {
      const list = document.createElement(kind === "unordered" ? "ul" : "ol");
      const pattern = kind === "unordered"
        ? /^\s{0,3}[-*+]\s+(.+)$/
        : /^\s{0,3}\d{1,3}[.)]\s+(.+)$/;
      while (index < lines.length) {
        const match = lines[index].match(pattern);
        if (!match) break;
        const item = document.createElement("li");
        appendInlineMarkdown(item, match[1]);
        list.append(item);
        index += 1;
      }
      container.append(list);
      continue;
    }
    if (kind === "quote") {
      const quoteLines = [];
      while (index < lines.length && markdownBlockKind(lines[index]) === "quote") {
        quoteLines.push(lines[index].replace(/^\s{0,3}>\s?/, ""));
        index += 1;
      }
      const quote = document.createElement("blockquote");
      appendInlineMarkdown(quote, quoteLines.join(" "));
      container.append(quote);
      continue;
    }
    if (kind === "rule") {
      container.append(document.createElement("hr"));
      index += 1;
      continue;
    }
    const paragraphLines = [line.trim()];
    index += 1;
    while (
      index < lines.length
      && lines[index].trim()
      && !markdownBlockKind(lines[index])
    ) {
      paragraphLines.push(lines[index].trim());
      index += 1;
    }
    const paragraph = document.createElement("p");
    appendInlineMarkdown(paragraph, paragraphLines.join(" "));
    container.append(paragraph);
  }
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
  const text = document.createElement("div");
  text.className = "message-content";
  if (role === "assistant") {
    appendMarkdown(text, content);
  } else {
    const paragraph = document.createElement("p");
    paragraph.textContent = content;
    text.append(paragraph);
  }
  body.append(heading, text);
  article.append(avatar, body);
  byId("messages").append(article);
  article.scrollIntoView({ behavior: motionBehavior(), block: "end" });
  return article;
}

function updatePromptHistoryStatus() {
  const count = state.promptHistory.length;
  byId("prompt-history-status").textContent = `${count} of ${state.promptHistoryLimit} prompt${count === 1 ? "" : "s"} retained · memory only · cleared with New task`;
}

function formatContextBytes(bytes) {
  return bytes < 1024 ? `${bytes} B` : `${Math.ceil(bytes / 1024)} KiB`;
}

function contextFormatLabel(mediaType, name = "") {
  const suffix = name.slice(name.lastIndexOf(".")).toLocaleLowerCase();
  if (CONTEXT_SOURCE_EXTENSIONS.has(suffix)) return "Source";
  return ({
    "application/json": "JSON",
    "text/csv": "CSV",
    "text/markdown": "Markdown",
    "text/plain": "Text",
  })[mediaType] || "Text";
}

function renderContextFiles() {
  const list = byId("context-file-list");
  list.replaceChildren();
  const totalBytes = state.contextFiles.reduce((sum, file) => sum + file.sizeBytes, 0);
  state.contextFiles.forEach((file, index) => {
    const item = document.createElement("li");
    item.className = "context-file";
    const name = document.createElement("span");
    name.className = "context-file-name";
    name.textContent = file.name;
    const meta = document.createElement("span");
    meta.className = "context-file-meta";
    meta.textContent = `${contextFormatLabel(file.mediaType, file.name)} · ${formatContextBytes(file.sizeBytes)} · ~${Math.ceil(file.sizeBytes / 4)} tokens`;
    const remove = document.createElement("button");
    remove.className = "button text-button remove-context-file";
    remove.type = "button";
    remove.textContent = "Remove";
    remove.setAttribute("aria-label", `Remove ${file.name}`);
    remove.addEventListener("click", () => {
      clearContextError();
      state.contextFiles.splice(index, 1);
      renderContextFiles();
    });
    const preview = document.createElement("details");
    preview.className = "context-preview";
    const previewSummary = document.createElement("summary");
    previewSummary.textContent = "Preview";
    previewSummary.setAttribute(
      "aria-label",
      `Preview selected ${contextFormatLabel(file.mediaType, file.name)}`,
    );
    const previewText = document.createElement("pre");
    previewText.textContent = file.content.length > 1000
      ? `${file.content.slice(0, 1000)}\n… preview limited to 1,000 characters`
      : file.content;
    preview.append(previewSummary, previewText);
    item.append(name, meta, remove, preview);
    list.append(item);
  });
  const count = state.contextFiles.length;
  list.classList.toggle("hidden", count === 0);
  renderContextImages();
  const imageCount = state.contextImages.length;
  const imageBytes = state.contextImages.reduce((sum, image) => sum + image.sizeBytes, 0);
  const parts = [];
  if (count) {
    parts.push(`${count} text file${count === 1 ? "" : "s"} · ${formatContextBytes(totalBytes)} · ~${Math.ceil(totalBytes / 4)} tokens`);
  }
  if (imageCount) {
    parts.push(`${imageCount} screenshot${imageCount === 1 ? "" : "s"} · ${formatContextBytes(imageBytes)}`);
  }
  byId("context-status").textContent = parts.length
    ? `${parts.join(" · ")} · memory only`
    : "No files or screenshots selected · memory only";
  byId("clear-context").classList.toggle("hidden", count === 0 && imageCount === 0);
  const showNetworkWarning = (count > 0 || imageCount > 0) && state.providerTrustScope === "trusted-lan";
  byId("context-network-warning").classList.toggle("hidden", !showNetworkWarning);
  byId("context-image-warning").classList.toggle("hidden", imageCount === 0);
}

function renderContextImages() {
  const list = byId("context-image-list");
  list.replaceChildren();
  state.contextImages.forEach((image, index) => {
    const item = document.createElement("li");
    item.className = "context-image";
    const thumbnail = document.createElement("img");
    thumbnail.src = image.dataUrl;
    thumbnail.alt = `Screenshot ${index + 1}: ${image.name}`;
    const meta = document.createElement("div");
    meta.className = "context-image-meta";
    const name = document.createElement("strong");
    name.textContent = image.name;
    const detail = document.createElement("span");
    detail.textContent = `${image.width}×${image.height} · ${formatContextBytes(image.sizeBytes)}`;
    meta.append(name, detail);
    const remove = document.createElement("button");
    remove.className = "button text-button remove-context-image";
    remove.type = "button";
    remove.textContent = "Remove";
    remove.setAttribute("aria-label", `Remove ${image.name}`);
    remove.addEventListener("click", () => {
      clearContextError();
      state.contextImages.splice(index, 1);
      renderContextFiles();
    });
    item.append(thumbnail, meta, remove);
    list.append(item);
  });
  list.classList.toggle("hidden", state.contextImages.length === 0);
}

function clearContextFiles() {
  clearContextError();
  state.contextFiles = [];
  state.contextImages = [];
  byId("context-files").value = "";
  renderContextFiles();
}

function updateContextImageLimitStatus() {
  byId("context-image-limit-status").textContent = (
    `Up to ${state.contextImageLimit} screenshot${state.contextImageLimit === 1 ? "" : "s"}`
    + " · 8 MiB and 33.5 million combined pixels remain the absolute limits"
  );
}

function resetContextImageLimit() {
  state.contextImageLimit = DEFAULT_CONTEXT_IMAGE_LIMIT;
  byId("context-image-limit").value = String(DEFAULT_CONTEXT_IMAGE_LIMIT);
  updateContextImageLimitStatus();
}

function inspectPngHeader(bytes) {
  const signature = [137, 80, 78, 71, 13, 10, 26, 10];
  if (
    bytes.byteLength < 33
    || signature.some((value, index) => bytes[index] !== value)
    || String.fromCharCode(...bytes.slice(12, 16)) !== "IHDR"
  ) throw new Error("invalid-context-image");
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const width = view.getUint32(16);
  const height = view.getUint32(20);
  if (
    width < 1
    || height < 1
    || width > 4096
    || height > 4096
    || width * height > 16777216
  ) throw new Error("context-image-dimensions-too-large");
  return { width, height };
}

function blobDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.addEventListener("load", () => resolve(String(reader.result)));
    reader.addEventListener("error", () => reject(new Error("invalid-context-image")));
    reader.readAsDataURL(blob);
  });
}

async function addContextImages(fileList, source = "clipboard") {
  const pending = [...fileList];
  if (state.contextImages.length + pending.length > state.contextImageLimit) {
    throw new Error("invalid-context-image-count");
  }
  const existing = new Set(state.contextImages.map((image) => image.name.toLocaleLowerCase()));
  const additions = [];
  let totalBytes = state.contextImages.reduce((sum, image) => sum + image.sizeBytes, 0);
  let totalPixels = state.contextImages.reduce(
    (sum, image) => sum + (image.width * image.height),
    0,
  );
  let nextSequence = state.contextImageSequence;
  for (const blob of pending) {
    if (blob.type !== "image/png") throw new Error("invalid-context-image-type");
    if (blob.size > 4194304) throw new Error("context-image-too-large");
    let name;
    if (source === "picker") {
      name = blob.name;
      if (
        typeof name !== "string"
        || !/^[A-Za-z0-9][A-Za-z0-9._ ()-]{0,119}$/.test(name)
        || !name.toLocaleLowerCase().endsWith(".png")
      ) throw new Error("invalid-context-image-name");
    } else {
      do {
        nextSequence += 1;
        name = `clipboard-screenshot-${nextSequence}.png`;
      } while (existing.has(name.toLocaleLowerCase()));
    }
    const foldedName = name.toLocaleLowerCase();
    if (existing.has(foldedName)) throw new Error("duplicate-context-image-name");
    const bytes = new Uint8Array(await blob.arrayBuffer());
    const { width, height } = inspectPngHeader(bytes);
    totalBytes += bytes.byteLength;
    if (totalBytes > MAX_CONTEXT_IMAGE_TOTAL_BYTES) {
      throw new Error("context-image-total-too-large");
    }
    totalPixels += width * height;
    if (totalPixels > MAX_CONTEXT_IMAGE_TOTAL_PIXELS) {
      throw new Error("context-image-total-pixels-too-large");
    }
    const dataUrl = await blobDataUrl(new Blob([bytes], { type: "image/png" }));
    additions.push({
      name,
      mediaType: "image/png",
      base64: dataUrl.slice(dataUrl.indexOf(",") + 1),
      sizeBytes: bytes.byteLength,
      width,
      height,
      dataUrl,
    });
    existing.add(foldedName);
  }
  state.contextImageSequence = nextSequence;
  state.contextImages.push(...additions);
  renderContextFiles();
}

async function addContextImage(blob) {
  await addContextImages([blob]);
}

function validateContextJson(content) {
  let parsed;
  try {
    parsed = JSON.parse(content);
  } catch {
    throw new Error("invalid-context-json");
  }
  const pending = [[parsed, 0]];
  let nodes = 0;
  while (pending.length) {
    const [current, depth] = pending.pop();
    if (depth > 64) throw new Error("context-json-too-complex");
    if (current && typeof current === "object") {
      nodes += 1;
      if (nodes > 10000) throw new Error("context-json-too-complex");
      Object.values(current).forEach((value) => pending.push([value, depth + 1]));
    }
  }
}

function validateContextCsv(content) {
  let quoted = false;
  let rows = 1;
  let columns = 1;
  let maximumColumns = 1;
  let cellCharacters = 0;
  for (let index = 0; index < content.length; index += 1) {
    const character = content[index];
    if (character === "\"") {
      if (quoted && content[index + 1] === "\"") {
        cellCharacters += 1;
        index += 1;
      } else {
        quoted = !quoted;
      }
    } else if (!quoted && character === ",") {
      columns += 1;
      maximumColumns = Math.max(maximumColumns, columns);
      cellCharacters = 0;
    } else if (!quoted && (character === "\n" || character === "\r")) {
      if (character === "\r" && content[index + 1] === "\n") index += 1;
      rows += 1;
      columns = 1;
      cellCharacters = 0;
    } else {
      cellCharacters += 1;
    }
    if (
      rows > 2000
      || maximumColumns > 256
      || cellCharacters > 8192
    ) throw new Error("context-csv-too-complex");
  }
  if (quoted) throw new Error("invalid-context-csv");
}

function bytesStartWith(bytes, signature) {
  return signature.every((value, index) => bytes[index] === value);
}

function validateContextContentIdentity(bytes, content, suffix, browserMediaType = "") {
  const blockedMediaTypes = new Set([
    "application/pdf",
    "application/zip",
    "application/x-7z-compressed",
    "application/x-rar-compressed",
    "application/x-msdownload",
    "application/x-powershell",
    "text/x-powershell",
    "text/x-shellscript",
  ]);
  if (blockedMediaTypes.has(browserMediaType.toLocaleLowerCase())) {
    throw new Error("context-file-content-type-mismatch");
  }
  const signatures = [
    [0x25, 0x50, 0x44, 0x46, 0x2d],
    [0x50, 0x4b, 0x03, 0x04],
    [0x7f, 0x45, 0x4c, 0x46],
    [0x1f, 0x8b],
    [0x52, 0x61, 0x72, 0x21, 0x1a, 0x07],
    [0x37, 0x7a, 0xbc, 0xaf, 0x27, 0x1c],
    [0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1],
  ];
  if (signatures.some((signature) => bytesStartWith(bytes, signature))) {
    throw new Error("context-file-content-type-mismatch");
  }
  if (
    bytes.length >= 64
    && bytes[0] === 0x4d
    && bytes[1] === 0x5a
  ) {
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const peOffset = view.getUint32(0x3c, true);
    if (
      peOffset <= bytes.length - 4
      && bytes[peOffset] === 0x50
      && bytes[peOffset + 1] === 0x45
      && bytes[peOffset + 2] === 0
      && bytes[peOffset + 3] === 0
    ) throw new Error("context-file-content-type-mismatch");
  }
  if ([...content].some((character) => {
    const code = character.codePointAt(0);
    return code < 32 && !["\t", "\n", "\r", "\f"].includes(character);
  })) throw new Error("context-file-content-type-mismatch");
  const sample = content.replace(/^[\ufeff \t\r\n]+/, "").slice(0, 8192);
  const firstLine = sample.split(/\r?\n/, 1)[0] || "";
  const shebang = firstLine.toLocaleLowerCase();
  if (shebang.startsWith("#!")) {
    if (/(?:^|[\/\s])(?:pwsh|powershell|bash|dash|fish|ksh|sh|zsh)(?:\s|$)/.test(shebang)) {
      throw new Error("context-file-content-type-mismatch");
    }
    if (/(?:^|[\/\s])python(?:[0-9.]*)?(?:\s|$)/.test(shebang) && suffix !== ".py") {
      throw new Error("context-file-content-type-mismatch");
    }
    if (/(?:^|[\/\s])node(?:\s|$)/.test(shebang) && ![".js", ".jsx", ".ts", ".tsx"].includes(suffix)) {
      throw new Error("context-file-content-type-mismatch");
    }
  }
  if (/^#requires\s+-(?:version|modules?|runasadministrator|psedition)\b/i.test(firstLine)) {
    throw new Error("context-file-content-type-mismatch");
  }
  if (/^\[cmdletbinding(?:\([^\r\n]*\))?\]\s*(?:\r?\n|$)/i.test(sample)) {
    throw new Error("context-file-content-type-mismatch");
  }
  if (/^@echo\s+off(?:\s|$)/i.test(firstLine)) {
    throw new Error("context-file-content-type-mismatch");
  }
  if (
    /^write-(?:host|output|error|warning|verbose|debug|information)\b/i.test(firstLine)
    || /^set-strictmode\b/i.test(firstLine)
    || /^\$erroractionpreference\s*=/i.test(firstLine)
  ) throw new Error("context-file-content-type-mismatch");
  if (/^param\s*\(/i.test(firstLine) && (
    sample.toLocaleLowerCase().includes("set-strictmode")
    || sample.toLocaleLowerCase().includes("$erroractionpreference")
    || /^\s*(?:write-host|write-output|get-|set-|invoke-|start-|stop-)[a-z]/im.test(sample)
  )) throw new Error("context-file-content-type-mismatch");
}

async function addContextFiles(fileList) {
  const pending = [...fileList];
  if (state.contextFiles.length + pending.length > 5) {
    throw new Error("invalid-context-file-count");
  }
  const existing = new Set(state.contextFiles.map((file) => file.name.toLocaleLowerCase()));
  const additions = [];
  let totalBytes = state.contextFiles.reduce((sum, file) => sum + file.sizeBytes, 0);
  for (const file of pending) {
    if (!/^[A-Za-z0-9][A-Za-z0-9._ ()-]{0,119}$/.test(file.name)) {
      throw new Error("invalid-context-file-name");
    }
    const suffix = file.name.slice(file.name.lastIndexOf(".")).toLocaleLowerCase();
    const mediaType = CONTEXT_TEXT_MEDIA_TYPES[suffix] || "";
    if (!mediaType) throw new Error("invalid-context-file-type");
    const foldedName = file.name.toLocaleLowerCase();
    if (existing.has(foldedName)) throw new Error("duplicate-context-file-name");
    if (file.size > 65536) throw new Error("context-file-too-large");
    const bytes = new Uint8Array(await file.arrayBuffer());
    let content;
    try {
      content = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    } catch {
      throw new Error("invalid-context-file-content");
    }
    const sizeBytes = new TextEncoder().encode(content).byteLength;
    if (!content || content.includes("\u0000")) throw new Error("invalid-context-file-content");
    if (sizeBytes > 65536) throw new Error("context-file-too-large");
    validateContextContentIdentity(bytes, content, suffix, file.type || "");
    if (suffix === ".json") validateContextJson(content);
    if (suffix === ".csv") validateContextCsv(content);
    totalBytes += sizeBytes;
    if (totalBytes > 131072) throw new Error("context-total-too-large");
    existing.add(foldedName);
    additions.push({ name: file.name, mediaType, content, sizeBytes });
  }
  state.contextFiles.push(...additions);
  renderContextFiles();
}

async function addContextAttachments(fileList) {
  const files = [...fileList];
  const textFiles = [];
  const imageFiles = [];
  for (const file of files) {
    const suffix = typeof file.name === "string"
      ? file.name.slice(file.name.lastIndexOf(".")).toLocaleLowerCase()
      : "";
    if (Object.hasOwn(CONTEXT_TEXT_MEDIA_TYPES, suffix)) {
      textFiles.push(file);
    } else if (suffix === ".png") {
      imageFiles.push(file);
    } else {
      throw new Error("invalid-context-file-type");
    }
  }
  const previousFiles = [...state.contextFiles];
  const previousImages = [...state.contextImages];
  const previousSequence = state.contextImageSequence;
  try {
    await addContextFiles(textFiles);
    await addContextImages(imageFiles, "picker");
  } catch (error) {
    state.contextFiles = previousFiles;
    state.contextImages = previousImages;
    state.contextImageSequence = previousSequence;
    renderContextFiles();
    throw error;
  }
}

function clearPromptHistory() {
  state.promptHistory = [];
  state.promptHistoryIndex = 0;
  state.promptHistoryDraft = "";
  updatePromptHistoryStatus();
}

function recordPromptHistory(content) {
  if (state.promptHistory.at(-1) !== content) {
    state.promptHistory.push(content);
    if (state.promptHistory.length > state.promptHistoryLimit) {
      state.promptHistory = state.promptHistory.slice(-state.promptHistoryLimit);
    }
  }
  state.promptHistoryIndex = state.promptHistory.length;
  state.promptHistoryDraft = "";
  updatePromptHistoryStatus();
}

function recallPrompt(direction) {
  const prompt = byId("prompt");
  if (
    state.promptHistory.length === 0
    || prompt.selectionStart !== prompt.selectionEnd
  ) return false;
  const onFirstLine = !prompt.value.slice(0, prompt.selectionStart).includes("\n");
  const onLastLine = !prompt.value.slice(prompt.selectionEnd).includes("\n");
  if ((direction < 0 && !onFirstLine) || (direction > 0 && !onLastLine)) return false;
  if (direction < 0) {
    if (state.promptHistoryIndex === state.promptHistory.length) {
      state.promptHistoryDraft = prompt.value;
    }
    state.promptHistoryIndex = Math.max(0, state.promptHistoryIndex - 1);
    prompt.value = state.promptHistory[state.promptHistoryIndex];
    prompt.setSelectionRange(0, 0);
    return true;
  }
  if (state.promptHistoryIndex >= state.promptHistory.length) return false;
  state.promptHistoryIndex += 1;
  prompt.value = state.promptHistoryIndex === state.promptHistory.length
    ? state.promptHistoryDraft
    : state.promptHistory[state.promptHistoryIndex];
  const end = prompt.value.length;
  prompt.setSelectionRange(end, end);
  return true;
}

function resetTask() {
  state.messages = [];
  state.approvedTextRequest = null;
  hideModelSwitchPrompt();
  clearPromptHistory();
  clearContextFiles();
  resetContextImageLimit();
  const capability = CAPABILITIES[state.capabilityId];
  const messages = byId("messages");
  messages.replaceChildren();
  addMessage("assistant", capability.welcome, "Haven 42");
  byId("prompt").value = "";
  byId("run-details").classList.add("hidden");
  byId("run-details-list").replaceChildren();
  byId("text-status").textContent = state.connected ? "Ready · nothing saved" : "Provider not connected";
}

async function connectProvider(endpoint, timeoutSeconds, idleUnloadSeconds) {
  const result = await api("/api/connect", { endpoint, timeoutSeconds, idleUnloadSeconds });
  state.connected = true;
  state.providerTrustScope = result.trustScope;
  state.providerTransportScheme = result.transportScheme;
  renderProviderTransportWarning(result.trustScope, result.transportScheme);
  state.recommendations = result.recommendations || {};
  state.modelOptions = result.modelOptions || [];
  if (state.desiredModel && state.modelOptions.some((item) => item.name === state.desiredModel.name)) {
    state.desiredModel = null;
  }
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
  renderModelDiscovery();
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
  byId("system-idle-unload").value = String(idleUnloadSeconds);
  state.idleUnloadSeconds = idleUnloadSeconds;
  state.providerConfig = { endpoint, timeoutSeconds, idleUnloadSeconds };
  updateProviderConnectionControl();
  updateWizardConnectionControl();
  updateCleanupPolicyControl();
  resetTask();
  byId("text-status").textContent = `${result.models.length} installed model${result.models.length === 1 ? "" : "s"} found`;
  byId("cleanup-status").textContent = cleanupPolicyLabel(result.idleUnloadSeconds);
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
    byId("about-version").textContent = `v${result.version}`;
    byId("host-status").textContent = `${result.runtime.platform} · ${result.runtime.architecture}`;
    state.capabilities = result.capabilities || [];
    renderCapabilities();
    await loadWorkflows();
    try {
      await loadAssurance();
    } catch (_error) {
      renderAssuranceUnavailable();
    }
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
  const requestedConfig = providerFormConfig();
  if (wasConnected && !providerConfigChanged(requestedConfig)) {
    updateProviderConnectionControl();
    return;
  }
  button.disabled = true;
  setProviderReady(false);
  button.textContent = "Checking…";
  try {
    await connectProvider(
      requestedConfig.endpoint,
      requestedConfig.timeoutSeconds,
      requestedConfig.idleUnloadSeconds,
    );
  } catch (error) {
    state.connected = wasConnected;
    setProviderReady(wasConnected);
    if (!wasConnected && error.message === "ollama-connection-failed") {
      state.connected = false;
      byId("connection-badge").textContent = "Not connected";
      byId("connection-badge").classList.remove("good");
      byId("prompt").placeholder = "Reconnect Ollama to begin…";
      byId("text-status").textContent = "Provider not connected";
    }
    showError(humanError(error));
  } finally {
    updateProviderConnectionControl();
  }
});

["endpoint", "timeout", "idle-unload"].forEach((id) => {
  byId(id).addEventListener(id === "endpoint" ? "input" : "change", updateProviderConnectionControl);
});

["wizard-endpoint", "wizard-timeout", "wizard-idle-unload"].forEach((id) => {
  byId(id).addEventListener(id === "wizard-endpoint" ? "input" : "change", updateWizardConnectionControl);
});

byId("model-search-query").addEventListener("input", () => {
  state.modelSearchResults = [];
  byId("model-search-status").textContent = "Filtering installed models locally.";
  renderModelDiscovery();
});

byId("model-search-capability").addEventListener("change", () => {
  state.modelSearchResults = [];
  state.desiredModel = null;
  byId("model-search-query").value = "";
  updateModelChoiceStatus();
  const capabilityLabel = CAPABILITIES[byId("model-search-capability").value].modelLabel.replace(" model", "");
  byId("model-search-status").textContent = `Showing installed models ranked for ${capabilityLabel}.`;
  renderModelDiscovery();
});

byId("model-search-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  const button = byId("model-search-button");
  const query = byId("model-search-query").value.trim();
  button.disabled = true;
  button.textContent = "Searching…";
  byId("model-search-status").textContent = "Searching the public Ollama catalog…";
  try {
    const result = validateModelSearch(await api("/api/model-search", { query, online: true }));
    state.modelSearchResults = result.results;
    byId("model-search-status").textContent = `${result.results.length} candidate${result.results.length === 1 ? "" : "s"} found. Nothing was downloaded.`;
    renderModelDiscovery();
  } catch (error) {
    state.modelSearchResults = [];
    byId("model-search-status").textContent = "Search stopped safely.";
    showError(humanError(error));
  } finally {
    button.disabled = false;
    button.textContent = "Search public catalog";
  }
});

byId("cleanup-policy-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  const button = byId("apply-cleanup-policy");
  const selectedSeconds = Number(byId("system-idle-unload").value);
  const previousSeconds = state.idleUnloadSeconds;
  if (selectedSeconds === state.idleUnloadSeconds) {
    updateCleanupPolicyControl();
    return;
  }
  byId("idle-unload").value = String(selectedSeconds);
  byId("wizard-idle-unload").value = String(selectedSeconds);
  if (!state.connected) {
    state.idleUnloadSeconds = selectedSeconds;
    byId("cleanup-status").textContent = `${cleanupPolicyLabel(selectedSeconds)} on next connection`;
    updateProviderConnectionControl();
    updateWizardConnectionControl();
    updateCleanupPolicyControl();
    return;
  }
  button.disabled = true;
  button.textContent = "Applying…";
  setProviderReady(false);
  try {
    await connectProvider(
      byId("endpoint").value.trim(),
      Number(byId("timeout").value),
      selectedSeconds,
    );
  } catch (error) {
    state.idleUnloadSeconds = previousSeconds;
    byId("idle-unload").value = String(previousSeconds);
    byId("wizard-idle-unload").value = String(previousSeconds);
    byId("system-idle-unload").value = String(previousSeconds);
    setProviderReady(true);
    showError(humanError(error));
  } finally {
    updateCleanupPolicyControl();
  }
});

byId("system-idle-unload").addEventListener("change", updateCleanupPolicyControl);

byId("prompt-history-limit").addEventListener("change", () => {
  const selectedLimit = Number(byId("prompt-history-limit").value);
  if (![20, 50, 100].includes(selectedLimit)) {
    byId("prompt-history-limit").value = String(state.promptHistoryLimit);
    return;
  }
  state.promptHistoryLimit = selectedLimit;
  state.promptHistory = state.promptHistory.slice(-selectedLimit);
  state.promptHistoryIndex = state.promptHistory.length;
  state.promptHistoryDraft = "";
  updatePromptHistoryStatus();
});

byId("decrease-chat-text").addEventListener("click", () => adjustChatTextSize(-1));
byId("increase-chat-text").addEventListener("click", () => adjustChatTextSize(1));

byId("context-image-limit").addEventListener("change", (event) => {
  clearError();
  clearContextError();
  const selectedLimit = Number(event.target.value);
  if (
    !Number.isInteger(selectedLimit)
    || selectedLimit < 1
    || selectedLimit > MAX_CONTEXT_IMAGE_LIMIT
    || state.contextImages.length > selectedLimit
  ) {
    event.target.value = String(state.contextImageLimit);
    if (state.contextImages.length > selectedLimit) {
      showContextError("Remove screenshots before lowering the limit for this task.");
    }
    return;
  }
  state.contextImageLimit = selectedLimit;
  updateContextImageLimitStatus();
});

byId("context-files").addEventListener("change", async (event) => {
  clearError();
  clearContextError();
  try {
    await addContextAttachments(event.target.files);
  } catch (error) {
    showContextError(humanError(error));
  } finally {
    event.target.value = "";
  }
});

byId("browse-context").addEventListener("click", () => {
  if (!byId("context-files").disabled) byId("context-files").click();
});

document.addEventListener("paste", async (event) => {
  const imageItems = [...(event.clipboardData?.items || [])].filter((item) => (
    item.kind === "file" && item.type.startsWith("image/")
  ));
  if (!imageItems.length) return;
  event.preventDefault();
  clearError();
  clearContextError();
  try {
    const blobs = imageItems.map((item) => item.getAsFile());
    if (blobs.some((blob) => !blob)) throw new Error("invalid-context-image");
    await addContextImages(blobs);
  } catch (error) {
    showContextError(humanError(error));
  }
});

byId("clear-context").addEventListener("click", clearContextFiles);

byId("copy-model-command").addEventListener("click", async () => {
  if (!state.desiredModel?.installCommand) return;
  try {
    await navigator.clipboard.writeText(state.desiredModel.installCommand);
    byId("copy-model-command").textContent = "Copied";
  } catch {
    byId("copy-model-command").textContent = "Select and copy the command above";
  }
});

byId("text-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  const prompt = byId("prompt");
  const content = prompt.value.trim();
  if (!content || !state.connected) return;
  const capabilityId = suggestedCapability(content);
  const capability = CAPABILITIES[capabilityId];
  const currentModel = selectedModel("general.chat");
  let model = currentModel;
  if (
    state.approvedTextRequest
    && state.approvedTextRequest.content === content
    && state.approvedTextRequest.capabilityId === capabilityId
  ) {
    model = state.approvedTextRequest.model;
    state.approvedTextRequest = null;
  } else {
    const recommendedModel = selectedModel(capabilityId);
    if (
      capabilityId !== "general.chat"
      && currentModel
      && recommendedModel
      && recommendedModel !== currentModel
    ) {
      showModelSwitchPrompt({ capabilityId, content, currentModel, recommendedModel });
      return;
    }
  }
  hideModelSwitchPrompt();
  const hasContext = Boolean(state.contextFiles.length || state.contextImages.length);
  const send = byId("send-button");
  send.disabled = true;
  prompt.disabled = true;
  setTaskControlsDisabled(true);
  prompt.value = "";
  const requestMessages = [...state.messages, { role: "user", content }].slice(-20);
  const previousMessages = [...state.messages];
  let focusPrompt = true;
  recordPromptHistory(content);
  state.messages = requestMessages;
  const userMessage = addMessage("user", content, "You");
  byId("text-status").textContent = capability.busy;
  setTaskEvent("Accepted · bounded local request in progress");
  try {
    if (!model) throw new Error("no-model-selected");
    const result = await api("/api/text", {
      capabilityId,
      model,
      messages: requestMessages,
      attachments: state.contextFiles,
      images: state.contextImages.map(({ dataUrl: _dataUrl, ...image }) => image),
      contextConsent: hasContext && state.providerTrustScope === "trusted-lan",
    });
    if (
      !result.context
      || result.context.fileCount !== state.contextFiles.length
      || result.context.totalBytes !== state.contextFiles.reduce((sum, file) => sum + file.sizeBytes, 0)
      || result.context.imageCount !== state.contextImages.length
      || result.context.imageTotalBytes !== state.contextImages.reduce((sum, image) => sum + image.sizeBytes, 0)
      || result.context.imageInputEvidence !== (state.contextImages.length ? "unverified" : "not-requested")
      || result.context.providerTrustScope !== state.providerTrustScope
      || result.context.persisted !== false
      || result.context.temporaryFilesWritten !== false
      || result.context.hostExecutionAllowed !== false
      || result.context.toolInvocationAllowed !== false
      || result.context.filesystemAccessAllowed !== false
    ) throw new Error("invalid-server-response");
    state.messages.push({ role: "assistant", content: result.content });
    renderTypedResult(result, capability, capabilityId);
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
    state.messages = previousMessages;
    userMessage.remove();
    prompt.value = content;
    clearContextFiles();
    showError(humanError(displayedError));
    focusPrompt = false;
    const retry = recovery?.retryAllowed === true
      ? " · input restored; retry creates a new request"
      : " · input restored for review";
    setTaskEvent(`${humanError(displayedError)}${retry}`, "error");
    byId("text-status").textContent = "Text request failed";
  } finally {
    send.disabled = false;
    prompt.disabled = false;
    setTaskControlsDisabled(false);
    if (focusPrompt) prompt.focus();
  }
});

byId("prompt").addEventListener("keydown", (event) => {
  if (
    (event.key === "ArrowUp" || event.key === "ArrowDown")
    && !event.altKey
    && !event.ctrlKey
    && !event.metaKey
    && !event.shiftKey
    && !event.isComposing
    && recallPrompt(event.key === "ArrowUp" ? -1 : 1)
  ) {
    event.preventDefault();
    return;
  }
  if (
    event.key !== "Enter"
    || event.shiftKey
    || event.isComposing
    || byId("send-button").disabled
  ) return;
  event.preventDefault();
  byId("text-form").requestSubmit();
});

byId("prompt").addEventListener("input", () => {
  state.promptHistoryIndex = state.promptHistory.length;
  state.promptHistoryDraft = "";
  state.approvedTextRequest = null;
  hideModelSwitchPrompt();
});

byId("keep-current-model").addEventListener("click", () => {
  const request = state.pendingTextRequest;
  if (!request) return;
  state.approvedTextRequest = {
    capabilityId: request.capabilityId,
    content: request.content,
    model: request.currentModel,
  };
  hideModelSwitchPrompt();
  byId("text-form").requestSubmit();
});

byId("use-recommended-model").addEventListener("click", () => {
  const request = state.pendingTextRequest;
  if (!request) return;
  state.modelSelections["general.chat"] = {
    mode: "manual",
    model: request.recommendedModel,
  };
  state.approvedTextRequest = {
    capabilityId: request.capabilityId,
    content: request.content,
    model: request.recommendedModel,
  };
  hideModelSwitchPrompt();
  renderModelSelect();
  byId("text-form").requestSubmit();
});
byId("model").addEventListener("change", () => {
  const value = byId("model").value;
  state.modelSelections[state.capabilityId] = value === "automatic"
    ? { mode: "automatic", model: null }
    : { mode: "manual", model: value.slice("manual:".length) };
  clearPromptHistory();
  clearContextFiles();
  renderModelSelect();
});
byId("reset-model-button").addEventListener("click", () => {
  state.modelSelections[state.capabilityId] = { mode: "automatic", model: null };
  clearPromptHistory();
  clearContextFiles();
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
  showPrimaryPanel("text-panel", "home-nav", "capability-title");
  window.scrollTo({ top: 0, behavior: motionBehavior() });
});
byId("software-nav").addEventListener("click", openSoftware);
byId("image-nav").addEventListener("click", openImages);
byId("models-nav").addEventListener("click", openModels);
byId("assurance-nav").addEventListener("click", openAssurance);
byId("about-nav").addEventListener("click", openAbout);
byId("workflow-plan-button").addEventListener("click", async () => {
  clearError();
  const button = byId("workflow-plan-button");
  button.disabled = true;
  byId("software-panel").setAttribute("aria-busy", "true");
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
    byId("workflow-result-title").focus({ preventScroll: true });
  } catch (error) {
    let displayedError = error;
    try {
      validateFailureDetails(error, "workflow");
    } catch {
      displayedError = new Error("invalid-server-response");
    }
    showError(humanError(displayedError));
  } finally {
    byId("software-panel").setAttribute("aria-busy", "false");
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
  byId("image-panel").setAttribute("aria-busy", "true");
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
    byId("image-preview").focus?.({ preventScroll: true });
  } catch (error) {
    let displayedError = error;
    try {
      validateFailureDetails(error, "image");
    } catch {
      displayedError = new Error("invalid-server-response");
    }
    showError(humanError(displayedError));
  } finally {
    byId("image-panel").setAttribute("aria-busy", "false");
    button.disabled = !state.imageConnected;
    button.textContent = "Generate with disclosed retention";
  }
});
byId("system-nav").addEventListener("click", () => {
  activateNavigation("system-nav", "status-panel", "system-title");
});
document.querySelectorAll(".availability-nav").forEach((button) => {
  button.addEventListener("click", () => {
    byId("capability-panel").scrollIntoView({ behavior: motionBehavior() });
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
  byId("connection-panel").scrollIntoView({ behavior: motionBehavior() });
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
  const wasConnected = state.connected;
  const requestedConfig = providerFormConfig("wizard-");
  if (wasConnected && !providerConfigChanged(requestedConfig)) {
    updateWizardConnectionControl();
    renderWizardReadiness();
    showWizardStep("ready");
    return;
  }
  button.disabled = true;
  button.textContent = "Checking…";
  try {
    await connectProvider(
      requestedConfig.endpoint,
      requestedConfig.timeoutSeconds,
      requestedConfig.idleUnloadSeconds,
    );
    renderWizardReadiness();
    showWizardStep("ready");
  } catch (error) {
    state.connected = wasConnected;
    setProviderReady(wasConnected);
    errorBox.textContent = humanError(error);
    errorBox.classList.remove("hidden");
  } finally {
    updateWizardConnectionControl();
  }
});
byId("wizard-back").addEventListener("click", () => {
  updateWizardConnectionControl();
  showWizardStep("provider");
});
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
