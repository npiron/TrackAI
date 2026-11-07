# .goal: how the team works

Four Claude Code agents move this project toward the goal in `GOAL.md`. They coordinate only through the files in this folder. The loop (`goal run`) calls **one agent per step**, chosen from the state of the work.

| Agent | Role | Writes |
|---|---|---|
| `goal-lead` | Turns the goal into a measurable success criterion and a roadmap of epics. Decides on blocked stories and inbox messages. Declares the goal reached. Never codes, never writes stories. | criterion in `GOAL.md`, `ROADMAP.md`, story status (blocked → draft or dropped), `JOURNAL.md`, empties `inbox/` |
| `goal-refiner` | Reads the code and splits an epic into user stories that meet the Definition of Ready. Never codes. | `stories/S-<n>.md`, `JOURNAL.md` |
| `goal-dev` | Implements one ready story with its tests, checks it, hands it over. Never commits. | code, its story (status, `## Dev notes`), `JOURNAL.md`, `inbox/` |
| `goal-reviewer` | Checks the story against its acceptance criteria and the Definition of Done, re-running the commands. The only one who commits. | story status and `## Review <n>`, `metrics.json`, commit, `JOURNAL.md`, `inbox/` |

## Who works next

At each step the loop picks the first rule that applies (the scheduler of the `goal` package decides; `goal status` shows where things stand):

1. `REPLAN` exists, a message waits in `inbox/`, or a story is `blocked` → **lead**
2. a story is in `review` → **reviewer**
3. a story is in `rework`, or `ready` with its dependencies done → **dev** (rework first, then by priority)
4. a story is `draft` or `needs-refinement` → **refiner** on those stories
5. no open epic → **lead**; the first open epic has all its stories done → **lead**; stories wait on dependencies that will never be done → **lead**
6. otherwise → **refiner** on the first open epic

The lead is also called after every `GOAL_LEAD_EVERY` stories done (5), and when nothing changed for `GOAL_MAX_IDLE` steps (3). After twice that, the loop stops and asks for a human.

## Files

- `GOAL.md`: your goal and constraints. The lead adds the measurable success criterion and its status. Editing the goal or the constraints calls the lead. When the criterion is met, the lead creates `GOAL_REACHED` and the loop stops. Keep the `## Success criterion` heading as is.
- `PROJECT.md`: what the project is, its commands (setup, fast tests, measure), its rules, the language to write in. Every agent reads it first.
- `ROADMAP.md`: the epics (`### E1 · Title` + `- status: open|in-progress|done|dropped`), and the decisions.
- `stories/S-<n>.md`: one user story per file, front matter + sections, see `stories/_TEMPLATE.md`. Its history (dev notes, reviews) stays in the file, so the dev reads only its story.
- `DOR.md` / `DOD.md`: Definition of Ready (checked by the refiner) and Definition of Done (checked by the reviewer). Add your project's rules at the end.
- `TODO.md`: index of the stories, **generated** by `goal run`, not versioned. Do not edit it.
- `JOURNAL.md`: shared journal, append only. Format: `## YYYY-MM-DD HH:MM · <agent> · <subject>` then a few factual bullets.
- `inbox/`: one file per message (`YYYYMMDD-HHMM-<author>-<subject>.md`). Anyone (you included) can propose something; the lead processes it and moves it to `inbox/done/`.
- `metrics.json`: measurements recorded by the reviewer, the only basis for "goal reached".
- `config.json`: model, effort and fallback model of each agent (editable from the monitor).
- `usage.jsonl`: one line per agent call (tokens, duration, estimated cost), not versioned. `logs/`: one log per call.
- `REPLAN` (call the lead at the next step), `STOP` (stop after the current step), `GOAL_REACHED`: flag files.

## Life of a story

```
draft ──(refiner)──► ready ──(loop)──► in-progress ──(dev)──► review ──(reviewer)──► done + commit
  ▲                    ▲                    │                   │
  │                    │                    │                   └──► rework + "## Review n" ──► (dev again)
  └── needs-refinement ◄────────────────────┘
blocked (too many attempts) ──(lead)──► draft (rethink, split) or dropped
```

The loop sets `in-progress` and counts the attempt when it hands a story to the dev. After `GOAL_MAX_ATTEMPTS` (3) the story becomes `blocked` and goes to the lead. A call that is interrupted or fails releases its story without counting the attempt.

## Rules for everyone

- Nothing counts as done without the reviewer, and no goal is reached without a measurement.
- Small steps: one story per dev call, one decision per change.
- Never `git push`, `git reset --hard`, rewrite history, `rm -rf` or `sudo`.
- Date journal entries with `date '+%Y-%m-%d %H:%M'`.
