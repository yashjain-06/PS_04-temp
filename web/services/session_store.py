"""One simulation per visitor, so several people can use the site at once (owner: M4).

A random cookie ('sid') identifies the visitor; each sid gets its own SimRunner. Idle sessions are dropped after
30 minutes and the store is capped. Sessions live in memory, so run ONE worker process (see docs/deployment.md).
"""
from __future__ import annotations

import threading
import time
import uuid

from flask import g, request

from web.services.sim_runner import SimRunner

MAX_SESSIONS, TTL_SECONDS = 200, 1800


class SessionStore:
    def __init__(self):
        self._d: dict = {}
        self._lock = threading.Lock()

    def get(self, sid: str) -> SimRunner:
        now = time.time()
        with self._lock:
            for k in [k for k, (_, t) in self._d.items() if now - t > TTL_SECONDS]:
                del self._d[k]
            if sid not in self._d and len(self._d) >= MAX_SESSIONS:
                del self._d[min(self._d, key=lambda k: self._d[k][1])]       # drop the least recently used
            runner = self._d[sid][0] if sid in self._d else SimRunner()
            self._d[sid] = (runner, now)
            return runner

    def __len__(self) -> int:
        return len(self._d)


store = SessionStore()


def init_app(app) -> None:
    @app.before_request
    def _sid():
        g.sid = request.cookies.get("sid") or uuid.uuid4().hex
        g.new_sid = "sid" not in request.cookies

    @app.after_request
    def _cookie(resp):
        if getattr(g, "new_sid", False):
            resp.set_cookie("sid", g.sid, httponly=True, samesite="Lax", max_age=86400)
        return resp


def get_runner() -> SimRunner:
    return store.get(g.sid)
