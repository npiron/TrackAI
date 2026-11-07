# Definition of Done

A story may be set to `done` (and committed) only when the reviewer has checked all of these themselves, without trusting the dev's notes.

- **Acceptance criteria**: every criterion of the story is met, checked by running the commands of its "Verify" section.
- **Tests**: the fast tests of `PROJECT.md` pass; new behaviour is covered by new or updated tests where the project has tests.
- **No regression**: nothing outside the story's scope is broken or changed without reason.
- **Clean change**: no debug leftovers, no secrets, no large generated or binary files, the project's style is kept.
- **Docs**: user-facing docs (README, help text, changelog if the project keeps one) are updated when the visible behaviour changes.
- **Measured**: if the story serves the success criterion, the measurement is recorded in `.goal/metrics.json`.
- **Committed**: one commit with a conventional message that names the story (`feat(S-12): ...`).

Projects can add their own rules below.
