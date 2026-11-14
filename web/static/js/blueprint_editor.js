/* Click-to-draw blueprint editor (owner: M1 + M4). Cells: "t" target, "r" rock, "d" depot. */
(function () {
  const $ = (id) => document.getElementById(id);
  const cv = $("ed"), c = cv.getContext("2d");
  let W = 24, H = 12, cells = new Map(), tool = "target", painting = false;
  const key = (x, y) => x + "," + y;
  const COLORS = {t: "#6b7280", r: "#475569", d: "#f59e0b"};

  function size() { const cell = Math.floor(Math.min(800 / W, 480 / H)); cv.width = cell * W; cv.height = cell * H; return cell; }
  function draw() {
    const cell = size(); c.clearRect(0, 0, cv.width, cv.height);
    c.strokeStyle = "rgba(128,128,128,.25)";
    for (let x = 0; x <= W; x++) { c.beginPath(); c.moveTo(x*cell, 0); c.lineTo(x*cell, H*cell); c.stroke(); }
    for (let y = 0; y <= H; y++) { c.beginPath(); c.moveTo(0, y*cell); c.lineTo(W*cell, y*cell); c.stroke(); }
    cells.forEach((v, k) => { const [x, y] = k.split(",").map(Number); c.fillStyle = COLORS[v]; c.fillRect(x*cell+1, y*cell+1, cell-2, cell-2); });
  }
  function paint(e) {
    const r = cv.getBoundingClientRect(), cell = cv.width / W;
    const x = Math.floor((e.clientX - r.left) * (cv.width / r.width) / cell), y = Math.floor((e.clientY - r.top) * (cv.height / r.height) / cell);
    if (x < 0 || y < 0 || x >= W || y >= H) return;
    if (tool === "erase") cells.delete(key(x, y));
    else cells.set(key(x, y), tool === "target" ? "t" : tool === "rock" ? "r" : "d");
    draw();
  }
  function toBlueprint() {
    const pick = (v) => [...cells].filter(([, t]) => t === v).map(([k]) => k.split(",").map(Number));
    return {name: $("name").value, width: W, height: H, depth: 1, depots: pick("d"), obstacles: pick("r"), cells: pick("t").map(([x, y]) => [x, y, 0])};
  }
  function fromBlueprint(b) {
    W = b.width; H = b.height; $("w").value = W; $("h").value = H; cells = new Map();
    b.cells.forEach(([x, y]) => cells.set(key(x, y), "t")); b.obstacles.forEach(([x, y]) => cells.set(key(x, y), "r"));
    b.depots.forEach(([x, y]) => cells.set(key(x, y), "d")); draw();
  }
  function resize() { W = +$("w").value; H = +$("h").value; cells.forEach((_, k) => { const [x, y] = k.split(",").map(Number); if (x >= W || y >= H) cells.delete(k); }); draw(); }

  cv.addEventListener("mousedown", (e) => { painting = true; paint(e); });
  cv.addEventListener("mousemove", (e) => { if (painting) paint(e); });
  window.addEventListener("mouseup", () => { painting = false; });
  document.querySelectorAll("#tools button").forEach((b) => b.onclick = () => {
    tool = b.dataset.tool; document.querySelectorAll("#tools button").forEach((o) => o.classList.toggle("primary", o === b)); });
  $("w").onchange = $("h").onchange = resize;
  $("load").onchange = async () => { if ($("load").value) fromBlueprint(await (await fetch("/api/blueprint?path=" + encodeURIComponent($("load").value))).json()); };

  async function post(url) {
    const r = await fetch(url, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(toBlueprint())});
    return [r.ok, await r.json()];
  }
  $("btnValidate").onclick = async () => {
    const [, d] = await post("/api/blueprint/validate");
    $("msg").textContent = d.ok ? `Valid: ${d.targets} blocks, ${d.seeds.length} starting seed(s).` : "Not valid: " + d.error;
  };
  $("btnSave").onclick = async () => {
    const [ok, d] = await post("/api/blueprint/save");
    if (!ok) { $("msg").textContent = "Not saved: " + d.error; return; }
    location.href = "/?bp=" + encodeURIComponent(d.path);
  };
  (async function init() {
    const bps = await Api.blueprints();
    $("load").innerHTML += bps.map((b) => `<option value="${b}">${b.replace("blueprints/", "")}</option>`).join("");
    draw();
  })();
})();
