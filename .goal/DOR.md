# Definition of Ready

A story may be set to `ready` only when all of these hold. The refiner checks them; the dev sends the story back with `needs-refinement` if one does not.

- **Goal**: the story says in one sentence what changes for a user or a developer, and why (which epic it serves).
- **Acceptance criteria**: a short list of checks a reviewer can verify without guessing (behaviour, inputs and expected outputs, error cases).
- **Verify**: the exact commands that prove the criteria (tests to run or add, a script, a manual command with its expected output).
- **Scope**: the files or modules most likely to change, and what is explicitly out of scope.
- **Dependencies**: listed in `depends:`; the story is only picked once they are done.
- **Size**: S or M, doable in one dev session (about 30 minutes of focused work). An L story must be split.
- **No open question**: anything unclear is answered in the story, or the story stays `draft` with the question written in it.

Projects can add their own rules below.
