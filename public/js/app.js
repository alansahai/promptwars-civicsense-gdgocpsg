/**
 * Application bootstrap entry point.
 * Initializes header, environment banner, router, and default view.
 */

import { api } from "./api.js";
import { renderBanner } from "./components/banner.js";
import { initHeader } from "./components/header.js";
import { updateI18nTexts } from "./i18n.js";
import { router } from "./router.js";
import { renderAdminView } from "./views/admin.js";
import { renderDashboardView } from "./views/dashboard.js";
import { renderReportView } from "./views/report.js";
import { renderTrackView } from "./views/track.js";

async function init() {
  const mainContent = document.getElementById("main-content");
  const bannerContainer = document.getElementById("banner-container");

  // Initialize accessibility toggles & header events
  initHeader();

  // Fetch health & environment status
  try {
    const health = await api.getHealth();
    renderBanner(bannerContainer, health);
  } catch (err) {
    console.warn("Unable to fetch health status:", err);
  }

  // Register router views
  router.register("#/report", () => {
    renderReportView(mainContent);
    updateI18nTexts();
  });

  router.register("#/track", (params) => {
    renderTrackView(mainContent, params);
    updateI18nTexts();
  });

  router.register("#/dashboard", () => {
    renderDashboardView(mainContent);
    updateI18nTexts();
  });

  router.register("#/admin", () => {
    renderAdminView(mainContent);
    updateI18nTexts();
  });

  // Start routing
  router.start();
  updateI18nTexts();
}

window.addEventListener("DOMContentLoaded", init);
