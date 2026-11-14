// The world on a canvas, in world pixels scaled to fit.
// Terrains and buildings are placed by their top-left corner, players by their
// centre, as the pygame renderer places them.

const TERRAIN_COLORS = {
  forest: "rgb(34, 85, 34)",
  lake: "rgb(70, 130, 180)",
  fertile_land: "rgb(107, 142, 35)",
  plain: "rgb(210, 180, 140)",
};
const UNKNOWN_TERRAIN = "rgb(80, 80, 80)";
const BUILDING_FILL = "rgb(255, 100, 100)";
const BUILDING_TEXT = "rgb(100, 255, 100)";
const BACKGROUND = "rgb(50, 50, 50)";
const SELECTED = "#f2c14e";
const SPRITE_SIZE = 75;
const MARGIN = 20;

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

export class WorldView {
  constructor(canvas, sprites) {
    this.canvas = canvas;
    this.sprites = sprites;
    this.images = new Map();
    // The area shown; it only grows, so the view does not jump as players move.
    this.bounds = null;
    this.snapshot = null;
    this.selected = null;
    this.transform = { scale: 1, x: 0, y: 0 };
  }

  update(snapshot, selected) {
    this.snapshot = snapshot;
    this.selected = selected;
    this.growBounds(snapshot);
    this.draw();
  }

  growBounds(snapshot) {
    for (const [x, y, w, h] of boxesOf(snapshot)) {
      const box = [x - MARGIN, y - MARGIN, x + w + MARGIN, y + h + MARGIN];
      if (this.bounds === null) {
        this.bounds = box;
      } else {
        this.bounds = [
          Math.min(this.bounds[0], box[0]),
          Math.min(this.bounds[1], box[1]),
          Math.max(this.bounds[2], box[2]),
          Math.max(this.bounds[3], box[3]),
        ];
      }
    }
  }

  image(url) {
    let img = this.images.get(url);
    if (img === undefined) {
      img = new Image();
      img.onload = () => this.draw();
      img.src = url;
      this.images.set(url, img);
    }
    return img;
  }

  fitCanvas() {
    const ratio = window.devicePixelRatio || 1;
    const width = Math.round(this.canvas.clientWidth * ratio);
    const height = Math.round(this.canvas.clientHeight * ratio);
    if (this.canvas.width !== width || this.canvas.height !== height) {
      this.canvas.width = width;
      this.canvas.height = height;
    }
    const [x0, y0, x1, y1] = this.bounds;
    const scale = Math.min(width / (x1 - x0), height / (y1 - y0));
    this.transform = {
      scale,
      x: (width - (x1 - x0) * scale) / 2 - x0 * scale,
      y: (height - (y1 - y0) * scale) / 2 - y0 * scale,
    };
  }

  draw() {
    if (this.snapshot === null || this.bounds === null) {
      return;
    }
    this.fitCanvas();
    const ctx = this.canvas.getContext("2d");
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = BACKGROUND;
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    const { scale, x, y } = this.transform;
    ctx.setTransform(scale, 0, 0, scale, x, y);

    for (const t of this.snapshot.terrains) {
      ctx.fillStyle = TERRAIN_COLORS[t.terrain_type] ?? UNKNOWN_TERRAIN;
      ctx.fillRect(t.position[0], t.position[1], t.size[0], t.size[1]);
    }

    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = "16px Helvetica, sans-serif";
    for (const b of this.snapshot.buildings) {
      const [w, h] = b.building_type.size;
      ctx.fillStyle = BUILDING_FILL;
      ctx.fillRect(b.position[0], b.position[1], w, h);
      ctx.fillStyle = BUILDING_TEXT;
      ctx.fillText(b.name, b.position[0] + w / 2, b.position[1] + h / 2, w);
    }

    const half = SPRITE_SIZE / 2;
    for (const p of this.snapshot.players) {
      const [px, py] = p.position;
      const url = this.sprites[p.player_type]?.[p.state];
      const img = url === undefined ? null : this.image(url);
      if (img !== null && img.complete && img.naturalWidth > 0) {
        ctx.drawImage(img, px - half, py - half, SPRITE_SIZE, SPRITE_SIZE);
      } else {
        ctx.fillStyle = SELECTED;
        ctx.fillRect(px - 4, py - 4, 8, 8);
      }
      if (p.name === this.selected) {
        ctx.strokeStyle = SELECTED;
        ctx.lineWidth = 3 / scale;
        ctx.strokeRect(px - half, py - half, SPRITE_SIZE, SPRITE_SIZE);
      }
      ctx.fillStyle = "white";
      ctx.fillText(p.name, px, py + half + 10);
    }
  }

  // The name of the player drawn at a point of the canvas, in CSS pixels, or null.
  playerAt(clientX, clientY) {
    if (this.snapshot === null) {
      return null;
    }
    const rect = this.canvas.getBoundingClientRect();
    const ratio = this.canvas.width / rect.width;
    const { scale, x, y } = this.transform;
    const wx = ((clientX - rect.left) * ratio - x) / scale;
    const wy = ((clientY - rect.top) * ratio - y) / scale;
    const half = SPRITE_SIZE / 2;
    const hit = this.snapshot.players.find(
      (p) => Math.abs(wx - p.position[0]) <= half && Math.abs(wy - p.position[1]) <= half,
    );
    return hit === undefined ? null : hit.name;
  }
}
