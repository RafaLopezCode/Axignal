import { test } from 'node:test';
import assert from 'node:assert/strict';
// @ts-expect-error Browser QA module is JS; it is run by the host browser tool.
import { validateUnknownStateSpacing, validateCognitiveReadingLayout } from '../tools/spacing-contract.mjs';

const readable = { present: true, statusTitle: 16, titleBody: 16,
  bodyAction: 24, insetTop: 24, insetLeft: 24, insetRight: 24, insetBottom: 24,
  actionHeight: 44, overflow: false };

test('spacing contract rejects the reported collapsed status/title regression', () => {
  assert.deepEqual(validateUnknownStateSpacing(readable), []);
  assert.match(validateUnknownStateSpacing({ ...readable, statusTitle: 0 })[0], /statusTitle/);
});
test('spacing contract rejects clipped content, tiny targets and absent measurements', () => {
  const failures = validateUnknownStateSpacing({ ...readable, insetRight: -8,
    actionHeight: 20, overflow: true });
  assert.equal(failures.length, 3);
  assert.equal(validateUnknownStateSpacing({ present: false }).length, 1);
  assert.ok(validateUnknownStateSpacing({ ...readable, titleBody: NaN }).length);
  assert.equal(validateUnknownStateSpacing({ ...readable,
    insetTop: 19, insetLeft: 19, insetRight: 19, insetBottom: 19 }).length, 4);
});

test('cognitive layout rejects the observed small targets and lost typography hierarchy', () => {
  const role = (size: number, weight: number, font = 'Manrope', tag = 'P') =>
    ({ size, weight, font, tag, height: 44, padding: [16, 16, 16, 16] });
  const sample = {
    present: true, overflow: false, fontsReady: 'loaded',
    h1: role(36, 400, 'Manrope', 'H1'), h2: role(26, 400, 'Manrope', 'H2'),
    body: role(14, 400), question: role(14, 600), metadata: role(11, 400),
    label: role(10, 400, 'IBM Plex Mono', 'H3'), control: role(13, 500),
    input: role(13, 500), component: role(14, 400),
    axentTitle: role(24, 400, 'Fraunces', 'H2'), axentBody: role(14, 400),
    axentControl: role(13, 500),
  };
  assert.deepEqual(validateCognitiveReadingLayout(sample), []);
  const failures = validateCognitiveReadingLayout({ ...sample,
    control: { ...role(12, 650), height: 36 }, metadata: role(13, 400),
    label: role(12, 400, 'Fraunces', 'H3'), overflow: true,
  });
  assert.ok(failures.some((value: string) => value.includes('target')));
  assert.ok(failures.some((value: string) => value.includes('metadata')));
  assert.ok(failures.some((value: string) => value.includes('label')));
  assert.ok(failures.some((value: string) => value.includes('overflows')));
  assert.ok(validateCognitiveReadingLayout({ ...sample, h2: sample.h1 }).length);
  assert.ok(validateCognitiveReadingLayout({ present: false }).length);
});
