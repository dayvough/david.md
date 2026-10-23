---
name: system-explainers
description: Show how a software system or one of its subsystems works as an animated 3D explainer, with models designed fresh for each system. Use when asked to explain, show, visualise or animate how a system, flow or request works.
---

# System explainers

A published page where a system is a little isometric diorama (a colour theme, blue by default,
with flat toon colours and dark ink outlines) and one request plays through it step by step: packets ride wires between
parts, parts react, callout cards explain, a trace panel logs each hop, and a toggle flips the
outcome. The page shell is fixed and designed. Your job is the scope, the story, new models for this system, and the `mountExplainer` block.

Needs the network for three.js (`cdn.jsdelivr.net/npm/three@0.170.0`, required) and Google Fonts (optional).

## 0. Pre-flight: pick the scope (every run, before drawing)

Systems contain subsystems, and the person often wants only one. Before building:

1. Work out the system from the conversation, repo or docs, and split it into 3–7 subsystems
   (for example *Edge* (DNS, CDN, load balancer), *Identity* (auth, users, roles), *Orders*
   (API, DB, cache), *Async* (queue, workers, email)). One line each: what it does, its parts.
2. Show that list and ask, as one multiple-choice question:
   - **Whole system**: each subsystem becomes one part; the story crosses them.
   - **One subsystem** (name each): its insides become the parts; at most two neighbours stay as
     plain parts at the edges, where the request enters and leaves.
   - **A series**: an overview scene plus one scene per subsystem, published separately.
3. Then ask which moment to trace, offering 2–3 concrete ones ("Ada signs in", "a payment fails").

Skip a question only when the person already answered it. Recommend an option each time.

## 1. Plan the story

One named person, one concrete request, 3–6 steps, 4–10 parts. Each step is one hop or one
decision, told in one or two plain sentences. Add one `params` toggle when an outcome can flip
(role editor/viewer, cache warm/cold, card valid/declined); branch inside `run` on `x.p`.

## 2. Design the models (new for every system)

Never reuse another explainer's models. Each system gets its own world and its own toys, so two
explainers never look alike. If earlier explainers are in the conversation or the project, pick a
different world and different shapes on purpose.

1. **Pick a world** that fits this system and is new here: a post office, a kitchen, a harbour,
   a rail yard, a theatre, a library, a greenhouse, a factory line, a high street of machines.
   Each part becomes something from that world whose job matches the role (a sorting office for
   a router, a ticket barrier for auth, a cold store for a cache, a crane for a deploy).
2. **Design each part** before coding it: a silhouette readable at a glance, 2–3 colours of its
   own, one moving piece that its action animates, and one detail that names its role (a screen,
   a sign with `plate`, a stamp, a dial). Keep parts 12–30 units across, base at y = 0.
3. **Build it** in the scene's `parts: { name(opts) { … } }` from the kit's shape tools, 6–25
   meshes each, and return `{ group, top, radius, actions, reset }` (`top` is where the callout
   points, `radius` where wires stop, `reset` puts moving pieces back).

Shape tools (all exported by the kit, all ink-outlined and shadowed): `rbox(w, h, d, r, color, x, y, z)`,
`cyl(r, h, color, x, y, z)`, `cone(r, h, color, x, y, z, seg, rTop)`, `sphere(r, color, x, y, z)`,
`lathe([[r, y], …], color)` for vases, domes and funnels, `tube([[x, y, z], …], r, color)` for pipes
and handles, `torus(r, t, color, arc)`, `extrude([[x, y], …], depth, color)` for any flat outline
(arrows, gears, roofs, bolts), `screen(w, h, draw)` for a canvas-drawn face with `userData.redraw`,
`plate(text, w, h, bg, fg)` for a name sign, `led(color, x, y, z)`, `group(...meshes)`. Animate with
`tween(ms, (k) => {…})` or `lerpTo(obj, key, to, ms)`; both are instant during replay. Set
`group.userData.lights = [leds]` to get `blink`. `THREE` is exported for anything else.

The kit's built-in `PARTS` (laptop, gateway, server, db, cards, signpost, balancer, cache, queue)
are only a fallback when the person asks for them. Hand-pick model colours per system too; the page
colours come from the theme (below), so models must read on both dark and light themes.

Place parts with `at: [x, z]` on the floor, roughly x −85…75 (flow left to right) and z −40…60,
30+ apart, with no long wires crossing. A node: `{ part, opts, at, rotate, title, icon, body, offset }`.
Icons: laptop gate lock db badge box key shield sign split server bolt belt gear clock.
`wires: [[a, b, { color }]]`, cables `C.cable` by default; pick wire colours per system.

## 3. Write the steps

`{ t, s, lede, callouts, accent, run }`. `t` is two to four words, `s` is "A → B". `lede`, callout bodies and `accent`
(`'ok'` or `'deny'`) may be functions of the params. `callouts: [[id, [dx, dy], title, body, icon]]`:
offset in px from the part's top, negative dy is up; one or two per step. `offset` on a node sets
its overview callout.

`run: async (x) => {}` gets `x.send(from, to, kind, label)` (needs a wire; kinds: `req` teal,
`data` blue, `tok` amber, `ok` green, `deny` red, `job` plum), `x.pulse(id, color)`, `x.part(id)`,
`x.at(id)`, `x.log(html)` with `x.who(name)` and spans `ok` `no` `tk`, `x.p`, `C`. Await each
hop so they play in order. Write `x.log` lines like a trace: `who → whom   what`. Keep packet
labels short (`GET /orders/42`, `JWT`, `403`). Jumping to a step replays earlier ones instantly,
so put all state changes in `run`.

## 4. Build and publish

Copy the page below, replace the sample scene (everything after the `// ===== Scene` line; its
models are an example of the method, not parts to reuse) and set `<title>`. The page imports the
engine from `./explainer-kit.js`, which ships with this skill at `assets/explainer-kit.js`. Copy
that file into the folder where you write the page, then:

- **Artifact tool available** (Claude Code, Claude projects): publish the page with the engine as a
  supporting file, `files: { "explainer-kit.js": "<folder>/explainer-kit.js" }`. To change it
  later, edit the page and publish the same path again so the link stays the same.
- **Local only**: serve the folder with `python3 -m http.server` and open the page from
  `http://localhost`. Browsers block module imports from `file://`, so a server is needed.

**Theme.** Set `theme` in `mountExplainer`: `'blue'` (default, dark navy), `'paper'` (cream),
`'blueprint'`, `'forest'`, `'plum'`, `'sand'`, `'graphite'`, or `'auto'` (paper by day, blue at
night). Use blue unless the person asks for another or wants to compare; to try one, add
`?theme=forest` to the URL. The page shows a swatch row so viewers can switch live (their pick is
remembered); `themePicker: false` hides it. Never restyle the page by hand; ask for a new theme in
the kit instead.

For a series, one page per scene. Never edit the engine, restyle the cards, or add DOM.

Before publishing: every part was designed for this system; every `send` has a wire; no callout covers the part it explains; every step
ends with a log line; the toggle changes something visible.

## The page

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>How a Card Payment Clears</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Semi+Condensed:wght@500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>html, body { background: #121828; }</style>
<script type="importmap">
{ "imports": {
  "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
  "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"
} }
</script>
</head>
<body>
<script type="module">
import { mountExplainer, C, THREE, rbox, cyl, sphere, cone, lathe, tube, torus, extrude, screen, plate, group, led, tween, lerpTo } from './explainer-kit.js';
// ===== Scene: everything below this line is yours to write. =====

// Models are designed for this system only. World: a little high street of money machines.
const ink = '#18213d';
const parts = {
  // a card reader with a live screen; a card drops into the slot
  reader() {
    const g = group(rbox(13, 4, 17, 1.4, '#2f3547'));
    const top = group(rbox(12, 1.4, 15, .6, '#454d66')); top.position.set(0, 4, 0); top.rotation.x = -.32; g.add(top);
    const lcd = screen(9, 5, (x, W, H) => { x.fillStyle = '#e7f3ea'; x.fillRect(0, 0, W, H); x.fillStyle = ink; x.font = `600 ${H * .34}px "JetBrains Mono"`; x.fillText('€42.00', W * .08, H * .45); });
    lcd.rotation.x = -Math.PI / 2; lcd.position.set(0, 1.45, -3); top.add(lcd);
    for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) top.add(rbox(2.2, .6, 1.6, .3, r === 2 && c === 2 ? C.green : '#d9dbe2', -3 + c * 3, 1.3, 2.2 + r * 2.2));
    const card = rbox(8, 11, .5, .6, C.teal, 0, 10, -7.2); card.rotation.x = -.32; g.add(card);
    const say = (text, color) => lcd.userData.redraw((x, W, H) => { x.fillStyle = color; x.fillRect(0, 0, W, H); x.fillStyle = ink; x.font = `600 ${H * .3}px "JetBrains Mono"`; x.fillText(text, W * .08, H * .45); });
    return { group: g, top: 16, radius: 11,
      actions: { insert: () => lerpTo(card.position, 'y', 3.5, 600), say },
      reset() { card.position.y = 10; say('€42.00', '#e7f3ea'); } };
  },
  // the processor: a mustard sorting machine with a hopper and a spinning wheel
  sorter() {
    const g = group(rbox(18, 11, 14, 1.2, '#e2a23b'), rbox(18.4, 1.2, 14.4, .5, '#c98a2a', 0, 11, 0));
    g.add(lathe([[1.6, 0], [1.6, 2], [6.5, 6], [7, 6.6]], '#c3c6ce', 0, 12, 0));
    const wheel = group(cyl(4.2, 1, '#2f3547').rotateX(Math.PI / 2));
    for (let i = 0; i < 6; i++) { const s = rbox(.8, 7.4, .6, .3, '#f9f2e5', 0, -3.7, 1.1); const arm = group(s); arm.rotation.z = i * Math.PI / 3; wheel.add(arm); }
    wheel.position.set(0, 5.5, 7); g.add(wheel);
    g.add(tube([[9, 4, 0], [13, 4, 0], [14, 1, 3]], 1, '#c3c6ce'));
    return { group: g, top: 19, radius: 12, actions: { whirr: () => tween(1200, (k) => { wheel.rotation.z = -k * Math.PI * 4; }, (t) => t) } };
  },
  // fraud check: a magnifying glass on a stand that sweeps side to side
  lens() {
    const g = group(cyl(5, 1.2, '#2f3547'), cyl(.8, 11, '#c3c6ce', 0, 1.2, 0, 16));
    const glass = group(torus(5, .9, '#c0652d'), cyl(4.4, .4, '#bfe3ea', 0, -.2, 0).rotateX(Math.PI / 2));
    glass.position.set(0, 17, 0); g.add(glass);
    return { group: g, top: 23, radius: 7,
      actions: { sweep: () => tween(1300, (k) => { glass.rotation.y = Math.sin(k * Math.PI * 2) * .7; }, (t) => t) } };
  },
  // the card network: a globe with an orbiting ring
  globe() {
    const g = group(cone(5, 3, '#2f3547'), cyl(.8, 5, '#c3c6ce', 0, 3, 0, 16));
    const ball = sphere(7.5, '#5aa9d6', 0, 15, 0); g.add(ball);
    const band = torus(7.6, .45, '#3fb36a'); band.rotation.x = Math.PI / 2; band.position.y = 15; g.add(band);
    const orbit = group(torus(11, .5, '#f2b13d'), sphere(1.4, '#f9f2e5', 11, 0, 0));
    orbit.position.y = 15; orbit.rotation.x = 1.2; g.add(orbit);
    return { group: g, top: 27, radius: 10, actions: { spin: () => tween(1400, (k) => { orbit.rotation.z = k * Math.PI * 2; }) } };
  },
  // the issuing bank: columns, a pediment and a vault door whose wheel turns
  bank() {
    const g = group(rbox(28, 2, 20, .6, '#ece0cc'), rbox(25, 1.2, 17, .5, '#dccdb4', 0, 2, 0));
    g.add(rbox(22, 11, 2, .5, '#d9c7ae', 0, 3, -4));
    for (const x of [-9.5, -3.2, 3.2, 9.5]) g.add(cyl(1.3, 11, '#f7f1e6', x, 3, 4, 18));
    g.add(rbox(27, 2, 18, .5, '#ece0cc', 0, 14, 0));
    const roof = extrude([[-13.5, 0], [13.5, 0], [0, 5]], 16, '#c59a68', .3); roof.position.set(0, 18.5, 0); g.add(roof);
    const door = cyl(3.6, 1, '#b9bcc4', 0, 8.5, -3).rotateX(Math.PI / 2); g.add(door);
    const handle = group(rbox(.6, 5, .6, .2, ink, 0, -2.5, 0), rbox(5, .6, .6, .2, ink, 0, -.3, 0));
    handle.position.set(0, 8.5, -1.6); g.add(handle);
    g.add(plate('Bank', 8, 2, '#f9f2e5', ink).translateY(16).translateZ(9.2));
    return { group: g, top: 24, radius: 15, actions: { turn: () => tween(900, (k) => { handle.rotation.z = k * Math.PI; }) }, reset() { handle.rotation.z = 0; } };
  },
};

mountExplainer({
  title: 'How a card payment clears',
  theme: 'blue',
  intro: 'Ada taps her card for a €42 coffee order. In about two seconds five machines agree whether the money exists. Press play to follow it.',
  partsLine: 'Five machines, one tap',
  parts,
  nodes: {
    reader: { part: 'reader', at: [-70, 10], title: 'Card reader', icon: 'laptop', body: 'Reads the card and shows the result.', offset: [-30, -150] },
    sorter: { part: 'sorter', at: [-30, 8], title: 'Processor', icon: 'gear', body: 'Takes every payment from the shop and routes it.', offset: [0, -190] },
    lens: { part: 'lens', at: [-26, -34], title: 'Fraud check', icon: 'shield', body: 'Scores how risky this payment looks.', offset: [-80, -110] },
    globe: { part: 'globe', at: [14, 14], title: 'Card network', icon: 'split', body: 'Knows which bank issued the card.', offset: [40, -200] },
    bank: { part: 'bank', at: [58, -8], rotate: -.3, title: 'Ada’s bank', icon: 'lock', body: 'Says yes or no. It holds the money.', offset: [80, -170] },
  },
  wires: [['reader', 'sorter'], ['sorter', 'lens', { color: C.plum }], ['sorter', 'globe'], ['globe', 'bank', { color: C.orange }]],
  params: [{ key: 'funds', label: 'Ada has', options: [['yes', 'Enough'], ['no', 'Too little']] }],
  steps: [
    { t: 'Tap', s: 'Reader → processor', lede: 'Ada’s card goes in. The reader sends the amount and a one-time code from the card chip.',
      callouts: [['reader', [-30, -150], 'Card reader', '<code>€42.00</code> and a chip code, never the PIN.']],
      run: async (x) => { await x.part('reader').insert(); x.log(`${x.who('reader')} → processor  €42.00 card ••4242`); await x.send('reader', 'sorter', 'req', '€42 · ••4242'); await Promise.all([x.pulse('sorter'), x.part('sorter').whirr()]); } },
    { t: 'Smell test', s: 'Processor ↔ fraud', lede: 'Before anything else, a fraud model checks the shop, the amount and Ada’s habits.',
      callouts: [['lens', [-80, -110], 'Fraud check', 'Score 0.04. Low risk, carry on.']],
      run: async (x) => { await x.send('sorter', 'lens', 'data', 'score?'); await Promise.all([x.pulse('lens'), x.part('lens').sweep()]); await x.send('lens', 'sorter', 'ok', 'low risk'); x.log(`${x.who('fraud')}  score 0.04 <span class="ok">✓</span>`); } },
    { t: 'Find the bank', s: 'Processor → network → bank', lede: 'The card number says which network to ask, and the network knows which bank issued the card.',
      callouts: [['globe', [40, -200], 'Card network', 'Routes by the first six digits of the card.']],
      run: async (x) => { await x.send('sorter', 'globe', 'req', 'auth €42'); await Promise.all([x.pulse('globe'), x.part('globe').spin()]); await x.send('globe', 'bank', 'req', 'auth €42'); x.log(`${x.who('network')} → bank  authorise €42.00`); } },
    { t: 'Bank decides', s: 'Bank → back the way it came',
      lede: (p) => p.funds === 'yes' ? 'The bank checks Ada’s balance, holds €42 and says yes.' : 'The bank checks Ada’s balance and says no. Nothing is held.',
      accent: (p) => p.funds === 'yes' ? 'ok' : 'deny',
      callouts: [['bank', [80, -170], 'Ada’s bank', (p) => p.funds === 'yes' ? 'Approved. €42 on hold until tonight.' : 'Declined: insufficient funds.']],
      run: async (x) => {
        const ok = x.p.funds === 'yes';
        await Promise.all([x.pulse('bank', ok ? C.green : C.red), x.part('bank').turn()]);
        await x.send('bank', 'globe', ok ? 'ok' : 'deny', ok ? 'approved' : 'declined');
        await x.send('globe', 'sorter', ok ? 'ok' : 'deny', ok ? 'approved' : 'declined');
        x.log(`${x.who('bank')}  ${ok ? '<span class="ok">approved</span> hold €42' : '<span class="no">declined</span> funds'}`);
      } },
    { t: 'Show Ada', s: 'Processor → reader', lede: (p) => p.funds === 'yes' ? 'The reader beeps green. The real money moves later, in the nightly settlement.' : 'The reader shows declined. Ada can try another card.',
      callouts: [['reader', [-30, -150], 'Card reader', (p) => p.funds === 'yes' ? 'Approved in 1.8 s.' : 'Declined.']],
      run: async (x) => {
        const ok = x.p.funds === 'yes';
        await x.send('sorter', 'reader', ok ? 'ok' : 'deny', ok ? 'approved' : 'declined');
        x.part('reader').say(ok ? 'APPROVED' : 'DECLINED', ok ? '#bfe8c9' : '#f5c4bb');
        await x.pulse('reader', ok ? C.green : C.red);
        x.log(`${x.who('reader')}  ${ok ? '<span class="ok">approved</span>' : '<span class="no">declined</span>'}`);
      } },
  ],
});
</script>
</body>
</html>
```
