/**
 * System announcement and demo-mode status banner component.
 */

import { t } from "../i18n.js";

export function renderBanner(container, healthInfo) {
  container.innerHTML = "";
  if (!healthInfo) return;

  const isMemory = healthInfo.storage_mode === "memory";
  const isRules = healthInfo.ai_mode === "rules";

  const banner = document.createElement("div");
  banner.className = "demo-banner";
  banner.setAttribute("role", "region");
  banner.setAttribute("aria-label", "Environment notification");

  const content = document.createElement("div");
  content.className = "banner-content";

  const badge = document.createElement("span");
  badge.className = "badge badge-demo";
  badge.textContent = isMemory ? "Demo Mode" : "Cloud Production";
  content.appendChild(badge);

  const text = document.createElement("span");
  text.className = "banner-text";
  
  let msg = `Active in ${healthInfo.city_name}. `;
  if (isMemory) {
    msg += "Storage: In-Memory (data resets on restart). ";
  } else {
    msg += "Storage: Upstash Redis. ";
  }
  if (isRules) {
    msg += "AI: Rule Heuristics (Add GEMINI_API_KEY for live GenAI). ";
  } else {
    msg += "AI: Google Gemini Flash Multimodal. ";
  }
  msg += `Admin demo password: civic-demo-2026`;
  
  text.textContent = msg;
  content.appendChild(text);

  banner.appendChild(content);
  container.appendChild(banner);
}
