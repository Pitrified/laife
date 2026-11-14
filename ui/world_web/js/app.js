// Wires the page: the snapshot is what is drawn; each event schedules a fresh
// snapshot and feeds the action list.

import { control, fetchSprites, fetchState, openEvents } from "./api.js";
import { ActionLog, renderPanel } from "./players.js";
import { WorldView } from "./world.js";

const REFRESH_MS = 250;

const ui = {
  pane: document.getElementById("world-pane"),
  players: document.getElementById("players"),
  pause: document.getElementById("pause"),
  step: document.getElementById("step"),
  fit: document.getElementById("fit"),
  quit: document.getElementById("quit"),
  status: document.getElementById("status"),
};

const log = new ActionLog();
let sprites = {};
let world = null;
let snapshot = null;
let selected = null;
let ended = false;
let refreshTimer = null;
let events = null;

function setStatus(text, isEnded = false) {
  ui.status.textContent = text;
  ui.status.classList.toggle("ended", isEnded);
}

function render() {
  if (snapshot === null || world === null) {
    return;
  }
  world.update(snapshot, selected);
  renderPanel(ui.players, snapshot, log, sprites, selected, select, back);
  ui.pause.textContent = snapshot.paused ? "resume" : "pause";
  ui.pause.disabled = ended || snapshot.paused === null;
  ui.step.disabled = ended || !snapshot.paused;
  ui.quit.disabled = ended;
  ui.fit.disabled = false;
}

// Show one player's detail and bring it into view.
function select(name) {
  selected = name;
  render();
  world.centreOn(name);
}

function back() {
  selected = null;
  render();
}

async function refresh() {
  refreshTimer = null;
  if (ended) {
    return;
  }
  try {
    snapshot = await fetchState();
    render();
  } catch (error) {
    setStatus(`state unavailable: ${error.message}`);
  }
}

function scheduleRefresh() {
  if (refreshTimer === null) {
    refreshTimer = setTimeout(refresh, REFRESH_MS);
  }
}

function end(reason) {
  ended = true;
  if (events !== null) {
    events.close();
  }
  setStatus(reason, true);
  render();
}

function connect() {
  events = openEvents({
    onEvent: (event) => {
      if (log.add(event)) {
        render();
      }
      scheduleRefresh();
    },
    onOpen: () => {
      setStatus("connected");
      scheduleRefresh();
    },
    onError: () => {
      if (ended) {
        return;
      }
      setStatus("reconnecting");
      // A stream also errors when the run stops; ask the server whether it is still there.
      fetchState().catch(() => end("run ended: the server is gone"));
    },
  });
}

async function act(action) {
  if (action === "quit") {
    // Closed first: the server ends the stream as it stops, and an open
    // EventSource would try to reconnect to it.
    events.close();
  }
  try {
    const answer = await control(action);
    if (action === "quit") {
      end("run ended");
      return;
    }
    snapshot = { ...snapshot, paused: answer.paused };
    render();
    scheduleRefresh();
  } catch (error) {
    setStatus(`${action} failed: ${error.message}`);
    if (action === "quit") {
      connect();
    }
  }
}

async function start() {
  try {
    sprites = await fetchSprites();
    snapshot = await fetchState();
    world = await WorldView.create(ui.pane, sprites, select);
  } catch (error) {
    setStatus(`cannot start: ${error.message}`, true);
    return;
  }
  render();
  connect();

  ui.pause.addEventListener("click", () => act(snapshot.paused ? "resume" : "pause"));
  ui.step.addEventListener("click", () => act("step"));
  ui.fit.addEventListener("click", () => world.fit());
  ui.quit.addEventListener("click", () => {
    if (window.confirm("Stop the run? It cannot be restarted from the page.")) {
      act("quit");
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && selected !== null) {
      back();
    }
  });
}

start();
