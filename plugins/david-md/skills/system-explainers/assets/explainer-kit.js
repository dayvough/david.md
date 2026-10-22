// explainer-kit.js: animated 3D system explainers in the learn-arduino style.
// Toon shading + an ink outline pass + an isometric orthographic camera, with HTML callouts,
// packets riding wires between parts, and a step script that plays the story.
//
//   mountExplainer({
//     title, intro,                         // panel heading and the overview lede
//     nodes: { id: { part, at: [x, z], title, body, icon, rotate, opts } },
//     wires: [[from, to, { color }]],
//     params: [{ key, label, options: [[value, label]] }],
//     steps: [{ t, s, lede, callouts: [[id, [dx, dy], title?, body?, icon?]], accent?, run: async (x) => {} }],
//   })
//
// Inside run, x has: send(from, to, kind, label), pulse(id, color), part(id) (that part's
// actions), log(html), who(name), p (current params), wait(ms), C (palette).
// Jumping to a step replays earlier steps instantly, so part state and the trace stay right.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

const CSS = `:root {
  --bg: #f6eddd; --bg-deep: #efe3d1; --card: #f9f2e5; --card-soft: #faf4e9f2;
  --line: #cec0ad; --line-soft: #e2d7c7; --navy: #18213d; --ink: #4f535b; --muted: #696d74;
  --faint: #ada293; --teal: #1aa3a1; --teal-soft: #d7ece6; --amber: #e8962e; --green: #2f9e5b;
  --red: #d64a3a; --trace: #d3bea3; --track: #e3d8ca; --code-bg: #f8f0e3; --pill: #18213d; --pill-ink: #f9f2e5;
  --grid: #d9c7ae; --floor-shadow: #7a5532; --floor-shadow-a: .4;
  --sans: "Barlow", system-ui, sans-serif; --cond: "Barlow Semi Condensed", "Barlow", system-ui, sans-serif;
  --mono: "JetBrains Mono", ui-monospace, monospace;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #121828; --bg-deep: #0e1320; --card: #1a2134; --card-soft: #1a2134f2;
    --line: #34405b; --line-soft: #283249; --navy: #efe6d6; --ink: #c3c6cf; --muted: #9a9fab;
    --faint: #6d7486; --teal: #2bbcb9; --teal-soft: #173a3d; --amber: #f2a93a; --green: #45c27a;
    --red: #ef6a5a; --trace: #2c3650; --track: #283249; --code-bg: #151b2b; --pill: #efe6d6; --pill-ink: #121828;
    --grid: #2a3550; --floor-shadow: #000000; --floor-shadow-a: .5;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #121828; --bg-deep: #0e1320; --card: #1a2134; --card-soft: #1a2134f2;
  --line: #34405b; --line-soft: #283249; --navy: #efe6d6; --ink: #c3c6cf; --muted: #9a9fab;
  --faint: #6d7486; --teal: #2bbcb9; --teal-soft: #173a3d; --amber: #f2a93a; --green: #45c27a;
  --red: #ef6a5a; --trace: #2c3650; --track: #283249; --code-bg: #151b2b; --pill: #efe6d6; --pill-ink: #121828;
  --grid: #2a3550; --floor-shadow: #000000; --floor-shadow-a: .5;
  color-scheme: dark;
}

* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; }
body { background: var(--bg); color: var(--ink); font: 15px/1.45 var(--sans); overflow: hidden; }
button { font: inherit; color: inherit; }

.app { position: relative; height: 100vh; height: 100dvh; display: grid; grid-template-columns: minmax(0, 1fr) 380px; }
.frame { position: absolute; inset: 0; pointer-events: none; }
.frame path { fill: none; stroke: var(--trace); stroke-width: 1.4; }
.frame circle { fill: var(--bg); stroke: var(--trace); stroke-width: 1.4; }

/* Stage */
.stage { position: relative; min-width: 0; overflow: hidden; touch-action: none; cursor: grab; }
.stage[data-drag="1"] { cursor: grabbing; }
.stage canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
.leaders, .tags, .callouts { position: absolute; inset: 0; pointer-events: none; }
.leaders { width: 100%; height: 100%; overflow: visible; }
.leaders path { fill: none; stroke: var(--navy); stroke-width: 1.2; stroke-dasharray: 3 3; opacity: .7; }
.leaders circle.ring { fill: var(--card); stroke: var(--teal); stroke-width: 2.4; }
.leaders circle.halo { fill: var(--teal); opacity: .18; }

.brand { position: absolute; left: 28px; top: 22px; display: flex; align-items: center; gap: 16px; z-index: 2; pointer-events: none; }
.brand svg { width: 52px; height: 52px; }
.brand svg .s { fill: none; stroke: var(--navy); stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
.brand svg .f { fill: var(--teal); }
.brand-rule { width: 1px; height: 40px; background: var(--line); }
.brand h1 { margin: 0; font: 600 26px/1 var(--cond); letter-spacing: .14em; color: var(--navy); text-transform: uppercase; }
.brand p { margin: 6px 0 0; font: 500 13px/1 var(--cond); letter-spacing: .2em; color: var(--muted); text-transform: uppercase; }
.brand p i { font-style: normal; color: var(--faint); margin: 0 .3em; }

.callout { position: absolute; left: 0; top: 0; width: 226px; padding: 12px 14px 12px 12px; display: grid; grid-template-columns: 30px 1fr; gap: 10px;
  background: var(--card-soft); border: 1px solid var(--line); border-radius: 4px; box-shadow: 0 1px 0 var(--line-soft), 0 10px 24px -18px #3a2a1466;
  opacity: 0; transform: translate3d(0, 6px, 0); transition: opacity .35s ease, transform .35s ease; will-change: transform; }
.callout.on { opacity: 1; }
.callout svg { width: 26px; height: 26px; margin-top: 1px; fill: none; stroke: var(--navy); stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }
.callout b { display: block; font: 600 14px/1.15 var(--cond); letter-spacing: .07em; text-transform: uppercase; color: var(--navy); }
.stage.compact .step0 span { display: none; }
.stage.compact .step0 { grid-template-columns: 18px 1fr; width: auto; padding: 7px 10px; } .stage.compact .step0 svg { width: 18px; height: 18px; }
.callout span { display: block; margin-top: 4px; font-size: 13px; line-height: 1.35; color: var(--ink); }
.callout code, .panel code { font: 500 11.5px/1.5 var(--mono); color: var(--navy); background: var(--code-bg); border: 1px solid var(--line-soft); border-radius: 3px; padding: 0 4px; }
.callout pre { margin: 6px 0 0; padding: 6px 8px; font: 500 11px/1.55 var(--mono); color: var(--navy); background: var(--code-bg); border: 1px solid var(--line-soft); border-radius: 3px; white-space: pre; }
.callout .k { color: #c0652d; }
.callout.accent-ok { border-color: color-mix(in srgb, var(--green) 55%, var(--line)); }
.callout.accent-deny { border-color: color-mix(in srgb, var(--red) 60%, var(--line)); }

.tag { position: absolute; left: 0; top: 0; padding: 3px 8px; border-radius: 4px; background: var(--pill); color: var(--pill-ink);
  font: 500 11px/1.3 var(--mono); white-space: nowrap; transform: translate(-50%, -100%); opacity: 0; transition: opacity .2s; }
.tag.on { opacity: 1; }
.tag::before { content: ""; display: inline-block; width: 7px; height: 7px; border-radius: 2px; margin-right: 6px; background: var(--c, var(--teal)); vertical-align: 0; }

.player { position: absolute; left: 50%; bottom: 22px; transform: translateX(-50%); display: flex; align-items: center; gap: 4px; padding: 5px;
  background: var(--card); border: 1px solid var(--line); border-radius: 6px; box-shadow: 0 1px 0 var(--line-soft); z-index: 3; }
.player button { width: 34px; height: 32px; border: 0; background: none; border-radius: 4px; display: grid; place-items: center; cursor: pointer; }
.player button:hover { background: var(--bg-deep); }
.player button svg { width: 18px; height: 18px; fill: none; stroke: var(--navy); stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.player button svg .fill { fill: var(--navy); stroke: none; }
.player .sep { width: 1px; height: 20px; background: var(--line); margin: 0 4px; }
.player .play { background: var(--navy); }
.player .play:hover { background: var(--navy); opacity: .9; }
.player .play svg .fill { fill: var(--card); }
.player .play svg { stroke: var(--card); }
.seg { display: flex; gap: 2px; padding: 2px; background: var(--bg-deep); border-radius: 4px; }
.seg button { width: auto; height: 28px; padding: 0 10px; font: 600 12px/1 var(--cond); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.seg button[aria-pressed="true"] { background: var(--card); color: var(--navy); box-shadow: 0 0 0 1px var(--line); }
.seg-label { font: 600 11px/1 var(--cond); letter-spacing: .12em; text-transform: uppercase; color: var(--faint); margin: 0 4px 0 6px; }
.hint { position: absolute; left: 50%; bottom: 72px; transform: translateX(-50%); font: 500 11px/1 var(--cond); letter-spacing: .06em; color: var(--faint); white-space: nowrap; pointer-events: none; }

/* Panel */
.panel { position: relative; z-index: 2; display: flex; flex-direction: column; gap: 14px; padding: 22px 22px 22px 0; min-height: 0; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 6px; box-shadow: 0 1px 0 var(--line-soft); }
.intro { padding: 18px 20px; }
.eyebrow { font: 600 12px/1 var(--cond); letter-spacing: .16em; text-transform: uppercase; color: var(--teal); }
.intro h2 { margin: 8px 0 8px; font: 600 24px/1.05 var(--cond); letter-spacing: .06em; text-transform: uppercase; color: var(--navy); }
.intro p { margin: 0; font-size: 14.5px; color: var(--ink); min-height: 4.4em; }
.steps { list-style: none; margin: 0; padding: 8px; overflow: auto; }
.steps li button { width: 100%; display: grid; grid-template-columns: 28px 1fr; gap: 12px; align-items: center; text-align: left; padding: 8px 10px; border: 0; background: none; border-radius: 4px; cursor: pointer; }
.steps li button:hover { background: var(--bg-deep); }
.steps .n { width: 28px; height: 28px; display: grid; place-items: center; border: 1px solid var(--line); border-radius: 4px; background: var(--card); font: 600 13px/1 var(--cond); color: var(--navy); }
.steps .t { font: 600 14px/1.1 var(--cond); letter-spacing: .07em; text-transform: uppercase; color: var(--navy); }
.steps .s { display: block; margin-top: 2px; font-size: 12.5px; color: var(--muted); }
.steps li.done .n { background: var(--teal); border-color: var(--teal); color: var(--card); }
.steps li.on button { background: var(--teal-soft); }
.steps li.on .n { border-color: var(--teal); color: var(--teal); }
.monitor { display: flex; flex-direction: column; min-height: 150px; flex: 1; overflow: hidden; }
.monitor-head { display: flex; align-items: center; gap: 8px; padding: 10px 14px; border-bottom: 1px solid var(--line-soft); font: 600 12px/1 var(--cond); letter-spacing: .12em; text-transform: uppercase; color: var(--navy); }
.monitor-head .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--teal); box-shadow: 0 0 0 3px var(--teal-soft); }
.monitor-head .st { color: var(--faint); font-weight: 500; }
.log { flex: 1; margin: 0; padding: 10px 14px; overflow: auto; font: 400 12px/1.7 var(--mono); color: var(--ink); background: var(--code-bg); border-radius: 0 0 6px 6px; }
.log div { white-space: pre-wrap; animation: in .3s ease; }
.log .who { color: var(--navy); font-weight: 500; }
.log .ok { color: var(--green); }
.log .no { color: var(--red); }
.log .tk { color: var(--amber); }
@keyframes in { from { opacity: 0; transform: translateY(3px); } }

@media (max-width: 900px) {
  body { overflow: auto; }
  .app { grid-template-columns: 1fr; height: auto; }
  .stage { height: 60vh; min-height: 420px; }
  .panel { padding: 0 16px 24px; }
  .brand { left: 16px; top: 14px; } .brand svg { width: 40px; height: 40px; } .brand h1 { font-size: 20px; } .brand p { font-size: 11px; }
  .callout { width: 180px; padding: 9px 10px; grid-template-columns: 22px 1fr; gap: 8px; } .callout svg { width: 20px; height: 20px; }
  .callout span { font-size: 12px; } .hint { display: none; } .player { bottom: 12px; }
  .seg-label { display: none; }
}
@media (prefers-reduced-motion: reduce) { .callout, .tag { transition: none; } }`;

const NO_INK = 1; // layer for floor, shadow and rings: drawn, but never outlined
const DEG = Math.PI / 180;

/* ---------- Ink pass: toon colour + edges found from normals and depth ---------- */
const INK_FRAG = `
  uniform sampler2D tColor; uniform sampler2D tNormal; uniform sampler2D tDepth;
  uniform vec2 texel; uniform float thickness; uniform float depthRange;
  uniform float depthThreshold; uniform float normalThreshold; uniform vec3 lineColor;
  varying vec2 vUv;
  float depthAt(vec2 uv) { return texture2D(tDepth, uv).r * depthRange; }
  float edgePair(vec2 uv, vec2 off, float d0, vec4 n0) {
    vec4 na = texture2D(tNormal, uv + off), nb = texture2D(tNormal, uv - off);
    float da = depthAt(uv + off), db = depthAt(uv - off);
    float e = max(abs(na.a - n0.a), abs(nb.a - n0.a));
    if (n0.a > 0.5) {
      float lap = abs(da + db - 2.0 * d0);
      float sa = na.a > 0.5 ? abs(da - d0) : 0.0, sb = nb.a > 0.5 ? abs(db - d0) : 0.0;
      e = max(e, smoothstep(depthThreshold, depthThreshold * 2.0, min(lap, max(sa, sb) * 2.0)));
      vec3 c = n0.xyz * 2.0 - 1.0;
      float ca = na.a > 0.5 ? 1.0 - dot(c, na.xyz * 2.0 - 1.0) : 0.0;
      float cb = nb.a > 0.5 ? 1.0 - dot(c, nb.xyz * 2.0 - 1.0) : 0.0;
      e = max(e, 0.9 * smoothstep(normalThreshold, normalThreshold * 2.2, max(ca, cb)));
    }
    return e;
  }
  void main() {
    vec4 col = texture2D(tColor, vUv); vec4 n0 = texture2D(tNormal, vUv); float d0 = depthAt(vUv);
    vec2 o = texel * thickness; float e = 0.0;
    e = max(e, edgePair(vUv, vec2(o.x, 0.0), d0, n0));
    e = max(e, edgePair(vUv, vec2(0.0, o.y), d0, n0));
    e = max(e, edgePair(vUv, o * 0.7071, d0, n0));
    e = max(e, edgePair(vUv, vec2(o.x, -o.y) * 0.7071, d0, n0));
    vec2 o2 = o * 1.5; float e2 = 0.0;
    e2 = max(e2, edgePair(vUv, vec2(o2.x, 0.0), d0, n0));
    e2 = max(e2, edgePair(vUv, vec2(0.0, o2.y), d0, n0));
    e = max(e, e2 * 0.35);
    vec3 rgb = col.a > 0.0 ? col.rgb / col.a : vec3(0.0);
    float a = col.a, outA = a + e * (1.0 - a);
    gl_FragColor = vec4((rgb * a * (1.0 - e) + lineColor * e) / max(outA, 1e-4), outA);
    #include <colorspace_fragment>
    gl_FragColor.rgb *= gl_FragColor.a;
  }`;

class InkComposer {
  constructor(renderer, { lineColor = '#141a2c', thickness = 1.3 } = {}) {
    this.renderer = renderer;
    this.color = new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType, samples: 4 });
    this.normal = new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType, depthTexture: new THREE.DepthTexture(1, 1, THREE.FloatType) });
    this.normalMat = new THREE.MeshNormalMaterial();
    this.mat = new THREE.ShaderMaterial({
      vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }',
      fragmentShader: INK_FRAG,
      uniforms: {
        tColor: { value: this.color.texture }, tNormal: { value: this.normal.texture }, tDepth: { value: this.normal.depthTexture },
        texel: { value: new THREE.Vector2() }, thickness: { value: thickness }, depthRange: { value: 1 },
        depthThreshold: { value: .35 }, normalThreshold: { value: .22 }, lineColor: { value: new THREE.Color(lineColor) },
      },
      depthTest: false, depthWrite: false, transparent: true, blending: THREE.NoBlending,
    });
    this.quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.mat);
    this.quad.frustumCulled = false;
    this.quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  }
  setSize(w, h, dpr) {
    const W = Math.max(1, Math.round(w * dpr)), H = Math.max(1, Math.round(h * dpr));
    this.color.setSize(W, H); this.normal.setSize(W, H);
    this.mat.uniforms.texel.value.set(1 / W, 1 / H);
    this.mat.uniforms.thickness.value = 1.3 * Math.min(dpr, 2) / 1.5 + .4;
  }
  render(scene, camera) {
    const r = this.renderer;
    this.mat.uniforms.depthRange.value = camera.far - camera.near;
    r.setClearColor(0, 0);
    camera.layers.enable(NO_INK);
    r.setRenderTarget(this.color); r.clear(); r.render(scene, camera);
    r.shadowMap.needsUpdate = false;
    camera.layers.disable(NO_INK);
    scene.overrideMaterial = this.normalMat;
    r.setRenderTarget(this.normal); r.clear(); r.render(scene, camera);
    scene.overrideMaterial = null;
    r.setRenderTarget(null); r.clear(); r.render(this.quad, this.quadCam);
  }
}

/* ---------- Palette, materials, shape helpers ---------- */
export const C = {
  cable: '#4a5371', navy: '#2b3866', blue: '#3f5196', blue2: '#4c62ad', bone: '#ece0cc', bone2: '#dccdb4',
  metal: '#c3c6ce', grey: '#8f93a0', dark: '#30364a', teal: '#1aa3a1', amber: '#f2b13d', red: '#e2553f',
  green: '#3fb36a', orange: '#e8823a', wood: '#d9b58a', wood2: '#c59a68', card: '#d9a46a', tape: '#c08a4e',
  white: '#f7f1e6', plum: '#8a5fb0', sky: '#7b8fd1',
};
const ramp = new THREE.DataTexture(new Uint8Array([120, 120, 120, 255, 200, 200, 200, 255, 255, 255, 255, 255]), 3, 1);
ramp.minFilter = ramp.magFilter = THREE.NearestFilter; ramp.needsUpdate = true;
const mats = new Map();
export const toon = (color, emissive) => {
  const k = color + (emissive || '');
  if (!mats.has(k)) mats.set(k, new THREE.MeshToonMaterial({ color, gradientMap: ramp, emissive: emissive || '#000000', emissiveIntensity: emissive ? .55 : 0 }));
  return mats.get(k);
};
export function mesh(geo, mat, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = true; return m;
}
export function rbox(w, h, d, r, color, x = 0, y = 0, z = 0) {
  const g = new RoundedBoxGeometry(w, h, d, 3, Math.min(r, w / 2, h / 2, d / 2) * .999);
  g.translate(0, h / 2, 0);
  return mesh(g, toon(color), x, y, z);
}
export function cyl(r, h, color, x = 0, y = 0, z = 0, seg = 40) {
  const g = new THREE.CylinderGeometry(r, r, h, seg); g.translate(0, h / 2, 0);
  return mesh(g, toon(color), x, y, z);
}
export function extrude(points, depth, color, bevel = .3) {
  const shape = new THREE.Shape(points.map(([x, y]) => new THREE.Vector2(x, y)));
  const g = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: true, bevelSize: bevel, bevelThickness: bevel, bevelSegments: 2 });
  g.center();
  return mesh(g, toon(color));
}
export const led = (color, x, y, z, r = .55) => mesh(new THREE.SphereGeometry(r, 12, 8), toon(color, color), x, y, z);

/* ---------- Shape tools for designing new models ----------
   Every builder returns a mesh that casts a shadow and gets ink outlines. Sizes are in floor
   units (a part is about 15-30 across). Group them, then return { group, top, radius }. */
export const sphere = (r, color, x = 0, y = 0, z = 0) => mesh(new THREE.SphereGeometry(r, 24, 16), toon(color), x, y, z);
export function cone(r, h, color, x = 0, y = 0, z = 0, seg = 32, rTop = 0) {
  const g = new THREE.CylinderGeometry(rTop, r, h, seg); g.translate(0, h / 2, 0);
  return mesh(g, toon(color), x, y, z);
}
// profile: [[radius, y], ...] from bottom to top, spun around the y axis (vases, bells, domes)
export function lathe(profile, color, x = 0, y = 0, z = 0, seg = 40) {
  const m = toon(color).clone(); m.side = THREE.DoubleSide; // lathes are open shells
  return mesh(new THREE.LatheGeometry(profile.map(([r, h]) => new THREE.Vector2(r, h)), seg), m, x, y, z);
}
// a bent rod through points [[x, y, z], ...] (pipes, handles, antennas, hoses)
export function tube(points, r, color, closed = false) {
  const c = new THREE.CatmullRomCurve3(points.map((q) => new THREE.Vector3(...q)), closed, 'centripetal');
  return mesh(new THREE.TubeGeometry(c, Math.max(24, points.length * 12), r, 10, closed), toon(color));
}
export const torus = (r, t, color, arc = Math.PI * 2) => mesh(new THREE.TorusGeometry(r, t, 12, 36, arc), toon(color));
// a flat picture drawn with canvas 2D: draw(g, w, h) in pixels; the plane is w x h units, facing +z
export function screen(w, h, draw, px = 64) {
  const c = document.createElement('canvas'); c.width = Math.round(w * px); c.height = Math.round(h * px);
  draw(c.getContext('2d'), c.width, c.height);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t, toneMapped: false }));
  m.userData.redraw = (fn) => { fn(c.getContext('2d'), c.width, c.height); t.needsUpdate = true; };
  return m;
}
// a sign with a word on it (name plates, labels on boxes), facing +z
export function plate(text, w, h, bg = '#f9f2e5', fg = '#18213d', depth = .5) {
  const g = new THREE.Group();
  g.add(rbox(w, h, depth, Math.min(w, h) * .15, bg));
  const face = screen(w * .9, h * .8, (x, W, H) => {
    x.fillStyle = bg; x.fillRect(0, 0, W, H); x.fillStyle = fg;
    x.font = `600 ${Math.round(H * .62)}px "Barlow Semi Condensed", sans-serif`; x.textAlign = 'center'; x.textBaseline = 'middle';
    x.fillText(text.toUpperCase(), W / 2, H / 2);
  });
  face.position.set(0, h / 2, depth / 2 + .02); g.add(face);
  return g;
}
export const group = (...kids) => { const g = new THREE.Group(); kids.forEach((k) => g.add(k)); return g; };

/* ---------- Tween clock (instant mode replays steps without animating) ---------- */
const tweens = new Set();
let speed = 1, instant = false;
const ease = (t) => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
export function tween(ms, fn, easing = ease) {
  if (instant) { fn(1, 1); return Promise.resolve(); }
  return new Promise((done) => tweens.add({ t0: performance.now(), ms: ms * speed, fn, easing, done }));
}
function tick(now) {
  for (const tw of tweens) {
    const t = Math.min(1, (now - tw.t0) / Math.max(1, tw.ms));
    tw.fn(tw.easing(t), t);
    if (t >= 1) { tweens.delete(tw); tw.done(); }
  }
}
const wait = (ms) => instant ? Promise.resolve() : new Promise((r) => setTimeout(r, ms * speed));
export const lerpTo = (obj, key, to, ms = 450) => { const from = obj[key]; return tween(ms, (k) => { obj[key] = from + (to - from) * k; }); };

/* ---------- Part library ----------
   Each part returns { group, top, radius, actions?, reset? }. top is where a callout points,
   radius is how far wires stop short of the centre. */
function screenTexture({ title = 'SIGN IN', fields = ['ada@acme.co', '••••••••'], button = 'CONTINUE' } = {}) {
  const c = document.createElement('canvas'); c.width = 512; c.height = 300;
  const g = c.getContext('2d');
  g.fillStyle = '#f9f2e5'; g.fillRect(0, 0, 512, 300);
  g.fillStyle = '#18213d'; g.font = '600 34px "Barlow Semi Condensed", sans-serif'; g.fillText(title, 150, 72);
  fields.forEach((txt, i) => {
    const y = 96 + i * 52;
    g.strokeStyle = '#cec0ad'; g.lineWidth = 3; g.beginPath(); g.roundRect(150, y, 212, 40, 6); g.stroke();
    g.fillStyle = '#696d74'; g.font = '22px "JetBrains Mono", monospace'; g.fillText(txt, 164, y + 28);
  });
  g.fillStyle = '#1aa3a1'; g.beginPath(); g.roundRect(150, 204, 212, 42, 6); g.fill();
  g.fillStyle = '#f9f2e5'; g.font = '600 22px "Barlow Semi Condensed", sans-serif';
  g.fillText(button, 256 - g.measureText(button).width / 2, 232);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}

function server(top, { body = C.blue, alt = C.blue2, leds = C.teal, tiers = 3 } = {}) {
  const g = new THREE.Group(), lights = [];
  for (let i = 0; i < tiers; i++) {
    g.add(rbox(18, 5.6, 16, .9, i % 2 ? alt : body, 0, i * 6.2, 0));
    for (let j = 0; j < 3; j++) { const l = led(leds, -6 + j * 1.8, i * 6.2 + 2.8, 8.05); g.add(l); lights.push(l); }
    g.add(rbox(7, .5, .4, .2, C.navy, 4, i * 6.2 + 2.55, 8.05));
  }
  return { g, lights, h: tiers * 6.2 - .6 };
}

export const PARTS = {
  laptop(o = {}) {
    const g = new THREE.Group();
    g.add(rbox(26, 1.8, 18, .8, C.metal));
    g.add(rbox(21, .5, 8, .25, C.dark, 0, 1.6, -2.4));
    g.add(rbox(8, .3, 4.5, .25, C.bone2, 0, 1.65, 5.2));
    const lid = new THREE.Group(); lid.position.set(0, 1.4, -8.4); lid.rotation.x = -.22;
    lid.add(rbox(26, 17, 1.3, .7, C.metal));
    const screen = new THREE.Mesh(new THREE.PlaneGeometry(22.6, 13.4), new THREE.MeshBasicMaterial({ map: screenTexture(o.screen), toneMapped: false }));
    screen.position.set(0, 8.9, .66); lid.add(screen);
    g.add(lid);
    return { group: g, top: 19, radius: 13 };
  },

  gateway() {
    const g = new THREE.Group();
    g.add(rbox(28, 2.2, 16, .8, C.bone));
    g.add(rbox(4.4, 14, 4.4, .9, C.navy, -10.5, 2, 0));
    g.add(rbox(4.4, 14, 4.4, .9, C.navy, 10.5, 2, 0));
    g.add(rbox(27, 3.6, 5.4, 1, C.blue, 0, 15.6, 0));
    const strip = mesh(new RoundedBoxGeometry(19, 1.1, .6, 2, .3), toon(C.teal, C.teal), 0, 17.4, 2.75);
    g.add(strip);
    const arm = new THREE.Group(); arm.position.set(-8.2, 7.2, 0);
    for (let i = 0; i < 6; i++) arm.add(rbox(3, 1.4, 1.4, .5, i % 2 ? C.white : C.red, 1.6 + i * 2.95, -.7, 0));
    g.add(arm);
    return {
      group: g, top: 19.5, radius: 15,
      actions: {
        open: () => lerpTo(arm.rotation, 'z', 1.35, 520),
        close: () => lerpTo(arm.rotation, 'z', 0, 520),
        light: (color) => { strip.material = toon(color, color); },
      },
      reset() { arm.rotation.z = 0; strip.material = toon(C.teal, C.teal); },
    };
  },

  // a server stack; opts.top = 'lock' | 'parcels' | 'gear' | null
  server(o = {}) {
    const { g, lights, h } = server(null, { tiers: o.tiers ?? 3, body: o.body, alt: o.alt, leds: o.leds });
    const actions = {}, resets = [];
    let top = h + 2;
    if (o.top === 'lock') {
      const lock = new THREE.Group(); lock.position.set(0, h + .6, 0);
      lock.add(rbox(8.4, 6.6, 3.6, 1, C.amber));
      lock.add(cyl(.9, .5, C.dark, 0, 3.3, 1.7).rotateX(Math.PI / 2));
      const shackle = new THREE.Mesh(new THREE.TorusGeometry(2.6, .75, 12, 28, Math.PI), toon(C.metal));
      shackle.castShadow = true; shackle.position.set(0, 6.6, 0); lock.add(shackle);
      for (const x of [-2.6, 2.6]) shackle.add(cyl(.75, 1.6, C.metal, x, -1.2, 0, 16));
      g.add(lock);
      actions.unlock = (open = true) => tween(480, (k) => {
        const from = shackle.userData.y ?? 6.6, to = open ? 9.4 : 6.6;
        shackle.position.y = from + (to - from) * k; shackle.rotation.y = (shackle.position.y - 6.6) / 2.8 * .9;
        if (k === 1) shackle.userData.y = to;
      });
      resets.push(() => { shackle.position.y = 6.6; shackle.rotation.y = 0; shackle.userData.y = 6.6; });
      top = h + 10;
    } else if (o.top === 'parcels') {
      const b1 = new THREE.Group(); b1.position.set(-3.2, h + .6, -1);
      b1.add(rbox(9, 5.5, 8, .4, C.card)); b1.add(rbox(9.1, .3, 1.6, .1, C.tape, 0, 5.4, 0));
      const b2 = new THREE.Group(); b2.position.set(4.6, h + .6, 2.4); b2.rotation.y = .3;
      b2.add(rbox(6, 4, 6, .4, C.card)); b2.add(rbox(1.4, .3, 6.1, .1, C.tape, 0, 3.9, 0));
      g.add(b1, b2); top = h + 7;
    } else if (o.top === 'gear') {
      const teeth = 10, pts = [];
      for (let i = 0; i < teeth * 4; i++) {
        const a = i / (teeth * 4) * Math.PI * 2, r = (i % 4 < 2) ? 5.6 : 4.4;
        pts.push([Math.cos(a) * r, Math.sin(a) * r]);
      }
      const gear = new THREE.Group(); gear.position.set(0, h + 2.2, 0);
      const body = extrude(pts, 1.6, C.amber, .25); body.rotation.x = Math.PI / 2; gear.add(body);
      gear.add(cyl(1.8, 2.4, C.dark, 0, -1.2, 0, 20));
      const holder = cyl(1.2, 2.2, C.metal, 0, h + .6, 0, 16);
      g.add(holder, gear); top = h + 5;
      actions.spin = (ms = 1600) => tween(ms, (k) => { gear.rotation.y = k * Math.PI * 1.5; }, (t) => t);
    }
    const glow = (color) => lights.forEach((l) => { l.material = toon(color, color); });
    if (o.status === 'down') { glow(C.red); }
    actions.lights = glow;
    actions.blink = (on) => { g.userData.blink = on; };
    g.userData.lights = lights;
    return {
      group: g, top, radius: 12, actions,
      reset() { resets.forEach((f) => f()); glow(o.status === 'down' ? C.red : (o.leds || C.teal)); g.userData.blink = false; },
    };
  },

  db() {
    const g = new THREE.Group();
    for (let i = 0; i < 3; i++) {
      g.add(cyl(9, 4.2, i % 2 ? C.blue2 : C.blue, 0, i * 4.9));
      g.add(cyl(9.15, .7, C.navy, 0, i * 4.9 + 4.2));
    }
    g.add(cyl(6, .4, C.bone, 0, 14.75));
    return { group: g, top: 17, radius: 10 };
  },

  // badge cards in a holder; opts.cards = [[name, color], ...]
  cards(o = {}) {
    const list = o.cards || [['admin', C.red], ['editor', C.teal], ['viewer', C.amber]];
    const g = new THREE.Group();
    g.add(rbox(24, 2.4, 11, .8, C.wood));
    g.add(rbox(22, 1, 3, .4, C.wood2, 0, 2.2, 0));
    const cards = {};
    list.forEach(([name, color], i) => {
      const x = (i - (list.length - 1) / 2) * 7.2;
      const card = new THREE.Group(); card.position.set(x, 2.6, 0); card.rotation.z = -x * .028;
      card.add(rbox(6.6, 10, .9, .6, color));
      const head = mesh(new THREE.CylinderGeometry(1.5, 1.5, .3, 24), toon(C.white), 0, 6.6, .55); head.rotation.x = Math.PI / 2; card.add(head);
      card.add(rbox(4, 1.4, .3, .3, C.white, 0, 3.4, .45));
      card.add(rbox(4, .6, .3, .2, C.white, 0, 2, .45));
      g.add(card); cards[name] = card;
    });
    return {
      group: g, top: 16, radius: 13,
      actions: { raise: (name, up = true) => lerpTo(cards[name].position, 'y', up ? 10.5 : 2.6) },
      reset() { for (const c of Object.values(cards)) c.position.y = 2.6; },
    };
  },

  // a signpost: the DNS address book of the street
  signpost(o = {}) {
    const g = new THREE.Group();
    g.add(cyl(6, 1.8, C.bone2));
    g.add(cyl(1.1, 30, C.metal, 0, 1.6, 0, 16));
    g.add(cyl(1.7, 1.4, C.amber, 0, 31.4, 0, 16));
    const boards = [];
    // angles chosen so the boards read side-on from the default camera
    (o.boards || [[C.teal, .5], [C.blue2, 3.7], [C.orange, .95]]).forEach(([color, a], i) => {
      const b = new THREE.Group(); b.position.y = 26.5 - i * 6.2; b.rotation.y = a;
      b.add(extrude([[-.5, -2.1], [11, -2.1], [14, 0], [11, 2.1], [-.5, 2.1]], .9, color, .3));
      b.children[0].position.x = 7;
      g.add(b); boards.push(b);
    });
    return {
      group: g, top: 33, radius: 8,
      actions: { point: (i) => tween(700, (k) => { boards[i].children[0].position.x = 7 + Math.sin(k * Math.PI) * 2.2; }, (t) => t) },
    };
  },

  // a turret that aims at the server it picks
  balancer() {
    const g = new THREE.Group();
    g.add(rbox(20, 3, 20, 1.2, C.bone));
    g.add(cyl(7.5, 5, C.navy, 0, 3));
    g.add(cyl(7.8, .8, C.teal, 0, 7.6));
    const head = new THREE.Group(); head.position.y = 8.4;
    head.add(cyl(5.2, 2.6, C.blue2, 0, 0, 0, 32));
    const arrow = extrude([[0, -1.3], [7, -1.3], [7, -3], [12, 0], [7, 3], [7, 1.3], [0, 1.3]], 1.4, C.amber, .25);
    arrow.rotation.x = -Math.PI / 2; arrow.position.set(6, 1.4, 0);
    head.add(arrow);
    g.add(head);
    return {
      group: g, top: 13, radius: 12,
      actions: {
        aim(at) { // at: [x, z] world point
          const p = g.position, to = Math.atan2(-(at[1] - p.z), at[0] - p.x);
          const from = head.rotation.y;
          let d = to - from; d = Math.atan2(Math.sin(d), Math.cos(d));
          return tween(600, (k) => { head.rotation.y = from + d * k; });
        },
      },
      reset() { head.rotation.y = 0; },
    };
  },

  // a small fast shelf with a bolt on top
  cache() {
    const g = new THREE.Group();
    g.add(rbox(16, 7, 13, 1, C.red));
    g.add(rbox(16.4, 1, 13.4, .5, '#b8402f', 0, 3.2, 0));
    for (let j = 0; j < 2; j++) g.add(rbox(10, .5, .4, .2, '#8e3226', 0, 1.6 + j * 3.4, 6.6));
    const bolt = extrude([[1, 6], [-3, 0], [0, 0], [-1.5, -6], [3.5, 1], [.5, 1], [2.5, 6]], 1.4, C.amber, .25);
    bolt.position.set(0, 12, 0);
    g.add(bolt);
    return { group: g, top: 18, radius: 10, actions: { zap: () => tween(600, (k) => { bolt.rotation.y = k * Math.PI * 2; }) }, reset() { bolt.rotation.y = 0; } };
  },

  // a conveyor belt; jobs ride along it
  queue(o = {}) {
    const len = o.length || 30, g = new THREE.Group();
    g.add(rbox(len, 3, 9, 1, C.dark));
    g.add(rbox(len - 1, .6, 7.6, .3, C.grey, 0, 3, 0));
    for (const x of [-len / 2 + 1.8, len / 2 - 1.8]) g.add(cyl(1.8, 9.4, C.metal, x, 3, -4.7, 18).rotateX(Math.PI / 2));
    for (const x of [-len / 2 + 3, len / 2 - 3]) for (const z of [-3, 3]) g.add(rbox(1.6, 2, 1.6, .4, C.navy, x, -2, z));
    g.children.forEach((m) => { if (m.position.y === -2) m.position.y = 0; });
    const slots = [];
    const jobs = [];
    const slotX = (i) => len / 2 - 5 - i * 7;
    const box = (color) => { const b = new THREE.Group(); b.add(rbox(5, 4, 5, .5, color)); b.add(rbox(5.1, .3, 1.2, .1, C.tape, 0, 3.9, 0)); return b; };
    (o.waiting || [C.card, C.card]).forEach((color, i) => { const b = box(color); b.position.set(slotX(i + 1), 3.6, 0); g.add(b); jobs.push(b); });
    const initial = jobs.slice();
    return {
      group: g, top: 10, radius: len / 2,
      actions: {
        // a new job lands at the back of the line
        push: async (color = C.amber) => {
          const b = box(color); b.position.set(-len / 2 + 3, 12, 0); g.add(b); jobs.push(b);
          await tween(450, (k) => { b.position.y = 12 - 8.4 * k; }, (t) => t * t);
          const targets = jobs.map((_, i) => slotX(i));
          const from = jobs.map((j) => j.position.x);
          await tween(700, (k) => jobs.forEach((j, i) => { j.position.x = from[i] + (targets[i] - from[i]) * k; }));
        },
        // the job at the front leaves the belt
        pop: async () => {
          const b = jobs.shift(); if (!b) return;
          await tween(500, (k) => { b.position.x = slotX(0) + 6 * k; b.position.y = 3.6 + Math.sin(k * Math.PI) * 4; b.scale.setScalar(1 - k * .9); });
          g.remove(b);
          const from = jobs.map((j) => j.position.x);
          await tween(600, (k) => jobs.forEach((j, i) => { j.position.x = from[i] + (slotX(i) - from[i]) * k; }));
        },
      },
      reset() {
        for (const j of jobs) g.remove(j);
        jobs.length = 0;
        initial.forEach((b, i) => { b.position.set(slotX(i + 1), 3.6, 0); b.scale.setScalar(1); g.add(b); jobs.push(b); });
      },
    };
  },
};

/* ---------- Icons for callouts (28x28 strokes) ---------- */
export const ICONS = {
  laptop: '<rect x="5" y="6" width="18" height="12" rx="1.5"/><path d="M2.5 22h23l-2-4h-19z"/>',
  gate: '<path d="M5 25V7M23 25V7M3 7h22M8 14h14"/><path d="M10 14l2-3M15 14l2-3"/>',
  lock: '<rect x="6" y="12" width="16" height="12" rx="2"/><path d="M9.5 12V8.5a4.5 4.5 0 0 1 9 0V12M14 17v3"/>',
  db: '<ellipse cx="14" cy="7" rx="8" ry="3"/><path d="M6 7v14c0 1.7 3.6 3 8 3s8-1.3 8-3V7M6 14c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
  badge: '<rect x="7" y="4" width="14" height="20" rx="2"/><circle cx="14" cy="11" r="2.6"/><path d="M10 18h8M11 21h6"/>',
  box: '<path d="M4 9l10-5 10 5v10l-10 5-10-5z"/><path d="M4 9l10 5 10-5M14 14v10"/>',
  key: '<circle cx="9" cy="14" r="4.5"/><path d="M13.5 14H25M21 14v4M24 14v3"/>',
  shield: '<path d="M14 3.5 5 7v6.5c0 5.4 3.8 9.3 9 11 5.2-1.7 9-5.6 9-11V7z"/><path d="m10 14 3 3 5-6"/>',
  sign: '<path d="M14 25V3M14 6h8l3 2.5-3 2.5h-8M14 14H6l-3 2.5L6 19h8"/>',
  split: '<path d="M3 14h7M10 14l6-7h8M10 14l6 7h8M10 14h14"/><circle cx="10" cy="14" r="2"/>',
  server: '<rect x="5" y="4" width="18" height="8" rx="1.5"/><rect x="5" y="16" width="18" height="8" rx="1.5"/><path d="M9 8h2M9 20h2"/>',
  bolt: '<path d="M16 3 6 16h7l-2 9 11-13h-7z"/>',
  belt: '<rect x="3" y="15" width="22" height="6" rx="3"/><rect x="6" y="7" width="6" height="6" rx="1"/><rect x="15" y="7" width="6" height="6" rx="1"/>',
  gear: '<circle cx="14" cy="14" r="3.5"/><path d="M14 3v4M14 21v4M3 14h4M21 14h4M6.2 6.2l2.8 2.8M19 19l2.8 2.8M6.2 21.8 9 19M19 9l2.8-2.8"/>',
  clock: '<circle cx="14" cy="14" r="10"/><path d="M14 8v6l4 3"/>',
};

/* ---------- Mount: DOM, renderer, scene, story ---------- */
export { THREE };
export function mountExplainer(cfg) {
  const style = document.createElement('style'); style.textContent = CSS; document.head.append(style);
  const $ = (s) => root.querySelector(s);
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const root = document.createElement('div');
  root.className = 'app';
  const params = cfg.params || [];
  root.innerHTML = `
  <svg class="frame" aria-hidden="true"></svg>
  <main class="stage">
    <canvas aria-label="Animated 3D view of ${cfg.title}. Drag to turn, scroll to zoom."></canvas>
    <svg class="leaders" aria-hidden="true"></svg>
    <div class="callouts"></div>
    <div class="tags"></div>
    <header class="brand">
      <svg viewBox="0 0 52 52" aria-hidden="true"><rect class="s" x="6" y="6" width="16" height="16" rx="3"/><rect class="s" x="30" y="30" width="16" height="16" rx="3"/><path class="s" d="M22 14h8a6 6 0 0 1 6 6v10"/><circle class="f" cx="36" cy="24" r="3"/></svg>
      <span class="brand-rule"></span>
      <div><h1>${cfg.brand || 'System Explainers'}</h1><p>See <i>·</i> Trace <i>·</i> Understand</p></div>
    </header>
    <p class="hint">Drag to turn · Scroll to zoom</p>
    <div class="player" role="toolbar" aria-label="Playback">
      <button class="prev" title="Previous step" aria-label="Previous step"><svg viewBox="0 0 24 24"><path d="M15 5.5 8.5 12l6.5 6.5"/></svg></button>
      <button class="play" title="Play" aria-label="Play"><svg viewBox="0 0 24 24"><path class="fill play-ico" d="M8 5.5v13l10.5-6.5z"/></svg></button>
      <button class="next" title="Next step" aria-label="Next step"><svg viewBox="0 0 24 24"><path d="M9 5.5 15.5 12 9 18.5"/></svg></button>
      ${params.map((p) => `<span class="sep"></span><span class="seg-label">${p.label}</span>
        <div class="seg" role="group" aria-label="${p.label}" data-key="${p.key}">
          ${p.options.map(([v, l], i) => `<button data-v="${v}" aria-pressed="${i === 0}">${l}</button>`).join('')}
        </div>`).join('')}
    </div>
  </main>
  <aside class="panel">
    <section class="card intro"><div class="eyebrow">Overview</div><h2>${cfg.title}</h2><p class="lede"></p></section>
    <section class="card"><ol class="steps"></ol></section>
    <section class="card monitor">
      <div class="monitor-head"><span class="dot"></span>Request trace <span class="st">idle</span></div>
      <div class="log" aria-live="polite"></div>
    </section>
  </aside>`;
  document.body.append(root);

  const stage = $('.stage'), canvas = $('canvas');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  speed = reduced ? .35 : 1;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: true, premultipliedAlpha: true, powerPreference: 'high-performance' });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.shadowMap.autoUpdate = false;
  const ink = new InkComposer(renderer);
  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 1, 900);

  scene.add(new THREE.HemisphereLight('#fffaf3', '#c2ae90', .9));
  const key = new THREE.DirectionalLight('#fff6ea', 1.7); key.position.set(-55, 100, 62); scene.add(key);
  // a separate, near-zero light only casts the shadow, so its angle never changes the shading
  const sun = new THREE.DirectionalLight('#ffffff', .001);
  sun.position.set(60, 104, 40); sun.target.position.set(10, 0, 0); sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -140, right: 140, top: 140, bottom: -140, near: 20, far: 340 });
  sun.shadow.radius = 11; sun.shadow.blurSamples = 20; sun.shadow.bias = -4e-4;
  scene.add(sun, sun.target);

  const shadowMat = new THREE.ShadowMaterial({ depthWrite: false });
  const shadowFloor = new THREE.Mesh(new THREE.PlaneGeometry(900, 900), shadowMat);
  shadowFloor.rotation.x = -Math.PI / 2; shadowFloor.receiveShadow = true; shadowFloor.layers.set(NO_INK);
  scene.add(shadowFloor);

  const gridMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false,
    uniforms: { color: { value: new THREE.Color() }, cell: { value: 9 }, center: { value: new THREE.Vector2(0, 4) }, inner: { value: 40 }, outer: { value: 100 }, strength: { value: .55 } },
    vertexShader: 'varying vec2 vPos; void main(){ vec4 wp = modelMatrix * vec4(position, 1.0); vPos = wp.xz; gl_Position = projectionMatrix * viewMatrix * wp; }',
    fragmentShader: `uniform vec3 color; uniform float cell, inner, outer, strength; uniform vec2 center; varying vec2 vPos;
      void main(){ vec2 g = abs(fract(vPos / cell - 0.5) - 0.5) / fwidth(vPos / cell);
        float line = 1.0 - min(min(g.x, g.y), 1.0);
        float fade = 1.0 - smoothstep(inner, outer, length((vPos - center) / vec2(1.3, 1.0)));
        gl_FragColor = vec4(color, line * fade * strength);
        #include <colorspace_fragment>
      }`,
  });
  const grid = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), gridMat);
  grid.rotation.x = -Math.PI / 2; grid.position.y = -.02; grid.layers.set(NO_INK);
  scene.add(grid);

  let dirty = true;
  const isDark = () => { const t = document.documentElement.dataset.theme; return t === 'dark' || (t !== 'light' && matchMedia('(prefers-color-scheme: dark)').matches); };
  function applyTheme() {
    gridMat.uniforms.color.value.set(css('--grid'));
    shadowMat.color.set(css('--floor-shadow')); shadowMat.opacity = +css('--floor-shadow-a');
    ink.mat.uniforms.lineColor.value.set(isDark() ? '#0b0f1a' : '#141a2c');
    renderer.shadowMap.needsUpdate = true; dirty = true;
  }
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyTheme);
  new MutationObserver(applyTheme).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  /* nodes */
  const parts = { ...PARTS, ...(cfg.parts || {}) };
  const nodes = {};
  for (const [id, n] of Object.entries(cfg.nodes)) {
    const made = parts[n.part](n.opts || {});
    const node = nodes[id] = { id, ...n, ...made, actions: made.actions || {} };
    node.group.position.set(n.at[0], 0, n.at[1]);
    if (n.rotate) node.group.rotation.y = n.rotate;
    scene.add(node.group);
    node.ring = new THREE.Mesh(new THREE.RingGeometry(node.radius + 1.5, node.radius + 2.6, 64), new THREE.MeshBasicMaterial({ color: C.teal, transparent: true, opacity: 0, depthWrite: false }));
    node.ring.rotation.x = -Math.PI / 2; node.ring.position.set(n.at[0], .05, n.at[1]); node.ring.layers.set(NO_INK);
    scene.add(node.ring);
  }

  /* wires: arched cables between parts, packets ride them */
  const wires = {};
  for (const [a, b, o = {}] of cfg.wires) {
    const A = nodes[a], B = nodes[b];
    const pa = new THREE.Vector3(A.at[0], 0, A.at[1]), pb = new THREE.Vector3(B.at[0], 0, B.at[1]);
    const dir = pb.clone().sub(pa).normalize();
    const s = pa.clone().addScaledVector(dir, A.radius - 1).setY(2.2);
    const e = pb.clone().addScaledVector(dir, -(B.radius - 1)).setY(2.2);
    const len = s.distanceTo(e), lift = o.lift ?? Math.min(12, 4 + len * .16);
    const pts = [s, s.clone().lerp(e, .18).setY(lift * .8), s.clone().lerp(e, .5).setY(lift), s.clone().lerp(e, .82).setY(lift * .8), e];
    const curve = new THREE.CatmullRomCurve3(pts, false, 'centripetal');
    scene.add(mesh(new THREE.TubeGeometry(curve, 80, .75, 10, false), toon(o.color || C.cable)));
    for (const p of [s, e]) scene.add(rbox(2.6, 2.4, 2.6, .6, C.dark, p.x, 0, p.z));
    wires[a + '>' + b] = curve;
  }
  function route(from, to) {
    if (wires[from + '>' + to]) return { curve: wires[from + '>' + to], rev: false };
    if (wires[to + '>' + from]) return { curve: wires[to + '>' + from], rev: true };
    throw new Error(`no wire between ${from} and ${to}`);
  }

  /* packets */
  const KIND = { req: [C.teal, '--teal'], data: [C.sky, '--navy'], tok: [C.amber, '--amber'], ok: [C.green, '--green'], deny: [C.red, '--red'], job: [C.plum, '--navy'] };
  const tagsEl = $('.tags');
  const live = new Set();
  let runToken = 0;
  async function send(from, to, kind, label, token) {
    if (instant) return;
    const { curve, rev } = route(from, to);
    const g = new THREE.Group();
    const body = mesh(new THREE.CapsuleGeometry(1.9, 4, 6, 14), toon(KIND[kind][0], KIND[kind][0]));
    body.rotation.z = Math.PI / 2; g.add(body);
    if (kind === 'tok') g.add(mesh(new THREE.TorusGeometry(1.4, .4, 8, 18), toon(C.white)).rotateY(Math.PI / 2));
    scene.add(g);
    const tag = document.createElement('div');
    tag.className = 'tag'; tag.textContent = label; tag.style.setProperty('--c', `var(${KIND[kind][1]})`);
    tagsEl.append(tag);
    const p = { g, tag, pos: new THREE.Vector3() };
    live.add(p);
    requestAnimationFrame(() => tag.classList.add('on'));
    const look = new THREE.Vector3();
    const clampU = (u) => Math.min(.9995, Math.max(.0005, u));
    await tween(Math.max(900, curve.getLength() * 26), (k) => {
      if (token !== runToken) return;
      const u = clampU(rev ? 1 - k : k);
      curve.getPointAt(u, p.pos); g.position.copy(p.pos).setY(p.pos.y + 1.9);
      curve.getPointAt(clampU(u + (rev ? -.01 : .01)), look); look.y += 1.9;
      g.lookAt(look); g.rotateY(Math.PI / 2);
    });
    tag.classList.remove('on');
    live.delete(p);
    setTimeout(() => tag.remove(), 250);
    scene.remove(g);
    dirty = true;
  }
  function clearPackets() {
    for (const p of live) { scene.remove(p.g); p.tag.remove(); }
    live.clear();
    for (const tw of tweens) tw.fn(1, 1);
    tweens.clear();
  }
  function pulse(id, color = C.teal) {
    const n = nodes[id];
    if (instant) return Promise.resolve();
    n.ring.material.color.set(color);
    return tween(1100, (k, t) => {
      n.ring.material.opacity = Math.sin(t * Math.PI) * .85;
      const s = 1 + Math.sin(t * Math.PI) * .035; n.group.scale.set(s, s, s);
    }, (t) => t);
  }
  function resetParts() {
    for (const n of Object.values(nodes)) { n.reset?.(); n.ring.material.opacity = 0; n.group.scale.set(1, 1, 1); }
    renderer.shadowMap.needsUpdate = true;
  }

  /* trace log */
  const logEl = $('.log');
  function log(html) { const d = document.createElement('div'); d.innerHTML = html; if (instant) d.style.animation = 'none'; logEl.append(d); logEl.scrollTop = logEl.scrollHeight; }
  const who = (s) => `<span class="who">${s}</span>`;

  /* params */
  const p = Object.fromEntries(params.map((q) => [q.key, q.options[0][0]]));
  const fill = (v) => (typeof v === 'function' ? v(p) : v ?? '').replace(/\{(\w+)\}/g, (m, k) => p[k] ?? m);

  /* callouts with leader lines */
  const STEPS = [{ t: 'The parts', s: cfg.partsLine || `${Object.keys(nodes).length} pieces, one story`, lede: cfg.intro, run: async () => {},
    callouts: cfg.overview || Object.keys(nodes).map((id) => [id, nodes[id].offset || [0, -140]]) }, ...cfg.steps];
  const calloutsEl = $('.callouts'), leaders = $('.leaders');
  let shown = [];
  function showCallouts(step) {
    for (const c of shown) { c.el.classList.remove('on'); setTimeout(() => c.el.remove(), 350); }
    shown = [];
    const st = STEPS[step], accent = st.accent ? fill(st.accent) : '';
    for (const [id, off, title, body, icon] of st.callouts || []) {
      const n = nodes[id];
      const el = document.createElement('div');
      el.className = 'callout' + (step === 0 ? ' step0' : '') + (accent ? ' accent-' + accent : '');
      el.innerHTML = `<svg viewBox="0 0 28 28">${ICONS[icon || n.icon] || ICONS.server}</svg><div><b>${fill(title || n.title)}</b><span>${fill(body || n.body)}</span></div>`;
      calloutsEl.append(el);
      shown.push({ el, n, off });
      requestAnimationFrame(() => requestAnimationFrame(() => { el.classList.add('on'); dirty = true; }));
    }
    dirty = true;
  }
  const v3 = new THREE.Vector3();
  const size = { w: 1, h: 1 };
  function toScreen(n) {
    v3.set(n.at[0], n.top * n.group.scale.y, n.at[1]).project(camera);
    return [(v3.x + 1) / 2 * size.w, (1 - v3.y) / 2 * size.h];
  }
  function placeOverlays() {
    const small = size.w < 700, k = small ? .62 : Math.min(1.15, Math.max(.8, size.w / 1100));
    let svg = '';
    const placed = [];
    for (const c of shown) {
      const [ax, ay] = toScreen(c.n);
      const w = c.el.offsetWidth, h = c.el.offsetHeight;
      let x = ax + c.off[0] * k - w / 2, y = ay + c.off[1] * k - h / 2;
      x = Math.max(12, Math.min(size.w - w - 12, x));
      const lo = small ? 70 : 96, hi = size.h - h - (small ? 64 : 84);
      y = Math.max(lo, Math.min(hi, y));
      // nudge away from cards already placed, in the direction the card already leans
      for (let tries = 0; tries < 8; tries++) {
        const hit = placed.find((r) => x < r.x + r.w + 10 && x + w + 10 > r.x && y < r.y + r.h + 10 && y + h + 10 > r.y);
        if (!hit) break;
        const ny = c.off[1] < 0 ? hit.y - h - 10 : hit.y + hit.h + 10;
        if (ny >= lo && ny <= hi) y = ny; else x = c.off[0] < 0 ? hit.x - w - 10 : hit.x + hit.w + 10;
        x = Math.max(12, Math.min(size.w - w - 12, x));
      }
      placed.push({ x, y, w, h });
      c.el.style.transform = `translate3d(${x}px, ${y}px, 0)` + (c.el.classList.contains('on') ? '' : ' translateY(6px)');
      if (!c.el.classList.contains('on')) continue;
      const cx = x + w / 2, cy = y + h / 2;
      let d;
      if (ay > y + h) d = `M${cx} ${y + h} V${(y + h + ay) / 2} H${ax} V${ay}`;
      else if (ay < y) d = `M${cx} ${y} V${(y + ay) / 2} H${ax} V${ay}`;
      else { const sx = ax < x ? x : x + w; d = `M${sx} ${cy} H${(sx + ax) / 2} V${ay} H${ax}`; }
      svg += `<path d="${d}"/><circle class="halo" cx="${ax}" cy="${ay}" r="9"/><circle class="ring" cx="${ax}" cy="${ay}" r="4.5"/>`;
    }
    leaders.innerHTML = svg;
    for (const q of live) {
      v3.copy(q.g.position).setY(q.g.position.y + 3.2).project(camera);
      q.tag.style.left = (v3.x + 1) / 2 * size.w + 'px';
      q.tag.style.top = (1 - v3.y) / 2 * size.h + 'px';
    }
  }

  /* step list, player */
  const stepsEl = $('.steps');
  stepsEl.innerHTML = STEPS.map((s, i) => `<li><button data-i="${i}"><span class="n">${i}</span><span><span class="t">${s.t}</span><span class="s">${s.s}</span></span></button></li>`).join('');
  stepsEl.addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) { setPlaying(false); go(+b.dataset.i); } });

  let current = 0, playing = false, status = 'idle';
  const setStatus = (s) => { status = s; $('.st').textContent = s; };
  const ctx = (tk) => ({
    send: (a, b, kind, label) => send(a, b, kind, label, tk),
    pulse, log, who, p, C, wait,
    part: (id) => nodes[id].actions,
    at: (id) => nodes[id].at,
  });
  async function go(i, fromPrev = false) {
    const tk = ++runToken;
    current = i;
    clearPackets();
    if (!fromPrev) {
      // rebuild the state of every earlier step instantly
      resetParts(); logEl.innerHTML = '';
      instant = true;
      try { for (let j = 1; j < i; j++) await STEPS[j].run(ctx(tk)); } finally { instant = false; }
      if (tk !== runToken) return;
    }
    $('.eyebrow').textContent = i === 0 ? 'Overview' : `Step ${i} of ${STEPS.length - 1}`;
    $('.lede').innerHTML = fill(STEPS[i].lede);
    [...stepsEl.children].forEach((li, j) => { li.classList.toggle('on', j === i); li.classList.toggle('done', j < i); });
    showCallouts(i);
    setStatus(i === 0 ? 'idle' : 'running');
    await STEPS[i].run(ctx(tk));
    if (tk !== runToken) return;
    setStatus(i === STEPS.length - 1 ? 'done' : 'waiting');
    if (playing) {
      await wait(i === 0 ? 1400 : 1600);
      if (tk !== runToken || !playing) return;
      if (i < STEPS.length - 1) go(i + 1, true);
      else { await wait(1600); if (tk === runToken && playing) go(0); }
    }
  }
  function setPlaying(on) {
    playing = on;
    $('.play-ico').setAttribute('d', on ? 'M7.5 5.5h3v13h-3zM13.5 5.5h3v13h-3z' : 'M8 5.5v13l10.5-6.5z');
    $('.play').setAttribute('aria-label', on ? 'Pause' : 'Play'); $('.play').title = on ? 'Pause' : 'Play';
  }
  $('.play').onclick = () => {
    setPlaying(!playing);
    if (!playing) return;
    if (current >= STEPS.length - 1) go(0);
    else if (status === 'waiting' || current === 0) go(current + 1, true);
    else if (status !== 'running') go(current);
  };
  $('.next').onclick = () => { setPlaying(false); go(Math.min(STEPS.length - 1, current + 1), status === 'waiting' || current === 0); };
  $('.prev').onclick = () => { setPlaying(false); go(Math.max(0, current - 1)); };
  root.querySelectorAll('.seg').forEach((seg) => seg.addEventListener('click', (e) => {
    const b = e.target.closest('button'); if (!b) return;
    p[seg.dataset.key] = b.dataset.v;
    seg.querySelectorAll('button').forEach((x) => x.setAttribute('aria-pressed', x === b));
    setPlaying(false); go(current);
  }));
  addEventListener('keydown', (e) => {
    if (e.target.closest?.('input, textarea')) return;
    if (e.key === 'ArrowRight') $('.next').click();
    else if (e.key === 'ArrowLeft') $('.prev').click();
    else if (e.key === ' ' && e.target === document.body) { e.preventDefault(); $('.play').click(); }
  });

  /* camera: fit, turn, zoom */
  const view = { az: (cfg.camera?.az ?? 36) * DEG, el: (cfg.camera?.el ?? 43) * DEG, zoom: 1 }, goal = { ...view };
  const target = new THREE.Vector3(0, 6, 3);
  const bounds = new THREE.Box3();
  for (const n of Object.values(nodes)) bounds.expandByObject(n.group);
  function placeCamera() {
    const r = 300;
    camera.position.set(target.x + r * Math.cos(view.el) * Math.sin(view.az), target.y + r * Math.sin(view.el), target.z + r * Math.cos(view.el) * Math.cos(view.az));
    camera.lookAt(target); camera.updateMatrixWorld();
    // fit the scene's bounding box in view space, leaving room for callouts
    const inv = camera.matrixWorldInverse, q = new THREE.Vector3();
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    for (let i = 0; i < 8; i++) {
      q.set(i & 1 ? bounds.max.x : bounds.min.x, i & 2 ? bounds.max.y : bounds.min.y, i & 4 ? bounds.max.z : bounds.min.z).applyMatrix4(inv);
      x0 = Math.min(x0, q.x); x1 = Math.max(x1, q.x); y0 = Math.min(y0, q.y); y1 = Math.max(y1, q.y);
    }
    const small = size.w < 700;
    const padX = small ? 1.02 : 1.22, padTop = small ? 1.3 : 1.42, aspect = size.w / size.h;
    let hw = (x1 - x0) / 2 * padX, hh = (y1 - y0) / 2 * padTop;
    if (hw / hh > aspect) hh = hw / aspect; else hw = hh * aspect;
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2 + hh * .08;
    camera.left = cx - hw; camera.right = cx + hw; camera.top = cy + hh; camera.bottom = cy - hh;
    camera.zoom = view.zoom; camera.updateProjectionMatrix();
  }
  let drag = null;
  stage.addEventListener('pointerdown', (e) => {
    if (e.target.closest('.player')) return;
    drag = { x: e.clientX, y: e.clientY, az: goal.az, el: goal.el }; stage.dataset.drag = '1'; stage.setPointerCapture(e.pointerId);
  });
  stage.addEventListener('pointermove', (e) => {
    if (!drag) return;
    goal.az = drag.az - (e.clientX - drag.x) * .006;
    goal.el = Math.max(22 * DEG, Math.min(68 * DEG, drag.el + (e.clientY - drag.y) * .004));
  });
  const endDrag = () => { drag = null; stage.dataset.drag = ''; };
  stage.addEventListener('pointerup', endDrag); stage.addEventListener('pointercancel', endDrag);
  stage.addEventListener('wheel', (e) => { e.preventDefault(); goal.zoom = Math.max(.7, Math.min(2.2, goal.zoom * Math.exp(-e.deltaY * .0012))); }, { passive: false });

  function drawFrame() {
    const f = $('.frame'), W = innerWidth, H = innerHeight;
    if (W < 900) { f.innerHTML = ''; return; }
    f.setAttribute('viewBox', `0 0 ${W} ${H}`);
    const px = W - 402;
    f.innerHTML = `
      <path d="M24 ${H - 120} V140 l26 -26 H${px * .42}"/><circle cx="${px * .42}" cy="114" r="4"/>
      <path d="M${px - 8} 16 V64 l-18 18 V${H * .36}"/><circle cx="${px - 26}" cy="${H * .36}" r="4"/>
      <path d="M${px * .58} ${H - 18} H${px - 30} l-20 -20 V${H * .62}"/><circle cx="${px - 50}" cy="${H * .62}" r="4"/>
      <path d="M60 ${H - 18} H${px * .3}"/><circle cx="${px * .3}" cy="${H - 18}" r="4"/>`;
  }
  function resize() {
    const r = stage.getBoundingClientRect();
    size.w = r.width; size.h = r.height;
    const dpr = Math.min(devicePixelRatio || 1, 2);
    renderer.setPixelRatio(dpr); renderer.setSize(size.w, size.h, false);
    ink.setSize(size.w, size.h, dpr);
    stage.classList.toggle('compact', size.w < 700);
    dirty = true;
    drawFrame();
  }
  new ResizeObserver(resize).observe(stage);

  /* loop */
  const blinkers = Object.values(nodes).filter((n) => n.group.userData.lights);
  function loop(now) {
    requestAnimationFrame(loop);
    const animating = tweens.size > 0;
    tick(now);
    let moved = false;
    for (const k of ['az', 'el', 'zoom']) {
      const d = goal[k] - view[k];
      if (Math.abs(d) > 1e-4) { view[k] += d * .16; moved = true; } else view[k] = goal[k];
    }
    // servers that are working blink their LEDs
    for (const n of blinkers) {
      const on = n.group.userData.blink;
      n.group.userData.lights.forEach((l, i) => { const v = !on || ((now / 160 + i * 1.7) % 3) > .8; if (l.visible !== v) { l.visible = v; moved = true; } });
    }
    if (!(dirty || animating || moved)) return;
    dirty = false;
    if (animating || moved) renderer.shadowMap.needsUpdate = true;
    placeCamera();
    ink.render(scene, camera);
    placeOverlays();
  }

  applyTheme();
  resize();
  renderer.shadowMap.needsUpdate = true;
  requestAnimationFrame(loop);
  go(0);
  document.fonts?.ready.then(() => { dirty = true; });
  setInterval(() => { dirty = true; }, 400);
  return { go, nodes, scene };
}
