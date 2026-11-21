/**
 * Public Transparency Dashboard View.
 * Renders summary metrics, inline SVG charts, locality scatter map,
 * and filterable grievance tables.
 */

import { api } from "../api.js";
import {
  renderCategoryBarChart,
  renderScatterMap,
  renderTrendLineChart,
} from "../components/charts.js";
import { t } from "../i18n.js";
import { router } from "../router.js";

export async function renderDashboardView(container) {
  container.innerHTML = "";

  const section = document.createElement("section");
  section.className = "view-section dashboard-view";

  const header = document.createElement("div");
  header.className = "section-header";
  header.innerHTML = `
    <h1>${t("dash_heading")}</h1>
    <p class="subtitle">${t("dash_sub")}</p>
  `;
  section.appendChild(header);

  // Summary Stat Cards Container
  const statsContainer = document.createElement("div");
  statsContainer.className = "stats-grid";
  statsContainer.id = "stats-grid";
  statsContainer.innerHTML = `<div class="loading-spinner">Loading municipal metrics...</div>`;
  section.appendChild(statsContainer);

  // SVG Visualizations Grid
  const chartsGrid = document.createElement("div");
  chartsGrid.className = "charts-grid";

  // Chart 1: Category breakdown
  const catCard = document.createElement("div");
  catCard.className = "card chart-card";
  catCard.innerHTML = `<h3>${t("chart_category_title")}</h3><div id="chart-cat" class="chart-container"></div>`;
  chartsGrid.appendChild(catCard);

  // Chart 2: 14-day trend
  const trendCard = document.createElement("div");
  trendCard.className = "card chart-card";
  trendCard.innerHTML = `<h3>${t("chart_trend_title")}</h3><div id="chart-trend" class="chart-container"></div>`;
  chartsGrid.appendChild(trendCard);

  // Chart 3: Locality scatter map
  const mapCard = document.createElement("div");
  mapCard.className = "card chart-card map-card";
  mapCard.innerHTML = `<h3>${t("chart_map_title")}</h3><div id="chart-map" class="chart-container"></div>`;
  chartsGrid.appendChild(mapCard);

  section.appendChild(chartsGrid);

  // Public Filter & Issues Table
  const tableSection = document.createElement("div");
  tableSection.className = "card table-card";
  tableSection.innerHTML = `
    <div class="table-header">
      <h2>Public Grievance Registry</h2>
      <div class="filters-row">
        <select id="filter-status" class="form-control form-control-sm">
          <option value="">All Statuses</option>
          <option value="Reported">Reported</option>
          <option value="In Progress">In Progress</option>
          <option value="Resolved">Resolved</option>
          <option value="Duplicate">Duplicate</option>
        </select>
        <select id="filter-category" class="form-control form-control-sm">
          <option value="">All Categories</option>
          <option value="Pothole">Pothole</option>
          <option value="Overflowing Garbage">Garbage</option>
          <option value="Damaged Streetlight">Streetlight</option>
          <option value="Water Leakage">Water Leakage</option>
          <option value="Exposed Live Wire">Exposed Live Wire</option>
          <option value="Sewage Overflow">Sewage Overflow</option>
        </select>
        <select id="filter-priority" class="form-control form-control-sm">
          <option value="">All Priorities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        <input type="text" id="filter-search" class="form-control form-control-sm" placeholder="${t("filter_search")}" />
      </div>
    </div>
    <div id="issues-table-container" class="table-responsive"></div>
  `;
  section.appendChild(tableSection);

  container.appendChild(section);

  // Load and populate data
  await loadDashboardData();
  setupFilters();
}

async function loadDashboardData() {
  try {
    const stats = await api.getStats();

    // 1. Populate Stat Cards
    const statsGrid = document.getElementById("stats-grid");
    if (statsGrid) {
      statsGrid.innerHTML = `
        <div class="stat-card">
          <div class="stat-label">${t("stat_total")}</div>
          <div class="stat-val">${stats.total_issues}</div>
          <div class="stat-sub">Across all wards in ${stats.city_name}</div>
        </div>
        <div class="stat-card stat-open">
          <div class="stat-label">${t("stat_open")}</div>
          <div class="stat-val">${stats.open_issues}</div>
          <div class="stat-sub">Under active field review</div>
        </div>
        <div class="stat-card stat-resolved">
          <div class="stat-label">${t("stat_resolved")}</div>
          <div class="stat-val">${stats.resolved_issues}</div>
          <div class="stat-sub">Work completed & verified</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">${t("stat_avg_sla")}</div>
          <div class="stat-val">${stats.average_resolution_hours}h</div>
          <div class="stat-sub">Average municipal turnaround</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">${t("stat_rate")}</div>
          <div class="stat-val">${stats.resolution_rate_percent}%</div>
          <div class="stat-sub">Grievance resolution efficiency</div>
        </div>
      `;
    }

    // 2. Render Inline Charts
    const catEl = document.getElementById("chart-cat");
    if (catEl) renderCategoryBarChart(catEl, stats.category_breakdown);

    const trendEl = document.getElementById("chart-trend");
    if (trendEl) renderTrendLineChart(trendEl, stats.trend_14_days);

    const mapEl = document.getElementById("chart-map");
    if (mapEl) {
      renderScatterMap(mapEl, stats.map_points, (ticketId) => {
        router.navigate(`/track?id=${encodeURIComponent(ticketId)}`);
      });
    }

    // 3. Load initial issues list
    await refreshIssuesList();
  } catch (err) {
    const statsGrid = document.getElementById("stats-grid");
    if (statsGrid) {
      statsGrid.innerHTML = `<div class="alert alert-error">Failed to load statistics: ${err.message}</div>`;
    }
  }
}

async function refreshIssuesList() {
  const tableContainer = document.getElementById("issues-table-container");
  if (!tableContainer) return;

  const status = document.getElementById("filter-status")?.value || "";
  const category = document.getElementById("filter-category")?.value || "";
  const priority = document.getElementById("filter-priority")?.value || "";
  const search = document.getElementById("filter-search")?.value || "";

  tableContainer.innerHTML = `<div class="loading-spinner">Filtering issues...</div>`;

  try {
    const res = await api.listIssues({ status, category, priority, search, limit: 30 });
    const items = res.items || [];

    if (items.length === 0) {
      tableContainer.innerHTML = `<p class="no-data">No grievances match the selected filter criteria.</p>`;
      return;
    }

    const table = document.createElement("table");
    table.className = "data-table";
    table.innerHTML = `
      <thead>
        <tr>
          <th>Ticket</th>
          <th>Issue Headline</th>
          <th>Category</th>
          <th>Priority</th>
          <th>Department</th>
          <th>Status</th>
          <th>Reported</th>
        </tr>
      </thead>
      <tbody>
        ${items
          .map(
            (it) => `
          <tr data-ticket="${escapeHtml(it.ticket_id)}" class="clickable-row">
            <td><a href="#/track?id=${encodeURIComponent(it.ticket_id)}" class="ticket-link"><strong>${escapeHtml(it.ticket_id)}</strong></a></td>
            <td>${escapeHtml(it.title)}</td>
            <td><span class="tag">${escapeHtml(it.category)}</span></td>
            <td><span class="badge ${getPriorityBadge(it.priority_level)}">${escapeHtml(it.priority_level)}</span></td>
            <td>${escapeHtml(it.department)}</td>
            <td><span class="badge ${getStatusBadge(it.status)}">${escapeHtml(it.status)}</span></td>
            <td class="text-muted small">${formatDate(it.created_at)}</td>
          </tr>
        `
          )
          .join("")}
      </tbody>
    `;

    tableContainer.innerHTML = "";
    tableContainer.appendChild(table);

    // Clickable rows
    table.querySelectorAll("tbody tr").forEach((row) => {
      row.addEventListener("click", (e) => {
        if (e.target.tagName !== "A") {
          const tid = row.getAttribute("data-ticket");
          if (tid) router.navigate(`/track?id=${encodeURIComponent(tid)}`);
        }
      });
    });
  } catch (err) {
    tableContainer.innerHTML = `<div class="alert alert-error">Failed to fetch issues: ${err.message}</div>`;
  }
}

function setupFilters() {
  const debounce = (fn, ms) => {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  };

  const statusEl = document.getElementById("filter-status");
  const catEl = document.getElementById("filter-category");
  const prioEl = document.getElementById("filter-priority");
  const searchEl = document.getElementById("filter-search");

  if (statusEl) statusEl.addEventListener("change", refreshIssuesList);
  if (catEl) catEl.addEventListener("change", refreshIssuesList);
  if (prioEl) prioEl.addEventListener("change", refreshIssuesList);
  if (searchEl) searchEl.addEventListener("input", debounce(refreshIssuesList, 300));
}

function getPriorityBadge(priority) {
  if (priority === "Critical") return "badge-critical";
  if (priority === "High") return "badge-high";
  if (priority === "Medium") return "badge-medium";
  return "badge-low";
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
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
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
