import test from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { SyntheticEvidenceProvider, useEvidenceLink } from "../components/evidence-link-context";
import { shouldApplyLandingFacet } from "../lib/observatory-url";
import { HOME_METADATA } from "../lib/public-home-metadata";

test("explicit deep links must override any demo initial family", () => {
  for (const value of ["family=presence&channel=seo&view=evidence","family=presence&channel=geo","family=markets","family=demand","channel=web","family="]) {
    assert.equal(shouldApplyLandingFacet(new URLSearchParams(value)), false, value);
  }
  assert.equal(shouldApplyLandingFacet(new URLSearchParams("view=evolution")), true);
  assert.equal(shouldApplyLandingFacet(new URLSearchParams()), true);
});

test("demo source provenance never becomes an outbound hyperlink; actual links remain available", () => {
  const url = "https://search-visibility.example.com/demo-seo-geo/queries";
  function LinkExample() {
    const link = useEvidenceLink();
    return createElement("p", null,
      link.href(url) ? createElement("a", { href: link.href(url) ?? "" }, "Evidence") : "Illustrative evidence",
    );
  }
  const real = renderToStaticMarkup(createElement(LinkExample));
  const demo = renderToStaticMarkup(createElement(SyntheticEvidenceProvider, null, createElement(LinkExample)));
  assert.match(real, /href="https:\/\/search-visibility\.example\.com\/demo-seo-geo\/queries"/);
  assert.doesNotMatch(demo, /href=/);
  assert.match(demo, /Illustrative evidence/);
});

test("root visitor-facing metadata is provided for every supported language", () => {
  for (const locale of ["es", "en", "de", "fr", "it", "pt"] as const) {
    assert.match(HOME_METADATA[locale].title, /AXIGNAL/);
    assert.ok(HOME_METADATA[locale].description.length > 50);
  }
  assert.notEqual(HOME_METADATA.es.title, HOME_METADATA.en.title);
});
