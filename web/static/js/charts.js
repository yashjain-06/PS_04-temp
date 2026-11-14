/* Tiny dependency-free canvas charts with error bars (owner: M4).
   Works offline (no Chart.js). Pure helpers at the top are unit-tested with node. */

function niceTicks(min, max, n = 5) {
  if (min === max) { max = min + 1; }
  const raw = (max - min) / n, mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw);
  const lo = Math.floor(min / step) * step, hi = Math.ceil(max / step) * step, out = [];
  for (let v = lo; v <= hi + step / 2; v += step) out.push(+v.toFixed(10));
  return out;
}

function seriesFromSummary(rows, {x, y, err, group, label}) {
  const map = new Map();
  rows.forEach((r) => {
    const g = group ? String(r[group]) : "all";
    if (!map.has(g)) map.set(g, []);
    map.get(g).push({x: r[x], y: r[y], err: err ? (r[err] || 0) : 0});
  });
  return [...map].map(([name, points]) => ({
    name: label ? label(name) : name, points: points.sort((a, b) => a.x - b.x)}));
}

const PALETTE = ["#2f6fed", "#e8590c", "#16a34a", "#a855f7", "#0ea5a5"];

function _theme() {
  const cs = getComputedStyle(document.documentElement);
  return {ink: cs.getPropertyValue("--ink").trim() || "#222", muted: cs.getPropertyValue("--muted").trim() || "#666",
          line: cs.getPropertyValue("--line").trim() || "#ddd"};
}

function _setup(canvas, height) {
  const dpr = window.devicePixelRatio || 1, w = canvas.parentElement.clientWidth || 600;
  canvas.style.width = w + "px"; canvas.style.height = height + "px";
  canvas.width = w * dpr; canvas.height = height * dpr;
  const c = canvas.getContext("2d"); c.setTransform(dpr, 0, 0, dpr, 0, 0); c.clearRect(0, 0, w, height);
  return {c, w, h: height, th: _theme()};
}

function _axes(c, w, h, th, m, xt, yt, xLabel, yLabel, xFmt) {
  const X = (v) => m.l + (v - xt[0]) / (xt[xt.length - 1] - xt[0] || 1) * (w - m.l - m.r);
  const Y = (v) => h - m.b - (v - yt[0]) / (yt[yt.length - 1] - yt[0] || 1) * (h - m.t - m.b);
  c.font = "12px system-ui, sans-serif"; c.fillStyle = th.muted; c.strokeStyle = th.line; c.lineWidth = 1;
  yt.forEach((v) => { c.beginPath(); c.moveTo(m.l, Y(v)); c.lineTo(w - m.r, Y(v)); c.stroke();
                      c.textAlign = "right"; c.fillText(String(v), m.l - 6, Y(v) + 4); });
  c.textAlign = "center";
  xt.forEach((v) => c.fillText(xFmt ? xFmt(v) : String(v), X(v), h - m.b + 16));
  c.fillStyle = th.ink; c.fillText(xLabel, (m.l + w - m.r) / 2, h - 6);
  c.save(); c.translate(14, (m.t + h - m.b) / 2); c.rotate(-Math.PI / 2); c.fillText(yLabel, 0, 0); c.restore();
  return {X, Y};
}

function lineChart(canvas, {series, xLabel, yLabel, height = 300}) {
  const {c, w, h, th} = _setup(canvas, height), m = {l: 56, r: 16, t: 26, b: 40};
  const pts = series.flatMap((s) => s.points);
  if (!pts.length) { c.fillStyle = th.muted; c.fillText("No data", 20, 30); return; }
  const xs = [...new Set(pts.map((p) => p.x))].sort((a, b) => a - b);
  const yt = niceTicks(Math.min(0, ...pts.map((p) => p.y - p.err)), Math.max(...pts.map((p) => p.y + p.err)));
  const {X, Y} = _axes(c, w, h, th, m, xs, yt, xLabel, yLabel);
  series.forEach((s, i) => {
    const col = PALETTE[i % PALETTE.length];
    c.strokeStyle = col; c.fillStyle = col; c.lineWidth = 2; c.beginPath();
    s.points.forEach((p, j) => (j ? c.lineTo(X(p.x), Y(p.y)) : c.moveTo(X(p.x), Y(p.y)))); c.stroke();
    s.points.forEach((p) => {
      c.lineWidth = 1; c.beginPath(); c.moveTo(X(p.x), Y(p.y - p.err)); c.lineTo(X(p.x), Y(p.y + p.err));
      c.moveTo(X(p.x) - 4, Y(p.y - p.err)); c.lineTo(X(p.x) + 4, Y(p.y - p.err));
      c.moveTo(X(p.x) - 4, Y(p.y + p.err)); c.lineTo(X(p.x) + 4, Y(p.y + p.err)); c.stroke();
      c.beginPath(); c.arc(X(p.x), Y(p.y), 3.5, 0, Math.PI * 2); c.fill();
    });
    c.font = "12px system-ui, sans-serif"; c.textAlign = "left";
    c.fillRect(m.l + i * 130, 8, 10, 10); c.fillStyle = th.ink; c.fillText(s.name, m.l + i * 130 + 15, 17);
  });
}

function barChart(canvas, {bars, xLabel, yLabel, height = 300, refLine = null}) {
  const {c, w, h, th} = _setup(canvas, height), m = {l: 56, r: 16, t: 20, b: 40};
  if (!bars.length) { c.fillStyle = th.muted; c.fillText("No data", 20, 30); return; }
  const yt = niceTicks(0, Math.max(...bars.map((b) => b.value + (b.err || 0)), refLine || 0));
  const {Y} = _axes(c, w, h, th, m, [0], yt, "", yLabel);
  const slot = (w - m.l - m.r) / bars.length, bw = Math.min(70, slot * 0.6);
  bars.forEach((b, i) => {
    const cx = m.l + slot * (i + 0.5);
    c.fillStyle = PALETTE[0]; c.fillRect(cx - bw / 2, Y(b.value), bw, Y(0) - Y(b.value));
    if (b.err) { c.strokeStyle = th.ink; c.beginPath(); c.moveTo(cx, Y(b.value - b.err)); c.lineTo(cx, Y(b.value + b.err));
                 c.moveTo(cx - 5, Y(b.value + b.err)); c.lineTo(cx + 5, Y(b.value + b.err)); c.stroke(); }
    c.fillStyle = th.ink; c.textAlign = "center"; c.font = "12px system-ui, sans-serif";
    c.fillText(b.label, cx, h - m.b + 16); c.fillText(String(b.value), cx, Y(b.value) - 6 - (b.err ? Math.abs(Y(b.value) - Y(b.value + b.err)) : 0));
  });
  if (refLine !== null) { c.strokeStyle = "#dc2626"; c.setLineDash([5, 4]); c.beginPath();
    c.moveTo(m.l, Y(refLine)); c.lineTo(w - m.r, Y(refLine)); c.stroke(); c.setLineDash([]); }
  c.fillStyle = th.ink; c.textAlign = "center"; c.fillText(xLabel, (m.l + w - m.r) / 2, h - 6);
}

if (typeof module !== "undefined") module.exports = {niceTicks, seriesFromSummary};
