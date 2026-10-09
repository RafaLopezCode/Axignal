import assert from "node:assert/strict";
import test from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { PublicUnderstandingView } from "../components/public-understanding";
import { LocaleProvider } from "../lib/locale";
import { publicUnderstandingSchema, understandingReportReference, type PublicUnderstanding } from "../lib/public-understanding-contracts";
import { translate } from "../lib/copy-catalog";

const measuredAt = "2026-10-09T10:00:00+00:00";
const reportId = "a".repeat(64);

function report(overrides: Partial<PublicUnderstanding> = {}): PublicUnderstanding {
  return {
    reportId,
    measuredAt,
    instrument: {
      id: "axignal.public-offer-understanding",
      version: "1.0.0",
      representationVersion: "public-citations.v1",
      interpretationVersion: "conditional-offer.v1",
      model: "controlled-test-model",
    },
    status: "MEASURED",
    cause: "CONDITIONED_INTERPRETATION",
    currentness: "CURRENT",
    execution: "EVALUATED",
    coverage: "BOUNDED_COMPLETE",
    authority: "DERIVED_CONDITIONED_NOT_CANONICAL",
    citations: [
      {
        id: "q1",
        url: "https://example.test/services",
        quote: "We repair shoes for households.",
        observedAt: measuredAt,
        contentFingerprint: "sha256:source-one",
      },
      {
        id: "q2",
        url: "https://example.test/about",
        quote: "Repairs are available in our workshop.",
        observedAt: measuredAt,
        contentFingerprint: "sha256:source-two",
      },
    ],
    dimensions: [
      {
        dimension: "offer",
        state: "STRENGTH",
        cause: "EXPLICIT_STATEMENT_SELECTED",
        citationIds: ["q1"],
        proposal: null,
        alternatives: ["DELIBERATE_LIMITED_DISCLOSURE"],
        recheck: "SAME_INSTRUMENT_AND_SOURCE_SCOPE_AFTER_HUMAN_REVIEW",
      },
      {
        dimension: "audience",
        state: "CONSTRUCTIVE_GAP",
        cause: "REPRESENTATION_LIMITATION_POSSIBLE",
        citationIds: ["q1", "q2"],
        proposal: "MAKE_AUDIENCE_EXPLICIT_IF_INTENDED",
        alternatives: ["DELIBERATE_LIMITED_DISCLOSURE", "SAMPLE_SCOPE", "EVALUATOR_ERROR"],
        recheck: "SAME_INSTRUMENT_AND_SOURCE_SCOPE_AFTER_HUMAN_REVIEW",
      },
      {
        dimension: "outcome",
        state: "UNCERTAIN",
        cause: "STATE_INSUFFICIENT",
        citationIds: ["q1", "q2"],
        proposal: null,
        alternatives: ["SAMPLE_SCOPE", "EVALUATOR_ERROR"],
        recheck: "SAME_INSTRUMENT_AND_SOURCE_SCOPE_AFTER_HUMAN_REVIEW",
      },
    ],
    ...overrides,
  };
}

function render(value: PublicUnderstanding): string {
  return renderToStaticMarkup(
    createElement(
      LocaleProvider,
      null,
      createElement(PublicUnderstandingView, { report: value }),
    ),
  );
}

test("public report schema strips evaluator trace and private operational fields", () => {
  const input = {
    ...report(),
    trace: [{ answer: "private evaluator payload", distribution: [["q1", 0.99]] }],
    stateFingerprint: "private-state-fingerprint",
    tenantId: "tenant-secret",
    providerInput: true,
    dimensions: report().dimensions.map((dimension) => ({
      ...dimension,
      distribution: [["STRENGTH", 0.99]],
      privatePrompt: "internal prompt",
    })),
  };
  const parsed = publicUnderstandingSchema.parse(input);

  assert.equal("trace" in parsed, false);
  assert.equal("stateFingerprint" in parsed, false);
  assert.equal("tenantId" in parsed, false);
  assert.equal("providerInput" in parsed, false);
  assert.equal("distribution" in parsed.dimensions[0], false);
  assert.equal("privatePrompt" in parsed.dimensions[0], false);
});

test("public report schema rejects canonical authority, invented states, and oversized quotes", () => {
  assert.equal(publicUnderstandingSchema.safeParse({ ...report(), authority: "FAXT" }).success, false);
  assert.equal(
    publicUnderstandingSchema.safeParse({
      ...report(),
      dimensions: [{ ...report().dimensions[0], state: "OBSERVED" }],
    }).success,
    false,
  );
  assert.equal(
    publicUnderstandingSchema.safeParse({
      ...report(),
      citations: [{ ...report().citations[0], quote: "x".repeat(481) }],
    }).success,
    false,
  );
});

test("subscriber report renders cited strengths, conditional gaps, uncertainty, history, and comparison", () => {
  const previous = report({
    reportId: "b".repeat(64),
    measuredAt: "2026-10-02T10:00:00+00:00",
    dimensions: [report().dimensions[0]],
  });
  const current = report({
    comparison: {
      previousReportId: previous.reportId,
      previousMeasuredAt: previous.measuredAt,
      state: "COMPARABLE",
      reason: "SAME_CONDITIONED_INSTRUMENT",
      meaning: "INTERPRETATION_CHANGE_NOT_PROVEN_BUSINESS_IMPROVEMENT",
      changes: [{ dimension: "audience", before: "UNCERTAIN", after: "CONSTRUCTIVE_GAP" }],
    },
    history: [previous],
  });
  const markup = render(current);

  assert.match(markup, /Evidence-backed strength/);
  assert.match(markup, /Opportunity to clarify/);
  assert.match(markup, /Uncertain understanding/);
  assert.match(markup, /We repair shoes for households\./);
  assert.match(markup, /example\.test\/services/);
  assert.match(markup, /Conditional proposal/);
  assert.match(markup, /What changed since the previous reading/);
  assert.match(markup, /Previous reading/);
  assert.match(markup, /Comparable instrument and scope/);
  assert.doesNotMatch(markup, /\b\d+(?:\.\d+)?\s*%|confidence|probability of truth/i);
});

test("instrument failure is reported without presenting a company critique", () => {
  const failed = report({
    status: "NON_INFORMATIVE",
    cause: "INSTRUMENT_ERROR",
    execution: "NONE",
    dimensions: [],
    citations: [],
  });
  const markup = render(failed);

  assert.match(markup, /The instrument failed or did not pass its controls/);
  assert.doesNotMatch(markup, /Opportunity to clarify|Conditional proposal/);
});

const translatedRows = [
  "What it offers",
  "What outcome it communicates",
  "Evidence-backed strength",
  "Opportunity to clarify",
  "Unresolved interpretation",
  "Uncertain understanding",
  "The instrument failed or did not pass its controls. It cannot assess the company's communication.",
  "Rights to send these sources to the instrument are missing. Public visibility does not grant that permission.",
  "The citations expired and were removed. A new observation is needed.",
  "Acquisition was insufficient. A page or excerpt may be missing; this does not demonstrate a communication deficiency.",
  "The instrument found incompatible statements. They may concern different offers or periods; both sources remain open to review.",
  "The text permits multiple interpretations. The cause remains unresolved.",
  "The measurement did not run within the available budget.",
  "The instrument is unavailable. Economic classification does not replace this measurement.",
  "The instrument linked this question to an explicit public statement. This is a conditioned interpretation, not business verification.",
  "In the inspected quotations, the instrument did not find an explicit answer to this question. The scope is the sample, not all of the organization's communication.",
  "The information or judgment is insufficient to conclude. Instrument uncertainty is not a business defect.",
  "If both pages describe the same current offer, review the incompatible statements with their owners before changing them.",
  "If you intend to disclose this offer, specify the product or service alongside the current description, without adding unverified capabilities.",
  "If you intend to communicate whom this offer serves, name the customer group or use case alongside the described service.",
  "If you can support this offer's benefit and intend to communicate it, add a concrete outcome and its conditions, without guaranteeing what you cannot demonstrate.",
  "Conditional proposal",
  "There may also be deliberately limited disclosure, information outside this sample or an evaluator error. Review the evidence before deciding.",
  "Inspect quotations and basis",
  "After human review, reobserve the same pages with the same instrument. An interpretation change alone does not prove a business improvement.",
  "How your public offer is understood",
  "A reading of the inspected pages through an interpretation instrument. It does not represent all customers, search engines or assistants, and does not verify business reality.",
  "Reading awaiting reobservation",
  "Judgment reused over the same evidence; not an independent replica.",
  "What changed since the previous reading",
  "Comparable instrument and scope. The change concerns interpretation, not a demonstrated business result.",
  "These readings are not comparable: the instrument, scope or measurement availability changed.",
  "No change in the interpreted dimensions.",
  "Instrument, scope and history",
  "Own website; reader without private context; one execution or exact reuse. Market unknown.",
  "Coverage",
  "Selected pages inspected; not a site census.",
  "Incomplete acquisition or representation.",
  "Previous reading",
  "No other retained reading is available to compare yet.",
  "Permission to keep or show these quotations is no longer in place, so they were removed. A new reading needs current rights and a new observation.",
  "Review the proposals below. If you apply any, reobserve with the same instrument.",
  "Review the quotations before deciding: this reading is not enough to conclude.",
  "Nothing to clarify in this sample. Reobserve when you change these pages.",
  "In short",
  "Understood well",
  "Worth clarifying",
  "No conclusion yet",
  "Next step",
];

test("all new report copy resolves in the six supported locales", () => {
  for (const english of translatedRows) {
    assert.ok(translate("Texto en español", english, "es"));
    assert.equal(translate("Texto en español", english, "en"), english);
    for (const locale of ["de", "pt", "fr", "it"] as const) {
      const translated = translate("Texto en español", english, locale);
      assert.ok(translated.trim(), `${locale}: ${english}`);
      assert.notEqual(translated, english, `${locale} fell back to English: ${english}`);
    }
  }
  assert.equal(translate("Qué ofrece", "What it offers", "es"), "Qué ofrece");
  assert.equal(translate("Qué ofrece", "What it offers", "en"), "What it offers");
});


test("comparison exposes the complete exact basis and reports source conditions", () => {
  const value = publicUnderstandingSchema.parse({
    ...report(), sourceObservedAt: measuredAt, validUntil: "2026-10-16T10:00:00+00:00",
    contentExpiresAt: "2026-11-08T10:00:00+00:00",
    conditions: {languages: ["en"], sourceSet: ["https://example.test/services"], sampleSize: 1},
    sourceRights: [{url:"https://example.test/services",basisRef:"source-registry:synthetic-reviewed-grant",
      policyVersion:"first-observation-content-rights.v1",providerInput:true,publicOfferInput:true}],
    comparison: {previousReportId: "b".repeat(64),previousMeasuredAt: measuredAt,state:"COMPARABLE",
      reason:"SAME_CONDITIONED_INSTRUMENT",meaning:"INTERPRETATION_CHANGE_NOT_PROVEN_BUSINESS_IMPROVEMENT",
      changes:[{dimension:"offer",before:"STRENGTH",after:"STRENGTH",kind:"INTERPRETATION_BASIS_CHANGED",
        beforeQuotations:["We repair shoes.","Leather repairs only."],afterQuotations:["We repair shoes and boots."]}]},
  });
  const markup = render(value);
  assert.match(markup, /The cited basis changed/);
  assert.match(markup, /Leather repairs only\./);
  assert.match(markup, /We repair shoes and boots\./);
  assert.match(markup, /Source language and sample/);
  assert.match(markup, /Citation retention until/);
  assert.match(markup, /source-registry:synthetic-reviewed-grant/);
});


test("AXENT report references remain private and require the authorized citation basis", () => {
  const value = report();
  const ref = `public-understanding:${value.reportId}:offer:q1`;
  assert.equal(understandingReportReference(ref, value), value.reportId);
  assert.equal(understandingReportReference(ref.replace(value.reportId, "b".repeat(64)), value), null);
  assert.equal(understandingReportReference(ref.replace("q1", "q16"), value), null);
  assert.equal(understandingReportReference(ref, report({status: "NOT_MEASURED"})), null);
  assert.equal(understandingReportReference(ref, report({currentness: "EXPIRED"})), null);
  assert.equal(understandingReportReference(ref), null);
  const previous = report({reportId:"b".repeat(64),currentness:"HISTORICAL"});
  assert.equal(understandingReportReference(`public-understanding:${previous.reportId}:offer:q1`, report({history:[previous]})), previous.reportId);
});


const count = (markup: string, text: string) => markup.split(text).length - 1;

test("a quick synthesis comes first and each explanation or quotation appears once", () => {
  const markup = render(report());
  const synthesis = markup.indexOf("Understood well");
  assert.ok(synthesis > 0 && synthesis < markup.indexOf("pu-dimension"), "synthesis precedes the detail");
  assert.match(markup, /Worth clarifying<\/dt><dd>For whom/);
  assert.match(markup, /No conclusion yet<\/dt><dd>What outcome it communicates/);
  assert.match(markup, /Next step<\/dt><dd>Review the proposals below/);
  // The strength keeps its specific quotation inline; the full set is listed once.
  assert.equal(count(markup, "We repair shoes for households."), 2);
  assert.equal(count(markup, "Repairs are available in our workshop."), 1);
  assert.equal(count(markup, "There may also be deliberately limited disclosure"), 1);
  assert.equal(count(markup, "After human review, reobserve the same pages"), 1);
  assert.match(markup, /Inspect quotations and basis \(<!-- -->2<!-- -->\)|Inspect quotations and basis \(2\)/);
});

test("a single selected quotation is still shown on its strength", () => {
  const single = report({
    citations: [report().citations[0]],
    dimensions: [{ ...report().dimensions[0], citationIds: ["q1"] }],
  });
  const markup = render(single);
  assert.match(markup, /Next step<\/dt><dd>Nothing to clarify in this sample/);
  assert.equal(count(markup, "We repair shoes for households."), 2);
});

test("withdrawn content rights show why quotations disappeared, without a critique", () => {
  const markup = render(report({
    status: "NOT_MEASURED", cause: "CONTENT_RIGHTS_WITHDRAWN", currentness: "EXPIRED",
    citations: [], dimensions: [],
  }));
  assert.match(markup, /Permission to keep or show these quotations is no longer in place/);
  assert.doesNotMatch(markup, /We repair shoes|Opportunity to clarify|Understood well/);
});
