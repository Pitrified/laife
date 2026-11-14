// The panel: a card per player, or the detail of the selected player.
// Latest actions come from the event stream (ActionLog).

const ACTIONS_KEPT = 30;
const ACTIONS_ON_CARD = 3;

// The missions from the root down to the deepest active step, as Mission.active_focus() walks.
function activePath(mission) {
  const path = [mission];
  let node = mission;
  for (;;) {
    const next = node.steps.find((step) => step.status === "active");
    if (next === undefined) {
      return path;
    }
    path.push(next);
    node = next;
  }
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

function head(player, sprites, lines) {
  const root = element("div", "head");
  const url = sprites[player.player_type]?.[player.state];
  if (url !== undefined) {
    const img = element("img");
    img.src = url;
    img.alt = player.state;
    root.append(img);
  }
  const who = element("div");
  who.append(element("div", "name", player.name));
  for (const line of lines) {
    who.append(element("div", "meta", line));
  }
  root.append(who);
  return root;
}

function actionList(actions) {
  const list = element("ol", "actions");
  for (const action of actions) {
    const item = element("li", undefined, `t${action.turn} ${action.type}: ${action.text}`);
    if (action.result !== null) {
      const times = action.count > 1 ? ` x${action.count}` : "";
      item.append(" ", element("span", `result ${action.status}`, `-> ${action.result}${times}`));
    }
    list.append(item);
  }
  return list;
}

function card(player, actions, sprites, onSelect) {
  const root = element("div", "player");
  root.dataset.player = player.name;
  root.addEventListener("click", () => onSelect(player.name));
  root.append(head(player, sprites, [`${player.state} · turn ${player.turn}`]));

  const mission = element("div", "mission");
  if (player.mission.objective === "") {
    mission.append(element("span", "status", "no mission yet"));
  } else {
    mission.append(element("div", "objective", player.mission.objective));
    mission.append(element("div", "status", player.mission.status));
    const path = activePath(player.mission);
    if (path.length > 1) {
      mission.append(element("div", "status", `now: ${path.at(-1).objective}`));
    }
  }
  root.append(mission, actionList(actions.slice(0, ACTIONS_ON_CARD)));
  return root;
}

function missionNode(mission, onPath) {
  const finished = mission.status === "completed" || mission.status === "failed";
  const classes = ["node", onPath.has(mission) ? "on-path" : "", finished ? "finished" : ""];
  const item = element("li", classes.join(" ").trim());
  const line = element("div", "line");
  line.append(element("span", "objective", mission.objective || "(no objective yet)"));
  line.append(" ", element("span", `badge ${mission.status}`, mission.status));
  if (mission.consecutive_failures > 0) {
    line.append(
      " ",
      element("span", "failures", `${mission.consecutive_failures}/${mission.max_failures} failures`),
    );
  }
  item.append(line);
  if (mission.steps.length > 0) {
    const children = element("ul", "tree");
    for (const step of mission.steps) {
      children.append(missionNode(step, onPath));
    }
    item.append(children);
  }
  return item;
}

function section(title, ...content) {
  const root = element("section", "section");
  root.append(element("h3", undefined, title), ...content);
  return root;
}

function detail(player, actions, sprites, onBack) {
  const root = element("div", "detail");
  root.dataset.player = player.name;
  const back = element("button", "back", "all players");
  back.type = "button";
  back.addEventListener("click", onBack);
  root.append(back);
  root.append(
    head(player, sprites, [
      `${player.player_type} · ${player.state} · turn ${player.turn}`,
      `at (${player.position[0]}, ${player.position[1]})`,
    ]),
  );

  const tree = element("ul", "tree root");
  tree.append(missionNode(player.mission, new Set(activePath(player.mission))));
  root.append(section("Mission", tree));

  const inventory =
    player.inventory.length === 0
      ? element("p", "meta", "empty")
      : (() => {
          const list = element("ul", "inventory");
          for (const utensil of player.inventory) {
            const item = element("li");
            item.append(element("span", "name", utensil.name), ` ${utensil.description}`);
            list.append(item);
          }
          return list;
        })();
  root.append(section("Inventory", inventory));
  root.append(
    section("Actions", actions.length === 0 ? element("p", "meta", "none seen yet") : actionList(actions)),
  );
  return root;
}

// Cards for every player, or the detail of *selected* when it is set.
export function renderPanel(container, snapshot, log, sprites, selected, onSelect, onBack) {
  const player = snapshot.players.find((p) => p.name === selected);
  if (player !== undefined) {
    container.replaceChildren(detail(player, log.of(player.name), sprites, onBack));
    return;
  }
  container.replaceChildren(...snapshot.players.map((p) => card(p, log.of(p.name), sprites, onSelect)));
}
