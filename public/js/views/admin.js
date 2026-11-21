/**
 * Protected Municipal Administrative Console View.
 *
 * Provides issue management, AI overrides, status workflow transitions,
 * workload distribution metrics, and Gemini-generated weekly operational summaries.
 * Built entirely with safe DOM constructors with zero innerHTML.
 */

import { api, getAuthToken, setAuthToken } from "../api.js";
import { openModal } from "../components/modal.js";
import { clear, h } from "../dom.js";
import { t } from "../i18n.js";

/**
 * Render administrative portal entry (login or dashboard).
 * @param {HTMLElement} container - Host container element.
 */
export async function renderAdminView(container) {
  clear(container);

  const section = h("section", { className: "view-section admin-view" });
  container.appendChild(section);

  const token = getAuthToken();
  if (!token) {
    _renderLoginForm(section);
  } else {
    await _renderDashboardContent(section);
  }
}

function _renderLoginForm(container) {
  clear(container);

  const formEl = _buildLoginFormElements();
  const wrapper = h(
    "div",
    { className: "admin-login-wrapper" },
    h(
      "div",
      { className: "card login-card" },
      h(
        "div",
        { className: "login-header" },
        h("div", { className: "login-icon" }, "🔒"),
        h("h2", {}, t("admin_login_title")),
        h("p", { className: "subtitle" }, t("admin_login_sub"))
      ),
      h(
        "div",
        { className: "demo-auth-pill" },
        h("span", {}, "Demo Password: "),
        h("code", {}, "civic-demo-2026")
      ),
      formEl
    )
  );

  container.appendChild(wrapper);
  _bindLoginSubmit(formEl, container);
}

function _buildLoginFormElements() {
  return h(
    "form",
    { id: "admin-login-form" },
    h(
      "div",
      { className: "form-group" },
      h("label", { for: "admin-pwd" }, t("admin_pwd_label")),
      h("input", {
        type: "password",
        id: "admin-pwd",
        className: "form-control",
        value: "civic-demo-2026",
        required: true,
        autofocus: true,
      })
    ),
    h("div", { id: "login-error", className: "alert alert-error hidden", role: "alert" }),
    h(
      "button",
      { type: "submit", id: "btn-login-submit", className: "btn btn-primary btn-block" },
      h("span", { className: "btn-text" }, t("btn_login")),
      h("span", { className: "spinner hidden", "aria-hidden": "true" })
    )
  );
}

function _bindLoginSubmit(form, container) {
  const pwdInput = form.querySelector("#admin-pwd");
  const errorBox = form.querySelector("#login-error");
  const submitBtn = form.querySelector("#btn-login-submit");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorBox.classList.add("hidden");
    submitBtn.disabled = true;

    try {
      const res = await api.login(pwdInput.value);
      setAuthToken(res.token);
      renderAdminView(container.parentElement);
    } catch (err) {
      errorBox.textContent = err.message || "Invalid administrative credentials.";
      errorBox.classList.remove("hidden");
    } finally {
      submitBtn.disabled = false;
    }
  });
}

async function _renderDashboardContent(container) {
  clear(container);

  container.appendChild(_buildAdminHeaderBar(container));
  container.appendChild(
    h(
      "div",
      { id: "admin-analytics-area", className: "admin-analytics-area" },
      h("div", { className: "loading-spinner" }, "Loading operational analytics...")
    )
  );
  container.appendChild(_buildAdminTableCard());

  await _loadAdminData();
}

function _buildAdminHeaderBar(container) {
  return h(
    "div",
    { className: "admin-header-bar" },
    h(
      "div",
      {},
      h("h1", {}, t("admin_heading")),
      h("p", { className: "subtitle" }, "Operational Dispatch & Departmental Workflow Console")
    ),
    h(
      "div",
      { className: "admin-top-actions" },
      h(
        "button",
        {
          id: "btn-summary",
          className: "btn btn-secondary",
          onclick: () => _openSummaryModal(),
        },
        `✨ ${t("btn_generate_summary")}`
      ),
      h(
        "button",
        {
          id: "btn-logout",
          className: "btn btn-outline",
          onclick: async () => {
            try {
              await api.logout();
            } catch {}
            setAuthToken(null);
            renderAdminView(container.parentElement);
          },
        },
        t("btn_logout")
      )
    )
  );
}

function _buildAdminTableCard() {
  return h(
    "div",
    { className: "card admin-table-card" },
    h(
      "div",
      { className: "table-header" },
      h("h2", {}, t("admin_issues_title")),
      h("small", { className: "text-muted" }, "Sorted deterministically by priority score, then age")
    ),
    h(
      "div",
      { id: "admin-table-container", className: "table-responsive" },
      h("div", { className: "loading-spinner" }, "Loading grievances...")
    )
  );
}

async function _loadAdminData() {
  try {
    const [analytics, issues] = await Promise.all([
      api.getAdminAnalytics(),
      api.listAdminIssues(),
    ]);

    _renderAnalytics(analytics);
    _renderAdminTable(issues);
  } catch (err) {
    if (err.status === 401) {
      setAuthToken(null);
      renderAdminView(document.querySelector(".admin-view")?.parentElement || document.body);
      return;
    }
    const container = document.getElementById("admin-table-container");
    if (container) {
      clear(container);
      container.appendChild(
        h("div", { className: "alert alert-error" }, `Failed to load dispatch data: ${err.message}`)
      );
    }
  }
}

function _renderAnalytics(analytics) {
  const container = document.getElementById("admin-analytics-area");
  if (!container) return;

  clear(container);
  container.appendChild(_buildWorkloadCard(analytics.department_workload || {}));
  container.appendChild(_buildSummaryMiniCards(analytics));
}

function _buildWorkloadCard(workload) {
  const items = Object.entries(workload);
  const content = items.length > 0
    ? items.map(([dept, count]) =>
        h(
          "div",
          { className: "workload-item" },
          h("span", { className: "dept-name" }, dept),
          h("span", { className: "badge badge-progress" }, `${count.open} open`),
          h("span", { className: "badge badge-resolved" }, `${count.resolved} resolved`)
        )
      )
    : [h("p", {}, "No workload data.")];

  return h(
    "div",
    { className: "analytics-card card" },
    h("h3", {}, "Departmental Workload Distribution"),
    h("div", { className: "workload-grid" }, ...content)
  );
}

function _buildSummaryMiniCards(analytics) {
  const overdueClass = analytics.overdue_count > 0 ? "stat-warn" : "";
  return h(
    "div",
    { className: "analytics-summary-cards" },
    h(
      "div",
      { className: `card mini-stat-card ${overdueClass}`.trim() },
      h("div", { className: "stat-label" }, "SLA Breached / Overdue"),
      h("div", { className: "stat-val" }, String(analytics.overdue_count)),
      h("div", { className: "stat-sub" }, "Tickets exceeding resolution target")
    ),
    h(
      "div",
      { className: "card mini-stat-card" },
      h("div", { className: "stat-label" }, "Admin Overrides"),
      h("div", { className: "stat-val" }, `${analytics.admin_override_count} (${analytics.admin_override_rate_percent}%)`),
      h("div", { className: "stat-sub" }, "Superintendent overrides applied")
    )
  );
}

function _renderAdminTable(issues) {
  const container = document.getElementById("admin-table-container");
  if (!container) return;

  clear(container);
  if (issues.length === 0) {
    container.appendChild(h("p", { className: "no-data" }, "No grievances in queue."));
    return;
  }

  const table = h(
    "table",
    { className: "data-table admin-table" },
    _buildAdminTableHeader(),
    h("tbody", {}, ...issues.map(_buildAdminTableRow))
  );

  container.appendChild(table);
}

function _buildAdminTableHeader() {
  return h(
    "thead",
    {},
    h(
      "tr",
      {},
      h("th", {}, "Ticket"),
      h("th", {}, "Title"),
      h("th", {}, "Category"),
      h("th", {}, "Priority"),
      h("th", {}, "Department"),
      h("th", {}, "Status"),
      h("th", {}, "Action")
    )
  );
}

function _buildAdminTableRow(it) {
  const pBadge = _getPriorityBadgeClass(it.priority_level);
  const sBadge = _getStatusBadgeClass(it.status);

  return h(
    "tr",
    {},
    h("td", {}, h("strong", {}, it.ticket_id)),
    h("td", {}, it.title),
    h("td", {}, h("span", { className: "tag" }, it.category)),
    h("td", {}, h("span", { className: `badge ${pBadge}` }, `${it.priority_level} (${it.priority_score})`)),
    h("td", {}, it.department),
    h("td", {}, h("span", { className: `badge ${sBadge}` }, it.status)),
    h(
      "td",
      {},
      h(
        "button",
        {
          type: "button",
          className: "btn btn-outline btn-sm btn-manage",
          onclick: () => _openManageModal(it.ticket_id),
        },
        "Manage"
      )
    )
  );
}

async function _openManageModal(ticketId) {
  const contentNode = h(
    "div",
    { className: "manage-modal-content" },
    h("div", { className: "loading-spinner" }, "Loading issue details...")
  );

  const modal = openModal({
    title: `Manage Grievance [${ticketId}]`,
    contentNode,
    onClose: () => {},
  });

  try {
    const issue = await api.getIssue(ticketId);
    clear(contentNode);
    _renderManageForm(contentNode, issue, modal);
  } catch (err) {
    clear(contentNode);
    contentNode.appendChild(
      h("div", { className: "alert alert-error" }, `Failed to load issue: ${err.message}`)
    );
  }
}

function _renderManageForm(container, issue, modal) {
  const grid = h(
    "div",
    { className: "manage-grid" },
    _buildManageInfoCol(issue),
    _buildManageActionsCol(issue, modal)
  );
  container.appendChild(grid);
}

function _buildManageInfoCol(issue) {
  const ai = issue.ai_analysis;
  const col = h(
    "div",
    { className: "manage-info" },
    h("h3", {}, issue.title),
    h("p", { className: "text-muted" }, `Reported on ${new Date(issue.created_at).toLocaleString()}`),
    h("p", {}, h("strong", {}, "Description: "), issue.description),
    h("p", {}, h("strong", {}, "Address: "), issue.address || "None specified")
  );

  if (issue.photo_data_url) {
    col.appendChild(
      h(
        "div",
        { className: "modal-photo" },
        h("img", { src: issue.photo_data_url, alt: "Civic Photo", className: "img-responsive" })
      )
    );
  }

  col.appendChild(_buildAiAssessmentCard(ai));
  return col;
}

function _buildAiAssessmentCard(ai) {
  return h(
    "div",
    { className: "ai-analysis-card card" },
    h("h4", {}, "🤖 AI Triage Assessment"),
    h("p", {}, h("strong", {}, "Reasoning: "), ai?.reasoning || "Standard classification"),
    h("p", {}, h("strong", {}, "Confidence: "), `${ai ? Math.round(ai.confidence * 100) : 90}%`),
    h("p", {}, h("strong", {}, "Safety Hazard: "), ai?.safety_risk ? "⚠️ YES - Flagged" : "No immediate peril"),
    h("p", {}, h("strong", {}, "Urgency Tier: "), ai?.urgency || "Standard")
  );
}

function _buildManageActionsCol(issue, modal) {
  const statuses = ["Reported", "In Progress", "Resolved", "Rejected", "Duplicate"];
  const depts = [
    "Roads & Highways", "Solid Waste Management", "Electricity & Street Lighting",
    "Water Supply & Drainage", "Animal Control & Welfare", "Town Planning & Enforcement",
    "Environmental Safety",
  ];
  const priorities = ["Critical", "High", "Medium", "Low"];

  const form = h(
    "form",
    { id: "manage-form" },
    _buildSelectGroup("m-status", "Target Status", statuses.map((s) => ({ val: s, label: s, sel: s === issue.status }))),
    h("div", { className: "form-group" },
      h("label", { for: "m-note" }, "Public Officer Note"),
      h("textarea", { id: "m-note", className: "form-control", rows: 2, placeholder: "Explain status shift or inspection findings..." })
    ),
    _buildSelectGroup("m-dept-override", "Department Override", [
      { val: issue.department, label: `Current: ${issue.department}`, sel: true },
      ...depts.filter((d) => d !== issue.department).map((d) => ({ val: d, label: d, sel: false })),
    ]),
    _buildSelectGroup("m-prio-override", "Priority Override", [
      { val: issue.priority_level, label: `Current: ${issue.priority_level}`, sel: true },
      ...priorities.filter((p) => p !== issue.priority_level).map((p) => ({ val: p, label: p, sel: false })),
    ]),
    h("div", { id: "m-alert", className: "alert hidden", role: "alert" }),
    _buildManageFormActions(issue, modal)
  );

  _bindManageFormSubmit(form, issue, modal);
  return h("div", { className: "manage-actions" }, form);
}

function _buildSelectGroup(id, label, options) {
  return h(
    "div",
    { className: "form-group" },
    h("label", { for: id }, label),
    h(
      "select",
      { id, className: "form-control" },
      ...options.map((o) => {
        const props = { value: o.val };
        if (o.sel) props.selected = true;
        return h("option", props, o.label);
      })
    )
  );
}

function _buildManageFormActions(issue, modal) {
  const reanalyzeBtn = h(
    "button",
    {
      type: "button",
      id: "btn-reanalyze",
      className: "btn btn-outline btn-block",
      onclick: async () => {
        reanalyzeBtn.disabled = true;
        reanalyzeBtn.textContent = "Re-analyzing with Gemini...";
        try {
          await api.reanalyzeIssue(issue.ticket_id);
          modal.close();
          await _loadAdminData();
        } catch (err) {
          const alertBox = document.getElementById("m-alert");
          if (alertBox) {
            clear(alertBox);
            alertBox.textContent = err.message || "Failed to re-analyze";
            alertBox.className = "alert alert-error";
            alertBox.classList.remove("hidden");
          }
          reanalyzeBtn.disabled = false;
          reanalyzeBtn.textContent = "⚡ Re-run AI Triage";
        }
      },
    },
    "⚡ Re-run AI Triage"
  );

  return h(
    "div",
    { className: "form-actions-stacked" },
    h("button", { type: "submit", className: "btn btn-primary btn-block" }, "Save Updates & Notify"),
    reanalyzeBtn
  );
}

function _bindManageFormSubmit(form, issue, modal) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const alertBox = form.querySelector("#m-alert");
    alertBox.classList.add("hidden");

    const statusVal = form.querySelector("#m-status").value;
    const noteVal = form.querySelector("#m-note").value.trim();
    const deptOverride = form.querySelector("#m-dept-override").value;
    const prioOverride = form.querySelector("#m-prio-override").value;

    try {
      await api.updateIssue(issue.ticket_id, {
        status: statusVal,
        note: noteVal || undefined,
        department_override: deptOverride !== issue.department ? deptOverride : undefined,
        priority_override: prioOverride !== issue.priority_level ? prioOverride : undefined,
      });
      modal.close();
      await _loadAdminData();
    } catch (err) {
      clear(alertBox);
      alertBox.textContent = err.message || "Failed to update issue";
      alertBox.className = "alert alert-error";
      alertBox.classList.remove("hidden");
    }
  });
}

async function _openSummaryModal() {
  const contentNode = h(
    "div",
    { className: "summary-modal-content" },
    h("div", { className: "loading-spinner" }, "Generating executive summary from live data...")
  );

  openModal({
    title: "Executive Operational Summary",
    contentNode,
    onClose: () => {},
  });

  try {
    const res = await api.generateSummary();
    clear(contentNode);
    const paragraphs = (res.summary || "")
      .split(/\n\n+/)
      .map((p) => h("p", { className: "summary-text" }, p.trim()));

    contentNode.appendChild(h("div", { className: "summary-body" }, ...paragraphs));
    contentNode.appendChild(
      h(
        "div",
        { className: "summary-footer" },
        h("small", { className: "text-muted" }, "Generated by Google Gemini based on live municipal operational data.")
      )
    );
  } catch (err) {
    clear(contentNode);
    contentNode.appendChild(
      h("div", { className: "alert alert-error" }, `Failed to generate summary: ${err.message}`)
    );
  }
}

function _getPriorityBadgeClass(priority) {
  if (priority === "Critical") return "badge-critical";
  if (priority === "High") return "badge-high";
  if (priority === "Medium") return "badge-medium";
  return "badge-low";
}

function _getStatusBadgeClass(status) {
  if (status === "In Progress") return "badge-progress";
  if (status === "Resolved") return "badge-resolved";
  if (status === "Rejected") return "badge-rejected";
  if (status === "Duplicate") return "badge-duplicate";
  return "badge-reported";
}
