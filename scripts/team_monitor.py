#!/usr/bin/env python3
"""Moniteur TUI de l'équipe d'agents TrackAI (curses, sans dépendance).

Usage : python3 scripts/team_monitor.py
Touches : q quitter · ↑/↓ défiler le panneau actif · tab changer de panneau · l log plein écran
"""
import curses
import json
import locale
import re
import subprocess
import textwrap
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEAM = ROOT / ".team"
REFRESH = 2.0
STATUS = {"x": "validée", "?": "à relire", "~": "en cours", "-": "à reprendre", "!": "bloquée", " ": "à faire"}
TASK_RE = re.compile(r"^- \[(.)\] \*\*(T\d+)\*\* · (.+?)(?: · (P\d))?\s*$")


# ---------- données ----------

def sh(*cmd):
    try:
        return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return ""


def read(p):
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def tasks():
    out, cur = [], None
    for line in read(TEAM / "TODO.md").splitlines():
        m = TASK_RE.match(line)
        if m:
            cur = {"st": m[1], "id": m[2], "title": m[3], "prio": m[4] or "", "details": []}
            out.append(cur)
        elif cur and line.startswith("  - "):
            cur["details"].append(line[4:])
        elif not line.strip():
            cur = None
    return out


def journal():
    parts = re.split(r"^## ", read(TEAM / "JOURNAL.md"), flags=re.M)[1:]
    entries = []
    for p in parts:
        head, _, body = p.partition("\n")
        bits = [b.strip() for b in head.split("·")]
        entries.append((bits[0], bits[1] if len(bits) > 1 else "", " · ".join(bits[2:]), body.strip()))
    return entries[::-1]


def loop_state():
    ps = sh("ps", "-Ao", "etime,command").splitlines()
    loop = next((l for l in ps if "team_loop.sh" in l and "grep" not in l), None)
    agent = None
    for l in ps:
        m = re.search(r"claude -p .*--agent (\w+)", l)
        if m:
            agent = m[1]
    logs = sorted((TEAM / "logs").glob("*.log"))
    last = logs[-1] if logs else None
    return {
        "running": loop is not None,
        "elapsed": loop.split()[0] if loop else "",
        "agent": agent if loop else None,
        "log": last.name if last else "",
        "log_lines": [l for l in read(last).splitlines() if "connectors are disabled" not in l] if last else [],
        "replan": (TEAM / "REPLAN").exists(),
        "stop": (TEAM / "STOP").exists(),
    }


def state():
    try:
        metrics = json.loads(read(TEAM / "metrics.json") or "[]")
    except Exception:
        metrics = []
    return {
        "loop": loop_state(),
        "tasks": tasks(),
        "journal": journal(),
        "metrics": metrics,
        "inbox": [p.name for p in sorted((TEAM / "inbox").glob("*.md"))],
        "branch": sh("git", "rev-parse", "--abbrev-ref", "HEAD").strip(),
        "commits": sh("git", "log", "--oneline", "-15").strip().splitlines(),
        "dirty": len(sh("git", "status", "--short").strip().splitlines()),
    }


# ---------- affichage ----------

C = {}


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    pairs = {"ok": curses.COLOR_GREEN, "info": curses.COLOR_CYAN, "run": curses.COLOR_MAGENTA,
             "warn": curses.COLOR_YELLOW, "bad": curses.COLOR_RED, "mute": 8 if curses.COLORS > 8 else curses.COLOR_WHITE,
             "title": curses.COLOR_BLUE}
    for i, (k, col) in enumerate(pairs.items(), 1):
        curses.init_pair(i, col, -1)
        C[k] = curses.color_pair(i)


ST_COLOR = {"x": "ok", "?": "info", "~": "run", "-": "warn", "!": "bad", " ": "mute"}
AGENT_COLOR = {"planner": "run", "worker": "info", "reviewer": "ok", "boucle": "warn"}


def put(win, y, x, text, attr=0):
    h, w = win.getmaxyx()
    if 0 <= y < h and x < w - 1:
        try:
            win.addnstr(y, x, text, w - 1 - x, attr)
        except curses.error:
            pass


def box(win, title, active):
    win.erase()
    win.attron(C["title"] if active else C["mute"])
    win.box()
    win.attroff(C["title"] if active else C["mute"])
    put(win, 0, 2, f" {title} ", curses.A_BOLD | (C["title"] if active else 0))


def lines_tasks(d, w):
    out = []
    counts = {}
    for t in d["tasks"]:
        counts[t["st"]] = counts.get(t["st"], 0) + 1
    out.append([("  ".join(f"{STATUS[k]} {v}" for k, v in counts.items()), C["mute"])])
    out.append([])
    for t in d["tasks"]:
        col = C[ST_COLOR.get(t["st"], "mute")]
        out.append([(f"[{t['st']}] ", col | curses.A_BOLD), (f"{t['id']} ", curses.A_BOLD),
                    (t["title"], 0), (f"  {t['prio']}", C["mute"])])
        if t["st"] not in "x":
            for det in t["details"]:
                for l in textwrap.wrap(det, max(10, w - 10)):
                    out.append([("      " + l, C["mute"])])
    return out


def lines_journal(d, w):
    out = []
    for when, agent, subj, body in d["journal"]:
        out.append([(when + " ", C["mute"]), (f"{agent} ", C[AGENT_COLOR.get(agent, "mute")] | curses.A_BOLD),
                    (subj, curses.A_BOLD)])
        for raw in body.splitlines():
            for l in textwrap.wrap(raw, max(10, w - 6)) or [""]:
                out.append([("  " + l, 0)])
        out.append([])
    return out


def lines_side(d, w):
    out = [[("Métriques", curses.A_BOLD)]]
    if d["metrics"]:
        for m in d["metrics"][-6:][::-1]:
            out.append([("  " + json.dumps(m, ensure_ascii=False)[: w - 6], 0)])
    else:
        out.append([("  aucune mesure", C["mute"])])
    out += [[], [("Inbox", curses.A_BOLD)]]
    out += [[("  " + f, C["warn"])] for f in d["inbox"]] or [[("  vide", C["mute"])]]
    out += [[], [(f"Git · {d['branch']}", curses.A_BOLD), (f"  {d['dirty']} modif(s) non commitée(s)" if d["dirty"] else "", C["warn"])]]
    for c in d["commits"]:
        h, _, msg = c.partition(" ")
        out.append([("  " + h + " ", C["warn"]), (msg, 0)])
    return out


def draw_lines(win, lines, scroll):
    h, w = win.getmaxyx()
    view = lines[scroll: scroll + h - 2]
    for i, segs in enumerate(view):
        x = 2
        for text, attr in segs:
            put(win, i + 1, x, text, attr)
            x += len(text)
    if len(lines) > h - 2:
        put(win, h - 1, w - 12, f" {scroll + 1}/{len(lines)} ", C["mute"])


def header(scr, d):
    L = d["loop"]
    w = scr.getmaxyx()[1]
    scr.move(0, 0)
    scr.clrtoeol()
    put(scr, 0, 1, " Équipe TrackAI ", curses.A_REVERSE | curses.A_BOLD)
    x = 19
    if L["running"]:
        s = f"● boucle active {L['elapsed']}"
        put(scr, 0, x, s, C["ok"] | curses.A_BOLD)
    else:
        s = "○ boucle à l'arrêt"
        put(scr, 0, x, s, C["mute"])
    x += len(s) + 3
    a = L["agent"] or "aucun agent"
    put(scr, 0, x, f"agent : {a}", C[AGENT_COLOR.get(a, "mute")] | curses.A_BOLD)
    x += len(a) + 12
    if L["replan"]:
        put(scr, 0, x, "REPLAN", C["warn"] | curses.A_BOLD)
        x += 8
    if L["stop"]:
        put(scr, 0, x, "STOP demandé", C["bad"] | curses.A_BOLD)
    put(scr, 0, w - 10, time.strftime("%H:%M:%S"), C["mute"])


def footer(scr):
    h, w = scr.getmaxyx()
    put(scr, h - 1, 1, "q quitter · ↑↓/PgUp/PgDn défiler · tab panneau · l log", C["mute"])


def main(scr):
    curses.curs_set(0)
    init_colors()
    scr.timeout(int(REFRESH * 1000))
    panels = ["todo", "journal", "side", "log"]
    active, scroll, full_log = 1, {p: 0 for p in panels}, False
    d, last = state(), time.time()
    while True:
        if time.time() - last >= REFRESH:
            d, last = state(), time.time()
        H, W = scr.getmaxyx()
        scr.erase()
        header(scr, d)
        footer(scr)
        if H < 16 or W < 70:
            put(scr, 2, 1, "Terminal trop petit (70x16 minimum)")
            scr.refresh()
        else:
            body_h = H - 2
            if full_log:
                wins = {"log": (body_h, W, 1, 0)}
            else:
                top = max(8, int(body_h * 0.68))
                lw = W // 3
                rw = W // 3
                wins = {
                    "todo": (top, lw, 1, 0),
                    "journal": (top, W - lw - rw, 1, lw),
                    "side": (top, rw, 1, W - rw),
                    "log": (body_h - top, W, 1 + top, 0),
                }
            scr.noutrefresh()
            content = {}
            for name, (h, w, y, x) in wins.items():
                win = curses.newwin(h, w, y, x)
                title = {"todo": "Todo", "journal": "Journal", "side": "Métriques · inbox · git",
                         "log": f"Dernier log · {d['loop']['log'] or '—'}"}[name]
                box(win, title, panels[active] == name or full_log)
                if name == "todo":
                    lines = lines_tasks(d, w)
                elif name == "journal":
                    lines = lines_journal(d, w)
                elif name == "side":
                    lines = lines_side(d, w)
                else:
                    lines = []
                    for raw in d["loop"]["log_lines"]:
                        lines += [[(l, 0)] for l in textwrap.wrap(raw, max(10, w - 4)) or [""]]
                    if not (panels[active] == "log" or full_log):
                        scroll["log"] = max(0, len(lines) - (h - 2))  # suivre la fin
                content[name] = (len(lines), h)
                scroll[name] = max(0, min(scroll[name], len(lines) - (h - 2)))
                draw_lines(win, lines, scroll[name])
                win.noutrefresh()
            curses.doupdate()

        k = scr.getch()
        if k in (ord("q"), 27):
            break
        name = "log" if full_log else panels[active]
        step = {curses.KEY_DOWN: 1, ord("j"): 1, curses.KEY_UP: -1, ord("k"): -1,
                curses.KEY_NPAGE: 10, curses.KEY_PPAGE: -10}.get(k)
        if step:
            scroll[name] = max(0, scroll[name] + step)
        elif k == 9:
            active = (active + 1) % len(panels)
        elif k == ord("l"):
            full_log = not full_log
        elif k == curses.KEY_RESIZE:
            curses.update_lines_cols()


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
