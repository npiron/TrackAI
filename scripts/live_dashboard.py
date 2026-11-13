"""Tableau de bord en direct de l'apprentissage, dans le navigateur.

Usage : python3 manage.py dashboard [--run data/checkpoints/f1_1t] [--port 8765]
Un petit serveur local (bibliothèque standard uniquement) lit progress.csv, train_stats.csv et config.json
des dossiers de data/checkpoints/ ; la page se met à jour toute seule toutes les 5 s.
"""
import argparse
import csv
import json
import os
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CKPT = os.path.join(ROOT, "data", "checkpoints")
PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_dashboard.html")
sys.path.insert(0, ROOT)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

# Évaluation de chaque génération sur des circuits fixes (toujours les mêmes : comparables d'une génération
# et d'un run à l'autre), politique déterministe, 1 tour. Résultats gardés dans <run>/eval_vitesse.csv.
EVAL_SEEDS = (11, 22, 33, 44, 55)
EVAL_FILE = "eval_vitesse.csv"
EVAL_COLS = ["gen", "vitesse_tour", "tours_finis", "chocs_moy"]


def eval_generation(path):
    """(vitesse moyenne au tour en fraction de la vitesse max, part des tours bouclés, chocs moyens)."""
    import numpy as np
    from scripts.eval import _load_model, detect_action_set, detect_obs_version
    from src.rl.wrappers import GymTimeAttack
    model, vn = _load_model(path)
    env = GymTimeAttack(render_mode=None, procedural=True, laps=1, track_variant=2,
                        obs_version=detect_obs_version(model), action_set=detect_action_set(model))
    speeds, done_laps, hits = [], 0, []
    for seed in EVAL_SEEDS:
        obs, _ = env.reset(options={"track_seed": seed})
        while True:
            o = obs if vn is None else np.clip((obs - vn.obs_rms.mean) / np.sqrt(vn.obs_rms.var + vn.epsilon),
                                               -vn.clip_obs, vn.clip_obs)
            obs, _, term, trunc, info = env.step(int(model.predict(o, deterministic=True)[0]))
            if term or trunc:
                break
        speeds += info.get("lap_speeds", [])
        done_laps += int(info.get("laps_done", 0) >= 1)
        hits.append(info.get("wall_hits", 0))
    env.close()
    return (round(float(np.mean(speeds)), 4) if speeds else None, round(done_laps / len(EVAL_SEEDS), 3),
            round(float(np.mean(hits)), 2))


def evaluator(server):
    """Fil de fond : évalue les nouvelles générations du run affiché (une à la fois, priorité basse)."""
    import glob
    import re
    try:
        os.nice(10)
    except OSError:
        pass
    while True:
        run = server.active_run
        d = os.path.join(CKPT, run) if run else None
        todo = None
        if d and os.path.isdir(d):
            done = {int(r["gen"]) for r in read_csv(os.path.join(d, EVAL_FILE)) if r.get("gen") is not None}
            for p in sorted(glob.glob(os.path.join(d, "gen_*.zip"))):
                m = re.search(r"gen_(\d+)\.zip$", p)
                if m and int(m.group(1)) not in done:
                    todo = (int(m.group(1)), p)
                    break
        if todo is None:
            time.sleep(3)
            continue
        gen, p = todo
        try:
            speed, laps, hits = eval_generation(p)
        except Exception as e:  # modèle illisible (ancien format) : on note l'échec pour ne pas boucler
            print(f"évaluation impossible de {p} : {e}", flush=True)
            speed, laps, hits = None, None, None
        path = os.path.join(d, EVAL_FILE)
        new = not os.path.isfile(path)
        with open(path, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(EVAL_COLS)
            w.writerow([gen, "" if speed is None else speed, "" if laps is None else laps, "" if hits is None else hits])


def runs():
    """Dossiers d'entraînement (avec progress.csv), le plus récemment modifié d'abord."""
    out = []
    for name in os.listdir(CKPT):
        p = os.path.join(CKPT, name, "progress.csv")
        if os.path.isfile(p):
            out.append((os.path.getmtime(p), name))
    return [n for _, n in sorted(out, reverse=True)]


def read_csv(path):
    if not os.path.isfile(path):
        return []
    with open(path, newline="") as f:
        rows = []
        for r in csv.DictReader(f):
            row = {}
            for k, v in r.items():
                try:
                    row[k] = float(v)
                except (TypeError, ValueError):
                    row[k] = None
            rows.append(row)
        return rows


def run_data(name):
    d = os.path.join(CKPT, os.path.basename(name))
    cfg = {}
    if os.path.isfile(os.path.join(d, "config.json")):
        with open(os.path.join(d, "config.json")) as f:
            cfg = json.load(f)
    finished = os.path.isfile(os.path.join(d, "last.zip"))
    prog = os.path.join(d, "progress.csv")
    age = time.time() - os.path.getmtime(prog) if os.path.isfile(prog) else None
    return {"name": os.path.basename(name), "config": cfg, "finished": finished, "age_s": age,
            "progress": read_csv(os.path.join(d, "progress.csv")),
            "stats": read_csv(os.path.join(d, "train_stats.csv")),
            "eval": read_csv(os.path.join(d, EVAL_FILE))}


def summary():
    """Meilleure vitesse évaluée (5 circuits fixes) de chaque run qui a été évalué."""
    out = []
    for name in runs():
        rows = [r for r in read_csv(os.path.join(CKPT, name, EVAL_FILE)) if r.get("vitesse_tour") is not None]
        if rows:
            best = max(rows, key=lambda r: r["vitesse_tour"])
            out.append({"run": name, "best": best["vitesse_tour"], "gen": best["gen"], "last": rows[-1]["vitesse_tour"]})
    return out


class Handler(BaseHTTPRequestHandler):
    def _send(self, body, ctype):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            with open(PAGE, encoding="utf-8") as f:
                return self._send(f.read(), "text/html; charset=utf-8")
        if u.path == "/api/runs":
            r = runs()   # par défaut : le run imposé au lancement, sinon le plus récent (celui qui tourne)
            return self._send(json.dumps({"runs": r, "default": self.server.default_run or (r[0] if r else None)}),
                              "application/json")
        if u.path == "/api/summary":
            return self._send(json.dumps(summary()), "application/json")
        if u.path == "/api/data":
            name = parse_qs(u.query).get("run", [""])[0]
            if name not in runs():
                self.send_error(404, "run inconnu")
                return
            self.server.active_run = name   # le fil d'évaluation suit le run affiché
            return self._send(json.dumps(run_data(name)), "application/json")
        self.send_error(404)

    def log_message(self, *args):
        pass


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--run", default=None, help="dossier affiché au démarrage (défaut : le plus récent)")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-browser", action="store_true")
    a = p.parse_args(argv)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    srv.default_run = os.path.basename(os.path.normpath(a.run)) if a.run else None
    srv.active_run = srv.default_run or (runs() or [None])[0]
    threading.Thread(target=evaluator, args=(srv,), daemon=True).start()
    url = f"http://127.0.0.1:{a.port}/"
    print(f"Tableau de bord : {url}  (Ctrl+C pour arrêter)", flush=True)
    if not a.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main())
