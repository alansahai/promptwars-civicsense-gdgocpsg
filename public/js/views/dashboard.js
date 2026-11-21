/**
 * Public Transparency Dashboard View.
 *
 * Renders municipal summary metrics, inline SVG charts, geographic scatter map,
 * and filterable grievance tables using safe DOM elements with zero innerHTML.
 */

import { api } from "../api.js";
import {
  renderCategoryBarChart,
  renderScatterMap,
  renderTrendLineChart,
} from "../components/charts.js";
import { clear, h } from "../dom.js";
import { t } from "../i18n.js";
import { router } from "../router.js";

/**
 * Render the public transparency dashboard view.
 * @param {HTMLElement} container - Host container element.
 */
export async function renderDashboardView(container) {
  clear(container);

  const section = h(
    "section",
    { className: "view-section dashboard-view" },
    h(
      "div",
      { className: "section-header" },
      h("h1", {}, t("dash_heading")),
      h("p", { className: "subtitle" }, t("dash_sub"))
    ),
    h(
      "div",
      { className: "stats-grid", id: "stats-grid" },
      h("div", { className: "loading-spinner" }, "Loading municipal metrics...")
    ),
    _buildChartsGrid(),
    _buildTableSection()
  );

  container.appendChild(section);

  _setupFilterListeners();
  await _loadDashboardMetrics();
}

function _buildChartsGrid() {
  return h(
    "div",
    { className: "charts-grid" },
    h(
      "div",
      { className: "card chart-card" },
      h("h3", {}, t("chart_category_title")),
      h("div", { id: "chart-cat", className: "chart-container" })
    ),
    h(
      "div",
      { className: "card chart-card" },
      h("h3", {}, t("chart_trend_title")),
      h("div", { id: "chart-trend", className: "chart-container" })
    ),
    h(
      "div",
      { className: "card chart-card map-card" },
      h("h3", {}, t("chart_map_title")),
      h("div", { id: "chart-map", className: "chart-container" })
    )
  );
}

function _buildTableSection() {
  return h(
    "div",
    { className: "card table-card" },
    h(
      "div",
      { className: "table-header" },
      h("h2", {}, "Public Grievance Registry"),
      _buildFiltersRow()
    ),
    h("div", { id: "issues-table-container", className: "table-responsive" })
  );
}

function _buildFilterSelects() {
  const statuses = ["", "Reported", "In Progress", "Resolved", "Duplicate"];
  const categories = ["", "Pothole", "Overflowing Garbage", "Damaged Streetlight", "Water Leakage", "Exposed Live Wire", "Sewage Overflow"];
  const priorities = ["", "Critical", "High", "Medium", "Low"];

  const buildSelect = (id, options, defaultLabel) =>
    h("select", { id, className: "form-control form-control-sm" },
      ...options.map((opt) => h("option", { value: opt }, opt || defaultLabel))
    );

  return [
    buildSelect("filter-status", statuses, "All Statuses"),
    buildSelect("filter-category", categories, "All Categories"),
    buildSelect("filter-priority", priorities, "All Priorities"),
  ];
}

function _buildFiltersRow() {
  return h(
    "div",
    { className: "filters-row" },
    ..._buildFilterSelects(),
    h("input", {
      type: "text",
      id: "filter-search",
      className: "form-control form-control-sm",
      placeholder: t("filter_search"),
    })
  );
}

async function _loadDashboardMetrics() {
  const statsGrid = document.getElementById("stats-grid");
  try {
    const stats = await api.getStats();
    if (statsGrid) _populateStatCards(statsGrid, stats);
    _renderCharts(stats);
    await _refreshIssuesList();
  } catch (err) {
    if (statsGrid) {
      clear(statsGrid);
      statsGrid.appendChild(
        h("div", { className: "alert alert-error" }, `Failed to load statistics: ${err.message}`)
      );
    }
  }
}

function _populateStatCards(grid, stats) {
  clear(grid);
  const cards = [
    { label: t("stat_total"), val: stats.total_issues, sub: `Across all wards in ${stats.city_name}`, cls: "" },
    { label: t("stat_open"), val: stats.open_issues, sub: "Under active field review", cls: "stat-open" },
    { label: t("stat_resolved"), val: stats.resolved_issues, sub: "Work completed & verified", cls: "stat-resolved" },
    { label: t("stat_avg_sla"), val: `${stats.average_resolution_hours}h`, sub: "Average municipal turnaround", cls: "" },
    { label: t("stat_rate"), val: `${stats.resolution_rate_percent}%`, sub: "Grievance resolution efficiency", cls: "" },
  ];

  cards.forEach(({ label, val, sub, cls }) => {
    grid.appendChild(
      h(
        "div",
        { className: `stat-card ${cls}`.trim() },
        h("div", { className: "stat-label" }, label),
        h("div", { className: "stat-val" }, String(val)),
        h("div", { className: "stat-sub" }, sub)
      )
    );
  });
}

function _renderCharts(stats) {
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
}

async function _refreshIssuesList() {
  const tableContainer = document.getElementById("issues-table-container");
  if (!tableContainer) return;

  const filters = {
    status: document.getElementById("filter-status")?.value || "",
    category: document.getElementById("filter-category")?.value || "",
    priority: document.getElementById("filter-priority")?.value || "",
    search: document.getElementById("filter-search")?.value || "",
    limit: 30,
  };

  clear(tableContainer);
  tableContainer.appendChild(h("div", { className: "loading-spinner" }, "Filtering issues..."));

  try {
    const res = await api.listIssues(filters);
    clear(tableContainer);
    _renderTableContent(tableContainer, res.items || []);
  } catch (err) {
    clear(tableContainer);
    tableContainer.appendChild(
      h("div", { className: "alert alert-error" }, `Failed to fetch issues: ${err.message}`)
    );
  }
}

function _renderTableContent(container, items) {
  if (items.length === 0) {
    container.appendChild(
      h("p", { className: "no-data" }, "No grievances match the selected filter criteria.")
    );
    return;
  }

  const table = h(
    "table",
    { className: "data-table" },
    _buildTableHeader(),
    h("tbody", {}, ...items.map(_buildTableRow))
  );

  container.appendChild(table);
}

function _buildTableHeader() {
  return h(
    "thead",
    {},
    h(
      "tr",
      {},
      h("th", {}, "Ticket"),
      h("th", {}, "Issue Headline"),
      h("th", {}, "Category"),
      h("th", {}, "Priority"),
      h("th", {}, "Department"),
      h("th", {}, "Status"),
      h("th", {}, "Reported")
    )
  );
}

function _buildTableRow(it) {
  const row = h(
    "tr",
    {
      className: "clickable-row",
      onclick: (e) => {
        if (e.target.tagName !== "A") {
          router.navigate(`/track?id=${encodeURIComponent(it.ticket_id)}`);
        }
      },
    },
    h("td", {}, h("a", { href: `#/track?id=${encodeURIComponent(it.ticket_id)}`, className: "ticket-link" }, h("strong", {}, it.ticket_id))),
    h("td", {}, it.title),
    h("td", {}, h("span", { className: "tag" }, it.category)),
    h("td", {}, h("span", { className: `badge ${_getPriorityBadgeClass(it.priority_level)}` }, it.priority_level)),
    h("td", {}, it.department),
    h("td", {}, h("span", { className: `badge ${_getStatusBadgeClass(it.status)}` }, it.status)),
    h("td", { className: "text-muted small" }, _formatDate(it.created_at))
  );
  return row;
}

function _setupFilterListeners() {
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

  if (statusEl) statusEl.addEventListener("change", _refreshIssuesList);
  if (catEl) catEl.addEventListener("change", _refreshIssuesList);
  if (prioEl) prioEl.addEventListener("change", _refreshIssuesList);
  if (searchEl) searchEl.addEventListener("input", debounce(_refreshIssuesList, 300));
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

function _formatDate(isoStr) {
  if (!isoStr) return "";
  try {
    const d = new Date(isoStr);
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return isoStr;
  }
}
