#!/usr/bin/env python3
"""TrackAI : commandes du projet (toujours sur les circuits longs aléatoires et la physique actuelle).

  python manage.py play                 conduire soi-même (circuits longs, 3 tours, N : nouveau circuit)
  python manage.py train --minutes 360  entraîner de zéro (obs v3, 15 actions) ; --live : fenêtre qui suit l'entraînement
  python manage.py watch                regarder le bot du dernier entraînement (Rust, 60-120 fps ; --follow DOSSIER, --hard)
  python manage.py hard-tracks --model M  classer les circuits où le bot M se plante le plus (data/hard_tracks/)
  python manage.py dashboard            graphiques de l'apprentissage en direct dans le navigateur
  python manage.py test                 lancer les tests

Les options non listées sont passées telles quelles au script appelé
(scripts/human_lap.py, scripts/train_long.py, scripts/watch_best.py).
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PY = ROOT / ".venv" / "bin" / "python"
if sys.prefix == sys.base_prefix and VENV_PY.exists():  # relancer avec le Python du venv
    os.execv(str(VENV_PY), [str(VENV_PY)] + sys.argv)

DEFAULT_RUN = "data/checkpoints/f1"
SIM_RS = ROOT / "sim-rs"
VIEWER = SIM_RS / "target" / "release" / "trackai"


def viewer(args, wait=True):
    """Viewer Rust (sim-rs/viewer) : compilé au besoin, lancé depuis la racine du projet."""
    sources = [p for p in (SIM_RS / "viewer" / "src").glob("*.rs")] + [p for p in (SIM_RS / "core" / "src").glob("*.rs")]
    if not VIEWER.exists() or max(p.stat().st_mtime for p in sources) > VIEWER.stat().st_mtime:
        print("$ cargo build --release -p trackai-viewer", flush=True)
        if subprocess.call(["cargo", "build", "--release", "-p", "trackai-viewer"], cwd=SIM_RS) != 0:
            return 1
    cmd = [str(VIEWER)] + [str(a) for a in args]
    print("$", " ".join(cmd), flush=True)
    if not wait:
        return subprocess.Popen(cmd, cwd=ROOT)
    return subprocess.call(cmd, cwd=ROOT)


def latest_run():
    """Dossier d'entraînement le plus récent (qui contient des générations)."""
    runs = [d for d in (ROOT / "data" / "checkpoints").glob("*") if d.is_dir() and any(d.glob("gen_*.zip"))]
    return str(max(runs, key=lambda d: max(g.stat().st_mtime for g in d.glob("gen_*.zip"))).relative_to(ROOT)) if runs else None


def run(args, wait=True):
    cmd = [sys.executable] + [str(a) for a in args]
    print("$", " ".join(cmd[1:]), flush=True)
    if not wait:
        return subprocess.Popen(cmd, cwd=ROOT)
    return subprocess.call(cmd, cwd=ROOT)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("play", help="conduire soi-même (viewer Rust, 60-120 fps)")
    sub.add_parser("play-py", help="conduire soi-même (ancienne version Pygame)")
    t = sub.add_parser("train", help="entraînement PPO de zéro (obs v3, 15 actions)")
    t.add_argument("--out-dir", default=DEFAULT_RUN)
    t.add_argument("--live", action="store_true", help="ouvre aussi une fenêtre qui suit les générations")
    w = sub.add_parser("watch", help="regarder un bot (viewer Rust, 60-120 fps) ; sans option : le dernier entraînement")
    w.add_argument("--follow", default=None, metavar="DOSSIER", help="suivre un entraînement en cours")
    wp = sub.add_parser("watch-py", help="regarder un bot (ancienne version Pygame)")
    wp.add_argument("--follow", default=None, metavar="DOSSIER")
    sub.add_parser("hard-tracks", help="classer les circuits où un bot se plante le plus")
    sub.add_parser("dashboard", help="graphiques de l'apprentissage en direct (navigateur)")
    sub.add_parser("test", help="lancer les tests")
    a, rest = p.parse_known_args()

    if a.command == "play":
        return viewer(["--play", "--laps", "3", *rest])
    if a.command == "play-py":
        return run(["scripts/human_lap.py", "--long", "--laps", "3", *rest])
    if a.command == "train":
        train = ["scripts/train_long.py", "--out-dir", a.out_dir, *rest]
        if not a.live:
            return run(train)
        proc = run(train, wait=False)
        try:
            laps = ["--laps", rest[rest.index("--laps") + 1]] if "--laps" in rest else []
            viewer(["--follow", a.out_dir, *laps])
        finally:
            print(f"Fenêtre fermée : l'entraînement continue (pid {proc.pid}, sortie dans {a.out_dir}).")
        return proc.wait()
    if a.command == "watch":
        follow = a.follow or (None if "--model" in rest else latest_run())
        extra = ["--follow", follow] if follow else []
        return viewer([*extra, *rest])
    if a.command == "watch-py":
        extra = ["--follow", a.follow] if a.follow else []
        return run(["scripts/watch_best.py", "--long", *extra, *rest])
    if a.command == "hard-tracks":
        return run(["scripts/hard_tracks.py", *rest])
    if a.command == "dashboard":
        return run(["scripts/live_dashboard.py", *rest])
    if a.command == "test":
        return run(["-m", "pytest", "-q", "tests/", *rest])
    return 1


if __name__ == "__main__":
    sys.exit(main())
