import { test } from 'node:test';
import assert from 'node:assert/strict';
// @ts-expect-error Browser QA module is JS; it is run by the host browser tool.
import { validateUnknownStateSpacing } from '../tools/spacing-contract.mjs';

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
});
