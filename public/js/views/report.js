/**
 * Citizen Grievance Submission View.
 *
 * Implements client-side image resizing, HTML5 geolocation,
 * live AI description enhancement, and structured triage confirmation.
 * Constructed strictly via safe DOM elements without innerHTML.
 */

import { api } from "../api.js";
import { clear, h } from "../dom.js";
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

/**
 * Render the main Citizen Grievance Reporting surface.
 * @param {HTMLElement} container - Host container element.
 */
export function renderReportView(container) {
  clear(container);

  const section = h(
    "section",
    { className: "view-section report-view" },
    h(
      "div",
      { className: "section-header" },
      h("h1", { "data-i18n": "report_heading" }, t("report_heading")),
      h("p", { className: "subtitle", "data-i18n": "report_sub" }, t("report_sub"))
    ),
    _buildSampleCards(),
    _buildReportForm(),
    h("div", { id: "confirmation-card-area" })
  );

  container.appendChild(section);

  const form = section.querySelector("#report-form");
  const confirmArea = section.querySelector("#confirmation-card-area");
  _attachReportHandlers(form, confirmArea);
}

/**
 * Build quick sample report selection buttons.
 * @returns {HTMLElement} Sample selector card.
 */
function _buildSampleCards() {
  const samplesList = [
    { key: "pothole", label: "🚧 " + t("sample_pothole") },
    { key: "garbage", label: "🗑️ " + t("sample_garbage") },
    { key: "wire", label: "⚡ " + t("sample_wire") },
    { key: "water", label: "💧 " + t("sample_water") },
    { key: "light", label: "💡 " + t("sample_light") },
  ];

  return h(
    "div",
    { className: "card sample-card" },
    h("p", { className: "sample-title" }, h("strong", {}, t("sample_title"))),
    h(
      "div",
      { className: "sample-buttons" },
      ...samplesList.map(({ key, label }) =>
        h("button", {
          type: "button",
          className: "btn btn-outline btn-sm sample-btn",
          onclick: () => _fillSample(key),
        }, label)
      )
    )
  );
}

/**
 * Populate report form fields with preset sample data.
 * @param {string} sampleKey - Key matching SAMPLES constant.
 */
function _fillSample(sampleKey) {
  const data = SAMPLES[sampleKey];
  if (!data) return;

  const fields = {
    "rep-desc": data.description,
    "rep-title": data.title,
    "rep-category": data.category,
    "rep-location": data.address,
    "rep-lat": String(data.lat),
    "rep-lon": String(data.lon),
  };

  for (const [id, val] of Object.entries(fields)) {
    const el = document.getElementById(id);
    if (el) el.value = val;
  }

  const form = document.getElementById("report-form");
  if (form) form.scrollIntoView({ behavior: "smooth" });
}

/**
 * Construct the comprehensive report submission form.
 * @returns {HTMLFormElement} Complete grievance form element.
 */
function _buildReportForm() {
  return h(
    "form",
    { className: "report-form card", id: "report-form" },
    _buildDescriptionField(),
    _buildTitleField(),
    _buildCategoryLocationGrid(),
    _buildPhotoNameGrid(),
    h("input", { type: "hidden", id: "rep-lat", value: "" }),
    h("input", { type: "hidden", id: "rep-lon", value: "" }),
    h("div", { id: "form-alert", className: "alert hidden", role: "alert", "aria-live": "assertive" }),
    _buildFormSubmitActions()
  );
}

function _buildDescriptionField() {
  return h(
    "div",
    { className: "form-group" },
    h("label", { for: "rep-desc" }, t("lbl_desc"), " ", h("span", { className: "required" }, "*")),
    h("textarea", {
      id: "rep-desc",
      rows: 4,
      required: true,
      className: "form-control",
      placeholder: t("lbl_desc_placeholder"),
    }),
    h("div", { id: "assist-box", className: "assist-box hidden", "aria-live": "polite" })
  );
}

function _buildTitleField() {
  return h(
    "div",
    { className: "form-group" },
    h("label", { for: "rep-title" }, t("lbl_title")),
    h("input", {
      type: "text",
      id: "rep-title",
      className: "form-control",
      placeholder: "Brief headline, or leave blank for AI to suggest",
    })
  );
}

function _buildCategorySelect() {
  const categories = [
    ["Let AI decide", t("lbl_category_ai")],
    ["Pothole", "Pothole"],
    ["Overflowing Garbage", "Overflowing Garbage"],
    ["Damaged Streetlight", "Damaged Streetlight"],
    ["Water Leakage", "Water Leakage"],
    ["Exposed Live Wire", "Exposed Live Wire"],
    ["Stray Animals", "Stray Animals"],
    ["Illegal Dumping", "Illegal Dumping"],
    ["Sewage Overflow", "Sewage Overflow"],
    ["Noise Complaint", "Noise Complaint"],
    ["Other", "Other"],
  ];
  return h(
    "div",
    { className: "form-group" },
    h("label", { for: "rep-category" }, t("lbl_category")),
    h(
      "select",
      { id: "rep-category", className: "form-control" },
      ...categories.map(([val, label]) => h("option", { value: val }, label))
    )
  );
}

function _buildLocationInput() {
  return h(
    "div",
    { className: "form-group" },
    h("label", { for: "rep-location" }, t("lbl_location")),
    h(
      "div",
      { className: "input-with-button" },
      h("input", {
        type: "text",
        id: "rep-location",
        className: "form-control",
        placeholder: t("lbl_location_placeholder"),
      }),
      h("button", {
        type: "button",
        id: "btn-geo",
        className: "btn btn-secondary btn-sm",
        title: "Use current GPS",
      }, "📍 GPS")
    ),
    h("small", { id: "geo-status", className: "form-help" })
  );
}

function _buildCategoryLocationGrid() {
  return h("div", { className: "form-grid" }, _buildCategorySelect(), _buildLocationInput());
}

function _buildPhotoNameGrid() {
  return h(
    "div",
    { className: "form-grid" },
    h(
      "div",
      { className: "form-group" },
      h("label", { for: "rep-photo" }, t("lbl_photo")),
      h("input", {
        type: "file",
        id: "rep-photo",
        accept: "image/jpeg,image/png,image/webp",
        className: "form-control",
      }),
      h("small", { className: "form-help" }, "Client-side resized to max 800px JPEG <= 300KB"),
      h("div", { id: "photo-preview", className: "photo-preview hidden" })
    ),
    h(
      "div",
      { className: "form-group" },
      h("label", { for: "rep-name" }, t("lbl_name")),
      h("input", {
        type: "text",
        id: "rep-name",
        className: "form-control",
        placeholder: "e.g. Anand Kumar",
      })
    )
  );
}

function _buildFormSubmitActions() {
  return h(
    "div",
    { className: "form-actions" },
    h(
      "button",
      { type: "submit", id: "btn-submit", className: "btn btn-primary btn-lg" },
      h("span", { className: "btn-text" }, t("btn_submit_report")),
      h("span", { className: "spinner hidden", "aria-hidden": "true" })
    )
  );
}

/**
 * Bind interactive events for geolocation, image preview, AI assist, and submission.
 */
function _attachReportHandlers(form, confirmContainer) {
  let photoDataUrl = null;

  _bindGeolocation();
  _bindPhotoResizer((dataUrl) => {
    photoDataUrl = dataUrl;
  });
  _bindAiAssist();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    await _handleFormSubmit(form, confirmContainer, photoDataUrl);
  });
}

function _bindGeolocation() {
  const geoBtn = document.getElementById("btn-geo");
  const geoStatus = document.getElementById("geo-status");
  if (!geoBtn || !geoStatus) return;

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
      () => {
        geoStatus.textContent = "Unable to fetch GPS. You may enter landmark manually.";
      },
      { timeout: 8000 }
    );
  });
}

function _bindPhotoResizer(onPhotoProcessed) {
  const photoInput = document.getElementById("rep-photo");
  const photoPreview = document.getElementById("photo-preview");
  if (!photoInput || !photoPreview) return;

  photoInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) {
      onPhotoProcessed(null);
      photoPreview.classList.add("hidden");
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        const compressed = _compressImage(img);
        onPhotoProcessed(compressed);
        clear(photoPreview);
        photoPreview.appendChild(
          h("img", {
            src: compressed,
            alt: "Resized upload preview",
            className: "img-thumbnail",
          })
        );
        photoPreview.classList.remove("hidden");
      };
      img.src = event.target.result;
    };
    reader.readAsDataURL(file);
  });
}

function _compressImage(img) {
  const maxDim = 800;
  let { width, height } = img;
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
  return canvas.toDataURL("image/jpeg", 0.75);
}

function _bindAiAssist() {
  const descEl = document.getElementById("rep-desc");
  const assistBox = document.getElementById("assist-box");
  if (!descEl || !assistBox) return;

  let debounceTimer = null;
  descEl.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const text = descEl.value.trim();
    if (text.length < 25) {
      assistBox.classList.add("hidden");
      return;
    }
    debounceTimer = setTimeout(async () => {
      try {
        const res = await api.getAssist(text);
        _renderAssistBox(assistBox, res);
      } catch {
        // Silent fallback on assist timeout or service absence
      }
    }, 900);
  });
}

function _renderAssistBox(box, assistData) {
  clear(box);
  if (!assistData) return;

  const children = [
    h("div", { className: "assist-header" }, "✨ ", h("strong", {}, "AI Suggestion")),
  ];

  if (assistData.suggested_title) {
    children.push(
      h(
        "div",
        { className: "assist-title-row" },
        h("span", {}, "Title: ", h("em", {}, assistData.suggested_title)),
        h("button", {
          type: "button",
          className: "btn btn-link btn-sm",
          onclick: () => {
            const titleInput = document.getElementById("rep-title");
            if (titleInput) titleInput.value = assistData.suggested_title;
          },
        }, "Apply Title")
      )
    );
  }

  if (assistData.clarifying_questions && assistData.clarifying_questions.length > 0) {
    children.push(
      h(
        "ul",
        { className: "assist-questions" },
        ...assistData.clarifying_questions.map((q) => h("li", {}, `💡 ${q}`))
      )
    );
  }

  children.forEach((c) => box.appendChild(c));
  box.classList.remove("hidden");
}

async function _handleFormSubmit(form, confirmContainer, photoDataUrl) {
  const alertBox = document.getElementById("form-alert");
  const submitBtn = document.getElementById("btn-submit");
  const btnText = submitBtn.querySelector(".btn-text");
  const spinner = submitBtn.querySelector(".spinner");

  alertBox.className = "alert hidden";
  submitBtn.disabled = true;
  btnText.textContent = "Analyzing & Lodging Grievance...";
  spinner.classList.remove("hidden");

  const payload = _extractFormData(photoDataUrl);

  try {
    const issue = await api.createIssue(payload);
    form.classList.add("hidden");
    _renderConfirmationCard(confirmContainer, issue);
    confirmContainer.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    clear(alertBox);
    alertBox.textContent = `Submission Error: ${err.message || "Failed to submit report"}`;
    alertBox.className = "alert alert-error";
    alertBox.classList.remove("hidden");
  } finally {
    submitBtn.disabled = false;
    btnText.textContent = t("btn_submit_report");
    spinner.classList.add("hidden");
  }
}

function _extractFormData(photoDataUrl) {
  const categoryVal = document.getElementById("rep-category").value;
  return {
    description: document.getElementById("rep-desc").value.trim(),
    title: document.getElementById("rep-title").value.trim() || null,
    category: categoryVal === "Let AI decide" ? null : categoryVal,
    address: document.getElementById("rep-location").value.trim() || null,
    citizen_name: document.getElementById("rep-name").value.trim() || null,
    latitude: parseFloat(document.getElementById("rep-lat").value) || null,
    longitude: parseFloat(document.getElementById("rep-lon").value) || null,
    photo_data_url: photoDataUrl,
  };
}

function _renderConfirmationCard(container, issue) {
  clear(container);

  const card = h(
    "div",
    { className: "card confirmation-card", role: "status", "aria-live": "polite" },
    _buildConfirmHeader(issue),
    _buildConfirmGrid(issue),
    _buildPriorityFactorsBox(issue),
    _buildDuplicatesBox(issue.duplicates),
    _buildConfirmActions(issue.ticket_id)
  );

  container.appendChild(card);
}

function _buildConfirmHeader(issue) {
  const aiBadge = issue.ai_analysis?.ai_generated
    ? h("span", { className: "badge badge-ai" }, "⚡ Multimodal Gemini Triaged")
    : h("span", { className: "badge badge-rules" }, "🛡️ Heuristic Rule Triaged");

  return h(
    "div",
    { className: "confirm-header" },
    h("div", { className: "confirm-icon" }, "✅"),
    h(
      "div",
      {},
      h("h2", {}, t("confirm_title")),
      h(
        "div",
        { className: "ticket-display" },
        h("span", {}, t("confirm_ticket"), " "),
        h("strong", { className: "ticket-id-highlight" }, issue.ticket_id),
        " ",
        aiBadge
      )
    )
  );
}

function _buildConfirmGrid(issue) {
  const pBadgeClass = _getPriorityBadgeClass(issue.priority_level);

  return h(
    "div",
    { className: "confirm-grid" },
    h("div", { className: "confirm-item" }, h("label", {}, t("confirm_category")), h("div", {}, h("strong", {}, issue.category))),
    h("div", { className: "confirm-item" }, h("label", {}, t("confirm_priority")), h("div", {}, h("span", { className: `badge ${pBadgeClass}` }, `${issue.priority_level} (${issue.priority_score}/100)`))),
    h("div", { className: "confirm-item" }, h("label", {}, t("confirm_dept")), h("div", {}, h("strong", {}, issue.department))),
    h("div", { className: "confirm-item" }, h("label", {}, t("confirm_sla")), h("div", {}, h("strong", {}, `${issue.sla_hours} Hours Target`)))
  );
}

function _getPriorityBadgeClass(level) {
  if (level === "Critical") return "badge-critical";
  if (level === "High") return "badge-high";
  if (level === "Medium") return "badge-medium";
  return "badge-low";
}

function _buildPriorityFactorsBox(issue) {
  const factors = issue.priority_breakdown || [];
  const listItems = factors.length > 0
    ? factors.map((f) =>
        h("li", {}, h("strong", {}, `${f.factor} (+${f.points} pts): `), f.explanation)
      )
    : [h("li", {}, "Standard baseline triage calculation applied.")];

  return h(
    "div",
    { className: "priority-breakdown-box" },
    h("h3", {}, t("confirm_why_priority")),
    h("ul", { className: "factors-list" }, ...listItems)
  );
}

function _buildDuplicatesBox(duplicates) {
  if (!duplicates || duplicates.length === 0) return null;

  return h(
    "div",
    { className: "duplicate-alert-box" },
    h("h4", {}, `⚠️ Potential Duplicate Issues Nearby (${duplicates.length})`),
    h("p", { className: "small text-muted" }, "Similar issues reported nearby have been cross-referenced."),
    h(
      "ul",
      {},
      ...duplicates.map((d) =>
        h("li", {},
          h("a", { href: `#/track?id=${encodeURIComponent(d.ticket_id)}` }, d.ticket_id),
          ` - ${d.title} (${d.distance_meters}m away)`
        )
      )
    )
  );
}

function _buildConfirmActions(ticketId) {
  return h(
    "div",
    { className: "confirm-actions" },
    h("a", {
      href: `#/track?id=${encodeURIComponent(ticketId)}`,
      className: "btn btn-primary btn-lg",
    }, t("btn_track_this")),
    h("button", {
      type: "button",
      id: "btn-report-another",
      className: "btn btn-outline btn-lg",
      onclick: () => {
        router.navigate("/report");
        window.location.reload();
      },
    }, t("btn_report_another"))
  );
}
