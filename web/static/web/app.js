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

/* Streaming POST: reads a Server-Sent Events body incrementally.
   EventSource cannot POST, so we use fetch + ReadableStream and split the text on blank lines ourselves. */
async function streamSSE(url, json, handlers) {
  let res;
  try {
    res = await fetch(url, {method: "POST", headers: {"Content-Type": "application/json", Accept: "text/event-stream"}, body: JSON.stringify(json)});
  } catch { throw new Error("Cannot reach the server. Check that it is running."); }
  if (!res.ok) {  // errors before the stream starts (400, 502, 503) are normal JSON
    let data = null;
    try { data = await res.json(); } catch { /* non-JSON body */ }
    throw new Error(errorText(data, res.status));
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "", finished = false;
  while (true) {
    const {value, done} = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, {stream: true});
    let end;
    while ((end = buffer.indexOf("\n\n")) !== -1) {      // one complete event
      const block = buffer.slice(0, end); buffer = buffer.slice(end + 2);
      const event = /^event: (.*)$/m.exec(block)?.[1];
      const data = /^data: (.*)$/m.exec(block)?.[1];
      if (!event || data === undefined) continue;
      if (event === "done" || event === "error") finished = true;
      handlers[event]?.(JSON.parse(data));
    }
  }
  if (!finished) throw new Error("The connection closed before the answer was complete.");
}
