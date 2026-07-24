---
campaign: v0.1.0-bootstrapping
created_by: John Hoff
created_on: '2026-07-24T05:08:55Z'
name: fix-cli-utf8-output-encoding
regions:
- crypts-and-commits
status: completed
updated_by: John Hoff
updated_on: '2026-07-24T05:20:17Z'
---

# Force UTF-8 Output Encoding in the CLI

## Requirements

The `cac` CLI must correctly emit non-ASCII/Unicode characters (arrows, em/en
dashes, smart quotes, etc.) on every platform, including Windows, without the
user or agent having to set `PYTHONIOENCODING=utf-8` (or any other external
environment variable) first.

- Content stored in `.sourcebook` bodies (encounters, lore, world, regions)
  routinely contains such characters. Any command that prints a stored body
  must display it, not crash.
- Today, on Windows, `cac encounter get` -- and any command that prints stored
  content through a `rich` `Console` -- raises
  `UnicodeEncodeError: 'charmap' codec can't encode character '→'` because
  the process stdout is cp1252. The only current workaround is prefixing the
  invocation with `PYTHONIOENCODING=utf-8`, which is a fragile per-call band-aid,
  not a fix.

## Rationale

We cannot realistically keep Unicode out of authored content -- an agent writing
bodies will naturally produce arrows, dashes, and smart quotes -- so the fix has
to live in the CLI, which owns its own output streams.

`rich` writes through the interpreter's stdout/stderr, whose encoding on Windows
defaults to the legacy code page (cp1252). Characters outside that code page
(e.g. U+2192 RIGHT ARROW) raise `UnicodeEncodeError`. The correct, durable fix
is for the CLI to guarantee UTF-8 on its own output streams at startup, so
correct display never depends on the caller's environment.

## Plan

*(Approach recommended below; final mechanism to be confirmed during
implementation.)*

- Force UTF-8 on the CLI's `stdout`/`stderr` at process entry, before any output
  is produced. Recommended mechanism: reconfigure the streams to
  `encoding="utf-8"` (with a safe `errors` fallback) in the console-script
  entrypoint / the root Typer callback in `cli/app.py`, so it runs once for every
  subcommand.
- Centralize the fix. All six CLI modules currently construct their own
  `Console()`; whatever solution is chosen must cover all of them without
  per-module drift. Prefer a single shared setup (e.g. in `cli/common.py` or a
  small `cli` startup hook) over editing each module.
- Guard the reconfigure so it is a safe no-op on streams that do not support it
  (e.g. `hasattr(stream, "reconfigure")`): test-capture buffers and some
  redirected streams are not `TextIOWrapper`s and must not raise. Apply a safe
  `errors` fallback (e.g. `backslashreplace`) rather than crashing on any
  stray un-encodable input.
- Confirm the fix holds across the relevant cases: a real Windows terminal,
  redirected/piped output on Windows, and POSIX platforms (must not regress).
- Keep `core` untouched -- this is a CLI presentation concern; per the
  architecture rule, no domain logic changes.

## Verification

- On Windows, with **no** `PYTHONIOENCODING` set, `cac encounter get <name>` on
  an encounter whose body contains a non-cp1252 character (e.g. a U+2192 arrow)
  prints the body correctly with no `UnicodeEncodeError`.
- A regression test asserts that printing a body containing a non-cp1252
  character succeeds without any external encoding environment variable.
  Note: the test must genuinely reproduce the failure mode -- a default
  `CliRunner` capture buffer is UTF-8 and would pass even with the bug present,
  so the test must exercise the code against a cp1252-encoded stream/`Console`
  (or otherwise assert the entrypoint reconfigures the streams to UTF-8), not
  merely capture default output.
- `pdm run pytest -q` passes and `pdm run ruff check .` / `ruff format .` are
  clean (per `clean-tests-and-lint`).

## Log

### Review - 2026-07-24T05:11:36Z - John Hoff

Lore review complete. Applicable lore: clean-tests-and-lint (world) and console-best-practices (region crypts-and-commits, applies after region assignment). Findings: (1) Verification already satisfies clean-tests-and-lint. (2) Fix changes output encoding, not markup, and adds no stored-content prints, so it does not conflict with console-best-practices; it keeps core untouched per the thin-CLI architecture rule. (3) Folded in two refinements before locking: guard the stream reconfigure with a capability check so it is a safe no-op under test-capture/redirected streams, and require the regression test to reproduce the cp1252 failure mode rather than rely on a UTF-8 CliRunner buffer. No blockers.

### Opened - 2026-07-24T05:11:43Z - John Hoff

Approved to proceed (user: 'You may proceed'). Sequenced first because it unblocks clean cac ... get output that later encounters depend on.

### Completed - 2026-07-24T05:20:17Z - John Hoff

Verification passed. cac encounter get renders U+2192 with no PYTHONIOENCODING and exit 0 (redirected and direct). Implemented configure_output_encoding() in cli/common.py (reconfigures stdout/stderr to UTF-8, errors=backslashreplace, guarded by a reconfigure capability check), wired into the root Typer callback in cli/app.py; no core changes. Added tests/cli/test_common.py reproducing the cp1252 failure mode plus a no-op-guard test, and a callback-wiring test in test_app.py. Full suite: 351 passed; ruff check and format clean.
