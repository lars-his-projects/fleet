---
name: verify
description: Verify a change to street-quiz before commit. Selects the check level (lint and fast tests, the build, a look at the page) from the type of change. Use before each commit and when a ticket says "verify".
---

# Verify a change

Do the levels from cheap to expensive that the change needs. Write the result of each check in the PR body.

## Level 1: lint and fast tests (each change)

    ruff check . && npx @biomejs/biome check .
    python3 -m pytest -q && npx vitest run

Both must pass before the commit. `npx @biomejs/biome check --write .` fixes the format. A change of the logic (`src/`)
gets a Vitest test in `tests/`. Tests use stored data: they never call a map or data service (P3).

## Level 2: the build (a change of a page, a dependency or the configuration)

    npm run build

The build also checks the types and makes `dist/`. Never commit `dist/`.

## Level 3: browser tests (a change of a page or a flow)

    npx playwright test

No browser test exists yet. The first ticket that needs one adds `@playwright/test` and `playwright.config.ts`, and
puts the command into `slow` of `agent.toml`.

## Level 4: images in the PR (each change that a user sees)

1. Make screenshots of each changed page with Playwright: a phone (390×844) and a laptop (1280×800).
2. Look at each image with the Read tool: the map has no street names during a quiz (P2), and no text runs out of its box.
3. The GitHub API cannot upload images. Push them as an orphan commit (`git mktree`, `git commit-tree`) to
   `refs/heads/checks/N` (N = the ticket) and link `https://raw.githubusercontent.com/OWNER/NAME/checks/N/FILE.png`
   (`repo` of `agent.toml`) in the PR body. Never commit images to `main`.
