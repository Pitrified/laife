// The server's routes; see docs/guides/web.md.

async function getJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`${path}: ${response.status}`);
  }
  return response.json();
}

export function fetchState() {
  return getJson("/state");
}

export function fetchSprites() {
  return getJson("/sprites");
}

// action is pause, resume, step or quit.
export async function control(action) {
  const response = await fetch(`/control/${action}`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`/control/${action}: ${response.status}`);
  }
  return response.json();
}

// The browser reconnects an EventSource by itself after an error.
export function openEvents({ onEvent, onOpen, onError }) {
  const source = new EventSource("/events");
  source.onmessage = (message) => onEvent(JSON.parse(message.data));
  source.onopen = onOpen;
  source.onerror = onError;
  return source;
}
