/**
 * Citizen Grievance Tracking View.
 * Displays real-time status progression, investigative timeline, SLA indicators,
 * and officer dispatch notes.
 */

import { api } from "../api.js";
import { t } from "../i18n.js";

export function renderTrackView(container, queryParams) {
  container.innerHTML = "";

  const section = document.createElement("section");
  section.className = "view-section track-view";

  const header = document.createElement("div");
  header.className = "section-header";
  header.innerHTML = `
    <h1>${t("track_heading")}</h1>
    <p class="subtitle">${t("track_sub")}</p>
  `;
  section.appendChild(header);

  // Search box
  const searchCard = document.createElement("div");
  searchCard.className = "card search-card";
  searchCard.innerHTML = `
    <form id="track-form" class="track-form">
      <div class="form-group">
        <label for="track-id-input">${t("track_input_label")}</label>
        <div class="input-with-button">
          <input type="text" id="track-id-input" class="form-control" placeholder="e.g. CR-2026-00001" required />
          <button type="submit" class="btn btn-primary">${t("btn_track")}</button>
        </div>
      </div>
    </form>
    <div id="track-error" class="alert alert-error hidden" role="alert"></div>
  `;
  section.appendChild(searchCard);

  // Results area
  const resultArea = document.createElement("div");
  resultArea.id = "track-result-area";
  section.appendChild(resultArea);

  container.appendChild(section);

  const form = document.getElementById("track-form");
  const input = document.getElementById("track-id-input");
  const errorBox = document.getElementById("track-error");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = input.value.trim();
    if (!id) return;
    await fetchAndRenderIssue(id, resultArea, errorBox);
  });

  // Auto-fill from query parameter e.g. #/track?id=CR-2026-00001
  const initialId = queryParams?.get("id");
  if (initialId) {
    input.value = initialId;
    fetchAndRenderIssue(initialId, resultArea, errorBox);
  }
}

async function fetchAndRenderIssue(ticketId, container, errorBox) {
  errorBox.classList.add("hidden");
  container.innerHTML = `<div class="loading-spinner">Loading ticket details...</div>`;

  try {
    const issue = await api.getIssue(ticketId);
    renderIssueDetails(container, issue);
  } catch (err) {
    container.innerHTML = "";
    errorBox.textContent = `Lookup Error: Ticket ${ticketId} could not be located. Verify the ID format.`;
    errorBox.classList.remove("hidden");
  }
}

function renderIssueDetails(container, issue) {
  container.innerHTML = "";

  const card = document.createElement("div");
  card.className = "card issue-detail-card";

  let priorityClass = "badge-low";
  if (issue.priority_level === "Critical") priorityClass = "badge-critical";
  else if (issue.priority_level === "High") priorityClass = "badge-high";
  else if (issue.priority_level === "Medium") priorityClass = "badge-medium";

  let statusClass = "badge-reported";
  if (issue.status === "In Progress") statusClass = "badge-progress";
  else if (issue.status === "Resolved") statusClass = "badge-resolved";
  else if (issue.status === "Rejected") statusClass = "badge-rejected";
  else if (issue.status === "Duplicate") statusClass = "badge-duplicate";

  const photoHtml = issue.photo_data_url
    ? `<div class="detail-photo"><img src="${issue.photo_data_url}" alt="Civic issue photo" class="img-responsive" /></div>`
    : "";

  // Timeline items
  const historyHtml = (issue.status_history || [])
    .filter((h) => h.is_public)
    .map(
      (h) => `
        <div class="timeline-item">
          <div class="timeline-marker"></div>
          <div class="timeline-content">
            <div class="timeline-header">
              <span class="badge ${getStatusBadge(h.status)}">${escapeHtml(h.status)}</span>
              <span class="timeline-time">${formatDate(h.timestamp)}</span>
            </div>
            <p class="timeline-note">${escapeHtml(h.note || "Status updated")}</p>
            <small class="text-muted">By: ${escapeHtml(h.author)}</small>
          </div>
        </div>
      `
    )
    .join("");

  card.innerHTML = `
    <div class="detail-header">
      <div>
        <div class="ticket-id-tag">${escapeHtml(issue.ticket_id)}</div>
        <h2>${escapeHtml(issue.title)}</h2>
        <p class="location-tag">📍 ${escapeHtml(issue.address || "Location on record")}</p>
      </div>
      <div class="header-badges">
        <span class="badge ${statusClass} badge-lg">${escapeHtml(issue.status)}</span>
        <span class="badge ${priorityClass} badge-lg">${escapeHtml(issue.priority_level)}</span>
      </div>
    </div>

    <div class="detail-meta-grid">
      <div class="meta-item">
        <label>Category</label>
        <div><strong>${escapeHtml(issue.category)}</strong></div>
      </div>
      <div class="meta-item">
        <label>Department</label>
        <div><strong>${escapeHtml(issue.department)}</strong></div>
      </div>
      <div class="meta-item">
        <label>Priority Score</label>
        <div><strong>${issue.priority_score} / 100</strong></div>
      </div>
      <div class="meta-item">
        <label>SLA Standard</label>
        <div><strong>${issue.sla_hours} Hours Target</strong></div>
      </div>
    </div>

    <div class="detail-body">
      <h3>Description</h3>
      <p class="detail-desc-text">${escapeHtml(issue.description)}</p>
      ${photoHtml}
    </div>

    <div class="timeline-section">
      <h3>${t("timeline_title")}</h3>
      <div class="timeline">
        ${historyHtml || "<p>No timeline updates recorded.</p>"}
      </div>
    </div>
  `;

  container.appendChild(card);
}

function getStatusBadge(status) {
  if (status === "In Progress") return "badge-progress";
  if (status === "Resolved") return "badge-resolved";
  if (status === "Rejected") return "badge-rejected";
  if (status === "Duplicate") return "badge-duplicate";
  return "badge-reported";
}

function formatDate(isoStr) {
  if (!isoStr) return "";
  try {
    const d = new Date(isoStr);
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoStr;
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
