const state = {
  sessionId: localStorage.getItem("carenav.sessionId") || "",
  busy: false,
};

const chatLog = document.querySelector("#chatLog");
const chatForm = document.querySelector("#chatForm");
const messageInput = document.querySelector("#messageInput");
const sendButton = document.querySelector("#sendButton");
const newSessionButton = document.querySelector("#newSessionButton");
const modelName = document.querySelector("#modelName");
const finderButton = document.querySelector("#finderButton");
const finderResults = document.querySelector("#finderResults");
const careType = document.querySelector("#careType");
const insuranceProvider = document.querySelector("#insuranceProvider");
const radiusRange = document.querySelector("#radiusRange");
const radiusValue = document.querySelector("#radiusValue");

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
    const payload = await api("/api/hospitals", {
      method: "POST",
      body: JSON.stringify({
        care_type: careType.value,
        insurance_provider: insuranceProvider.value,
        radius: Number(radiusRange.value) * 1000,
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

finderButton.addEventListener("click", findCare);

init();
