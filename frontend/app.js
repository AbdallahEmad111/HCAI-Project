const GREETING_TEXT =
  "Hi! I'm an AI assistant, not a person. I suggest research directions in CS, SC, AI and IS using a curated set of 12 verified papers (expanding to 32). I can't confirm that an idea is new, guarantee acceptance by a journal, or cover topics outside these papers.";

const STEP_LABELS = {
  1: "Step 1 of 5: Profile",
  2: "Step 2 of 5: Retrieve",
  3: "Step 3 of 5: Analyze",
  4: "Step 4 of 5: Explain",
  5: "Step 5 of 5: Publish",
};

// State & Undo history (Shneiderman Rule 6)
let currentState = {
  department: "",
  skills: "",
  interests: "",
  compute: "low",
  lastResult: null,
};
let historyStack = [];
let fontScaleIndex = 0; // 0 -> 100%, 1 -> 150%, 2 -> 200%

// DOM Elements
const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const deptSelect = document.getElementById("dept-select");
const computeSelect = document.getElementById("compute-select");
const skillsInput = document.getElementById("skills-input");
const messageInput = document.getElementById("message-input");
const btnSend = document.getElementById("btn-send");

const stepStatusText = document.getElementById("step-status-text");
const stepItems = document.querySelectorAll(".step-item");
const profileSummaryText = document.getElementById("profile-summary-text");
const btnUndo = document.getElementById("btn-undo");

const whyContent = document.getElementById("why-content");
const evidenceStatusBadge = document.getElementById("evidence-status-badge");
const closureBox = document.getElementById("closure-box");

// Accessibility & Toolbar Controls
const btnFontSize = document.getElementById("btn-font-size");
const btnContrast = document.getElementById("btn-contrast");
const btnPlainLang = document.getElementById("btn-plain-lang");
const btnToggleHints = document.getElementById("btn-toggle-hints");
const guidedHintBox = document.getElementById("guided-hint-box");
const helpDialog = document.getElementById("help-dialog");

function setStep(stepNumber) {
  stepStatusText.textContent = STEP_LABELS[stepNumber] || STEP_LABELS[1];
  stepItems.forEach((item) => {
    const s = Number(item.dataset.step);
    item.classList.remove("active", "done");
    if (s < stepNumber) item.classList.add("done");
    if (s === stepNumber) item.classList.add("active");
  });
}

function updateProfileStrip() {
  const dept = deptSelect.value || "Not set";
  const skills = skillsInput.value.trim() || "None";
  const compute = computeSelect.value || "low";
  const interest = messageInput.value.trim() || "General";

  profileSummaryText.innerHTML = `<strong>Active Profile:</strong> Dept: <em>${escapeHtml(dept)}</em> | Skills: <em>${escapeHtml(skills)}</em> | Compute: <em>${escapeHtml(compute)}</em> | Interest: <em>${escapeHtml(interest)}</em>`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function formatBotMarkdown(text) {
  let safe = escapeHtml(text || "");
  safe = safe.replace(/^###\s+(.+)$/gm, '<h4 class="chat-heading">$1</h4>');
  safe = safe.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  safe = safe.replace(/^\s*[-*]\s+(.+)$/gm, '<div class="chat-bullet">• $1</div>');
  safe = safe.replace(/^\s*(\d+\.)\s+(.+)$/gm, '<div class="chat-numbered"><strong>$1</strong> $2</div>');
  return safe;
}

function appendMessage(role, text, extraClass = "") {
  const wrapper = document.createElement("div");
  wrapper.className = `msg ${role === "user" ? "msg-user" : "msg-bot"} ${extraClass}`.trim();

  const label = document.createElement("span");
  label.className = "msg-role";
  label.textContent = role === "user" ? "You" : "AI Research Roadmap Agent";

  const body = document.createElement("div");
  body.className = "msg-body";
  if (role === "user") {
    body.textContent = text;
  } else {
    body.innerHTML = formatBotMarkdown(text);
  }

  wrapper.appendChild(label);
  wrapper.appendChild(body);
  chatMessages.appendChild(wrapper);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function pushUndoSnapshot() {
  historyStack.push(JSON.parse(JSON.stringify(currentState)));
  btnUndo.disabled = historyStack.length === 0;
}

function restoreState(snapshot) {
  currentState = snapshot;
  deptSelect.value = snapshot.department || "";
  skillsInput.value = snapshot.skills || "";
  messageInput.value = snapshot.interests || "";
  computeSelect.value = snapshot.compute || "low";
  updateProfileStrip();

  if (snapshot.lastResult) {
    renderWhyPanel(snapshot.lastResult);
    setStep(5);
  } else {
    resetWhyPanel();
    setStep(1);
  }
}

function resetWhyPanel() {
  evidenceStatusBadge.textContent = "Status: Awaiting Profile";
  closureBox.classList.add("hidden");
  whyContent.innerHTML = `
    <div class="empty-state">
      <p><strong>No directions retrieved yet.</strong></p>
      <p>Submit your profile or click <em>"Try Worked Example"</em> to inspect the exact matching scores, skill overlaps, compute checks, and paper DOIs.</p>
    </div>
  `;
}

function renderWhyPanel(data) {
  const papers = data.papers || [];
  const venues = data.venues || [];

  if (!papers.length) {
    evidenceStatusBadge.textContent = `Status: ${data.status || "No match"}`;
    closureBox.classList.add("hidden");
    whyContent.innerHTML = `
      <div class="empty-state">
        <p><strong>No papers matched or request outside scope.</strong></p>
        <p>${escapeHtml(data.scope_reason || data.reply || "Edit your profile or select one of CS, SC, AI, or IS.")}</p>
      </div>
    `;
    return;
  }

  evidenceStatusBadge.textContent =
    data.status === "degraded_timeout"
      ? "Status: Backend Reasons Only (Model Timeout)"
      : `Status: Verified (${papers.length} Papers)`;

  let html = "";

  papers.forEach((p, idx) => {
    const reasonsHtml = (p.reasons || [])
      .map((r) => `<li>${escapeHtml(r)}</li>`)
      .join("");

    html += `
      <article class="paper-card" aria-label="Recommended paper ${idx + 1}">
        <div class="paper-card-top">
          <span class="paper-id-tag">${escapeHtml(p.paper_id)} · ${escapeHtml(p.department)}</span>
          <span class="score-tag">Match Score: ${Number(p.score)}</span>
        </div>
        <h3 class="paper-title">${escapeHtml(p.title)}</h3>
        <div class="paper-meta">
          ${escapeHtml(p.venue)} (${Number(p.year)}) · License: ${escapeHtml(p.license)} ·
          <a href="${escapeHtml(p.url)}" target="_blank" rel="noopener noreferrer">DOI: ${escapeHtml(p.doi)}</a>
        </div>
        <strong>Why this paper was selected (computed by backend):</strong>
        <ul class="reason-list">${reasonsHtml}</ul>
        <div class="limitation-box">
          <strong>Documented Limitation:</strong> ${escapeHtml(p.documented_limitations)}<br/>
          <strong>Suggested Direction:</strong> ${escapeHtml(p.suggested_direction)}
        </div>
      </article>
    `;
  });

  if (venues.length) {
    const venueItems = venues
      .map(
        (v) => `
        <div class="venue-card">
          <strong>Target Venue: ${escapeHtml(v.name)}</strong> (Verified: ${escapeHtml(v.last_verified)})<br/>
          <span>${escapeHtml(v.focus)}</span><br/>
          <a href="${escapeHtml(v.official_url)}" target="_blank" rel="noopener noreferrer">Official Author Guidelines</a>
          <div style="font-size:0.8rem; margin-top:0.25rem;">${escapeHtml(v.note)}</div>
        </div>
      `
      )
      .join("");
    html += venueItems;
  }

  whyContent.innerHTML = html;
  closureBox.classList.remove("hidden");
}

async function submitProfile(event) {
  if (event) event.preventDefault();

  const department = deptSelect.value.trim();
  const skills = skillsInput.value.trim();
  const interests = messageInput.value.trim();
  const compute = computeSelect.value;
  const plainLanguage = btnPlainLang.getAttribute("aria-pressed") === "true";

  updateProfileStrip();

  const userSummary = `Department: ${department || "Not specified"} | Skills: ${skills || "None"} | Compute: ${compute}${interests ? " | Question: " + interests : ""}`;
  appendMessage("user", userSummary);

  pushUndoSnapshot();
  setStep(2);
  btnSend.disabled = true;
  evidenceStatusBadge.textContent = "Status: Searching 12 papers...";

  try {
    setStep(3);
    const response = await fetch("/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        department,
        skills,
        interests,
        compute,
        message: interests,
        plain_language: plainLanguage,
      }),
    });

    const data = await response.json();
    setStep(4);

    const isSafety = ["fallback", "handover", "unclear", "degraded_timeout"].includes(data.status);
    appendMessage("bot", data.reply || "No response received.", isSafety ? "msg-safety" : "");

    renderWhyPanel(data);

    currentState = {
      department,
      skills,
      interests,
      compute,
      lastResult: data,
    };

    if (data.papers && data.papers.length > 0) {
      setStep(5);
    } else {
      setStep(1);
    }
  } catch (err) {
    appendMessage(
      "bot",
      "Network error reaching the local Flask server. Make sure 'python app.py' is running.",
      "msg-safety"
    );
    evidenceStatusBadge.textContent = "Status: Connection Error";
    setStep(1);
  } finally {
    btnSend.disabled = false;
  }
}

// Event Listeners
chatForm.addEventListener("submit", submitProfile);
[deptSelect, skillsInput, messageInput, computeSelect].forEach((el) => {
  el.addEventListener("input", updateProfileStrip);
  el.addEventListener("change", updateProfileStrip);
});

// Quick department chips
document.querySelectorAll(".quick-replies .chip-btn[data-dept]").forEach((btn) => {
  btn.addEventListener("click", () => {
    deptSelect.value = btn.dataset.dept;
    updateProfileStrip();
    skillsInput.focus();
  });
});

// Onboarding Stage 1: Worked Example button
document.getElementById("btn-worked-example").addEventListener("click", () => {
  deptSelect.value = "CS";
  skillsInput.value = "Python, statistics";
  computeSelect.value = "low";
  messageInput.value = "software engineering defect prediction";
  updateProfileStrip();
  submitProfile();
});

// Paste Full Profile Shortcut (Shneiderman Rule 2)
const pasteDrawer = document.getElementById("paste-drawer");
const pasteInput = document.getElementById("paste-input");

document.getElementById("btn-paste-profile").addEventListener("click", () => {
  pasteDrawer.classList.remove("hidden");
  pasteInput.focus();
});

document.getElementById("btn-close-paste").addEventListener("click", () => {
  pasteDrawer.classList.add("hidden");
});

document.getElementById("btn-apply-paste").addEventListener("click", () => {
  const parts = pasteInput.value.split("|").map((p) => p.trim());
  if (parts[0]) deptSelect.value = parts[0].toUpperCase();
  if (parts[1]) skillsInput.value = parts[1];
  if (parts[2]) messageInput.value = parts[2];
  if (parts[3] && ["low", "medium", "high"].includes(parts[3].toLowerCase())) {
    computeSelect.value = parts[3].toLowerCase();
  }
  pasteDrawer.classList.add("hidden");
  updateProfileStrip();
  submitProfile();
});

// Undo & Start Over (Shneiderman Rule 6)
btnUndo.addEventListener("click", () => {
  if (!historyStack.length) return;
  const previous = historyStack.pop();
  btnUndo.disabled = historyStack.length === 0;
  restoreState(previous);
  appendMessage("bot", "Reverted to your previous profile state.");
});

document.getElementById("btn-start-over").addEventListener("click", () => {
  pushUndoSnapshot();
  deptSelect.value = "";
  skillsInput.value = "";
  messageInput.value = "";
  computeSelect.value = "low";
  chatMessages.innerHTML = "";
  appendMessage("bot", GREETING_TEXT);
  resetWhyPanel();
  updateProfileStrip();
  setStep(1);
});

// Accessibility Toggles
btnFontSize.addEventListener("click", () => {
  fontScaleIndex = (fontScaleIndex + 1) % 3;
  document.body.classList.remove("scale-150", "scale-200");
  if (fontScaleIndex === 1) {
    document.body.classList.add("scale-150");
    btnFontSize.textContent = "Text Size: 150%";
    btnFontSize.setAttribute("aria-pressed", "true");
  } else if (fontScaleIndex === 2) {
    document.body.classList.add("scale-200");
    btnFontSize.textContent = "Text Size: 200%";
    btnFontSize.setAttribute("aria-pressed", "true");
  } else {
    btnFontSize.textContent = "Text Size: 100%";
    btnFontSize.setAttribute("aria-pressed", "false");
  }
});

btnContrast.addEventListener("click", () => {
  const active = document.body.classList.toggle("high-contrast");
  btnContrast.textContent = `High Contrast: ${active ? "On" : "Off"}`;
  btnContrast.setAttribute("aria-pressed", String(active));
});

btnPlainLang.addEventListener("click", () => {
  const active = btnPlainLang.getAttribute("aria-pressed") !== "true";
  btnPlainLang.setAttribute("aria-pressed", String(active));
  btnPlainLang.textContent = `Plain Language: ${active ? "On" : "Off"}`;
});

// Onboarding Stage 3: Hints toggle
btnToggleHints.addEventListener("click", () => {
  const active = btnToggleHints.getAttribute("aria-pressed") !== "true";
  btnToggleHints.setAttribute("aria-pressed", String(active));
  btnToggleHints.textContent = `Guided Hints: ${active ? "On" : "Off"}`;
  guidedHintBox.classList.toggle("hidden", !active);
});

// Help Dialog
document.getElementById("btn-help").addEventListener("click", () => helpDialog.showModal());
document.getElementById("btn-close-help").addEventListener("click", () => helpDialog.close());

// Closure & Feedback (Shneiderman Rule 4 + HAI Ladder Level 4)
document.getElementById("btn-save-roadmap").addEventListener("click", () => {
  if (!currentState.lastResult) return;
  const lines = [
    "AI RESEARCH ROADMAP SUMMARY",
    `Department: ${currentState.department} | Skills: ${currentState.skills} | Compute: ${currentState.compute}`,
    "------------------------------------------------------------",
    currentState.lastResult.reply || "",
    "\nRETRIEVED PAPERS & REASONS:",
    ...(currentState.lastResult.papers || []).map(
      (p) => `- [${p.paper_id}] ${p.title} (DOI: ${p.doi})\n  Reasons: ${p.reasons.join(" | ")}`
    ),
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `Research_Roadmap_${currentState.department || "Summary"}.txt`;
  link.click();
});

const feedbackReasonBox = document.getElementById("feedback-reason-box");
const feedbackConfirm = document.getElementById("feedback-confirm");

document.getElementById("btn-thumb-up").addEventListener("click", () => {
  feedbackReasonBox.classList.add("hidden");
  feedbackConfirm.textContent = "Thank you! Positive feedback recorded for this recommendation.";
});

document.getElementById("btn-thumb-down").addEventListener("click", () => {
  feedbackReasonBox.classList.remove("hidden");
  document.getElementById("feedback-text").focus();
});

document.getElementById("btn-submit-feedback").addEventListener("click", () => {
  const reason = document.getElementById("feedback-text").value.trim();
  feedbackReasonBox.classList.add("hidden");
  feedbackConfirm.textContent = reason
    ? `Feedback logged: "${reason}". Try editing your skills or compute filter above.`
    : "Feedback logged. Try editing your skills or compute filter above.";
});

// Initialize on load
appendMessage("bot", GREETING_TEXT);
updateProfileStrip();
setStep(1);