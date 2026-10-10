import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { EUR_REFERENCE, PUBLISHED_PRICES, approvedPriceBook, formatFixedMoney, monthlyFixedPriceMinor, suggestedCurrency } from "../lib/commercial-prices";
import { monthlyReferenceCents } from "../lib/presentation";

test("MASTER EUR price is the only published price and does not localize into USD/GBP", () => {
  assert.deepEqual([...PUBLISHED_PRICES.keys()], ["EUR"]);
  assert.equal(monthlyReferenceCents(1), 995);
  assert.equal(monthlyReferenceCents(2), 1490);
  assert.equal(monthlyReferenceCents(100), 50000);
  assert.equal(suggestedCurrency("US"), "EUR");
  assert.equal(suggestedCurrency("GB"), "EUR");
  assert.equal(suggestedCurrency("DE"), "EUR");
  assert.equal(formatFixedMoney("en-US", EUR_REFERENCE, 995), "€9.95");
});

test("foreign prices require explicit approved Stripe references; no invented FX", () => {
  assert.throws(() => approvedPriceBook([EUR_REFERENCE, {currency:"USD", baseMinor:1000, additionalMinor:500, approvalRef:"proposal"}]));
  const book = approvedPriceBook([EUR_REFERENCE, {
    currency: "USD", baseMinor: 1249, additionalMinor: 500, approvalRef: "example-approved-for-test",
    stripeBasePriceRef: "price_usd_base_test", stripeAdditionalPriceRef: "price_usd_addon_test",
  }]);
  assert.equal(suggestedCurrency("US", book), "USD");
  assert.equal(suggestedCurrency("GB", book), "EUR");
  assert.equal(monthlyFixedPriceMinor(book.get("USD")!, 3), 2249);
  assert.equal(monthlyReferenceCents(3), 1985);
  assert.throws(() => approvedPriceBook([EUR_REFERENCE, EUR_REFERENCE]));
  assert.throws(() => approvedPriceBook([{...EUR_REFERENCE, baseMinor: 999}]));
});

test("fixed price rejects invalid quantities, precision and negative minor units", () => {
  for (const count of [0,-1,101,1.5,NaN,Infinity]) {
    assert.throws(() => monthlyFixedPriceMinor(EUR_REFERENCE, count));
  }
  assert.throws(() => formatFixedMoney("es-ES", EUR_REFERENCE, -10));
});

test("no UI or Stripe purchases use an unapproved conversion rate", () => {
  const root = path.resolve(import.meta.dirname, "..");
  const landing = fs.readFileSync(path.join(root,"components/landing-extras.tsx"), "utf8");
  const account = fs.readFileSync(path.join(root,"components/observatory.tsx"), "utf8");
  assert.match(landing, /formatReferenceMoney/);
  assert.match(account, /formatReferenceMoney/);
  assert.ok(!landing.includes('currency: "USD"'));
  assert.ok(!account.includes('currency: "GBP"'));
});
