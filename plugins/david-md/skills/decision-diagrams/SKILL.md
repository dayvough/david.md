---
name: decision-diagrams
description: Visualise any decision as a diagram of calm cards that lay themselves out: options and trade-offs, yes/no flows, plans, or a conversation as it unfolds. Use when asked to diagram, map, visualise or lay out a decision, choice or plan.
---

# Decision diagrams

Draw a decision as a published canvas of cards. Every card has the same calm anatomy: an icon,
a one-or-two-word name with a small subline, one coloured status pill, one sentence, and a
footer of facts. Colour lives only in the pill. Options that were ruled out stay on the diagram
in grey with their reason, so the diagram shows what was dropped and why, not just what won.

The page is fixed and designed. Your job is the content: choose a shape, write the `MAP` block,
drop it into the page below, show it. Never restyle the cards, add sections to them, or position
anything by hand; the layout engine (Pele) places every card and routes every line.

## What this skill contains

Everything it needs is in this file. The complete page, `decision-diagram.html`, is at the end
under **The page**: card design, layout engine wrapper, camera, icons and a sample `MAP`. It
works in any project, with no repo, package manager or build step.

It loads two things over the network when it opens:

- **Pele** (`pele@1.7.0`, layout and edge routing) from
  `https://cdn.jsdelivr.net/npm/pele@1.7.0/dist/pele.global.js`. Required.
- **Inter** from Google Fonts. Optional; it falls back to the system font.

If jsDelivr is blocked where the page will be opened, the page says so instead of drawing.
Then download `pele.global.js` once (`npm pack pele@1.7.0`, file `package/dist/pele.global.js`),
put it next to the page and change that `<script src>` to `./pele.global.js`.

## 1. Pick the shape

Choose the one that fits what the person is deciding. Mix them when it helps (an options tree
whose favourite option grows into a short plan).

| shape | use it when | how it looks |
| --- | --- | --- |
| **Options tree** | "Should I…?", "Which one…?" with a few real alternatives | the question on top; each option a card under it with pros, cons and numbers as facts; the consequences or sub-questions an option raises hang under that option |
| **Yes/no flow** | the answer depends on a few checks ("Fix or replace my laptop?", "Which visa do I need?") | `direction: 'LR'`; each check a question card; edges labelled "yes" / "no" (or "under €300", "over"); outcome cards at the ends, the recommended one `decided` |
| **Plan** | the decision is made and the question is how ("How do we move by June?") | steps as cards top to bottom; done steps `decided` tagged "Done", the current one `open` and the `focus`, later ones `considered` tagged "Later"; risks or alternatives branch off the step they belong to |
| **Live map** | the person is thinking out loud over a conversation | options tree that keeps growing; `sub` credits who raised each option; `focus` is the card the chat is on now; republish to the same link as it moves |

## 2. Write the MAP

```js
const MAP = {
  kind: 'Decisions',             // breadcrumb root: 'Decisions', 'Plans', 'Trips', 'Money'...
  title: 'Fix or replace my laptop?',
  meta: '',                      // one short provenance line ('From today’s chat'), or ''
  direction: 'LR',               // 'TB' (top to bottom, default) or 'LR' (left to right, good for yes/no flows)
  focus: '',                     // a node id to mark "you are here" with a blue path, or ''
  nodes: [
    { id: 'age', status: 'open', icon: 'clock', title: 'Age', sub: 'Check 1',
      line: 'Is the laptop more than 5 years old?', facts: ['Bought 2019'] },
    { id: 'cost', status: 'open', icon: 'wallet', title: 'Repair cost', sub: 'Check 2',
      line: 'Does the repair cost less than a third of a new one?', facts: ['Quote €220', 'new €900'] },
    { id: 'replace', status: 'considered', icon: 'monitor', title: 'Replace', sub: 'Outcome',
      line: 'Buy new; batteries and support run out soon after 5 years.', facts: ['€900'] },
    { id: 'fix', status: 'decided', tag: 'Best value', icon: 'check', title: 'Repair', sub: 'Outcome',
      line: 'Fix it and get two more good years for a quarter of the price.', facts: ['€220', '+ 2 years'] },
    { id: 'diy', status: 'rejected', icon: 'alert', title: 'DIY fix', sub: 'Outcome',
      line: 'Order the part and swap it yourself.', reason: 'Ruled out: voids the warranty on the screen' },
  ],
  edges: [
    { source: 'age', target: 'replace', label: 'yes' },
    { source: 'age', target: 'cost', label: 'no' },
    { source: 'cost', target: 'fix', label: 'yes' },
    { source: 'cost', target: 'replace', label: 'no' },
    { source: 'cost', target: 'diy', dashed: true },
  ],
};
```

Node fields:

| field | what goes in it |
| --- | --- |
| `id` | short, unique, lowercase, no spaces |
| `status` | one of the six states below |
| `tag` | optional: renames the pill and keeps its colour ("Done", "Later", "Best value", "Cheapest"). Two words at most |
| `icon` | a name from the icon list |
| `title` | **one or two words**, three at most ("Repair", "80% pay"). Never the full question |
| `sub` | the card's role or who raised it: "Question", "Option", "Check 1", "Outcome", "Step 2", "Sam’s idea", "Claude’s idea" |
| `line` | one sentence: the full question, or the gist of the option. Under about 90 characters |
| `facts` | one to three short facts, shown joined by " · ". The first is the headline: a number, "+ pro", "− con", "2 for · 1 against" |
| `reason` | only for `rejected` and `unexplored`, instead of `facts`: "Ruled out: <why>" or "Nobody has raised this yet" |

Edges go from parent to child. `label` (two words at most) when the condition matters: "yes",
"no", "if kept", "then", "under €300". `dashed: true` for a path to an `unexplored` card or a
maybe. A card may have two parents when two paths really end in the same place (both "no"
branches lead to Replace); otherwise keep it a tree.

## 3. The six states

The pill is the only colour on a card. Use `tag` when the default word doesn't fit the shape.

| status | pill | means |
| --- | --- | --- |
| `open` | Open (orange) | a question or check still to answer; the current step of a plan |
| `considered` | On the table (grey) | a live option or outcome, nothing special about it yet; a later step |
| `kept` | Kept (blue) | the favourite, shortlisted, leaning towards |
| `decided` | Decided (green) | chosen, settled, done, or the recommended outcome |
| `rejected` | Ruled out (greyed card) | dropped, with the reason in its footer |
| `unexplored` | Not explored (ghost card) | a credible option nobody has raised; add one or two when they exist, credited "Claude’s idea" |

## 4. Content rules

- Use the person's own words, names and numbers. Facts are concrete (€, hours, dates, people),
  not adjectives.
- 4 to 15 cards, about three levels deep. Fold small points into facts rather than new cards.
- Keep ruled-out options on the diagram with their reason; never delete them.
- Show trade-offs as facts with "+" and "−", and put the deciding number first.
- Say what you recommend through the states (`decided` or `kept`), not in extra text on the page.
- Use typographic apostrophes (’) and real minus signs (−) in visible text.
- If the decision or its options are unclear, ask one short question first, then draw.

## 5. Build the page

Do not retype the page; copy it out of this file with a script and swap in your `MAP`.

1. Write your `MAP` (the whole `const MAP = { ... };` statement) to a file, say `map.js`.
2. Run this, with `SKILL` set to the path of this SKILL.md (the skill's base directory is shown
   when the skill loads), a page title of two to four words, and an output name:
   ```bash
   python3 - "$SKILL" map.js "Laptop Repair Flow" laptop-repair-flow.html <<'PY'
   import sys, re
   skill, mapfile, title, out = sys.argv[1:5]
   s = open(skill, encoding='utf-8').read()
   page = s[s.rindex('<!-- BEGIN decision-diagram.html -->'):s.rindex('<!-- END decision-diagram.html -->')]
   a = page.index('  const MAP = {'); b = page.index('  // ===== End of the map.')
   m = open(mapfile, encoding='utf-8').read().strip()
   page = page[:a] + '  ' + m.replace('\n', '\n  ') + '\n' + page[b:]
   page = re.sub(r'<title>.*?</title>', '<title>' + title.replace('&', '&amp;').replace('<', '&lt;') + '</title>', page, count=1)
   open(out, 'w', encoding='utf-8').write(page)
   print('wrote', out)
   PY
   ```
   With no shell, copy the page below by hand and replace only the block between
   `// ===== The map.` and `// ===== End of the map.`, plus the `<title>`.
3. Show it:
   - **Artifact tool available** (Claude Code, Claude projects): publish the one file with
     `icon: "map"` and a one-sentence `description`. To change it later, edit the file and
     publish the same path again so the link stays the same.
   - **claude.ai chat with HTML artifacts**: put the whole page in one HTML artifact.
   - **Local only**: save the file and open it in a browser. It works from `file://`; no server
     is needed.
4. Reply with the link and two or three lines: what the diagram recommends or where things
   stand, what was ruled out, and any "Not explored" option worth a look.

## Icons

target, listChecks, check, clock, lock, star, heart, home, user, users, wallet, calendar, flag,
briefcase, alert, plane, sun, mapPin, shield, car, building, leaf, zap, split, scale, sparkles,
monitor. An unknown name falls back to a list icon.

## Checks before you publish

- Every edge id and the `focus` (if set) exist in `nodes`.
- Titles are one or two words; the detail lives in `line`.
- `rejected` and `unexplored` cards have a `reason` and no `facts`.
- The page `<title>` is a two-to-four-word name.

## The page

The complete page. Change only the `MAP` block and the `<title>`. Everything else (tokens for
light and dark, the card anatomy, the layout wrapper) is the design; leave it as it is.

```html
<!-- BEGIN decision-diagram.html -->
<title>Decision Diagram Template</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap">
<style>
:root{--page: #ffffff;--canvas: #fafafa;--dot: rgba(0, 0, 0, .1);--card: #ffffff;--card-shadow: 0 0 0 .5px rgba(0, 0, 0, .06), 0 1px 1px -1px rgba(0, 0, 0, .1), 0 1px 2px 0 rgba(0, 0, 0, .05);--rule: #e5e5e5;--strong: #000000;--ink: rgba(0, 0, 0, .88);--text: rgba(0, 0, 0, .61);--muted: rgba(0, 0, 0, .45);--faint: rgba(0, 0, 0, .27);--fill: rgba(0, 0, 0, .06);--strip: rgba(0, 0, 0, .025);--edge: rgba(0, 0, 0, .2);--brand-fg: #006dcbf2;--brand-bg: #008ff519;--link: #82bcff;--ok-fg: #007d2ee0;--ok-bg: #00a43319;--warn-fg: #cc4e00;--warn-bg: #ff9c0029;--font: "Inter", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif}@media (prefers-color-scheme: dark){:root:not([data-theme=light]){--page: #0c0c0d;--canvas: #141416;--dot: rgba(255, 255, 255, .08);--card: #1c1c1f;--card-shadow: 0 0 0 .5px rgba(255, 255, 255, .1), 0 1px 2px 0 rgba(0, 0, 0, .4);--rule: #26262a;--strong: #ffffff;--ink: rgba(255, 255, 255, .9);--text: rgba(255, 255, 255, .62);--muted: rgba(255, 255, 255, .45);--faint: rgba(255, 255, 255, .28);--fill: rgba(255, 255, 255, .08);--strip: rgba(255, 255, 255, .03);--edge: rgba(255, 255, 255, .22);--brand-fg: #70b8ff;--brand-bg: #0077ff3a;--link: #4f8fdb;--ok-fg: #3dd68c;--ok-bg: #00f04a1f;--warn-fg: #ffa057;--warn-bg: #fb6a0025;color-scheme:dark}}:root[data-theme=dark]{--page: #0c0c0d;--canvas: #141416;--dot: rgba(255, 255, 255, .08);--card: #1c1c1f;--card-shadow: 0 0 0 .5px rgba(255, 255, 255, .1), 0 1px 2px 0 rgba(0, 0, 0, .4);--rule: #26262a;--strong: #ffffff;--ink: rgba(255, 255, 255, .9);--text: rgba(255, 255, 255, .62);--muted: rgba(255, 255, 255, .45);--faint: rgba(255, 255, 255, .28);--fill: rgba(255, 255, 255, .08);--strip: rgba(255, 255, 255, .03);--edge: rgba(255, 255, 255, .22);--brand-fg: #70b8ff;--brand-bg: #0077ff3a;--link: #4f8fdb;--ok-fg: #3dd68c;--ok-bg: #00f04a1f;--warn-fg: #ffa057;--warn-bg: #fb6a0025;color-scheme:dark}html,body{height:100%}body{margin:0;background:var(--page);color:var(--ink);font:400 13px/20px var(--font)}.frame{height:100%;display:grid;grid-template-rows:auto 1fr}.bar{display:flex;align-items:center;gap:12px;flex-wrap:wrap;min-height:48px;box-sizing:border-box;padding-block:8px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));border-bottom:1px solid var(--rule);background:var(--page)}.crumbs{display:flex;align-items:center;gap:6px;min-width:0}.crumbs span{color:var(--muted)}.crumbs svg{width:14px;height:14px;color:var(--faint);flex:none}.crumbs b{font-weight:500;color:var(--strong);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.meta{color:var(--muted);font-size:12px;padding-left:12px;border-left:1px solid var(--rule);white-space:nowrap}.sum{margin-left:auto;display:flex;align-items:center;gap:10px;font-size:12px;line-height:16px;font-variant-numeric:tabular-nums;color:var(--muted);flex-wrap:wrap}.sum .is-ok{color:var(--ok-fg)}.sum .is-brand{color:var(--brand-fg)}.sum .is-open{color:var(--warn-fg);background:var(--warn-bg);font-weight:500;border-radius:5px;padding:3px 7px}.stage{position:relative;min-height:0}#flow{position:absolute;inset:0}#flow.pf-viewport{--pf-bg: var(--canvas);--pf-line: var(--edge);--pf-accent: var(--link);--pf-ring: var(--brand-fg);--pf-muted: var(--muted);--pf-label-border: var(--rule);--pf-card-radius: 8px;background-color:var(--canvas);background-image:radial-gradient(var(--dot) 1px,transparent 1.2px)}#flow .pele-edge-label text{font-family:var(--font)}#flow .pele-edge.is-path path{stroke:var(--link);stroke-width:2}#flow .pele-edge.is-path .pele-marker{fill:var(--link)}#flow .pf-node.is-muted{opacity:1}#flow .pf-node.is-selected{outline:1.5px solid var(--brand-fg);outline-offset:2px}.zoom{position:absolute;z-index:2;display:flex;align-items:center;gap:2px;padding:4px;left:max(16px,env(safe-area-inset-left,0px));bottom:calc(16px + env(safe-area-inset-bottom,0px));background:var(--card);border-radius:10px;box-shadow:var(--card-shadow)}.zoom button{border:0;background:none;color:var(--text);height:28px;min-width:28px;padding:0 6px;border-radius:6px;display:grid;place-items:center;font:500 12px/1 var(--font);cursor:pointer;font-variant-numeric:tabular-nums}.zoom button:hover{background:var(--fill);color:var(--ink)}.zoom button:focus-visible{outline:2px solid var(--brand-fg);outline-offset:1px}.zoom svg{width:15px;height:15px}.zoom i{width:1px;height:16px;background:var(--rule);margin:0 2px}.hint{position:absolute;z-index:2;right:max(16px,env(safe-area-inset-right,0px));bottom:calc(16px + env(safe-area-inset-bottom,0px));font-size:12px;color:var(--muted);background:var(--card);box-shadow:var(--card-shadow);border-radius:8px;padding:6px 10px;max-width:46ch}.hint b{color:var(--ink);font-weight:500}@media (max-width: 640px){.hint,.meta{display:none}}.dc{width:240px;box-sizing:border-box;padding:10px 10px 8px;display:grid;gap:6px;background:var(--card);border-radius:8px;box-shadow:var(--card-shadow);font:400 13px/20px var(--font);color:var(--text);overflow:hidden}.dc__top{display:flex;align-items:flex-start;gap:8px}.dc__tile{flex:none;width:22px;height:22px;border-radius:6px;margin-top:4px;display:grid;place-items:center;background:var(--card);box-shadow:var(--card-shadow);color:var(--ink)}.dc__tile svg{width:13px;height:13px}.dc__who{flex:1;min-width:0;display:grid}.dc__name{color:var(--strong);font-weight:500;line-height:16px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;text-wrap:pretty}.dc__sub{color:var(--muted);font-size:11px;line-height:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.dc__pill{flex:none;height:18px;padding:0 6px 0 4px;border-radius:4px;display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:500;line-height:16px;white-space:nowrap}.dc__pill svg{width:12px;height:12px}.tone-warn{color:var(--warn-fg);background:var(--warn-bg)}.tone-brand{color:var(--brand-fg);background:var(--brand-bg)}.tone-ok{color:var(--ok-fg);background:var(--ok-bg)}.tone-plain{color:var(--text);background:var(--fill)}.tone-faint{color:var(--muted);background:var(--fill)}.dc__line{margin:0;font-size:12px;line-height:16px;color:var(--text);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.dc__meta{display:flex;align-items:center;gap:6px;height:20px;font-variant-numeric:tabular-nums}.dc__facts{flex:1;min-width:0;font-size:11px;line-height:16px;font-weight:500;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.dc__facts span{color:var(--muted);font-weight:400}.dc__fold{flex:none;height:20px;padding:0 4px 0 6px;border-radius:5px;border:0;background:none;display:inline-flex;align-items:center;gap:2px;font:500 11px/20px var(--font);color:var(--muted);cursor:pointer}.dc__fold:hover{background:var(--fill);color:var(--ink)}.dc__fold:focus-visible{outline:2px solid var(--brand-fg);outline-offset:1px}.dc__fold svg{width:12px;height:12px;transition:transform .2s ease}.dc__fold[aria-expanded=false] svg{transform:rotate(-90deg)}.dc__strip{margin:0 -10px -8px;padding:6px 10px;display:flex;align-items:flex-start;gap:6px;border-top:1px solid var(--fill);background:var(--strip);font-size:12px;line-height:16px;color:var(--muted)}.dc__strip svg{width:14px;height:14px;flex:none;margin-top:1px}.dc.is-stopped .dc__name{color:var(--muted)}.dc.is-stopped .dc__line,.dc.is-stopped .dc__sub{color:var(--faint)}.dc.is-stopped .dc__tile{color:var(--muted);box-shadow:0 0 0 .5px var(--fill)}.dc.is-ghost{box-shadow:0 0 0 1px var(--fill);background:transparent}.dc.is-ghost .dc__strip{color:var(--brand-fg)}.dc.is-ghost .dc__tile{background:transparent;box-shadow:0 0 0 1px var(--fill);color:var(--muted)}@media (prefers-reduced-motion: reduce){.dc__fold svg{transition:none}}
</style>

<div class="frame">
  <header class="bar">
    <nav class="crumbs" aria-label="Breadcrumb">
      <span id="kind"></span>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
      <b id="crumb"></b>
    </nav>
    <span class="meta" id="meta"></span>
    <div class="sum" id="sum" aria-live="polite"></div>
  </header>
  <section class="stage">
    <div id="flow" aria-label="Decision map"></div>
    <div class="zoom" role="toolbar" aria-label="Zoom">
      <button type="button" id="zout" aria-label="Zoom out"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 12h14"/></svg></button>
      <button type="button" id="zpct" aria-label="Zoom to 100%">100%</button>
      <button type="button" id="zin" aria-label="Zoom in"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg></button>
      <i></i>
      <button type="button" id="zfit" aria-label="Fit the whole map"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/></svg></button>
    </div>
    <p class="hint" id="hint"></p>
  </section>
</div>

<script src="https://cdn.jsdelivr.net/npm/pele@1.7.0/dist/pele.global.js"></script>
<script type="module">
  // ---- engine: pele-flow.js (layout, camera, selection), Lucide icons (ISC), esc(). Minified; do not edit. ----
const DEFAULTS={direction:"TB",nodeGap:40,rankGap:72,padding:24,minZoom:.1,maxZoom:2.5,zoomStep:1.25,fitPadding:32,readableZoom:.6,portGap:24,cameraResponse:90,edgeFontSize:11,fontFamily:"sans-serif",gridSize:24,onSelect:null,onOpen:null,onCamera:null},STYLE=`
.pf-viewport{position:relative;overflow:hidden;touch-action:none;user-select:none;-webkit-user-select:none;cursor:grab;
  background-color:var(--pf-bg,#f7f6f3);
  background-image:linear-gradient(var(--pf-grid,rgba(0,0,0,.045)) 1px,transparent 1px),linear-gradient(90deg,var(--pf-grid,rgba(0,0,0,.045)) 1px,transparent 1px);}
.pf-viewport.is-panning{cursor:grabbing}
.pf-viewport:focus-visible{outline:2px solid var(--pf-ring,rgba(180,84,58,.7));outline-offset:-2px}
.pf-plane{position:absolute;left:0;top:0;transform-origin:0 0;will-change:transform}
.pf-plane.is-hidden{opacity:0}
.pf-edges,.pf-cards{position:absolute;left:0;top:0}
.pf-edges svg{position:absolute;left:0;top:0;overflow:visible;display:block;transition:opacity .22s ease}
.pf-edges svg.is-leaving{opacity:0;pointer-events:none}
.pf-edges svg.is-entering{opacity:0}
.pf-measure{position:absolute;left:0;top:0;visibility:hidden;pointer-events:none}
.pf-node{position:absolute;left:0;top:0;cursor:pointer;border-radius:var(--pf-card-radius,14px);outline:none;will-change:transform}
.pf-ready .pf-node{transition:transform .32s cubic-bezier(.2,.8,.2,1),opacity .2s ease}
.pf-node.is-muted{opacity:.45}
.pf-node.is-selected{outline:2px solid var(--pf-ring,rgba(180,84,58,.7));outline-offset:3px}
.pf-node:focus-visible{outline:2px solid var(--pf-ring,rgba(180,84,58,.7));outline-offset:3px}
/* Pele's edges, restyled to onevra's palette and metrics. */
.pf-edges .pele-edge path{stroke:var(--pf-line,#b5b1ab);stroke-width:1.5;transition:stroke .15s ease,opacity .15s ease}
.pf-edges .pele-edge path[stroke-dasharray]{stroke-dasharray:4 5}
.pf-edges .pele-edge .pele-marker{fill:var(--pf-line,#b5b1ab);stroke:none}
.pf-edges .pele-edge.is-muted{opacity:.35}
.pf-edges .pele-edge.is-emphasized path{stroke:var(--pf-accent,#b4543a);stroke-width:2}
.pf-edges .pele-edge.is-emphasized .pele-marker{fill:var(--pf-accent,#b4543a)}
.pf-edges .pele-edge-labels{font-weight:500;letter-spacing:.01em}
.pf-edges .pele-edge-label rect{rx:9px;fill:var(--pf-bg,#f7f6f3);stroke:var(--pf-label-border,rgba(0,0,0,.12));stroke-width:1}
.pf-edges .pele-edge-label text{fill:var(--pf-muted,#8a8580)}
.pf-edges .pele-edge-label.is-muted{opacity:.6}
.pf-edges .pele-nodes{display:none}
.pf-edges .pele-cluster rect{fill:var(--pf-group-fill,rgba(0,0,0,.025));stroke:var(--pf-label-border,rgba(0,0,0,.12));stroke-dasharray:4 5;rx:18px}
.pf-edges .pele-cluster-label{fill:var(--pf-muted,#8a8580);font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase}
@media (prefers-reduced-motion:reduce){.pf-ready .pf-node,.pf-edges svg{transition:none}}
`;let styleInjected=!1;function injectStyle(){if(styleInjected||typeof document>"u")return;styleInjected=!0;const d=document.createElement("style");d.textContent=STYLE,document.head.appendChild(d)}const clamp=(d,v,p)=>Math.max(v,Math.min(d,p)),el=d=>{const v=document.createElement("div");return v.className=d,v},cleanLabel=d=>String(d??"").replace(/[|"`<>]/g," ").replace(/\s+/g," ").trim();function createFlow(d,v={}){if(typeof v.render!="function")throw new TypeError("createFlow needs options.render (pele.render)");if(typeof v.card!="function")throw new TypeError("createFlow needs options.card(node) returning an element");injectStyle();const p={...DEFAULTS,...v};d.classList.add("pf-viewport"),d.tabIndex=d.tabIndex>=0?d.tabIndex:0,d.setAttribute("role","group");const w=el("pf-plane is-hidden"),H=el("pf-edges"),b=el("pf-cards"),N=el("pf-measure");w.append(H,b),d.append(w,N);const E=typeof matchMedia=="function"&&matchMedia("(prefers-reduced-motion: reduce)").matches,e={nodes:new Map,order:[],edges:[],svg:null,width:0,height:0,vw:0,vh:0,camera:{x:0,y:0,z:1},shown:{x:0,y:0,z:1},ready:!1,userMoved:!1,selected:"",hovered:"",raf:0,lastFrame:0,source:"",pct:0};function C(){const{x:t,y:n,z:r}=e.shown;w.style.transform=`translate(${t}px,${n}px) scale(${r})`;const l=p.gridSize*r;d.style.backgroundSize=`${l}px ${l}px`,d.style.backgroundPosition=`${t}px ${n}px`;const c=Math.round(r*100);c!==e.pct&&(e.pct=c,p.onCamera?.(r))}function Y(t){e.raf=0;const n=e.lastFrame?Math.min(Math.max(0,t-e.lastFrame),48):16;e.lastFrame=t;const r=e.camera,l=e.shown,c=r.x-l.x,i=r.y-l.y,m=r.z-l.z;if(E||Math.abs(c)<.05&&Math.abs(i)<.05&&Math.abs(m)<5e-4){e.shown={...r},C(),e.lastFrame=0;return}const u=1-Math.exp(-n/p.cameraResponse);e.shown={x:l.x+c*u,y:l.y+i*u,z:l.z+m*u},C(),e.raf=requestAnimationFrame(Y)}function O(){e.raf||(e.raf=requestAnimationFrame(Y))}function Z(){e.shown={...e.camera},C()}function A(t,n=p.minZoom){if(!e.nodes.size||!e.vw)return;const r=typeof p.fitPadding=="number"?{top:p.fitPadding,right:p.fitPadding,bottom:p.fitPadding,left:p.fitPadding}:{top:32,right:32,bottom:32,left:32,...p.fitPadding},l=Math.max(1,e.vw-r.left-r.right),c=Math.max(1,e.vh-r.top-r.bottom),i=Math.max(1,e.width),m=Math.max(1,e.height),u=clamp(Math.max(Math.min(l/i,c/m),Math.min(n,1)),p.minZoom,1),s=e.nodes.get(e.order[0]),g=(a,o,f,y,x)=>o*u<=a?f+(a-o*u)/2:y||!s?f:clamp(f+a/2-x*u,f+a-o*u,f),h=p.direction==="LR";e.camera={x:g(l,i,r.left,h,s?s.x+s.w/2:0),y:g(c,m,r.top,!h,s?s.y+s.h/2:0),z:u},e.userMoved=!1,t||E?Z():O()}function S(t,n,r,l){const c=l?e.camera:e.shown,i=clamp(c.z*r,p.minZoom,p.maxZoom),m=(t-c.x)/c.z,u=(n-c.y)/c.z;e.camera={x:t-m*i,y:n-u*i,z:i},e.userMoved=!0,!l||E?Z():O()}function K(t){const n=e.nodes.get(t);if(!n||!e.vw)return;const r=e.camera.z;e.camera={x:e.vw/2-(n.x+n.w/2)*r,y:e.vh/2-(n.y+n.h/2)*r,z:r},e.userMoved=!0,O()}function ne(t){const n=e.nodes.get(t);if(!n)return;const r=e.camera.z,l=16,c=n.x*r+e.camera.x,i=n.y*r+e.camera.y;(c<l||i<l||c+n.w*r>e.vw-l||i+n.h*r>e.vh-l)&&K(t)}function I(){const t=[e.hovered,e.selected].filter(Boolean),n=e.svg?.querySelector(".pele-edges");for(const r of e.edges){if(!r.group)continue;const l=e.nodes.get(r.source)?.node.muted||e.nodes.get(r.target)?.node.muted,c=t.some(i=>i===r.source||i===r.target);r.group.classList.toggle("is-muted",!!l),r.group.classList.toggle("is-emphasized",c),r.labelGroup&&r.labelGroup.classList.toggle("is-muted",!!l),c&&n&&n.appendChild(r.group)}}function Q(){for(const[t,n]of e.nodes)n.wrap.classList.toggle("is-selected",t===e.selected)}function ae(t,n,r){const l=new Map(t.map((s,g)=>[s,`n${g}`])),c={flowchart:{curve:"step",nodeSpacing:p.nodeGap,rankSpacing:p.rankGap}};let i=`%%{init: ${JSON.stringify(c)}}%%
flowchart ${p.direction}
`;const m=s=>{const g=e.nodes.get(s);return`${l.get(s)}@{ img: "x", w: ${g.w}, h: ${g.h}, label: "" }
`},u=new Set;r.forEach((s,g)=>{const h=t.filter(a=>e.nodes.get(a).node.group===s.id);if(h.length){i+=`  subgraph g${g} [${cleanLabel(s.label||s.id)||" "}]
`;for(const a of h)i+="    "+m(a),u.add(a);i+=`  end
`}});for(const s of t)u.has(s)||(i+="  "+m(s));return n.forEach((s,g)=>{const h=l.get(s.source),a=l.get(s.target);if(!h||!a||h===a)return;const o=cleanLabel(s.label),f=s.dashed?"-.->":"-->";i+=`  ${h} e${g}@${f}${o?`|${o}|`:""} ${a}
`}),i}function re(){const t=p.direction==="LR"?1:0,n=1-t,r=new Map;for(const c of e.edges){const i=c.group?.querySelector("path:not(.pele-marker)"),m=i?.getAttribute("d")??"";if(!/^M[-\d.,\sLQ]+$/.test(m))continue;const u=[...m.matchAll(/([MLQ])([^MLQ]*)/g)].map(([,y,x])=>{const z=x.split(/[\s,]+/).filter(Boolean).map(Number),M=[];for(let L=0;L+1<z.length;L+=2)M.push([z[L],z[L+1]]);return{c:y,pairs:M}}),s=u.flatMap(y=>y.pairs);if(s.length<2)continue;const g=s[s.length-1];let h=s.length-1;for(;h>0&&Math.abs(s[h-1][t]-g[t])<.01;)h--;if(h===s.length-1)continue;const a=h===0,o=a?null:[s[Math.max(0,h-2)][t],s[h-1][t]],f=`${c.target}|${Math.sign(g[n]-s[h][n])}`;r.has(f)||r.set(f,[]),r.get(f).push({e:c,path:i,cmds:u,pts:s,k:h,straight:a,turn:o,at:g[t],from:a?g[t]:o[0]})}for(const[c,i]of r){if(i.length<2)continue;const m=e.nodes.get(c.slice(0,c.lastIndexOf("|"))),u=m?t?m.h:m.w:0,s=Math.min(p.portGap,Math.max(0,u-40)/(i.length-1));if(!s)continue;i.sort((a,o)=>a.from-o.from);const g=i.findIndex(a=>a.straight),h=g>=0?g:(i.length-1)/2;i.forEach((a,o)=>{const f=(o-h)*s;f&&(!a.straight&&Math.sign(f)===Math.sign(a.turn[0]-a.at)&&Math.abs(a.turn[1]-a.turn[0])-Math.abs(f)<4||l(a,f))})}function l({e:c,path:i,cmds:m,pts:u,k:s,straight:g,at:h},a){const o=g?0:s-1;u.forEach((k,$)=>{$>=o&&(k[t]+=a)});const f=k=>+k.toFixed(2);i.setAttribute("d",m.map(k=>k.c+k.pairs.map($=>`${f($[0])},${f($[1])}`).join(" ")).join(""));const y=c.group.querySelector(".pele-marker");y?.setAttribute("d",y.getAttribute("d").replace(/(-?[\d.]+),(-?[\d.]+)/g,(k,$,fe)=>{const j=[+$,+fe];return j[t]+=a,`${f(j[0])},${f(j[1])}`}));const x=c.labelGroup?.querySelector("rect"),z=c.labelGroup?.querySelector("text");if(!x||!z)return;const[M,L]=t?["y","height"]:["x","width"],[ie,de]=t?["x","width"]:["y","height"],ce=+x.getAttribute(M)+ +x.getAttribute(L)/2,te=+x.getAttribute(ie)+ +x.getAttribute(de)/2,le=Math.min(u[s][n],u.at(-1)[n]),pe=Math.max(u[s][n],u.at(-1)[n]);Math.abs(ce-h)<1&&(g||te>=le&&te<=pe)&&(x.setAttribute(M,f(+x.getAttribute(M)+a)),z.setAttribute(M,f(+z.getAttribute(M)+a)))}}function W(t){const n=t.nodes??[],r=t.edges??[],l=t.groups??[],c=new Set,i=[];for(const a of n){if(!a.id||c.has(a.id))continue;c.add(a.id),i.push(a.id);let o=e.nodes.get(a.id);const f=p.card(a);if(o)o.node=a,o.wrap.replaceChildren(f);else{const y=el("pf-node");y.dataset.id=a.id,y.tabIndex=0,y.setAttribute("role","button"),y.append(f),N.append(y),o={node:a,wrap:y,w:0,h:0,x:0,y:0,fresh:!0},e.nodes.set(a.id,o)}o.wrap.setAttribute("aria-label",a.label||a.id),o.wrap.classList.toggle("is-muted",!!a.muted),o.w=Math.round(o.wrap.offsetWidth*2)/2,o.h=Math.round(o.wrap.offsetHeight*2)/2}for(const[a,o]of e.nodes)c.has(a)||(o.wrap.remove(),e.nodes.delete(a));if(e.order=i,e.edges=r.filter(a=>c.has(a.source)&&c.has(a.target)&&a.source!==a.target).map(a=>({...a})),!i.length){e.svg?.remove(),e.svg=null,e.width=e.height=0,w.classList.add("is-hidden"),e.ready=!1;return}e.source=ae(i,e.edges,l);const m=p.render(e.source,{images:!1,responsive:!1,padding:p.padding,fontSize:p.edgeFontSize/.875,fontFamily:p.fontFamily});e.width=m.width,e.height=m.height,w.style.width=`${e.width}px`,w.style.height=`${e.height}px`;const u=new DOMParser().parseFromString(m.svg,"image/svg+xml"),s=document.adoptNode(u.documentElement);s.removeAttribute("style"),s.style.fontFamily=p.fontFamily,s.style.fontSize=`${p.edgeFontSize}px`;const g=new Map(i.map((a,o)=>[`n${o}`,a]));for(const a of s.querySelectorAll("g.pele-node")){const o=g.get(a.getAttribute("data-id")),f=/translate\(([-\d.]+),([-\d.]+)\)/.exec(a.getAttribute("transform")||""),y=o&&e.nodes.get(o);!y||!f||(y.x=parseFloat(f[1])-y.w/2,y.y=parseFloat(f[2])-y.h/2)}e.edges.forEach((a,o)=>{a.group=s.querySelector(`g.pele-edge[data-id="e${o}"]`),a.labelGroup=s.querySelector(`g.pele-edge-label[data-id="e${o}"]`)}),re();for(const a of i){const o=e.nodes.get(a);o.fresh?(o.fresh=!1,o.wrap.style.transition="none",o.wrap.style.transform=`translate(${o.x}px,${o.y}px)`,b.append(o.wrap),o.wrap.offsetWidth,o.wrap.style.transition=""):o.wrap.style.transform=`translate(${o.x}px,${o.y}px)`}const h=e.svg;e.svg=s,h&&e.ready&&!E?(h.classList.add("is-leaving"),setTimeout(()=>h.remove(),260),s.classList.add("is-entering"),H.append(s),requestAnimationFrame(()=>requestAnimationFrame(()=>s.classList.remove("is-entering")))):(h?.remove(),H.append(s)),I(),Q(),X(),e.ready?e.userMoved||A(!1,p.readableZoom):(e.ready=!0,A(!0,p.readableZoom),w.classList.remove("is-hidden"),requestAnimationFrame(()=>d.classList.add("pf-ready")))}function X(){const t=d.clientWidth,n=d.clientHeight;if(!t||!n||t===e.vw&&n===e.vh)return;if(!e.vw||!e.ready){e.vw=t,e.vh=n;return}const r=(t-e.vw)/2,l=(n-e.vh)/2;if(e.vw=t,e.vh=n,!e.userMoved){A(!0,p.readableZoom);return}e.camera.x+=r,e.camera.y+=l,e.shown.x+=r,e.shown.y+=l,C()}const J=typeof ResizeObserver=="function"?new ResizeObserver(()=>X()):null;J?.observe(d);let F=!1,R=!1,D=0,T=0,B=0,V=0,U=0,q=null;const P=t=>{const n=d.getBoundingClientRect();return[t.clientX-n.left,t.clientY-n.top]};d.addEventListener("pointerdown",t=>{!e.ready||t.button!==0&&t.button!==1||t.target.closest(".pf-node")||(F=!0,R=!1,U=t.detail,q=t.pointerId,[D,T]=P(t),B=D,V=T,e.camera={...e.shown},d.setPointerCapture(t.pointerId),d.classList.add("is-panning"))}),d.addEventListener("pointermove",t=>{if(!F||t.pointerId!==q)return;const[n,r]=P(t);Math.hypot(n-D,r-T)>4&&(R=!0),e.camera.x+=n-B,e.camera.y+=r-V,B=n,V=r,e.userMoved=!0,Z()});const se=t=>{if(!F||t.pointerId!==q||(F=!1,d.classList.remove("is-panning"),R||t.button!==0))return;const[n,r]=P(t);U>=2?S(n,r,t.shiftKey?.5:2,!0):e.selected&&G("")};d.addEventListener("pointerup",se),d.addEventListener("pointercancel",t=>{t.pointerId===q&&(F=!1,d.classList.remove("is-panning"))}),d.addEventListener("wheel",t=>{if(!e.ready)return;t.preventDefault();const[n,r]=P(t),l=t.deltaMode===1?16:t.deltaMode===2?e.vh:1;t.ctrlKey||t.metaKey?S(n,r,Math.exp(-t.deltaY*l*.01),!1):(e.camera={x:e.shown.x-t.deltaX*l,y:e.shown.y-t.deltaY*l,z:e.shown.z},e.userMoved=!0,Z())},{passive:!1}),b.addEventListener("click",t=>{const n=t.target.closest(".pf-node");n&&G(n.dataset.id)}),b.addEventListener("dblclick",t=>{const n=t.target.closest(".pf-node");n&&p.onOpen?.(n.dataset.id)}),b.addEventListener("pointerover",t=>{const n=t.target.closest(".pf-node"),r=n?n.dataset.id:"";r!==e.hovered&&(e.hovered=r,I())}),b.addEventListener("pointerleave",()=>{e.hovered&&(e.hovered="",I())}),b.addEventListener("focusin",t=>{const n=t.target.closest(".pf-node");n&&n.matches(":focus-visible")&&ne(n.dataset.id)}),b.addEventListener("keydown",t=>{const n=t.target.closest(".pf-node");n&&(t.key==="Enter"||t.key===" ")&&(t.preventDefault(),G(n.dataset.id))}),d.addEventListener("keydown",t=>{t.target===d&&(t.key==="+"||t.key==="="?(_(),t.preventDefault()):t.key==="-"?(ee(),t.preventDefault()):t.key==="0"&&(A(!1),t.preventDefault()))});function G(t){e.selected=t||"",Q(),I(),p.onSelect?.(e.selected)}function _(){S(e.vw/2,e.vh/2,p.zoomStep,!0)}function ee(){S(e.vw/2,e.vh/2,1/p.zoomStep,!0)}function oe(t){S(e.vw/2,e.vh/2,t/e.camera.z,!0)}return{update:W,select:G,fit:()=>A(!1),zoomIn:_,zoomOut:ee,zoomTo:oe,reveal:K,setDirection(t,n){p.direction=t==="LR"?"LR":"TB",n&&W(n)},get zoom(){return e.camera.z},get selected(){return e.selected},get source(){return e.source},get ready(){return e.ready},position(t){const n=e.nodes.get(t);return n?{x:n.x,y:n.y,w:n.w,h:n.h}:null},destroy(){J?.disconnect(),cancelAnimationFrame(e.raf),d.replaceChildren(),d.classList.remove("pf-viewport","pf-ready")}}}const icons={target:'<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',listChecks:'<path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/>',check:'<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',clock:'<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',lock:'<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',star:'<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',heart:'<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',home:'<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',user:'<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',users:'<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',wallet:'<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',calendar:'<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',flag:'<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" x2="4" y1="22" y2="15"/>',briefcase:'<path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect width="20" height="14" x="2" y="6" rx="2"/>',alert:'<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',plane:'<path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/>',sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',mapPin:'<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',shield:'<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',car:'<path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/>',building:'<rect width="16" height="20" x="4" y="2" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/>',leaf:'<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>',zap:'<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>',split:'<path d="M16 3h5v5"/><path d="M8 3H3v5"/><path d="M12 22v-8.3a4 4 0 0 0-1.172-2.872L3 3"/><path d="m15 9 6-6"/>',scale:'<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',sparkles:'<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/><path d="M4 17v2"/><path d="M5 18H3"/>',monitor:'<rect width="20" height="14" x="2" y="3" rx="2"/><line x1="8" x2="16" y1="21" y2="21"/><line x1="12" x2="12" y1="17" y2="21"/>'},icon=(d,v="")=>`<svg class="${v}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[d]??icons.listChecks}</svg>`,esc=d=>String(d??"").replace(/[&<>"]/g,v=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"})[v]);

  if (!window.pele) {
    document.getElementById('flow').innerHTML = '<p style="padding:24px;color:var(--muted)">Could not load the layout engine (pele@1.7.0 from cdn.jsdelivr.net). Check the network and reload.</p>';
    throw new Error('pele did not load');
  }

  // ===== The map. This block is the only part to edit. =====
  // map:   { kind, title, meta?, direction?: 'TB' | 'LR', focus?: node id (paints the path to it blue), nodes, edges }
  // node:  { id, status, icon, title, sub, line, facts: [..], tag? }   ruled out / not explored take reason: '..' instead of facts
  //        tag renames the pill and keeps its colour ('Done', 'Yes', 'Best value')
  // edge:  { source, target, label?, dashed? }   dashed for a path nobody has raised yet
  // status: open | considered | kept | decided | rejected | unexplored
  const MAP = {
    kind: 'Decisions',
    title: 'Which city?',
    meta: '',
    direction: 'TB',
    focus: '',
    nodes: [
      { id: 'q', status: 'open', icon: 'mapPin', title: 'Next city', sub: 'Question',
        line: 'Where should we live from next spring?', facts: ['2 options', '1 ruled out'] },
      { id: 'lis', status: 'kept', icon: 'sun', title: 'Lisbon', sub: 'Option',
        line: 'Sunny, cheaper, two hours from family.', facts: ['+ €600 a month', '− new language'] },
      { id: 'ber', status: 'rejected', icon: 'building', title: 'Berlin', sub: 'Option',
        line: 'Stay where we are.', reason: 'Ruled out: the lease ends and rents went up 30%' },
    ],
    edges: [
      { source: 'q', target: 'lis' },
      { source: 'q', target: 'ber' },
    ],
  };
  // ===== End of the map. =====
  // ---- renderer (minified; do not edit) ----
const STATE={open:{label:"Open",tone:"warn",glyph:'<circle cx="6" cy="6" r="4.25"/><path d="M6 1.75a4.25 4.25 0 0 1 0 8.5z" fill="currentColor" stroke="none"/>'},considered:{label:"On the table",tone:"plain",glyph:'<circle cx="6" cy="6" r="4"/>'},kept:{label:"Kept",tone:"brand",glyph:'<path d="M3.5 2h5v8L6 8.25 3.5 10z" stroke-linejoin="round"/>'},decided:{label:"Decided",tone:"ok",glyph:'<path d="m2.5 6.25 2.25 2.25L9.5 3.5" stroke-linecap="round" stroke-linejoin="round"/>'},rejected:{label:"Ruled out",tone:"faint",glyph:'<path d="m3.5 3.5 5 5M8.5 3.5l-5 5" stroke-linecap="round"/>'},unexplored:{label:"Not explored",tone:"brand",glyph:'<path d="M6 1.5 7.1 4.9 10.5 6 7.1 7.1 6 10.5 4.9 7.1 1.5 6 4.9 4.9z" fill="currentColor" stroke="none"/>'}},pill=(e,t)=>`<span class="dc__pill tone-${STATE[e].tone}"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.5">${STATE[e].glyph}</svg>${esc(t||STATE[e].label)}</span>`,DASH='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M3.5 7h7"/></svg>',SPARK='<svg viewBox="0 0 14 14"><path d="M7 1.5 8.3 5.7 12.5 7 8.3 8.3 7 12.5 5.7 8.3 1.5 7 5.7 5.7z" fill="currentColor"/></svg>',CHEV='<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m3 4.5 3 3 3-3"/></svg>',NODES=MAP.nodes.map(e=>({...e,status:STATE[e.status]?e.status:"considered"})),byId=new Map(NODES.map(e=>[e.id,e])),EDGES=MAP.edges.filter(e=>byId.has(e.source)&&byId.has(e.target)),ROOTS=NODES.filter(e=>!EDGES.some(t=>t.target===e.id)).map(e=>e.id),FOCUS=byId.has(MAP.focus)?MAP.focus:"",collapsed=new Set,kids=e=>EDGES.filter(t=>t.source===e).map(t=>t.target);function card(e){const t=document.createElement("article"),n=e.status==="rejected"||e.status==="unexplored";t.className="dc"+(n?" is-stopped":"")+(e.status==="unexplored"?" is-ghost":""),t.setAttribute("aria-label",`${e.title}, ${e.tag||STATE[e.status].label}`);const o=kids(e.id).length,[s,...a]=e.facts??[],c=n?`<p class="dc__strip">${e.status==="unexplored"?SPARK:DASH}<span>${esc(e.reason??(e.status==="unexplored"?"Nobody has raised this yet":"Ruled out"))}</span></p>`:`<div class="dc__meta"><span class="dc__facts">${esc(s??"")}${a.length?` <span>· ${a.map(esc).join(" · ")}</span>`:""}</span>${o?`<button class="dc__fold" type="button" aria-expanded="${!collapsed.has(e.id)}" aria-label="${collapsed.has(e.id)?"Show":"Hide"} ${o} below" data-fold="${e.id}">${o}${CHEV}</button>`:""}</div>`;return t.innerHTML=`<div class="dc__top"><span class="dc__tile">${icon(e.icon)}</span><span class="dc__who"><span class="dc__name">${esc(e.title)}</span><span class="dc__sub">${esc(e.sub)}</span></span>${pill(e.status,e.tag)}</div>
      ${e.line?`<p class="dc__line">${esc(e.line)}</p>`:""}${c}`,t}function visible(){const e=new Set(ROOTS),t=s=>{if(!collapsed.has(s))for(const a of kids(s))e.has(a)||(e.add(a),t(a))};ROOTS.forEach(t);const n=EDGES.filter(s=>e.has(s.source)&&e.has(s.target));return{nodes:NODES.filter(s=>e.has(s.id)).map(s=>({...s,label:s.title,muted:s.status==="rejected"})),edges:n}}function paintPath(e){const t=new Set,n=new Set;let o=e;for(;o&&!n.has(o);){n.add(o);const c=EDGES.find(d=>d.target===o);if(!c)break;t.add(c.source+">"+o),o=c.source}const{edges:s}=visible(),a=document.querySelector("#flow .pf-edges svg:not(.is-leaving)");s.forEach((c,d)=>a?.querySelector(`g.pele-edge[data-id="e${d}"]`)?.classList.toggle("is-path",t.has(c.source+">"+c.target)))}function summary(){const e=n=>NODES.filter(o=>o.status===n).length,t=(n,o,s)=>e(n)?`<span${o?` class="${o}"`:""}>${e(n)} ${s}</span>`:"";document.getElementById("sum").innerHTML=`<span>${NODES.length} cards</span>`+t("decided","is-ok","decided")+t("kept","is-brand","kept")+t("rejected","","ruled out")+t("unexplored","","not explored")+t("open","is-open","open")}function hint(e){const t=byId.get(e||FOCUS);if(!t){document.getElementById("hint").innerHTML="Click any card to see its path.";return}const n=!visible().nodes.some(o=>o.id===FOCUS);document.getElementById("hint").innerHTML=e&&e!==FOCUS?`<b>${esc(t.title)}</b> is ${esc((t.tag||STATE[t.status].label).toLowerCase())}. ${FOCUS?n?"Unfold its branch to get back to where you are.":`Click <b>${esc(byId.get(FOCUS).title)}</b> to go back.`:"Click empty canvas to clear."}`:`You are here: <b>${esc(t.title)}</b>. Click any card to see its path.`}document.getElementById("kind").textContent=MAP.kind||"Decisions",document.getElementById("crumb").textContent=MAP.title,document.getElementById("meta").textContent=MAP.meta||"",MAP.meta||(document.getElementById("meta").hidden=!0);const vp=document.getElementById("flow"),flow=createFlow(vp,{render:pele.render,card,fontFamily:getComputedStyle(document.body).fontFamily,direction:MAP.direction==="LR"?"LR":"TB",nodeGap:32,rankGap:64,readableZoom:.55,fitPadding:{top:32,right:32,bottom:72,left:32},onSelect:e=>{paintPath(e||FOCUS),hint(e)},onCamera:e=>{document.getElementById("zpct").textContent=Math.round(e*100)+"%"}});function render(){flow.update(visible()),paintPath(flow.selected||FOCUS)}vp.addEventListener("click",e=>{const t=e.target.closest("[data-fold]");if(!t)return;e.stopPropagation();const n=t.dataset.fold;collapsed.has(n)?collapsed.delete(n):collapsed.add(n),render();const o=new Set(visible().nodes.map(a=>a.id)),s=flow.selected||FOCUS;s&&!o.has(s)?flow.select(n):hint(flow.selected)},!0),vp.addEventListener("keydown",e=>{(e.key==="Enter"||e.key===" ")&&e.target.closest("[data-fold]")&&e.stopPropagation()},!0),vp.addEventListener("pointerdown",e=>{e.target.closest("[data-fold]")&&e.stopPropagation()},!0),document.getElementById("zin").onclick=()=>flow.zoomIn(),document.getElementById("zout").onclick=()=>flow.zoomOut(),document.getElementById("zpct").onclick=()=>flow.zoomTo(1),document.getElementById("zfit").onclick=()=>flow.fit(),summary(),render(),FOCUS?flow.select(FOCUS):hint("");
</script>
<!-- END decision-diagram.html -->
```
