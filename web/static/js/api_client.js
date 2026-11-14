/* fetch/EventSource wrappers (owner: M4) */
const Api = {
  async _json(url, opts) {
    const r = await fetch(url, opts);
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.error || r.statusText);
    return data;
  },
  _post(url, body) {
    return this._json(url, {method: "POST", headers: {"Content-Type": "application/json"},
                            body: JSON.stringify(body || {})});
  },
  blueprints() { return this._json("/api/blueprints"); },
  config()     { return this._json("/api/config"); },
  start(p)     { return this._post("/api/start", p); },
  step(n = 1)  { return this._post("/api/step", {n}); },
  pause()      { return this._post("/api/pause"); },
  resume()     { return this._post("/api/resume"); },
  reset()      { return this._post("/api/reset"); },
  metrics()    { return this._json("/api/metrics"); },
  openStream(sps, onSnapshot, onDone, onError) {
    const es = new EventSource(`/api/stream?sps=${sps}`);
    es.onmessage = (e) => onSnapshot(JSON.parse(e.data));
    es.addEventListener("done", (e) => onDone && onDone(JSON.parse(e.data)));
    es.onerror = () => onError && onError();
    return es;
  },
};
