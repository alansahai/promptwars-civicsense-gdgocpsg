/**
 * Accessible dialog and modal component helper.
 */

export function openModal({ title, contentNode, onClose }) {
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  backdrop.setAttribute("role", "dialog");
  backdrop.setAttribute("aria-modal", "true");
  backdrop.setAttribute("aria-labelledby", "modal-title");

  const dialog = document.createElement("div");
  dialog.className = "modal-dialog";

  const header = document.createElement("div");
  header.className = "modal-header";

  const titleEl = document.createElement("h2");
  titleEl.id = "modal-title";
  titleEl.textContent = title;
  header.appendChild(titleEl);

  const closeBtn = document.createElement("button");
  closeBtn.className = "btn btn-icon btn-close";
  closeBtn.setAttribute("aria-label", "Close modal");
  closeBtn.textContent = "✕";
  closeBtn.addEventListener("click", close);
  header.appendChild(closeBtn);

  const body = document.createElement("div");
  body.className = "modal-body";
  body.appendChild(contentNode);

  dialog.appendChild(header);
  dialog.appendChild(body);
  backdrop.appendChild(dialog);
  document.body.appendChild(backdrop);

  function close() {
    if (backdrop.parentNode) {
      backdrop.parentNode.removeChild(backdrop);
    }
    if (onClose) onClose();
  }

  // Keyboard navigation & escape listener
  backdrop.addEventListener("keydown", (e) => {
    if (e.key === "Escape") close();
  });
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) close();
  });

  closeBtn.focus();
  return { close };
}
