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
    throw new Error(result.error || `request-failed-${response.status}`);
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
  });
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
}

function resetTask() {
  state.messages = [];
  const capability = CAPABILITIES[state.capabilityId];
  const messages = byId("messages");
  messages.replaceChildren();
  addMessage("assistant", capability.welcome, "Haven 42");
  byId("prompt").value = "";
  byId("text-status").textContent = state.connected ? "Ready · nothing saved" : "Provider not connected";
}

function selectCapability(capabilityId) {
  if (!Object.hasOwn(CAPABILITIES, capabilityId)) return;
  state.capabilityId = capabilityId;
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
  if (capabilityId === "general.chat") state.messages = requestMessages;
  addMessage("user", content, capabilityId === "content.summarize" ? "Source" : "You");
  byId("text-status").textContent = capability.busy;
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
    addMessage("assistant", result.content, capability.resultLabel);
    byId("text-status").textContent = result.modelUnloaded
      ? `${result.model} · response complete · model unloaded`
      : `${result.model} · response complete · kept warm until idle timeout`;
  } catch (error) {
    showError(humanError(error));
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
    if (cleanupStatus) byId("text-status").textContent = cleanupStatus;
    setTaskControlsDisabled(false);
  }
});
byId("home-nav").addEventListener("click", () => {
  document.querySelectorAll(".nav-item").forEach((button) => button.classList.remove("active"));
  byId("home-nav").classList.add("active");
  window.scrollTo({ top: 0, behavior: "smooth" });
});
byId("models-nav").addEventListener("click", () => {
  byId("connection-panel").scrollIntoView({ behavior: "smooth" });
});
byId("system-nav").addEventListener("click", () => {
  byId("status-panel").scrollIntoView({ behavior: "smooth" });
});

byId("wizard-start").addEventListener("click", () => {
  showWizardStep("provider");
  byId("wizard-endpoint").focus();
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

bootstrap();
