let currentFunction = "answer";
let lastRun = null;

const tabs = document.querySelectorAll(".tab");
const promptSelect = document.getElementById("promptSelect");
const userInput = document.getElementById("userInput");
const charCount = document.getElementById("charCount");
const runBtn = document.getElementById("runBtn");
const statusMessage = document.getElementById("statusMessage");
const resultBox = document.getElementById("resultBox");
const resultMeta = document.getElementById("resultMeta");
const resultText = document.getElementById("resultText");
const thumbsUp = document.getElementById("thumbsUp");
const thumbsDown = document.getElementById("thumbsDown");
const fbThanks = document.getElementById("fbThanks");
const statsBox = document.getElementById("statsBox");

function setStatus(message = "", kind = "") {
  statusMessage.textContent = message;
  statusMessage.className = `status ${kind}`.trim();
}

function populatePrompts(fn) {
  promptSelect.replaceChildren();
  for (const prompt of PROMPT_LIBRARY[fn] || []) {
    const option = document.createElement("option");
    option.value = prompt.id;
    option.textContent = prompt.label;
    promptSelect.appendChild(option);
  }
}

function clearResult() {
  resultBox.classList.add("hidden");
  lastRun = null;
  thumbsUp.classList.remove("selected");
  thumbsDown.classList.remove("selected");
  fbThanks.classList.add("hidden");
}

function updateCount() {
  charCount.textContent = String(userInput.value.length);
}

async function readJson(response) {
  try {
    return await response.json();
  } catch {
    return { error: "The server returned an invalid response." };
  }
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((item) => item.classList.remove("active"));
    tab.classList.add("active");
    currentFunction = tab.dataset.fn;
    populatePrompts(currentFunction);
    clearResult();
    setStatus();
  });
});

userInput.addEventListener("input", updateCount);

runBtn.addEventListener("click", async () => {
  const input = userInput.value.trim();
  if (!input) {
    setStatus("Please enter some input first.", "error");
    userInput.focus();
    return;
  }

  runBtn.disabled = true;
  resultBox.classList.add("hidden");
  setStatus("Generating response…", "busy");

  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ function: currentFunction, prompt_id: promptSelect.value, input }),
    });
    const data = await readJson(response);

    if (!response.ok || data.error) {
      throw new Error(data.error || "The request could not be completed.");
    }

    resultMeta.textContent = `Function: ${data.function} · Prompt: ${data.prompt_used} · ${data.elapsed_seconds}s`;
    resultText.textContent = data.result;
    lastRun = { function: data.function, prompt_used: data.prompt_used, input, output: data.result };
    thumbsUp.classList.remove("selected");
    thumbsDown.classList.remove("selected");
    fbThanks.classList.add("hidden");
    resultBox.classList.remove("hidden");
    setStatus("Response ready.", "success");
  } catch (error) {
    const message = error instanceof Error ? error.message : "Something went wrong.";
    resultText.textContent = message;
    resultBox.classList.remove("hidden");
    setStatus("The request could not be completed.", "error");
  } finally {
    runBtn.disabled = false;
  }
});

async function sendFeedback(helpful) {
  if (!lastRun) return;

  thumbsUp.disabled = true;
  thumbsDown.disabled = true;
  try {
    const response = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ ...lastRun, helpful }),
    });
    const data = await readJson(response);
    if (!response.ok || data.error) throw new Error(data.error || "Feedback could not be saved.");

    thumbsUp.classList.toggle("selected", helpful === true);
    thumbsDown.classList.toggle("selected", helpful === false);
    fbThanks.classList.remove("hidden");
    await loadStats();
  } catch {
    setStatus("Feedback could not be submitted. Please try again.", "error");
  } finally {
    thumbsUp.disabled = false;
    thumbsDown.disabled = false;
  }
}

thumbsUp.addEventListener("click", () => sendFeedback(true));
thumbsDown.addEventListener("click", () => sendFeedback(false));

async function loadStats() {
  try {
    const response = await fetch("/api/feedback/stats", { headers: { Accept: "application/json" } });
    const data = await readJson(response);
    if (!response.ok) throw new Error();

    statsBox.replaceChildren();
    const total = document.createElement("strong");
    total.textContent = String(data.total ?? 0);
    statsBox.append("Ratings recorded: ", total, document.createElement("br"));
    statsBox.append(`Helpful: ${data.helpful ?? 0} · Not helpful: ${data.not_helpful ?? 0}`);
  } catch {
    statsBox.textContent = "Feedback statistics unavailable.";
  }
}

populatePrompts(currentFunction);
updateCount();
loadStats();
