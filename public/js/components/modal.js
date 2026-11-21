/**
 * Accessible dialog and modal component helper.
 */

function _buildModalHeader(title, onClose) {
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
  closeBtn.addEventListener("click", onClose);
  header.appendChild(closeBtn);

  return { header, closeBtn };
}

function _bindModalEvents(backdrop, close) {
  backdrop.addEventListener("keydown", (e) => {
    if (e.key === "Escape") close();
  });
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) close();
  });
}

export function openModal({ title, contentNode, onClose }) {
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  backdrop.setAttribute("role", "dialog");
  backdrop.setAttribute("aria-modal", "true");
  backdrop.setAttribute("aria-labelledby", "modal-title");

  const dialog = document.createElement("div");
  dialog.className = "modal-dialog";

  function close() {
    if (backdrop.parentNode) backdrop.parentNode.removeChild(backdrop);
    if (onClose) onClose();
  }

  const { header, closeBtn } = _buildModalHeader(title, close);
  const body = document.createElement("div");
  body.className = "modal-body";
  body.appendChild(contentNode);

  dialog.appendChild(header);
  dialog.appendChild(body);
  backdrop.appendChild(dialog);
  document.body.appendChild(backdrop);

  _bindModalEvents(backdrop, close);
  closeBtn.focus();
  return { close };
}
