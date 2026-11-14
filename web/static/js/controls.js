/* Wire up buttons, sliders and the live stream (owner: M4) */
(function () {
  const $ = (id) => document.getElementById(id);
  const grid = new GridCanvas($("grid"));
  let stream = null, started = false, last = null;

  function show(snap) {
    last = snap; grid.draw(snap);
    const m = snap.metrics;
    $("mTick").textContent = snap.tick;
    $("mAcc").textContent = (m.accuracy * 100).toFixed(1) + "%";
    $("mPlaced").textContent = m.placed;
    $("mAgents").textContent = `${m.active_agents} / ${m.failed_agents}`;
    $("mBlocked").textContent = m.blocked_ticks ?? "-";
    $("mStatus").textContent = m.complete ? "complete" : (stream ? "running" : "paused");
  }
  async function showMetrics() {
    const m = await Api.metrics();
    if (m.efficiency !== undefined) $("mEff").textContent = m.efficiency;
  }
  function closeStream() { if (stream) { stream.close(); stream = null; } }
  function openStream() {
    closeStream();
    stream = Api.openStream(+$("speed").value, show,
      async () => { closeStream(); $("mStatus").textContent = "complete"; await showMetrics(); },
      () => {});
  }
  function params() {
    return {blueprint: $("blueprint").value, n_agents: +$("nAgents").value,
            fail_rate: +$("failRate").value / 100, use_aco: $("useAco").checked, pso_depots: $("usePso").checked, fail_at_tick: +$("failAt").value, seed: +$("seed").value};
  }

  [["nAgents", "nAgentsVal"], ["failRate", "failVal"], ["speed", "speedVal"]].forEach(([i, o]) =>
    $(i).addEventListener("input", () => { $(o).textContent = $(i).value; }));
  $("showTraffic").onchange = () => { grid.opts.traffic = $("showTraffic").checked; if (last) grid.draw(last); };
  $("showPher").onchange = () => { grid.opts.pheromone = $("showPher").checked; if (last) grid.draw(last); };
  $("speed").addEventListener("change", () => { if (stream) openStream(); });

  $("btnStart").onclick = async () => {
    try { show(await Api.start(params())); started = true; openStream(); }
    catch (e) { $("mStatus").textContent = "error: " + e.message; }
  };
  $("btnPause").onclick = async () => {
    if (!started) return;
    if (stream) { closeStream(); await Api.pause(); $("btnPause").textContent = "Resume"; $("mStatus").textContent = "paused"; }
    else { await Api.resume(); openStream(); $("btnPause").textContent = "Pause"; }
  };
  $("btnStep").onclick = async () => {
    if (!started) return;
    closeStream(); await Api.pause(); $("btnPause").textContent = "Resume";
    show(await Api.step(1));
  };
  $("btnReset").onclick = async () => {
    closeStream(); await Api.reset(); started = false;
    ["mTick","mAcc","mPlaced","mAgents","mEff","mBlocked"].forEach((i) => $(i).textContent = "-");
    $("mStatus").textContent = "idle"; $("btnPause").textContent = "Pause";
    grid.ctx.clearRect(0, 0, $("grid").width, $("grid").height);
  };

  (async function init() {
    const bps = await Api.blueprints();
    $("blueprint").innerHTML = bps.map((b) => `<option value="${b}">${b.split("/").pop()}</option>`).join("");
    const q = new URLSearchParams(location.search).get("bp");
    const pref = bps.includes(q) ? q : bps.find((b) => b.includes("wall_with_opening")); if (pref) $("blueprint").value = pref;
    $("modelNote").textContent = "Each robot senses only a radius-2 window plus the blueprint. No central scheduler.";
  })();
})();
