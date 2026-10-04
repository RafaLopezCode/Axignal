// Read-only DOM probe, executed through the host browser tool. No browser package.
export function measureUnknownStateSpacing() {
  const panel = document.querySelector('.canonical-product .family-empty');
  if (!panel) return { present: false };
  const badge = panel.querySelector('.badge');
  const title = panel.querySelector('h2');
  const body = panel.querySelector('p');
  const action = panel.querySelector('button');
  if (!badge || !title || !body || !action) return { present: false };
  const rect = panel.getBoundingClientRect();
  const b = badge.getBoundingClientRect();
  const h = title.getBoundingClientRect();
  const p = body.getBoundingClientRect();
  const a = action.getBoundingClientRect();
  return {
    present: true, viewport: innerWidth,
    statusTitle: h.top - b.bottom,
    titleBody: p.top - h.bottom,
    bodyAction: a.top - p.bottom,
    insetTop: b.top - rect.top,
    insetLeft: b.left - rect.left,
    insetRight: rect.right - Math.max(h.right, p.right, a.right),
    insetBottom: rect.bottom - a.bottom,
    actionHeight: a.height,
    overflow: document.documentElement.scrollWidth > innerWidth,
  };
}

// Perceptual minimums, independent of CSS token values. Subpixel tolerance is 1px.
export function validateUnknownStateSpacing(sample) {
  if (!sample.present) return ['Unknown state not rendered'];
  const minimums = { statusTitle: 16, titleBody: 16, bodyAction: 24,
    insetTop: 24, insetLeft: 24, insetRight: 24, insetBottom: 24,
    actionHeight: 44 };
  const failures = Object.entries(minimums).flatMap(([key, minimum]) =>
    Number.isFinite(sample[key]) && sample[key] >= minimum - 1
      ? [] : [`${key}: ${sample[key]}px; expected at least ${minimum}px`]);
  if (sample.overflow) failures.push('Document overflows viewport');
  return failures;
}
