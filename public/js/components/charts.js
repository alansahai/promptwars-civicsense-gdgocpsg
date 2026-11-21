/**
 * Zero-dependency accessible Inline SVG Data Visualizations:
 * 1. Category Breakdown Horizontal Bar Chart
 * 2. 14-Day Grievance Trend Area/Line Chart
 * 3. Locality Incident Scatter Map
 */

export function renderCategoryBarChart(container, categoryData) {
  container.innerHTML = "";
  if (!categoryData || Object.keys(categoryData).length === 0) {
    container.textContent = "No data available";
    return;
  }

  const entries = Object.entries(categoryData).sort((a, b) => b[1] - a[1]);
  const maxVal = Math.max(...entries.map((e) => e[1]), 1);

  const wrapper = document.createElement("div");
  wrapper.className = "chart-wrapper";

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 500 ${entries.length * 36 + 20}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Horizontal bar chart showing grievances by category");

  entries.forEach(([cat, count], idx) => {
    const y = idx * 36 + 10;
    const barWidth = Math.max(4, Math.round((count / maxVal) * 300));

    // Category Label
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", "10");
    text.setAttribute("y", `${y + 16}`);
    text.setAttribute("class", "chart-label");
    text.textContent = cat.length > 20 ? cat.slice(0, 18) + "…" : cat;
    svg.appendChild(text);

    // Bar background track
    const bgBar = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    bgBar.setAttribute("x", "160");
    bgBar.setAttribute("y", `${y + 4}`);
    bgBar.setAttribute("width", "300");
    bgBar.setAttribute("height", "18");
    bgBar.setAttribute("rx", "4");
    bgBar.setAttribute("class", "chart-bar-bg");
    svg.appendChild(bgBar);

    // Value bar
    const bar = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    bar.setAttribute("x", "160");
    bar.setAttribute("y", `${y + 4}`);
    bar.setAttribute("width", `${barWidth}`);
    bar.setAttribute("height", "18");
    bar.setAttribute("rx", "4");
    bar.setAttribute("class", "chart-bar-fill");
    svg.appendChild(bar);

    // Value text
    const valText = document.createElementNS("http://www.w3.org/2000/svg", "text");
    valText.setAttribute("x", `${168 + barWidth}`);
    valText.setAttribute("y", `${y + 17}`);
    valText.setAttribute("class", "chart-value");
    valText.textContent = `${count}`;
    svg.appendChild(valText);
  });

  wrapper.appendChild(svg);
  container.appendChild(wrapper);
}

export function renderTrendLineChart(container, trendData) {
  container.innerHTML = "";
  if (!trendData || trendData.length === 0) {
    container.textContent = "No trend data available";
    return;
  }

  const width = 500;
  const height = 180;
  const padLeft = 40;
  const padRight = 20;
  const padTop = 20;
  const padBottom = 30;

  const maxVal = Math.max(...trendData.map((d) => d.count), 4);
  const plotWidth = width - padLeft - padRight;
  const plotHeight = height - padTop - padBottom;

  const points = trendData.map((d, idx) => {
    const x = padLeft + (idx / (trendData.length - 1)) * plotWidth;
    const y = padTop + plotHeight - (d.count / maxVal) * plotHeight;
    return { x, y, date: d.date, count: d.count };
  });

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Line chart showing 14-day grievance trends");

  // Grid lines
  for (let i = 0; i <= 4; i++) {
    const gy = padTop + (plotHeight / 4) * i;
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", `${padLeft}`);
    line.setAttribute("y1", `${gy}`);
    line.setAttribute("x2", `${width - padRight}`);
    line.setAttribute("y2", `${gy}`);
    line.setAttribute("class", "chart-grid-line");
    svg.appendChild(line);

    const valLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    valLabel.setAttribute("x", "30");
    valLabel.setAttribute("y", `${gy + 4}`);
    valLabel.setAttribute("class", "chart-axis-text");
    valLabel.textContent = `${Math.round(maxVal - (maxVal / 4) * i)}`;
    svg.appendChild(valLabel);
  }

  // Area fill path
  const areaPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
  const areaD = `M ${points[0].x} ${padTop + plotHeight} ` +
    points.map((p) => `L ${p.x} ${p.y}`).join(" ") +
    ` L ${points[points.length - 1].x} ${padTop + plotHeight} Z`;
  areaPath.setAttribute("d", areaD);
  areaPath.setAttribute("class", "chart-area-fill");
  svg.appendChild(areaPath);

  // Line path
  const linePath = document.createElementNS("http://www.w3.org/2000/svg", "path");
  const lineD = points.map((p, idx) => `${idx === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  linePath.setAttribute("d", lineD);
  linePath.setAttribute("class", "chart-line-stroke");
  svg.appendChild(linePath);

  // Data point dots
  points.forEach((p) => {
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", `${p.x}`);
    circle.setAttribute("cy", `${p.y}`);
    circle.setAttribute("r", "4");
    circle.setAttribute("class", "chart-dot");
    const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
    title.textContent = `${p.date}: ${p.count} issues`;
    circle.appendChild(title);
    svg.appendChild(circle);
  });

  container.appendChild(svg);
}

export function renderScatterMap(container, mapPoints, onPointClick) {
  container.innerHTML = "";
  if (!mapPoints || mapPoints.length === 0) {
    container.textContent = "No geo-tagged grievances recorded.";
    return;
  }

  const width = 500;
  const height = 300;
  const pad = 30;

  const lats = mapPoints.map((p) => p.lat);
  const lons = mapPoints.map((p) => p.lon);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);

  const latSpan = maxLat - minLat || 0.05;
  const lonSpan = maxLon - minLon || 0.05;

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Locality incident scatter map");

  // Grid background
  const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  rect.setAttribute("width", `${width}`);
  rect.setAttribute("height", `${height}`);
  rect.setAttribute("class", "map-bg");
  rect.setAttribute("rx", "8");
  svg.appendChild(rect);

  // Map coordinates grid rings
  for (let r = 50; r <= 220; r += 50) {
    const ring = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    ring.setAttribute("cx", `${width / 2}`);
    ring.setAttribute("cy", `${height / 2}`);
    ring.setAttribute("r", `${r}`);
    ring.setAttribute("class", "map-grid-ring");
    svg.appendChild(ring);
  }

  // Points
  mapPoints.forEach((p) => {
    // Invert lat for SVG y coordinate
    const x = pad + ((p.lon - minLon) / lonSpan) * (width - 2 * pad);
    const y = pad + ((maxLat - p.lat) / latSpan) * (height - 2 * pad);

    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.setAttribute("class", "map-point-group");
    group.style.cursor = "pointer";

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", `${x}`);
    circle.setAttribute("cy", `${y}`);
    circle.setAttribute("r", p.priority === "Critical" ? "8" : p.priority === "High" ? "6" : "5");

    let colorClass = "priority-low-fill";
    if (p.priority === "Critical") colorClass = "priority-critical-fill";
    else if (p.priority === "High") colorClass = "priority-high-fill";
    else if (p.priority === "Medium") colorClass = "priority-medium-fill";
    circle.setAttribute("class", `map-point ${colorClass}`);

    const titleEl = document.createElementNS("http://www.w3.org/2000/svg", "title");
    titleEl.textContent = `[${p.ticket_id}] ${p.priority} - ${p.category}: ${p.title}`;
    group.appendChild(titleEl);
    group.appendChild(circle);

    group.addEventListener("click", () => {
      if (onPointClick) onPointClick(p.ticket_id);
    });

    svg.appendChild(group);
  });

  container.appendChild(svg);
}
