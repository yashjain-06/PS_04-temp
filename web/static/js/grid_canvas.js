/* Draw grid, blueprint ghost, blocks, pheromone, depots, robots (owner: M4).
   Input is the snapshot JSON from docs/interfaces.md. */
const STATE_COLORS = {seek: "#2f6fed", carry: "#16a34a", place: "#a855f7", return: "#0ea5a5"};

class GridCanvas {
  constructor(canvas, opts = {}) {
    this.canvas = canvas; this.ctx = canvas.getContext("2d");
    this.opts = Object.assign({traffic: false, pheromone: true}, opts);
  }

  draw(snap) {
    const {width: W, height: H} = snap.grid;
    const cell = Math.floor(Math.min(this.canvas.width / W, this.canvas.height / H));
    this.canvas.width = cell * W; this.canvas.height = cell * H;
    const c = this.ctx;
    c.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // traffic heatmap (red, alpha by how often robots stood there)
    if (this.opts.traffic) (snap.traffic || []).forEach((row, y) => row.forEach((v, x) => {
      if (v > 0) { c.fillStyle = `rgba(220,38,38,${Math.min(0.75, v * 0.75)})`; c.fillRect(x*cell, y*cell, cell, cell); }
    }));

    // pheromone heat (orange, alpha by value)
    if (this.opts.pheromone) (snap.pheromone || []).forEach((row, y) => row.forEach((v, x) => {
      if (v > 0.02) { c.fillStyle = `rgba(245,158,11,${Math.min(0.6, v * 0.6)})`; c.fillRect(x*cell, y*cell, cell, cell); }
    }));

    // grid lines
    c.strokeStyle = "rgba(128,128,128,.18)"; c.lineWidth = 1;
    for (let x = 0; x <= W; x++) { c.beginPath(); c.moveTo(x*cell, 0); c.lineTo(x*cell, H*cell); c.stroke(); }
    for (let y = 0; y <= H; y++) { c.beginPath(); c.moveTo(0, y*cell); c.lineTo(W*cell, y*cell); c.stroke(); }

    // rocks / barrier
    c.fillStyle = "#475569";
    (snap.obstacles || []).forEach(([x, y]) => c.fillRect(x*cell, y*cell, cell, cell));

    // blueprint ghost
    c.fillStyle = "rgba(47,111,237,.15)"; c.strokeStyle = "#2f6fed"; c.setLineDash([4, 3]);
    snap.blueprint.forEach(([x, y]) => { c.fillRect(x*cell, y*cell, cell, cell); c.strokeRect(x*cell+.5, y*cell+.5, cell-1, cell-1); });
    c.setLineDash([]);

    // built blocks
    c.fillStyle = "#6b7280";
    snap.structure.forEach(([x, y]) => c.fillRect(x*cell+1, y*cell+1, cell-2, cell-2));

    // depots
    c.fillStyle = "#f59e0b";
    snap.depots.forEach(([x, y]) => c.fillRect(x*cell+2, y*cell+2, cell-4, cell-4));

    // route overlays (logistics page): [{cells: [[x,y],...], color: "#hex"}]
    (snap.routes || []).forEach((r) => {
      c.strokeStyle = r.color; c.lineWidth = Math.max(2, cell * 0.18); c.beginPath();
      r.cells.forEach(([x, y], i) => (i ? c.lineTo(x*cell + cell/2, y*cell + cell/2) : c.moveTo(x*cell + cell/2, y*cell + cell/2)));
      c.stroke(); c.lineWidth = 1;
    });

    // robots
    snap.agents.forEach((a) => {
      const cx = a.x*cell + cell/2, cy = a.y*cell + cell/2, r = cell*0.32;
      if (a.failed) {
        c.strokeStyle = "#dc2626"; c.lineWidth = 3;
        c.beginPath(); c.moveTo(cx-r, cy-r); c.lineTo(cx+r, cy+r); c.moveTo(cx+r, cy-r); c.lineTo(cx-r, cy+r); c.stroke();
        c.lineWidth = 1; return;
      }
      c.fillStyle = STATE_COLORS[a.state] || "#000";
      c.beginPath(); c.arc(cx, cy, r, 0, Math.PI * 2); c.fill();
      if (a.carrying) { c.fillStyle = "#fff"; c.fillRect(cx-r/2.2, cy-r/2.2, r/1.1, r/1.1); }
    });
  }
}
