"use client";

import { useEffect, useId, useRef, useState } from "react";
import { ChevronDown, CircleHelp, Database, FileSearch, LockKeyhole, RefreshCw, Search, SearchX, ShieldAlert } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { collections, domainSections, label, readOperationalProjection, scalar, visibleFields, type JsonValue, type OperationalDomain, type OperationalProjection } from "@/lib/admin-projections";
import { formatValue, humanValue, isRecord, isUnknown, matchesRecord, recordReference, recordTitle, text, type OperationalRecord } from "@/lib/admin-presentation";
import type { Locale } from "@/lib/languages";

const extraFields = new Set(["purpose", "owner", "environment", "family", "action", "outcome", "count", "changeCount", "sampleSize", "questionServed", "decisionServed", "formulaOrCodingRule", "unsupportedCanonicalWriteTargetCount", "deliveryEligibleCount", "marketingEventCount", "anonymousSessionCount", "attributedRequestCount", "received", "succeeded", "retryPending", "deadLetter", "rejected", "errors", "errorCount", "quotaRemaining", "rateLimited", "reviewState", "consentState", "deliveryEligible", "requestedAt", "effectiveAt", "occurredAt", "lastObservedAt", "billedMinor", "paidMinor", "refundedMinor", "creditNoteMinor", "processorFeeMinor", "settledGrossMinor", "settledNetMinor", "accountedMinor", "infrastructureCostMinor", "businessExpenseMinor"]);
const extraCollections = new Set(["policyChanges", "totals", "webhooks", "authEvents"]);
const sourceKeys = ["sourceRecordIds", "sourceLearningEventIds", "sourceAdminRecordIds", "sourceRefs", "sourceRecordTypes", "unknownReason", "sourceProjectionId", "methodologyVersion", "expectedMethodologyVersion", "metricId", "reason", "recordId", "sourceRef", "sourceObjectRef", "policyId", "requiredScope", "resultCode", "unit", "periodStart", "periodEnd", "coverageNotes", "interpretationLimits", "missingEvidence", "invalidReasons", "authorityBoundary", "scopes", "instrumentId", "instrumentVersion", "windowStart", "windowEnd", "uncertainty", "subjectRef"];
const PAGE_SIZE = 8;
const time = (value: string, locale: Locale) => new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short", timeZone: "Europe/Madrid" }).format(new Date(value));

export function Sources({ record, locale }: { record: OperationalRecord; locale: Locale }) {
  const entries = sourceKeys.flatMap(key => {
    const value = record[key];
    if (value === undefined || value === null || (Array.isArray(value) && !value.length)) return [];
    const values = Array.isArray(value) ? value.filter(item => item !== null && typeof item !== "object") : typeof value !== "object" ? [value] : [];
    return values.length ? [{ key, values }] : [];
  });
  return <details className="admin-source-details">
    <summary><FileSearch size={15} aria-hidden="true" /><span>{label("sources", locale)}</span><ChevronDown className="admin-disclosure-chevron" size={14} aria-hidden="true" /></summary>
    <div className="admin-source-body">
      {!entries.length ? <p>{label("noSources", locale)}</p> : <dl>{entries.map(({ key, values }) => <div key={key}>
        <dt>{text(key, locale)}</dt>
        <dd>{values.map((value, index) => <span key={index}>{key === "unknownReason" && humanValue(value, locale) !== String(value) && <span>{humanValue(value, locale)}</span>}{["periodStart", "periodEnd"].includes(key) ? formatValue(key, value, record, locale) : <code>{String(value)}</code>}</span>)}</dd>
      </div>)}</dl>}
    </div>
  </details>;
}

function Status({ value, locale }: { value: JsonValue; locale: Locale }) {
  // Styling describes the supplied state; it never computes a health verdict.
  const tone = isUnknown(value) ? "unknown" : ["PARTIAL", "STALE", "DEGRADED", "PENDING"].includes(String(value)) ? "limited" : "neutral";
  return <span className="admin-state" data-tone={tone}>{isUnknown(value) && <CircleHelp size={13} aria-hidden="true" />}{scalar(value, locale)}</span>;
}

function MetricList({ items, locale, nested = false }: { items: OperationalRecord[]; locale: Locale; nested?: boolean }) {
  const Heading = nested ? "h4" : "h3";
  const [filter, setFilter] = useState("all");
  const known = items.filter(item => !isUnknown(item.value)).length;
  const shown = items.filter(item => filter === "all" || (filter === "available" ? !isUnknown(item.value) : isUnknown(item.value)));
  return <div className="admin-metrics">
    <div className="admin-metric-controls" role="group" aria-label={label("metrics", locale)}>
      {([ ["all", items.length], ["available", known], ["missing", items.length - known] ] as const).map(([key, count]) => <button key={key} aria-pressed={filter === key} onClick={() => setFilter(key)}>{text(key, locale)}<span>{count}</span></button>)}
    </div>
    {known === 0 && <p className="admin-coverage-note"><CircleHelp size={16} aria-hidden="true" />{text("noValues", locale)}</p>}
    <div className="admin-metric-list" aria-live="polite">
      {shown.map((item, index) => <article className="admin-metric-row" key={String(item.metricId ?? index)}>
        <div className="admin-metric-name"><Heading>{recordTitle(item, locale, index)}</Heading>{typeof item.group === "string" && <span>{groupName(item.group, locale)}</span>}</div>
        <strong className="admin-metric-value" data-unknown={isUnknown(item.value)}>{formatValue("value", item.value ?? null, item, locale)}</strong>
        <div className="admin-metric-status">{(!isUnknown(item.value) || !isUnknown(item.completeness)) && <Status value={item.completeness ?? "UNKNOWN"} locale={locale} />}</div>
        <Sources record={item} locale={locale} />
      </article>)}
      {!shown.length && <p className="admin-empty-inline">{label("empty", locale)}</p>}
    </div>
  </div>;
}

function groupName(group: string, locale: Locale) {
  const groups: Record<string, string> = { BUSINESS: "business", XEEDS: "xeeds", AXIGLAND: "axigland", SYSTEM: "state", STRATEGIC: "measurementRegistry" };
  return groups[group.toUpperCase()] ? text(groups[group.toUpperCase()], locale) : "";
}

function Collection({ name, items, locale, depth }: { name: string; items: JsonValue[]; locale: Locale; depth: number }) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const searchId = useId();
  const headingId = useId();
  const result = items.map((item, index) => ({ item, index })).filter(({ item, index }) => isRecord(item) ? matchesRecord(item, query, locale, index) : scalar(item, locale).toLocaleLowerCase(locale).includes(query.toLocaleLowerCase(locale)));
  const lastPage = Math.max(0, Math.ceil(result.length / PAGE_SIZE) - 1);
  const currentPage = Math.min(page, lastPage);
  const start = currentPage * PAGE_SIZE;
  return <section className="admin-reading-group" aria-labelledby={headingId}>
    <div className="admin-group-heading"><h3 id={headingId}>{text(name, locale)}<span className="admin-count">{items.length}</span></h3>
      {items.length > PAGE_SIZE && <label className="admin-collection-search" htmlFor={searchId}><Search size={16} aria-hidden="true" /><input id={searchId} type="search" aria-label={`${text("search", locale)}: ${text(name, locale)}`} placeholder={text("search", locale)} value={query} onChange={event => { setQuery(event.target.value); setPage(0); }} /></label>}
    </div>
    {!items.length ? <div className="admin-empty-inline"><Database size={18} aria-hidden="true" /><p>{label("empty", locale)}</p></div> : !result.length ? <div className="admin-empty-inline"><SearchX size={20} aria-hidden="true" /><p role="status">{text("noMatches", locale)}</p><button className="text-link" onClick={() => { setQuery(""); setPage(0); }}>{text("clear", locale)}</button></div> : <>
      <div className="admin-record-list">{result.slice(start, start + PAGE_SIZE).map(({ item, index }) => isRecord(item) ? <article className="admin-record-card" key={`${recordReference(item) ?? name}:${index}`}>
        <header><div><h4>{recordTitle(item, locale, index)}</h4>{recordReference(item) && recordReference(item) !== recordTitle(item, locale, index) && <p className="admin-record-reference"><span>{text("identity", locale)}: </span><code>{recordReference(item)}</code></p>}</div>{item.completeness !== undefined && <Status value={item.completeness} locale={locale} />}</header>
        <Reading record={item} locale={locale} depth={depth + 1} /><Sources record={item} locale={locale} />
      </article> : <p key={index}>{scalar(item, locale)}</p>)}</div>
      {items.length > PAGE_SIZE && <div className="admin-pagination"><p role="status">{text("shown", locale)} {start + 1}–{Math.min(start + PAGE_SIZE, result.length)} {text("of", locale)} {result.length}</p><div><button className="button secondary" disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)}>{text("previous", locale)}</button><button className="button secondary" disabled={currentPage === lastPage} onClick={() => setPage(currentPage + 1)}>{text("next", locale)}</button></div></div>}
    </>}
  </section>;
}

export function Reading({ record, locale, depth = 0 }: { record: OperationalRecord; locale: Locale; depth?: number }) {
  const fields = Object.entries(record).filter(([key, value]) => (visibleFields.has(key) || extraFields.has(key)) && (value === null || typeof value !== "object") && key !== "completeness");
  const children = Object.entries(record).filter(([key, value]) => (collections.has(key) || extraCollections.has(key)) && value !== null && typeof value === "object");
  return <>
    {fields.length > 0 && <dl className="admin-reading-values">{fields.map(([key, value]) => <div key={key}><dt>{text(key, locale)}</dt><dd>{["state", "health", "outcome", "credentialState"].includes(key) ? <Status value={value} locale={locale} /> : formatValue(key, value, record, locale)}</dd></div>)}</dl>}
    {depth < 3 && children.map(([key, value]) => {
      if (key === "metrics" && Array.isArray(value))
        return <MetricList key={key} items={value.filter(isRecord)} locale={locale} />;
      if (key === "alerts" && Array.isArray(value) && value.length > 0)
        return <section className="admin-reading-group" key={key} aria-label={text(key, locale)}>
          <div className="admin-group-heading"><h3>{text(key, locale)}</h3></div>
          <MetricList nested items={value.filter(isRecord).map(item => ({ ...item, value: item.count ?? null }))} locale={locale} />
        </section>;
      if (Array.isArray(value))
        return <Collection key={key} name={key} items={value} locale={locale} depth={depth} />;
      if (isRecord(value))
        return <section className="admin-reading-group" key={key} aria-label={text(key, locale)}>
          <div className="admin-group-heading"><h3>{text(key, locale)}</h3>{value.completeness !== undefined && <Status value={value.completeness} locale={locale} />}</div>
          <Reading record={value} locale={locale} depth={depth + 1} /><Sources record={value} locale={locale} />
        </section>;
      return null;
    })}
  </>;
}

export function AdminOperationalPanel({ domain }: { domain: OperationalDomain }) {
  const { locale } = useLocale();
  const [retry, setRetry] = useState(0);
  const [state, setState] = useState<{ domain: OperationalDomain; data: OperationalProjection | null; error: string | null; readAt: string | null }>({ domain, data: null, error: null, readAt: null });
  const retryButton = useRef<HTMLButtonElement>(null);
  const restoreRefreshFocus = useRef(false);
  useEffect(() => {
    const controller = new AbortController();
    setState({ domain, data: null, error: null, readAt: null });
    void (async () => {
      try {
        const data = await readOperationalProjection(domain, controller.signal);
        if (!controller.signal.aborted) setState({ domain, data, error: null, readAt: new Date().toISOString() });
      } catch (error) {
        if (!controller.signal.aborted) setState({ domain, data: null, error: error instanceof Error && ["session", "denied"].includes(error.message) ? error.message : "unavailable", readAt: null });
      }
    })();
    return () => controller.abort();
  }, [domain, retry]);
  const current = state.domain === domain ? state : null;
  const loading = !current || (!current.data && !current.error);
  useEffect(() => {
    if (!loading && restoreRefreshFocus.current) {
      restoreRefreshFocus.current = false;
      retryButton.current?.focus({ preventScroll: true });
    }
  }, [loading]);
  return <div className="admin-operational">
    <div className="admin-reading-toolbar">
      <div className="admin-reading-meta"><LockKeyhole size={15} aria-hidden="true" /><span>{text("readOnly", locale)}</span>{current?.readAt && <time dateTime={current.readAt} title={label("readAt", locale)}>{time(current.readAt, locale)}</time>}</div>
      <button ref={retryButton} className="button secondary" disabled={loading} onClick={() => { restoreRefreshFocus.current = true; setRetry(value => value + 1); }}><RefreshCw size={15} aria-hidden="true" />{label(loading ? "loading" : "refresh", locale)}</button>
    </div>
    <div className="admin-reader-live" role="status" aria-live="polite">{loading ? label("loading", locale) : current?.data ? text("updated", locale) : ""}</div>
    {loading && <div className="admin-loading" aria-hidden="true"><div /><div /><div /></div>}
    {current?.error && <div className="admin-error" role="alert"><ShieldAlert size={24} aria-hidden="true" /><div><h2>{label(current.error, locale)}</h2><p>{current.error === "unavailable" ? label("notes", locale) : text("readOnly", locale)}</p><button className="button secondary" onClick={() => { restoreRefreshFocus.current = true; setRetry(value => value + 1); }}>{text("retry", locale)}</button></div></div>}
    {current?.data && <div className="admin-reading-content">{domainSections[domain].map(key => {
      const original = current.data![key]!;
      // Distinct operator tasks over the same authorized source; never duplicate or infer data.
      const record = key === "xeedObservatory" ? Object.fromEntries(Object.entries(original).filter(([name]) => domain === "focus" ? name !== "axigland" : name !== "xeeds")) : original;
      const timestamp = record.asOf ?? record.generatedAt;
      return <section className="admin-reading-section" key={key} aria-labelledby={`reading-${key}`}>
        <header className="admin-section-heading"><div><h2 id={`reading-${key}`}>{label(key, locale)}</h2>{typeof timestamp === "string" && Number.isFinite(Date.parse(timestamp)) && <p className="admin-reading-time">{label("observedAt", locale)} <time dateTime={timestamp}>{time(timestamp, locale)}</time></p>}</div>{record.completeness !== undefined && <Status value={record.completeness} locale={locale} />}</header>
        <Reading record={record} locale={locale} /><Sources record={record} locale={locale} />
      </section>;
    })}</div>}
    <p className="admin-reader-footnote"><CircleHelp size={15} aria-hidden="true" />{label("notes", locale)}</p>
  </div>;
}
