# street-quiz – guide for Claude Code

street-quiz is a web app to learn the street names of an area. It shows a real map with no street names, marks a
street and asks its name, or gives a name and asks you to tap the street. The data is OpenStreetMap.

The owner is **Larspolo**. The users are the owner and friends, on a phone first and also on a computer. There is no
account. The agent system: `framework/docs/SYSTEM.md`. The project values: `agent.toml`. The direction:
`steering/project/PRINCIPLES.md`. Write all text in ASD-STE100 Simplified Technical English (short sentences, active
voice, imperative).

## Commands

| Task | Command |
|---|---|
| Install | `python3 -m pip install -r requirements-dev.txt && npm ci` |
| Lint | `ruff check . && npx @biomejs/biome check .` (`--write` fixes the format) |
| Fast tests | `python3 -m pytest -q && npx vitest run` (one file: `npx vitest run tests/a.test.ts`) |
| Build | `npm run build` (checks the types, then makes `dist/`) |
| Development server | `npm run dev` |
| Slow tests | None yet: the first feature that needs a browser test adds Playwright |

Put scratch output in the scratchpad or in `out/`. Never commit `dist/` or `node_modules/`.

## Code map

A static web app: TypeScript and Vite, with MapLibre GL JS for the map. There is no server and no database. Keep this
map up to date.

- `index.html`, `src/main.ts` – the page and its entry point. `vite.config.ts` sets `base: "/street-quiz/"`: the app is
  served from https://lars-his-projects.github.io/street-quiz/.
- `src/` – the logic and the map code. `src/normalize.ts` compares street names (lower case, no accents, trimmed).
- `tests/` – Vitest tests (`*.test.ts`) and pytest tests of the agent tools. A pytest file name must not repeat a name in `framework/tests/`.
- `framework/`, `.claude/`, `steering/` – the agent system.

## Rules of the domain

- **P1, a flashcard, not a trivia game:** the quiz asks only for the name of a marked street or the street of a given
  name. It never asks about history or facts (`steering/project/PRINCIPLES.md`).
- **P3, open data and free services:** no code sends a request to a map or data service from CI or from a cloud
  session. Tests use stored data. Keep the data on the device.

@framework/CLAUDE.md
@docs/LEARNINGS.md
