# The image of the fleet worker on polopc: a GitHub Actions self-hosted runner with a real browser.
# The workflow worker-image.yml builds it and pushes ghcr.io/lars-his-projects/fleet-worker:latest.
# The base image has the runner in /home/runner (config.sh, run.sh) and the user `runner` (uid 1001).
FROM ghcr.io/actions/actions-runner:latest

LABEL org.opencontainers.image.source=https://github.com/lars-his-projects/fleet
LABEL org.opencontainers.image.description="The fleet worker: a GitHub Actions runner with Chromium"

USER root

# The tools of a job. Xvfb gives a display to a browser that is not headless (`xvfb-run`).
# libatomic1: the Node.js binary below needs it (the first build failed with no libatomic.so.1).
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends git curl jq unzip ca-certificates \
       python3 python3-pip python3-venv xvfb xauth libatomic1 \
    && rm -rf /var/lib/apt/lists/*

# The GitHub CLI from the official apt source of GitHub (a signed package, no install script). The skills use `gh api`.
# The run gives it the token of the job as GH_TOKEN (worker-run.yml).
RUN mkdir -p -m 755 /etc/apt/keyrings \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
       > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/* \
    && gh --version

# Node.js LTS from the official Node image: no install script from the internet.
COPY --from=node:lts-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:lts-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -sf ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
    && node --version && npm --version

# Playwright with Chromium and its system libraries. The browsers are in /ms-playwright for all users.
# A job that needs another Playwright version installs its own browser into this directory.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN python3 -m venv /opt/playwright \
    && /opt/playwright/bin/pip install --no-cache-dir playwright \
    && /opt/playwright/bin/playwright install --with-deps chromium \
    && chown -R runner:runner /ms-playwright \
    && rm -rf /var/lib/apt/lists/*

# The Claude Code CLI. The image rebuild updates it, so the CLI does not update itself.
ENV DISABLE_AUTOUPDATER=1
RUN npm install -g @anthropic-ai/claude-code && claude --version

# The base image gives `runner` sudo with no password. Remove it: a job gets no root.
RUN gpasswd -d runner sudo

# The browser profiles of the agents. Compose mounts a named volume here.
RUN mkdir -p /home/runner/profiles /home/runner/tools && chown runner:runner /home/runner/profiles /home/runner/tools
ENV BROWSER_PROFILES=/home/runner/profiles
# Heavy tools that a job installs one time (the Android SDK for a phone emulator). Compose mounts a volume here.
ENV WORKER_TOOLS=/home/runner/tools

# Root owns the start script, outside the home directory, so a job cannot change it.
COPY --chmod=755 entrypoint.sh /usr/local/bin/worker-entrypoint

USER runner
WORKDIR /home/runner
ENTRYPOINT ["/usr/local/bin/worker-entrypoint"]
