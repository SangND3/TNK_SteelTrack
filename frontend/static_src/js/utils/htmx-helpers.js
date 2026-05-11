/**
 * Global HTMX event hooks for TNK SteelTrack.
 * Keep Alpine.js for UI state; use these only for cross-cutting concerns.
 */

// Re-attach CSRF header on every request (redundant safety net)
document.body.addEventListener("htmx:configRequest", (e) => {
  e.detail.headers["X-CSRFToken"] =
    document.querySelector("meta[name='csrf-token']")?.content ?? "";
});

// Show a global spinner on HTMX requests
document.body.addEventListener("htmx:beforeRequest", () => {
  document.getElementById("global-spinner")?.classList.remove("hidden");
});
document.body.addEventListener("htmx:afterRequest", () => {
  document.getElementById("global-spinner")?.classList.add("hidden");
});

// Redirect on 401 (session expired)
document.body.addEventListener("htmx:responseError", (e) => {
  if (e.detail.xhr.status === 401) {
    window.location.href = "/accounts/login/";
  }
});
