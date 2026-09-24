/** Deterministic-ish browser instrumentation shared by all adapters. */

export const metrics = {
  marks: {},
  events: [],
};

export function mark(name) {
  metrics.marks[name] = performance.now();
  return metrics.marks[name];
}

export function since(name) {
  return performance.now() - (metrics.marks[name] ?? performance.now());
}

export function record(name, value) {
  metrics.events.push({ name, value, at: performance.now() });
  return value;
}

/** Sample `frameCount` animation frames; returns frame-delta statistics (ms). */
export function sampleFrames(frameCount = 90) {
  return new Promise((resolve) => {
    const deltas = [];
    let last = performance.now();
    let count = 0;
    function tick(now) {
      deltas.push(now - last);
      last = now;
      count += 1;
      if (count >= frameCount) {
        resolve(frameStats(deltas));
        return;
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
}

export function frameStats(deltas) {
  const sorted = [...deltas].sort((a, b) => a - b);
  const at = (q) => sorted[Math.min(sorted.length - 1, Math.floor(q * sorted.length))];
  return {
    count: sorted.length,
    mean: round(sorted.reduce((s, v) => s + v, 0) / sorted.length),
    p50: round(at(0.5)),
    p95: round(at(0.95)),
    p99: round(at(0.99)),
  };
}

export function heapMB() {
  const m = performance.memory;
  return m ? round(m.usedJSHeapSize / (1024 * 1024)) : null;
}

export function round(v) {
  return Math.round(v * 100) / 100;
}

/** Simulate a wheel gesture (pan/zoom) and measure frames during it. */
export async function measureWheel(container, frames = 90, deltaY = 120) {
  const rect = container.getBoundingClientRect();
  const x = rect.left + rect.width / 2;
  const y = rect.top + rect.height / 2;
  const sampler = sampleFrames(frames);
  let ticks = 0;
  const interval = setInterval(() => {
    ticks += 1;
    const ev = new WheelEvent("wheel", {
      deltaY: ticks % 2 === 0 ? deltaY : -deltaY,
      clientX: x,
      clientY: y,
      bubbles: true,
      cancelable: true,
    });
    container.dispatchEvent(ev);
    if (ticks > frames / 3) clearInterval(interval);
  }, 16);
  const stats = await sampler;
  clearInterval(interval);
  return stats;
}

export function nextFrame() {
  return new Promise((resolve) => requestAnimationFrame(() => resolve(performance.now())));
}
