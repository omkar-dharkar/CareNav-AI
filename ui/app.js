const state = {
  sessionId: localStorage.getItem("carenav.sessionId") || "",
  location: JSON.parse(localStorage.getItem("carenav.location") || "null"),
  busy: false,
};

const chatLog = document.querySelector("#chatLog");
const chatForm = document.querySelector("#chatForm");
const messageInput = document.querySelector("#messageInput");
const sendButton = document.querySelector("#sendButton");
const voiceButton = document.querySelector("#voiceButton");
const newSessionButton = document.querySelector("#newSessionButton");
const modelName = document.querySelector("#modelName");
const locationStatus = document.querySelector("#locationStatus");
const locationButton = document.querySelector("#locationButton");
const finderButton = document.querySelector("#finderButton");
const finderResults = document.querySelector("#finderResults");
const careType = document.querySelector("#careType");
const insuranceProvider = document.querySelector("#insuranceProvider");
const radiusRange = document.querySelector("#radiusRange");
const radiusValue = document.querySelector("#radiusValue");

let recognition = null;
let listening = false;

function locationPayload() {
  if (!state.location) return {};
  return {
    latitude: state.location.latitude,
    longitude: state.location.longitude,
    location_label: state.location.label,
  };
}

function updateLocationStatus() {
  if (!locationStatus) return;
  if (state.location) {
    locationStatus.textContent = state.location.label || "Device location";
    locationStatus.title = `${state.location.latitude.toFixed(5)}, ${state.location.longitude.toFixed(5)}`;
  } else {
    locationStatus.textContent = "Permission needed";
    locationStatus.removeAttribute("title");
  }
}

function needsLocation(text) {
  return /\b(nearby|near me|closest|hospital|er|emergency room|urgent care|clinic|pharmacy|medicaid|unitedhealthcare|uhc|insurance|map|address)\b/i.test(text);
}

async function getBrowserLocation() {
  if (!navigator.geolocation) {
    throw new Error("Browser location is not available. The app will use server fallback location.");
  }

  const position = await new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 300000,
    });
  });

  const { latitude, longitude, accuracy } = position.coords;
  const label = `Device location (${Math.round(accuracy)}m)`;
  state.location = { latitude, longitude, accuracy, label };
  localStorage.setItem("carenav.location", JSON.stringify(state.location));
  updateLocationStatus();
  return state.location;
}

async function ensureLocationForCare() {
  if (state.location) return state.location;
  try {
    return await getBrowserLocation();
  } catch (error) {
    updateLocationStatus();
    return null;
  }
}

const escapeHtml = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

function linkFor(value, label) {
  if (!value || /not available/i.test(value)) return "";
  const safe = escapeHtml(value);
  const href = value.startsWith("http") ? value : `tel:${value.replace(/[^\d+]/g, "")}`;
  return `<a class="mini-link" href="${escapeHtml(href)}" target="_blank" rel="noreferrer">${escapeHtml(label)}</a>`;
}

function parseFacilities(text) {
  const blocks = [];
  const pattern = /(?:^|\n)\s*(?:[-*]\s*)?\*\*(?:\d+\.\s*)?([^*]+)\*\*\s*([\s\S]*?)(?=\n\s*(?:[-*]\s*)?\*\*(?:\d+\.\s*)?[^*]+\*\*|\n\nEMERGENCY:|\n\nPoison exposure|\n\nServices note:|\n\nInsurance note:|\n\nNote:|$)/g;
  let match;

  while ((match = pattern.exec(text)) !== null) {
    const body = match[2] || "";
    const fields = {};
    for (const line of body.split("\n")) {
      const fieldMatch = line.match(/^(Address|Phone|Rating|Website|Maps|Status):\s*(.*)$/);
      if (fieldMatch) fields[fieldMatch[1].toLowerCase()] = fieldMatch[2].trim();
    }

    if (fields.address || fields.phone || fields.maps) {
      blocks.push({
        name: match[1].trim(),
        ...fields,
      });
    }
  }

  return blocks;
}

function removeFacilityBlocks(text) {
  const pattern = /(?:^|\n)\s*(?:[-*]\s*)?\*\*(?:\d+\.\s*)?[^*]+\*\*\s*([\s\S]*?)(?=\n\s*(?:[-*]\s*)?\*\*(?:\d+\.\s*)?[^*]+\*\*|\n\nEMERGENCY:|\n\nPoison exposure|\n\nServices note:|\n\nInsurance note:|\n\nNote:|$)/g;

  return text
    .replace(pattern, (block, body) =>
      /^(Address|Phone|Rating|Website|Maps|Status):/m.test(body) ? "" : block,
    )
    .trim();
}

function paragraphHtml(text) {
  const escaped = escapeHtml(text)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noreferrer">$1</a>');

  return escaped
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)
    .map((paragraph) => `<p>${paragraph.replace(/\n/g, "<br>")}</p>`)
    .join("");
}

function facilityCardsHtml(facilities) {
  if (!facilities.length) return "";

  return `
    <div class="facility-grid">
      ${facilities
        .map(
          (facility) => `
            <article class="facility-card">
              <h3>${escapeHtml(facility.name)}</h3>
              <div class="facility-meta">
                ${facility.address ? `<span>${escapeHtml(facility.address)}</span>` : ""}
                ${facility.phone ? `<span>${escapeHtml(facility.phone)}</span>` : ""}
                ${facility.rating ? `<span>Rating: ${escapeHtml(facility.rating)}</span>` : ""}
                ${facility.status ? `<span>${escapeHtml(facility.status)}</span>` : ""}
              </div>
              <div class="facility-actions">
                ${linkFor(facility.phone, "Call")}
                ${linkFor(facility.maps, "Map")}
                ${linkFor(facility.website, "Website")}
              </div>
            </article>
          `,
        )
        .join("")}
    </div>
  `;
}

function richTextHtml(text) {
  const facilities = parseFacilities(text);
  const remainder = removeFacilityBlocks(text);
  return `${facilityCardsHtml(facilities)}${paragraphHtml(remainder)}`;
}

function addMessage(role, text, tools = []) {
  const article = document.createElement("article");
  article.className = `message ${role}`;
  article.innerHTML = `
    <div class="avatar" aria-hidden="true">${role === "user" ? "YOU" : "CN"}</div>
    <div class="bubble">
      ${role === "assistant" ? richTextHtml(text) : paragraphHtml(text)}
      ${
        tools.length
          ? `<div class="tool-row">${tools
              .map((tool) => `<span class="tool-pill">${escapeHtml(tool)}</span>`)
              .join("")}</div>`
          : ""
      }
    </div>
  `;
  chatLog.appendChild(article);
  chatLog.scrollTop = chatLog.scrollHeight;
  return article;
}

function setBusy(value) {
  state.busy = value;
  sendButton.disabled = value;
  finderButton.disabled = value;
}

function setListening(value) {
  listening = value;
  if (!voiceButton) return;
  voiceButton.classList.toggle("listening", value);
  voiceButton.setAttribute("aria-label", value ? "Stop voice input" : "Start voice input");
  voiceButton.title = value ? "Stop voice input" : "Voice input";
}

function setupVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!voiceButton || !SpeechRecognition) {
    if (voiceButton) {
      voiceButton.disabled = true;
      voiceButton.title = "Voice input is not supported in this browser";
    }
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = true;
  recognition.continuous = false;

  recognition.onresult = (event) => {
    let finalText = "";
    let interimText = "";
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const transcript = event.results[i][0].transcript.trim();
      if (event.results[i].isFinal) {
        finalText += `${transcript} `;
      } else {
        interimText += `${transcript} `;
      }
    }

    const existing = messageInput.value.replace(/\s*\[[^\]]*listening[^\]]*\]\s*$/i, "").trim();
    const spoken = `${finalText}${interimText}`.trim();
    messageInput.value = [existing, spoken ? `${spoken}${interimText ? " [listening]" : ""}` : ""]
      .filter(Boolean)
      .join(existing ? " " : "");
    resizeInput();
  };

  recognition.onerror = () => {
    setListening(false);
  };

  recognition.onend = () => {
    messageInput.value = messageInput.value.replace(/\s*\[[^\]]*listening[^\]]*\]\s*$/i, "").trim();
    resizeInput();
    setListening(false);
  };
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Request failed.");
  }
  return payload;
}

async function ensureSession(force = false) {
  if (state.sessionId && !force) return state.sessionId;
  const payload = await api("/api/session", { method: "POST" });
  state.sessionId = payload.session_id;
  localStorage.setItem("carenav.sessionId", state.sessionId);
  return state.sessionId;
}

async function sendMessage(text) {
  const trimmed = text.trim();
  if (!trimmed || state.busy) return;

  await ensureSession();
  if (needsLocation(trimmed)) {
    await ensureLocationForCare();
  }
  addMessage("user", trimmed);
  messageInput.value = "";
  resizeInput();
  setBusy(true);
  const loading = addMessage("assistant", "CareNav is checking this now.", []);
  loading.querySelector(".bubble").classList.add("loading");

  try {
    const payload = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        session_id: state.sessionId,
        message: trimmed,
        ...locationPayload(),
      }),
    });
    state.sessionId = payload.session_id;
    localStorage.setItem("carenav.sessionId", state.sessionId);
    loading.remove();
    addMessage("assistant", payload.text, payload.tools || []);
  } catch (error) {
    loading.remove();
    addMessage("assistant", error.message);
  } finally {
    setBusy(false);
    messageInput.focus();
  }
}

async function findCare() {
  if (state.busy) return;
  setBusy(true);
  finderResults.innerHTML = `<p class="empty-state loading">Searching nearby care</p>`;

  try {
    await ensureLocationForCare();
    const payload = await api("/api/hospitals", {
      method: "POST",
      body: JSON.stringify({
        care_type: careType.value,
        insurance_provider: insuranceProvider.value,
        radius: Number(radiusRange.value) * 1000,
        ...locationPayload(),
      }),
    });

    const html = richTextHtml(payload.text);
    finderResults.innerHTML = html || `<p class="empty-state">No matching results.</p>`;
    addMessage("assistant", payload.text, ["find_nearby_hospitals"]);
  } catch (error) {
    finderResults.innerHTML = `<p class="empty-state">${escapeHtml(error.message)}</p>`;
  } finally {
    setBusy(false);
  }
}

function resizeInput() {
  messageInput.style.height = "auto";
  messageInput.style.height = `${Math.min(messageInput.scrollHeight, 150)}px`;
}

async function init() {
  try {
    const health = await api("/api/health");
    modelName.textContent = (health.model || "Ready")
      .replace("gemini-", "")
      .replaceAll("-", " ");
  } catch {
    modelName.textContent = "Offline";
  }

  await ensureSession();
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(messageInput.value);
});

messageInput.addEventListener("input", resizeInput);

messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage(messageInput.value);
  }
});

newSessionButton.addEventListener("click", async () => {
  localStorage.removeItem("carenav.sessionId");
  state.sessionId = "";
  chatLog.innerHTML = "";
  addMessage(
    "assistant",
    "New session started. For a medical emergency in the U.S., call 911 now.",
  );
  await ensureSession(true);
});

document.querySelectorAll(".quick-chip").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.prompt || ""));
});

radiusRange.addEventListener("input", () => {
  radiusValue.textContent = `${radiusRange.value} km`;
});

locationButton.addEventListener("click", async () => {
  locationButton.classList.add("loading");
  locationButton.disabled = true;
  try {
    await getBrowserLocation();
  } catch (error) {
    addMessage("assistant", `${error.message} You can still search, but results may reflect the server region.`);
  } finally {
    locationButton.classList.remove("loading");
    locationButton.disabled = false;
  }
});

voiceButton?.addEventListener("click", () => {
  if (!recognition) return;
  if (listening) {
    recognition.stop();
    return;
  }
  try {
    setListening(true);
    recognition.start();
  } catch {
    setListening(false);
  }
});

finderButton.addEventListener("click", findCare);

setupVoiceInput();
updateLocationStatus();
init();
