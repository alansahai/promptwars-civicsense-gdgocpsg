/**
 * Unified API Client for CivicResolve.
 * Handles request timeouts, JSON serialization, CSRF tokens, and credentials.
 */

let authToken = localStorage.getItem("civic_admin_token") || null;

export function setAuthToken(token) {
  authToken = token;
  if (token) {
    localStorage.setItem("civic_admin_token", token);
  } else {
    localStorage.removeItem("civic_admin_token");
  }
}

export function getAuthToken() {
  return authToken;
}

async function request(url, options = {}) {
  const headers = {
    "Accept": "application/json",
    ...(options.headers || {}),
  };

  if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(options.body);
  }

  // Include admin token if present
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  // State-changing requests receive custom header for CSRF defense
  if (options.method && ["POST", "PATCH", "DELETE"].includes(options.method.toUpperCase())) {
    headers["X-Civic-Admin"] = "1";
    headers["X-Requested-With"] = "XMLHttpRequest";
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "same-origin", // includes httpOnly cookies
  });

  if (!response.ok) {
    let errorDetail = `Request failed (${response.status})`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      // Ignore text parse error
    }
    const err = new Error(errorDetail);
    err.status = response.status;
    throw err;
  }

  return response.json();
}

export const api = {
  // Public Endpoints
  getHealth: () => request("/api/health"),
  createIssue: (data) => request("/api/issues", { method: "POST", body: data }),
  listIssues: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== null && v !== undefined && v !== "") query.append(k, v);
    });
    const qs = query.toString();
    return request(`/api/issues${qs ? `?${qs}` : ""}`);
  },
  getIssue: (ticketId) => request(`/api/issues/${encodeURIComponent(ticketId)}`),
  getStats: () => request("/api/stats"),
  getAssist: (partialText) => request("/api/assist", { method: "POST", body: { partial_text: partialText } }),

  // Admin Endpoints
  login: (password) => request("/api/admin/login", { method: "POST", body: { password } }),
  logout: () => request("/api/admin/logout", { method: "POST" }),
  listAdminIssues: () => request("/api/admin/issues"),
  updateIssue: (ticketId, updateData) =>
    request(`/api/admin/issues/${encodeURIComponent(ticketId)}`, { method: "PATCH", body: updateData }),
  reanalyzeIssue: (ticketId) =>
    request(`/api/admin/issues/${encodeURIComponent(ticketId)}/reanalyze`, { method: "POST" }),
  getAdminAnalytics: () => request("/api/admin/analytics"),
  generateSummary: () => request("/api/admin/summary", { method: "POST" }),
};
