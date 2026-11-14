// Run: node tests/charts_helpers.test.js   (owner: M4)
const {niceTicks, seriesFromSummary} = require("../web/static/js/charts.js");
let bad = 0;
const eq = (a, b, m) => { const ok = JSON.stringify(a) === JSON.stringify(b); bad += !ok;
  console.log(ok ? "PASS" : "FAIL", m, ok ? "" : JSON.stringify(a)); };
eq(niceTicks(0, 101), [0, 25, 50, 75, 100, 125], "ticks 0-101");
eq(niceTicks(0, 1.3), [0, 0.5, 1, 1.5], "ticks 0-1.3");
eq(niceTicks(5, 5).length > 1, true, "flat range still gives ticks");
const rows = [{n: 20, t: 50, e: 1, a: true}, {n: 10, t: 100, e: 2, a: true}, {n: 10, t: 101, e: 3, a: false}];
const s = seriesFromSummary(rows, {x: "n", y: "t", err: "e", group: "a", label: (g) => (g === "true" ? "ACO" : "Base")});
eq(s.map((x) => x.name), ["ACO", "Base"], "series names");
eq(s[0].points.map((p) => p.x), [10, 20], "points sorted by x");
eq(s[0].points[0], {x: 10, y: 100, err: 2}, "point values");
process.exit(bad ? 1 : 0);
