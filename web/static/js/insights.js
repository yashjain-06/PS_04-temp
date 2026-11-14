/* Predicted build-time curves and surrogate accuracy (owner: M4) */
(function () {
  const $ = (id) => document.getElementById(id);
  async function load() {
    $("err").textContent = "";
    const r = await fetch("/api/insights?blueprint=" + encodeURIComponent($("bp").value));
    const d = await r.json();
    if (!r.ok) { $("err").textContent = d.error; return; }
    const pts = (c) => c.map((p) => ({x: p.n_agents, y: p.predicted_build_time, err: 0}));
    lineChart($("cPred"), {series: [{name: "Baseline routes", points: pts(d.baseline.curve)}, {name: "ACO routes", points: pts(d.aco.curve)}],
                           xLabel: "Agents", yLabel: "Predicted build time (ticks)"});
    $("rec").innerHTML = `<span class="badge ok">Baseline: best about ${d.baseline.best_n_agents} agents (${d.baseline.predicted_build_time} ticks)</span>
                          <span class="badge ok">ACO: best about ${d.aco.best_n_agents} agents (${d.aco.predicted_build_time} ticks)</span>`;
    const rep = d.report;
    if (!rep) { $("rep").innerHTML = ""; return; }
    const h = rep.held_out_seed;
    let rows = `<tr><th>Test</th><th>R&sup2;</th><th>MAE (ticks)</th></tr>
      <tr><td>Held-out seed, gradient boosting</td><td>${h.gbr.r2}</td><td>${h.gbr.mae_ticks}</td></tr>
      <tr><td>Held-out seed, ridge baseline</td><td>${h.ridge_baseline.r2}</td><td>${h.ridge_baseline.mae_ticks}</td></tr>
      <tr><td>Held-out seed, always predict the mean</td><td>-</td><td>${h.predict_mean_baseline_mae}</td></tr>`;
    Object.entries(rep.leave_one_blueprint_out).forEach(([k, v]) => {
      rows += `<tr><td>Unseen blueprint: ${k}</td><td>${v.r2}</td><td>${v.mae_ticks}</td></tr>`; });
    $("rep").innerHTML = rows;
  }
  (async function () {
    const bps = (await Api.blueprints()).filter((b) => !b.includes("uploads"));
    $("bp").innerHTML = bps.map((b) => `<option value="${b}">${b.split("/").pop()}</option>`).join("");
    const pref = bps.find((b) => b.includes("wall_with_opening")); if (pref) $("bp").value = pref;
    $("bp").onchange = load; load();
  })();
})();
