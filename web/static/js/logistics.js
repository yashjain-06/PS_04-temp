/* Side-by-side route comparison (owner: M3 + M4) */
(function () {
  const $ = (id) => document.getElementById(id);
  const A = new GridCanvas($("cBase")), B = new GridCanvas($("cAco"));
  $("cBase").width = $("cAco").width = 600; $("cBase").height = $("cAco").height = 300;

  function pseudo(site, route, color) {
    return {grid: site.grid, blueprint: site.blueprint, structure: [], depots: site.depots, obstacles: site.obstacles,
            agents: [], pheromone: [], traffic: [], routes: [{cells: route, color}]};
  }

  async function load() {
    $("err").textContent = "";
    const r = await fetch("/api/logistics?blueprint=" + encodeURIComponent($("bp").value));
    const d = await r.json();
    if (!r.ok) { $("err").textContent = d.error || "failed"; return; }
    const ex = d.example;
    A.draw(pseudo(d.site, [ex.src, ...ex.baseline_route], "#dc2626"));
    B.draw(pseudo(d.site, [ex.src, ...ex.aco_route], "#16a34a"));
    $("caption").textContent = `Example trip from depot ${JSON.stringify(ex.src)} to ${JSON.stringify(ex.dst)}: optimal ${ex.optimal} steps, ` +
      `baseline plan ${ex.baseline} steps (but it crosses the barrier, so robots must detour), ACO ${ex.aco} steps.`;
    const pct = (v) => (v * 100).toFixed(0) + "%";
    $("stats").innerHTML = "<tr><th></th><th>Baseline</th><th>ACO</th></tr>" +
      `<tr><td>Mean planned route length</td><td>${d.mean_baseline}</td><td>${d.mean_aco}</td></tr>` +
      `<tr><td>Mean optimal length (A*)</td><td>${d.mean_optimal}</td><td>${d.mean_optimal}</td></tr>` +
      `<tr><td>Routes that cross the barrier</td><td>${pct(d.baseline_obstacle_rate)}</td><td>${pct(d.aco_obstacle_rate)}</td></tr>` +
      `<tr><td>Length vs optimal (valid routes only)</td><td>n/a</td><td>${d.aco_vs_optimal}x</td></tr>` +
      `<tr><td>Sampled pairs / ACO fallbacks to A*</td><td>${d.pairs}</td><td>${d.aco_fallbacks}</td></tr>`;
    lineChart($("cConv"), {series: [{name: "ACO / optimal", points: d.convergence.map((v, i) => ({x: i + 1, y: v, err: 0}))}],
                           xLabel: "Iteration", yLabel: "Length / optimal", height: 240});
  }

  (async function init() {
    const bps = await Api.blueprints();
    $("bp").innerHTML = bps.map((b) => `<option value="${b}">${b.split("/").pop()}</option>`).join("");
    const pref = bps.find((b) => b.includes("wall_with_opening")); if (pref) $("bp").value = pref;
    $("bp").onchange = load; load();
  })();
})();
