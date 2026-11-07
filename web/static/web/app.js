/* Small helpers shared by all pages. No dependencies. */
function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  for (const c of children) node.append(c);  // strings become text nodes, never HTML
  return node;
}

function errorText(data, status) {
  if (data && typeof data === "object") {
    if (data.detail) return String(data.detail);
    const parts = Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(" ") : v}`);
    if (parts.length) return parts.join(" · ");
  }
  return `Request failed (${status}).`;
}

async function api(url, {method = "GET", json, body} = {}) {
  const init = {method, headers: {Accept: "application/json"}};
  if (json !== undefined) { init.body = JSON.stringify(json); init.headers["Content-Type"] = "application/json"; }
  else if (body) init.body = body;
  let res;
  try { res = await fetch(url, init); }
  catch { throw new Error("Cannot reach the server. Check that it is running."); }
  if (res.status === 204) return null;
  let data = null;
  try { data = await res.json(); } catch { /* non-JSON body */ }
  if (!res.ok) throw new Error(errorText(data, res.status));
  return data;
}

let toastTimer;
function toast(message, isError = false) {
  const t = document.getElementById("toast");
  t.textContent = message;
  t.className = "toast show" + (isError ? " error" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.className = "toast"; }, 4500);
}
