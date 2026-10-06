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

// Semantic roles from docs/design/TYPOGRAPHY_ROLES.md, measured on the actual
// subscriber reading. This probe never changes the DOM or invents product data.
export function measureCognitiveReadingLayout() {
  const pick = selector => {
    const element = document.querySelector(selector);
    if (!element) return null;
    const style = getComputedStyle(element);
    return {
      font: style.fontFamily, size: Number.parseFloat(style.fontSize),
      weight: Number(style.fontWeight), tag: element.tagName,
      height: element.getBoundingClientRect().height,
      padding: [style.paddingTop, style.paddingRight, style.paddingBottom, style.paddingLeft]
        .map(value => Number.parseFloat(value)),
    };
  };
  return {
    present: Boolean(document.querySelector('.runtime-cognitive-lens')),
    viewport: innerWidth, overflow: document.documentElement.scrollWidth > innerWidth,
    h1: pick('main h1'), h2: pick('.subscriber-reading h2'),
    body: pick('.runtime-cognitive-lens p.cg-unknown'),
    question: pick('.runtime-cognitive-lens .cg-question'),
    metadata: pick('.runtime-cognitive-lens .cg-meta'),
    control: pick('.runtime-cognitive-controls button'),
    input: pick('.runtime-cut-control input'),
    component: pick('.runtime-cognitive-lens .cg-component'),
    label: pick('.runtime-cognitive-lens .cg-title'),
    axentTitle: pick('.axent-welcome h2'), axentBody: pick('.axent-welcome p'),
    axentControl: pick('.axent-questions button'),
    fontsReady: document.fonts.status,
  };
}

export function validateCognitiveReadingLayout(sample) {
  if (!sample.present) return ['Cognitive reading not rendered'];
  const failures = [];
  const roles = {
    body: [14, 400, 'Manrope'], question: [14, 600, 'Manrope'],
    metadata: [11, 400, 'Manrope'], label: [10, 400, 'IBM Plex Mono'],
    control: [13, 500, 'Manrope'], input: [13, 500, 'Manrope'],
    axentTitle: [24, 400, 'Fraunces'], axentBody: [14, 400, 'Manrope'],
    axentControl: [13, 500, 'Manrope'],
  };
  for (const [name, [size, weight, family]] of Object.entries(roles)) {
    const role = sample[name];
    if (!role || role.size !== size || role.weight !== weight || !role.font.includes(family))
      failures.push(`${name}: missing or incorrect typography role`);
  }
  for (const name of ['control', 'input', 'axentControl']) {
    if (!Number.isFinite(sample[name]?.height) || sample[name].height < 43)
      failures.push(`${name}: target below 44px`);
  }
  if (!sample.component || sample.component.padding.some(value => !Number.isFinite(value) || value < 15))
    failures.push('Evidence panel: missing or insufficient inset');
  if (!sample.h1 || !sample.h2 || sample.h1.tag !== 'H1' || sample.h2.tag !== 'H2' ||
      sample.label?.tag !== 'H3' || !(sample.h1.size > sample.h2.size && sample.h2.size > 14))
    failures.push('Heading hierarchy missing or collapsed');
  if (sample.overflow) failures.push('Document overflows viewport');
  if (sample.fontsReady !== 'loaded') failures.push('Fonts not settled');
  return failures;
}
