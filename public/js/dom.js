/**
 * Safe, zero-dependency DOM and SVG element builder.
 *
 * Guarantees zero innerHTML usage across the entire application,
 * preventing DOM-based cross-site scripting vulnerabilities.
 */

"use strict";

const SVG_NS = "http://www.w3.org/2000/svg";

/**
 * Remove all child nodes from a DOM element safely.
 * @param {HTMLElement} node - Target container element to empty.
 */
export function clear(node) {
  if (!node) return;
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

/**
 * Apply attributes, event listeners, and dataset properties to an element.
 * @param {Element} el - Target DOM or SVG element.
 * @param {Object} props - Attribute and event mapping.
 */
function applyProps(el, props) {
  if (!props) return;
  for (const [key, val] of Object.entries(props)) {
    if (val === undefined || val === null) continue;

    if (key.startsWith("on") && typeof val === "function") {
      const eventName = key.slice(2).toLowerCase();
      el.addEventListener(eventName, val);
    } else if (key === "className" || key === "class") {
      el.setAttribute("class", String(val));
    } else if (key === "dataset" && typeof val === "object") {
      for (const [dKey, dVal] of Object.entries(val)) {
        el.dataset[dKey] = String(dVal);
      }
    } else if (key === "style" && typeof val === "object") {
      for (const [sKey, sVal] of Object.entries(val)) {
        el.style[sKey] = sVal;
      }
    } else if (typeof val === "boolean") {
      if (val) el.setAttribute(key, "");
      else el.removeAttribute(key);
    } else {
      el.setAttribute(key, String(val));
    }
  }
}

/**
 * Append child nodes or text to a parent element.
 * @param {Element} parent - Parent element.
 * @param {Array} children - Child elements, strings, numbers, or arrays.
 */
function appendChildren(parent, children) {
  for (const child of children.flat(Infinity)) {
    if (child === undefined || child === null || child === false) continue;
    if (child instanceof Node) {
      parent.appendChild(child);
    } else {
      parent.appendChild(document.createTextNode(String(child)));
    }
  }
}

/**
 * Construct an HTML element with safe props and children.
 * @param {string} tag - HTML tag name.
 * @param {Object} [props={}] - Element attributes and listeners.
 * @param {...(Node|string|number|Array)} children - Child elements or text.
 * @returns {HTMLElement} Newly created HTML element.
 */
export function h(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  applyProps(el, props);
  appendChildren(el, children);
  return el;
}

/**
 * Construct an SVG element within the SVG namespace.
 * @param {string} tag - SVG tag name.
 * @param {Object} [props={}] - SVG attributes and listeners.
 * @param {...(Node|string|number|Array)} children - Child SVG elements or text.
 * @returns {SVGElement} Newly created SVG element.
 */
export function svg(tag, props = {}, ...children) {
  const el = document.createElementNS(SVG_NS, tag);
  applyProps(el, props);
  appendChildren(el, children);
  return el;
}
