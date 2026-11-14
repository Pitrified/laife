// The world in PixiJS, inside a pixi-viewport for drag, wheel zoom and pinch.
// World coordinates are the game's pixels. Terrains and buildings are placed by
// their top-left corner, players by their centre, as the pygame renderer places them.

import { Application, Assets, Container, Graphics, Sprite, Text } from "pixi.js";
import { Viewport } from "pixi-viewport";

const TERRAIN_COLORS = {
  forest: 0x225522,
  lake: 0x4682b4,
  fertile_land: 0x6b8e23,
  plain: 0xd2b48c,
};
const UNKNOWN_TERRAIN = 0x505050;
const BUILDING_FILL = 0xff6464;
const BUILDING_TEXT = 0x64ff64;
const BACKGROUND = 0x323232;
const SELECTED = 0xf2c14e;
const SPRITE_SIZE = 75;
const MARGIN = 20;
const MAX_ZOOM = 4;
// Zooming out stops a little past the fit, so the whole world is always reachable.
const MIN_ZOOM_OF_FIT = 0.8;
const MOVE_MS = 200;
// A move longer than this is drawn as a jump, not a slide.
const MAX_SLIDE = 300;
const CENTRE_MS = 400;

function boxesOf(snapshot) {
  const half = SPRITE_SIZE / 2;
  return [
    ...snapshot.terrains.map((t) => [t.position[0], t.position[1], t.size[0], t.size[1]]),
    ...snapshot.buildings.map((b) => [
      b.position[0],
      b.position[1],
      b.building_type.size[0],
      b.building_type.size[1],
    ]),
    ...snapshot.players.map((p) => [p.position[0] - half, p.position[1] - half, SPRITE_SIZE, SPRITE_SIZE]),
  ];
}

// A key that changes when the list of terrains or buildings changes.
function layoutKey(snapshot) {
  return JSON.stringify([
    snapshot.terrains.map((t) => [t.name, t.position, t.size]),
    snapshot.buildings.map((b) => [b.name, b.position, b.building_type.size]),
  ]);
}

class PlayerFigure {
  constructor(textures) {
    this.textures = textures;
    this.root = new Container();
    this.outline = new Graphics()
      .rect(-SPRITE_SIZE / 2, -SPRITE_SIZE / 2, SPRITE_SIZE, SPRITE_SIZE)
      .stroke({ width: 3, color: SELECTED });
    this.sprite = new Sprite();
    this.sprite.anchor.set(0.5);
    this.label = new Text({ text: "", style: { fontSize: 14, fill: 0xffffff, fontFamily: "Helvetica, sans-serif" } });
    this.label.anchor.set(0.5, 0);
    this.label.position.set(0, SPRITE_SIZE / 2 + 2);
    this.root.addChild(this.sprite, this.outline, this.label);
    this.slide = null;
    this.placed = false;
  }

  update(player, selected, now) {
    this.label.text = player.name;
    const texture = this.textures[player.player_type]?.[player.state];
    if (texture !== undefined && this.sprite.texture !== texture) {
      this.sprite.texture = texture;
      this.sprite.width = SPRITE_SIZE;
      this.sprite.height = SPRITE_SIZE;
    }
    this.outline.visible = selected;
    const [x, y] = player.position;
    const from = { x: this.root.x, y: this.root.y };
    const far = Math.hypot(x - from.x, y - from.y) > MAX_SLIDE;
    if (!this.placed) {
      this.placed = true;
      this.root.position.set(x, y);
    } else if (far) {
      this.slide = null;
      this.root.position.set(x, y);
    } else if (x !== from.x || y !== from.y) {
      this.slide = { from, to: { x, y }, start: now };
    }
  }

  tick(now) {
    if (this.slide === null) {
      return;
    }
    const t = Math.min(1, (now - this.slide.start) / MOVE_MS);
    const { from, to } = this.slide;
    this.root.position.set(from.x + (to.x - from.x) * t, from.y + (to.y - from.y) * t);
    if (t === 1) {
      this.slide = null;
    }
  }
}

export class WorldView {
  // PixiJS starts asynchronously, so a view is made with create(), not new.
  static async create(pane, sprites, onPick) {
    const view = new WorldView(pane, onPick);
    await view.init(sprites);
    return view;
  }

  constructor(pane, onPick) {
    this.pane = pane;
    this.onPick = onPick;
    // The area shown when fitting; it only grows, so the view does not jump as players move.
    this.bounds = null;
    this.layout = null;
    this.snapshot = null;
    this.figures = new Map();
  }

  async init(sprites) {
    this.app = new Application();
    await this.app.init({
      resizeTo: this.pane,
      background: BACKGROUND,
      antialias: true,
      autoDensity: true,
      resolution: window.devicePixelRatio || 1,
      preference: "webgl",
    });
    this.app.canvas.id = "world";
    this.pane.append(this.app.canvas);

    this.textures = {};
    for (const [type, states] of Object.entries(sprites)) {
      this.textures[type] = {};
      for (const [state, url] of Object.entries(states)) {
        this.textures[type][state] = await Assets.load(url);
      }
    }

    this.viewport = new Viewport({
      screenWidth: this.pane.clientWidth,
      screenHeight: this.pane.clientHeight,
      events: this.app.renderer.events,
    });
    this.viewport.drag().pinch().wheel().decelerate();
    this.app.stage.addChild(this.viewport);
    this.terrains = new Container();
    this.buildings = new Container();
    this.players = new Container();
    this.viewport.addChild(this.terrains, this.buildings, this.players);

    this.viewport.on("clicked", (event) => {
      const name = this.playerAt(event.world.x, event.world.y);
      if (name !== null) {
        this.onPick(name);
      }
    });
    this.viewport.on("zoomed", () => this.markZoom());
    this.app.renderer.on("resize", (width, height) => {
      this.viewport.resize(width, height);
      this.limitZoom();
    });
    this.app.ticker.add(() => {
      const now = performance.now();
      for (const figure of this.figures.values()) {
        figure.tick(now);
      }
    });
  }

  update(snapshot, selected) {
    const first = this.snapshot === null;
    this.snapshot = snapshot;
    this.growBounds(snapshot);
    const key = layoutKey(snapshot);
    if (key !== this.layout) {
      this.layout = key;
      this.drawLayout(snapshot);
    }
    const now = performance.now();
    for (const player of snapshot.players) {
      let figure = this.figures.get(player.name);
      if (figure === undefined) {
        figure = new PlayerFigure(this.textures);
        this.figures.set(player.name, figure);
        this.players.addChild(figure.root);
      }
      figure.update(player, player.name === selected, now);
    }
    if (first) {
      this.fit();
    } else {
      this.limitZoom();
    }
  }

  drawLayout(snapshot) {
    this.terrains.removeChildren().forEach((child) => child.destroy());
    this.buildings.removeChildren().forEach((child) => child.destroy());
    const ground = new Graphics();
    for (const t of snapshot.terrains) {
      ground.rect(t.position[0], t.position[1], t.size[0], t.size[1]).fill(TERRAIN_COLORS[t.terrain_type] ?? UNKNOWN_TERRAIN);
    }
    this.terrains.addChild(ground);
    for (const b of snapshot.buildings) {
      const [w, h] = b.building_type.size;
      const block = new Graphics().rect(b.position[0], b.position[1], w, h).fill(BUILDING_FILL);
      const name = new Text({ text: b.name, style: { fontSize: 14, fill: BUILDING_TEXT, fontFamily: "Helvetica, sans-serif" } });
      name.anchor.set(0.5);
      name.position.set(b.position[0] + w / 2, b.position[1] + h / 2);
      if (name.width > w) {
        name.scale.set(w / name.width);
      }
      this.buildings.addChild(block, name);
    }
  }

  growBounds(snapshot) {
    for (const [x, y, w, h] of boxesOf(snapshot)) {
      const box = [x - MARGIN, y - MARGIN, x + w + MARGIN, y + h + MARGIN];
      this.bounds =
        this.bounds === null
          ? box
          : [
              Math.min(this.bounds[0], box[0]),
              Math.min(this.bounds[1], box[1]),
              Math.max(this.bounds[2], box[2]),
              Math.max(this.bounds[3], box[3]),
            ];
    }
  }

  fitScale() {
    const [x0, y0, x1, y1] = this.bounds;
    return Math.min(this.viewport.screenWidth / (x1 - x0), this.viewport.screenHeight / (y1 - y0));
  }

  limitZoom() {
    if (this.bounds === null) {
      return;
    }
    this.viewport.clampZoom({ minScale: this.fitScale() * MIN_ZOOM_OF_FIT, maxScale: MAX_ZOOM });
    this.markZoom();
  }

  // Show the whole world, centred.
  fit() {
    if (this.bounds === null) {
      return;
    }
    const [x0, y0, x1, y1] = this.bounds;
    this.viewport.setZoom(this.fitScale(), true);
    this.viewport.moveCenter((x0 + x1) / 2, (y0 + y1) / 2);
    this.limitZoom();
  }

  centreOn(name) {
    const figure = this.figures.get(name);
    if (figure === undefined) {
      return;
    }
    this.viewport.animate({ position: { x: figure.root.x, y: figure.root.y }, time: CENTRE_MS, ease: "easeInOutSine" });
  }

  // The zoom, kept on the canvas so a browser test can read it.
  markZoom() {
    this.app.canvas.dataset.zoom = this.viewport.scale.x.toFixed(4);
  }

  // The name of the player drawn at a world point, or null.
  playerAt(wx, wy) {
    if (this.snapshot === null) {
      return null;
    }
    const half = SPRITE_SIZE / 2;
    for (const [name, figure] of this.figures) {
      if (Math.abs(wx - figure.root.x) <= half && Math.abs(wy - figure.root.y) <= half) {
        return name;
      }
    }
    return null;
  }
}
