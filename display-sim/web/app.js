// Control page: builds the controls from /api/meta, keeps them in step with settings.txt
// (/api/state), and saves every change. All text comes from the API and is set with
// textContent, never as HTML.

const $ = (selector) => document.querySelector(selector);
const SAVE_DELAY_MS = 80;       // wait for a slider drag to settle before writing
const POLL_MS = 1000;           // pick up hand edits to settings.txt
const QUIET_MS = 1500;          // do not overwrite the page right after you touched it

let meta;
let state;
let saveTimer = null;
let lastTouch = 0;

const pageButtons = new Map();
const expressionButtons = new Map();
const voiceButtons = new Map();
const themeButtons = new Map();

// ---- talking to the server ------------------------------------------------------------------

async function request(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error([].concat(body.detail ?? response.statusText).join(", "));
  }
  return response;
}

function setStatus(text, kind = "") {
  const status = $("#status");
  status.textContent = text;
  status.className = `status ${kind}`;
}

function scheduleSave() {
  lastTouch = Date.now();
  setStatus("Saving");
  clearTimeout(saveTimer);
  saveTimer = setTimeout(save, SAVE_DELAY_MS);
}

async function save() {
  saveTimer = null;
  try {
    await request("/api/state", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state),
    });
    setStatus("Saved", "ok");
  } catch (error) {
    setStatus(error.message, "bad");
  }
}

async function poll() {
  if (saveTimer || Date.now() - lastTouch < QUIET_MS) return;
  try {
    const latest = await (await request("/api/state")).json();
    if (JSON.stringify(latest) !== JSON.stringify(state)) {
      state = latest;
      sync();
    }
    setStatus("Connected", "ok");
  } catch (error) {
    setStatus("Control server not reachable", "bad");
  }
}

async function restartSimulator() {
  setStatus("Restarting the simulator");
  try {
    await request("/api/restart", { method: "POST" });
    setStatus("Simulator restarting, the window reopens in a few seconds", "ok");
  } catch (error) {
    setStatus(error.message, "bad");
  }
}

// ---- building the controls ------------------------------------------------------------------

function chip(label, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.addEventListener("click", onClick);
  return button;
}

function buildChips(container, names, buttons, onPick) {
  for (const name of names) {
    const button = chip(name, () => onPick(name));
    buttons.set(name, button);
    container.append(button);
  }
}

const toHex = (rgb) => `#${rgb.map((v) => v.toString(16).padStart(2, "0")).join("")}`;

// A theme sets the accent, secondary and background lights together, like the device's Theme select.
function buildThemes() {
  for (const theme of meta.themes) {
    const button = chip(theme.name, () => {
      state.accent = toHex(theme.accent);
      state.secondary = toHex(theme.secondary);
      state.background = toHex(theme.bg);
      scheduleSave();
      sync();
    });
    themeButtons.set(theme.name, button);
    $("#themes").append(button);
  }
}

function bindText(selector, key, counter, max) {
  const input = $(selector);
  input.maxLength = max;
  input.addEventListener("input", () => {
    state[key] = input.value.split(/\s+/).join(" ");
    scheduleSave();
    sync();
  });
  return { input, key, counter, max };
}

const texts = [];

function bindControls() {
  buildChips($("#pages"), meta.pages, pageButtons, (name) => {
    state.page = name;
    scheduleSave();
    sync();
  });
  texts.push(bindText("#message-title", "message_title", "#title-count", meta.title_max));
  texts.push(bindText("#message-body", "message_body", "#body-count", meta.body_max));
  $("#clock-24h").addEventListener("change", (event) => {
    state.clock_24h = event.target.checked;
    scheduleSave();
  });
  $("#clock-time").addEventListener("input", (event) => {
    state.clock_time = event.target.value;
    scheduleSave();
    sync();
  });
  $("#clock-live").addEventListener("click", () => {
    state.clock_time = "";
    scheduleSave();
    sync();
  });
  buildChips($("#expressions"), meta.expressions, expressionButtons, (name) => {
    state.expression = name;
    scheduleSave();
    sync();
  });
  buildChips($("#voices"), meta.voices, voiceButtons, (name) => {
    state.voice = name;
    scheduleSave();
    sync();
  });
  buildThemes();
  for (const key of ["accent", "secondary", "background"]) {
    $(`#${key}`).addEventListener("input", (event) => {
      state[key] = event.target.value;
      scheduleSave();
      sync();
    });
  }

  $("#speaking").addEventListener("change", (event) => {
    state.speaking = event.target.checked;
    scheduleSave();
  });
  const fps = $("#fps");
  Object.assign(fps, { min: meta.fps.min, max: meta.fps.max, step: meta.fps.step });
  fps.addEventListener("input", () => {
    state.fps = Number(fps.value);
    scheduleSave();
    sync();
  });
  $("#restart").addEventListener("click", restartSimulator);
}

// ---- showing the state ----------------------------------------------------------------------

function sync() {
  for (const [name, button] of pageButtons) button.setAttribute("aria-pressed", name === state.page);
  $("#card-face").hidden = state.page !== "Face";
  $("#card-clock").hidden = state.page !== "Clock";
  $("#card-message").hidden = state.page !== "Message";
  for (const [name, button] of expressionButtons) button.setAttribute("aria-pressed", name === state.expression);
  for (const [name, button] of voiceButtons) button.setAttribute("aria-pressed", name === state.voice);
  for (const theme of meta.themes) {
    const on = toHex(theme.accent) === state.accent && toHex(theme.secondary) === state.secondary &&
      toHex(theme.bg) === state.background;
    themeButtons.get(theme.name).setAttribute("aria-pressed", on);
  }
  $("#accent").value = state.accent;
  $("#secondary").value = state.secondary;
  $("#background").value = state.background;
  $("#speaking").checked = state.speaking;
  $("#fps").value = state.fps;
  $("#fps-value").textContent = `${state.fps} fps`;
  $("#clock-24h").checked = state.clock_24h;
  $("#clock-time").value = state.clock_time;
  $("#clock-hint").textContent = state.clock_time ? "The clock page is frozen at this time." : "Showing this computer's time.";
  for (const { input, key, counter, max } of texts) {
    // Rewrite only when different, so the caret stays put while typing.
    if (input.value !== state[key]) input.value = state[key];
    $(counter).textContent = `${state[key].length}/${max}`;
  }
}

async function init() {
  try {
    meta = await (await request("/api/meta")).json();
    state = await (await request("/api/state")).json();
  } catch (error) {
    setStatus(`Cannot load: ${error.message}`, "bad");
    return;
  }
  bindControls();
  sync();
  setStatus("Connected", "ok");
  setInterval(poll, POLL_MS);
}

init();
