import { notFound } from "next/navigation";
import { poolReadingFor } from "@/lib/subscriber-server";
import { poolCopy } from "@/lib/marketing-pool-copy";
import "../pool-reading.css";

// A recipient's reading: private by link, never indexed, read at request time.
export const dynamic = "force-dynamic";
export const metadata = { title: "AXIGNAL", robots: { index: false, follow: false } };

export default async function Page({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const reading = await poolReadingFor(token);
  if (!reading) notFound();
  const copy = poolCopy(reading.language);
  const host = (url: string | null) => { try { return url ? new URL(url).hostname.replace(/^www\./, "") : null; } catch { return null; } };
  return <main className="pool-reading" lang={reading.language ?? "en"}>
    <header className="pool-reading-head">
      <a href="/" aria-label="AXIGNAL"><img src="/email/logo-440.png" width={132} height={38} alt="Axignal" /></a>
    </header>
    <section className="pool-reading-hero">
      <div>
        <p className="pool-reading-eyebrow">{copy.eyebrow}</p>
        <p className="pool-reading-meta">{reading.domain}{reading.studiedAt ? ` · ${copy.observed} ${reading.studiedAt.slice(0, 10)}` : ""}</p>
        <h1>{copy.title.replace("{name}", reading.name)}</h1>
        <p className="pool-reading-intro">{copy.intro}</p>
      </div>
      <img className="pool-reading-observer" src="/email/observer-laptop-480.png" width={240} height={272} alt="" />
    </section>
    <ol className="pool-reading-findings">
      {reading.findings.map((f, i) => <li key={f.kind + f.code} data-state={f.state}
        id={reading.findings.findIndex(x => x.family === f.family) === i ? f.family : undefined}>
        <p className="pool-reading-family">{copy.families[f.family as keyof typeof copy.families] ?? f.family}</p>
        <p className="pool-reading-statement">{f.statement}</p>
        <p className="pool-reading-source">{copy.states[f.state] ?? f.state}{f.source && host(f.source) ? <> · {copy.source}: <a href={f.source} rel="noreferrer noopener nofollow" target="_blank">{host(f.source)}</a></> : null}</p>
      </li>)}
    </ol>
    <p className="pool-reading-actions">
      <a className="button primary" href="/">{copy.cta}</a>
      <a className="text-link" href={`/r/${token}/unsubscribe`}>{copy.unsubscribeLink}</a>
    </p>
  </main>;
}
