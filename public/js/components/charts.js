/**
 * Zero-dependency accessible Inline SVG Data Visualizations:
 * 1. Category Breakdown Horizontal Bar Chart
 * 2. 14-Day Grievance Trend Area/Line Chart
 * 3. Locality Incident Scatter Map
 */

"use strict";

import { clear, h, svg } from "../dom.js";

/**
 * Render category bar row entry into SVG.
 * @param {string} cat - Category name.
 * @param {number} count - Incident count.
 * @param {number} maxVal - Maximum incident count.
 * @param {number} idx - Row index.
 * @returns {Array<SVGElement>} SVG elements for bar row.
 */
function renderBarRow(cat, count, maxVal, idx) {
  const y = idx * 36 + 10;
  const barWidth = Math.max(4, Math.round((count / maxVal) * 300));
  const label = cat.length > 20 ? `${cat.slice(0, 18)}…` : cat;

  return [
    svg("text", { x: 10, y: y + 16, class: "chart-label" }, label),
    svg("rect", { x: 160, y: y + 4, width: 300, height: 18, rx: 4, class: "chart-bar-bg" }),
    svg("rect", { x: 160, y: y + 4, width: barWidth, height: 18, rx: 4, class: "chart-bar-fill" }),
    svg("text", { x: 168 + barWidth, y: y + 17, class: "chart-value" }, count),
  ];
}

/**
 * Render horizontal category breakdown bar chart.
 * @param {HTMLElement} container - Target container.
 * @param {Object} categoryData - Category count mapping.
 */
export function renderCategoryBarChart(container, categoryData) {
  clear(container);
  if (!categoryData || Object.keys(categoryData).length === 0) {
    container.appendChild(h("p", { class: "no-data" }, "No data available"));
    return;
  }

  const entries = Object.entries(categoryData).sort((a, b) => b[1] - a[1]);
  const maxVal = Math.max(...entries.map((e) => e[1]), 1);
  const rows = entries.flatMap(([cat, count], idx) => renderBarRow(cat, count, maxVal, idx));

  const chartSvg = svg(
    "svg",
    {
      viewBox: `0 0 500 ${entries.length * 36 + 20}`,
      role: "img",
      "aria-label": "Horizontal bar chart showing grievances by category",
    },
    ...rows
  );

  container.appendChild(h("div", { class: "chart-wrapper" }, chartSvg));
}

/**
 * Build grid lines and labels for trend chart.
 * @param {number} plotHeight - Graph height.
 * @param {number} maxVal - Max value.
 * @returns {Array<SVGElement>} Grid line elements.
 */
function buildTrendGrid(plotHeight, maxVal) {
  const gridElements = [];
  for (let i = 0; i <= 4; i++) {
    const gy = 20 + (plotHeight / 4) * i;
    gridElements.push(
      svg("line", { x1: 40, y1: gy, x2: 480, y2: gy, class: "chart-grid-line" }),
      svg("text", { x: 30, y: gy + 4, class: "chart-axis-text" }, Math.round(maxVal - (maxVal / 4) * i))
    );
  }
  return gridElements;
}

/**
 * Render 14-day grievance volume trend area/line chart.
 * @param {HTMLElement} container - Target container.
 * @param {Array} trendData - 14-day data point array.
 */
export function renderTrendLineChart(container, trendData) {
  clear(container);
  if (!trendData || trendData.length === 0) {
    container.appendChild(h("p", { class: "no-data" }, "No trend data available"));
    return;
  }

  const maxVal = Math.max(...trendData.map((d) => d.count), 4);
  const plotWidth = 440;
  const plotHeight = 130;

  const points = trendData.map((d, idx) => ({
    x: 40 + (idx / (trendData.length - 1)) * plotWidth,
    y: 20 + plotHeight - (d.count / maxVal) * plotHeight,
    date: d.date,
    count: d.count,
  }));

  const areaD = `M ${points[0].x} ${150} ` +
    points.map((p) => `L ${p.x} ${p.y}`).join(" ") +
    ` L ${points[points.length - 1].x} ${150} Z`;
  const lineD = points.map((p, idx) => `${idx === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  const grid = buildTrendGrid(plotHeight, maxVal);
  const dots = points.map((p) =>
    svg("circle", { cx: p.x, cy: p.y, r: 4, class: "chart-dot" }, svg("title", {}, `${p.date}: ${p.count} issues`))
  );

  const chartSvg = svg(
    "svg",
    {
      viewBox: "0 0 500 180",
      role: "img",
      "aria-label": "Line chart showing 14-day grievance trends",
    },
    ...grid,
    svg("path", { d: areaD, class: "chart-area-fill" }),
    svg("path", { d: lineD, class: "chart-line-stroke" }),
    ...dots
  );

  container.appendChild(chartSvg);
}

/**
 * Build a single geo point group on the scatter map.
 * @param {Object} p - Point coordinate and priority payload.
 * @param {Object} bounds - Spatial coordinate bounding box.
 * @param {Function} [onPointClick] - Optional click handler.
 * @returns {SVGElement} SVG group element.
 */
function buildScatterPoint(p, bounds, onPointClick) {
  const x = 30 + ((p.lon - bounds.minLon) / bounds.lonSpan) * 440;
  const y = 30 + ((bounds.maxLat - p.lat) / bounds.latSpan) * 240;
  const r = p.priority === "Critical" ? 8 : p.priority === "High" ? 6 : 5;

  let colorClass = "priority-low-fill";
  if (p.priority === "Critical") colorClass = "priority-critical-fill";
  else if (p.priority === "High") colorClass = "priority-high-fill";
  else if (p.priority === "Medium") colorClass = "priority-medium-fill";

  const group = svg(
    "g",
    {
      class: "map-point-group cursor-pointer",
      onClick: () => onPointClick && onPointClick(p.ticket_id),
    },
    svg("title", {}, `[${p.ticket_id}] ${p.priority} - ${p.category}: ${p.title}`),
    svg("circle", { cx: x, cy: y, r, class: `map-point ${colorClass}` })
  );
  return group;
}

/**
 * Render geographical scatter map of geo-tagged civic grievances.
 * @param {HTMLElement} container - Target container.
 * @param {Array} mapPoints - Array of mapped coordinates.
 * @param {Function} [onPointClick] - Coordinate click callback.
 */
export function renderScatterMap(container, mapPoints, onPointClick) {
  clear(container);
  if (!mapPoints || mapPoints.length === 0) {
    container.appendChild(h("p", { class: "no-data" }, "No geo-tagged grievances recorded."));
    return;
  }

  const lats = mapPoints.map((p) => p.lat);
  const lons = mapPoints.map((p) => p.lon);
  const bounds = {
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats),
    minLon: Math.min(...lons),
    maxLon: Math.max(...lons),
    latSpan: Math.max(...lats) - Math.min(...lats) || 0.05,
    lonSpan: Math.max(...lons) - Math.min(...lons) || 0.05,
  };

  const rings = [50, 100, 150, 200].map((r) =>
    svg("circle", { cx: 250, cy: 150, r, class: "map-grid-ring" })
  );
  const points = mapPoints.map((p) => buildScatterPoint(p, bounds, onPointClick));

  const mapSvg = svg(
    "svg",
    {
      viewBox: "0 0 500 300",
      role: "img",
      "aria-label": "Locality incident scatter map",
    },
    svg("rect", { width: 500, height: 300, rx: 8, class: "map-bg" }),
    ...rings,
    ...points
  );

  container.appendChild(mapSvg);
}
