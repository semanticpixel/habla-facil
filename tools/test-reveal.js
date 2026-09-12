// Tests the tap-to-reveal script against a DOM shim.
//
// The script under test is extracted from the BUILT page, not copied here, so
// this cannot drift from what actually ships. Run the build first:
//
//     python3 tools/build-menu.py && node tools/test-reveal.js
//
// What it does not cover: real touch behaviour on a phone -- double-tap zoom,
// tap highlight, whether three taps on a logo is comfortable. Test that by hand.
const fs = require("fs"), vm = require("vm"), path = require("path");

const built = fs.readdirSync("_site").find(f => f.endsWith(".html") && f !== "index.html" && f !== "404.html");
const html = fs.readFileSync(path.join("_site", built), "utf8");
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];

let fails = 0;
const ok = (label, cond) => { console.log(`${cond ? "  ok  " : "  FAIL"}  ${label}`); if (!cond) fails++; };

function makeEnv({ stored = null, storageThrows = false } = {}) {
  const store = {};
  if (stored !== null) store["hf-methods"] = stored;
  const classes = new Set();
  const listeners = {};
  const logo = {
    handlers: [],
    addEventListener(t, fn) { if (t === "click") this.handlers.push(fn); },
    click() { this.handlers.forEach(fn => fn()); },
  };
  const localStorage = storageThrows
    ? { get getItem() { throw new Error("blocked"); } }
    : {
        getItem: k => (k in store ? store[k] : null),
        setItem: (k, v) => { store[k] = String(v); },
        removeItem: k => { delete store[k]; },
      };
  const ctx = {
    window: {},
    document: {
      documentElement: {
        classList: {
          add: c => classes.add(c),
          contains: c => classes.has(c),
          toggle: c => (classes.has(c) ? (classes.delete(c), false) : (classes.add(c), true)),
        },
      },
      addEventListener: (t, fn) => { (listeners[t] ||= []).push(fn); },
      querySelector: () => logo,
    },
    setTimeout: (fn, ms) => { const id = Symbol(); timers.set(id, { fn, at: now + ms }); return id; },
    clearTimeout: id => timers.delete(id),
  };
  Object.defineProperty(ctx.window, "localStorage", { get: () => { if (storageThrows) throw new Error("blocked"); return localStorage; } });
  let now = 0;
  const timers = new Map();
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(script, ctx);
  return {
    ready: () => (listeners.DOMContentLoaded || []).forEach(fn => fn()),
    tap: () => logo.click(),
    advance: ms => { now += ms; for (const [id, t] of [...timers]) if (t.at <= now) { timers.delete(id); t.fn(); } },
    shown: () => classes.has("recipes"),
    stored: () => store["hf-methods"],
  };
}

console.log(`\nreveal script from _site/${built}\n`);

console.log("three taps reveal");
{ const e = makeEnv(); e.ready();
  e.tap(); ok("one tap does nothing", !e.shown());
  e.tap(); ok("two taps do nothing", !e.shown());
  e.tap(); ok("third tap reveals", e.shown());
  ok("persisted to storage", e.stored() === "1"); }

console.log("\nthree more taps hide again");
{ const e = makeEnv(); e.ready();
  e.tap(); e.tap(); e.tap(); ok("revealed", e.shown());
  e.tap(); e.tap(); e.tap(); ok("hidden again", !e.shown());
  ok("storage cleared", e.stored() === undefined); }

console.log("\ntaps expire");
{ const e = makeEnv(); e.ready();
  e.tap(); e.tap(); e.advance(900);
  e.tap(); ok("a slow third tap does not reveal", !e.shown());
  e.tap(); e.tap(); ok("counting restarted cleanly", e.shown()); }

console.log("\nthe window is per-tap, not total");
{ const e = makeEnv(); e.ready();
  e.tap(); e.advance(800); e.tap(); e.advance(800); e.tap();
  ok("taps 800ms apart still reveal", e.shown()); }

console.log("\nstored state applies before paint");
{ const e = makeEnv({ stored: "1" });
  ok("class set without waiting for DOMContentLoaded", e.shown()); }
{ const e = makeEnv({ stored: null });
  ok("absent storage leaves it hidden", !e.shown()); }

console.log("\nprivate window / blocked storage");
{ let threw = false, e;
  try { e = makeEnv({ storageThrows: true }); e.ready(); } catch (err) { threw = true; }
  ok("script survives storage throwing", !threw);
  if (!threw) { e.tap(); e.tap(); e.tap(); ok("reveal still works in-session", e.shown()); } }

console.log(fails ? `\n${fails} FAILED\n` : "\nall passed\n");
process.exit(fails ? 1 : 0);
