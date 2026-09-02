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
const MAX_DISCOVERED_MODELS = 512;
const MAX_MARKDOWN_DOM_ELEMENTS = 2048;
const SECTION_TOUR_STORAGE_KEY = "haven42.section-tours.v1";
const LAST_SECTION_STORAGE_KEY = "haven42.last-section.v1";
const SECTION_TOURS = Object.freeze({
  chat: Object.freeze({
    label: "Chat",
    revision: 11,
    panelId: "text-panel",
    returnId: "capability-title",
    steps: Object.freeze([
      { target: ".rail", title: "Move around Haven 42", description: "Use this menu to open Chat, Models, System, Technical details, or About. Each section has its own short help tour." },
      { target: ".conversation-toolbar", title: "See the model or change settings", description: "The current model and Automatic or Manual choice stay visible here. Open Settings to choose an installed model or a tested download, adjust text size, browse models, or start a new task." },
      { target: "#messages", title: "Your conversation comes first", description: "Questions and answers use the main area of this page. Haven 42 follows new replies unless you scroll up to review an earlier message." },
      { target: ".composer-surface", title: "Write and attach files", description: "Type your request here, press Enter to send, or use Shift+Enter for a new line. Attachments stay in memory for the current task, and the Keep setting controls prompt recall for this session." },
      { target: "#research-tools", title: "Research with explicit approval", description: "Choose Wikipedia or a wider-web browser search. Haven 42 shows the exact search words before every request, never lets the AI browse on its own, and keeps in-app research only in memory." },
      { target: ".status-glance", title: "Check connection and system activity", description: "This status area shows the active AI server, selected model, CPU, memory, graphics use, response speed, and your optional electricity estimate. “This computer” means AI requests stay on this device." },
    ]),
  }),
  models: Object.freeze({
    label: "Models",
    revision: 5,
    panelId: "models-panel",
    returnId: "models-title",
    steps: Object.freeze([
      { target: "#models-title", title: "Your AI models", description: "This page helps you understand and choose the models available from your connected Ollama server." },
      { target: "#model-search-capability", title: "Choose the task", description: "Select Chat, Writing, or Summarization to see which installed model Haven 42 recommends for that work." },
      { target: "#model-choice-status", title: "Read the recommendation", description: "This message explains the current model choice and whether Haven 42 has test evidence for the selected task." },
      { target: "#model-discovery", title: "Find another model", description: "Haven 42 lists installed models and tested choices for matching hardware. You can also search Ollama's public catalog. Every download requires your review and approval." },
      { target: "#model-search-form", title: "Search, review, then install", description: "Enter a model name or capability. If the model is not installed, select it and approve the download once. Haven 42 then shows live download progress and verifies the model before selecting it." },
    ]),
  }),
  system: Object.freeze({
    label: "System",
    revision: 5,
    panelId: "system-panel",
    returnId: "system-workspace-title",
    steps: Object.freeze([
      { target: "#system-workspace-title", title: "System settings", description: "Use this page to manage your AI connection, local components, resource information, and troubleshooting tools." },
      { target: "#connection-panel", title: "Connect another AI server", description: "A local setup connects automatically. Advanced users can use this area to switch to another trusted Ollama server." },
      { target: "#open-diagnostics", title: "Open troubleshooting logs", description: "Use this clearly labeled button to see recent sanitized technical events or save a support report. Search words, chats, and responses are not recorded." },
      { target: "#software-updates", title: "Choose certified or newest", description: "Certified releases are recommended. You may also review a newer official Ollama release before Haven 42 finishes compatibility testing; every install requires approval, and the certified runtime remains available for rollback." },
      { target: "#evidence-panel", title: "Check connection health", description: "These checks explain whether the AI server, model information, and local files are ready." },
      { target: "#energy-estimator-panel", title: "Estimate graphics-card electricity", description: "Use a measured GPU average and your own electricity rate. Official averages are optional, location is never inferred, and the result is not a whole-computer bill prediction." },
    ]),
  }),
  technical: Object.freeze({
    label: "Technical details",
    revision: 2,
    panelId: "assurance-panel",
    returnId: "assurance-title",
    steps: Object.freeze([
      { target: "#assurance-title", title: "Technical test details", description: "This optional page summarizes the evidence included with this Haven 42 build. It is mainly for advanced users and contributors." },
      { target: "#assurance-panel .status-list", title: "Evidence summary", description: "These counts show how many test records, models, and app surfaces are represented in the included evidence." },
      { target: "#assurance-status-list", title: "Evidence outcomes", description: "Review the recorded test outcomes here. Opening this page does not run a live hardware test." },
      { target: ".assurance-wiki-link", title: "Open the detailed evidence", description: "Use this link when you want the full evidence dashboard on GitHub. It opens an external website in a new tab." },
    ]),
  }),
  about: Object.freeze({
    label: "About",
    revision: 2,
    panelId: "about-panel",
    returnId: "about-title",
    steps: Object.freeze([
      { target: "#about-title", title: "About Haven 42", description: "This page explains what the app does, which version you are using, and how it handles your chat." },
      { target: "#about-panel .status-list", title: "What this version includes", description: "This summary covers text AI, experimental features, software tools, chat privacy, and the status of this test build." },
      { target: ".about-reference", title: "Accessibility information", description: "Open the Accessibility Statement to review completed checks, known limitations, and ways to report a barrier." },
      { target: ".alpha-reporting", title: "Get help or report a problem", description: "Prepare safe computer details, open the short problem form, or contact the project email. Nothing is collected or uploaded until you choose an action." },
    ]),
  }),
});
const PANEL_TOUR_SECTIONS = Object.freeze({
  "text-panel": "chat",
  "models-panel": "models",
  "system-panel": "system",
  "assurance-panel": "technical",
  "about-panel": "about",
});

const state = {
  token: "",
  browserSessionId: crypto.randomUUID(),
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
  testedModelOptions: [],
  testedModelCatalog: null,
  testedModelRequestId: 0,
  qualifiedModelCandidates: [],
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
  localSetupReturnToChat: false,
  pendingTextRequest: null,
  activeTextExecution: null,
  approvedTextRequest: null,
  pendingAnswerReport: null,
  alphaTextOnly: true,
  appVersion: "unknown",
  platformFamily: "unknown",
  lastMetricsAnnouncementAt: 0,
  electricityRateProfile: null,
  energyEstimate: null,
  chatAutoFollow: true,
  researchResultId: null,
  activePanelId: "text-panel",
  pendingModelInstall: null,
  modelInstallReturnToChat: false,
};

const byId = (id) => document.getElementById(id);

function showError(message, fieldId = null) {
  const box = byId("connection-error");
  box.textContent = message;
  if (fieldId) byId(fieldId)?.setAttribute("aria-invalid", "true");
  box.tabIndex = -1;
  box.classList.remove("hidden");
  box.focus({ preventScroll: true });
}

function clearError() {
  const box = byId("connection-error");
  box.classList.add("hidden");
  box.removeAttribute("tabindex");
  byId("endpoint")?.removeAttribute("aria-invalid");
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
      ? "Local connection notice: this connection is not encrypted, but it stays on this computer. Advanced users may choose HTTPS for additional protection."
      : "Security warning: this connection to another computer is not encrypted. Someone with access to that network could read or change chats and attachments. Use a trusted HTTPS address, or connect through a secure tunnel to 127.0.0.1.";
  for (const box of boxes) {
    box.textContent = message;
    box.classList.toggle("hidden", !message);
    box.classList.toggle("loopback", isHttp && trustScope === "loopback");
    box.setAttribute("aria-atomic", "true");
    if (!message) {
      box.setAttribute("role", "status");
      box.setAttribute("aria-live", "off");
    } else if (trustScope === "loopback") {
      box.setAttribute("role", "note");
      box.setAttribute("aria-live", "polite");
    } else {
      box.setAttribute("role", "alert");
      box.setAttribute("aria-live", "assertive");
    }
  }
}

function motionBehavior() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
}

function emptySectionTourState() {
  return Object.fromEntries(Object.keys(SECTION_TOURS).map((section) => [section, 0]));
}

function loadSectionTourState() {
  const result = emptySectionTourState();
  try {
    const saved = window.localStorage.getItem(SECTION_TOUR_STORAGE_KEY);
    if (!saved || saved.length > 2048) return result;
    const parsed = JSON.parse(saved);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return result;
    for (const section of Object.keys(result)) {
      const revision = parsed[section];
      result[section] = Number.isSafeInteger(revision) && revision > 0 ? revision : 0;
    }
  } catch (_error) {
    // Browser storage can be unavailable. Tours remain usable without persistence.
  }
  return result;
}

const sectionTourState = loadSectionTourState();
const activeSectionTour = { section: null, stepIndex: 0, returnFocus: null };

function saveSectionTourState() {
  try {
    const safeState = Object.fromEntries(
      Object.keys(SECTION_TOURS).map((section) => [section, sectionTourState[section]]),
    );
    window.localStorage.setItem(SECTION_TOUR_STORAGE_KEY, JSON.stringify(safeState));
  } catch (_error) {
    // Completion persistence is optional; never block the app when storage is unavailable.
  }
}

function activeTourConfiguration() {
  return activeSectionTour.section ? SECTION_TOURS[activeSectionTour.section] : null;
}

function visibleTourTarget(selector) {
  const target = document.querySelector(selector);
  if (!(target instanceof HTMLElement) || target.closest(".hidden")) return null;
  return target;
}

function positionSectionTour() {
  const configuration = activeTourConfiguration();
  if (!configuration) return;
  const step = configuration.steps[activeSectionTour.stepIndex];
  const target = visibleTourTarget(step.target);
  if (!target) return;
  const rect = target.getBoundingClientRect();
  const margin = 8;
  const spotlight = byId("section-tour-spotlight");
  const spotlightLeft = Math.max(margin, rect.left - margin);
  const spotlightTop = Math.max(margin, rect.top - margin);
  const spotlightRight = Math.min(window.innerWidth - margin, rect.right + margin);
  const spotlightBottom = Math.min(window.innerHeight - margin, rect.bottom + margin);
  spotlight.style.left = `${spotlightLeft}px`;
  spotlight.style.top = `${spotlightTop}px`;
  spotlight.style.width = `${Math.max(1, spotlightRight - spotlightLeft)}px`;
  spotlight.style.height = `${Math.max(1, spotlightBottom - spotlightTop)}px`;

  const dialog = byId("section-tour-dialog");
  const dialogRect = dialog.getBoundingClientRect();
  const gap = 18;
  const viewportPadding = 12;
  let left = rect.right + gap;
  let top = rect.top;
  if (left + dialogRect.width > window.innerWidth - viewportPadding) left = rect.left - dialogRect.width - gap;
  if (left < viewportPadding) {
    left = Math.min(
      Math.max(viewportPadding, rect.left),
      Math.max(viewportPadding, window.innerWidth - dialogRect.width - viewportPadding),
    );
    top = rect.bottom + gap;
    if (top + dialogRect.height > window.innerHeight - viewportPadding) top = rect.top - dialogRect.height - gap;
  }
  top = Math.min(
    Math.max(viewportPadding, top),
    Math.max(viewportPadding, window.innerHeight - dialogRect.height - viewportPadding),
  );
  dialog.style.left = `${Math.round(left)}px`;
  dialog.style.top = `${Math.round(top)}px`;
}

function renderSectionTourStep() {
  const configuration = activeTourConfiguration();
  if (!configuration) return;
  const step = configuration.steps[activeSectionTour.stepIndex];
  const target = visibleTourTarget(step.target);
  if (!target) {
    finishSectionTour();
    return;
  }
  const stepNumber = activeSectionTour.stepIndex + 1;
  byId("section-tour-progress").textContent = `${configuration.label} · Step ${stepNumber} of ${configuration.steps.length}`;
  byId("section-tour-title").textContent = step.title;
  byId("section-tour-description").textContent = step.description;
  byId("section-tour-dialog").setAttribute("aria-label", `${configuration.label} help, step ${stepNumber} of ${configuration.steps.length}`);
  byId("section-tour-back").disabled = activeSectionTour.stepIndex === 0;
  byId("section-tour-next").textContent = stepNumber === configuration.steps.length ? "Finish" : "Next";
  const dots = configuration.steps.map((_item, index) => {
    const dot = document.createElement("span");
    dot.className = "section-tour-dot";
    dot.classList.toggle("active", index === activeSectionTour.stepIndex);
    return dot;
  });
  byId("section-tour-dots").replaceChildren(...dots);
  target.scrollIntoView({ behavior: motionBehavior(), block: "center", inline: "nearest" });
  window.requestAnimationFrame(() => {
    positionSectionTour();
    byId("section-tour-next").focus({ preventScroll: true });
  });
}

function startSectionTour(section, options = {}) {
  if (!Object.hasOwn(SECTION_TOURS, section)) return false;
  const configuration = SECTION_TOURS[section];
  if (activeSectionTour.section) return false;
  if (!options.manual && sectionTourState[section] === configuration.revision) return false;
  const panel = byId(configuration.panelId);
  if (!panel || panel.classList.contains("hidden") || !byId("setup-wizard").classList.contains("hidden")) return false;
  activeSectionTour.section = section;
  activeSectionTour.stepIndex = 0;
  activeSectionTour.returnFocus = options.returnFocus instanceof HTMLElement
    ? options.returnFocus
    : byId(configuration.returnId);
  byId("section-tour-layer").classList.remove("hidden");
  byId("section-tour-layer").setAttribute("aria-hidden", "false");
  document.querySelector(".shell").inert = true;
  document.body.classList.add("section-tour-active");
  renderSectionTourStep();
  return true;
}

function finishSectionTour() {
  const configuration = activeTourConfiguration();
  if (!configuration) return;
  sectionTourState[activeSectionTour.section] = configuration.revision;
  saveSectionTourState();
  const returnTarget = activeSectionTour.returnFocus;
  activeSectionTour.section = null;
  activeSectionTour.stepIndex = 0;
  activeSectionTour.returnFocus = null;
  byId("section-tour-layer").classList.add("hidden");
  byId("section-tour-layer").setAttribute("aria-hidden", "true");
  document.querySelector(".shell").inert = false;
  document.body.classList.remove("section-tour-active");
  if (returnTarget instanceof HTMLElement && returnTarget.isConnected) {
    returnTarget.focus({ preventScroll: true });
  }
}

function scheduleSectionTour(section) {
  window.setTimeout(() => startSectionTour(section), 0);
}

function activateNavigation(buttonId, targetId, focusId) {
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.classList.remove("active");
    button.removeAttribute("aria-current");
  });
  byId(buttonId).classList.add("active");
  byId(buttonId).setAttribute("aria-current", "page");
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
  const urgent = kind === "error" || kind === "warning";
  event.setAttribute("role", urgent ? "alert" : "status");
  event.setAttribute("aria-live", urgent ? "assertive" : "polite");
  event.setAttribute("aria-atomic", "true");
}

function renderCapabilities() {
  const container = byId("capability-list");
  container.replaceChildren();
  const labels = {
    available: "Available",
    "configuration-required": "Setup needed",
    "not-admitted-in-web": "Not available yet",
    "provider-profile-required": "Setup needed",
  };
  for (const capability of state.capabilities) {
    const row = document.createElement("div");
    row.className = "capability-item";
    const detail = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = capability.label;
    const execution = document.createElement("small");
    execution.textContent = capability.execution === "local"
      ? "Runs using your connected AI server"
      : "Not available in this version";
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
    && Object.getPrototypeOf(value) === Object.prototype
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
  const outcomeGroups = [
    { id: "passed", title: "Passed", matches: (status) => /(?:pass|validated|verified|supported)/u.test(status) && !/(?:partial|fail|block)/u.test(status) },
    { id: "partial", title: "Partial or candidate", matches: (status) => /(?:partial|candidate|planned|scaffold|not-run|pending)/u.test(status) },
    { id: "blocked", title: "Failed or blocked", matches: (status) => /(?:fail|block|retired)/u.test(status) },
  ];
  const remaining = [...result.evidence.statusCounts];
  outcomeGroups.forEach((group) => {
    const items = remaining.filter((item) => group.matches(item.status));
    items.forEach((item) => remaining.splice(remaining.indexOf(item), 1));
    if (items.length === 0) return;
    const cluster = document.createElement("section");
    cluster.className = `assurance-cluster ${group.id}`;
    const heading = document.createElement("h4");
    heading.textContent = group.title;
    const grid = document.createElement("div");
    grid.className = "assurance-cluster-grid";
    items.forEach((item) => {
      const row = document.createElement("div");
      row.className = `assurance-status-item ${group.id}`;
      const label = document.createElement("span");
      label.textContent = item.status.replaceAll("-", " ");
      const count = document.createElement("strong");
      count.textContent = String(item.count);
      row.append(label, count);
      grid.append(row);
    });
    cluster.append(heading, grid);
    statuses.append(cluster);
  });
  if (remaining.length > 0) {
    const cluster = document.createElement("section");
    cluster.className = "assurance-cluster informational";
    const heading = document.createElement("h4");
    heading.textContent = "Informational";
    const grid = document.createElement("div");
    grid.className = "assurance-cluster-grid";
    remaining.forEach((item) => {
      const row = document.createElement("div");
      row.className = "assurance-status-item informational";
      const label = document.createElement("span");
      label.textContent = item.status.replaceAll("-", " ");
      const count = document.createElement("strong");
      count.textContent = String(item.count);
      row.append(label, count);
      grid.append(row);
    });
    cluster.append(heading, grid);
    statuses.append(cluster);
  }
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
  if (panelId !== "text-panel") byId("research-tools").open = false;
  if (panelId !== "text-panel") byId("conversation-settings").open = false;
  ["text-panel", "software-panel", "image-panel", "models-panel", "system-panel", "assurance-panel", "about-panel"].forEach((id) => {
    byId(id).classList.toggle("hidden", id !== panelId);
  });
  state.activePanelId = panelId;
  try {
    window.localStorage.setItem(LAST_SECTION_STORAGE_KEY, panelId);
  } catch (_error) {
    // Remembering the current section is optional and never stores user content.
  }
  activateNavigation(navigationId, panelId, focusId);
  const tourSection = PANEL_TOUR_SECTIONS[panelId];
  if (tourSection) scheduleSectionTour(tourSection);
}

function restoreLastSection() {
  let panelId = "text-panel";
  try {
    panelId = window.localStorage.getItem(LAST_SECTION_STORAGE_KEY) || panelId;
  } catch (_error) {
    // Use Chat when browser storage is unavailable.
  }
  const routes = {
    "text-panel": openChat,
    "models-panel": openModels,
    "system-panel": openSystem,
    "assurance-panel": openAssurance,
    "about-panel": openAbout,
  };
  (routes[panelId] || openChat)();
}

function initializeSystemWorkspace() {
  const workspace = byId("system-workspace-content");
  for (const id of ["alpha-metrics", "connection-panel", "status-panel", "capability-panel", "evidence-panel", "energy-estimator-panel"]) {
    workspace.append(byId(id));
  }
}

const ENERGY_MEASUREMENT_PROFILES = Object.freeze({
  "rx7800xt-qwen35-9b": Object.freeze({
    watts: 40.084,
    label: "RX 7800 XT · Qwen 3.5 9B · Ollama 0.32.5",
  }),
});

// The official European source supports this admitted country set. Country
// choices are explicit; Haven 42 never infers a location from the network,
// operating system, or browser.
const EUROSTAT_COUNTRIES = new Set([
  "AL", "AT", "BA", "BE", "BG", "CH", "CY", "CZ", "DE", "DK", "EE",
  "ES", "FI", "FR", "GB", "GE", "GR", "HR", "HU", "IE", "IS", "IT",
  "LI", "LT", "LU", "LV", "MD", "ME", "MK", "MT", "NL", "NO", "PL",
  "PT", "RO", "RS", "SE", "SI", "SK", "TR", "UA", "XK",
]);

function applyCountryCurrency() {
  const selected = byId("energy-country").selectedOptions[0];
  const currency = selected?.dataset.currency;
  if (byId("energy-rate-source").value !== "eia") {
    byId("energy-currency").value = currency || "";
  }
}

function filterEnergyCountries(source) {
  const countrySelect = byId("energy-country");
  for (const option of countrySelect.options) {
    const supported = source === "manual"
      || (source === "eia" && option.value === "US")
      || (source === "eurostat" && EUROSTAT_COUNTRIES.has(option.value));
    option.hidden = !supported;
    option.disabled = !supported;
  }
  if (countrySelect.selectedOptions[0]?.disabled) {
    countrySelect.value = source === "eurostat" ? "DE" : "US";
  }
  applyCountryCurrency();
}

function energyNumber(id, minimum, maximum) {
  const value = Number(byId(id).value);
  if (!Number.isFinite(value) || value < minimum || value > maximum) {
    byId(id).setAttribute("aria-invalid", "true");
    return null;
  }
  byId(id).removeAttribute("aria-invalid");
  return value;
}

function updateEnergyRateControls() {
  const source = byId("energy-rate-source").value;
  const official = source !== "manual";
  byId("fetch-official-rate").classList.toggle("hidden", !official);
  byId("energy-rate").readOnly = official;
  byId("energy-region-label").classList.toggle("hidden", source === "eurostat");
  filterEnergyCountries(source);
  if (source === "eia") {
    byId("energy-country").value = "US";
    byId("energy-country").disabled = true;
    byId("energy-currency").value = "USD";
    byId("energy-currency").readOnly = true;
    byId("energy-rate-help").textContent = "This government source provides a U.S. national or state household average—not your utility's exact rate. Choose Get selected official average to continue.";
  } else if (source === "eurostat") {
    byId("energy-country").disabled = false;
    applyCountryCurrency();
    byId("energy-currency").readOnly = true;
    byId("energy-region").value = "";
    byId("energy-rate-help").textContent = "Choose your country, then request the latest available household average with taxes included. Haven 42 selects that country's usual currency.";
  } else {
    byId("energy-country").disabled = false;
    byId("energy-currency").readOnly = false;
    byId("energy-rate-help").textContent = "Look on your bill for the price per kilowatt-hour (kWh). This is usually more accurate than a country or state average.";
  }
  state.electricityRateProfile = null;
  if (official) byId("energy-rate").value = "";
  byId("energy-estimate-result").classList.add("hidden");
}

function updateEnergyMeasurement() {
  const profile = ENERGY_MEASUREMENT_PROFILES[byId("energy-measurement-profile").value];
  const input = byId("energy-average-watts");
  input.readOnly = Boolean(profile);
  input.value = profile ? String(profile.watts) : "";
  byId("energy-measurement-help").textContent = profile
    ? `${profile.label}. This is GPU-board power from one exact 30-minute test, not a general rating for the card.`
    : "Enter an average measured by your graphics vendor's tool or a wall meter. Do not enter the card's advertised maximum power.";
  byId("energy-estimate-result").classList.add("hidden");
}

async function fetchOfficialElectricityRate() {
  const button = byId("fetch-official-rate");
  const source = byId("energy-rate-source").value;
  const country = byId("energy-country").value.trim().toUpperCase();
  const currency = byId("energy-currency").value.trim().toUpperCase();
  const region = byId("energy-region").value.trim().toUpperCase();
  button.disabled = true;
  button.textContent = "Getting official average…";
  byId("energy-rate-help").textContent = "Contacting only the selected official source…";
  try {
    const profile = await api("/api/electricity-rate", { source, country, currency, region });
    if (
      profile.schemaVersion !== 1
      || profile.kind !== "haven42-electricity-rate-profile"
      || profile.sourceKind !== "official-average"
      || profile.locationWasInferred !== false
      || profile.estimateOnly !== true
      || !Number.isFinite(profile.ratePerKwh)
    ) throw new Error("invalid-electricity-rate-response");
    state.electricityRateProfile = profile;
    byId("energy-rate").value = String(profile.ratePerKwh);
    byId("energy-country").value = profile.countryCode;
    byId("energy-currency").value = profile.currency;
    const regionText = profile.subdivisionCode ? ` · ${profile.subdivisionCode}` : "";
    byId("energy-rate-help").textContent = `${profile.sourceName} · ${profile.countryCode}${regionText} · ${profile.effectivePeriod} · ${profile.taxScope}. Estimate only.`;
  } catch (error) {
    state.electricityRateProfile = null;
    byId("energy-rate").value = "";
    const message = error.message === "electricity-rate-api-key-unavailable"
      ? "The U.S. government-price lookup is not configured. Use the rate from your bill, or configure an EIA API key before starting Haven 42."
      : "Haven 42 could not retrieve that official average. Check the country and currency, or use the rate from your bill.";
    byId("energy-rate-help").textContent = message;
  } finally {
    button.disabled = false;
    button.textContent = "Get selected official average";
  }
}

function calculateElectricityEstimate(event) {
  event.preventDefault();
  const watts = energyNumber("energy-average-watts", 0.001, 2000);
  const hours = energyNumber("energy-hours-per-day", 0, 24);
  const days = energyNumber("energy-billing-days", 1, 366);
  const rate = energyNumber("energy-rate", 0, 10000000);
  const country = byId("energy-country").value.trim().toUpperCase();
  const currency = byId("energy-currency").value.trim().toUpperCase();
  const result = byId("energy-estimate-result");
  const countryValid = /^[A-Z]{2}$/.test(country);
  const currencyValid = /^[A-Z]{3}$/.test(currency);
  const daysValid = days !== null && Number.isInteger(days);
  byId("energy-country").toggleAttribute("aria-invalid", !countryValid);
  byId("energy-currency").toggleAttribute("aria-invalid", !currencyValid);
  byId("energy-billing-days").toggleAttribute("aria-invalid", !daysValid);
  if (watts === null || hours === null || !daysValid || rate === null || !countryValid || !currencyValid) {
    result.classList.remove("hidden");
    byId("energy-estimate-cost").textContent = "Check the highlighted estimate fields.";
    byId("energy-estimate-usage").textContent = "Choose a country and use the three-letter currency shown on your bill.";
    byId("energy-estimate-source").textContent = "No estimate was calculated.";
    return;
  }
  const kwh = watts / 1000 * hours * Math.trunc(days);
  const cost = kwh * rate;
  const profile = state.electricityRateProfile;
  const source = profile
    ? `${profile.sourceName} · ${profile.effectivePeriod}`
    : `Rate entered from your bill · ${country}`;
  const formattedCost = `${cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}`;
  const formattedKwh = `${kwh.toFixed(3)} kWh`;
  byId("energy-estimate-cost").textContent = formattedCost;
  byId("energy-estimate-usage").textContent = `${formattedKwh} of graphics-card energy over ${Math.trunc(days)} days`;
  byId("energy-estimate-source").textContent = `${source} · ${rate} ${currency}/kWh`;
  result.classList.remove("hidden");
  state.energyEstimate = Object.freeze({ formattedCost, formattedKwh, days: Math.trunc(days) });
  syncEnergyStatusWidget();
}

function syncEnergyStatusWidget() {
  const widget = byId("status-energy-widget");
  const pinned = byId("energy-pin-status").checked;
  const estimate = state.energyEstimate;
  widget.classList.toggle("hidden", !pinned || !estimate);
  if (pinned && estimate) {
    byId("status-energy-kwh").textContent = estimate.formattedKwh;
    byId("status-energy-cost").textContent = estimate.formattedCost;
    byId("status-energy-period").textContent = `${estimate.days} days · GPU only · current session`;
    byId("energy-pin-help").textContent = "Pinned in the status sidebar for this session. The values are not saved.";
  } else if (pinned) {
    byId("energy-pin-help").textContent = "Pinned after you calculate an estimate. The values are not saved.";
  } else {
    byId("energy-pin-help").textContent = "The widget stays visible while Haven 42 is open. Its values are not saved and disappear when the app closes.";
  }
}

function openSystem() {
  showPrimaryPanel("system-panel", "system-nav", "system-workspace-title");
  void refreshDiagnosticsQuietly();
}

function openChat() {
  showPrimaryPanel("text-panel", "home-nav", "capability-title");
  byId("prompt").focus({ preventScroll: true });
}

function syncStatusSidebar() {
  const connected = state.connected === true;
  const status = byId("sidebar-connection-status");
  status.textContent = connected ? "Connected" : "Not connected";
  status.classList.toggle("good", connected);
  byId("sidebar-server-name").textContent = connected
    ? byId("connection-badge").textContent
    : "AI server not connected";
  const model = selectedModel(state.capabilityId);
  byId("sidebar-model-name").textContent = model
    ? `Model · ${model}`
    : "No model selected";
  byId("sidebar-cpu").textContent = byId("alpha-cpu").textContent;
  byId("sidebar-ram").textContent = byId("alpha-ram").textContent;
  byId("sidebar-gpu").textContent = byId("alpha-gpu").textContent;
  byId("sidebar-speed").textContent = byId("alpha-speed").textContent;
}

function initializeStatusSidebar() {
  const observer = new MutationObserver(syncStatusSidebar);
  for (const id of [
    "connection-badge", "model-state", "alpha-cpu", "alpha-ram", "alpha-gpu", "alpha-speed",
  ]) observer.observe(byId(id), { attributes: true, childList: true, characterData: true, subtree: true });
  byId("model").addEventListener("change", syncStatusSidebar);
  syncStatusSidebar();
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
  void loadHardwareMatchedModels();
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

async function maintainBrowserLifecycle() {
  while (state.token) {
    try {
      const response = await fetch("/api/browser-lifecycle", {
        credentials: "same-origin",
        cache: "no-store",
        headers: {
          "X-Haven-Token": state.token,
          "X-Haven-Browser-Session": state.browserSessionId,
        },
      });
      if (!response.ok || !response.body) return;
      const reader = response.body.getReader();
      while (state.token) {
        const chunk = await reader.read();
        if (chunk.done) break;
      }
    } catch (_error) {
      // A short loopback interruption is retried within the server's close grace period.
    }
    if (state.token) await new Promise((resolve) => window.setTimeout(resolve, 500));
  }
}

function humanError(error) {
  const messages = {
    "provider-host-must-be-ip-literal": "Enter the numeric address shown in your AI server or router settings. Names such as my-server are not accepted.",
    "loopback-provider-required": "Enter 127.0.0.1 for an Ollama server running on this computer.",
    "trusted-lan-provider-required": "That address is outside your private home or office network, so Haven 42 blocked it.",
    "invalid-provider-authentication-mode": "Choose one of the supported Ollama authentication methods.",
    "invalid-provider-api-key": "Check the API key. It cannot contain spaces or line breaks.",
    "unexpected-provider-api-key": "Remove the API key or choose an authentication method.",
    "authenticated-provider-requires-https": "API keys require an HTTPS Ollama address when connecting across a private network.",
    "ollama-connection-failed": "Haven 42 could not reach Ollama at that address.",
    "ollama-chat-failed": "Ollama did not complete the text request.",
    "text-request-cancelled": "Generation stopped. Your message was restored so you can edit or try again.",
    "text-request-already-running": "Wait for the current response to stop before sending another message.",
    "empty-model-response": "The model returned an empty response.",
    "capability-not-admitted": "That capability is not available in this Haven 42 release.",
    "explicit-online-search-consent-required": "Use “Search public catalog” to explicitly start an online search.",
    "invalid-model-search-query": "Enter a short model name using letters, numbers, spaces, dots, dashes, underscores, or colons.",
    "model-catalog-search-failed": "The public Ollama catalog could not be reached.",
    "invalid-model-catalog-response": "The public catalog returned an invalid response, so Haven 42 rejected it.",
    "model-install-provider-required": "Connect your Ollama server before installing a model.",
    "model-install-candidate-expired": "Search for that model again before installing it.",
    "model-incompatible-with-hardware": "This model is known not to fit this computer, so Haven 42 did not start the download.",
    "model-install-approval-invalid": "That one-time model approval expired or was already used. Review the download again.",
    "ollama-model-install-failed": "Ollama could not finish downloading this model. Existing model data was left in place so you can try again.",
    "ollama-model-install-verification-failed": "Ollama finished the request but did not list the model afterward, so Haven 42 did not select it.",
    "invalid-model-install-preparation": "Haven 42 could not verify the model-download review, so nothing was downloaded.",
    "invalid-model-install-result": "Haven 42 could not verify the completed model download, so it was not selected.",
    "research-query-size": "Enter between 1 and 256 characters to research.",
    "research-query-active-content": "Remove markup or control characters from the research words.",
    "research-query-credential-like": "Remove passwords, tokens, or API-key-like text before researching.",
    "research-approval-invalid": "That one-time approval expired or was already used. Review the request again.",
    "research-selection-invalid": "That result is no longer available in memory. Run the search again.",
    "research-provider-transport-failed": "The selected research source could not be reached securely. Nothing was saved; try again later.",
    "research-page-provider-transport-failed": "The approved Wikipedia page could not be reached securely. Nothing was saved.",
    "research-provider-response-invalid": "The selected research source returned an unexpected response, so Haven 42 rejected it.",
    "research-api-key-invalid": "Enter a valid Brave Search API key. It stays in memory and is never saved.",
    "research-query-invalid": "Enter plain search words without markup or control characters.",
    "research-model-not-available": "Connect Ollama and choose an installed chat model before requesting a cited web answer.",
    "research-search-provider-http-401": "Brave rejected the search key. Check the key and try again.",
    "research-search-provider-http-403": "This Brave search key is not allowed to run that request.",
    "research-search-provider-http-429": "The web search provider is temporarily rate-limiting requests. Try again later.",
    "research-search-provider-transport-failed": "The web search provider could not be reached securely. Nothing was saved.",
    "research-search-provider-no-results": "No usable public results were returned. Try different search words.",
    "research-synthesis-failed": "The local AI could not prepare a cited answer. The approved source text was discarded.",
    "research-synthesis-invalid": "The local AI returned an answer without valid source citations, so Haven 42 rejected it.",
    "research-review-unavailable": "Close the open setup, help, or review window before starting web research.",
    "invalid-research-preparation": "Haven 42 could not verify the research approval request, so nothing was sent.",
    "invalid-research-query-result": "Haven 42 rejected an unexpected research result. Nothing was saved.",
    "invalid-research-page-result": "Haven 42 rejected unexpected page content. Nothing was saved.",
    "invalid-research-web-result": "Haven 42 could not verify the approved web-search destination, so it did not open it.",
    "private-context-confirmation-required": "Confirm that the attached content may be sent to your private-network Ollama server.",
    "invalid-context-file-count": "Attach no more than five text files.",
    "invalid-context-file-name": "A selected filename is not supported.",
    "invalid-context-file-type": "That file type isn't supported yet. Choose a text, CSV, JSON, source code, or PNG file.",
    "invalid-context-file-content": "A selected file is empty or is not supported text.",
    "context-file-content-type-mismatch": "This file's contents do not match its name. For safety, attach the original supported text, source-code, CSV, JSON, or PNG file.",
    "invalid-context-json": "The selected JSON file is malformed.",
    "context-json-too-complex": "That JSON file is too deeply nested or complex for this version of Haven 42.",
    "invalid-context-csv": "The selected CSV file is malformed.",
    "context-csv-too-complex": "That CSV file has too many rows or columns, or contains a cell that is too large.",
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
    "managed-components-removal-confirmation-required": "Confirm removal before deleting managed components.",
    "setup-already-running": "Wait for setup to finish or cancel it before removing components.",
    "model-download-failed": "The model download was interrupted. Check your internet connection, then retry. Haven 42 will keep verified files and request permission before continuing.",
    "managed-provider-request-failed": "The local AI engine stopped responding. Try again. Haven 42 will keep verified files and request permission before continuing.",
    "managed-provider-start-timeout": "The local AI engine did not start within 2 minutes. Your downloaded files were kept. Use View troubleshooting logs for more details.",
    "managed-provider-exited-before-ready": "The local AI engine closed before it was ready. Your downloaded files were kept. Use View troubleshooting logs for more details.",
    "managed-provider-exited-during-validation": "The model downloaded, but the local AI engine closed during its private test. Your model was kept for retry.",
    "macos-ollama-approval-does-not-match-plan": "This setup review is no longer current. Check this computer again before approving startup.",
    "invalid-macos-ollama-approval": "That one-time approval expired or was already used. Review the startup effects again.",
    "macos-ollama-version-changed-after-approval": "The installed Ollama version changed after the review. Check this computer again before continuing.",
    "macos-ollama-private-port-unavailable": "Haven 42 could not reserve its private local-AI connection. Close another Haven 42 session and try again.",
    "macos-ollama-process-exited": "Ollama closed before its private local-AI connection was ready.",
    "macos-ollama-start-timeout": "Ollama did not start within 20 seconds. Nothing was installed or downloaded.",
    "macos-ollama-signature-unverified": "macOS could not verify the installed Ollama app, so Haven 42 did not start it.",
    "macos-ollama-publisher-unverified": "The installed Ollama app is not signed by the expected publisher, so Haven 42 did not start it.",
    "macos-ollama-gatekeeper-unverified": "Gatekeeper did not approve the installed Ollama app, so Haven 42 did not start it.",
    "invalid-macos-installed-ollama-result": "Haven 42 could not verify the completed local-AI startup, so it stopped safely.",
    "managed-inference-request-failed": "The model downloaded, but the local AI engine stopped responding during its private test. Your model was kept for retry.",
    "managed-inference-request-rejected": "The model downloaded, but the local AI engine could not load or test it on this computer. Your model was kept for troubleshooting.",
    "managed-inference-response-invalid": "The model downloaded, but its private test returned an unexpected result. Your model was kept for troubleshooting.",
    "managed-model-status-request-failed": "The private model test finished, but Haven 42 could not confirm that the model stayed loaded.",
    "managed-model-status-request-rejected": "The local AI engine would not report the loaded model after its private test.",
    "managed-model-status-response-invalid": "The local AI engine returned an unexpected model status after its private test.",
    "managed-inference-validation-failed": "The model downloaded, but it did not complete Haven 42's private test correctly.",
    "managed-model-not-loaded": "The private test finished, but the selected model was no longer loaded.",
    "managed-accelerator-not-active": "The private test did not use the required graphics hardware, so Haven 42 stopped safely.",
    "insufficient-managed-storage": "There is not enough free space in this Haven 42 folder to complete local setup.",
    "component-integrity-mismatch": "A downloaded component did not pass its safety check. Haven 42 did not use it.",
    "unowned-portable-data-root": "Haven 42 found a data folder it did not create, so it left the folder unchanged.",
    "unsafe-portable-data-entry": "Haven 42 found an unexpected linked file or folder, so it safely stopped removal.",
    "portable-data-removal-failed": "Haven could not completely remove its managed data. No other location was touched.",
    "diagnostic-report-save-failed": "Haven 42 could not safely create the support report. No report was uploaded.",
    "answer-report-save-failed": "Haven 42 could not safely create the answer report. The question and answer were not recorded or uploaded.",
    "diagnostic-clear-failed": "Haven 42 could not safely clear the troubleshooting events.",
    "diagnostic-removal-failed": "Haven 42 found an unexpected item in the log folder, so it left the folder unchanged.",
  };
  if (typeof error.message === "string" && error.message.startsWith("research-")) {
    return "The research source returned information Haven 42 could not safely verify. Nothing was saved. Try again, or open the troubleshooting logs below.";
  }
  return messages[error.message] || "Haven 42 safely stopped this request because it could not verify it. Open troubleshooting logs for more details.";
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
    authMode: byId(`${prefix}auth-mode`).value,
    apiKey: byId(`${prefix}api-key`).value,
  };
}

function providerConfigChanged(config) {
  return !state.providerConfig
    || config.endpoint !== state.providerConfig.endpoint
    || config.timeoutSeconds !== state.providerConfig.timeoutSeconds
    || config.idleUnloadSeconds !== state.providerConfig.idleUnloadSeconds
    || config.authMode !== state.providerConfig.authMode
    || config.apiKey.length > 0;
}

function setPasswordVisibility(inputId, buttonId, visible) {
  const input = byId(inputId);
  const button = byId(buttonId);
  input.type = visible ? "text" : "password";
  button.setAttribute("aria-pressed", String(visible));
  button.textContent = visible ? "Hide" : "Show";
  button.setAttribute("aria-label", `${visible ? "Hide" : "Show"} API key`);
}

function togglePasswordVisibility(inputId, buttonId) {
  const button = byId(buttonId);
  setPasswordVisibility(inputId, buttonId, button.getAttribute("aria-pressed") !== "true");
}

function updateProviderAuthenticationControl(prefix = "") {
  const mode = byId(`${prefix}auth-mode`).value;
  const key = byId(`${prefix}api-key`);
  const visibility = byId(`${prefix}api-key-visibility`);
  const endpoint = byId(`${prefix}endpoint`).value.trim();
  const canReuse = state.connected
    && state.providerConfig?.endpoint === endpoint
    && state.providerConfig?.authMode === mode;
  key.disabled = mode === "none";
  visibility.disabled = key.disabled;
  key.required = mode !== "none" && !canReuse;
  key.placeholder = mode === "none"
    ? "Not used"
    : canReuse
      ? "Current session key retained"
      : "Required";
  if (mode === "none") {
    key.value = "";
    setPasswordVisibility(`${prefix}api-key`, `${prefix}api-key-visibility`, false);
  }
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
        "hardwareFitReason", "licenseStatus", "minimumSystemMemoryGiB", "name",
        "source", "status", "validationStatus",
      ].sort().join(",")
      || !/^[A-Za-z0-9][A-Za-z0-9._/:+-]{0,255}$/.test(item.name)
      || names.has(item.name)
      || item.source !== "ollama-public-catalog"
      || !["installed", "not-installed"].includes(item.status)
      || item.validationStatus !== "candidate-only"
      || item.capabilityEvidence !== "unverified"
      || !["unknown", "compatible", "incompatible"].includes(item.hardwareFit)
      || ![null, "insufficient-system-memory", "reviewed-memory-limit-satisfied"].includes(item.hardwareFitReason)
      || !(item.minimumSystemMemoryGiB === null
        || (Number.isInteger(item.minimumSystemMemoryGiB) && item.minimumSystemMemoryGiB >= 4))
      || (item.hardwareFit === "incompatible" && item.hardwareFitReason !== "insufficient-system-memory")
      || item.licenseStatus !== "review-required"
      || item.executionAllowed !== installed
      || item.installCommand !== (installed ? null : `ollama pull ${item.name}`)
    ) throw new Error("invalid-model-catalog-response");
    names.add(item.name);
  });
  return result;
}

function chooseDiscoveredModel(item) {
  resetModelInstallProgress();
  const capabilityId = byId("model-search-capability").value;
  if (item.status === "installed") {
    assignModelToSupportedCapabilities(
      state.modelOptions.find((option) => option.name === item.name),
      capabilityId,
    );
    state.desiredModel = null;
    if (capabilityId === state.capabilityId) renderModelSelect();
    byId("model-choice-status").textContent = `${item.name} selected for ${CAPABILITIES[capabilityId].modelLabel.toLocaleLowerCase()}.`;
  } else {
    state.desiredModel = item;
    byId("model-choice-status").textContent = `${item.name} is not installed yet. Review the download below when you are ready.`;
  }
  renderModelDiscovery();
  if (item.status !== "installed") {
    window.setTimeout(() => {
      const review = byId("desired-model");
      review.scrollIntoView({ behavior: motionBehavior(), block: "center" });
      byId("install-model-button").focus({ preventScroll: true });
    }, 0);
  }
}

function assignModelToSupportedCapabilities(modelOption, fallbackCapabilityId = state.capabilityId) {
  if (!modelOption || typeof modelOption.name !== "string") return;
  const supported = Object.entries(modelOption.capabilityStatus || {})
    .map(([capabilityId]) => capabilityId)
    .filter((capabilityId) => Object.hasOwn(CAPABILITIES, capabilityId));
  const targets = supported.length > 0 ? supported : [fallbackCapabilityId];
  targets.forEach((capabilityId) => {
    state.modelSelections[capabilityId] = { mode: "manual", model: modelOption.name };
  });
}

function closeModelInstallReview(preserveSetupReturn = false) {
  byId("model-install-review-layer").classList.add("hidden");
  byId("model-install-review-layer").setAttribute("aria-hidden", "true");
  document.querySelector(".shell").inert = false;
  if (!preserveSetupReturn) state.modelInstallReturnToChat = false;
  const target = state.pendingModelInstall?.returnFocus;
  state.pendingModelInstall = null;
  byId("install-model-button").disabled = false;
  if (!byId("model-install-status").textContent.includes("Downloading")) {
    byId("model-install-status").textContent = "Nothing was downloaded. You can review this model again when you are ready.";
  }
  if (target instanceof HTMLElement && target.isConnected) target.focus({ preventScroll: true });
}

function validateModelInstallPreparation(result, expectedModel) {
  const fields = [
    "approvalToken", "destination", "downloadStarted", "expiresInSeconds", "hardwareFit",
    "hardwareFitReason", "kind", "licenseStatus", "minimumSystemMemoryGiB", "model",
    "persisted", "schemaVersion", "singleUse",
  ];
  if (
    !hasExactObjectKeys(result, fields)
    || result.schemaVersion !== 1
    || result.kind !== "model-install-approval"
    || result.model !== expectedModel
    || !/^[0-9a-f]{32}$/u.test(result.approvalToken)
    || result.expiresInSeconds !== 300
    || result.singleUse !== true
    || result.persisted !== false
    || result.downloadStarted !== false
    || result.licenseStatus !== "review-required"
    || !["unknown", "compatible"].includes(result.hardwareFit)
    || ![null, "reviewed-memory-limit-satisfied", "matched-tested-hardware-profile"].includes(result.hardwareFitReason)
    || !(result.minimumSystemMemoryGiB === null
      || (Number.isInteger(result.minimumSystemMemoryGiB) && result.minimumSystemMemoryGiB >= 4))
    || !["This computer", "Your connected private AI server"].includes(result.destination)
  ) throw new Error("invalid-model-install-preparation");
  return result;
}

function resetModelInstallProgress() {
  const region = byId("model-install-progress");
  const bar = byId("model-install-progress-bar");
  region.classList.add("hidden");
  region.removeAttribute("data-state");
  bar.value = 0;
  bar.textContent = "0%";
  byId("model-install-progress-percent").textContent = "0%";
  byId("model-install-progress-detail").textContent = "Starting download…";
}

function validateModelInstallProgress(result, expectedModel) {
  const fields = [
    "completedBytes", "kind", "model", "phase", "progressPercent",
    "schemaVersion", "status", "terminal", "totalBytes",
  ];
  if (
    !hasExactObjectKeys(result, fields)
    || result.schemaVersion !== 1
    || result.kind !== "model-install-progress"
    || result.model !== expectedModel
    || !["downloading", "verifying", "complete", "failed"].includes(result.phase)
    || typeOfNumber(result.progressPercent) !== "integer"
    || result.progressPercent < 0
    || result.progressPercent > 100
    || ![null, "integer"].includes(typeOfNumber(result.completedBytes))
    || ![null, "integer"].includes(typeOfNumber(result.totalBytes))
    || (result.completedBytes === null) !== (result.totalBytes === null)
    || (result.completedBytes !== null && result.completedBytes < 0)
    || (result.totalBytes !== null && result.totalBytes <= 0)
    || (result.totalBytes !== null && result.completedBytes > result.totalBytes)
    || typeof result.status !== "string"
    || result.status.length < 1
    || result.status.length > 160
    || typeof result.terminal !== "boolean"
    || result.terminal !== ["complete", "failed"].includes(result.phase)
  ) throw new Error("invalid-model-install-progress");
  return result;
}

function typeOfNumber(value) {
  if (value === null) return null;
  return typeof value === "number" && Number.isInteger(value) ? "integer" : typeof value;
}

function renderModelInstallProgress(progress) {
  const region = byId("model-install-progress");
  const bar = byId("model-install-progress-bar");
  const percent = `${progress.progressPercent}%`;
  const labels = {
    downloading: "Downloading model",
    verifying: "Verifying model",
    complete: "Model ready",
    failed: "Download stopped",
  };
  region.classList.remove("hidden");
  region.dataset.state = progress.phase;
  byId("model-install-progress-label").textContent = labels[progress.phase];
  byId("model-install-progress-percent").textContent = percent;
  bar.value = progress.progressPercent;
  bar.textContent = percent;
  const transferred = progress.totalBytes === null
    ? ""
    : ` · ${formatSetupBytes(progress.completedBytes)} of ${formatSetupBytes(progress.totalBytes)}`;
  byId("model-install-progress-detail").textContent = `${progress.status}${transferred}`;
}

async function monitorModelInstallProgress(progressToken, model) {
  for (let attempt = 0; attempt < 7200; attempt += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, attempt === 0 ? 100 : 500));
    try {
      const progress = validateModelInstallProgress(
        await api("/api/model-install/status", { progressToken }),
        model,
      );
      renderModelInstallProgress(progress);
      if (progress.terminal) return progress;
    } catch (error) {
      if (attempt >= 9) throw error;
    }
  }
  throw new Error("model-install-progress-timeout");
}

async function prepareModelInstall() {
  const model = state.desiredModel?.name;
  if (!model) return false;
  const button = byId("install-model-button");
  button.disabled = true;
  byId("model-install-status").textContent = "Preparing the model and destination for review…";
  try {
    const preparation = validateModelInstallPreparation(
      await api("/api/model-install/prepare", { model }),
      model,
    );
    state.pendingModelInstall = { ...preparation, returnFocus: button };
    byId("model-install-review-name").textContent = preparation.model;
    byId("model-install-review-destination").textContent = preparation.destination;
    byId("model-install-review-status").textContent = "Nothing has been downloaded.";
    document.querySelector(".shell").inert = true;
    byId("model-install-review-layer").classList.remove("hidden");
    byId("model-install-review-layer").setAttribute("aria-hidden", "false");
    byId("model-install-review-dialog").focus({ preventScroll: true });
    return true;
  } catch (error) {
    byId("model-install-status").textContent = humanError(error);
    button.disabled = false;
    return false;
  }
}

async function executeModelInstall() {
  const pending = state.pendingModelInstall;
  if (!pending) return;
  const model = pending.model;
  const token = pending.approvalToken;
  closeModelInstallReview(true);
  const button = byId("install-model-button");
  button.disabled = true;
  button.textContent = "Downloading…";
  byId("model-install-status").textContent = `Downloading ${model}. Large models can take several minutes; keep Haven 42 open.`;
  byId("model-install-progress").classList.remove("hidden");
  try {
    const installation = api("/api/model-install/execute", { approvalToken: token, confirmed: true });
    const progressMonitoring = monitorModelInstallProgress(token, model).catch(() => null);
    const result = await installation;
    await progressMonitoring;
    if (
      !result
      || result.schemaVersion !== 1
      || result.kind !== "model-install-result"
      || result.status !== "installed"
      || result.model !== model
      || result.verifiedByProviderCatalog !== true
      || result.selectedAutomatically !== true
      || !result.modelOption
      || result.modelOption.name !== model
      || typeof result.modelOption.digestVerified !== "boolean"
      || !result.modelOption.capabilityStatus
    ) throw new Error("invalid-model-install-result");
    state.modelOptions = [...state.modelOptions.filter((item) => item.name !== model), result.modelOption];
    state.modelSearchResults = state.modelSearchResults.map((item) => (
      item.name === model ? { ...item, status: "installed", executionAllowed: true, installCommand: null } : item
    ));
    const capabilityId = byId("model-search-capability").value;
    assignModelToSupportedCapabilities(result.modelOption, capabilityId);
    state.desiredModel = null;
    renderModelSelect();
    renderModelDiscovery();
    byId("model-choice-status").textContent = `${model} is installed and selected for every supported text task.`;
    byId("model-search-status").textContent = `${model} was downloaded and verified by your Ollama server.`;
    if (state.modelInstallReturnToChat) {
      state.modelInstallReturnToChat = false;
      openChat();
      byId("text-status").textContent = `${model} is installed, selected, and ready.`;
    }
  } catch (error) {
    byId("model-install-status").textContent = humanError(error);
  } finally {
    if (state.desiredModel?.name === model) {
      button.disabled = false;
      button.textContent = "Review and install model";
    }
  }
}

async function offerRecommendedModelDuringSetup() {
  const candidate = state.qualifiedModelCandidates.find((item) => (
    item.recommended === true
    && !state.modelOptions.some((installed) => installed.name === item.name)
  ));
  if (!candidate) return false;
  state.modelInstallReturnToChat = true;
  byId("setup-wizard").classList.add("hidden");
  openModels();
  chooseDiscoveredModel({
    ...candidate,
    status: "not-installed",
    validationStatus: "validated-on-matching-hardware",
    installCommand: `ollama pull ${candidate.name}`,
  });
  const prepared = await prepareModelInstall();
  if (!prepared) state.modelInstallReturnToChat = false;
  return prepared;
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

function validateTestedModelCatalog(result) {
  if (
    !result
    || typeof result !== "object"
    || Array.isArray(result)
    || !hasExactObjectKeys(result, [
      "schemaVersion", "kind", "status", "profile", "runtimeVersion", "options",
    ])
    || result.schemaVersion !== 1
    || result.kind !== "hardware-aware-tested-models"
    || !["exact-profile", "runtime-differs", "no-matching-evidence", "remote-hardware-not-verifiable"].includes(result.status)
    || typeof result.runtimeVersion !== "string"
    || !Array.isArray(result.options)
    || result.options.length > 128
  ) throw new Error("invalid-tested-model-catalog");
  if (["no-matching-evidence", "remote-hardware-not-verifiable"].includes(result.status)) {
    if (result.profile !== null || result.options.length !== 0) throw new Error("invalid-tested-model-catalog");
    return result;
  }
  if (
    !hasExactObjectKeys(result.profile, [
      "id", "hardware", "operatingSystem", "testedRuntimeVersion", "recommendedModel",
    ])
    || Object.values(result.profile).some((value) => typeof value !== "string" || value.length === 0)
  ) throw new Error("invalid-tested-model-catalog");
  const names = new Set();
  result.options.forEach((item) => {
    const installed = item?.status === "installed";
    if (
      !hasExactObjectKeys(item, [
        "name", "status", "validationStatus", "capabilities", "testProfile",
        "testedRuntimeVersion", "currentRuntimeVersion", "evidence", "recommended", "installCommand",
      ])
      || !/^[A-Za-z0-9][A-Za-z0-9._/:+-]{0,255}$/u.test(item.name)
      || names.has(item.name)
      || !["installed", "not-installed"].includes(item.status)
      || !["tested-exact-profile", "tested-hardware-runtime-differs"].includes(item.validationStatus)
      || !Array.isArray(item.capabilities)
      || item.capabilities.some((value) => !Object.hasOwn(CAPABILITIES, value))
      || typeof item.testProfile !== "string"
      || typeof item.testedRuntimeVersion !== "string"
      || item.currentRuntimeVersion !== result.runtimeVersion
      || typeof item.evidence !== "string"
      || typeof item.recommended !== "boolean"
      || item.installCommand !== (installed ? null : `ollama pull ${item.name}`)
    ) throw new Error("invalid-tested-model-catalog");
    names.add(item.name);
  });
  return result;
}

async function loadHardwareMatchedModels() {
  const requestId = ++state.testedModelRequestId;
  state.testedModelOptions = [];
  state.testedModelCatalog = null;
  if (!state.connected) {
    renderModelDiscovery();
    return;
  }
  byId("model-search-status").textContent = "Checking qualification evidence for this AI computer…";
  try {
    const result = validateTestedModelCatalog(await api("/api/models/tested", {}));
    if (requestId !== state.testedModelRequestId) return;
    state.testedModelCatalog = result;
    state.testedModelOptions = result.options;
    const recommended = result.options.find((item) => item.recommended && item.status === "not-installed");
    if (recommended && !state.desiredModel) state.desiredModel = recommended;
    renderModelSelect();
    renderModelDiscovery();
  } catch (error) {
    if (requestId !== state.testedModelRequestId) return;
    state.testedModelCatalog = { status: "check-failed" };
    state.testedModelOptions = [];
    byId("model-search-status").textContent = `Hardware-aware model check stopped safely. ${humanError(error)}`;
    renderModelDiscovery();
  }
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
  state.testedModelOptions.forEach((item) => {
    if (!modelMatchesQuery(item.name, query)) return;
    const existing = merged.get(item.name);
    merged.set(item.name, existing ? { ...existing, ...item, status: "installed", installCommand: null } : item);
  });
  state.qualifiedModelCandidates.forEach((item) => {
    if (modelMatchesQuery(item.name, query) && !merged.has(item.name)) {
      merged.set(item.name, {
        ...item,
        status: "not-installed",
        validationStatus: "validated-on-matching-hardware",
        installCommand: `ollama pull ${item.name}`,
      });
    }
  });
  state.modelSearchResults.forEach((item) => {
    if (modelMatchesQuery(item.name, query) && !merged.has(item.name)) merged.set(item.name, item);
  });
  const validationPriority = {
    recommended: 0,
    "tested-exact-profile": 1,
    compatible: 2,
    "tested-hardware-runtime-differs": 3,
    unverified: 4,
    "candidate-only": 5,
    validated: 0,
    "validated-on-matching-hardware": 1,
  };
  const configuredModel = selectedModel(capabilityId);
  const results = [...merged.values()].sort((left, right) => {
    const leftConfigured = left.status === "installed" && left.name === configuredModel;
    const rightConfigured = right.status === "installed" && right.name === configuredModel;
    if (leftConfigured !== rightConfigured) return leftConfigured ? -1 : 1;
    if (Boolean(left.recommended) !== Boolean(right.recommended)) return left.recommended ? -1 : 1;
    if (left.status !== right.status) return left.status === "installed" ? -1 : 1;
    const validationDifference = (validationPriority[left.validationStatus] ?? 3)
      - (validationPriority[right.validationStatus] ?? 3);
    return validationDifference || left.name.localeCompare(right.name);
  });
  const container = byId("model-search-results");
  const desired = byId("desired-model");
  container.replaceChildren();
  results.forEach((item) => {
    const row = document.createElement("div");
    row.className = "model-search-result";
    const detail = document.createElement("div");
    const name = document.createElement("strong");
    name.textContent = item.name;
    const status = document.createElement("small");
    const configured = item.status === "installed" && selectedModel(capabilityId) === item.name;
    const knownIncompatible = item.status !== "installed" && item.hardwareFit === "incompatible";
    const evidenceLabel = item.validationStatus === "tested-exact-profile"
      ? "tested on this hardware, operating system, and Ollama version"
      : item.validationStatus === "tested-hardware-runtime-differs"
        ? `tested on this hardware with Ollama ${item.testedRuntimeVersion}; connected server uses ${item.currentRuntimeVersion}`
        : null;
    const recommendationLabel = item.recommended ? "Recommended for this computer · " : "";
    status.textContent = knownIncompatible
      ? `Cannot run on this computer · needs at least ${item.minimumSystemMemoryGiB} GiB total memory · download blocked`
      : item.status === "installed"
      ? `${recommendationLabel}Already available on your server${configured ? " · selected" : ""}${evidenceLabel ? ` · ${evidenceLabel}` : ""}`
      : evidenceLabel
        ? `${recommendationLabel}Not installed · ${evidenceLabel}`
      : item.validationStatus === "validated-on-matching-hardware"
        ? `${recommendationLabel}Tested on matching hardware · not installed · nothing downloads without approval`
        : "Not tested on this computer · you can still review and install it · nothing downloads without approval";
    detail.append(name, status);
    const choose = document.createElement("button");
    choose.className = "button secondary";
    choose.type = "button";
    const capabilityLabel = CAPABILITIES[capabilityId].modelLabel.replace(" model", "");
    choose.textContent = configured
      ? "Selected"
      : item.status === "installed"
        ? `Use for ${capabilityLabel}`
        : "Review and install";
    choose.setAttribute("aria-label", `${choose.textContent} ${item.name}`);
    choose.disabled = configured || knownIncompatible;
    choose.addEventListener("click", () => chooseDiscoveredModel(item));
    row.append(detail, choose);
    container.append(row);
    if (state.desiredModel?.name === item.name) container.append(desired);
  });
  const testedCatalog = state.testedModelCatalog;
  const publicMatches = state.modelSearchResults.filter((item) => modelMatchesQuery(item.name, query)).length;
  if (publicMatches > 0) {
    // Preserve the explicit public-search result message, including its no-download disclosure.
  } else if (testedCatalog?.status === "remote-hardware-not-verifiable") {
    byId("model-search-status").textContent = "This connected AI server does not report enough hardware information for Haven 42 to match a tested profile. Installed models remain available, and you can search the public catalog.";
  } else if (testedCatalog?.status === "no-matching-evidence") {
    byId("model-search-status").textContent = "No matching qualification profile exists for this AI computer yet. Installed models remain available without a hardware-tested label.";
  } else if (["exact-profile", "runtime-differs"].includes(testedCatalog?.status)) {
    const count = state.testedModelOptions.length;
    const runtimeNote = testedCatalog.status === "runtime-differs"
      ? ` The evidence used Ollama ${testedCatalog.profile.testedRuntimeVersion}; this server uses ${testedCatalog.runtimeVersion}.`
      : "";
    byId("model-search-status").textContent = `${count} tested choice${count === 1 ? "" : "s"} match ${testedCatalog.profile.hardware} on ${testedCatalog.profile.operatingSystem}.${runtimeNote}`;
  } else if (results.length === 0 && !byId("model-search-status").textContent.includes("Searching")) {
    byId("model-search-status").textContent = "No installed or catalog matches yet.";
  } else if (
    installed.length > 0
    || results.some((item) => item.validationStatus === "validated-on-matching-hardware")
  ) {
    const capabilityLabel = CAPABILITIES[capabilityId].modelLabel.replace(" model", "");
    const testedDownloads = results.filter((item) => item.validationStatus === "validated-on-matching-hardware").length;
    byId("model-search-status").textContent = `${installed.length} installed and ${testedDownloads} tested download${testedDownloads === 1 ? "" : "s"} shown for ${capabilityLabel}.`;
  }
  if (desired.parentElement !== container) container.append(desired);
  desired.classList.toggle("hidden", !state.desiredModel);
  if (state.desiredModel) {
    byId("desired-model-name").textContent = state.desiredModel.name;
    byId("desired-model-state").textContent = "Not installed yet · review this model before downloading";
    byId("desired-model-command").textContent = state.desiredModel.installCommand;
  }
}

function showWizardStep(step) {
  const progressStep = ["readiness", "provider"].includes(step) ? "middle" : step;
  byId("setup-wizard").querySelector(".wizard-progress").classList.toggle("hidden", step === "removed");
  document.querySelectorAll("[data-wizard-step]").forEach((panel) => {
    panel.classList.toggle("hidden", panel.dataset.wizardStep !== step);
  });
  document.querySelectorAll("[data-wizard-progress]").forEach((marker) => {
    marker.classList.toggle("active", marker.dataset.wizardProgress === progressStep);
    if (marker.dataset.wizardProgress === progressStep) marker.setAttribute("aria-current", "step");
    else marker.removeAttribute("aria-current");
  });
  const middleMarker = document.querySelector('[data-wizard-progress="middle"]');
  if (middleMarker && progressStep === "middle") {
    middleMarker.setAttribute("aria-label", step === "readiness" ? "Check and set up this computer" : "Connect another AI server");
  }
  const panel = document.querySelector(`[data-wizard-step="${step}"]`);
  const focusTarget = panel.querySelector("input, button, select, summary, [tabindex]");
  (focusTarget || byId("setup-wizard").querySelector(".wizard-card")).focus();
}

function showPostRemovalExperience() {
  state.connected = false;
  state.providerConfig = null;
  state.modelOptions = [];
  state.testedModelRequestId += 1;
  state.testedModelOptions = [];
  state.testedModelCatalog = null;
  state.qualifiedModelCandidates = [];
  state.modelSearchResults = [];
  state.modelSelections = {};
  state.recommendations = {};
  state.desiredModel = null;
  state.activeTextExecution = null;
  setProviderReady(false);
  resetTask();
  renderTextMode();
  updateProviderConnectionControl();
  updateWizardConnectionControl();
  updateCleanupPolicyControl();
  byId("alpha-tokens").textContent = "0";
  byId("alpha-speed").textContent = "Waiting";
  byId("removed-actions").classList.remove("hidden");
  byId("removed-close-status").classList.add("hidden");
  byId("removed-close-status").textContent = "";
  byId("setup-wizard").classList.remove("hidden");
  showWizardStep("removed");
}

function acceleratorDisplayName(vendor, model) {
  const normalizedVendor = String(vendor || "").trim();
  const normalizedModel = String(model || "").trim();
  if (!normalizedVendor) return normalizedModel || "Graphics device";
  if (!normalizedModel) return normalizedVendor;
  return normalizedModel.toLocaleLowerCase().startsWith(normalizedVendor.toLocaleLowerCase())
    ? normalizedModel
    : `${normalizedVendor} ${normalizedModel}`;
}

function readinessFacts(snapshot) {
  const platformName = snapshot.platform.operatingSystem === "macos"
    ? "macOS"
    : snapshot.platform.productName || snapshot.platform.operatingSystem;
  const platformBuild = Number.isSafeInteger(snapshot.platform.buildNumber)
    ? ` · build ${snapshot.platform.buildNumber}`
    : "";
  const memory = snapshot.platform.systemMemoryGiB == null
    ? "Unknown"
    : `${snapshot.platform.systemMemoryGiB} GiB`;
  const accelerator = snapshot.accelerators.length
    ? snapshot.accelerators.map((item) => {
      const driver = item.driverName
        ? `${item.driverName} · version ${item.driverVersion || "Unavailable"}`
        : item.driverVersion || "Unavailable";
      return `${acceleratorDisplayName(item.vendor, item.model)} · ${item.memoryGiB ? `${item.memoryGiB} GiB` : "graphics memory Unavailable"} · driver ${driver}`;
    }).join(", ")
    : "Not detected or permission limited";
  const softwareLabels = {
    python: "Embedded Python runtime",
    ollama: "System Ollama",
    "nvidia-runtime": "NVIDIA tools",
    "amd-runtime": "AMD graphics tools",
    "intel-runtime": "Intel graphics tools",
  };
  const detectedVendors = snapshot.accelerators.map((item) => (
    `${item.vendor || ""} ${item.model || ""}`.toLocaleLowerCase()
  ));
  const relevantSoftware = (componentId) => {
    if (["python", "ollama"].includes(componentId)) return true;
    if (componentId === "nvidia-runtime") {
      return detectedVendors.some((value) => value.includes("nvidia"));
    }
    if (componentId === "amd-runtime") {
      return detectedVendors.some((value) => (
        value.includes("amd") || value.includes("advanced micro devices")
      ));
    }
    if (componentId === "intel-runtime") {
      return detectedVendors.some((value) => value.includes("intel"));
    }
    return false;
  };
  const software = snapshot.software
    .filter((item) => (
      Object.hasOwn(softwareLabels, item.componentId)
      && relevantSoftware(item.componentId)
    ))
    .map((item) => [
      softwareLabels[item.componentId],
      item.version ? `${item.state} · ${item.version}` : item.state,
    ]);
  const processor = Number.isSafeInteger(snapshot.platform.logicalProcessors)
    ? `${snapshot.platform.logicalProcessors} logical processors`
    : "Unavailable";
  const storage = snapshot.platform.availableStorageGiB == null
    ? "Unavailable"
    : `${snapshot.platform.availableStorageGiB} GiB free beside Haven 42`;
  const linuxDetails = snapshot.platform.operatingSystem === "linux"
    ? [
      ["Linux kernel", snapshot.platform.kernelVersion || "Unavailable"],
      ["Desktop session", `${snapshot.platform.desktopEnvironmentReported || "Unavailable"} · ${snapshot.platform.sessionTypeReported || "session type Unavailable"}`],
      ["Linux compatibility", snapshot.platform.libcFamily && snapshot.platform.libcVersion
        ? `${snapshot.platform.libcFamily} ${snapshot.platform.libcVersion}`
        : "Unavailable"],
    ]
    : [];
  const macDetails = snapshot.platform.operatingSystem === "macos"
    ? [["Mac model", snapshot.platform.productName || "Unavailable"]]
    : [];
  return [
    ["Operating system", `${platformName}${platformBuild} · ${snapshot.platform.architecture}`],
    ...macDetails,
    ["Processor", processor],
    ["Memory", memory],
    ["Available space", storage],
    ["Accelerator", accelerator],
    ...linuxDetails,
    ...software,
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

function safeProblemReportValue(value, fallback = "Not available", maximumLength = 160) {
  const text = String(value ?? "")
    .replace(/[\u0000-\u001f\u007f]/g, " ")
    .replace(/[@<>]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  return text ? text.slice(0, maximumLength) : fallback;
}

function problemReportDetails(snapshot) {
  const platformName = safeProblemReportValue(
    snapshot.platform.productName || snapshot.platform.operatingSystem,
  );
  const platformBuild = Number.isSafeInteger(snapshot.platform.buildNumber)
    ? ` build ${snapshot.platform.buildNumber}`
    : "";
  const memory = snapshot.platform.systemMemoryGiB == null
    ? "Not available"
    : `${snapshot.platform.systemMemoryGiB} GiB`;
  const graphics = snapshot.accelerators.length
    ? snapshot.accelerators.slice(0, 4).map((item) => (
      `${safeProblemReportValue(acceleratorDisplayName(item.vendor, item.model), "Unknown graphics device", 160)}${item.memoryGiB ? ` (${item.memoryGiB} GiB)` : ""}${item.driverVersion ? `, driver ${safeProblemReportValue(item.driverVersion, "", 80)}` : ""}`
    )).join("; ")
    : "Not detected or permission limited";
  return [
    `Haven 42: ${safeProblemReportValue(state.appVersion, "Unknown", 40)}`,
    `Operating system: ${platformName}${platformBuild} · ${safeProblemReportValue(snapshot.platform.architecture, "Unknown", 40)}`,
    `Memory: ${memory}`,
    `Graphics: ${graphics}`,
    "Privacy: no hostname, username, address, local path, prompt, response, or file name included.",
  ].join("\n");
}

async function prepareProblemReport() {
  const status = byId("problem-report-status");
  status.textContent = "Checking general computer details…";
  try {
    const snapshot = state.readinessSnapshot || await api("/api/readiness", { force: true });
    state.readinessSnapshot = snapshot;
    const details = problemReportDetails(snapshot);
    const field = byId("problem-report-details");
    field.value = details;
    try {
      await navigator.clipboard.writeText(details);
      status.textContent = "Copied. Review the text, open the short form, and paste it into the optional computer-details box.";
    } catch (_error) {
      field.focus();
      field.select();
      status.textContent = "The details are ready. Copy the selected text, then paste it into the optional computer-details box.";
    }
  } catch (error) {
    status.textContent = humanError(error);
  }
}

function validAlphaSetupProgress(status) {
  const states = new Set([
    "pending", "present", "downloading", "verifying", "installing", "ready",
    "validating", "complete", "failed", "cancelled",
  ]);
  if (
    !status || status.schemaVersion !== 1
    || !["windows-alpha-setup-progress", "linux-alpha-setup-progress"].includes(status.kind)
    || !Number.isSafeInteger(status.progressPercent)
    || status.progressPercent < 0 || status.progressPercent > 100
    || typeof status.completedSetupCandidate !== "boolean"
    || !Array.isArray(status.components) || status.components.length > 4
  ) return false;
  const identifiers = new Set();
  for (const item of status.components) {
    if (
      !item || typeof item.componentId !== "string"
      || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(item.componentId)
      || identifiers.has(item.componentId)
      || !["runtime", "model"].includes(item.kind)
      || typeof item.displayName !== "string" || item.displayName.length < 1 || item.displayName.length > 80
      || typeof item.version !== "string" || item.version.length < 1 || item.version.length > 40
      || !(
        (item.technologyName === null && item.technologyVersion === null)
        || (
          typeof item.technologyName === "string" && /^[A-Za-z0-9 .+-]{1,24}$/.test(item.technologyName)
          && typeof item.technologyVersion === "string" && /^[0-9]+(?:\.[0-9]+){0,3}$/.test(item.technologyVersion)
        )
      )
      || typeof item.purpose !== "string" || item.purpose.length < 1 || item.purpose.length > 180
      || !Number.isSafeInteger(item.sizeBytes) || item.sizeBytes < 1
      || !states.has(item.state)
      || !Number.isSafeInteger(item.progressPercent)
      || item.progressPercent < 0 || item.progressPercent > 100
      || !Number.isSafeInteger(item.downloadedBytes)
      || item.downloadedBytes < 0 || item.downloadedBytes > item.sizeBytes
      || !Number.isSafeInteger(item.bytesPerSecond)
      || item.bytesPerSecond < 0 || item.bytesPerSecond > item.sizeBytes * 10
      || !(
        item.etaSeconds === null
        || (Number.isSafeInteger(item.etaSeconds) && item.etaSeconds >= 0 && item.etaSeconds <= 604800)
      )
      || typeof item.progressActive !== "boolean"
    ) return false;
    identifiers.add(item.componentId);
  }
  return true;
}

function formatSetupBytes(value) {
  const gib = value / (1024 ** 3);
  return gib >= 0.1 ? `${gib.toFixed(1)} GiB` : `${Math.ceil(value / (1024 ** 2))} MiB`;
}

function formatSetupRate(value) {
  if (!Number.isSafeInteger(value) || value <= 0) return "Calculating speed";
  if (value >= 1024 ** 2) return `${(value / (1024 ** 2)).toFixed(1)} MiB/s`;
  return `${Math.max(1, Math.round(value / 1024))} KiB/s`;
}

function formatSetupEta(value) {
  if (!Number.isSafeInteger(value) || value < 0) return "Estimating time remaining";
  if (value < 60) return "Less than a minute remaining";
  if (value < 3600) return `About ${Math.ceil(value / 60)} minutes remaining`;
  return `About ${Math.ceil(value / 3600)} hours remaining`;
}

function setupComponentDetails(item) {
  if (item.kind === "model") {
    return {
      why: "Selected to provide private chat, writing, and summaries while fitting this computer's detected memory and graphics capacity.",
      contents: `The files that let the local AI understand and create text, already prepared in ${item.version} format. Haven 42 does not modify this model on your computer.`,
      source: "Ollama model registry",
      technicalName: item.displayName,
    };
  }
  if (item.componentId === "ollama-windows-amd-rocm") {
    return {
      why: "Selected because Haven 42 detected a validated AMD graphics acceleration path.",
      contents: `Portable ROCm ${item.technologyVersion} acceleration libraries from the Ollama ${item.version} AMD support package. This is not a graphics driver.`,
      source: "Official Ollama release on GitHub",
    };
  }
  return {
    why: `Required to run the selected text model locally on this ${state.platformFamily === "linux" ? "Linux" : "Windows"} computer.`,
    contents: `Portable Ollama runtime files. No ${state.platformFamily === "linux" ? "system service" : "Windows service"} or system-wide Ollama installation is created.`,
    source: "Official Ollama release on GitHub",
  };
}

function appendSetupDetail(list, termText, descriptionText) {
  const term = document.createElement("dt");
  term.textContent = termText;
  const description = document.createElement("dd");
  description.textContent = descriptionText;
  list.append(term, description);
}

function renderAlphaSetupProgress(status) {
  const panel = byId("alpha-installation-panel");
  if (!panel) return;
  if (!validAlphaSetupProgress(status)) throw new Error("invalid-managed-setup-status");
  const overall = byId("alpha-installation-overall");
  const overallValue = byId("alpha-installation-overall-value");
  overall.value = status.progressPercent;
  overallValue.textContent = `${status.progressPercent}%`;
  const list = byId("alpha-installation-components");
  const expandedComponentIds = new Set(
    Array.from(list.querySelectorAll(".installation-component-details[open]"))
      .map((details) => details.closest("[data-component-id]")?.dataset.componentId)
      .filter(Boolean),
  );
  list.replaceChildren();
  const stateLabels = {
    pending: "Waiting", present: "Found locally", downloading: "Downloading", verifying: "Verifying integrity",
    installing: "Preparing portable files", ready: "Ready", validating: "Testing locally",
    complete: "Complete", failed: "Stopped", cancelled: "Cancelled",
  };
  for (const item of status.components) {
    const details = setupComponentDetails(item);
    const row = document.createElement("li");
    row.className = `installation-component state-${item.state}`;
    row.dataset.componentId = item.componentId;
    const heading = document.createElement("div");
    heading.className = "installation-component-heading";
    const identityGroup = document.createElement("div");
    identityGroup.className = "installation-component-identity";
    if (["present", "ready", "complete"].includes(item.state)) {
      const installed = document.createElement("span");
      installed.className = "installation-component-check";
      installed.setAttribute("aria-hidden", "true");
      installed.textContent = "✓";
      identityGroup.append(installed);
    }
    const identity = document.createElement("strong");
    identity.textContent = item.kind === "model"
      ? "Local AI model for chat, writing, and summaries"
      : item.technologyName
        ? `${item.displayName} · ${item.technologyName} ${item.technologyVersion}`
        : `${item.displayName} · ${item.version}`;
    const stateLabel = document.createElement("span");
    stateLabel.textContent = item.state === "present"
      ? "Found locally · verification required"
      : `${stateLabels[item.state]} · ${item.progressPercent}%`;
    identityGroup.append(identity);
    heading.append(identityGroup, stateLabel);
    const purpose = document.createElement("p");
    purpose.textContent = item.purpose;
    const selectionReason = document.createElement("p");
    selectionReason.className = "installation-component-reason";
    selectionReason.textContent = details.why;
    const downloadSummary = document.createElement("p");
    downloadSummary.className = "installation-component-download";
    downloadSummary.textContent = item.state === "present"
      ? `Already downloaded locally · original size ${formatSetupBytes(item.sizeBytes)} · source: ${details.source}.`
      : `Download: ${formatSetupBytes(item.sizeBytes)} from ${details.source}.`;
    const liveProgress = document.createElement("p");
    liveProgress.className = "installation-component-live-progress";
    if (item.kind === "model" && item.state === "downloading") {
      liveProgress.textContent = item.downloadedBytes > 0
        ? `${formatSetupBytes(item.downloadedBytes)} of ${formatSetupBytes(item.sizeBytes)} · ${formatSetupRate(item.bytesPerSecond)} · ${formatSetupEta(item.etaSeconds)}`
        : "Waiting for download progress from the local AI engine…";
    } else if (item.kind === "model" && ["failed", "cancelled"].includes(item.state) && item.downloadedBytes > 0) {
      liveProgress.textContent = item.downloadedBytes === item.sizeBytes
        ? "Model download complete. The local test stopped, and the downloaded model was kept for troubleshooting and retry."
        : `Download stopped after ${formatSetupBytes(item.downloadedBytes)}. Existing local download data was kept so Haven 42 can retry safely.`;
    } else {
      liveProgress.classList.add("hidden");
    }
    const information = document.createElement("details");
    information.className = "installation-component-details";
    information.open = expandedComponentIds.has(item.componentId);
    const informationSummary = document.createElement("summary");
    informationSummary.textContent = "Download and safety details";
    const informationList = document.createElement("dl");
    if (details.technicalName) {
      appendSetupDetail(informationList, "Technical model name", details.technicalName);
    }
    appendSetupDetail(informationList, "Contents", details.contents);
    appendSetupDetail(informationList, "Storage", "Haven42-Data inside this extracted Haven 42 folder.");
    appendSetupDetail(informationList, "Verification", "Size, SHA-256 checksum, safe archive paths, and executable signature where applicable are checked before use.");
    appendSetupDetail(informationList, "Removal", "The managed components can be removed from Haven 42 without uninstalling system software.");
    information.append(informationSummary, informationList);
    const progress = document.createElement("progress");
    progress.max = 100;
    progress.value = item.progressPercent;
    progress.setAttribute("aria-label", `${item.displayName} progress`);
    row.append(heading, purpose, selectionReason, downloadSummary, liveProgress, information, progress);
    list.append(row);
  }
}

function updateManagedSetupAvailability(status) {
  const reviewButton = byId("alpha-setup-review");
  const disclosure = byId("alpha-setup-storage-summary");
  const approvalDescription = byId("alpha-setup-approval-description");
  const progress = byId("alpha-setup-progress");
  const cancelButton = byId("alpha-setup-cancel");
  const troubleshootingButton = byId("alpha-setup-troubleshooting");
  if (!reviewButton || !disclosure || !approvalDescription || !progress) return;
  const active = [
    "approved", "downloading", "verifying", "extracting", "starting",
    "model-download", "validating",
  ].includes(status.phase);
  if (cancelButton) {
    cancelButton.hidden = !active;
    cancelButton.disabled = false;
    cancelButton.textContent = status.phase === "model-download" ? "Cancel model download" : "Cancel setup";
  }
  if (troubleshootingButton) {
    troubleshootingButton.hidden = !["failed", "cancelled"].includes(status.phase);
  }
  const reusable = status.completedSetupCandidate === true
    && status.components.length > 0 && status.components.every((item) => (
    ["present", "ready", "complete"].includes(item.state)
  ));
  const interruptedModelDownload = status.phase === "failed"
    && status.error === "model-download-failed"
    && status.components.some((item) => item.kind === "runtime" && ["present", "ready", "complete"].includes(item.state))
    && status.components.some((item) => item.kind === "model" && item.state === "failed");
  const validationErrors = new Set([
    "managed-provider-exited-during-validation",
    "managed-inference-request-failed", "managed-inference-request-rejected",
    "managed-inference-response-invalid", "managed-inference-validation-failed",
    "managed-model-status-request-failed", "managed-model-status-request-rejected",
    "managed-model-status-response-invalid", "managed-model-not-loaded",
    "managed-accelerator-not-active",
  ]);
  const failedValidation = status.phase === "failed" && validationErrors.has(status.error);
  reviewButton.dataset.mode = reusable
    ? "resume"
    : interruptedModelDownload
      ? "retry-download"
      : failedValidation
        ? "retry-validation"
        : "setup";
  reviewButton.textContent = reusable
    ? "Try starting local AI"
    : interruptedModelDownload
      ? "Retry model download"
      : failedValidation
        ? "Retry local AI test"
        : "Review and approve setup";
  const manualButton = byId("alpha-setup-manual");
  if (manualButton) manualButton.hidden = reusable;
  if (reusable) {
    disclosure.textContent = "Your local AI is already installed in Haven42-Data. Haven 42 could not start it automatically, so you can safely try again.";
    progress.textContent = "Trying again will verify and start the existing local AI only. Nothing will be downloaded, installed, or replaced.";
    approvalDescription.textContent = "Allow Haven 42 to verify and start the existing local AI. Nothing will be downloaded, installed, or replaced.";
  } else if (interruptedModelDownload) {
    disclosure.textContent = "The internet connection was lost while downloading the local AI model. The verified local AI engine is still ready.";
    progress.textContent = "Reconnect to the internet, then choose Retry model download. Haven 42 will keep verified files and ask for permission before continuing.";
    approvalDescription.textContent = "Allow Haven 42 to retry only the missing local AI model, keep verified files in Haven42-Data, start the local AI engine, and run a short private test.";
  } else if (failedValidation) {
    disclosure.textContent = "The model is downloaded in Haven42-Data, but the local AI test did not finish successfully.";
    progress.textContent = `${humanError(new Error(status.error))} Retrying will reuse the downloaded model.`;
    approvalDescription.textContent = "Allow Haven 42 to reuse the downloaded model, restart the local AI engine, and repeat its short private test. Nothing will be downloaded or replaced.";
  } else {
    approvalDescription.textContent = "Allow Haven 42 to download any missing items shown above, keep them in Haven42-Data, start the local AI engine, and run a short private test.";
  }
}

async function refreshAlphaSetupProgress() {
  const response = await fetch("/api/alpha/setup-status", {
    credentials: "same-origin", cache: "no-store",
  });
  if (!response.ok) throw new Error("managed-setup-status-failed");
  const status = await response.json();
  renderAlphaSetupProgress(status);
  updateManagedSetupAvailability(status);
  return status;
}

async function openSetupTroubleshooting() {
  byId("setup-wizard").classList.add("hidden");
  openSystem();
  const diagnostics = byId("diagnostics-control");
  diagnostics.open = true;
  await refreshDiagnosticsQuietly();
  diagnostics.scrollIntoView({ block: "start" });
  diagnostics.querySelector("summary")?.focus();
}

async function openTroubleshootingLogs() {
  openSystem();
  const diagnostics = byId("diagnostics-control");
  diagnostics.open = true;
  diagnostics.scrollIntoView({ behavior: motionBehavior(), block: "center" });
  await refreshDiagnosticsQuietly();
  diagnostics.querySelector("summary")?.focus({ preventScroll: true });
}

function linuxSetupRemediation(blockers) {
  const messages = {
    "linux-x64-required": "This Alpha supports 64-bit Intel or AMD Linux computers only.",
    "linux-distribution-not-in-alpha2-matrix": "This Linux distribution has not completed Alpha 2 validation. You can still connect to another AI server.",
    "linux-distribution-version-unavailable": "Haven 42 could not verify the Linux distribution version. Update the operating-system identity files, then check again.",
    "glibc-required": "This portable local AI engine requires a glibc-based Linux distribution.",
    "glibc-version-threshold": "The installed Linux compatibility library is older than the version required by this Alpha. Update the operating system, then check again.",
    "logical-processor-threshold": "This computer needs at least four logical processors for managed local setup.",
    "system-memory-threshold": "This computer needs at least 8 GiB of memory for managed local setup.",
    "storage-threshold": "Free more space beside Haven 42, then run the computer check again.",
    "nvidia-capacity-or-driver-unverified": "Haven 42 could not verify the NVIDIA driver and graphics memory. Use your Linux distribution's driver tools, then check again.",
    "linux-amd-native-evidence-required": "AMD graphics were detected, but managed AMD acceleration on Linux is still being validated for Alpha 2.",
    "linux-intel-native-evidence-required": "Intel graphics were detected, but managed Intel acceleration on Linux is still being validated for Alpha 2.",
    "multiple-accelerators-require-manual-review": "More than one graphics platform was detected. Automatic setup is paused until Haven 42 can choose safely.",
  };
  if (!Array.isArray(blockers)) return [];
  return blockers.filter((item) => Object.hasOwn(messages, item)).map((item) => messages[item]);
}

function renderSetupPlan(plan) {
  const container = byId("wizard-setup-plan");
  container.replaceChildren();
  const heading = document.createElement("strong");
  heading.textContent = "Recommended setup for this computer";
  const summary = document.createElement("p");
  summary.textContent = "Haven 42 checked your computer and prepared the safest setup it can recommend. Review the result below.";
  const fit = document.createElement("p");
  const modelSelection = plan.alphaCandidate?.modelSelection;
  const alphaModel = modelSelection?.selected?.name;
  const automaticAllowed = modelSelection?.automaticExecutionAllowed === true;
  const managed = plan.alphaCandidate?.managedPlan;
  const runtimeCompatibility = plan.alphaCandidate?.runtimeCompatibility;
  const macosRuntime = plan.alphaCandidate?.macosInstalledRuntime;
  const macosRuntimePlan = macosRuntime?.available === true ? macosRuntime.plan : null;
  const cpuCompatibilityMode = managed?.backendMode === "cpu";
  fit.textContent = macosRuntimePlan
    ? `Haven 42 verified official Ollama ${macosRuntimePlan.version} on this Mac. Review the version warning and startup effects below. Haven 42 will check the available models after the local AI engine connects.`
    : alphaModel
    ? automaticAllowed
      ? cpuCompatibilityMode
        ? `Haven 42 selected a local AI model for chat, writing, and summaries that can run in processor compatibility mode. The detected graphics hardware is not required, and Haven 42 must pass a private local test before setup can finish. Technical model name: ${alphaModel}.`
        : `Haven 42 selected a local AI model for chat, writing, and summaries because it fits this computer's memory and graphics hardware. Technical model name: ${alphaModel}.`
      : `Haven 42 found a local AI model that may fit this computer, but cannot safely set it up automatically yet. You can view the manual steps instead. Technical model name: ${alphaModel}.`
    : plan.hardwareAssessment.candidateModel
      ? `Haven 42 found a possible local AI model, but has not confirmed that it can be set up safely on this computer. Technical model name: ${plan.hardwareAssessment.candidateModel}.`
      : "Haven 42 could not safely choose a local AI model from the available computer information.";
  container.append(heading, summary, fit);
  const remediationMessages = linuxSetupRemediation(
    plan.alphaCandidate?.hardware?.blockers,
  );
  if (remediationMessages.length) {
    const remediation = document.createElement("p");
    remediation.className = "setup-remediation";
    remediation.textContent = remediationMessages.join(" ");
    container.append(remediation);
  }
  for (const action of plan.actions) {
    const row = document.createElement("div");
    row.className = "plan-action";
    const label = document.createElement("strong");
    const actionLabels = {
      python: "Haven 42 app runtime",
      ollama: "Local AI engine (Ollama)",
      "ollama-model-qwen35-9b": "Recommended AI model",
    };
    label.textContent = actionLabels[action.componentId] || "Required setup component";
    const stateLabel = document.createElement("span");
    if (macosRuntimePlan && action.componentId === "ollama") {
      stateLabel.textContent = `Installed · ${macosRuntimePlan.version} · approval required`;
    } else if (macosRuntimePlan && action.componentId === "ollama-model-qwen35-9b") {
      stateLabel.textContent = "Checked after local AI starts";
    } else {
      stateLabel.textContent = action.state === "already-available" ? "Already available" : "Needed for this setup";
    }
    row.append(label, stateLabel);
    container.append(row);
  }
  if (managed && plan.alphaCandidate?.managedSetupCandidateAvailable === true && !macosRuntimePlan) {
    const runtimeSummary = document.createElement("section");
    runtimeSummary.className = "setup-runtime-summary";
    runtimeSummary.setAttribute("aria-label", "Selected local AI software");
    const runtimeTitle = document.createElement("strong");
    runtimeTitle.textContent = "Software selected for this model";
    const runtimeIntro = document.createElement("p");
    runtimeIntro.textContent = "Haven 42 matched the model to a tested engine route for this computer. These versions are checked again before use.";
    const runtimeFacts = document.createElement("dl");
    const engineLabel = runtimeCompatibility?.engine === "llama.cpp" ? "llama.cpp" : "Ollama";
    const runtimeVersion = runtimeCompatibility?.selectedRuntimeVersion || "Unavailable";
    const backendLabels = {
      cpu: "Processor compatibility mode", cuda: "NVIDIA CUDA", rocm: "AMD ROCm",
      vulkan: "Vulkan graphics", sycl: "Intel SYCL", core: "Automatic hardware support",
    };
    const runtimeBytes = (runtimeCompatibility?.runtimeArtifacts || [])
      .reduce((total, artifact) => total + (Number.isSafeInteger(artifact.byteLength) ? artifact.byteLength : 0), 0);
    appendSetupDetail(runtimeFacts, "Local AI engine", `${engineLabel} ${runtimeVersion}`);
    appendSetupDetail(runtimeFacts, "Hardware route", backendLabels[managed.backendMode] || managed.backendMode);
    appendSetupDetail(runtimeFacts, "AI model", `${alphaModel} · ${modelSelection.selected.quantization}`);
    appendSetupDetail(runtimeFacts, "Engine download", formatSetupBytes(runtimeBytes));
    appendSetupDetail(runtimeFacts, "Model download", formatSetupBytes(modelSelection.selected.modelBytes));
    appendSetupDetail(runtimeFacts, "Stored in", "Haven42-Data beside the Haven 42 app");
    runtimeSummary.append(runtimeTitle, runtimeIntro, runtimeFacts);
    const disclosure = document.createElement("span");
    disclosure.id = "alpha-setup-storage-summary";
    disclosure.className = "setup-storage-summary";
    const requiredStorageGiB = Number.isSafeInteger(managed.requiredStorageBytes) && managed.requiredStorageBytes > 0
      ? Math.ceil((managed.requiredStorageBytes / (1024 ** 3)) * 10) / 10
      : null;
    const storageText = requiredStorageGiB == null ? "verified free space" : `${requiredStorageGiB} GiB free space`;
    disclosure.textContent = `${storageText} required · stored beside the app`;
    const installLocation = document.createElement("details");
    installLocation.className = "setup-install-location";
    installLocation.setAttribute("aria-label", "Local AI install location");
    const installLocationSummary = document.createElement("summary");
    installLocationSummary.className = "setup-install-location-summary";
    const installLocationCopy = document.createElement("span");
    installLocationCopy.className = "setup-install-location-copy";
    const installLocationTitle = document.createElement("strong");
    installLocationTitle.textContent = "Install location";
    installLocationCopy.append(installLocationTitle, disclosure);
    const installLocationPath = document.createElement("code");
    installLocationPath.textContent = "Haven42-Data";
    installLocationSummary.append(installLocationCopy, installLocationPath);
    const installLocationDetails = document.createElement("div");
    installLocationDetails.className = "setup-install-location-details";
    const installLocationIntro = document.createElement("p");
    installLocationIntro.textContent = "Open this row for storage details. Haven 42 keeps its local AI files together in the extracted app folder.";
    const installLocationList = document.createElement("ul");
    for (const text of [
      "Contains the local AI engine, graphics support, model, and temporary setup files.",
      state.platformFamily === "linux"
        ? "Does not use system application folders and does not create a system service."
        : "Does not use Program Files or AppData, and does not create a Windows service.",
    ]) {
      const item = document.createElement("li");
      item.textContent = text;
      installLocationList.append(item);
    }
    installLocationDetails.append(installLocationIntro, installLocationList);
    installLocation.append(installLocationSummary, installLocationDetails);
    const safeguards = document.createElement("details");
    safeguards.className = "setup-safeguards";
    const safeguardsSummary = document.createElement("summary");
    safeguardsSummary.textContent = "What Haven 42 will do · details";
    const safeguardsList = document.createElement("ul");
    for (const text of [
      "Download only the Ollama and model files shown below, then check that every file is genuine and unchanged.",
      cpuCompatibilityMode
        ? "Use processor compatibility mode and require a successful private local response before setup can finish."
        : "Run a short private test and confirm that your graphics card is used when required.",
      "Stop and explain the problem if a safety check fails.",
      "Keep all downloaded files in this Haven 42 folder so they are easy to remove later.",
    ]) {
      const item = document.createElement("li");
      item.textContent = text;
      safeguardsList.append(item);
    }
    const driverCaution = document.createElement("p");
    driverCaution.className = "setup-driver-caution";
    driverCaution.textContent = "Drivers and Windows settings are not changed automatically. If a driver needs attention, Haven 42 will show instructions for you to review.";
    safeguards.append(safeguardsSummary, safeguardsList, driverCaution);
    const controls = document.createElement("div");
    controls.className = "wizard-actions";
    const automatic = document.createElement("button");
    automatic.id = "alpha-setup-review";
    automatic.type = "button";
    automatic.className = "button primary";
    automatic.textContent = "Review and approve setup";
    const instructions = document.createElement("button");
    instructions.id = "alpha-setup-manual";
    instructions.type = "button";
    instructions.className = "button secondary";
    instructions.textContent = "Show manual steps";
    instructions.addEventListener("click", () => renderManualAlphaSteps(plan, container));
    const cancelSetup = document.createElement("button");
    cancelSetup.id = "alpha-setup-cancel";
    cancelSetup.type = "button";
    cancelSetup.className = "button secondary";
    cancelSetup.textContent = "Cancel setup";
    cancelSetup.hidden = true;
    cancelSetup.addEventListener("click", async () => {
      cancelSetup.disabled = true;
      cancelSetup.textContent = "Stopping safely…";
      try {
        await api("/api/alpha/setup-cancel", {});
        progress.textContent = "Stopping setup safely. Downloaded local data will be kept for retry.";
      } catch (error) {
        progress.textContent = humanError(error);
        cancelSetup.disabled = false;
      }
    });
    const troubleshooting = document.createElement("button");
    troubleshooting.id = "alpha-setup-troubleshooting";
    troubleshooting.type = "button";
    troubleshooting.className = "button secondary";
    troubleshooting.textContent = "View troubleshooting logs";
    troubleshooting.hidden = true;
    troubleshooting.addEventListener("click", () => { void openSetupTroubleshooting(); });
    const progress = document.createElement("p");
    progress.id = "alpha-setup-progress";
    progress.setAttribute("role", "status");
    progress.setAttribute("aria-live", "polite");
    progress.textContent = "Nothing will be downloaded or started until you review the list and give permission.";
    const installationPanel = document.createElement("section");
    installationPanel.id = "alpha-installation-panel";
    installationPanel.className = "installation-progress";
    installationPanel.setAttribute("aria-labelledby", "alpha-installation-title");
    const installationHeading = document.createElement("div");
    installationHeading.className = "installation-progress-heading";
    const installationTitle = document.createElement("strong");
    installationTitle.id = "alpha-installation-title";
    installationTitle.textContent = "What Haven 42 needs";
    const overallValue = document.createElement("output");
    overallValue.id = "alpha-installation-overall-value";
    overallValue.textContent = "0%";
    installationHeading.append(installationTitle, overallValue);
    const overallProgress = document.createElement("progress");
    overallProgress.id = "alpha-installation-overall";
    overallProgress.max = 100;
    overallProgress.value = 0;
    overallProgress.setAttribute("aria-label", "Overall setup progress");
    const componentList = document.createElement("ul");
    componentList.id = "alpha-installation-components";
    componentList.className = "installation-components";
    installationPanel.append(installationHeading, overallProgress, componentList);
    const approvalPanel = document.createElement("section");
    approvalPanel.id = "alpha-setup-approval";
    approvalPanel.className = "setup-approval hidden";
    approvalPanel.setAttribute("aria-labelledby", "alpha-setup-approval-title");
    const approvalTitle = document.createElement("strong");
    approvalTitle.id = "alpha-setup-approval-title";
    approvalTitle.textContent = "Your permission is required";
    const approvalDescription = document.createElement("p");
    approvalDescription.id = "alpha-setup-approval-description";
    approvalDescription.textContent = "Allow Haven 42 to download any missing items shown above, keep them in Haven42-Data, start the local AI engine, and run a short private test.";
    const approvalEffects = document.createElement("ul");
    for (const text of [
      "Download only missing files, using the official sources shown above.",
      "Keep downloaded files inside Haven42-Data in this extracted folder.",
      "Start the local AI engine for this Haven 42 session only.",
      cpuCompatibilityMode
        ? "Send a short private test message and stop safely unless processor compatibility mode works."
        : "Send a short private test message and check that compatible graphics hardware is used.",
    ]) {
      const item = document.createElement("li");
      item.textContent = text;
      approvalEffects.append(item);
    }
    const consentRow = document.createElement("label");
    consentRow.className = "setup-consent";
    const consent = document.createElement("input");
    consent.id = "alpha-setup-consent";
    consent.type = "checkbox";
    consent.autocomplete = "off";
    const consentText = document.createElement("span");
    consentText.textContent = "I understand the list above and allow Haven 42 to complete this setup now.";
    consentRow.append(consent, consentText);
    const approvalActions = document.createElement("div");
    approvalActions.className = "wizard-actions";
    const approve = document.createElement("button");
    approve.type = "button";
    approve.className = "button primary";
    approve.textContent = "Approve and continue";
    approve.disabled = true;
    const cancelApproval = document.createElement("button");
    cancelApproval.type = "button";
    cancelApproval.className = "button secondary";
    cancelApproval.textContent = "Cancel";
    consent.addEventListener("change", () => { approve.disabled = !consent.checked; });
    automatic.addEventListener("click", async () => {
      if (automatic.dataset.mode === "resume") {
        await retryManagedAlphaSetup(automatic, progress);
        return;
      }
      approvalPanel.classList.remove("hidden");
      consent.focus();
    });
    cancelApproval.addEventListener("click", () => {
      consent.checked = false;
      approve.disabled = true;
      approvalPanel.classList.add("hidden");
      automatic.focus();
    });
    approve.addEventListener("click", () => (
      runManagedAlphaSetup(plan, approve, consent, approvalPanel, automatic)
    ));
    approvalActions.append(approve, cancelApproval);
    approvalPanel.append(approvalTitle, approvalDescription, approvalEffects, consentRow, approvalActions);
    controls.append(automatic, instructions, cancelSetup, troubleshooting);
    container.append(runtimeSummary, installLocation, safeguards, installationPanel, controls, approvalPanel, progress);
    refreshAlphaSetupProgress().catch(() => {
      progress.textContent = "Component details are temporarily unavailable. Setup has not started.";
    });
  } else if (alphaModel || state.platformFamily === "macos" || macosRuntimePlan) {
    const macosExternalSetup = state.platformFamily === "macos" || Boolean(macosRuntimePlan);
    const disclosure = document.createElement("p");
    disclosure.className = "notice";
    disclosure.textContent = macosExternalSetup
      ? macosRuntimePlan
        ? macosRuntimePlan.versionStatus === "newer-unverified"
          ? `Haven 42 verified official Ollama ${macosRuntimePlan.version} in Applications. This is newer than the certified macOS version ${macosRuntimePlan.certifiedVersion}, so Haven 42 has not completed compatibility testing for it. You can continue after reviewing and approving the warning below. This step starts Ollama without downloading an app or model; if a model is needed, Haven 42 will choose the best tested fit for this Mac and ask separately before downloading it.`
          : `Haven 42 found Ollama ${macosRuntimePlan.version} in Applications and verified its publisher with macOS. It can start the local engine after you review and approve the exact effects below. This step does not download an app or model; if a model is needed, Haven 42 will choose the best tested fit for this Mac and ask separately before downloading it.`
        : "Haven 42 did not find an official Ollama app it could verify in Applications. Install Ollama from its official macOS download, then return here and check this computer again. Haven 42 will not use Terminal or change system settings."
      : runtimeCompatibility?.decision === "deny"
      ? `This model fits the computer, but Haven 42 does not have an approved ${runtimeCompatibility.engine || "local AI engine"} version for it on this operating system. Setup stopped before downloading anything. Technical reason: ${runtimeCompatibility.reason || "no-compatible-runtime"}.`
      : "This model may fit your computer, but automatic setup has not passed all required tests. You can view manual instructions instead; Haven 42 will not make changes for you.";
    const controls = document.createElement("div");
    controls.className = "wizard-actions";
    if (macosRuntimePlan) {
      const approvalPanel = document.createElement("div");
      approvalPanel.className = "setup-approval hidden";
      approvalPanel.id = "macos-installed-ollama-approval";
      approvalPanel.setAttribute("role", "region");
      approvalPanel.setAttribute("aria-hidden", "true");
      approvalPanel.setAttribute("aria-labelledby", "macos-installed-ollama-approval-title");
      const approvalTitle = document.createElement("strong");
      approvalTitle.id = "macos-installed-ollama-approval-title";
      approvalTitle.textContent = "Your permission is required";
      const approvalEffects = document.createElement("ul");
      for (const effect of macosRuntimePlan.effects) {
        const item = document.createElement("li");
        item.textContent = effect;
        approvalEffects.append(item);
      }
      const consentRow = document.createElement("label");
      consentRow.className = "setup-consent";
      const consent = document.createElement("input");
      consent.type = "checkbox";
      consent.autocomplete = "off";
      const consentText = document.createElement("span");
      consentText.textContent = "I understand and allow Haven 42 to start this verified local AI now.";
      consentRow.append(consent, consentText);
      const approvalActions = document.createElement("div");
      approvalActions.className = "wizard-actions";
      const approve = document.createElement("button");
      approve.type = "button";
      approve.className = "button primary";
      approve.textContent = "Approve and start";
      approve.disabled = true;
      const actionStatus = document.createElement("p");
      actionStatus.id = "macos-installed-ollama-action-status";
      actionStatus.className = "setup-action-status";
      actionStatus.setAttribute("role", "status");
      actionStatus.setAttribute("aria-live", "polite");
      actionStatus.textContent = "Nothing has started. Review the effects and confirm below.";
      const cancel = document.createElement("button");
      cancel.type = "button";
      cancel.className = "button secondary";
      cancel.textContent = "Cancel";
      consent.addEventListener("change", () => { approve.disabled = !consent.checked; });
      cancel.addEventListener("click", () => {
        approvalPanel.classList.add("hidden");
        approvalPanel.setAttribute("aria-hidden", "true");
        consent.checked = false;
        approve.disabled = true;
        actionStatus.textContent = "Nothing has started.";
        byId("wizard-readiness-next").focus();
      });
      approve.addEventListener("click", () => {
        void runMacOSInstalledOllamaSetup(
          macosRuntimePlan, approve, byId("wizard-readiness-next"), consent, approvalPanel, actionStatus,
        );
      });
      approvalActions.append(approve, cancel);
      approvalPanel.append(approvalTitle, approvalEffects, consentRow, actionStatus, approvalActions);
      container.append(disclosure, controls, approvalPanel);
    } else if (macosExternalSetup) {
      const installLink = document.createElement("a");
      installLink.className = "button secondary";
      installLink.href = "https://ollama.com/download/mac";
      installLink.target = "_blank";
      installLink.rel = "noopener noreferrer";
      installLink.referrerPolicy = "no-referrer";
      installLink.textContent = "Install Ollama for macOS";
      controls.append(installLink);
      container.append(disclosure, controls);
    } else {
      const instructions = document.createElement("button");
      instructions.type = "button";
      instructions.className = "button secondary";
      instructions.textContent = "Show manual steps";
      instructions.addEventListener("click", () => renderManualAlphaSteps(plan, container));
      controls.append(instructions);
      container.append(disclosure, controls);
    }
  }
}

function revealMacOSInstalledOllamaApproval(approvalPanel, consent, actionStatus) {
  approvalPanel.classList.remove("hidden");
  approvalPanel.setAttribute("aria-hidden", "false");
  actionStatus.textContent = "Nothing has started. Review the effects and confirm below.";
  approvalPanel.scrollIntoView({ behavior: motionBehavior(), block: "center" });
  consent.focus();
}

async function runMacOSInstalledOllamaSetup(
  plan, approve, review, consent, approvalPanel, actionStatus,
) {
  if (!plan || approve.disabled || !consent.checked) return;
  approve.disabled = true;
  approve.textContent = "Starting local AI…";
  review.disabled = true;
  actionStatus.textContent = "Verifying the installed Ollama app and starting local AI…";
  byId("wizard-scan-status").textContent = "Verifying and starting the installed Ollama app…";
  try {
    const approval = await api("/api/macos/installed-ollama-approve", {
      planId: plan.planId,
      effects: plan.effects,
      confirmed: true,
    });
    const result = await api("/api/macos/installed-ollama-start", {
      approvalToken: approval.approvalToken,
    });
    const local = result.localSetup;
    if (
      result.kind !== "macos-installed-ollama-connection"
      || !local || local.status !== "started"
      || local.signatureVerified !== true || local.gatekeeperAccepted !== true
      || local.ownedProcess !== true || local.approvalConsumed !== true
      || local.downloadPerformed !== false || local.installationPerformed !== false
      || local.appBundleChanged !== false || local.modelDownloadPerformed !== false
      || local.persisted !== false || local.endpoint !== "http://127.0.0.1:11435"
    ) throw new Error("invalid-macos-installed-ollama-result");
    applyProviderConnection(result.connection, local.endpoint, 120, 300);
    actionStatus.textContent = "Local AI started and connected.";
    approvalPanel.classList.add("hidden");
    approvalPanel.setAttribute("aria-hidden", "true");
    if (await offerRecommendedModelDuringSetup()) {
      byId("wizard-scan-status").textContent = "Haven 42 selected the best tested model for this Mac. Review and approve its download; it will be selected automatically when verification finishes.";
      return;
    }
    renderWizardReadiness();
    showWizardStep("ready");
    byId("wizard-scan-status").textContent = "The verified local AI is connected. No app or model was downloaded.";
  } catch (error) {
    const message = `Local AI startup stopped safely. ${humanError(error)}`;
    actionStatus.textContent = message;
    byId("wizard-scan-status").textContent = message;
    review.disabled = false;
    approve.disabled = !consent.checked;
    approve.textContent = "Approve and try again";
  } finally {
    await refreshDiagnosticsQuietly();
  }
}

function renderManualAlphaSteps(plan, container) {
  let panel = byId("alpha-manual-steps");
  if (!panel) {
    panel = document.createElement("div");
    panel.id = "alpha-manual-steps";
    panel.className = "notice";
    container.append(panel);
  }
  panel.replaceChildren();
  const title = document.createElement("strong");
  title.textContent = "Manual setup";
  const text = document.createElement("p");
  const technicalModelName = plan.alphaCandidate?.modelSelection?.selected?.name;
  const platformLabel = state.platformFamily === "linux"
    ? "Linux"
    : state.platformFamily === "macos"
      ? "macOS"
      : "Windows";
  text.textContent = technicalModelName
    ? `Install the Ollama local AI engine from its official ${platformLabel} download, then add the recommended model for chat, writing, and summaries. Its technical name is ${technicalModelName}. Return here and choose Use another AI server. Haven 42 will not make changes in manual mode.`
    : `Install the Ollama local AI engine from its official ${platformLabel} download, then add a compatible text model. Return here and choose Use another AI server. Haven 42 will not make changes in manual mode.`;
  const link = document.createElement("a");
  link.href = state.platformFamily === "linux"
    ? "https://ollama.com/download/linux"
    : state.platformFamily === "macos"
      ? "https://ollama.com/download/mac"
      : "https://ollama.com/download/windows";
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.referrerPolicy = "no-referrer";
  link.textContent = `Open official Ollama ${platformLabel} instructions`;
  panel.append(title, text, link);
  for (const guidance of plan.alphaCandidate?.driverGuidance || []) {
    const driver = document.createElement("p");
    driver.textContent = guidance.driverDetected
      ? `${guidance.vendor.toUpperCase()} driver ${guidance.driverVersion} detected. Haven 42 will not replace it.`
      : `${guidance.vendor.toUpperCase()} driver was not confirmed. Use the vendor's consumer driver guidance before continuing.`;
    panel.append(driver);
  }
}

async function retryManagedAlphaSetup(button, progress) {
  button.disabled = true;
  button.textContent = "Checking existing setup…";
  progress.textContent = "Checking the existing files and starting the local AI. Nothing is being downloaded or installed.";
  try {
    const managed = await api("/api/alpha/connect-managed-provider", {});
    validateManagedProviderResume(managed);
    applyProviderConnection(managed, managed.managedResume.endpoint, 120, 300);
    await showManagedLocalReady();
    byId("setup-wizard").classList.add("hidden");
    openChat();
  } catch (error) {
    progress.textContent = `The existing local AI could not start safely. Nothing was downloaded or replaced. ${humanError(error)}`;
    button.disabled = false;
    button.textContent = "Try starting local AI";
  }
}

function validateManagedProviderResume(managed) {
  const platformTrustVerified = state.platformFamily === "linux"
    ? managed.managedResume?.registeredDigestVerified === true
      && managed.managedResume?.publisherVerified === false
    : managed.managedResume?.publisherVerified === true;
  if (
    managed.managedResume?.receiptVerified !== true
    || managed.managedResume?.integrityVerified !== true
    || !platformTrustVerified
    || managed.managedResume?.downloadPerformed !== false
    || managed.managedResume?.installationPerformed !== false
    || managed.trustScope !== "loopback"
  ) throw new Error("invalid-managed-provider-resume");
  return managed;
}

async function showManagedLocalReady() {
  state.localSetupReturnToChat = false;
  try {
    const storage = await refreshManagedStorageStatus();
    if (
      !storage || storage.managedComponentsPresent !== true
      || !["managed", "managed-with-legacy"].includes(storage.managedComponentsState)
    ) throw new Error("managed-local-storage-status-mismatch");
    byId("local-setup-action-status").textContent = "Local AI is installed and connected on this computer.";
  } catch (_error) {
    byId("portable-storage-status").textContent = "Local AI is connected, but Haven 42 could not refresh the installation details.";
    byId("local-setup-action-status").textContent = "Chat remains available. Open System → Troubleshooting logs if this status does not update after restarting Haven 42.";
  }
}

async function runManagedAlphaSetup(plan, button, consent, approvalPanel, reviewButton) {
  const managed = plan.alphaCandidate?.managedPlan;
  if (!managed || button.disabled || !consent.checked) return;
  button.disabled = true;
  reviewButton.disabled = true;
  approvalPanel.classList.add("hidden");
  const progress = byId("alpha-setup-progress");
  progress.textContent = "Recording your one-time approval…";
  try {
    const approval = await api("/api/alpha/setup-approve", {
      planId: managed.planId,
      effects: managed.effects,
      confirmed: true,
    });
    await api("/api/alpha/setup-execute", { approvalToken: approval.approvalToken });
    while (true) {
      await new Promise((resolve) => window.setTimeout(resolve, 1000));
      const status = await refreshAlphaSetupProgress();
      if (
        status.persisted !== false || status.driverChanges !== false
        || status.serviceChanges !== false || status.firewallChanges !== false
        || status.elevationRequested !== false
      ) throw new Error("invalid-managed-setup-status");
      const labels = {
        approved: "Approval accepted", downloading: "Downloading exact registered component",
        verifying: "Checking downloaded files", extracting: "Preparing local AI files",
        starting: "Starting the local AI engine", "model-download": "Downloading the recommended model",
        validating: "Testing the local AI", complete: "Local AI setup complete",
        failed: "Setup stopped safely", cancelled: "Setup cancelled",
      };
      const safeError = status.error ? ` · ${humanError(new Error(status.error))}` : "";
      progress.textContent = `${labels[status.phase] || "Preparing"} · ${status.progressPercent}%${safeError}`;
      if (status.phase === "complete") {
        const connection = await api("/api/alpha/connect-managed-provider", {});
        validateManagedProviderResume(connection);
        applyProviderConnection(connection, connection.managedResume.endpoint, 120, 300);
        await showManagedLocalReady();
        byId("setup-wizard").classList.add("hidden");
        openChat();
        setTaskEvent("Local AI setup complete · ready to chat", "result");
        return;
      }
      if (["failed", "cancelled"].includes(status.phase)) return;
    }
  } catch (error) {
    progress.textContent = `Setup stopped safely · ${humanError(error)}`;
  } finally {
    consent.checked = false;
    button.disabled = true;
    reviewButton.disabled = false;
    await refreshDiagnosticsQuietly();
  }
}

function updateReadinessNextControl(managedSetupAvailable, macosRuntimeAvailable) {
  const macosExternalSetup = state.platformFamily === "macos" && !macosRuntimeAvailable;
  byId("wizard-readiness-next").disabled = managedSetupAvailable || (!macosRuntimeAvailable && !macosExternalSetup);
  byId("wizard-readiness-next").textContent = managedSetupAvailable
    ? "Complete setup above"
    : macosRuntimeAvailable
      ? "Review and start local AI"
    : macosExternalSetup
      ? "I've installed Ollama — check again"
      : "Local setup unavailable";
}

async function runReadiness() {
  showWizardStep("readiness");
  const platformLabel = state.platformFamily === "linux"
    ? "Linux"
    : state.platformFamily === "macos"
      ? "macOS"
      : "Windows";
  byId("wizard-scan-status").textContent = `Checking ${platformLabel}, memory, storage, and graphics hardware…`;
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
    byId("wizard-scan-status").textContent = "Check complete. Nothing was installed, downloaded, or saved.";
    const managedSetupAvailable = (
      plan.alphaCandidate?.managedSetupCandidateAvailable === true
      && Boolean(plan.alphaCandidate?.managedPlan)
    );
    const macosRuntimeAvailable = (
      plan.alphaCandidate?.macosInstalledRuntime?.available === true
      && Boolean(plan.alphaCandidate?.macosInstalledRuntime?.plan)
    );
    updateReadinessNextControl(managedSetupAvailable, macosRuntimeAvailable);
  } catch (error) {
    byId("wizard-scan-status").textContent = humanError(error);
  } finally {
    await refreshDiagnosticsQuietly();
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
  const selectedMode = byId("text-mode").value;
  if (selectedMode !== "automatic" && Object.hasOwn(CAPABILITIES, selectedMode)) {
    return selectedMode;
  }
  const normalized = content.trimStart().toLocaleLowerCase();
  if (/^(?:please\s+)?(?:summari[sz]e|condense|give me (?:a )?summary|tl;dr)\b/.test(normalized)) {
    return "content.summarize";
  }
  if (/^(?:please\s+)?(?:write|draft|compose|rewrite)\b/.test(normalized)) {
    return "content.write";
  }
  return "general.chat";
}

function renderTextMode() {
  const value = byId("text-mode").value;
  syncTaskModePicker();
  const capabilityId = value === "automatic" ? "general.chat" : value;
  const capability = CAPABILITIES[capabilityId] || CAPABILITIES["general.chat"];
  state.capabilityId = capabilityId;
  byId("capability-eyebrow").textContent = value === "automatic" ? "CONVERSATION · CHOOSE FOR ME" : capability.eyebrow;
  byId("capability-title").textContent = value === "automatic" ? "Private conversation" : capability.title;
  byId("prompt-label").textContent = capability.promptLabel;
  byId("prompt").placeholder = state.connected ? capability.placeholder : "Connect Ollama to begin…";
  byId("model-label").textContent = capability.modelLabel;
  byId("text-mode-status").textContent = value === "automatic"
    ? "Haven 42 will choose chat, writing, or summarization"
    : `${capability.title} selected`;
  renderModelSelect();
}

const TASK_MODE_LABELS = {
  automatic: "Choose for me",
  "general.chat": "Chat",
  "content.write": "Write",
  "content.summarize": "Summarize",
};

function taskModeOptions() {
  return [...document.querySelectorAll(".task-mode-option")];
}

function syncTaskModePicker() {
  const value = byId("text-mode").value;
  byId("text-mode-button-label").textContent = TASK_MODE_LABELS[value] || "Choose for me";
  taskModeOptions().forEach((option) => {
    option.setAttribute("aria-selected", String(option.dataset.value === value));
  });
}

function closeTaskModePicker({ restoreFocus = false } = {}) {
  const button = byId("text-mode-button");
  byId("text-mode-options").classList.add("hidden");
  button.setAttribute("aria-expanded", "false");
  if (restoreFocus) button.focus();
}

function openTaskModePicker() {
  const menu = byId("text-mode-options");
  const button = byId("text-mode-button");
  menu.classList.remove("hidden");
  button.setAttribute("aria-expanded", "true");
  const selected = taskModeOptions().find((option) => option.getAttribute("aria-selected") === "true");
  (selected || taskModeOptions()[0])?.focus();
}

function chooseTaskMode(value) {
  const select = byId("text-mode");
  if (!Object.hasOwn(TASK_MODE_LABELS, value)) return;
  select.value = value;
  select.dispatchEvent(new Event("change", { bubbles: true }));
  closeTaskModePicker({ restoreFocus: true });
}

function formatBytes(value) {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) return "Unavailable";
  return `${(value / 1073741824).toFixed(1)} GiB`;
}

function renderAlphaMetrics(value) {
  if (
    !value || value.schemaVersion !== 1 || value.kind !== "windows-alpha-local-metrics"
    || value.persisted !== false || value.externalTelemetryUsed !== false
    || !value.sample || value.sample.persisted !== false
    || !value.sessionTokens || value.sessionTokens.persisted !== false
  ) return;
  byId("alpha-cpu").textContent = value.sample.systemCpuPercent == null
    ? "Unavailable" : `${Math.round(value.sample.systemCpuPercent)}%`;
  byId("alpha-ram").textContent = (
    value.sample.systemMemoryUsedBytes == null || value.sample.systemMemoryTotalBytes == null
  ) ? "Unavailable" : `${formatBytes(value.sample.systemMemoryUsedBytes)} / ${formatBytes(value.sample.systemMemoryTotalBytes)}`;
  byId("alpha-gpu").textContent = value.sample.gpuUtilizationPercent == null
    ? "Unavailable" : `${Math.round(value.sample.gpuUtilizationPercent)}% · ${formatBytes(value.sample.gpuMemoryUsedBytes)}`;
  byId("alpha-tokens").textContent = String(value.sessionTokens.totalTokens ?? 0);
  const now = Date.now();
  if (now - state.lastMetricsAnnouncementAt >= 60000) {
    byId("resource-status-announcement").textContent = [
      `CPU ${byId("alpha-cpu").textContent}`,
      `memory ${byId("alpha-ram").textContent}`,
      `GPU ${byId("alpha-gpu").textContent}`,
      `session tokens ${byId("alpha-tokens").textContent}`,
    ].join(", ");
    state.lastMetricsAnnouncementAt = now;
  }
}

async function refreshAlphaMetrics() {
  try {
    const response = await fetch("/api/alpha/resources", { credentials: "same-origin", cache: "no-store" });
    if (response.ok) renderAlphaMetrics(await response.json());
  } catch (_error) {
    // The chat path remains usable when a local measurement is unavailable.
  }
}

function renderManagedStorageStatus(value) {
  if (
    !value || value.schemaVersion !== 1
    || !["windows-alpha-setup-progress", "linux-alpha-setup-progress"].includes(value.kind)
    || value.storageScope !== "inside-extracted-folder"
    || value.storageDirectoryName !== "Haven42-Data"
    || !["empty", "managed", "legacy-managed", "managed-with-legacy", "blocked-unrecognized"].includes(value.managedComponentsState)
    || typeof value.managedComponentsPresent !== "boolean"
    || typeof value.legacyManagedComponentsPresent !== "boolean"
    || typeof value.completedSetupCandidate !== "boolean"
  ) throw new Error("invalid-managed-storage-status");
  const status = byId("portable-storage-status");
  const setupButton = byId("setup-local-components");
  const removeButton = byId("remove-managed-components");
  const canConnectLocal = value.completedSetupCandidate === true
    && ["managed", "managed-with-legacy"].includes(value.managedComponentsState);
  setupButton.disabled = false;
  setupButton.dataset.action = canConnectLocal ? "connect-local" : "guided-setup";
  if (value.managedComponentsState === "managed-with-legacy") {
    status.textContent = "Local AI components are installed, including verified files from an earlier Alpha.";
    setupButton.textContent = canConnectLocal ? "Use local AI on this computer" : "Review or finish local setup";
    removeButton.textContent = "Uninstall local AI components";
    removeButton.disabled = false;
  } else if (value.managedComponentsState === "legacy-managed") {
    status.textContent = "Verified data from an earlier Alpha is outside this folder. Remove it before using the new portable layout.";
    setupButton.textContent = "Review local setup";
    removeButton.textContent = "Uninstall earlier Alpha components";
    removeButton.disabled = false;
  } else if (value.managedComponentsState === "managed") {
    status.textContent = "Local AI is installed in Haven42-Data inside this extracted folder.";
    setupButton.textContent = canConnectLocal ? "Use local AI on this computer" : "Review or finish local setup";
    removeButton.textContent = "Uninstall local AI components";
    removeButton.disabled = false;
  } else if (value.managedComponentsState === "blocked-unrecognized") {
    status.textContent = "Haven 42 found an unrecognized Haven42-Data folder and will not remove it automatically.";
    setupButton.textContent = "Local setup unavailable — folder not verified";
    setupButton.disabled = true;
    removeButton.textContent = "Uninstall unavailable — folder not verified";
    removeButton.disabled = true;
  } else {
    status.textContent = "No Haven-managed local AI components are installed in this folder.";
    setupButton.textContent = "Set up local AI on this computer";
    removeButton.textContent = "No local AI components installed";
    removeButton.disabled = true;
  }
}

async function refreshManagedStorageStatus() {
  const response = await fetch("/api/alpha/setup-status", { credentials: "same-origin", cache: "no-store" });
  if (response.status === 404) {
    byId("portable-storage-status").textContent = "Local component management is unavailable on this system.";
    byId("setup-local-components").textContent = "Local setup unavailable on this system";
    byId("setup-local-components").disabled = true;
    byId("remove-managed-components").textContent = "Uninstall unavailable on this system";
    byId("remove-managed-components").disabled = true;
    return null;
  }
  if (!response.ok) throw new Error("managed-storage-status-failed");
  const value = await response.json();
  renderManagedStorageStatus(value);
  return value;
}

const DIAGNOSTIC_EVENT_FIELDS = [
  "appVersion", "category", "code", "eventId", "outcome", "schemaVersion", "timestamp",
];
const DIAGNOSTIC_PRIVACY_FIELDS = [
  "attachmentDataRecorded", "automaticUpload", "commandsRecorded", "credentialsRecorded",
  "endpointsRecorded", "identityRecorded", "pathsRecorded", "promptsRecorded",
  "rawChildOutputRecorded", "responsesRecorded",
];

function validDiagnosticSummary(value) {
  if (
    !value || value.schemaVersion !== 1 || value.kind !== "haven42-sanitized-diagnostics"
    || typeof value.available !== "boolean" || typeof value.removedForSession !== "boolean"
    || ![null, "diagnostic-data-unavailable"].includes(value.error)
    || value.storageScope !== "inside-extracted-folder"
    || value.storageDirectoryName !== "Haven42-Logs"
    || !Number.isSafeInteger(value.eventCount) || value.eventCount < 0 || value.eventCount > 100
    || !Array.isArray(value.events) || value.events.length !== value.eventCount
    || !value.privacy || Object.keys(value.privacy).sort().join("|") !== DIAGNOSTIC_PRIVACY_FIELDS.join("|")
    || DIAGNOSTIC_PRIVACY_FIELDS.some((field) => value.privacy[field] !== false)
  ) return false;
  return value.events.every((event) => (
    event && Object.keys(event).sort().join("|") === DIAGNOSTIC_EVENT_FIELDS.join("|")
    && event.schemaVersion === 1
    && /^[a-f0-9]{16}$/.test(event.eventId)
    && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(event.timestamp)
    && /^[A-Z][A-Z0-9_]{2,79}$/.test(event.code)
    && ["application", "provider", "setup", "text", "storage", "security"].includes(event.category)
    && ["started", "completed", "cancelled", "failed", "warning", "observed"].includes(event.outcome)
    && typeof event.appVersion === "string" && /^[0-9A-Za-z.-]{1,40}$/.test(event.appVersion)
  ));
}

function renderDiagnostics(value) {
  if (!validDiagnosticSummary(value)) throw new Error("invalid-diagnostic-summary");
  const list = byId("diagnostic-events");
  list.replaceChildren();
  if (value.removedForSession) {
    byId("diagnostics-status").textContent = "All troubleshooting logs were removed. Logging stays off until Haven 42 is restarted.";
    return;
  }
  if (!value.available) {
    byId("diagnostics-status").textContent = "Troubleshooting events are unavailable. Haven 42 will continue without recording them.";
    return;
  }
  byId("diagnostics-status").textContent = value.eventCount === 1
    ? "1 sanitized technical event is stored locally."
    : `${value.eventCount} sanitized technical events are stored locally.`;
  value.events.slice().reverse().forEach((event) => {
    const row = document.createElement("li");
    const label = document.createElement("strong");
    const result = document.createElement("span");
    label.textContent = event.code.split("_").map((part) => (
      part.charAt(0) + part.slice(1).toLocaleLowerCase()
    )).join(" ");
    result.textContent = `${event.outcome} · ${event.timestamp.replace("T", " ")}`;
    row.append(label, result);
    list.append(row);
  });
}

async function refreshDiagnostics() {
  const value = await api("/api/alpha/diagnostics", {});
  renderDiagnostics(value);
}

let diagnosticsRefreshPromise = null;

function refreshDiagnosticsQuietly() {
  if (diagnosticsRefreshPromise) return diagnosticsRefreshPromise;
  diagnosticsRefreshPromise = refreshDiagnostics()
    .catch(() => {
      byId("diagnostics-status").textContent =
        "Troubleshooting events are unavailable. Haven 42 will continue without recording them.";
    })
    .finally(() => {
      diagnosticsRefreshPromise = null;
    });
  return diagnosticsRefreshPromise;
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
      const statusLabel = ["recommended", "validated"].includes(status)
        ? "tested for this task"
        : status === "compatible"
          ? "tested for a different task"
          : "not tested for this task";
      option.value = `manual:${item.name}`;
      option.textContent = `${item.name} — ${statusLabel}`;
      advanced.append(option);
    }
    select.append(advanced);
  }

  const installedNames = new Set(state.modelOptions.map((item) => item.name));
  const downloadableByName = new Map();
  state.qualifiedModelCandidates.forEach((item) => {
    if (!installedNames.has(item.name)) downloadableByName.set(item.name, item);
  });
  state.testedModelOptions.forEach((item) => {
    if (item.status !== "installed" && item.capabilities.includes(capabilityId)) {
      downloadableByName.set(item.name, {
        ...item,
        capabilityStatus: Object.fromEntries(item.capabilities.map((id) => [id, "validated-on-matching-hardware"])),
      });
    }
  });
  const downloadable = [...downloadableByName.values()].sort((left, right) => (
    Number(Boolean(right.recommended)) - Number(Boolean(left.recommended))
    || left.name.localeCompare(right.name)
  ));
  if (downloadable.length > 0) {
    const tested = document.createElement("optgroup");
    tested.label = "Tested on matching hardware · download requires approval";
    for (const item of downloadable) {
      const option = document.createElement("option");
      option.value = `candidate:${item.name}`;
      option.textContent = item.recommended
        ? `${item.name} — Recommended · not installed`
        : `${item.name} — tested · not installed`;
      tested.append(option);
    }
    select.append(tested);
  }

  if (selection.mode === "automatic" && recommendation?.automatic) {
    select.value = "automatic";
  } else if (selection.mode === "manual") {
    select.value = `manual:${selection.model}`;
  } else {
    select.selectedIndex = recommendation?.automatic ? 0 : -1;
  }
  const model = selectedModel(capabilityId);
  byId("current-model-name").textContent = model || "No model selected";
  const status = selection.mode === "manual"
    ? state.modelOptions.find((item) => item.name === model)?.capabilityStatus[capabilityId]
    : recommendation?.status;
  const testedForTask = ["recommended", "validated"].includes(status);
  const selectedStatusLabel = testedForTask
    ? "Tested choice"
    : status === "compatible"
      ? "Available · tested for a different task"
      : "Available · not tested for this task";
  byId("model-state").textContent = model
    ? `${selectedStatusLabel} · ${model}`
    : `No suitable installed model found · add ${recommendation?.model || "a recommended model"}, then connect again`;
  const mode = byId("model-selection-mode");
  mode.textContent = selection.mode === "manual" ? "Manual" : "Automatic";
  mode.classList.toggle("manual", selection.mode === "manual");
  byId("reset-model-button").classList.toggle(
    "hidden",
    selection.mode !== "manual" || !recommendation?.automatic,
  );
  const ready = state.connected && Boolean(model);
  select.disabled = !state.connected || (state.modelOptions.length === 0 && downloadable.length === 0);
  byId("context-files").disabled = !state.connected;
  byId("browse-context").disabled = !state.connected;
  byId("prompt").disabled = !ready;
  byId("send-button").disabled = !ready;
  byId("prompt").placeholder = ready
    ? CAPABILITIES[capabilityId].placeholder
    : "Choose an available model to continue…";
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
    model.textContent = recommendation.model || "No recommended model found";
    detail.append(title, model);
    const status = document.createElement("span");
    status.className = `readiness-state ${recommendation.status}`;
    status.textContent = recommendation.automatic ? "Recommended" : "Not ready";
    row.append(detail, status);
    container.append(row);
  }
  const usable = automaticCount > 0;
  byId("wizard-ready-title").textContent = usable ? "Your local AI is ready" : "A model is still needed";
  byId("wizard-ready-summary").textContent = usable
    ? `Haven 42 found ${automaticCount} ready model choice${automaticCount === 1 ? "" : "s"}. You can change these later under Models.`
    : "The local AI engine is connected, but it still needs a model. Choose one under Models; Haven 42 will show the download and ask before starting it.";
  byId("wizard-finish").textContent = usable ? "Open chat" : "Choose a model";
  byId("wizard-finish").disabled = !state.connected;
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
  const elapsedSeconds = details.totalDurationMs == null
    ? "Response time was not reported"
    : `Response completed in ${(details.totalDurationMs / 1000).toFixed(1)} seconds`;
  const generated = details.outputTokens == null
    ? "output length was not reported"
    : `${details.outputTokens} tokens generated`;
  byId("run-details-summary").textContent = `${elapsedSeconds}; ${generated}.`;
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
  const summary = `${capability.resultLabel} ready · kept in this session · no file saved`;
  if (warnings.some((event) => event.code === "MODEL_IMAGE_INPUT_UNVERIFIED")) {
    setTaskEvent(`Warning · Haven 42 has not confirmed that this model can understand screenshots · ${summary}`, "warning");
  } else if (warnings.some((event) => event.code === "MODEL_SELECTION_UNVERIFIED_FOR_CAPABILITY")) {
    setTaskEvent(`Warning · Haven 42 has not tested this model for the selected task · ${summary}`, "warning");
  } else {
    setTaskEvent(summary, "result");
  }
  renderRunDetails(result.runDetails);
  if (result.sessionTokenTotals?.persisted === false) {
    byId("alpha-tokens").textContent = String(result.sessionTokenTotals.totalTokens ?? 0);
  }
  byId("alpha-speed").textContent = result.runDetails.tokensPerSecond == null
    ? "Not reported"
    : `${result.runDetails.tokensPerSecond} tokens/s`;
  addMessage("assistant", result.artifact.content.text, capability.resultLabel, {
    reportToken: result.answerReportToken,
  });
}

function reserveMarkdownElements(budget, count = 1) {
  if (budget.remaining < count) return false;
  budget.remaining -= count;
  return true;
}

function appendMarkdownFallback(container, lines, index) {
  const fallback = document.createElement("pre");
  fallback.className = "markdown-render-limit";
  fallback.textContent = lines.slice(index).join("\n");
  container.append(fallback);
}

function appendInlineMarkdown(container, source, budget) {
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
    if (!reserveMarkdownElements(budget)) {
      buffer += source.slice(index);
      break;
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
  const budget = { remaining: MAX_MARKDOWN_DOM_ELEMENTS };
  for (let index = 0; index < lines.length;) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }
    const kind = markdownBlockKind(line);
    if (kind === "fence") {
      if (!reserveMarkdownElements(budget, 2)) {
        appendMarkdownFallback(container, lines, index);
        return;
      }
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
      if (!reserveMarkdownElements(budget)) {
        appendMarkdownFallback(container, lines, index);
        return;
      }
      const match = line.match(/^(#{1,4})\s+(.+)$/);
      const heading = document.createElement(`h${Math.min(5, match[1].length + 2)}`);
      appendInlineMarkdown(heading, match[2], budget);
      container.append(heading);
      index += 1;
      continue;
    }
    if (kind === "unordered" || kind === "ordered") {
      if (!reserveMarkdownElements(budget)) {
        appendMarkdownFallback(container, lines, index);
        return;
      }
      const list = document.createElement(kind === "unordered" ? "ul" : "ol");
      const pattern = kind === "unordered"
        ? /^\s{0,3}[-*+]\s+(.+)$/
        : /^\s{0,3}\d{1,3}[.)]\s+(.+)$/;
      container.append(list);
      while (index < lines.length) {
        const match = lines[index].match(pattern);
        if (!match) break;
        if (!reserveMarkdownElements(budget)) {
          appendMarkdownFallback(container, lines, index);
          return;
        }
        const item = document.createElement("li");
        appendInlineMarkdown(item, match[1], budget);
        list.append(item);
        index += 1;
      }
      continue;
    }
    if (kind === "quote") {
      if (!reserveMarkdownElements(budget)) {
        appendMarkdownFallback(container, lines, index);
        return;
      }
      const quoteLines = [];
      while (index < lines.length && markdownBlockKind(lines[index]) === "quote") {
        quoteLines.push(lines[index].replace(/^\s{0,3}>\s?/, ""));
        index += 1;
      }
      const quote = document.createElement("blockquote");
      appendInlineMarkdown(quote, quoteLines.join(" "), budget);
      container.append(quote);
      continue;
    }
    if (kind === "rule") {
      if (!reserveMarkdownElements(budget)) {
        appendMarkdownFallback(container, lines, index);
        return;
      }
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
    if (!reserveMarkdownElements(budget)) {
      appendMarkdownFallback(container, lines, index - paragraphLines.length);
      return;
    }
    const paragraph = document.createElement("p");
    appendInlineMarkdown(paragraph, paragraphLines.join(" "), budget);
    container.append(paragraph);
  }
}

function validAnswerReportIdentity(value) {
  return Boolean(
    value
    && Object.keys(value).join("|") === "reportToken"
    && typeof value.reportToken === "string"
    && /^[a-f0-9]{32}$/.test(value.reportToken)
  );
}

function closeAnswerReport(restoreFocus = true) {
  const trigger = state.pendingAnswerReport?.trigger;
  state.pendingAnswerReport = null;
  byId("answer-report-panel").classList.add("hidden");
  byId("answer-report-note").value = "";
  byId("answer-report-status").textContent = "";
  if (restoreFocus && trigger?.isConnected) trigger.focus();
}

function openAnswerReport(identity, trigger) {
  if (!validAnswerReportIdentity(identity)) return;
  state.pendingAnswerReport = { identity: {...identity}, trigger };
  byId("answer-report-category").value = "incorrect";
  byId("answer-report-note").value = "";
  byId("answer-report-status").textContent = "Nothing is sent anywhere. The report stays in Haven42-Logs.";
  byId("answer-report-panel").classList.remove("hidden");
  byId("answer-report-category").focus();
}

function createMessageAction(label, iconPaths) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "button text-button message-action";
  const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  icon.classList.add("message-action-icon");
  icon.setAttribute("viewBox", "0 0 24 24");
  icon.setAttribute("aria-hidden", "true");
  icon.setAttribute("focusable", "false");
  iconPaths.forEach((pathData) => {
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", pathData);
    icon.append(path);
  });
  const text = document.createElement("span");
  text.textContent = label;
  button.append(icon, text);
  return {button, text};
}

function addMessage(role, content, label, answerReportIdentity = null) {
  const messages = byId("messages");
  const wasFollowing = state.chatAutoFollow
    || messages.scrollHeight - messages.scrollTop - messages.clientHeight < 48;
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
  if (role === "assistant" && validAnswerReportIdentity(answerReportIdentity)) {
    const actions = document.createElement("div");
    actions.className = "message-actions";
    const copyAction = createMessageAction("Copy answer", ["M8 8h11v11H8z", "M5 16V5h11"]);
    const copy = copyAction.button;
    copy.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(content);
        copyAction.text.textContent = "Copied";
      } catch (_error) {
        copyAction.text.textContent = "Copy unavailable";
      }
    });
    const retry = createMessageAction("Try again", ["M20 7v5h-5", "M19 12a7 7 0 1 0-2.05 4.95"]);
    const retryButton = retry.button;
    retryButton.addEventListener("click", () => {
      const priorPrompt = [...state.messages].reverse().find((item) => item.role === "user")?.content;
      if (!priorPrompt) return;
      byId("prompt").value = priorPrompt;
      byId("prompt").focus();
      setTaskEvent("Previous request restored for review. Press Send when you are ready.", "result");
    });
    const report = createMessageAction("Report this answer", ["M5 21V4", "M5 5h12l-2 4 2 4H5"]);
    const reportButton = report.button;
    reportButton.addEventListener("click", () => openAnswerReport(answerReportIdentity, reportButton));
    actions.append(copy, retryButton, reportButton);
    body.append(actions);
  }
  article.append(avatar, body);
  messages.append(article);
  messages.classList.toggle(
    "empty-conversation",
    state.messages.length === 0 && messages.childElementCount === 1,
  );
  if (wasFollowing) {
    state.chatAutoFollow = true;
    const scrollToLatest = () => messages.scrollTo({ top: messages.scrollHeight, behavior: "auto" });
    scrollToLatest();
    window.requestAnimationFrame(scrollToLatest);
  }
  return article;
}

const TRUSTED_CITATION_FIELDS = Object.freeze([
  "activeNavigationAllowed", "citationId", "destination",
  "destinationDisclosureRequired", "displayDomain", "title",
]);
const TRUSTED_CITATION_BUNDLE_FIELDS = Object.freeze([
  "citations", "exactSourceAccounting", "modelSuppliedLinksAccepted",
  "runtimeAdmissionGranted", "schemaVersion",
]);

function hasExactObjectKeys(value, fields) {
  return Boolean(
    value
    && typeof value === "object"
    && !Array.isArray(value)
    && Object.keys(value).sort().join("\u0000") === [...fields].sort().join("\u0000")
  );
}

function isTrustedCitationText(value, maximum) {
  return (
    typeof value === "string"
    && value.length > 0
    && value.length <= maximum
    && value === value.trim()
    && !/[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff<>]/u.test(value)
  );
}

function isApprovedWebSearchDestination(value, normalizedQuery = null) {
  try {
    const destination = new URL(value);
    return destination.protocol === "https:"
      && destination.hostname === "search.brave.com"
      && destination.port === ""
      && destination.pathname === "/search"
      && [...destination.searchParams.keys()].join(",") === "q"
      && isTrustedCitationText(destination.searchParams.get("q"), 256)
      && (normalizedQuery === null || destination.searchParams.get("q") === normalizedQuery)
      && destination.hash === ""
      && destination.username === ""
      && destination.password === "";
  } catch (_error) {
    return false;
  }
}

function isPublicResearchDestination(value, expectedDomain) {
  try {
    const destination = new URL(value);
    const host = destination.hostname.toLocaleLowerCase().replace(/\.$/u, "");
    return destination.protocol === "https:"
      && destination.port === ""
      && destination.username === ""
      && destination.password === ""
      && destination.hash === ""
      && host === expectedDomain
      && !["localhost"].includes(host)
      && !host.endsWith(".localhost")
      && !host.endsWith(".local")
      && /^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/u.test(host);
  } catch (_error) {
    return false;
  }
}

function validateTrustedCitationBundle(bundle) {
  if (
    !hasExactObjectKeys(bundle, TRUSTED_CITATION_BUNDLE_FIELDS)
    || bundle.schemaVersion !== 1
    || bundle.exactSourceAccounting !== true
    || bundle.modelSuppliedLinksAccepted !== false
    || bundle.runtimeAdmissionGranted !== true
    || !Array.isArray(bundle.citations)
    || bundle.citations.length < 1
    || bundle.citations.length > 10
  ) return null;
  const citationIds = new Set();
  const destinations = new Set();
  const accepted = [];
  for (const citation of bundle.citations) {
    if (
      !hasExactObjectKeys(citation, TRUSTED_CITATION_FIELDS)
      || !/^source-[0-9a-f]{20}$/u.test(citation.citationId)
      || !isTrustedCitationText(citation.title, 200)
      || !isTrustedCitationText(citation.displayDomain, 253)
      || !isPublicResearchDestination(citation.destination, citation.displayDomain)
      || citation.destinationDisclosureRequired !== true
      || citation.activeNavigationAllowed !== false
      || citationIds.has(citation.citationId)
      || destinations.has(citation.destination)
    ) return null;
    citationIds.add(citation.citationId);
    destinations.add(citation.destination);
    accepted.push(citation);
  }
  return accepted;
}

function clearTrustedCitations() {
  byId("research-source-list").replaceChildren();
  byId("research-sources-status").textContent = "";
  byId("research-sources").classList.add("hidden");
}

function renderTrustedCitations(bundle) {
  const citations = validateTrustedCitationBundle(bundle);
  if (!citations) {
    clearTrustedCitations();
    return Object.freeze({ accepted: false, rendered: 0 });
  }
  const items = citations.map((citation) => {
    const item = document.createElement("li");
    item.className = "trusted-citation";
    const title = document.createElement("strong");
    title.textContent = citation.title;
    const domain = document.createElement("span");
    domain.textContent = `Source: ${citation.displayDomain}`;
    const destination = document.createElement("code");
    destination.textContent = `Destination: ${citation.destination}`;
    item.append(title, domain, destination);
    return item;
  });
  byId("research-source-list").replaceChildren(...items);
  byId("research-sources").classList.remove("hidden");
  byId("research-sources-status").textContent = `${citations.length} trusted research source${citations.length === 1 ? "" : "s"} shown. Destinations are disclosed but inactive.`;
  return Object.freeze({ accepted: true, rendered: citations.length });
}

window.Haven42TrustedCitationRenderer = Object.freeze({
  clear: clearTrustedCitations,
  render: renderTrustedCitations,
});

const RESEARCH_REVIEW_FIELDS = Object.freeze([
  "schemaVersion", "reviewId", "kind", "normalizedQuery", "providerId",
  "citation", "exactReviewRequired", "modelApprovalAccepted",
  "networkAuthorityGranted", "runtimeAdmissionGranted", "persistenceAllowed",
  "automaticFollowUpAllowed",
]);
let pendingResearchReview = null;
let pendingResearchDecision = null;
let pendingResearchExecution = null;
let researchReviewReturnFocus = null;
let researchReviewInertState = [];

function validateResearchReviewBundle(bundle) {
  if (
    !hasExactObjectKeys(bundle, RESEARCH_REVIEW_FIELDS)
    || bundle.schemaVersion !== 1
    || !/^review-[0-9a-f]{20}$/u.test(bundle.reviewId)
    || !["query", "page", "web", "general-web"].includes(bundle.kind)
    || !isTrustedCitationText(bundle.normalizedQuery, 256)
    || !["wikipedia", "brave-browser-search", "brave-search-api"].includes(bundle.providerId)
    || bundle.exactReviewRequired !== true
    || bundle.modelApprovalAccepted !== false
    || bundle.networkAuthorityGranted !== false
    || bundle.runtimeAdmissionGranted !== false
    || bundle.persistenceAllowed !== false
    || bundle.automaticFollowUpAllowed !== false
  ) return null;
  if (bundle.kind === "query" && (bundle.citation !== null || bundle.providerId !== "wikipedia")) return null;
  if (bundle.kind === "page") {
    const citations = validateTrustedCitationBundle({
      schemaVersion: 1,
      citations: [bundle.citation],
      exactSourceAccounting: true,
      modelSuppliedLinksAccepted: false,
      runtimeAdmissionGranted: true,
    });
    if (!citations) return null;
  }
  if (bundle.kind === "web") {
    if (
      bundle.providerId !== "brave-browser-search"
      || !hasExactObjectKeys(bundle.citation, ["destination", "displayDomain", "title"])
      || bundle.citation.title !== "Brave Search"
      || bundle.citation.displayDomain !== "search.brave.com"
      || !isApprovedWebSearchDestination(bundle.citation.destination, bundle.normalizedQuery)
    ) return null;
  }
  if (bundle.kind === "general-web") {
    if (
      bundle.providerId !== "brave-search-api"
      || !hasExactObjectKeys(bundle.citation, ["destination", "displayDomain", "title"])
      || bundle.citation.title !== "Brave Search API and selected public pages"
      || bundle.citation.displayDomain !== "api.search.brave.com"
      || bundle.citation.destination !== "https://api.search.brave.com/res/v1/web/search"
    ) return null;
  }
  return Object.freeze({
    ...bundle,
    citation: bundle.citation === null ? null : Object.freeze({ ...bundle.citation }),
  });
}

function setResearchReviewBackgroundInert(active) {
  if (active) {
    researchReviewInertState = [...document.body.children]
      .filter((element) => element.id !== "research-review-layer" && element.tagName !== "SCRIPT")
      .map((element) => [element, element.inert]);
    researchReviewInertState.forEach(([element]) => { element.inert = true; });
    return;
  }
  researchReviewInertState.forEach(([element, wasInert]) => { element.inert = wasInert; });
  researchReviewInertState = [];
}

function closeResearchApprovalReview(decision = null) {
  const review = pendingResearchReview;
  const execution = pendingResearchExecution;
  const layer = byId("research-review-layer");
  const wasOpen = review !== null || !layer.classList.contains("hidden");
  if (review && decision) {
    pendingResearchDecision = Object.freeze({
      schemaVersion: 1,
      reviewId: review.reviewId,
      kind: review.kind,
      decision,
      singleUse: true,
      networkStarted: decision === "approved" && execution !== null,
    });
  }
  pendingResearchReview = null;
  pendingResearchExecution = null;
  layer.classList.add("hidden");
  layer.setAttribute("aria-hidden", "true");
  byId("research-review-status").textContent = "";
  setResearchReviewBackgroundInert(false);
  if (!wasOpen) {
    researchReviewReturnFocus = null;
    return;
  }
  const target = researchReviewReturnFocus instanceof HTMLElement
    && researchReviewReturnFocus.isConnected
    && researchReviewReturnFocus.matches('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')
    && !researchReviewReturnFocus.closest(".hidden")
    ? researchReviewReturnFocus
    : byId("home-nav");
  researchReviewReturnFocus = null;
  if (!target.inert) target.focus({ preventScroll: true });
  if (decision === "cancelled" && execution) {
    if (execution.kind === "general-web") byId("research-api-key").value = "";
    byId("research-query-status").textContent = "Research request cancelled. Nothing was sent.";
    byId("research-query-status").removeAttribute("data-state");
    void api("/api/research/approval/cancel", { approvalToken: execution.approvalToken }).catch(() => {});
  }
}

function clearResearchApprovalReview() {
  pendingResearchDecision = null;
  pendingResearchExecution = null;
  closeResearchApprovalReview();
}

function openResearchApprovalReview(bundle, returnFocus = document.activeElement, execution = null) {
  const review = validateResearchReviewBundle(bundle);
  if (
    !review
    || (
      execution !== null
      && (
        !hasExactObjectKeys(execution, ["approvalToken", "kind"])
        || !["query", "page", "web", "general-web"].includes(execution.kind)
        || !/^[0-9a-f]{32}$/u.test(execution.approvalToken)
        || execution.kind !== review.kind
      )
    )
    || !byId("setup-wizard").classList.contains("hidden")
    || !byId("section-tour-layer").classList.contains("hidden")
    || !byId("research-review-layer").classList.contains("hidden")
  ) {
    clearResearchApprovalReview();
    return Object.freeze({ accepted: false, opened: false });
  }
  pendingResearchDecision = null;
  pendingResearchReview = review;
  pendingResearchExecution = execution === null ? null : Object.freeze({ ...execution });
  researchReviewReturnFocus = returnFocus instanceof HTMLElement ? returnFocus : byId("home-nav");
  byId("research-review-kind").textContent = review.kind === "query"
    ? "Search Wikipedia"
    : review.kind === "web"
      ? "Open a wider-web search in your browser"
      : review.kind === "general-web"
        ? "Search selected public pages and create a cited local answer"
        : "Read one selected Wikipedia page";
  byId("research-review-description").textContent = review.kind === "web"
    ? "Haven 42 will not open the wider-web search unless you approve these exact search words and destination."
    : review.kind === "general-web"
      ? "Haven 42 will send the exact query to Brave, read a bounded set of returned public pages, and ask your selected local model for a citation-bound answer."
      : "Haven 42 will not contact Wikipedia unless you approve this exact request.";
  byId("research-review-query").textContent = review.normalizedQuery;
  const pageReview = ["page", "web", "general-web"].includes(review.kind);
  byId("research-review-source-row").classList.toggle("hidden", !pageReview);
  byId("research-review-destination-row").classList.toggle("hidden", !pageReview);
  byId("research-review-source").textContent = pageReview ? review.citation.title : "";
  byId("research-review-destination").textContent = pageReview ? review.citation.destination : "";
  const layer = byId("research-review-layer");
  setResearchReviewBackgroundInert(true);
  layer.classList.remove("hidden");
  layer.setAttribute("aria-hidden", "false");
  byId("research-review-status").textContent = `${review.kind === "page" ? "Page" : "Search"} request ready for your review. Nothing has been sent.`;
  byId("research-review-dialog").focus({ preventScroll: true });
  return Object.freeze({ accepted: true, opened: true });
}

function consumeResearchApprovalDecision() {
  const decision = pendingResearchDecision;
  pendingResearchDecision = null;
  return decision;
}

byId("research-review-close").addEventListener("click", () => closeResearchApprovalReview("cancelled"));
byId("research-review-cancel").addEventListener("click", () => closeResearchApprovalReview("cancelled"));
byId("research-review-approve").addEventListener("click", (event) => {
  if (!event.isTrusted) {
    byId("research-review-status").textContent = "Approval requires a direct user action.";
    return;
  }
  const execution = pendingResearchExecution;
  closeResearchApprovalReview("approved");
  if (execution) void executeResearchApproval(execution);
});
byId("research-review-layer").addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    event.preventDefault();
    closeResearchApprovalReview("cancelled");
    return;
  }
  if (event.key !== "Tab") return;
  const controls = [...byId("research-review-dialog").querySelectorAll(
    'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
  )].filter((element) => !element.closest(".hidden"));
  if (controls.length === 0) return;
  const first = controls[0];
  const last = controls[controls.length - 1];
  if (event.shiftKey && [first, byId("research-review-dialog")].includes(document.activeElement)) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
});

window.Haven42ResearchApprovalReview = Object.freeze({
  clear: clearResearchApprovalReview,
  consumeDecision: consumeResearchApprovalDecision,
  open: openResearchApprovalReview,
});

const RESEARCH_PREPARATION_FIELDS = Object.freeze([
  "approvalToken", "expiresInSeconds", "kind", "persisted",
  "review", "schemaVersion", "singleUse",
]);
const RESEARCH_QUERY_RESULT_FIELDS = Object.freeze([
  "additionalResultsAvailable", "automaticFollowUpAllowed", "citations",
  "contentPersisted", "kind", "modelToolAllowed", "networkUsed",
  "normalizedQuery", "queryPersisted", "resultId", "schemaVersion", "status",
]);
const RESEARCH_PAGE_RESULT_FIELDS = Object.freeze([
  "activeNavigationAllowed", "automaticFollowUpAllowed", "contentCharacters",
  "contentPersisted", "kind", "modelToolAllowed", "networkUsed",
  "normalizedQuery", "pageExecutionAllowed", "schemaVersion", "segments",
  "source", "status",
]);

function validateResearchPreparation(value, kind) {
  const review = hasExactObjectKeys(value, RESEARCH_PREPARATION_FIELDS)
    ? validateResearchReviewBundle(value.review)
    : null;
  if (
    value?.schemaVersion !== 1
    || value?.kind !== "research-approval-preparation"
    || !/^[0-9a-f]{32}$/u.test(value?.approvalToken || "")
    || value?.expiresInSeconds !== 300
    || value?.singleUse !== true
    || value?.persisted !== false
    || !review
    || review.kind !== kind
  ) throw new Error("invalid-research-preparation");
  return Object.freeze({ ...value, review });
}

function validateResearchCitationBundleAllowEmpty(bundle) {
  if (
    !hasExactObjectKeys(bundle, TRUSTED_CITATION_BUNDLE_FIELDS)
    || bundle?.schemaVersion !== 1
    || bundle?.exactSourceAccounting !== true
    || bundle?.modelSuppliedLinksAccepted !== false
    || bundle?.runtimeAdmissionGranted !== true
    || !Array.isArray(bundle?.citations)
    || bundle.citations.length > 10
  ) return null;
  return bundle.citations.length === 0 ? [] : validateTrustedCitationBundle(bundle);
}

function clearResearchWorkspace() {
  state.researchResultId = null;
  byId("research-query").value = "";
  byId("research-api-key").value = "";
  byId("research-query-status").textContent = "";
  byId("research-query-status").removeAttribute("data-state");
  byId("research-result-list").replaceChildren();
  byId("research-results").classList.add("hidden");
  byId("research-page-title").textContent = "";
  byId("research-page-destination").textContent = "";
  byId("research-page-content").replaceChildren();
  byId("research-page").classList.add("hidden");
  byId("research-answer-claims").replaceChildren();
  byId("research-answer").classList.add("hidden");
  byId("research-tools").removeAttribute("aria-busy");
  byId("research-tools").open = false;
  byId("research-open-troubleshooting").classList.add("hidden");
  byId("research-web-link").href = "about:blank";
  byId("research-web-link").classList.add("hidden");
  clearTrustedCitations();
  clearResearchApprovalReview();
}

function renderGeneralWebAnswer(result) {
  const expected = [
    "automaticFollowUpAllowed", "citations", "claims", "contentPersisted",
    "credentialPersisted", "kind", "modelToolAllowed", "networkUsed",
    "normalizedQuery", "queryPersisted", "schemaVersion", "sourceCount", "status",
  ];
  const citations = hasExactObjectKeys(result, expected)
    ? validateTrustedCitationBundle({
      schemaVersion: 1,
      citations: result.citations,
      exactSourceAccounting: true,
      modelSuppliedLinksAccepted: false,
      runtimeAdmissionGranted: true,
    })
    : null;
  const allowed = new Set((citations || []).map((item) => item.citationId));
  if (
    !citations
    || result.schemaVersion !== 1
    || result.kind !== "general-web-research-answer"
    || result.status !== "succeeded"
    || !isTrustedCitationText(result.normalizedQuery, 256)
    || result.sourceCount !== citations.length
    || !Array.isArray(result.claims)
    || result.claims.length < 1
    || result.claims.length > 20
    || result.claims.some((claim, index) => (
      !hasExactObjectKeys(claim, ["citationIds", "claimIndex", "text"])
      || claim.claimIndex !== index + 1
      || !isTrustedCitationText(claim.text, 1000)
      || /(?:https?:\/\/|www\.|\[[^\]]+\]\([^\)]+\))/iu.test(claim.text)
      || !Array.isArray(claim.citationIds)
      || claim.citationIds.length < 1
      || claim.citationIds.length > 5
      || new Set(claim.citationIds).size !== claim.citationIds.length
      || claim.citationIds.some((item) => !allowed.has(item))
    ))
    || result.networkUsed !== true
    || result.queryPersisted !== false
    || result.contentPersisted !== false
    || result.credentialPersisted !== false
    || result.modelToolAllowed !== false
    || result.automaticFollowUpAllowed !== false
  ) throw new Error("invalid-general-web-answer");
  const claims = result.claims.map((claim) => {
    const paragraph = document.createElement("p");
    paragraph.append(document.createTextNode(`${claim.text} `));
    const references = document.createElement("span");
    references.className = "research-claim-citations";
    references.textContent = claim.citationIds.map((id) => {
      const index = citations.findIndex((item) => item.citationId === id) + 1;
      return `[${index}]`;
    }).join(" ");
    references.setAttribute("aria-label", `Sources ${claim.citationIds.map((id) => citations.findIndex((item) => item.citationId === id) + 1).join(", ")}`);
    paragraph.append(references);
    return paragraph;
  });
  byId("research-answer-claims").replaceChildren(...claims);
  byId("research-answer").classList.remove("hidden");
  renderTrustedCitations({
    schemaVersion: 1,
    citations: result.citations,
    exactSourceAccounting: true,
    modelSuppliedLinksAccepted: false,
    runtimeAdmissionGranted: true,
  });
  byId("research-query-status").textContent = `Cited answer ready from ${citations.length} public sources. Nothing was saved.`;
  byId("research-answer-title").focus({ preventScroll: true });
}

function renderResearchQueryResult(result) {
  const citations = hasExactObjectKeys(result, RESEARCH_QUERY_RESULT_FIELDS)
    ? validateResearchCitationBundleAllowEmpty(result.citations)
    : null;
  if (
    citations === null
    || result.schemaVersion !== 1
    || result.kind !== "wikipedia-research-query-result"
    || result.status !== "succeeded"
    || !/^result-[0-9a-f]{20}$/u.test(result.resultId)
    || !isTrustedCitationText(result.normalizedQuery, 256)
    || typeof result.additionalResultsAvailable !== "boolean"
    || result.networkUsed !== true
    || result.queryPersisted !== false
    || result.contentPersisted !== false
    || result.modelToolAllowed !== false
    || result.automaticFollowUpAllowed !== false
  ) throw new Error("invalid-research-query-result");
  state.researchResultId = result.resultId;
  const list = byId("research-result-list");
  list.replaceChildren();
  byId("research-page").classList.add("hidden");
  byId("research-page-content").replaceChildren();
  if (citations.length === 0) {
    clearTrustedCitations();
    byId("research-results").classList.add("hidden");
    byId("research-query-status").textContent = "No matching Wikipedia pages were found. Try different search words.";
    return;
  }
  citations.forEach((citation) => {
    const item = document.createElement("li");
    item.className = "research-result";
    const details = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = citation.title;
    const domain = document.createElement("span");
    domain.textContent = `Source: ${citation.displayDomain}`;
    const destination = document.createElement("code");
    destination.textContent = `Destination: ${citation.destination}`;
    const review = document.createElement("button");
    review.type = "button";
    review.className = "button text-button";
    review.textContent = "Review page request";
    review.setAttribute("aria-label", `Review request to read ${citation.title}`);
    review.addEventListener("click", () => {
      void prepareResearchPage(citation.citationId, review);
    });
    details.append(title, domain, destination, review);
    item.append(details);
    list.append(item);
  });
  renderTrustedCitations(result.citations);
  byId("research-results").classList.remove("hidden");
  byId("research-query-status").textContent = `${citations.length} result${citations.length === 1 ? "" : "s"} received. Page contents have not been requested.`;
  byId("research-results-title").focus({ preventScroll: true });
}

function renderResearchPageResult(result) {
  const sources = hasExactObjectKeys(result, RESEARCH_PAGE_RESULT_FIELDS)
    ? validateTrustedCitationBundle({
      schemaVersion: 1,
      citations: [result.source],
      exactSourceAccounting: true,
      modelSuppliedLinksAccepted: false,
      runtimeAdmissionGranted: true,
    })
    : null;
  if (
    !sources
    || result.schemaVersion !== 1
    || result.kind !== "wikipedia-research-page-result"
    || result.status !== "succeeded"
    || !isTrustedCitationText(result.normalizedQuery, 256)
    || !Array.isArray(result.segments)
    || result.segments.length < 1
    || result.segments.length > 500
    || result.segments.some((item, index) => (
      !hasExactObjectKeys(item, ["index", "text", "trust"])
      || item.index !== index + 1
      || !isTrustedCitationText(item.text, 100000)
      || item.trust !== "untrusted-inert-text"
    ))
    || result.contentCharacters !== result.segments.reduce((sum, item) => sum + item.text.length, 0)
    || result.contentCharacters > 100000
    || result.networkUsed !== true
    || result.contentPersisted !== false
    || result.activeNavigationAllowed !== false
    || result.pageExecutionAllowed !== false
    || result.modelToolAllowed !== false
    || result.automaticFollowUpAllowed !== false
  ) throw new Error("invalid-research-page-result");
  const content = byId("research-page-content");
  content.replaceChildren(...result.segments.map((segment) => {
    const paragraph = document.createElement("p");
    paragraph.textContent = segment.text;
    return paragraph;
  }));
  byId("research-page-title").textContent = result.source.title;
  byId("research-page-destination").textContent = `Source: ${result.source.displayDomain} · Destination: ${result.source.destination}`;
  renderTrustedCitations({
    schemaVersion: 1,
    citations: [result.source],
    exactSourceAccounting: true,
    modelSuppliedLinksAccepted: false,
    runtimeAdmissionGranted: true,
  });
  byId("research-page").classList.remove("hidden");
  byId("research-query-status").textContent = `Selected page read. ${result.contentCharacters.toLocaleString()} characters remain in memory for this task.`;
  byId("research-page-title").focus({ preventScroll: true });
}

async function executeResearchApproval(execution) {
  const status = byId("research-query-status");
  byId("research-tools").setAttribute("aria-busy", "true");
  status.removeAttribute("data-state");
  status.textContent = execution.kind === "query"
    ? "Searching Wikipedia…"
    : execution.kind === "web"
      ? "Preparing your approved web-search link…"
      : execution.kind === "general-web"
        ? "Searching public sources and preparing a cited local answer…"
      : "Reading the approved Wikipedia page…";
  try {
    const result = await api(
      execution.kind === "query"
        ? "/api/research/query/execute"
        : execution.kind === "web"
          ? "/api/research/web/execute"
          : execution.kind === "general-web"
            ? "/api/research/general/execute"
          : "/api/research/page/execute",
      { approvalToken: execution.approvalToken, confirmed: true },
    );
    if (execution.kind === "query") renderResearchQueryResult(result);
    else if (execution.kind === "general-web") renderGeneralWebAnswer(result);
    else if (execution.kind === "web") {
      if (
        !hasExactObjectKeys(result, [
          "automaticFollowUpAllowed", "contentPersisted", "destination", "kind",
          "modelToolAllowed", "networkUsed", "normalizedQuery", "queryPersisted",
          "schemaVersion", "status",
        ])
        || result.schemaVersion !== 1
        || result.kind !== "external-web-search-navigation"
        || result.status !== "approved"
        || !isTrustedCitationText(result.normalizedQuery, 256)
        || !isApprovedWebSearchDestination(result.destination, result.normalizedQuery)
        || result.networkUsed !== false
        || result.queryPersisted !== false
        || result.contentPersisted !== false
        || result.modelToolAllowed !== false
        || result.automaticFollowUpAllowed !== false
      ) throw new Error("invalid-research-web-result");
      const link = byId("research-web-link");
      link.href = result.destination;
      link.classList.remove("hidden");
      status.textContent = "Approved. Choose Open approved web search to view results in a new browser tab. Haven 42 will not read or save those pages.";
      link.focus({ preventScroll: true });
    } else renderResearchPageResult(result);
  } catch (error) {
    status.dataset.state = "error";
    status.textContent = humanError(error);
    byId("research-open-troubleshooting").classList.remove("hidden");
  } finally {
    if (execution.kind === "general-web") byId("research-api-key").value = "";
    byId("research-tools").removeAttribute("aria-busy");
  }
}

async function prepareResearchPage(citationId, returnFocus) {
  const status = byId("research-query-status");
  status.removeAttribute("data-state");
  status.textContent = "Preparing an exact page request for review…";
  try {
    const preparation = validateResearchPreparation(
      await api("/api/research/page/prepare", {
        resultId: state.researchResultId,
        citationId,
      }),
      "page",
    );
    if (!openResearchApprovalReview(
      preparation.review,
      returnFocus,
      { kind: "page", approvalToken: preparation.approvalToken },
    ).opened) throw new Error("research-review-unavailable");
  } catch (error) {
    status.dataset.state = "error";
    status.textContent = humanError(error);
  }
}

byId("research-query-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = byId("research-query").value.trim();
  const source = byId("research-source").value;
  const button = byId("research-query-button");
  const status = byId("research-query-status");
  if (!query) return;
  button.disabled = true;
  status.removeAttribute("data-state");
  status.textContent = "Preparing the exact search words for review…";
  try {
    const preparation = validateResearchPreparation(
      source === "web"
        ? await api("/api/research/web/prepare", { query })
        : source === "general-web"
          ? await api("/api/research/general/prepare", {
            query,
            apiKey: byId("research-api-key").value,
            model: selectedModel("general.chat"),
          })
          : await api("/api/research/query/prepare", { query, resultLimit: 5 }),
      source === "web" ? "web" : source === "general-web" ? "general-web" : "query",
    );
    if (!openResearchApprovalReview(
      preparation.review,
      button,
      { kind: source === "web" ? "web" : source === "general-web" ? "general-web" : "query", approvalToken: preparation.approvalToken },
    ).opened) throw new Error("research-review-unavailable");
  } catch (error) {
    status.dataset.state = "error";
    status.textContent = humanError(error);
  } finally {
    button.disabled = false;
  }
});
byId("research-source").addEventListener("change", () => {
  state.researchResultId = null;
  byId("research-result-list").replaceChildren();
  byId("research-results").classList.add("hidden");
  byId("research-page").classList.add("hidden");
  byId("research-answer-claims").replaceChildren();
  byId("research-answer").classList.add("hidden");
  byId("research-web-link").href = "about:blank";
  byId("research-web-link").classList.add("hidden");
  byId("research-query-status").textContent = "";
  byId("research-open-troubleshooting").classList.add("hidden");
  const general = byId("research-source").value === "general-web";
  byId("research-api-key-row").classList.toggle("hidden", !general);
  byId("research-api-key-help").classList.toggle("hidden", !general);
  byId("research-api-key").required = general;
});
byId("research-web-link").addEventListener("click", () => {
  byId("research-tools").open = false;
});

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

const SAFE_CONTEXT_FILE_PUNCTUATION = new Set([..."._ ()-#'’&,+–—"]);

function validContextFileName(name) {
  if (typeof name !== "string") return false;
  const characters = [...name];
  return characters.length >= 1
    && characters.length <= 120
    && /^[\p{L}\p{N}]$/u.test(characters[0])
    && name !== "."
    && name !== ".."
    && !name.includes("/")
    && !name.includes("\\")
    && characters.every((character) => (
      /^[\p{L}\p{M}\p{N}]$/u.test(character)
      || SAFE_CONTEXT_FILE_PUNCTUATION.has(character)
    ));
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
    if (!validContextFileName(file.name)) {
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
  if (state.pendingAnswerReport) closeAnswerReport(false);
  state.messages = [];
  state.approvedTextRequest = null;
  hideModelSwitchPrompt();
  clearPromptHistory();
  clearContextFiles();
  clearResearchWorkspace();
  resetContextImageLimit();
  const capability = CAPABILITIES[state.capabilityId];
  const messages = byId("messages");
  state.chatAutoFollow = true;
  messages.replaceChildren();
  addMessage("assistant", capability.welcome, "Haven 42");
  byId("prompt").value = "";
  byId("run-details").classList.add("hidden");
  byId("run-details-list").replaceChildren();
  byId("text-status").textContent = state.connected ? "Ready · nothing saved" : "AI not connected";
}

async function connectProvider(endpoint, timeoutSeconds, idleUnloadSeconds, authMode, apiKey) {
  const result = await api("/api/connect", {
    endpoint,
    timeoutSeconds,
    idleUnloadSeconds,
    authentication: { mode: authMode, apiKey },
  });
  return applyProviderConnection(result, endpoint, timeoutSeconds, idleUnloadSeconds);
}

function applyProviderConnection(result, endpoint, timeoutSeconds, idleUnloadSeconds, resetConversation = true) {
  if (
    !Array.isArray(result.models)
    || !Array.isArray(result.modelOptions)
    || !Array.isArray(result.manualModelCandidates)
    || result.models.length > MAX_DISCOVERED_MODELS
    || result.modelOptions.length > MAX_DISCOVERED_MODELS
    || result.manualModelCandidates.length > MAX_DISCOVERED_MODELS
  ) throw new Error("invalid-provider-model-catalog");
  const candidateNames = new Set();
  result.manualModelCandidates.forEach((item) => {
    if (
      !item
      || typeof item !== "object"
      || Array.isArray(item)
      || Object.keys(item).sort().join(",") !== [
        "automatic", "capabilityStatus", "downloadRequiresApproval", "hardwareFit",
        "minimumOllamaVersion", "name", "profileId", "recommended",
      ].sort().join(",")
      || !/^[A-Za-z0-9][A-Za-z0-9._/:+-]{0,255}$/.test(item.name)
      || candidateNames.has(item.name)
      || item.automatic !== item.recommended
      || typeof item.recommended !== "boolean"
      || item.downloadRequiresApproval !== true
      || item.hardwareFit !== "matched-tested-hardware-profile"
      || !/^[a-z0-9][a-z0-9-]{0,79}$/.test(item.profileId)
      || !/^[0-9]+(?:\.[0-9]+){1,3}$/.test(item.minimumOllamaVersion)
      || !item.capabilityStatus
      || Object.keys(item.capabilityStatus).sort().join(",") !== Object.keys(CAPABILITIES).sort().join(",")
      || Object.values(item.capabilityStatus).some((status) => status !== "validated-on-matching-hardware")
    ) throw new Error("invalid-provider-model-catalog");
    candidateNames.add(item.name);
  });
  if (
    !result.authentication
    || Object.keys(result.authentication).sort().join(",") !== "configured,mode,persisted"
    || !["none", "bearer", "x-api-key"].includes(result.authentication.mode)
    || typeof result.authentication.configured !== "boolean"
    || result.authentication.persisted !== false
  ) throw new Error("invalid-provider-authentication-status");
  state.connected = true;
  state.testedModelRequestId += 1;
  state.testedModelOptions = [];
  state.testedModelCatalog = null;
  state.providerTrustScope = result.trustScope;
  state.providerTransportScheme = result.transportScheme;
  renderProviderTransportWarning(result.trustScope, result.transportScheme);
  state.recommendations = result.recommendations || {};
  state.modelOptions = result.modelOptions || [];
  state.qualifiedModelCandidates = result.manualModelCandidates || [];
  const hardwareDefault = state.qualifiedModelCandidates.find((item) => item.recommended);
  if (
    hardwareDefault
    && !state.modelOptions.some((item) => item.name === hardwareDefault.name)
    && !state.desiredModel
  ) {
    state.desiredModel = {
      ...hardwareDefault,
      status: "not-installed",
      validationStatus: "validated-on-matching-hardware",
      installCommand: `ollama pull ${hardwareDefault.name}`,
    };
  }
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
    ) || selection.mode === "none") {
      state.modelSelections[capabilityId] = {
        mode: state.recommendations[capabilityId]?.automatic ? "automatic" : "none",
        model: null,
      };
    }
  }
  renderModelSelect();
  renderModelDiscovery();
  void loadHardwareMatchedModels();
  const badge = byId("connection-badge");
  const location = result.trustScope === "loopback" ? "this computer" : "private network";
  const authenticationLabel = result.authentication.configured ? " · authenticated" : "";
  badge.textContent = `Connected · ${location}${authenticationLabel} · Ollama ${result.version}`;
  badge.classList.add("good");
  byId("endpoint").value = endpoint;
  byId("wizard-endpoint").value = endpoint;
  byId("timeout").value = String(timeoutSeconds);
  byId("wizard-timeout").value = String(timeoutSeconds);
  byId("idle-unload").value = String(idleUnloadSeconds);
  byId("wizard-idle-unload").value = String(idleUnloadSeconds);
  byId("system-idle-unload").value = String(idleUnloadSeconds);
  byId("auth-mode").value = result.authentication.mode;
  byId("wizard-auth-mode").value = result.authentication.mode;
  byId("api-key").value = "";
  byId("wizard-api-key").value = "";
  state.idleUnloadSeconds = idleUnloadSeconds;
  state.providerConfig = {
    endpoint, timeoutSeconds, idleUnloadSeconds, authMode: result.authentication.mode,
  };
  updateProviderAuthenticationControl();
  updateProviderAuthenticationControl("wizard-");
  updateProviderConnectionControl();
  updateWizardConnectionControl();
  updateCleanupPolicyControl();
  if (resetConversation) resetTask();
  byId("text-status").textContent = `${result.models.length} installed model${result.models.length === 1 ? "" : "s"} found`;
  byId("cleanup-status").textContent = cleanupPolicyLabel(result.idleUnloadSeconds);
  byId("health-badge").textContent = "Healthy";
  byId("health-badge").classList.add("good");
  byId("provider-health").textContent = result.providerHealth.status === "healthy"
    ? `Working · ${location}`
    : "Needs attention";
  byId("evidence-status").textContent = result.evidenceBoundary.catalogStatus === "ready"
    ? "Recommended model information found"
    : "Model information unavailable";
  byId("digest-status").textContent = result.evidenceBoundary.immutableDigestBound
    ? "Files verified"
    : "Not checked yet";
  return result;
}

async function bootstrap() {
  try {
    const response = await fetch("/api/bootstrap", { credentials: "same-origin" });
    if (!response.ok) throw new Error("bootstrap-failed");
    const result = await response.json();
    state.token = result.sessionToken;
    maintainBrowserLifecycle();
    state.alphaTextOnly = result.alpha?.textOnly === true;
    state.appVersion = result.version;
    state.platformFamily = result.runtime.platform;
    byId("brand-version").textContent = `${result.alpha?.label || `Haven 42 ${result.version}`} · private AI on your computer`;
    byId("app-version").textContent = `v${result.version}`;
    byId("about-version").textContent = `v${result.version}`;
    const runtimeBuild = Number.isSafeInteger(result.runtime.buildNumber)
      ? ` · build ${result.runtime.buildNumber}`
      : "";
    const architecture = result.runtime.architecture === "amd64"
      ? "64-bit"
      : result.runtime.architecture;
    byId("host-status").textContent = `${result.runtime.productName}${runtimeBuild} · ${architecture}`;
    state.capabilities = (result.capabilities || []).filter((item) => (
      !state.alphaTextOnly || Object.hasOwn(CAPABILITIES, item.id)
    ));
    renderCapabilities();
    let providerConnected = false;
    if (result.alpha?.managedSetupCompletedCandidate === true) {
      try {
        const managed = await api("/api/alpha/connect-managed-provider", {});
        validateManagedProviderResume(managed);
        applyProviderConnection(managed, managed.managedResume.endpoint, 120, 300);
        providerConnected = true;
        byId("setup-wizard").classList.add("hidden");
      } catch (_error) {
        byId("wizard-description").textContent = "Haven 42 found local setup data but could not safely verify and start it. Guided setup will explain what needs attention; no replacement files were downloaded.";
      }
    }
    if (!providerConnected && result.provider?.connected === true) {
      try {
        const resumed = await api("/api/resume-provider", {});
        if (
          resumed.sessionResume !== true
          || resumed.configurationPersisted !== false
          || typeof resumed.endpoint !== "string"
          || !Number.isSafeInteger(resumed.timeoutSeconds)
        ) throw new Error("invalid-provider-session-resume");
        applyProviderConnection(
          resumed,
          resumed.endpoint,
          resumed.timeoutSeconds,
          resumed.idleUnloadSeconds,
        );
        providerConnected = true;
        byId("setup-wizard").classList.add("hidden");
      } catch (error) {
        byId("wizard-description").textContent = `Haven 42 remembered an AI connection for this running session but could not verify that it still works. Setup is shown so you can reconnect safely. ${humanError(error)}`;
      }
    }
    if (!state.alphaTextOnly) await loadWorkflows();
    try {
      await loadAssurance();
    } catch (_error) {
      renderAssuranceUnavailable();
    }
    byId("update-status").textContent = result.updates?.mode === "user-initiated-only"
      ? "Only when you choose Check now"
      : "Unavailable";
    if (!providerConnected) {
      state.lastFocusBeforeWizard = document.activeElement;
      byId("setup-wizard").querySelector(".wizard-card").focus();
    } else {
      restoreLastSection();
    }
    await refreshAlphaMetrics();
    await refreshManagedStorageStatus();
    try {
      await refreshDiagnostics();
    } catch (_error) {
      byId("diagnostics-status").textContent = "Troubleshooting events are unavailable. Haven 42 will continue without recording them.";
    }
    window.setInterval(refreshAlphaMetrics, 2000);
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
  if (!wasConnected) setProviderReady(false);
  button.textContent = "Checking…";
  try {
    await connectProvider(
      requestedConfig.endpoint,
      requestedConfig.timeoutSeconds,
      requestedConfig.idleUnloadSeconds,
      requestedConfig.authMode,
      requestedConfig.apiKey,
    );
    openChat();
  } catch (error) {
    if (!wasConnected) {
      state.connected = false;
      state.providerConfig = null;
      setProviderReady(false);
    }
    if (!wasConnected && error.message === "ollama-connection-failed") {
      byId("connection-badge").textContent = "Not connected";
      byId("connection-badge").classList.remove("good");
      byId("prompt").placeholder = "Reconnect Ollama to begin…";
      byId("text-status").textContent = "AI not connected";
    }
    showError(humanError(error), "endpoint");
  } finally {
    updateProviderConnectionControl();
  }
});

["endpoint", "timeout", "idle-unload", "auth-mode", "api-key"].forEach((id) => {
  const eventName = ["endpoint", "api-key"].includes(id) ? "input" : "change";
  byId(id).addEventListener(eventName, () => {
    if (id === "endpoint") {
      byId("endpoint").removeAttribute("aria-invalid");
      byId("connection-error").classList.add("hidden");
    }
    if (["endpoint", "auth-mode"].includes(id)) updateProviderAuthenticationControl();
    updateProviderConnectionControl();
  });
});

["wizard-endpoint", "wizard-timeout", "wizard-idle-unload", "wizard-auth-mode", "wizard-api-key"].forEach((id) => {
  const eventName = ["wizard-endpoint", "wizard-api-key"].includes(id) ? "input" : "change";
  byId(id).addEventListener(eventName, () => {
    if (id === "wizard-endpoint") {
      byId("wizard-endpoint").removeAttribute("aria-invalid");
      byId("wizard-error").classList.add("hidden");
    }
    if (["wizard-endpoint", "wizard-auth-mode"].includes(id)) {
      updateProviderAuthenticationControl("wizard-");
    }
    updateWizardConnectionControl();
  });
});

byId("api-key-visibility").addEventListener("click", () => {
  togglePasswordVisibility("api-key", "api-key-visibility");
});
byId("wizard-api-key-visibility").addEventListener("click", () => {
  togglePasswordVisibility("wizard-api-key", "wizard-api-key-visibility");
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
      state.providerConfig.authMode,
      "",
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
byId("install-model-button").addEventListener("click", () => { void prepareModelInstall(); });
byId("model-install-review-close").addEventListener("click", closeModelInstallReview);
byId("model-install-review-cancel").addEventListener("click", closeModelInstallReview);
byId("model-install-review-approve").addEventListener("click", (event) => {
  if (!event.isTrusted) {
    byId("model-install-review-status").textContent = "Approval requires a direct user action.";
    return;
  }
  void executeModelInstall();
});
byId("model-install-review-layer").addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    event.preventDefault();
    closeModelInstallReview();
    return;
  }
  if (event.key !== "Tab") return;
  const controls = [...byId("model-install-review-dialog").querySelectorAll(
    'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
  )];
  if (controls.length === 0) return;
  const first = controls[0];
  const last = controls[controls.length - 1];
  if (event.shiftKey && [first, byId("model-install-review-dialog")].includes(document.activeElement)) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
});

byId("text-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  const prompt = byId("prompt");
  const content = prompt.value.trim();
  if (!content || !state.connected) return;
  clearResearchWorkspace();
  const capabilityId = suggestedCapability(content);
  const capability = CAPABILITIES[capabilityId];
  const automaticMode = byId("text-mode").value === "automatic";
  const currentModel = selectedModel(automaticMode ? "general.chat" : capabilityId);
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
      automaticMode
      && capabilityId !== "general.chat"
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
  const stop = byId("stop-generation");
  const requestId = crypto.randomUUID().replaceAll("-", "").toLowerCase();
  const execution = { requestId, cancelRequested: false };
  state.activeTextExecution = execution;
  send.disabled = true;
  send.classList.add("hidden");
  stop.disabled = false;
  stop.textContent = "Stop";
  stop.classList.remove("hidden");
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
      requestId,
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
    const wasCancelled = execution.cancelRequested || displayedError.message === "text-request-cancelled";
    if (wasCancelled) clearError();
    else showError(humanError(displayedError));
    focusPrompt = false;
    const retry = recovery?.retryAllowed === true
      ? " · input restored; retry creates a new request"
      : " · input restored for review";
    setTaskEvent(
      wasCancelled ? "Generation stopped · message restored" : `${humanError(displayedError)}${retry}`,
      wasCancelled ? "warning" : "error",
    );
    byId("text-status").textContent = wasCancelled ? "Generation stopped" : "Text request failed";
  } finally {
    if (state.activeTextExecution === execution) state.activeTextExecution = null;
    stop.classList.add("hidden");
    stop.disabled = false;
    stop.textContent = "Stop";
    send.classList.remove("hidden");
    send.disabled = false;
    prompt.disabled = false;
    setTaskControlsDisabled(false);
    if (focusPrompt) prompt.focus();
  }
});

byId("stop-generation").addEventListener("click", async () => {
  const execution = state.activeTextExecution;
  if (!execution || execution.cancelRequested) return;
  execution.cancelRequested = true;
  const stop = byId("stop-generation");
  stop.disabled = true;
  stop.textContent = "Stopping…";
  setTaskEvent("Stopping generation and unloading the active model…");
  try {
    const result = await api("/api/text/cancel", { requestId: execution.requestId });
    if (!result.cancelAccepted && !result.alreadyComplete) throw new Error("invalid-server-response");
  } catch (error) {
    execution.cancelRequested = false;
    stop.disabled = false;
    stop.textContent = "Stop";
    showError(humanError(error));
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
  if (value.startsWith("candidate:")) {
    const model = value.slice("candidate:".length);
    const candidate = state.qualifiedModelCandidates.find((item) => item.name === model)
      || state.testedModelOptions.find((item) => item.name === model);
    renderModelSelect();
    if (!candidate) return;
    byId("conversation-settings").open = false;
    byId("model-search-capability").value = state.capabilityId;
    openModels();
    chooseDiscoveredModel({
      ...candidate,
      status: "not-installed",
      validationStatus: "validated-on-matching-hardware",
      installCommand: `ollama pull ${candidate.name}`,
    });
    return;
  }
  state.modelSelections[state.capabilityId] = value === "automatic"
    ? { mode: "automatic", model: null }
    : { mode: "manual", model: value.slice("manual:".length) };
  clearPromptHistory();
  clearContextFiles();
  renderModelSelect();
});
byId("text-mode").addEventListener("change", () => {
  hideModelSwitchPrompt();
  state.approvedTextRequest = null;
  renderTextMode();
});
byId("text-mode-button").addEventListener("click", () => {
  if (byId("text-mode-button").getAttribute("aria-expanded") === "true") {
    closeTaskModePicker({ restoreFocus: true });
  } else {
    openTaskModePicker();
  }
});
byId("text-mode-button").addEventListener("keydown", (event) => {
  if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  openTaskModePicker();
  const options = taskModeOptions();
  (event.key === "ArrowUp" || event.key === "End" ? options.at(-1) : options[0])?.focus();
});
byId("text-mode-options").addEventListener("click", (event) => {
  const option = event.target.closest(".task-mode-option");
  if (option) chooseTaskMode(option.dataset.value);
});
byId("text-mode-options").addEventListener("keydown", (event) => {
  const options = taskModeOptions();
  const current = options.indexOf(document.activeElement);
  if (event.key === "Escape") {
    event.preventDefault();
    event.stopPropagation();
    closeTaskModePicker({ restoreFocus: true });
    return;
  }
  if (event.key === "Tab") {
    closeTaskModePicker();
    return;
  }
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    chooseTaskMode(document.activeElement?.dataset.value);
    return;
  }
  if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  const next = event.key === "Home" ? 0
    : event.key === "End" ? options.length - 1
      : event.key === "ArrowDown" ? (current + 1) % options.length
        : (current - 1 + options.length) % options.length;
  options[next]?.focus();
});
document.addEventListener("pointerdown", (event) => {
  if (!event.target.closest(".task-mode-picker")) closeTaskModePicker();
});
byId("reset-model-button").addEventListener("click", () => {
  state.modelSelections[state.capabilityId] = { mode: "automatic", model: null };
  clearPromptHistory();
  clearContextFiles();
  renderModelSelect();
});
byId("new-task-button").addEventListener("click", async () => {
  byId("conversation-settings").open = false;
  setTaskControlsDisabled(true);
  let cleanupStatus = "";
  try {
    if (state.connected) {
      const result = await api("/api/unload", {});
      cleanupStatus = result.modelUnloaded
        ? "New task · active model unloaded"
        : "New task · model cleanup needs attention";
    }
    await Promise.all([
      api("/api/alpha/session-reset", {}),
      api("/api/research/clear", {}),
    ]);
    byId("alpha-tokens").textContent = "0";
    byId("alpha-speed").textContent = "Waiting";
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
  openChat();
  window.scrollTo({ top: 0, behavior: motionBehavior() });
});
byId("messages").addEventListener("scroll", () => {
  const messages = byId("messages");
  state.chatAutoFollow = messages.scrollHeight - messages.scrollTop - messages.clientHeight < 48;
}, { passive: true });
byId("conversation-settings").addEventListener("toggle", () => {
  const open = byId("conversation-settings").open;
  const trigger = byId("conversation-settings-trigger");
  trigger.setAttribute("aria-expanded", String(open));
  trigger.setAttribute("aria-label", `${open ? "Close" : "Open"} conversation settings`);
});
document.addEventListener("pointerdown", (event) => {
  const settings = byId("conversation-settings");
  if (settings.open && !settings.contains(event.target)) settings.open = false;
});
document.addEventListener("keydown", (event) => {
  const settings = byId("conversation-settings");
  if (event.key !== "Escape" || !settings.open) return;
  event.preventDefault();
  settings.open = false;
  byId("conversation-settings-trigger").focus({ preventScroll: true });
});
byId("software-nav").addEventListener("click", openSoftware);
byId("image-nav").addEventListener("click", openImages);
byId("models-nav").addEventListener("click", openModels);
byId("open-models-from-chat").addEventListener("click", () => {
  byId("conversation-settings").open = false;
  openModels();
});
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
  openSystem();
});
byId("view-system-details").addEventListener("click", openSystem);
byId("energy-measurement-profile").addEventListener("change", updateEnergyMeasurement);
byId("energy-rate-source").addEventListener("change", updateEnergyRateControls);
byId("energy-pin-status").addEventListener("change", syncEnergyStatusWidget);
byId("status-energy-remove").addEventListener("click", () => {
  byId("energy-pin-status").checked = false;
  syncEnergyStatusWidget();
  byId("view-system-details").focus();
});
for (const id of ["energy-country", "energy-region", "energy-currency"]) {
  byId(id).addEventListener("input", () => {
    if (id === "energy-country") applyCountryCurrency();
    if (byId("energy-rate-source").value !== "manual") {
      state.electricityRateProfile = null;
      byId("energy-rate").value = "";
      byId("energy-estimate-result").classList.add("hidden");
    }
  });
}
byId("fetch-official-rate").addEventListener("click", () => { void fetchOfficialElectricityRate(); });
byId("energy-estimator-form").addEventListener("submit", calculateElectricityEstimate);
byId("diagnostics-control").addEventListener("toggle", () => {
  if (byId("diagnostics-control").open) void refreshDiagnosticsQuietly();
});
byId("open-diagnostics").addEventListener("click", () => { void openTroubleshootingLogs(); });
byId("research-open-troubleshooting").addEventListener("click", () => { void openTroubleshootingLogs(); });

byId("prepare-problem-report").addEventListener("click", () => {
  void prepareProblemReport();
});
document.querySelectorAll(".availability-nav").forEach((button) => {
  button.addEventListener("click", () => {
    openSystem();
    byId("capability-panel").scrollIntoView({ behavior: motionBehavior() });
  });
});

byId("wizard-guided").addEventListener("click", runReadiness);
byId("wizard-existing").addEventListener("click", () => {
  showWizardStep("provider");
  byId("wizard-endpoint").focus();
});
byId("wizard-provider-back").addEventListener("click", () => {
  showWizardStep(state.readinessSnapshot ? "readiness" : "welcome");
});
byId("wizard-explore").addEventListener("click", () => {
  byId("setup-wizard").classList.add("hidden");
  byId("welcome-message").textContent = "You can look through Chat, Models, System, and About. When you are ready, use Setup to connect an AI server.";
  openSystem();
  byId("connection-panel").scrollIntoView({ behavior: motionBehavior() });
});
byId("wizard-readiness-back").addEventListener("click", () => {
  if (state.localSetupReturnToChat) {
    state.localSetupReturnToChat = false;
    byId("setup-wizard").classList.add("hidden");
    byId("setup-local-components").focus();
    return;
  }
  showWizardStep("welcome");
});
byId("wizard-readiness-next").addEventListener("click", async () => {
  if (state.connected) {
    byId("setup-wizard").classList.add("hidden");
    openChat();
    return;
  }
  const macosApproval = byId("macos-installed-ollama-approval");
  if (macosApproval) {
    const approvalPanel = byId("macos-installed-ollama-approval");
    const consent = approvalPanel?.querySelector('.setup-consent input[type="checkbox"]');
    const actionStatus = byId("macos-installed-ollama-action-status");
    if (!approvalPanel || !consent || !actionStatus) {
      byId("wizard-scan-status").textContent = "The local AI review could not be opened. Check this computer again, then retry.";
      return;
    }
    revealMacOSInstalledOllamaApproval(approvalPanel, consent, actionStatus);
    return;
  }
  if (
    state.setupPlan?.alphaCandidate?.managedSetupCandidateAvailable === true
    && state.setupPlan?.alphaCandidate?.managedPlan
  ) {
    byId("wizard-scan-status").textContent = "Finish the local setup above. Haven 42 will open chat automatically after it checks and starts the local AI.";
    byId("alpha-setup-review")?.focus();
    return;
  }
  if (state.platformFamily === "macos") {
    const button = byId("wizard-readiness-next");
    button.disabled = true;
    button.textContent = "Checking Ollama…";
    byId("wizard-scan-status").textContent = "Checking for Ollama on this Mac. No files or settings are changed.";
    try {
      await connectProvider("http://127.0.0.1:11434", 120, 300, "none", "");
      if (await offerRecommendedModelDuringSetup()) {
        byId("wizard-scan-status").textContent = "Haven 42 selected the best tested model for this computer. Review and approve its download; it will be selected automatically when verification finishes.";
        return;
      }
      renderWizardReadiness();
      showWizardStep("ready");
    } catch (_error) {
      byId("wizard-scan-status").textContent = "Ollama is not running yet. Install and open Ollama, then check again. Haven 42 made no changes.";
      button.disabled = false;
      button.textContent = "I've installed Ollama — check again";
    }
    return;
  }
  byId("wizard-scan-status").textContent = "Local setup is not ready, so Haven 42 will not continue. Review the explanation above, or go Back and choose the advanced external-server option.";
});
byId("scan-system-button").addEventListener("click", async () => {
  const button = byId("scan-system-button");
  button.disabled = true;
  button.textContent = "Checking…";
  try {
    const snapshot = await api("/api/readiness", { force: true });
    state.readinessSnapshot = snapshot;
    renderSystemReadiness("system-readiness", snapshot);
    button.textContent = "Check again";
  } catch (error) {
    showError(humanError(error));
    button.textContent = "Check this computer";
  } finally {
    button.disabled = false;
    await refreshDiagnosticsQuietly();
  }
});

function validateSoftwareUpdateCheck(value) {
  if (
    !value || value.schemaVersion !== 1
    || value.kind !== "haven42-managed-software-update-check"
    || value.checkedBecauseUserRequested !== true
    || value.automaticChecksEnabled !== false
    || value.configurationPersisted !== false
    || value.userContentSent !== false
    || !Array.isArray(value.components) || value.components.length !== 1
  ) throw new Error("invalid-software-update-check");
  const component = value.components[0];
  if (
    component.id !== "ollama-runtime"
    || component.displayName !== "Ollama local AI engine"
    || !/^\d+\.\d+\.\d+$/.test(component.managedVersion)
    || !/^\d+\.\d+\.\d+$/.test(component.latestStableVersion)
    || typeof component.newerOfficialVersionAvailable !== "boolean"
    || typeof component.managedVersionIsLatest !== "boolean"
    || typeof component.availableForManagedSetup !== "boolean"
    || !["certified", "official-unverified"].includes(component.certificationStatus)
    || !Number.isSafeInteger(component.downloadBytes)
    || component.downloadBytes < 1 || component.downloadBytes > 4 * 1024 ** 3
    || !/^[a-f0-9]{64}$/.test(component.sha256)
    || component.releaseUrl !== `https://github.com/ollama/ollama/releases/tag/v${component.latestStableVersion}`
    || component.downloadUrl !== `https://github.com/ollama/ollama/releases/download/v${component.latestStableVersion}/${component.artifactName}`
  ) throw new Error("invalid-software-update-component");
  return { component, runtimeStatus: validateRuntimeUpdateStatus(value.runtimeStatus) };
}

function validateRuntimeUpdateStatus(value) {
  if (
    !value || value.schemaVersion !== 1
    || value.kind !== "haven42-managed-runtime-update-status"
    || !/^\d+\.\d+\.\d+$/.test(value.activeVersion)
    || !/^\d+\.\d+\.\d+$/.test(value.certifiedVersion)
    || !["certified", "official-unverified"].includes(value.activeCertificationStatus)
    || typeof value.rollbackAvailable !== "boolean"
    || typeof value.updateInProgress !== "boolean"
    || !["idle", "starting", "downloading", "extracting", "validating", "complete", "failed"].includes(value.phase)
    || !Number.isSafeInteger(value.progressPercent) || value.progressPercent < 0 || value.progressPercent > 100
    || (value.error !== null && typeof value.error !== "string")
    || (value.targetVersion !== null && !/^\d+\.\d+\.\d+$/.test(value.targetVersion))
    || (value.targetCertification !== null && !["certified", "official-unverified"].includes(value.targetCertification))
    || typeof value.rollbackPerformed !== "boolean"
  ) throw new Error("invalid-runtime-update-status");
  return value;
}

let checkedSoftwareUpdate = null;
let pendingSoftwareUpdatePlan = null;
let softwareUpdatePoll = null;

function refreshSoftwareUpdateChoice() {
  const updateButton = byId("use-software-update");
  if (!checkedSoftwareUpdate) {
    updateButton.disabled = true;
    updateButton.textContent = "Check releases first";
    return;
  }
  const { component, runtimeStatus } = checkedSoftwareUpdate;
  const latest = byId("software-update-preference").value === "latest";
  if (latest) {
    updateButton.dataset.target = "latest-official";
    updateButton.textContent = `Review and install Ollama ${component.latestStableVersion}`;
    updateButton.disabled = (
      runtimeStatus.activeVersion === component.latestStableVersion
      || (!component.newerOfficialVersionAvailable && !component.managedVersionIsLatest)
    );
  } else {
    updateButton.dataset.target = "certified";
    updateButton.textContent = runtimeStatus.rollbackAvailable
      ? `Review restore to certified Ollama ${runtimeStatus.certifiedVersion}`
      : `Certified Ollama ${runtimeStatus.certifiedVersion} is active`;
    updateButton.disabled = !runtimeStatus.rollbackAvailable;
  }
  byId("rollback-certified-runtime").classList.toggle("hidden", !runtimeStatus.rollbackAvailable);
}

byId("software-update-preference").addEventListener("change", refreshSoftwareUpdateChoice);

byId("check-software-updates").addEventListener("click", async () => {
  const button = byId("check-software-updates");
  const updateButton = byId("use-software-update");
  const result = byId("software-update-result");
  const releaseLink = byId("software-update-release-link");
  button.disabled = true;
  button.textContent = "Checking official release…";
  updateButton.disabled = true;
  updateButton.textContent = "Checking official releases…";
  updateButton.dataset.available = "false";
  releaseLink.classList.add("hidden");
  result.textContent = "Contacting Ollama's official GitHub release service…";
  try {
    checkedSoftwareUpdate = validateSoftwareUpdateCheck(
      await api("/api/software-updates/check", { confirmed: true }),
    );
    const { component, runtimeStatus } = checkedSoftwareUpdate;
    releaseLink.href = component.releaseUrl;
    releaseLink.textContent = `View the official Ollama ${component.latestStableVersion} release page`;
    releaseLink.classList.remove("hidden");
    byId("update-status").textContent = `Checked · Ollama ${component.latestStableVersion}`;
    if (component.newerOfficialVersionAvailable) {
      result.textContent = `Ollama ${component.latestStableVersion} is the newest official stable release. Haven 42 has certified ${component.managedVersion}. You may install the newer release after reviewing the compatibility warning; the certified version remains available for rollback.`;
    } else if (component.managedVersionIsLatest) {
      result.textContent = `Ollama ${component.managedVersion} is both the newest official stable release and the latest version certified by Haven 42.`;
    } else {
      result.textContent = `Haven 42 has certified Ollama ${component.managedVersion}, which is newer than the official stable release currently reported. Haven 42 will not offer an automatic downgrade.`;
    }
    if (runtimeStatus.activeCertificationStatus === "official-unverified") {
      result.textContent += ` This computer is currently using unverified Ollama ${runtimeStatus.activeVersion}.`;
    }
    refreshSoftwareUpdateChoice();
  } catch (error) {
    result.textContent = `The official release could not be verified. Nothing was downloaded or changed. ${humanError(error)}`;
    updateButton.textContent = "Release check unavailable";
    byId("update-status").textContent = "Check failed · no changes";
  } finally {
    button.disabled = false;
    button.textContent = "Check official releases again";
    await refreshDiagnosticsQuietly();
  }
});

byId("use-software-update").addEventListener("click", () => {
  if (byId("use-software-update").disabled) return;
  prepareSoftwareRuntimeChange(byId("use-software-update").dataset.target);
});

async function prepareSoftwareRuntimeChange(target) {
  const result = byId("software-update-result");
  try {
    const plan = await api("/api/software-updates/prepare", { target });
    if (
      !plan || plan.schemaVersion !== 1 || plan.kind !== "haven42-managed-runtime-update-plan"
      || typeof plan.planId !== "string" || !["latest-official", "certified"].includes(plan.target)
      || !/^\d+\.\d+\.\d+$/.test(plan.version)
      || !["certified", "official-unverified"].includes(plan.certificationStatus)
      || !Array.isArray(plan.effects) || plan.effects.length !== 4
      || plan.approvalRequired !== true || plan.modelsAndUserDataKept !== true
    ) throw new Error("invalid-runtime-update-plan");
    pendingSoftwareUpdatePlan = plan;
    byId("software-update-review-title").textContent = plan.target === "certified"
      ? `Restore certified Ollama ${plan.version}` : `Install Ollama ${plan.version}`;
    byId("software-update-review-summary").textContent = plan.target === "certified"
      ? "Haven 42 will stop its local AI, select the retained certified runtime, verify it, and start local AI again. Models and user data stay in place."
      : `Haven 42 will download ${formatBytes(plan.downloadBytes)} from Ollama's official release, verify its published digest, install it beside the certified runtime, and test startup before activation.`;
    const warning = byId("software-update-review-warning");
    warning.textContent = plan.warning || "";
    warning.classList.toggle("hidden", !plan.warning);
    const consentRow = byId("software-update-unverified-consent-row");
    const consent = byId("software-update-unverified-consent");
    consent.checked = false;
    consentRow.classList.toggle("hidden", plan.certificationStatus !== "official-unverified");
    const effectLabels = {
      "download-runtime-files": "Download only the selected Ollama runtime into Haven42-Data.",
      "select-certified-runtime": "Switch back to the retained Haven 42-certified runtime.",
      "stop-and-restart-owned-local-ai": "Briefly stop and restart only the local AI process owned by Haven 42.",
      "keep-models-and-user-data": "Keep downloaded models, settings, and user data in place.",
      "retain-certified-rollback": "Keep the latest certified runtime available as a recovery option.",
    };
    byId("software-update-review-effects").replaceChildren(...plan.effects.map((effect) => {
      const item = document.createElement("li");
      item.textContent = effectLabels[effect] || effect;
      return item;
    }));
    byId("software-update-review").classList.remove("hidden");
    byId("software-update-review").focus();
    result.textContent = "Review the exact change below. Nothing has been downloaded yet.";
  } catch (error) {
    result.textContent = `The update review could not be prepared. ${humanError(error)}`;
  }
}

byId("rollback-certified-runtime").addEventListener("click", () => prepareSoftwareRuntimeChange("certified"));

byId("cancel-software-update-review").addEventListener("click", () => {
  pendingSoftwareUpdatePlan = null;
  byId("software-update-review").classList.add("hidden");
  byId("use-software-update").focus();
});

byId("confirm-software-update").addEventListener("click", async () => {
  const plan = pendingSoftwareUpdatePlan;
  if (!plan) return;
  if (plan.certificationStatus === "official-unverified" && !byId("software-update-unverified-consent").checked) {
    byId("software-update-result").textContent = "Confirm that you understand this official release has not yet been tested by Haven 42.";
    byId("software-update-unverified-consent").focus();
    return;
  }
  const button = byId("confirm-software-update");
  button.disabled = true;
  try {
    const approved = await api("/api/software-updates/approve", {
      planId: plan.planId, effects: plan.effects, confirmed: true,
    });
    if (!approved || approved.schemaVersion !== 1 || typeof approved.approvalToken !== "string") {
      throw new Error("invalid-runtime-update-approval");
    }
    const status = validateRuntimeUpdateStatus(await api("/api/software-updates/execute", {
      approvalToken: approved.approvalToken,
    }));
    byId("software-update-review").classList.add("hidden");
    pendingSoftwareUpdatePlan = null;
    renderRuntimeUpdateProgress(status);
    clearInterval(softwareUpdatePoll);
    softwareUpdatePoll = setInterval(pollRuntimeUpdate, 1000);
  } catch (error) {
    byId("software-update-result").textContent = `The update did not start. Nothing was changed. ${humanError(error)}`;
  } finally {
    button.disabled = false;
  }
});

function renderRuntimeUpdateProgress(status) {
  const shell = byId("software-update-progress-shell");
  shell.classList.remove("hidden");
  shell.setAttribute("aria-hidden", "false");
  byId("software-update-progress-bar").value = status.progressPercent;
  byId("software-update-progress-bar").textContent = `${status.progressPercent}%`;
  const labels = {
    starting: "Preparing the local AI engine change",
    downloading: "Downloading the official Ollama release",
    extracting: "Verifying and installing the runtime",
    validating: "Starting and testing local AI",
    complete: "Local AI engine change completed",
    failed: status.rollbackPerformed
      ? "The change failed; Haven 42 restored the previous working runtime"
      : "The change failed and local AI needs repair",
    idle: "Waiting to start",
  };
  byId("software-update-progress").textContent = `${labels[status.phase]} · ${status.progressPercent}%`;
}

async function pollRuntimeUpdate() {
  try {
    const status = validateRuntimeUpdateStatus(await api("/api/software-updates/status", {}));
    renderRuntimeUpdateProgress(status);
    if (!status.updateInProgress) {
      clearInterval(softwareUpdatePoll);
      softwareUpdatePoll = null;
      if (checkedSoftwareUpdate) checkedSoftwareUpdate.runtimeStatus = status;
      refreshSoftwareUpdateChoice();
      if (status.phase === "complete") {
        try {
          const refreshed = await api("/api/resume-provider", {});
          if (
            refreshed.sessionResume !== true || refreshed.configurationPersisted !== false
            || typeof refreshed.endpoint !== "string"
          ) throw new Error("invalid-provider-session-resume");
          applyProviderConnection(
            refreshed, refreshed.endpoint, refreshed.timeoutSeconds,
            refreshed.idleUnloadSeconds, false,
          );
        } catch (_error) {
          byId("software-update-result").textContent = `Ollama ${status.activeVersion} is active, but the page could not refresh its connection details. Reload Haven 42 to update every status view.`;
          return;
        }
        byId("software-update-result").textContent = `Ollama ${status.activeVersion} is active. System status, model compatibility, and connection details now use this version. Your installed models, conversation, and data were kept.`;
      } else {
        byId("software-update-result").textContent = `${byId("software-update-progress").textContent}${status.error ? ` (${status.error})` : ""}.`;
      }
    }
  } catch (error) {
    clearInterval(softwareUpdatePoll);
    softwareUpdatePoll = null;
    byId("software-update-result").textContent = `Update status could not be read. ${humanError(error)}`;
  }
}

byId("setup-local-components").addEventListener("click", async () => {
  const button = byId("setup-local-components");
  if (button.disabled) return;
  clearError();
  const actionStatus = byId("local-setup-action-status");
  if (button.dataset.action === "connect-local") {
    button.disabled = true;
    actionStatus.textContent = "Checking and starting the installed local AI…";
    try {
      const managed = validateManagedProviderResume(
        await api("/api/alpha/connect-managed-provider", {}),
      );
      applyProviderConnection(managed, managed.managedResume.endpoint, 120, 300);
      await showManagedLocalReady();
      activateNavigation("chat-nav", "capability-panel", "capability-title");
      byId("prompt").focus();
    } catch (error) {
      actionStatus.textContent = "Local AI could not start. Your current AI connection was kept unchanged. Guided setup is open so you can review or repair the local components.";
      state.localSetupReturnToChat = state.connected;
      state.lastFocusBeforeWizard = button;
      byId("setup-wizard").classList.remove("hidden");
      await runReadiness();
    } finally {
      await refreshManagedStorageStatus().catch(() => {});
    }
    return;
  }
  state.localSetupReturnToChat = state.connected;
  state.lastFocusBeforeWizard = button;
  actionStatus.textContent = state.connected
    ? "Your current AI connection will stay active unless local setup finishes successfully."
    : "Haven 42 will check this computer before asking permission to download anything.";
  byId("setup-wizard").classList.remove("hidden");
  await runReadiness();
});
byId("remove-managed-components").addEventListener("click", async () => {
  const button = byId("remove-managed-components");
  if (button.disabled) return;
  const confirmed = window.confirm(
    "Remove Haven-managed Ollama, downloaded models, and working data from this extracted folder? This cannot be undone. Drivers and other Ollama installations will not be changed.",
  );
  if (!confirmed) return;
  button.disabled = true;
  byId("portable-storage-status").textContent = "Stopping Haven-managed processes and removing components…";
  try {
    const result = await api("/api/alpha/remove-managed-components", { confirmed: true });
    if (
      result.schemaVersion !== 1 || result.kind !== "windows-alpha-managed-components-removal"
      || result.managedComponentsPresent !== false
      || typeof result.legacyManagedComponentsRemoved !== "boolean"
      || result.storageScope !== "inside-extracted-folder"
      || result.driversChanged !== false || result.servicesChanged !== false
      || result.firewallChanged !== false || result.globalRuntimeChanged !== false
      || result.applicationFilesRemoved !== false
    ) throw new Error("invalid-managed-removal-result");
    byId("portable-storage-status").textContent = result.removed
      ? "Managed components removed. Troubleshooting logs are kept separately in Haven42-Logs."
      : "No Haven-managed components were present.";
    await refreshDiagnostics();
    showPostRemovalExperience();
  } catch (error) {
    showError(humanError(error));
    await refreshManagedStorageStatus().catch(() => {});
  }
});
byId("refresh-diagnostics").addEventListener("click", async () => {
  byId("diagnostics-action-status").textContent = "Refreshing…";
  try {
    await refreshDiagnostics();
    byId("diagnostics-action-status").textContent = "Troubleshooting events refreshed.";
  } catch (error) {
    byId("diagnostics-action-status").textContent = humanError(error);
  }
});
byId("cancel-answer-report").addEventListener("click", () => closeAnswerReport());
byId("save-answer-report").addEventListener("click", async () => {
  const pending = state.pendingAnswerReport;
  if (!pending || !validAnswerReportIdentity(pending.identity)) return;
  const button = byId("save-answer-report");
  const testerNote = byId("answer-report-note").value.trim();
  button.disabled = true;
  byId("answer-report-status").textContent = "Saving a private report in Haven42-Logs…";
  try {
    const result = await api("/api/alpha/diagnostics/answer-report", {
      reportToken: pending.identity.reportToken,
      category: byId("answer-report-category").value,
      testerNote,
    });
    if (
      !result || result.saved !== true || result.directoryName !== "Haven42-Logs"
      || result.automaticUpload !== false
      || !/^answer-report-[a-f0-9]{16}\.json$/.test(result.fileName)
      || !/^[a-f0-9]{16}$/.test(result.eventReference)
      || Object.keys(result).sort().join("|") !== "automaticUpload|directoryName|eventReference|fileName|saved"
    ) throw new Error("invalid-answer-report-result");
    closeAnswerReport(false);
    setTaskEvent(`Private answer report saved as ${result.fileName} in Haven42-Logs · nothing uploaded`, "result");
    await refreshDiagnosticsQuietly();
    pending.trigger?.focus();
  } catch (error) {
    byId("answer-report-status").textContent = humanError(error);
  } finally {
    button.disabled = false;
  }
});
byId("save-support-report").addEventListener("click", async () => {
  byId("diagnostics-action-status").textContent = "Creating a private local report…";
  try {
    const result = await api("/api/alpha/diagnostics/report", {});
    if (
      !result || result.saved !== true || result.directoryName !== "Haven42-Logs"
      || !/^support-report-[a-f0-9]{16}\.json$/.test(result.fileName)
      || Object.keys(result).sort().join("|") !== "directoryName|fileName|saved"
    ) throw new Error("invalid-diagnostic-report-result");
    byId("diagnostics-action-status").textContent = `Saved ${result.fileName} in Haven42-Logs. Nothing was uploaded.`;
    await refreshDiagnostics();
  } catch (error) {
    byId("diagnostics-action-status").textContent = humanError(error);
  }
});
byId("clear-diagnostics").addEventListener("click", async () => {
  if (!window.confirm("Clear the current troubleshooting events? Saved support reports will be kept.")) return;
  try {
    const result = await api("/api/alpha/diagnostics/clear", { confirmed: true });
    if (
      !result || result.cleared !== true || result.reportsPreserved !== true
      || result.directoryName !== "Haven42-Logs"
    ) throw new Error("invalid-diagnostic-clear-result");
    await refreshDiagnostics();
    byId("diagnostics-action-status").textContent = "Troubleshooting events cleared. Saved reports were kept.";
  } catch (error) {
    byId("diagnostics-action-status").textContent = humanError(error);
  }
});
byId("remove-diagnostics").addEventListener("click", async () => {
  if (!window.confirm("Remove all troubleshooting events and saved support reports? Logging will remain off until Haven 42 is restarted.")) return;
  try {
    const result = await api("/api/alpha/diagnostics/remove", { confirmed: true });
    if (!result || result.removed !== true || result.directoryName !== "Haven42-Logs") {
      throw new Error("invalid-diagnostic-removal-result");
    }
    await refreshDiagnostics();
    byId("diagnostics-action-status").textContent = "All troubleshooting logs removed. Logging will resume after Haven 42 is restarted.";
  } catch (error) {
    byId("diagnostics-action-status").textContent = humanError(error);
  }
});
byId("removed-guided").addEventListener("click", runReadiness);
byId("removed-existing").addEventListener("click", () => showWizardStep("provider"));
byId("removed-close").addEventListener("click", async () => {
  const actions = byId("removed-actions");
  const status = byId("removed-close-status");
  actions.querySelectorAll("button").forEach((button) => { button.disabled = true; });
  status.textContent = "Closing Haven 42…";
  status.classList.remove("hidden");
  try {
    await api("/api/shutdown", {});
    state.token = "";
    actions.classList.add("hidden");
    status.textContent = "Haven 42 is closed. You can close this browser tab.";
  } catch (error) {
    actions.querySelectorAll("button").forEach((button) => { button.disabled = false; });
    status.textContent = humanError(error);
  }
});
byId("close-app-nav").addEventListener("click", async () => {
  if (!window.confirm("Close Haven 42? The local service will stop and this session will end.")) return;
  const button = byId("close-app-nav");
  button.disabled = true;
  button.textContent = "Closing Haven 42…";
  try {
    await api("/api/shutdown", {});
    state.token = "";
    document.querySelector(".shell").classList.add("hidden");
    const wizard = byId("setup-wizard");
    wizard.classList.remove("hidden");
    wizard.setAttribute("aria-labelledby", "shutdown-title");
    wizard.setAttribute("aria-describedby", "shutdown-description");
    wizard.replaceChildren();
    const panel = document.createElement("section");
    panel.className = "wizard-card";
    const title = document.createElement("h1");
    title.id = "shutdown-title";
    title.textContent = "Haven 42 is closed";
    const description = document.createElement("p");
    description.id = "shutdown-description";
    description.textContent = "The local service and any models used in this session have stopped. You can close this browser window.";
    panel.append(title, description);
    wizard.append(panel);
  } catch (error) {
    button.disabled = false;
    button.textContent = "Close Haven 42";
    window.alert(humanError(error));
  }
});
byId("wizard-connection-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const errorBox = byId("wizard-error");
  errorBox.classList.add("hidden");
  byId("wizard-endpoint").removeAttribute("aria-invalid");
  const button = byId("wizard-connect");
  const wasConnected = state.connected;
  const requestedConfig = providerFormConfig("wizard-");
  if (wasConnected && !providerConfigChanged(requestedConfig)) {
    updateWizardConnectionControl();
    if (await offerRecommendedModelDuringSetup()) return;
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
      requestedConfig.authMode,
      requestedConfig.apiKey,
    );
    byId("wizard-endpoint").removeAttribute("aria-invalid");
    if (await offerRecommendedModelDuringSetup()) return;
    renderWizardReadiness();
    showWizardStep("ready");
  } catch (error) {
    if (!wasConnected) {
      state.connected = false;
      state.providerConfig = null;
      setProviderReady(false);
    }
    errorBox.textContent = humanError(error);
    byId("wizard-endpoint").setAttribute("aria-invalid", "true");
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
  const usable = Object.values(state.recommendations).some((item) => item?.automatic === true);
  if (usable) openChat();
  else openModels();
});
byId("setup-wizard").addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    event.preventDefault();
    byId("setup-wizard").classList.add("hidden");
    const previous = state.lastFocusBeforeWizard;
    const returnTarget = previous instanceof HTMLElement
      && !previous.closest("#setup-wizard")
      && previous.matches('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')
      ? previous
      : byId("home-nav");
    returnTarget.focus({ preventScroll: true });
    const visiblePanel = Object.entries(PANEL_TOUR_SECTIONS).find(([panelId]) => !byId(panelId).classList.contains("hidden"));
    if (visiblePanel) scheduleSectionTour(visiblePanel[1]);
    return;
  }
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

document.querySelectorAll("[data-tour-section]").forEach((button) => {
  button.addEventListener("click", () => {
    startSectionTour(button.dataset.tourSection, { manual: true, returnFocus: button });
  });
});
byId("section-tour-close").addEventListener("click", finishSectionTour);
byId("section-tour-skip").addEventListener("click", finishSectionTour);
byId("section-tour-back").addEventListener("click", () => {
  if (!activeSectionTour.section || activeSectionTour.stepIndex === 0) return;
  activeSectionTour.stepIndex -= 1;
  renderSectionTourStep();
});
byId("section-tour-next").addEventListener("click", () => {
  const configuration = activeTourConfiguration();
  if (!configuration) return;
  if (activeSectionTour.stepIndex >= configuration.steps.length - 1) {
    finishSectionTour();
    return;
  }
  activeSectionTour.stepIndex += 1;
  renderSectionTourStep();
});
byId("section-tour-layer").addEventListener("keydown", (event) => {
  if (!activeSectionTour.section) return;
  if (event.key === "Escape") {
    event.preventDefault();
    finishSectionTour();
    return;
  }
  if (event.key === "Enter" && event.target === byId("section-tour-dialog")) {
    event.preventDefault();
    byId("section-tour-next").click();
    return;
  }
  if (event.key !== "Tab") return;
  const controls = [...byId("section-tour-dialog").querySelectorAll("button:not([disabled])")];
  if (controls.length === 0) return;
  const first = controls[0];
  const last = controls[controls.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
});
window.addEventListener("resize", positionSectionTour);
window.addEventListener("scroll", positionSectionTour, true);

updateProviderAuthenticationControl();
updateProviderAuthenticationControl("wizard-");
initializeSystemWorkspace();
initializeStatusSidebar();
updateEnergyMeasurement();
updateEnergyRateControls();
bootstrap();
