const tg = window.Telegram ? window.Telegram.WebApp : null;
const initData = tg ? tg.initData : "";

const statusText = document.getElementById("status-text");
const baseCurrency = document.getElementById("base-currency");
const workspaceName = document.getElementById("workspace-name");
const userPill = document.getElementById("user-pill");
const reportText = document.getElementById("report-text");
const balanceText = document.getElementById("balance-text");
const formMessage = document.getElementById("form-message");

let submitAction = "expense";

function showMessage(message) {
  formMessage.textContent = message;
  if (tg && tg.showAlert) {
    tg.showAlert(message);
  }
}

async function apiFetch(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    "X-Telegram-Init-Data": initData,
    ...options.headers,
  };
  const response = await fetch(path, { ...options, headers });
  const payload = await response.json().catch(() => ({ ok: false }));
  if (!response.ok || !payload.ok) {
    const error = payload.error || "Request failed";
    throw new Error(error);
  }
  return payload;
}

async function loadStatus() {
  if (!initData) {
    statusText.textContent = "Open inside Telegram";
    return;
  }
  try {
    const data = await apiFetch("/api/status", { method: "GET" });
    const user = data.user || {};
    const workspace = data.workspace || {};
    const label = user.username ? `@${user.username}` : user.first_name || "Member";
    userPill.textContent = label;
    workspaceName.textContent = workspace.name || "Workspace";
    baseCurrency.textContent = workspace.base_currency || "USD";
    statusText.textContent = "Connected";
  } catch (error) {
    statusText.textContent = "Setup needed";
    showMessage("Run /setup in the chat to create a workspace.");
  }
}

async function loadReport() {
  if (!initData) {
    reportText.textContent = "Open inside Telegram to load data.";
    return;
  }
  try {
    const data = await apiFetch("/api/report", { method: "GET" });
    reportText.textContent = data.report || "No data.";
  } catch (error) {
    reportText.textContent = "No report yet.";
  }
}

async function loadBalance() {
  if (!initData) {
    balanceText.textContent = "Open inside Telegram to load data.";
    return;
  }
  try {
    const data = await apiFetch("/api/balance", { method: "GET" });
    balanceText.textContent = data.report || "All settled.";
  } catch (error) {
    balanceText.textContent = "No balance yet.";
  }
}

function bindForm() {
  const form = document.getElementById("entry-form");
  const actionButtons = form.querySelectorAll("button[data-action]");
  actionButtons.forEach((button) => {
    button.addEventListener("click", () => {
      submitAction = button.dataset.action;
    });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!initData) {
      showMessage("Open this app from Telegram to submit data.");
      return;
    }
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    try {
      await apiFetch(`/api/${submitAction}`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      showMessage("Saved.");
      form.reset();
      await Promise.all([loadReport(), loadBalance()]);
    } catch (error) {
      showMessage(error.message);
    }
  });
}

if (tg) {
  tg.ready();
  tg.expand();
}

bindForm();
loadStatus();
loadReport();
loadBalance();
