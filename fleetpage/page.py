"""The HTML of the fleet page from the model of `model.build()`: one file, no script and no font from another host.

Each text that comes from GitHub (a title, a name, an error) goes through `html.escape`: an issue title is input from outside.
"""
import datetime
import html
import json

from fleetpage.model import LIMIT, ts

E = html.escape
HUES = 8                        # the project colors --p0 ... --p7; a later project gets the neutral color
KIND_NAMES = {"decision": "Decision", "check": "Check", "epic": "Epic", "bug": "Bug", "question": "Question"}
LANE_NAMES = {"haiku": "Haiku", "sonnet": "Sonnet", "opus": "Opus", "fable": "Fable", "deep": "Deep (old lane)"}
W, H, L, R, T, B = 320, 200, 30, 8, 10, 24          # the weekly curve: size and margins of the drawing
PW, PH = W - L - R, H - T - B

CSS = """
:root { color-scheme: light dark;
  --plane: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e; --muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7; --ring: rgba(11,11,11,.12); --wash: rgba(11,11,11,.045);
  --p0: #2a78d6; --p1: #eb6834; --p2: #1baf7a; --p3: #eda100; --p4: #e87ba4; --p5: #008300; --p6: #6250d6; --p7: #e34948;
  --good: #0ca30c; --warn: #fab219; --crit: #d03b3b; --tip-bg: #0b0b0b; --tip-fg: #fcfcfb;
  --text: system-ui, -apple-system, "Segoe UI", sans-serif; --mono: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace; }
@media (prefers-color-scheme: dark) { :root {
  --plane: #0d0d0d; --surface: #1a1a19; --ink: #f0efec; --ink-2: #c3c2b7; --muted: #898781;
  --grid: #2c2c2a; --axis: #383835; --ring: rgba(255,255,255,.12); --wash: rgba(255,255,255,.05);
  --p0: #3987e5; --p1: #d95926; --p2: #199e70; --p3: #c98500; --p4: #d55181; --p5: #008300; --p6: #9085e9; --p7: #e66767;
  --tip-bg: #f0efec; --tip-fg: #0d0d0d; } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--plane); color: var(--ink); font: 400 16px/1.55 var(--text); }
.sheet { max-width: 1080px; margin: 0 auto; padding: 28px 16px 64px; display: flex; flex-direction: column; gap: 48px; }
a { color: inherit; text-decoration: underline; text-decoration-thickness: 1px; text-underline-offset: 3px; }
a:hover { text-decoration-thickness: 2px; }
a:focus-visible, summary:focus-visible, .seg:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }
code { font: 500 .88em var(--mono); background: var(--wash); padding: 1px 4px; border-radius: 3px; overflow-wrap: anywhere; }
p { margin: 0; }
h1 { font: 650 clamp(30px, 5vw, 42px)/1.08 var(--text); margin: 0; letter-spacing: -.01em; }
h2 { font: 650 26px/1.15 var(--text); margin: 0; }
h3 { font: 650 19px/1.2 var(--text); margin: 0; }
h4 { font: 600 15px/1.3 var(--text); margin: 0; }
.mast { display: flex; flex-direction: column; gap: 14px; border-top: 3px solid var(--ink); padding-top: 14px; }
.eyebrow { font: 500 12px/1.4 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--ink-2); }
.lead { color: var(--ink-2); max-width: 70ch; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 18px 22px; }
.tile { border-top: 1px solid var(--ink); padding-top: 9px; display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.tile .v { font: 650 32px/1.05 var(--text); white-space: nowrap; }
.tile .l { font-weight: 600; font-size: 14.5px; }
.tile .s { font-size: 13px; color: var(--ink-2); }
section { display: flex; flex-direction: column; gap: 18px; min-width: 0; }
.sec { border-top: 1px solid var(--ink); padding-top: 10px; }
.caution { border: 1.5px solid var(--ink); padding: 12px 14px; display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 4px 14px; max-width: 860px; }
.note { border-top: 1px solid var(--axis); padding-top: 8px; display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 4px 14px; max-width: 860px; color: var(--ink-2); font-size: 14.5px; }
.tag { font: 600 12px/1.9 var(--mono); letter-spacing: .1em; white-space: nowrap; }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; vertical-align: 1px; }
.d-warn { background: var(--warn); } .d-crit { background: var(--crit); } .d-good { background: var(--good); }
.key { width: 11px; height: 11px; border-radius: 2px; flex: none; display: inline-block; margin-right: 7px; vertical-align: -1px; }
.pill { font: 500 11px/1.6 var(--mono); letter-spacing: .05em; text-transform: uppercase; border: 1px solid var(--axis); border-radius: 999px; padding: 0 8px; color: var(--ink-2); white-space: nowrap; }
.tw { overflow-x: auto; min-width: 0; }
table { border-collapse: collapse; width: 100%; font-size: 14.5px; }
th { font: 500 11.5px/1.4 var(--mono); letter-spacing: .06em; text-transform: uppercase; text-align: left; color: var(--ink-2); border-bottom: 1px solid var(--ink); padding: 8px 10px; vertical-align: bottom; }
td { border-bottom: 1px solid var(--grid); padding: 9px 10px; vertical-align: top; }
td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
td.n { font: 400 13.5px/1.6 var(--mono); }
.s { color: var(--ink-2); font-size: 13px; }
td.nw { white-space: nowrap; }
table.now { min-width: 860px; }
tr.sum td { font-weight: 600; border-bottom: 0; border-top: 1px solid var(--ink); }
table.wide { min-width: 720px; }
.meter { display: inline-block; width: 52px; height: 6px; border-radius: 3px; background: var(--grid); vertical-align: middle; margin-left: 8px; overflow: hidden; }
.meter i { display: block; height: 100%; background: var(--ink-2); border-radius: 3px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 16px; align-items: start; }
.card, .fig { background: var(--surface); border: 1px solid var(--ring); border-radius: 6px; padding: 16px; display: flex; flex-direction: column; gap: 12px; min-width: 0; }
.card .row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.card .what { font-size: 14px; color: var(--ink-2); }
.total { display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
.total .v { font: 650 25px/1 var(--text); white-space: nowrap; }
.total .l { font-size: 13.5px; color: var(--ink-2); }
.goals { display: flex; flex-direction: column; gap: 8px; }
.goal { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 3px 10px; font-size: 13.5px; }
.goal .c { font: 500 12.5px var(--mono); color: var(--ink-2); }
.bar { grid-column: 1 / -1; height: 8px; border-radius: 4px; background: var(--grid); overflow: hidden; }
.bar i { display: block; height: 100%; border-radius: 4px; }
.links { display: flex; gap: 14px; flex-wrap: wrap; font-size: 13.5px; }
.fig p.sub { font-size: 14px; color: var(--ink-2); max-width: 76ch; }
.panels { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 18px 22px; }
.panel { position: relative; display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.panel .big { font: 650 24px/1.1 var(--text); }
.panel .cap { font-size: 13px; color: var(--ink-2); min-height: 2.9em; }
.panel svg { width: 100%; height: auto; display: block; color: var(--ink); touch-action: pan-y; }
.gl { stroke: var(--grid); stroke-width: 1; } .bl { stroke: var(--axis); stroke-width: 1; }
.pace { stroke: var(--axis); stroke-width: 1; fill: none; } .rsv { stroke: var(--muted); stroke-width: 1; fill: none; }
.ln { stroke: currentColor; stroke-width: 2; fill: none; stroke-linejoin: round; stroke-linecap: round; }
.ar { fill: currentColor; fill-opacity: .08; stroke: none; }
.mk { fill: currentColor; stroke: var(--surface); stroke-width: 2; }
.ax { fill: var(--muted); font: 10px var(--mono); }
.hv { stroke: var(--ink-2); stroke-width: 1; }
.tip { position: absolute; z-index: 2; background: var(--tip-bg); color: var(--tip-fg); font: 500 12px/1.3 var(--mono); padding: 4px 8px; border-radius: 4px; pointer-events: none; white-space: nowrap; transform: translate(-50%, -130%); }
[hidden] { display: none !important; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 13.5px; color: var(--ink-2); }
.legend span { display: inline-flex; align-items: center; }
.lk { width: 18px; height: 0; border-top: 2px solid var(--ink); display: inline-block; margin-right: 7px; }
.lk.p { border-top: 1px solid var(--axis); } .lk.r { border-top: 1px solid var(--muted); }
.segs { display: flex; flex-direction: column; gap: 12px; }
.seg-row { display: grid; grid-template-columns: 110px minmax(0, 1fr) auto; gap: 6px 12px; align-items: center; font-size: 13.5px; }
.seg-row .t { text-align: right; font: 500 12.5px var(--mono); white-space: nowrap; }
.seg-bar { display: flex; gap: 2px; height: 28px; min-width: 0; }
.seg { border-radius: 4px; display: flex; align-items: center; padding: 0 8px; color: #fff; font: 600 12.5px var(--text); min-width: 0; white-space: nowrap; overflow: hidden; }
.seg.dark { color: #0b0b0b; }
@media (max-width: 560px) { .seg-row { grid-template-columns: minmax(0, 1fr) auto; } .seg-bar { grid-column: 1 / -1; grid-row: 2; }
  .caution, .note { grid-template-columns: minmax(0, 1fr); } }
details summary { cursor: pointer; font: 500 12px var(--mono); letter-spacing: .04em; color: var(--ink-2); width: fit-content; }
details[open] summary { margin-bottom: 10px; }
.prose { max-width: 72ch; display: flex; flex-direction: column; gap: 10px; }
.method { font-size: 13.5px; color: var(--ink-2); border-top: 1px solid var(--ink); padding-top: 12px; display: flex; flex-direction: column; gap: 6px; max-width: 88ch; }
"""

SCRIPT = """
(function () {
  var DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  document.querySelectorAll(".panel").forEach(function (panel) {
    var svg = panel.querySelector("svg"), tip = panel.querySelector(".tip");
    if (!svg || !tip) return;
    var pts = JSON.parse(svg.getAttribute("data-pts")), start = Date.parse(svg.getAttribute("data-start"));
    var g = JSON.parse(svg.getAttribute("data-geo")), line = svg.querySelector(".hv"), dot = svg.querySelector(".hd");
    function show(clientX) {
      var r = svg.getBoundingClientRect(), x = (clientX - r.left) / r.width * g.w;
      var h = Math.max(0, Math.min(168, (x - g.l) / g.pw * 168)), best = pts[0];
      for (var i = 0; i < pts.length; i++) if (Math.abs(pts[i][0] - h) < Math.abs(best[0] - h)) best = pts[i];
      var px = g.l + g.pw * best[0] / 168, py = g.t + g.ph * (1 - best[1]);
      line.setAttribute("x1", px); line.setAttribute("x2", px); line.removeAttribute("visibility");
      dot.setAttribute("cx", px); dot.setAttribute("cy", py); dot.removeAttribute("visibility");
      var d = new Date(start + best[0] * 3600000);
      tip.textContent = DAYS[d.getUTCDay()] + " " + ("0" + d.getUTCHours()).slice(-2) + ":00 UTC \\u00b7 " + Math.round(best[1] * 100) + " %";
      tip.style.left = (svg.offsetLeft + px / g.w * r.width) + "px";
      tip.style.top = (svg.offsetTop + py / g.h * r.height) + "px";
      tip.hidden = false;
    }
    function hide() { tip.hidden = true; line.setAttribute("visibility", "hidden"); dot.setAttribute("visibility", "hidden"); }
    svg.addEventListener("pointermove", function (e) { show(e.clientX); });
    svg.addEventListener("pointerdown", function (e) { show(e.clientX); });
    svg.addEventListener("pointerleave", hide);
  });
})();
"""


def pct(share):
    return f"{100 * share:.0f} %"


def usd(amount):
    return f"${amount:,.0f}"


def day(when):
    return f"{when:%a} {when.day} {when:%b}"


def stamp(when):
    return f"{day(when)}, {when:%H:%M} UTC"


def ago(minutes):
    """`12 min`, `3 h` or `8 days` for an age in minutes."""
    if minutes is None:
        return "–"
    if minutes < 90:
        return f"{max(0, round(minutes))} min"
    if minutes < 48 * 60:
        return f"{minutes / 60:.0f} h"
    return f"{minutes / 1440:.0f} days"


def hue(index):
    return f"var(--p{index})" if index < HUES else "var(--muted)"


def key(index):
    return f'<i class="key" style="background:{hue(index)}"></i>'


def tiles(m):
    q, t = m["quota"], m["totals"]
    out = []
    if q:
        ahead = q["seven_day"]["used"] - q["pace"]
        state = ("d-warn", "ahead of an even pace") if ahead > 0.05 else ("d-good", "on or below an even pace")
        out.append(("Weekly quota used", pct(q["seven_day"]["used"]),
                    f'<span class="dot {state[0]}"></span>{state[1]} ({pct(q["pace"])}). Reset: {stamp(ts(q["seven_day"]["resets"]))}.'))
        out.append(("5-hour window used", pct(q["five_hour"]["used"]), f'Reset: {stamp(ts(q["five_hour"]["resets"]))}.'))
    else:
        out.append(("Weekly quota used", "–", "No pacer record."))
    out.append(("Runs at work", str(t["claims"]), f'Ready tickets: {t["ready"]}.'))
    out.append(("Tickets that wait for a person", str(t["waiting"]), f'Merged PRs in 7 days: {t["prs_7d"]:,}.'))
    share = f' ({pct(t["done"] / t["total"])})' if t["total"] else ""
    out.append(("Roadmap features done", f'{t["done"]} / {t["total"]}', f'In {len(m["projects"])} projects{share}.'))
    return '<div class="tiles">' + "".join(
        f'<div class="tile"><div class="v">{E(v)}</div><div class="l">{E(label)}</div><div class="s">{s}</div></div>'
        for label, v, s in out) + "</div>"


def alerts(m):
    out = []
    q = m["quota"]
    if q and q["age_minutes"] > 45:
        out.append(f'<div class="caution"><div class="tag">CAUTION</div><p>The newest pacer record is {E(ago(q["age_minutes"]))} old. '
                   "Look at the workflow Pacer of the projects.</p></div>")
    lines = [f'{E(p["name"])}: {E(text)}' for p in m["projects"] for text in p["errors"]]
    lines += [f'{E(p["name"])}: pacer problem: {E(str(x))}' for p in m["projects"] for x in (p["pacer"] or {}).get("problems", [])]
    if lines:
        out.append('<div class="note"><div class="tag">NOTE</div><p>' + "<br>".join(lines) + "</p></div>")
    return "".join(out)


def now_table(m, now):
    rows = []
    for i, p in enumerate(m["projects"]):
        pc = p["pacer"]
        last = "–"
        if p["last_report"]:
            when = ts(p["last_report"])
            last = f'{E(ago((now - when).total_seconds() / 60))} ago<br><span class="s">{E(stamp(when))}</span>'
        if pc:
            state = "paused" if pc["paused"] else f'target {pc["target"]}'
            pacer = f'{E(state)}<br><span class="s">record {E(ago(pc["age_minutes"]))} old</span>'
            idle = "–" if pc["idle_week"] is None else pct(pc["idle_week"])
            claims, ready = pc["claims"], pc["ready"]
        else:
            pacer, idle, claims, ready = "no record", "–", "–", "–"
        wait = "?" if p["waiting"] is None else len(p["waiting"])
        rows.append(
            f'<tr><td>{key(i)}<b>{E(p["name"])}</b> <span class="pill">{E(p["stage"])}</span></td>'
            f'<td class="n">{pct(p["share"])}</td><td class="n">{claims}</td><td class="n">{ready}</td><td class="n">{wait}</td>'
            f'<td class="n">{p["reports_24h"]}</td><td class="nw">{last}</td><td class="nw">{pacer}</td><td class="n">{idle}</td></tr>')
    return ('<div class="tw"><table class="now"><thead><tr><th>Project</th><th class="n">Share</th><th class="n">At work</th>'
            '<th class="n">Ready</th><th class="n">Waiting</th><th class="n">Reports, 24 h</th><th>Last report</th>'
            '<th>Pacer</th><th class="n">No work</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>"
            '<p class="s">Share: the part of the quota that the weight of the project gives. At work: runs with a claim. Ready: tickets that a run '
            "can take. Waiting: tickets that wait for a person. No work: the pacer cycles of this quota week with no ready ticket and no claim.</p>")


def working(m):
    rows, failed = [], []
    for i, p in enumerate(m["projects"]):
        if p.get("working") is None:
            failed.append(p["name"])
            continue
        for t in p["working"]:
            rows.append(f'<tr><td>{key(i)}{E(p["name"])}</td><td><a href="{E(t["url"])}">#{t["number"]}</a> {E(t["title"])}</td>'
                        f'<td class="n">{E(ago(t["minutes"]))}</td></tr>')
    note = f'<p class="sub">Not read: {E(", ".join(failed))}.</p>' if failed else ""
    if not rows:
        return note + "<p>No run is at work.</p>"
    return (note + '<div class="tw"><table class="wide"><thead><tr><th>Project</th><th>Ticket</th>'
            '<th class="n">Last change</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")


def inbox(m):
    rows, failed = [], []
    for i, p in enumerate(m["projects"]):
        if p["waiting"] is None:
            failed.append(p["name"])
            continue
        for t in p["waiting"]:
            who = ", ".join(t["for"]) or "–"
            days = "–" if t["days"] is None else (f'{t["days"]:.0f} d' if t["days"] >= 1 else "today")
            rows.append(f'<tr><td>{key(i)}{E(p["name"])}</td><td><a href="{E(t["url"])}">#{t["number"]}</a> {E(t["title"])}</td>'
                        f'<td>{E(KIND_NAMES.get(t["kind"], t["kind"]))}</td><td>{E(who)}</td><td class="n">{days}</td></tr>')
    note = f'<p class="sub">Not read: {E(", ".join(failed))}.</p>' if failed else ""
    if not rows:
        return note + "<p>No ticket waits for a person.</p>"
    return (note + '<div class="tw"><table class="wide"><thead><tr><th>Project</th><th>Ticket</th><th>Kind</th><th>For</th>'
            '<th class="n">Waits</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")


def progress(m):
    cards = []
    for i, p in enumerate(m["projects"]):
        if p["goals"] is None:
            body = '<p class="what">The roadmap file was not read.</p>'
        elif not p["total"]:
            body = '<p class="what">The roadmap has no feature line.</p>'
        else:
            goals = "".join(
                f'<div class="goal"><span>{E(g["title"])}</span><span class="c">{g["done"]} / {g["total"]}</span>'
                f'<div class="bar"><i style="width:{100 * g["done"] / max(g["total"], 1):.1f}%;background:{hue(i)}"></i></div></div>'
                for g in p["goals"])
            body = (f'<div class="total"><span class="v">{p["done"]} / {p["total"]}</span>'
                    f'<span class="l">roadmap features done ({pct(p["done"] / p["total"])})</span></div><div class="goals">{goals}</div>')
        links = [("Repository", f'https://github.com/{p["repo"]}')] + [(k.capitalize(), v) for k, v in p["links"].items()]
        cards.append(f'<article class="card"><div class="row">{key(i)}<h3>{E(p["name"])}</h3><span class="pill">stage: {E(p["stage"])}</span></div>'
                     f'<p class="what">{E(p["what"])}</p>{body}<div class="links">'
                     + "".join(f'<a href="{E(u)}">{E(t)}</a>' for t, u in links) + "</div></article>")
    return '<div class="cards">' + "".join(cards) + "</div>"


def x_of(hour):
    return L + PW * hour / 168


def y_of(used):
    return T + PH * (1 - min(max(used, 0.0), 1.0))


def panel(week, quota, reserve):
    start = ts(week["start"])
    pts = week["points"]
    if week["current"]:
        title = "This week"
        used = quota["seven_day"]["used"] if quota else week["max"]
        cap = f'After {quota["week_hours"]:.0f} hours. An even pace is {pct(quota["pace"])}.' if quota else "The week is not complete."
        mark = pts[-1]
    else:
        title, used = f"Week of {start.day} {start:%b}", week["max"]
        if week["limit_hour"] is not None:
            at = start + datetime.timedelta(hours=week["limit_hour"])
            cap = (f"At {pct(LIMIT)} or more from {at:%a} {at:%H:%M} UTC, {168 - week['limit_hour']:.1f} hours before the reset.")
            mark = [week["limit_hour"], next((u for h, u in pts if h >= week["limit_hour"]), week["max"])]
        else:
            cap, mark = f"The week ended at {pct(week['max'])}.", pts[-1]
    path = "M" + " L".join(f"{x_of(h):.1f} {y_of(u):.1f}" for h, u in pts)
    area = path + f" L{x_of(pts[-1][0]):.1f} {y_of(0):.1f} L{x_of(0):.1f} {y_of(0):.1f} Z"
    grid = "".join(f'<line class="gl" x1="{L}" x2="{W - R}" y1="{y_of(v):.1f}" y2="{y_of(v):.1f}"/>' for v in (0.25, 0.5, 0.75, 1.0))
    ylab = "".join(f'<text class="ax" x="{L - 5}" y="{y_of(v) + 3.5:.1f}" text-anchor="end">{t}</text>' for v, t in ((0, "0"), (0.5, "50"), (1.0, "100")))
    xlab = "".join(
        f'<text class="ax" x="{x_of(24 * i):.1f}" y="{H - 7}" text-anchor="{"start" if i == 0 else "end" if i == 7 else "middle"}">'
        f'{(start + datetime.timedelta(days=i)):%a}</text>' for i in range(8))
    ticks = "".join(f'<line class="bl" x1="{x_of(24 * i):.1f}" x2="{x_of(24 * i):.1f}" y1="{y_of(0):.1f}" y2="{y_of(0) + 4:.1f}"/>' for i in range(8))
    rsv = (f'<line class="rsv" x1="{L}" x2="{W - R}" y1="{y_of(1 - reserve):.1f}" y2="{y_of(1 - reserve):.1f}"/>'
           if week["current"] and reserve > 0 else "")
    geo = json.dumps({"w": W, "h": H, "l": L, "t": T, "pw": PW, "ph": PH})
    svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{E(title)}: {E(pct(used))} of the weekly quota. {E(cap)}" '
           f"data-pts='{json.dumps(pts)}' data-start=\"{week['start']}\" data-geo='{geo}'>"
           f'{grid}<line class="bl" x1="{L}" x2="{W - R}" y1="{y_of(0):.1f}" y2="{y_of(0):.1f}"/>{ticks}{rsv}'
           f'<line class="pace" x1="{x_of(0):.1f}" y1="{y_of(0):.1f}" x2="{x_of(168):.1f}" y2="{y_of(1):.1f}"/>'
           f'<path class="ar" d="{area}"/><path class="ln" d="{path}"/>'
           f'<circle class="mk" cx="{x_of(mark[0]):.1f}" cy="{y_of(mark[1]):.1f}" r="4.5"/>'
           f'<line class="hv" x1="0" x2="0" y1="{T}" y2="{y_of(0):.1f}" visibility="hidden"/>'
           f'<circle class="mk hd" cx="0" cy="0" r="4" visibility="hidden"/>{ylab}{xlab}</svg>')
    return (f'<div class="panel"><h4>{E(title)}</h4><div class="big">{E(pct(used))}</div><p class="cap">{E(cap)}</p>{svg}'
            f'<div class="tip" hidden></div></div>')


def week_title(week):
    start = ts(week["start"])
    return "This week" if week["current"] else f"Week of {start.day} {start:%b}"


def budget_fig(m):
    b = m.get("budget")
    if not b or not m["quota"]:
        return ""
    used = pct(m["quota"]["seven_day"]["used"])
    if b["mode"] == "free":
        state = f"The week is at or behind an even pace ({used} used, the pace is {pct(b['pace'])}): the budget gives no limit now."
    else:
        state = (f"The week is ahead of an even pace ({used} used, the pace is {pct(b['pace'])}). The rest of the budget carries "
                 f"{b['rate']:.2f} runs to the reset: {b['slots']} in this cycle.")
    rows = []
    for i, p in enumerate(m["projects"]):
        r = b["projects"].get(p["name"])
        if not r:
            continue
        runs = "no limit" if r["runs"] is None else str(r["runs"])
        own = "–" if not p["pacer"] else str(p["pacer"]["target"])
        rows.append(f'<tr><td>{key(i)}{E(p["name"])}</td><td class="n">{pct(r["share"])}</td><td class="n">{pct(r["actual"])}</td>'
                    f'<td class="n">{runs}</td><td class="n">{own}</td></tr>')
    reserve = f" It keeps {pct(m['fleet']['week_reserve'])} of the week free for the owner." if m["fleet"]["week_reserve"] else ""
    return ('<div class="fig"><h3>The one budget (advice)</h3><p class="sub">What one pacer for the account gives each project in '
            f"this cycle.{reserve} No pacer follows it yet (roadmap <code>pacer:one</code>): each project still has its own pacer. "
            f"{E(state)}</p><div class=\"tw\"><table><thead><tr><th>Project</th><th class=\"n\">Share by weight</th>"
            '<th class="n">Share of the usage, this week</th><th class="n">Runs by the budget</th><th class="n">Target of its own pacer</th>'
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
            '<p class="s">Share by weight: among the projects that have work now. A project with no work gets 0 runs.</p></div>')


def usage(m):
    if not m["weeks"]:
        return "<p>No pacer record yet: the weekly curve needs the <code>metrics</code> branch of a project.</p>"
    reserve = m["fleet"]["week_reserve"]
    panels = "".join(panel(w, m["quota"], reserve) for w in m["weeks"])
    legend = '<span><i class="lk"></i>7-day usage</span><span><i class="lk p"></i>Even pace</span>'
    if reserve > 0:
        legend += f'<span><i class="lk r"></i>Reserve for the owner ({pct(reserve)}), this week</span>'
    index = {p["name"]: i for i, p in enumerate(m["projects"])}
    segs, rows = [], []
    for w in m["weeks"]:
        if not w["usd"]:
            continue
        bars, names = [], []
        for name, s in sorted(w["split"].items(), key=lambda kv: index.get(kv[0], 99)):
            share = s["usd"] / w["usd"]
            i = index.get(name, HUES)
            names.append(f"{name} {pct(share)}")
            dark = " dark" if i == 3 else ""       # the yellow color takes a dark label
            label = pct(share) if share >= 0.08 else ""
            bars.append(f'<div class="seg{dark}" tabindex="0" style="flex:{100 * share:.2f} 1 0;background:{hue(i)}" '
                        f'title="{E(name)}: {usd(s["usd"])}, {pct(share)}, {s["prs"]:.0f} PRs, {s["hours"]:.0f} run-hours">{label}</div>')
            rows.append(f'<tr><td>{E(week_title(w))}</td><td>{key(i)}{E(name)}</td><td class="n">{s["reports"]:,.0f}</td>'
                        f'<td class="n">{s["prs"]:,.0f}</td><td class="n">{usd(s["usd"])}</td><td class="n">{pct(share)}</td>'
                        f'<td class="n">{s["hours"]:,.0f}</td></tr>')
        segs.append(f'<div class="seg-row"><span>{E(week_title(w))}</span>'
                    f'<div class="seg-bar" role="img" aria-label="{E(week_title(w))}: {E(", ".join(names))}">{"".join(bars)}</div>'
                    f'<span class="t">{usd(w["usd"])} · {w["hours"]:,.0f} run-hours</span></div>')
    keys = "".join(f"<span>{key(i)}{E(p['name'])}</span>" for i, p in enumerate(m["projects"]))
    split = ""
    if segs:
        split = ('<div class="fig"><h3>The split of the usage between the projects</h3>'
                 '<p class="sub">Share of the measured usage in each quota week, at API prices. One run-hour is one hour of one run.</p>'
                 f'<div class="legend">{keys}</div><div class="segs">{"".join(segs)}</div>'
                 '<details><summary>Show the numbers</summary><div class="tw"><table><thead><tr><th>Quota week</th><th>Project</th>'
                 '<th class="n">Run reports</th><th class="n">PRs</th><th class="n">Usage</th><th class="n">Share</th><th class="n">Run-hours</th>'
                 f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div></details></div>')
    return ('<div class="fig"><h3>The weekly quota</h3><p class="sub">Usage of the 7-day window from one reset to the next. '
            f'The thin line is an even pace to 100 % at the reset.</p><div class="legend">{legend}</div><div class="panels">{panels}</div></div>'
            + budget_fig(m) + split)


def cost(m):
    lanes = m["lanes"]
    tot = {k: sum(lane[k] for lane in lanes) for k in ("reports", "prs", "usd", "nopr_usd")}
    if not tot["reports"]:
        return "<p>No run report yet.</p>"
    rows = []
    for lane in lanes:
        share_u = lane["usd"] / tot["usd"] if tot["usd"] else 0
        share_p = lane["prs"] / tot["prs"] if tot["prs"] else 0
        per = f'${lane["usd"] / lane["prs"]:.2f}' if lane["prs"] else "–"
        nopr = f'{usd(lane["nopr_usd"])} ({pct(lane["nopr_usd"] / lane["usd"])})' if lane["usd"] else "–"
        rows.append(
            f'<tr><td><b>{E(LANE_NAMES.get(lane["lane"], lane["lane"]))}</b></td><td class="n">{lane["reports"]:,.0f}</td>'
            f'<td class="n">{lane["prs"]:,.0f}<span class="meter" title="{pct(share_p)} of the PRs"><i style="width:{100 * share_p:.0f}%"></i></span></td>'
            f'<td class="n">{pct(share_p)}</td>'
            f'<td class="n">{usd(lane["usd"])}<span class="meter" title="{pct(share_u)} of the usage"><i style="width:{100 * share_u:.0f}%"></i></span></td>'
            f'<td class="n">{pct(share_u)}</td><td class="n">{per}</td><td class="n">{nopr}</td></tr>')
    per = f'${tot["usd"] / tot["prs"]:.2f}' if tot["prs"] else "–"
    nopr = f'{usd(tot["nopr_usd"])} ({pct(tot["nopr_usd"] / tot["usd"])})' if tot["usd"] else "–"
    rows.append(f'<tr class="sum"><td>All lanes</td><td class="n">{tot["reports"]:,.0f}</td><td class="n">{tot["prs"]:,.0f}</td>'
                f'<td class="n">100 %</td><td class="n">{usd(tot["usd"])}</td><td class="n">100 %</td><td class="n">{per}</td><td class="n">{nopr}</td></tr>')
    since = f" since {day(ts(m['lanes_since']))}" if m["lanes_since"] else ""
    return ('<div class="tw"><table class="wide"><thead><tr><th>Lane</th><th class="n">Run reports</th><th class="n">PRs</th>'
            '<th class="n">Share of PRs</th><th class="n">Usage</th><th class="n">Share of usage</th><th class="n">Usage per PR</th>'
            f'<th class="n">In reports with no PR</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
            f'<div class="prose"><p>The run reports{since}. Usage in USD is the price of the tokens at API prices, as each run report '
            "writes it. It is a measure of usage. You do not pay it.</p><p>A report with no PR is a queue refill, an epic check, a review, "
            "a repair or a cycle with no ticket. Not all of this is waste. It is the first place to look.</p></div>")


def workers(m):
    if not m.get("workers"):
        return "<p>Worker: no heartbeat.</p>"
    lines = []
    for w in m["workers"]:
        when = ts(w["last"])
        state = "online" if w["online"] else "offline"
        lines.append(f'<li><b>{E(w["name"])}</b>: {state}, last job {E(stamp(when))} ({E(ago(w["minutes"]))} ago)</li>')
    return "<ul>" + "".join(lines) + "</ul>"


def render(m):
    """The page as one HTML document."""
    now = ts(m["generated"])
    names = ", ".join(p["name"] for p in m["projects"]) or "no project"
    budget = m["fleet"]["attention_minutes"]
    body = f"""<div class="sheet">
<header class="mast">
  <div class="eyebrow">Fleet of {E(m["fleet"]["org"])} · built {E(stamp(now))}</div>
  <h1>Fleet</h1>
  <p class="lead">The projects that the agents work on: {E(names)}. The numbers come from the <code>metrics</code> branch, the roadmap and the open issues of each project.</p>
  {tiles(m)}
  {alerts(m)}
</header>
<section id="now"><div class="sec"><h2>Now</h2></div>{now_table(m, now)}
  <h3>Runs at work</h3>{working(m)}
  <h3>Worker</h3>{workers(m)}</section>
<section id="inbox"><div class="sec"><h2>Inbox</h2></div>
  <p class="lead">Each open ticket with the label <code>needs-human</code>. The attention budget is {budget} minutes per week. The tickets do not have a price in minutes yet.</p>
  {inbox(m)}</section>
<section id="progress"><div class="sec"><h2>Progress</h2></div>{progress(m)}</section>
<section id="usage"><div class="sec"><h2>Usage</h2></div>{usage(m)}</section>
<section id="cost"><div class="sec"><h2>Cost points</h2></div>{cost(m)}</section>
<footer class="method">
  <p><b>Method.</b> A workflow of the repository <code>fleet</code> builds this page with no Claude quota. The project list is <code>fleet.toml</code>.</p>
  <p>A PR is a ticket with the result "pr #N" in a run report. Run-hours add the wall minutes of each session. "No work" counts the pacer cycles with no ready ticket and no claim. Progress counts the feature lines of the roadmap file. The <code>metrics</code> branch of a project keeps 14 days.</p>
  <p>The same numbers as data: <a href="data.json">data.json</a>.</p>
</footer>
</div>"""
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta name="robots" content="noindex"><title>Fleet</title><style>' + CSS + "</style></head><body>" + body
            + "<script>" + SCRIPT + "</script></body></html>\n")
