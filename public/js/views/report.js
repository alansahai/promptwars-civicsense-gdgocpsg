/**
 * Citizen Grievance Submission View with Client-Side Image Resizing,
 * Geolocation, AI Assist, and Structured Confirmation Card.
 */

import { api } from "../api.js";
import { t } from "../i18n.js";
import { router } from "../router.js";

const SAMPLES = {
  pothole: {
    title: "Deep waterlogged pothole near school entrance",
    description: "Large 2-foot pothole right in front of the primary school gate. Motorcyclists are losing balance and slipping, especially in evening hours. High hazard for school children.",
    category: "Pothole",
    address: "DB Road, near Govt Girls High School, RS Puram, Coimbatore",
    lat: 11.0086,
    lon: 76.9520,
  },
  garbage: {
    title: "Overflowing municipal garbage bin spilling onto pedestrian path",
    description: "Solid waste bin has not been cleared for over 4 days. Vegetable waste and plastic bags are scattered across the street, creating severe foul odor and attracting stray cattle.",
    category: "Overflowing Garbage",
    address: "Crosscut Road, Gandhipuram, Coimbatore",
    lat: 11.0183,
    lon: 76.9644,
  },
  wire: {
    title: "Dangling high-voltage electrical cable sparking on sidewalk",
    description: "Storm winds dislodged the overhead electrical cable. It is hanging down to waist height over the public footpath. Visible sparking occurs when heavy buses pass.",
    category: "Exposed Live Wire",
    address: "Avinashi Road near Lakshmi Mills junction, Coimbatore",
    lat: 11.0210,
    lon: 76.9850,
  },
  water: {
    title: "Municipal drinking water main pipe burst flooding roadway",
    description: "Underground drinking water distribution pipe ruptured with heavy pressure. Fresh water is gushing out and washing away road ballast. Street is impassable.",
    category: "Water Leakage",
    address: "Alagesan Road, Saibaba Colony, Coimbatore",
    lat: 11.0289,
    lon: 76.9458,
  },
  light: {
    title: "Stretch of 4 streetlights broken leaving junction pitch black",
    description: "Streetlights have been non-functional for a week. The entire intersection is dark, causing near-miss pedestrian accidents every evening.",
    category: "Damaged Streetlight",
    address: "Trichy Road, Singanallur, Coimbatore",
    lat: 10.9992,
    lon: 77.0256,
  },
};

export function renderReportView(container) {
  container.innerHTML = "";

  const section = document.createElement("section");
  section.className = "view-section report-view";

  // Section Header
  const header = document.createElement("div");
  header.className = "section-header";
  const h1 = document.createElement("h1");
  h1.setAttribute("data-i18n", "report_heading");
  h1.textContent = t("report_heading");
  const p = document.createElement("p");
  p.className = "subtitle";
  p.setAttribute("data-i18n", "report_sub");
  p.textContent = t("report_sub");
  header.appendChild(h1);
  header.appendChild(p);
  section.appendChild(header);

  // Quick Sample Buttons Container
  const sampleCard = document.createElement("div");
  sampleCard.className = "card sample-card";
  const sampleTitle = document.createElement("p");
  sampleTitle.className = "sample-title";
  sampleTitle.innerHTML = `<strong>${t("sample_title")}</strong>`;
  sampleCard.appendChild(sampleTitle);

  const sampleButtons = document.createElement("div");
  sampleButtons.className = "sample-buttons";
  const samplesList = [
    { key: "pothole", label: "🚧 " + t("sample_pothole") },
    { key: "garbage", label: "🗑️ " + t("sample_garbage") },
    { key: "wire", label: "⚡ " + t("sample_wire") },
    { key: "water", label: "💧 " + t("sample_water") },
    { key: "light", label: "💡 " + t("sample_light") },
  ];

  samplesList.forEach(({ key, label }) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-outline btn-sm sample-btn";
    btn.textContent = label;
    btn.addEventListener("click", () => fillSample(key));
    sampleButtons.appendChild(btn);
  });
  sampleCard.appendChild(sampleButtons);
  section.appendChild(sampleCard);

  // Main Report Form
  const form = document.createElement("form");
  form.className = "report-form card";
  form.id = "report-form";

  // Form body fields
  form.innerHTML = `
    <div class="form-group">
      <label for="rep-desc">${t("lbl_desc")} <span class="required">*</span></label>
      <textarea id="rep-desc" rows="4" required class="form-control" placeholder="${t("lbl_desc_placeholder")}"></textarea>
      <div id="assist-box" class="assist-box hidden" aria-live="polite"></div>
    </div>

    <div class="form-group">
      <label for="rep-title">${t("lbl_title")}</label>
      <input type="text" id="rep-title" class="form-control" placeholder="Brief headline, or leave blank for AI to suggest" />
    </div>

    <div class="form-grid">
      <div class="form-group">
        <label for="rep-category">${t("lbl_category")}</label>
        <select id="rep-category" class="form-control">
          <option value="Let AI decide">${t("lbl_category_ai")}</option>
          <option value="Pothole">Pothole</option>
          <option value="Overflowing Garbage">Overflowing Garbage</option>
          <option value="Damaged Streetlight">Damaged Streetlight</option>
          <option value="Water Leakage">Water Leakage</option>
          <option value="Exposed Live Wire">Exposed Live Wire</option>
          <option value="Stray Animals">Stray Animals</option>
          <option value="Illegal Dumping">Illegal Dumping</option>
          <option value="Sewage Overflow">Sewage Overflow</option>
          <option value="Noise Complaint">Noise Complaint</option>
          <option value="Other">Other</option>
        </select>
      </div>

      <div class="form-group">
        <label for="rep-location">${t("lbl_location")}</label>
        <div class="input-with-button">
          <input type="text" id="rep-location" class="form-control" placeholder="${t("lbl_location_placeholder")}" />
          <button type="button" id="btn-geo" class="btn btn-secondary btn-sm" title="Use current GPS">📍 GPS</button>
        </div>
        <small id="geo-status" class="form-help"></small>
      </div>
    </div>

    <div class="form-grid">
      <div class="form-group">
        <label for="rep-photo">${t("lbl_photo")}</label>
        <input type="file" id="rep-photo" accept="image/jpeg,image/png,image/webp" class="form-control" />
        <small class="form-help">Client-side resized to max 800px JPEG &lt;= 300KB</small>
        <div id="photo-preview" class="photo-preview hidden"></div>
      </div>

      <div class="form-group">
        <label for="rep-name">${t("lbl_name")}</label>
        <input type="text" id="rep-name" class="form-control" placeholder="e.g. Anand Kumar" />
      </div>
    </div>

    <input type="hidden" id="rep-lat" value="" />
    <input type="hidden" id="rep-lon" value="" />

    <div id="form-alert" class="alert hidden" role="alert" aria-live="assertive"></div>

    <div class="form-actions">
      <button type="submit" id="btn-submit" class="btn btn-primary btn-lg">
        <span class="btn-text">${t("btn_submit_report")}</span>
        <span class="spinner hidden" aria-hidden="true"></span>
      </button>
    </div>
  `;

  section.appendChild(form);

  // Container for Confirmation Card after submit
  const confirmContainer = document.createElement("div");
  confirmContainer.id = "confirmation-card-area";
  section.appendChild(confirmContainer);

  container.appendChild(section);

  // Attach Event Handlers
  attachReportHandlers(form, confirmContainer);
}

function fillSample(sampleKey) {
  const data = SAMPLES[sampleKey];
  if (!data) return;

  const descEl = document.getElementById("rep-desc");
  const titleEl = document.getElementById("rep-title");
  const catEl = document.getElementById("rep-category");
  const locEl = document.getElementById("rep-location");
  const latEl = document.getElementById("rep-lat");
  const lonEl = document.getElementById("rep-lon");

  if (descEl) descEl.value = data.description;
  if (titleEl) titleEl.value = data.title;
  if (catEl) catEl.value = data.category;
  if (locEl) locEl.value = data.address;
  if (latEl) latEl.value = data.lat;
  if (lonEl) lonEl.value = data.lon;

  // Scroll to form smoothly
  const form = document.getElementById("report-form");
  if (form) form.scrollIntoView({ behavior: "smooth" });
}

function attachReportHandlers(form, confirmContainer) {
  let photoDataUrl = null;
  let assistDebounce = null;

  // Geolocation button
  const geoBtn = document.getElementById("btn-geo");
  const geoStatus = document.getElementById("geo-status");
  if (geoBtn) {
    geoBtn.addEventListener("click", () => {
      if (!navigator.geolocation) {
        geoStatus.textContent = "Geolocation is not supported by your browser.";
        return;
      }
      geoStatus.textContent = "Acquiring GPS coordinates...";
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          document.getElementById("rep-lat").value = pos.coords.latitude.toFixed(6);
          document.getElementById("rep-lon").value = pos.coords.longitude.toFixed(6);
          geoStatus.textContent = `GPS Captured: (${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)})`;
        },
        (err) => {
          geoStatus.textContent = "Unable to fetch GPS. You may enter landmark manually.";
        },
        { timeout: 8000 }
      );
    });
  }

  // Client-side photo resizing
  const photoInput = document.getElementById("rep-photo");
  const photoPreview = document.getElementById("photo-preview");
  if (photoInput) {
    photoInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (!file) {
        photoDataUrl = null;
        photoPreview.classList.add("hidden");
        return;
      }

      const reader = new FileReader();
      reader.onload = (event) => {
        const img = new Image();
        img.onload = () => {
          const maxDim = 800;
          let width = img.width;
          let height = img.height;
          if (width > maxDim || height > maxDim) {
            if (width > height) {
              height = Math.round((height * maxDim) / width);
              width = maxDim;
            } else {
              width = Math.round((width * maxDim) / height);
              height = maxDim;
            }
          }

          const canvas = document.createElement("canvas");
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext("2d");
          ctx.drawImage(img, 0, 0, width, height);

          // Compress to JPEG with quality 0.75
          photoDataUrl = canvas.toDataURL("image/jpeg", 0.75);

          photoPreview.innerHTML = "";
          const previewImg = document.createElement("img");
          previewImg.src = photoDataUrl;
          previewImg.alt = "Resized upload preview";
          previewImg.className = "img-thumbnail";
          photoPreview.appendChild(previewImg);
          photoPreview.classList.remove("hidden");
        };
        img.src = event.target.result;
      };
      reader.readAsDataURL(file);
    });
  }

  // AI Assist on description change
  const descEl = document.getElementById("rep-desc");
  const assistBox = document.getElementById("assist-box");
  if (descEl && assistBox) {
    descEl.addEventListener("input", () => {
      clearTimeout(assistDebounce);
      const text = descEl.value.trim();
      if (text.length < 25) {
        assistBox.classList.add("hidden");
        return;
      }
      assistDebounce = setTimeout(async () => {
        try {
          const res = await api.getAssist(text);
          renderAssistBox(assistBox, res);
        } catch {
          // Silent fallback on assist error
        }
      }, 900);
    });
  }

  // Form submission
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const alertBox = document.getElementById("form-alert");
    const submitBtn = document.getElementById("btn-submit");
    const btnText = submitBtn.querySelector(".btn-text");
    const spinner = submitBtn.querySelector(".spinner");

    alertBox.className = "alert hidden";
    submitBtn.disabled = true;
    btnText.textContent = "Analyzing & Lodging Grievance...";
    spinner.classList.remove("hidden");

    const description = document.getElementById("rep-desc").value.trim();
    const title = document.getElementById("rep-title").value.trim() || null;
    const categoryVal = document.getElementById("rep-category").value;
    const category = categoryVal === "Let AI decide" ? null : categoryVal;
    const address = document.getElementById("rep-location").value.trim() || null;
    const citizenName = document.getElementById("rep-name").value.trim() || null;
    const lat = parseFloat(document.getElementById("rep-lat").value) || null;
    const lon = parseFloat(document.getElementById("rep-lon").value) || null;

    try {
      const issue = await api.createIssue({
        description,
        title,
        category,
        address,
        citizen_name: citizenName,
        latitude: lat,
        longitude: lon,
        photo_data_url: photoDataUrl,
      });

      // Hide form and show confirmation card
      form.classList.add("hidden");
      renderConfirmationCard(confirmContainer, issue);
      confirmContainer.scrollIntoView({ behavior: "smooth" });
    } catch (err) {
      alertBox.textContent = `Submission Error: ${err.message || "Failed to submit report"}`;
      alertBox.className = "alert alert-error";
      alertBox.classList.remove("hidden");
    } finally {
      submitBtn.disabled = false;
      btnText.textContent = t("btn_submit_report");
      spinner.classList.add("hidden");
    }
  });
}

function renderAssistBox(box, assistData) {
  box.innerHTML = "";
  if (!assistData) return;

  const header = document.createElement("div");
  header.className = "assist-header";
  header.innerHTML = `✨ <strong>AI Suggestion</strong>`;
  box.appendChild(header);

  if (assistData.suggested_title) {
    const titleDiv = document.createElement("div");
    titleDiv.className = "assist-title-row";
    titleDiv.innerHTML = `<span>Title: <em>${escapeHtml(assistData.suggested_title)}</em></span>`;
    const useBtn = document.createElement("button");
    useBtn.type = "button";
    useBtn.className = "btn btn-link btn-sm";
    useBtn.textContent = "Apply Title";
    useBtn.addEventListener("click", () => {
      const titleInput = document.getElementById("rep-title");
      if (titleInput) titleInput.value = assistData.suggested_title;
    });
    titleDiv.appendChild(useBtn);
    box.appendChild(titleDiv);
  }

  if (assistData.clarifying_questions && assistData.clarifying_questions.length > 0) {
    const qList = document.createElement("ul");
    qList.className = "assist-questions";
    assistData.clarifying_questions.forEach((q) => {
      const li = document.createElement("li");
      li.textContent = `💡 ${q}`;
      qList.appendChild(li);
    });
    box.appendChild(qList);
  }

  box.classList.remove("hidden");
}

function renderConfirmationCard(container, issue) {
  container.innerHTML = "";

  const card = document.createElement("div");
  card.className = "card confirmation-card";
  card.setAttribute("role", "status");
  card.setAttribute("aria-live", "polite");

  const aiSourceBadge = issue.ai_analysis?.ai_generated
    ? `<span class="badge badge-ai">⚡ Multimodal Gemini Triaged</span>`
    : `<span class="badge badge-rules">🛡️ Heuristic Rule Triaged</span>`;

  let priorityClass = "badge-low";
  if (issue.priority_level === "Critical") priorityClass = "badge-critical";
  else if (issue.priority_level === "High") priorityClass = "badge-high";
  else if (issue.priority_level === "Medium") priorityClass = "badge-medium";

  // Priority factors breakdown list
  const factorsHtml = (issue.priority_breakdown || [])
    .map((f) => `<li><strong>${escapeHtml(f.factor)} (+${f.points} pts):</strong> ${escapeHtml(f.explanation)}</li>`)
    .join("");

  // Duplicates list if any
  let dupsHtml = "";
  if (issue.duplicates && issue.duplicates.length > 0) {
    dupsHtml = `
      <div class="duplicate-alert-box">
        <h4>⚠️ Potential Duplicate Issues Nearby (${issue.duplicates.length})</h4>
        <p class="small text-muted">Similar issues reported nearby have been cross-referenced.</p>
        <ul>
          ${issue.duplicates
            .map(
              (d) =>
                `<li><a href="#/track?id=${encodeURIComponent(d.ticket_id)}">${escapeHtml(d.ticket_id)}</a> - ${escapeHtml(d.title)} (${d.distance_meters}m away)</li>`
            )
            .join("")}
        </ul>
      </div>
    `;
  }

  card.innerHTML = `
    <div class="confirm-header">
      <div class="confirm-icon">✅</div>
      <div>
        <h2>${t("confirm_title")}</h2>
        <div class="ticket-display">
          <span>${t("confirm_ticket")}</span>
          <strong class="ticket-id-highlight">${escapeHtml(issue.ticket_id)}</strong>
          ${aiSourceBadge}
        </div>
      </div>
    </div>

    <div class="confirm-grid">
      <div class="confirm-item">
        <label>${t("confirm_category")}</label>
        <div><strong>${escapeHtml(issue.category)}</strong></div>
      </div>
      <div class="confirm-item">
        <label>${t("confirm_priority")}</label>
        <div><span class="badge ${priorityClass}">${escapeHtml(issue.priority_level)} (${issue.priority_score}/100)</span></div>
      </div>
      <div class="confirm-item">
        <label>${t("confirm_dept")}</label>
        <div><strong>${escapeHtml(issue.department)}</strong></div>
      </div>
      <div class="confirm-item">
        <label>${t("confirm_sla")}</label>
        <div><strong>${issue.sla_hours} Hours Target</strong></div>
      </div>
    </div>

    <div class="priority-breakdown-box">
      <h3>${t("confirm_why_priority")}</h3>
      <ul class="factors-list">
        ${factorsHtml || "<li>Standard baseline triage calculation applied.</li>"}
      </ul>
    </div>

    ${dupsHtml}

    <div class="confirm-actions">
      <a href="#/track?id=${encodeURIComponent(issue.ticket_id)}" class="btn btn-primary btn-lg">${t("btn_track_this")}</a>
      <button type="button" id="btn-report-another" class="btn btn-outline btn-lg">${t("btn_report_another")}</button>
    </div>
  `;

  container.appendChild(card);

  const anotherBtn = document.getElementById("btn-report-another");
  if (anotherBtn) {
    anotherBtn.addEventListener("click", () => {
      router.navigate("/report");
      window.location.reload();
    });
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
