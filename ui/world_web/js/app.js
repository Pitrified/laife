// Wires the page: the snapshot is what is drawn; each event schedules a fresh
// snapshot and feeds the action list.

import { control, fetchSprites, fetchState, openEvents } from "./api.js";
import { ActionLog, renderPlayers } from "./players.js";
import { WorldView } from "./world.js";

const REFRESH_MS = 250;

const ui = {
  canvas: document.getElementById("world"),
  players: document.getElementById("players"),
  pause: document.getElementById("pause"),
  step: document.getElementById("step"),
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
  if (snapshot === null) {
    return;
  }
  world.update(snapshot, selected);
  renderPlayers(ui.players, snapshot, log, sprites, selected, select);
  ui.pause.textContent = snapshot.paused ? "resume" : "pause";
  ui.pause.disabled = ended || snapshot.paused === null;
  ui.step.disabled = ended || !snapshot.paused;
  ui.quit.disabled = ended;
}

function select(name) {
  selected = selected === name ? null : name;
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

async function act(action) {
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
  }
}

async function start() {
  try {
    sprites = await fetchSprites();
    snapshot = await fetchState();
  } catch (error) {
    setStatus(`cannot reach the server: ${error.message}`, true);
    return;
  }
  world = new WorldView(ui.canvas, sprites);
  render();

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

  ui.pause.addEventListener("click", () => act(snapshot.paused ? "resume" : "pause"));
  ui.step.addEventListener("click", () => act("step"));
  ui.quit.addEventListener("click", () => {
    if (window.confirm("Stop the run? It cannot be restarted from the page.")) {
      act("quit");
    }
  });
  ui.canvas.addEventListener("click", (e) => {
    const name = world.playerAt(e.clientX, e.clientY);
    if (name !== null) {
      select(name);
    }
  });
  window.addEventListener("resize", () => world.draw());
}

start();
