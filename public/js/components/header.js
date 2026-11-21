/**
 * Header and navigation component with accessibility & i18n controls.
 */

import { getLanguage, setLanguage, t } from "../i18n.js";

export function initHeader() {
  // Accessibility toggle: High contrast
  const contrastBtn = document.getElementById("btn-contrast");
  if (contrastBtn) {
    contrastBtn.addEventListener("click", () => {
      const isHigh = document.body.classList.toggle("high-contrast");
      localStorage.setItem("civic_high_contrast", isHigh ? "true" : "false");
      contrastBtn.setAttribute("aria-pressed", isHigh ? "true" : "false");
    });
    if (localStorage.getItem("civic_high_contrast") === "true") {
      document.body.classList.add("high-contrast");
      contrastBtn.setAttribute("aria-pressed", "true");
    }
  }

  // Accessibility toggle: Large text
  const fontBtn = document.getElementById("btn-font");
  if (fontBtn) {
    fontBtn.addEventListener("click", () => {
      const isLarge = document.body.classList.toggle("large-text");
      localStorage.setItem("civic_large_text", isLarge ? "true" : "false");
      fontBtn.setAttribute("aria-pressed", isLarge ? "true" : "false");
    });
    if (localStorage.getItem("civic_large_text") === "true") {
      document.body.classList.add("large-text");
      fontBtn.setAttribute("aria-pressed", "true");
    }
  }

  // Language switcher select
  const langSelect = document.getElementById("lang-select");
  if (langSelect) {
    langSelect.value = getLanguage();
    langSelect.addEventListener("change", (e) => {
      setLanguage(e.target.value);
    });
  }
}
