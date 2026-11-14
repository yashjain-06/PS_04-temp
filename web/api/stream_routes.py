"""Server-Sent Events stream: one snapshot per message (owner: M4)."""
import json
import time

from flask import Blueprint, Response, request, stream_with_context

from src.utils.config import load_config
from web.services.session_store import get_runner

bp = Blueprint("stream", __name__, url_prefix="/api")


@bp.get("/stream")
def stream():
    sps = float(request.args.get("sps") or load_config()["web"]["steps_per_second"])
    sps = min(max(sps, 1.0), 60.0)
    runner = get_runner()                      # resolve the visitor's runner now; the generator outlives the request context

    @stream_with_context
    def gen():
        while True:
            if runner.model is None:
                yield ": waiting\n\n"
            elif runner.running:
                snap = runner.step(1)
                yield f"data: {json.dumps(snap)}\n\n"
                if not runner.running:                    # finished this tick
                    yield f"event: done\ndata: {json.dumps(runner.metrics())}\n\n"
            else:
                yield ": paused\n\n"                      # keep-alive
            time.sleep(1.0 / sps)

    return Response(gen(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
