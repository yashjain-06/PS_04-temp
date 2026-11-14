# Putting it on the web

The app is a normal Flask app. Each visitor gets their own simulation (cookie `sid`), kept in memory.
Because sessions live in memory, **always run exactly one worker process**; use threads for concurrency
(each live view holds one thread, so `--threads 32` serves about 30 people watching at the same time).

## A. Same Wi-Fi (fastest for a demo room)
```bash
HOST=0.0.0.0 python scripts/run_server.py          # Windows PowerShell:  $env:HOST="0.0.0.0"; python scripts/run_server.py
```
Find your laptop's IP (`ipconfig` / `ifconfig`) and open `http://<that-ip>:5000` on another device.
If it does not load, allow Python through the firewall.

## B. A public link from your laptop (ngrok or Cloudflare Tunnel)
```bash
python scripts/run_server.py                       # terminal 1
ngrok http 5000                                    # terminal 2 -> prints https://xxxx.ngrok-free.app
```
Share the https link. It works while your laptop and both terminals stay running.

## C. A permanent site on Render (free plan available)
1. Put the project on GitHub (`git init`, `git add .`, `git commit`, `git push`).
2. On render.com: New > Web Service > connect the repo.
3. Settings: Runtime **Python 3**; Build command `pip install -r requirements.txt`;
   Start command `gunicorn wsgi:app --worker-class gthread --workers 1 --threads 32 --timeout 0 --bind 0.0.0.0:$PORT`
   (this is also in the `Procfile`); environment variable `PYTHON_VERSION` = `3.11.9`.
4. Deploy. You get `https://<name>.onrender.com`.
Free plans sleep after ~15 minutes idle and take up to a minute to wake: open the site before you present.
Railway and Fly.io work the same way (they read the `Procfile` / `Dockerfile`).

## D. Docker (any host)
```bash
docker build -t swarm .
docker run -p 8000:8000 swarm                      # http://localhost:8000
```

## Things to know
- Python 3.10-3.12. gunicorn runs on Linux/Mac only (hosts are Linux); on Windows use `scripts/run_server.py`.
- Public limits built in: 1-60 agents per run, idle sessions dropped after 30 min (max 200), at most 100 saved blueprints.
  There is no login and no rate limiting, so do not leave it open to the world for long.
- Experiment charts read the CSVs in `results/`, which are included. Re-run `make experiments` to refresh them.
- The ML model is retrained automatically from `results/raw/surrogate_data.csv` if the saved file does not load.
- Not tested here: gunicorn, Docker and the hosting platforms (the sandbox has no network). The Flask server, per-visitor sessions and the
  live stream were tested over real HTTP.
