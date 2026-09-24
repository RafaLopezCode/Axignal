/** Fixture loading + deterministic base/pending split for expansion tests. */

export function baseSplit(data, baseFraction) {
  const nodes = data.nodes;
  const baseCount = Math.max(1, Math.floor(nodes.length * baseFraction));
  const inBase = new Set();
  for (let i = 0; i < baseCount; i += 1) inBase.add(nodes[i].id);
  const baseNodes = nodes.slice(0, baseCount);
  const pendingNodes = nodes.slice(baseCount);
  const baseEdges = [];
  const pendingEdges = [];
  for (const e of data.edges) {
    if (inBase.has(e.source) && inBase.has(e.target)) baseEdges.push(e);
    else pendingEdges.push(e);
  }
  return {
    base: { nodes: baseNodes, edges: baseEdges },
    pending: { nodes: pendingNodes, edges: pendingEdges },
    full: data,
  };
}

export async function loadFixture(url) {
  const t0 = performance.now();
  const res = await fetch(url);
  const text = await res.text();
  const parsedAt = performance.now();
  const data = JSON.parse(text);
  const doneAt = performance.now();
  return {
    data,
    timings: { fetchMs: parsedAt - t0, parseMs: doneAt - parsedAt, bytes: text.length },
  };
}

/** A deterministic path over the base edges for the PATHX scenario. */
export function pickPath(data, length = 6) {
  const bySource = new Map();
  for (const e of data.edges) {
    if (!bySource.has(e.source)) bySource.set(e.source, []);
    bySource.get(e.source).push(e);
  }
  for (const start of data.nodes) {
    const path = [];
    let current = start.id;
    const visited = new Set([current]);
    for (let i = 0; i < length; i += 1) {
      const candidates = (bySource.get(current) || []).filter((e) => !visited.has(e.target));
      if (candidates.length === 0) break;
      const edge = candidates[Math.floor(candidates.length / 2)];
      path.push(edge);
      visited.add(edge.target);
      current = edge.target;
    }
    if (path.length >= 3) return path;
  }
  return data.edges.slice(0, 3);
}
