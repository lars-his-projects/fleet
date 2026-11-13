---
name: verify
description: Verify a change to fleet before commit. Selects the check level from the type of change. Use before each commit and when a ticket says "verify".
---

# Verify a change

## Level 1: lint and tests (each change)

    ruff check .
    python3 -m pytest

Both must pass before the commit.

## Level 2: the fleet page (when `fleetpage/` changes)

Build the page with no network. The options are at the top of `fleetpage/build.py`:

    python3 -m fleetpage.build --out out/site --offline

Open `out/site/index.html` and look at it. Check that each project shows and that a fault shows as a line, not as a crash.
Never commit a built page.
