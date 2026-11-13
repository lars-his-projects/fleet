import { defineConfig } from "vitest/config";

// Only tests/: the Playwright tests (when the first feature adds them) run with `npx playwright test`.
export default defineConfig({
  test: { include: ["tests/**/*.test.ts"] },
});
