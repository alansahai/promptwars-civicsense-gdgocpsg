/**
 * System announcement and demo-mode status banner component.
 */

"use strict";

import { clear, h } from "../dom.js";

/**
 * Render system health and capability status banner into container.
 * @param {HTMLElement} container - Parent container element.
 * @param {Object} healthInfo - Health status payload from /api/health.
 */
export function renderBanner(container, healthInfo) {
  clear(container);
  if (!healthInfo) return;

  const isMemory = healthInfo.storage_mode === "memory";
  const isRules = healthInfo.ai_mode === "rules";

  let msg = `Active in ${healthInfo.city_name}. `;
  msg += isMemory
    ? "Storage: In-Memory (data resets on restart). "
    : "Storage: Upstash Redis. ";
  msg += isRules
    ? "AI: Rule Heuristics (Add GEMINI_API_KEY for live GenAI). "
    : "AI: Google Gemini Flash Multimodal. ";
  msg += "Admin demo password: civic-demo-2026";

  const banner = h(
    "div",
    {
      class: "demo-banner",
      role: "region",
      "aria-label": "Environment notification",
    },
    h(
      "div",
      { class: "banner-content" },
      h(
        "span",
        { class: "badge badge-demo" },
        isMemory ? "Demo Mode" : "Cloud Production"
      ),
      h("span", { class: "banner-text" }, msg)
    )
  );

  container.appendChild(banner);
}
