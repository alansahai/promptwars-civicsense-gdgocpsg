/**
 * Citizen Grievance Tracking View.
 * Displays real-time status progression, investigative timeline, SLA indicators,
 * and officer dispatch notes.
 */

"use strict";

import { api } from "../api.js";
import { clear, h } from "../dom.js";
import { t } from "../i18n.js";

function getStatusBadge(status) {
  if (status === "In Progress") return "badge-progress";
  if (status === "Resolved") return "badge-resolved";
  if (status === "Rejected") return "badge-rejected";
  if (status === "Duplicate") return "badge-duplicate";
  return "badge-reported";
}

function getPriorityBadge(priority) {
  if (priority === "Critical") return "badge-critical";
  if (priority === "High") return "badge-high";
  if (priority === "Medium") return "badge-medium";
  return "badge-low";
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

function buildTimelineItem(hItem) {
  return h(
    "div",
    { class: "timeline-item" },
    h("div", { class: "timeline-marker" }),
    h(
      "div",
      { class: "timeline-content" },
      h(
        "div",
        { class: "timeline-header" },
        h("span", { class: `badge ${getStatusBadge(hItem.status)}` }, hItem.status),
        h("span", { class: "timeline-time" }, formatDate(hItem.timestamp))
      ),
      h("p", { class: "timeline-note" }, hItem.note || "Status updated"),
      h("small", { class: "text-muted" }, `By: ${hItem.author}`)
    )
  );
}

function buildMetaGrid(issue) {
  return h(
    "div",
    { class: "detail-meta-grid" },
    h("div", { class: "meta-item" }, h("label", {}, "Category"), h("div", {}, h("strong", {}, issue.category))),
    h("div", { class: "meta-item" }, h("label", {}, "Department"), h("div", {}, h("strong", {}, issue.department))),
    h("div", { class: "meta-item" }, h("label", {}, "Priority Score"), h("div", {}, h("strong", {}, `${issue.priority_score} / 100`))),
    h("div", { class: "meta-item" }, h("label", {}, "SLA Standard"), h("div", {}, h("strong", {}, `${issue.sla_hours} Hours Target`)))
  );
}

function renderIssueDetails(container, issue) {
  clear(container);
  const statusClass = getStatusBadge(issue.status);
  const priorityClass = getPriorityBadge(issue.priority_level);

  const photoNode = issue.photo_data_url
    ? h("div", { class: "detail-photo" }, h("img", { src: issue.photo_data_url, alt: "Civic issue photo", class: "img-responsive" }))
    : null;

  const publicHistory = (issue.status_history || []).filter((it) => it.is_public);
  const timelineNodes = publicHistory.length > 0
    ? publicHistory.map(buildTimelineItem)
    : [h("p", {}, "No timeline updates recorded.")];

  const card = h(
    "div",
    { class: "card issue-detail-card" },
    h(
      "div",
      { class: "detail-header" },
      h(
        "div",
        {},
        h("div", { class: "ticket-id-tag" }, issue.ticket_id),
        h("h2", {}, issue.title),
        h("p", { class: "location-tag" }, `📍 ${issue.address || "Location on record"}`)
      ),
      h(
        "div",
        { class: "header-badges" },
        h("span", { class: `badge ${statusClass} badge-lg` }, issue.status),
        h("span", { class: `badge ${priorityClass} badge-lg` }, issue.priority_level)
      )
    ),
    buildMetaGrid(issue),
    h("div", { class: "detail-body" }, h("h3", {}, "Description"), h("p", { class: "detail-desc-text" }, issue.description), photoNode),
    h("div", { class: "timeline-section" }, h("h3", {}, t("timeline_title")), h("div", { class: "timeline" }, ...timelineNodes))
  );

  container.appendChild(card);
}

async function fetchAndRenderIssue(ticketId, container, errorBox) {
  errorBox.classList.add("hidden");
  clear(container);
  container.appendChild(h("div", { class: "loading-spinner" }, "Loading ticket details..."));

  try {
    const issue = await api.getIssue(ticketId);
    renderIssueDetails(container, issue);
  } catch {
    clear(container);
    errorBox.textContent = `Lookup Error: Ticket ${ticketId} could not be located. Verify the ID format.`;
    errorBox.classList.remove("hidden");
  }
}

function _buildSearchForm(onSearch) {
  const idInput = h("input", {
    type: "text",
    id: "track-id-input",
    class: "form-control",
    placeholder: "e.g. CR-2026-00001",
    required: true,
  });

  const form = h(
    "form",
    {
      id: "track-form",
      class: "track-form",
      onSubmit: (e) => {
        e.preventDefault();
        const id = idInput.value.trim();
        if (id) onSearch(id);
      },
    },
    h(
      "div",
      { class: "form-group" },
      h("label", { for: "track-id-input" }, t("track_input_label")),
      h("div", { class: "input-with-button" }, idInput, h("button", { type: "submit", class: "btn btn-primary" }, t("btn_track")))
    )
  );

  return { form, idInput };
}

export function renderTrackView(container, queryParams) {
  clear(container);

  const errorBox = h("div", { id: "track-error", class: "alert alert-error hidden", role: "alert" });
  const resultArea = h("div", { id: "track-result-area" });

  const { form, idInput } = _buildSearchForm((id) => {
    fetchAndRenderIssue(id, resultArea, errorBox);
  });

  const section = h(
    "section",
    { class: "view-section track-view" },
    h("div", { class: "section-header" }, h("h1", {}, t("track_heading")), h("p", { class: "subtitle" }, t("track_sub"))),
    h("div", { class: "card search-card" }, form, errorBox),
    resultArea
  );

  container.appendChild(section);

  const initialId = queryParams?.get("id");
  if (initialId) {
    idInput.value = initialId;
    fetchAndRenderIssue(initialId, resultArea, errorBox);
  }
}
