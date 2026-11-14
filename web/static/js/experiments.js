/* Load summary CSVs from /api/results and draw the charts (owner: M4) */
(function () {
  const $ = (id) => document.getElementById(id);
  const get = (name) => fetch(`/api/results/${name}`).then((r) => (r.ok ? r.json() : null));
  const acoLabel = (g) => (g === "true" || g === "True" ? "ACO" : "Baseline");
  let scaling = null, failures = null;

  function draw() {
    if (scaling) {
      const rows = scaling.filter((r) => r.fail_rate === 0);
      lineChart($("cTime"), {series: seriesFromSummary(rows, {x: "n_agents", y: "build_time_mean",
        err: "build_time_ci95", group: "use_aco", label: acoLabel}), xLabel: "Agents", yLabel: "Build time (ticks)"});
      lineChart($("cEff"), {series: seriesFromSummary(rows, {x: "n_agents", y: "efficiency_mean",
        err: "efficiency_ci95", group: "use_aco", label: acoLabel}), xLabel: "Agents", yLabel: "Efficiency (blocks / agent-tick)"});
    }
    if (failures) {
      const rows = failures.filter((r) => r.use_aco === failures[0].use_aco);
      barChart($("cSlow"), {bars: rows.map((r) => ({label: `${Math.round(r.fail_rate * 100)}% failed`,
        value: r.slowdown, err: 0})), xLabel: "Share of robots failed", yLabel: "Slowdown (x)", refLine: 1});
      lineChart($("cFail"), {series: seriesFromSummary(rows, {x: "fail_rate", y: "build_time_mean",
        err: "build_time_ci95", label: () => "Build time"}), xLabel: "Failure rate", yLabel: "Build time (ticks)"});
    }
  }

  function badges(rows, el) {
    const runs = rows.reduce((s, r) => s + r.n_runs, 0);
    const exact = rows.reduce((s, r) => s + r.exact_rate * r.n_runs, 0) / runs;
    const done = rows.reduce((s, r) => s + r.completed_rate * r.n_runs, 0) / runs;
    el.innerHTML = `<span class="badge ${exact === 1 ? "ok" : "bad"}">Exact structure: ${(exact * 100).toFixed(0)}% of ${runs} runs</span>
                    <span class="badge ${done === 1 ? "ok" : "bad"}">Completed: ${(done * 100).toFixed(0)}%</span>`;
  }

  function table(rows) {
    const cols = ["n_agents", "fail_rate", "use_aco", "n_runs", "build_time_mean", "build_time_ci95", "accuracy_mean", "exact_rate", "slowdown"];
    $("tbl").innerHTML = "<tr>" + cols.map((c) => `<th>${c}</th>`).join("") + "</tr>" +
      rows.map((r) => "<tr>" + cols.map((c) => `<td>${r[c] ?? "-"}</td>`).join("") + "</tr>").join("");
  }

  (async function init() {
    [scaling, failures] = await Promise.all([get("scaling_summary"), get("failures_summary")]);
    if (!scaling && !failures) { $("empty").hidden = false; $("content").hidden = true; return; }
    $("empty").hidden = true;
    const all = [...(scaling || []), ...(failures || [])];
    badges(all, $("badges")); table(all); draw();
    window.addEventListener("resize", draw);
  })();
})();
