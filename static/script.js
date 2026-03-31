/**
 * Forensic AI — Frontend Script
 */

const uploadZone     = document.getElementById("uploadZone");
const fileInput      = document.getElementById("fileInput");
const uploadPH       = document.getElementById("uploadPlaceholder");
const previewImg     = document.getElementById("previewImg");
const clearBtn       = document.getElementById("clearBtn");
const matchBtn       = document.getElementById("matchBtn");
const matchBtnText   = document.getElementById("matchBtnText");
const matchBtnSpin   = document.getElementById("matchBtnSpinner");
const statusBar      = document.getElementById("statusBar");
const statusText     = document.getElementById("statusText");
const resultsCard    = document.getElementById("resultsCard");
const resultsCount   = document.getElementById("resultsCount");
const resultsNote    = document.getElementById("resultsNote");
const matchGrid      = document.getElementById("matchGrid");
const noMatchCard    = document.getElementById("noMatchCard");
const modalOverlay   = document.getElementById("modalOverlay");
const modalBox       = document.getElementById("modalBox");
const modalClose     = document.getElementById("modalClose");
const modalName      = document.getElementById("modalName");
const modalSimilarity= document.getElementById("modalSimilarity");
const modalFields    = document.getElementById("modalFields");
const modalPhoto     = document.getElementById("modalPhoto");

let selectedFile = null;

// ─── Upload Zone ────────────────────────────────────────────────────────────
uploadZone.addEventListener("click", () => fileInput.click());
uploadZone.addEventListener("dragover", (e) => { e.preventDefault(); uploadZone.classList.add("drag-over"); });
uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("drag-over"));
uploadZone.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith("image/")) handleFile(file);
});
fileInput.addEventListener("change", () => { if (fileInput.files[0]) handleFile(fileInput.files[0]); });

function handleFile(file) {
  selectedFile = file;
  previewImg.src = URL.createObjectURL(file);
  previewImg.classList.remove("hidden");
  uploadPH.classList.add("hidden");
  matchBtn.disabled = false;
  clearBtn.disabled = false;
  hideResults();
}

clearBtn.addEventListener("click", () => {
  selectedFile = null;
  fileInput.value = "";
  previewImg.src = "";
  previewImg.classList.add("hidden");
  uploadPH.classList.remove("hidden");
  matchBtn.disabled = true;
  clearBtn.disabled = true;
  hideResults();
});

// ─── Run Match ──────────────────────────────────────────────────────────────
matchBtn.addEventListener("click", runMatch);

async function runMatch() {
  if (!selectedFile) return;

  // Get selected gender
  const genderRadio = document.querySelector('input[name="gender"]:checked');
  const gender = genderRadio ? genderRadio.value : "any";

  matchBtn.disabled = true;
  clearBtn.disabled = true;
  matchBtnText.textContent = "Analyzing…";
  matchBtnSpin.classList.remove("hidden");
  showStatus("Uploading image and running face comparison…");
  hideResults();

  try {
    const formData = new FormData();
    formData.append("image", selectedFile);
    formData.append("gender", gender);   // ← send gender to backend

    showStatus("Comparing with suspect database…");

    const response = await fetch("/api/match", { method: "POST", body: formData });
    const data = await response.json();

    if (!data.success) {
      showStatus("Error: " + data.error);
      return;
    }

    const genderLabel = gender === "any" ? "" : ` (${gender} suspects only)`;
    showStatus(`Analysis complete — found ${data.total_found} match(es)${genderLabel}.`);
    renderResults(data.matches);

  } catch (err) {
    console.error(err);
    showStatus("Connection error. Is the Flask server running?");
  } finally {
    matchBtn.disabled = false;
    clearBtn.disabled = false;
    matchBtnText.textContent = "Run Face Match";
    matchBtnSpin.classList.add("hidden");
  }
}

// ─── Render Results ─────────────────────────────────────────────────────────
function renderResults(matches) {
  matchGrid.innerHTML = "";
  if (!matches || matches.length === 0) {
    noMatchCard.classList.remove("hidden");
    return;
  }
  resultsCard.classList.remove("hidden");
  resultsCount.textContent = `${matches.length} suspect${matches.length > 1 ? "s" : ""} shortlisted`;
  resultsNote.textContent =
    `The system found ${matches.length} person${matches.length > 1 ? "s" : ""} with significant facial similarity. ` +
    `Police must investigate further using witness statements and other evidence before confirming identity.`;

  matches.forEach((m, i) => {
    const card = buildMatchCard(m, i + 1);
    matchGrid.appendChild(card);
    setTimeout(() => {
      const fill = card.querySelector(".similarity-fill");
      if (fill) fill.style.width = m.similarity + "%";
    }, 80 * i);
  });
}

function buildMatchCard(m, rank) {
  const pct  = parseFloat(m.similarity);
  const tier = pct >= 80 ? "high" : pct >= 65 ? "mid" : "low";

  const card = document.createElement("div");
  card.className = `match-card ${tier === "high" ? "high-match" : tier === "mid" ? "mid-match" : ""}`;
  card.innerHTML = `
    <div class="match-rank">#${rank}</div>
    <div class="match-avatar">
      ${m.image_file
        ? `<img src="/suspect_images/${m.image_file}" alt="${m.name}" onerror="this.parentElement.innerHTML='👤'">`
        : "👤"}
    </div>
    <div class="match-name">${m.name}</div>
    <div class="match-id">${m.id}</div>
    <div class="similarity-bar-wrap">
      <div class="similarity-label">
        <span>Similarity</span>
        <span class="similarity-pct pct-${tier}">${pct}%</span>
      </div>
      <div class="similarity-bar">
        <div class="similarity-fill fill-${tier}" style="width:0%"></div>
      </div>
    </div>
    <div class="match-city">📍 ${m.city}, ${m.state}</div>
    ${m.crime_history !== "N/A" && m.crime_history !== "None"
      ? `<div class="match-crime-badge">⚠ Prior: ${m.crime_history}</div>` : ""}
    <div class="view-details">View full details →</div>
  `;
  card.addEventListener("click", () => openModal(m));
  return card;
}

// ─── Modal ───────────────────────────────────────────────────────────────────
function openModal(m) {
  modalName.textContent       = m.name;
  modalSimilarity.textContent = `${m.similarity}% match`;
  modalPhoto.innerHTML = m.image_file
    ? `<img src="/suspect_images/${m.image_file}" alt="${m.name}" style="width:100%;height:100%;object-fit:cover;">`
    : "👤";

  const fields = [
    { label: "Suspect ID",        value: m.id },
    { label: "Age",               value: m.age },
    { label: "Gender",            value: m.gender },
    { label: "Phone",             value: m.phone },
    { label: "City",              value: m.city },
    { label: "State",             value: m.state },
    { label: "Aadhaar (partial)", value: m.aadhaar },
    { label: "Crime history",     value: m.crime_history || "None on record" },
    { label: "Full address",      value: m.address, full: true },
  ];
  modalFields.innerHTML = fields.map(f =>
    `<div class="field ${f.full ? "full" : ""}">
      <div class="field-label">${f.label}</div>
      <div class="field-value">${f.value}</div>
    </div>`
  ).join("");

  modalOverlay.classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  modalOverlay.classList.add("hidden");
  document.body.style.overflow = "";
}
modalClose.addEventListener("click", closeModal);
modalOverlay.addEventListener("click", (e) => { if (e.target === modalOverlay) closeModal(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });

function showStatus(msg) {
  statusBar.classList.remove("hidden");
  statusText.textContent = msg;
}
function hideResults() {
  statusBar.classList.add("hidden");
  resultsCard.classList.add("hidden");
  noMatchCard.classList.add("hidden");
  matchGrid.innerHTML = "";
}
