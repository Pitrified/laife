// The player cards and the latest actions, built from the event stream.

const ACTIONS_KEPT = 6;

// The deepest active step, as Mission.active_focus() finds it.
function activeFocus(mission) {
  for (const step of mission.steps) {
    if (step.status === "active") {
      return activeFocus(step);
    }
  }
  return mission;
}

// Latest actions per player. A snapshot's history resets on a new mission, a
// plan and a completed step, so the list comes from the stream instead.
export class ActionLog {
  constructor() {
    this.byPlayer = new Map();
  }

  // Returns true when the event changed a list.
  add(event) {
    if (event.player === null) {
      return false;
    }
    const list = this.byPlayer.get(event.player) ?? [];
    if (event.event === "action") {
      list.unshift({
        turn: event.turn,
        type: event.extra.action_type,
        text: event.extra.action,
        result: null,
        count: 0,
      });
      list.length = Math.min(list.length, ACTIONS_KEPT);
      this.byPlayer.set(event.player, list);
      return true;
    }
    // Every turn observes, and every move step answers; only the rest are shown.
    if (event.event === "world_response" && event.extra.kind !== "WResObserve") {
      const last = list[0];
      if (last === undefined || last.turn !== event.turn) {
        return false;
      }
      const result = `${event.extra.kind} ${event.extra.status}`;
      last.count = last.result === result ? last.count + 1 : 1;
      last.result = result;
      last.status = event.extra.status;
      return true;
    }
    return false;
  }

  of(player) {
    return this.byPlayer.get(player) ?? [];
  }
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) {
    node.className = className;
  }
  if (text !== undefined) {
    node.textContent = text;
  }
  return node;
}

function card(player, actions, sprites, selected, onSelect) {
  const root = element("div", player.name === selected ? "player selected" : "player");
  root.dataset.player = player.name;
  root.addEventListener("click", () => onSelect(player.name));

  const head = element("div", "head");
  const url = sprites[player.player_type]?.[player.state];
  if (url !== undefined) {
    const img = element("img");
    img.src = url;
    img.alt = player.state;
    head.append(img);
  }
  const who = element("div");
  who.append(element("div", "name", player.name));
  who.append(element("div", "meta", `${player.state} · turn ${player.turn}`));
  head.append(who);
  root.append(head);

  const mission = element("div", "mission");
  if (player.mission.objective === "") {
    mission.append(element("span", "status", "no mission yet"));
  } else {
    mission.append(element("div", "objective", player.mission.objective));
    mission.append(element("div", "status", player.mission.status));
    const focus = activeFocus(player.mission);
    if (focus !== player.mission) {
      mission.append(element("div", "status", `now: ${focus.objective}`));
    }
  }
  root.append(mission);

  const list = element("ol", "actions");
  for (const action of actions) {
    const item = element("li", undefined, `t${action.turn} ${action.type}: ${action.text}`);
    if (action.result !== null) {
      const times = action.count > 1 ? ` x${action.count}` : "";
      item.append(" ", element("span", `result ${action.status}`, `-> ${action.result}${times}`));
    }
    list.append(item);
  }
  root.append(list);
  return root;
}

export function renderPlayers(container, snapshot, log, sprites, selected, onSelect) {
  container.replaceChildren(
    ...snapshot.players.map((p) => card(p, log.of(p.name), sprites, selected, onSelect)),
  );
}
