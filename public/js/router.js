/**
 * Lightweight hash-based client router (#/report, #/track, #/dashboard, #/admin).
 */

class HashRouter {
  constructor() {
    this.routes = {};
    this.currentRoute = null;
    window.addEventListener("hashchange", () => this.handleRouting());
  }

  register(path, viewHandler) {
    this.routes[path] = viewHandler;
  }

  navigate(path) {
    window.location.hash = path.startsWith("#") ? path : `#${path}`;
  }

  handleRouting() {
    const hash = window.location.hash || "#/report";
    const [path, queryString] = hash.split("?");
    const params = new URLSearchParams(queryString || "");

    const handler = this.routes[path] || this.routes["#/report"];
    if (handler) {
      this.currentRoute = path;
      this.updateActiveNavLinks(path);
      handler(params);
    }
  }

  updateActiveNavLinks(activePath) {
    document.querySelectorAll("nav a[href]").forEach((link) => {
      const href = link.getAttribute("href");
      if (href === activePath) {
        link.classList.add("nav-active");
        link.setAttribute("aria-current", "page");
      } else {
        link.classList.remove("nav-active");
        link.removeAttribute("aria-current");
      }
    });
  }

  start() {
    this.handleRouting();
  }
}

export const router = new HashRouter();
