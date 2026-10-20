import { test } from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { firstReadingScript } from "../lib/landing-first-reading";

function deferred() {
  let resolve!: () => void;
  let reject!: () => void;
  const promise = new Promise<void>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
const flush = async () => {
  for (let i = 0; i < 12; i++) await Promise.resolve();
};
function browser({
  small = true,
  hash = "",
  loading = false,
  supportsPaint = true,
} = {}) {
  const attributes = new Set<string>();
  const listeners = new Map<string, () => void>();
  const frames = new Map<number, () => void>();
  const fontLoads: string[] = [];
  const primary = deferred();
  const secondary = deferred();
  let dom: (() => void) | undefined;
  let paint:
    | ((list: { getEntries: () => { name: string }[] }) => void)
    | undefined;
  let disconnected = 0;
  let settled = 0;
  let readinessReads = 0;
  let frameId = 0;
  class PaintObserver {
    static supportedEntryTypes = ["paint"];
    constructor(callback: typeof paint) {
      paint = callback;
    }
    observe() {}
    disconnect() {
      disconnected++;
    }
  }
  const observer = supportsPaint ? PaintObserver : undefined;
  const window = {
    matchMedia: () => ({ matches: small }),
    PerformanceObserver: observer,
    addEventListener: (name: string, fn: () => void) => listeners.set(name, fn),
    removeEventListener: (name: string) => listeners.delete(name),
    dispatchEvent: (event: Event) => {
      if (event.type === "axignal:secondary-type-settled") settled++;
    },
  };
  const document = {
    readyState: loading ? "loading" : "complete",
    documentElement: {
      setAttribute: (name: string) => attributes.add(name),
      removeAttribute: (name: string) => attributes.delete(name),
    },
    addEventListener: (_name: string, fn: () => void) => {
      dom = fn;
    },
    fonts: {
      get ready() {
        readinessReads++;
        return primary.promise;
      },
      load: (face: string) => {
        fontLoads.push(face);
        return face.includes("Bic Notes") ? secondary.promise : primary.promise;
      },
    },
  };
  vm.runInNewContext(firstReadingScript, {
    window,
    document,
    location: { hash },
    performance: { getEntriesByName: () => [] },
    PerformanceObserver: observer,
    requestAnimationFrame: (fn: () => void) => {
      const id = ++frameId;
      frames.set(id, fn);
      return id;
    },
    cancelAnimationFrame: (id: number) => frames.delete(id),
    Event,
    Promise,
  });
  return {
    attributes,
    listeners,
    frames,
    fontLoads,
    primary,
    secondary,
    dom: () => dom?.(),
    paint: () =>
      paint?.({ getEntries: () => [{ name: "first-contentful-paint" }] }),
    frame: () => {
      const queued = [...frames.values()];
      frames.clear();
      queued.forEach((fn) => fn());
    },
    counts: () => ({ settled, disconnected, readinessReads }),
  };
}
test("desktop and native deep links keep the original eager type path", async () => {
  for (const options of [
    { small: false },
    { hash: "#pricing" },
    { hash: "#discover" },
    { hash: "#trust" },
  ]) {
    const b = browser(options);
    await flush();
    assert.equal(b.attributes.size, 0);
    assert.equal(b.listeners.size, 0);
    assert.deepEqual(b.fontLoads, []);
  }
});
test("secondary type waits for DOM, primary fonts and real paint, then two frames", async () => {
  const b = browser({ loading: true });
  assert.ok(b.attributes.has("data-lab-first-reading"));
  await flush();
  assert.equal(b.fontLoads.length, 0);
  b.dom();
  await flush();
  assert.equal(b.fontLoads.length, 0);
  assert.equal(
    b.counts().readinessReads,
    0,
    "Readiness must be sampled after real paint",
  );
  b.primary.resolve();
  await flush();
  assert.equal(
    b.frames.size,
    0,
    "Font readiness alone is not a painted reading",
  );
  b.paint();
  await flush();
  b.frame();
  assert.ok(b.attributes.has("data-lab-first-reading"));
  b.frame();
  assert.equal(b.attributes.size, 0);
  assert.equal(b.listeners.size, 0);
  assert.match(b.fontLoads[0], /Bic Notes Lab/);
  assert.equal(b.counts().readinessReads, 1);
  assert.equal(b.counts().settled, 0);
  b.secondary.resolve();
  await flush();
  assert.equal(b.counts().settled, 1);
});
test("human intent restores notes immediately and cleans up even when a font fails", async () => {
  for (const intent of [
    "scroll",
    "pointerdown",
    "keydown",
    "resize",
    "pagehide",
  ]) {
    const b = browser();
    b.listeners.get(intent)!();
    assert.equal(b.attributes.size, 0);
    assert.equal(b.listeners.size, 0);
    b.secondary.reject();
    b.primary.resolve();
    b.paint();
    await flush();
    assert.equal(b.frames.size, 0);
    assert.equal(b.counts().settled, 1);
    assert.equal(
      b.fontLoads.filter((face) => face.includes("Bic Notes")).length,
      1,
    );
  }
});
test("browsers without paint observation retain readable content and release normally", async () => {
  const b = browser({ supportsPaint: false });
  b.primary.resolve();
  await flush();
  b.frame();
  b.frame();
  assert.equal(b.attributes.size, 0);
  assert.equal(b.listeners.size, 0);
  b.secondary.resolve();
  await flush();
  assert.equal(b.counts().settled, 1);
});

test("real paint still waits for the fonts actually selected by CSS", async () => {
  const b = browser();
  b.paint();
  await flush();
  assert.equal(b.counts().readinessReads, 1);
  assert.equal(b.frames.size, 0);
  assert.equal(b.fontLoads.length, 0);
  b.primary.resolve();
  await flush();
  b.frame();
  b.frame();
  assert.equal(b.attributes.size, 0);
  assert.equal(b.fontLoads.length, 1);
  b.secondary.resolve();
  await flush();
  assert.equal(b.counts().settled, 1);
});
