# Resources

What the agents can use, and the limits of each resource. To get more (a resource, an integration, a tool, money),
write a proposal card (`HUMAN.md`): the evidence, the cost and the prepared steps. The default budget is free
services only (travel-aggregator, 2026-11-06; kept for the fleet until the owner changes it).

| Resource | What it is | Limits |
|---|---|---|
| Claude subscription | One account for all projects, with a 5-hour and a 7-day usage window. The lanes: Haiku (small tickets), main (Opus at low effort), deep (Opus at high effort). | The 7-day window is the real limit. 10 % of the week stays free for the owner (`week_reserve` in `fleet.toml`). |
| GitHub organization `lars-his-projects` | The hub and the projects. A public repository has free Actions minutes, Pages and packages (`ghcr.io`). | A private repository has a limited number of Actions minutes, and Pages needs a paid plan there. No secret goes into git. |
| polopc | The owner's desktop computer with Linux: 12 cores, 32 GB of memory, an NVIDIA GPU with 8 GB. It is on all day. For local runs, a real browser, the real Minecraft client, Minecraft servers, Docker builds and GPU jobs. | Not set up yet (roadmap `workers:polopc`). An agent gets a user of its own and containers. It gets no access to the owner's files, keys or main browser profile. The pacer gives it work only while it is online. |
| Home server | It runs the previews of travel-aggregator and tumach-dance, and the live sites. | No agent gets a shell (S10). Previews: the preview operator (roadmap `setup:preview-operator`). Live sites: the owner, by hand, with the kit of the project (roadmap `setup:live-kit`). |
| Addresses | `larspolo.nl` (the preview of travel-aggregator) and `tumach.dance`. Cloudflare tunnels connect the server. | The owner changes DNS. |
| Services | Mailgun (e-mail of tumach-dance) and ntfy (messages of travel-aggregator), on free plans. | The keys are on the server only. |
| Real travel sites | An agent can use them in a browser profile of its own on polopc (the owners Lars and Jeroen, 2026-11-13). | Only as a person does: one search at a time. No request from CI and no request from a cloud session. |

## What is never a resource

- A shell on a server of the owner, the owner's personal browser profile, and the owner's personal GitHub repositories.
- The data of a person who uses a product (a dancer, a traveller). It stays on the server of the product.
- A paid service or a second subscription with no approved proposal card.
