/**
 * Protected Municipal Administrative Console View.
 * Provides issue management, AI overrides, status workflow transitions,
 * workload distribution metrics, and Gemini-generated weekly operational summaries.
 */

import { api, getAuthToken, setAuthToken } from "../api.js";
import { openModal } from "../components/modal.js";
import { t } from "../i18n.js";

export async function renderAdminView(container) {
  container.innerHTML = "";

  const section = document.createElement("section");
  section.className = "view-section admin-view";
  container.appendChild(section);

  const token = getAuthToken();
  if (!token) {
    renderLoginForm(section);
  } else {
    await renderDashboardContent(section);
  }
}

function renderLoginForm(container) {
  container.innerHTML = `
    <div class="admin-login-wrapper">
      <div class="card login-card">
        <div class="login-header">
          <div class="login-icon">🔒</div>
          <h2>${t("admin_login_title")}</h2>
          <p class="subtitle">${t("admin_login_sub")}</p>
        </div>

        <div class="demo-auth-pill">
          <span>Demo Password:</span>
          <code>civic-demo-2026</code>
        </div>

        <form id="admin-login-form">
          <div class="form-group">
            <label for="admin-pwd">${t("admin_pwd_label")}</label>
            <input type="password" id="admin-pwd" class="form-control" value="civic-demo-2026" required autofocus />
          </div>
          <div id="login-error" class="alert alert-error hidden" role="alert"></div>
          <button type="submit" id="btn-login-submit" class="btn btn-primary btn-block">
            <span class="btn-text">${t("btn_login")}</span>
            <span class="spinner hidden" aria-hidden="true"></span>
          </button>
        </form>
      </div>
    </div>
  `;

  const form = container.querySelector("#admin-login-form");
  const pwdInput = container.querySelector("#admin-pwd");
  const errorBox = container.querySelector("#login-error");
  const submitBtn = container.querySelector("#btn-login-submit");

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

async function renderDashboardContent(container) {
  container.innerHTML = `
    <div class="admin-header-bar">
      <div>
        <h1>${t("admin_heading")}</h1>
        <p class="subtitle">Operational Dispatch &amp; Departmental Workflow Console</p>
      </div>
      <div class="admin-top-actions">
        <button id="btn-summary" class="btn btn-secondary">✨ ${t("btn_generate_summary")}</button>
        <button id="btn-logout" class="btn btn-outline">${t("btn_logout")}</button>
      </div>
    </div>

    <div id="admin-analytics-area" class="admin-analytics-area">
      <div class="loading-spinner">Loading operational analytics...</div>
    </div>

    <div class="card admin-table-card">
      <div class="table-header">
        <h2>${t("admin_issues_title")}</h2>
        <small class="text-muted">Sorted deterministically by priority score, then age</small>
      </div>
      <div id="admin-table-container" class="table-responsive">
        <div class="loading-spinner">Loading grievances...</div>
      </div>
    </div>
  `;

  // Attach top bar actions
  document.getElementById("btn-logout").addEventListener("click", async () => {
    try {
      await api.logout();
    } catch {}
    setAuthToken(null);
    renderAdminView(container.parentElement);
  });

  document.getElementById("btn-summary").addEventListener("click", () => {
    openSummaryModal();
  });

  // Load analytics & table
  await loadAdminData();
}

async function loadAdminData() {
  try {
    const [analytics, issues] = await Promise.all([
      api.getAdminAnalytics(),
      api.listAdminIssues(),
    ]);

    renderAnalytics(analytics);
    renderAdminTable(issues);
  } catch (err) {
    if (err.status === 401) {
      setAuthToken(null);
      renderLoginForm(document.querySelector(".admin-view"));
      return;
    }
    const container = document.getElementById("admin-table-container");
    if (container) {
      container.innerHTML = `<div class="alert alert-error">Failed to load dispatch data: ${err.message}</div>`;
    }
  }
}

function renderAnalytics(analytics) {
  const container = document.getElementById("admin-analytics-area");
  if (!container) return;

  const workloadItems = Object.entries(analytics.department_workload || {})
    .map(
      ([dept, count]) => `
      <div class="workload-item">
        <span class="dept-name">${escapeHtml(dept)}</span>
        <span class="badge badge-progress">${count.open} open</span>
        <span class="badge badge-resolved">${count.resolved} resolved</span>
      </div>
    `
    )
    .join("");

  container.innerHTML = `
    <div class="analytics-card card">
      <h3>Departmental Workload Distribution</h3>
      <div class="workload-grid">
        ${workloadItems || "<p>No workload data.</p>"}
      </div>
    </div>

    <div class="analytics-summary-cards">
      <div class="card mini-stat-card ${analytics.overdue_count > 0 ? "stat-warn" : ""}">
        <div class="stat-label">SLA Breached / Overdue</div>
        <div class="stat-val">${analytics.overdue_count}</div>
        <div class="stat-sub">Tickets exceeding resolution target</div>
      </div>
      <div class="card mini-stat-card">
        <div class="stat-label">Admin Overrides</div>
        <div class="stat-val">${analytics.admin_override_count} (${analytics.admin_override_rate_percent}%)</div>
        <div class="stat-sub">Superintendent overrides applied</div>
      </div>
    </div>
  `;
}

function renderAdminTable(issues) {
  const container = document.getElementById("admin-table-container");
  if (!container) return;

  if (issues.length === 0) {
    container.innerHTML = `<p class="no-data">No grievances in queue.</p>`;
    return;
  }

  const table = document.createElement("table");
  table.className = "data-table admin-table";
  table.innerHTML = `
    <thead>
      <tr>
        <th>Ticket</th>
        <th>Title</th>
        <th>Category</th>
        <th>Priority</th>
        <th>Department</th>
        <th>Status</th>
        <th>Action</th>
      </tr>
    </thead>
    <tbody>
      ${issues
        .map((it) => {
          let pBadge = "badge-low";
          if (it.priority_level === "Critical") pBadge = "badge-critical";
          else if (it.priority_level === "High") pBadge = "badge-high";
          else if (it.priority_level === "Medium") pBadge = "badge-medium";

          let sBadge = "badge-reported";
          if (it.status === "In Progress") sBadge = "badge-progress";
          else if (it.status === "Resolved") sBadge = "badge-resolved";
          else if (it.status === "Rejected") sBadge = "badge-rejected";
          else if (it.status === "Duplicate") sBadge = "badge-duplicate";

          return `
            <tr>
              <td><strong>${escapeHtml(it.ticket_id)}</strong></td>
              <td>${escapeHtml(it.title)}</td>
              <td><span class="tag">${escapeHtml(it.category)}</span></td>
              <td><span class="badge ${pBadge}">${escapeHtml(it.priority_level)} (${it.priority_score})</span></td>
              <td>${escapeHtml(it.department)}</td>
              <td><span class="badge ${sBadge}">${escapeHtml(it.status)}</span></td>
              <td>
                <button type="button" class="btn btn-outline btn-sm btn-manage" data-ticket="${escapeHtml(it.ticket_id)}">
                  Manage
                </button>
              </td>
            </tr>
          `;
        })
        .join("")}
    </tbody>
  `;

  container.innerHTML = "";
  container.appendChild(table);

  table.querySelectorAll(".btn-manage").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tid = btn.getAttribute("data-ticket");
      if (tid) openManageModal(tid);
    });
  });
}

async function openManageModal(ticketId) {
  const contentNode = document.createElement("div");
  contentNode.className = "manage-modal-content";
  contentNode.innerHTML = `<div class="loading-spinner">Loading issue details...</div>`;

  const modal = openModal({
    title: `Manage Grievance [${ticketId}]`,
    contentNode,
    onClose: () => {},
  });

  try {
    const issue = await api.getIssue(ticketId);
    renderManageForm(contentNode, issue, modal);
  } catch (err) {
    contentNode.innerHTML = `<div class="alert alert-error">Failed to load issue: ${err.message}</div>`;
  }
}

function renderManageForm(container, issue, modal) {
  const ai = issue.ai_analysis;
  const photoHtml = issue.photo_data_url
    ? `<div class="modal-photo"><img src="${issue.photo_data_url}" alt="Civic Photo" class="img-responsive" /></div>`
    : "";

  container.innerHTML = `
    <div class="manage-grid">
      <div class="manage-info">
        <h3>${escapeHtml(issue.title)}</h3>
        <p class="text-muted">Reported on ${new Date(issue.created_at).toLocaleString()}</p>
        <p><strong>Description:</strong> ${escapeHtml(issue.description)}</p>
        <p><strong>Address:</strong> ${escapeHtml(issue.address || "None specified")}</p>
        ${photoHtml}

        <div class="ai-analysis-card card">
          <h4>🤖 AI Triage Assessment</h4>
          <p><strong>Reasoning:</strong> ${escapeHtml(ai?.reasoning || "Standard classification")}</p>
          <p><strong>Confidence:</strong> ${ai ? Math.round(ai.confidence * 100) : 90}%</p>
          <p><strong>Safety Hazard:</strong> ${ai?.safety_risk ? "⚠️ YES - Flagged" : "No immediate peril"}</p>
          <p><strong>Urgency Tier:</strong> ${escapeHtml(ai?.urgency || "Standard")}</p>
        </div>
      </div>

      <div class="manage-actions">
        <form id="manage-form">
          <div class="form-group">
            <label for="m-status">Target Status</label>
            <select id="m-status" class="form-control" required>
              <option value="Reported" ${issue.status === "Reported" ? "selected" : ""}>Reported</option>
              <option value="In Progress" ${issue.status === "In Progress" ? "selected" : ""}>In Progress</option>
              <option value="Resolved" ${issue.status === "Resolved" ? "selected" : ""}>Resolved</option>
              <option value="Rejected" ${issue.status === "Rejected" ? "selected" : ""}>Rejected</option>
              <option value="Duplicate" ${issue.status === "Duplicate" ? "selected" : ""}>Duplicate</option>
            </select>
          </div>

          <div class="form-group">
            <label for="m-note">Public Officer Note</label>
            <textarea id="m-note" class="form-control" rows="2" placeholder="Explain status shift or inspection findings..."></textarea>
          </div>

          <div class="form-group">
            <label for="m-dept-override">Department Override</label>
            <select id="m-dept-override" class="form-control">
              <option value="${escapeHtml(issue.department)}">Current: ${escapeHtml(issue.department)}</option>
              <option value="Roads & Highways">Roads &amp; Highways</option>
              <option value="Solid Waste Management">Solid Waste Management</option>
              <option value="Electricity & Street Lighting">Electricity &amp; Street Lighting</option>
              <option value="Water Supply & Drainage">Water Supply &amp; Drainage</option>
              <option value="Animal Control & Welfare">Animal Control &amp; Welfare</option>
              <option value="Town Planning & Enforcement">Town Planning &amp; Enforcement</option>
              <option value="Environmental Safety">Environmental Safety</option>
            </select>
          </div>

          <div class="form-group">
            <label for="m-prio-override">Priority Override</label>
            <select id="m-prio-override" class="form-control">
              <option value="${escapeHtml(issue.priority_level)}">Current: ${escapeHtml(issue.priority_level)}</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>

          <div id="m-alert" class="alert hidden" role="alert"></div>

          <div class="form-actions-stacked">
            <button type="submit" class="btn btn-primary btn-block">Save Updates &amp; Notify</button>
            <button type="button" id="btn-reanalyze" class="btn btn-outline btn-block">⚡ Re-run AI Triage</button>
          </div>
        </form>
      </div>
    </div>
  `;

  const form = document.getElementById("manage-form");
  const alertBox = document.getElementById("m-alert");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    alertBox.classList.add("hidden");

    const statusVal = document.getElementById("m-status").value;
    const noteVal = document.getElementById("m-note").value.trim();
    const deptOverride = document.getElementById("m-dept-override").value;
    const prioOverride = document.getElementById("m-prio-override").value;

    try {
      await api.updateIssue(issue.ticket_id, {
        status: statusVal,
        note: noteVal || undefined,
        department_override: deptOverride !== issue.department ? deptOverride : undefined,
        priority_override: prioOverride !== issue.priority_level ? prioOverride : undefined,
      });
      modal.close();
      await loadAdminData();
    } catch (err) {
      alertBox.textContent = err.message || "Failed to update issue";
      alertBox.className = "alert alert-error";
      alertBox.classList.remove("hidden");
    }
  });

  const reanalyzeBtn = document.getElementById("btn-reanalyze");
  if (reanalyzeBtn) {
    reanalyzeBtn.addEventListener("click", async () => {
      reanalyzeBtn.disabled = true;
      reanalyzeBtn.textContent = "Re-analyzing with Gemini...";
      try {
        await api.reanalyzeIssue(issue.ticket_id);
        modal.close();
        await loadAdminData();
      } catch (err) {
        alertBox.textContent = err.message || "Failed to re-analyze";
        alertBox.className = "alert alert-error";
        alertBox.classList.remove("hidden");
        reanalyzeBtn.disabled = false;
        reanalyzeBtn.textContent = "⚡ Re-run AI Triage";
      }
    });
  }
}

async function openSummaryModal() {
  const contentNode = document.createElement("div");
  contentNode.className = "summary-modal-content";
  contentNode.innerHTML = `<div class="loading-spinner">Generating executive summary from live data...</div>`;

  openModal({
    title: "Executive Operational Summary",
    contentNode,
    onClose: () => {},
  });

  try {
    const res = await api.generateSummary();
    contentNode.innerHTML = `
      <div class="summary-body">
        <p class="summary-text">${escapeHtml(res.summary).replace(/\n\n/g, "</p><p class='summary-text'>")}</p>
      </div>
      <div class="summary-footer">
        <small class="text-muted">Generated by Google Gemini based on live municipal operational data.</small>
      </div>
    `;
  } catch (err) {
    contentNode.innerHTML = `<div class="alert alert-error">Failed to generate summary: ${err.message}</div>`;
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
