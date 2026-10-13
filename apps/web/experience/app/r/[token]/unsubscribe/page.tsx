import { poolReadingFor } from "@/lib/subscriber-server";
import { poolCopy } from "@/lib/marketing-pool-copy";
import { PoolUnsubscribe } from "@/components/pool-unsubscribe";
import "../../pool-reading.css";

// A link scanner opening this page unsubscribes nobody: only the confirm button does.
export const dynamic = "force-dynamic";
export const metadata = { title: "AXIGNAL", robots: { index: false, follow: false } };

export default async function Page({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const reading = await poolReadingFor(token);
  const copy = poolCopy(reading?.language);
  return <main className="pool-reading pool-reading-narrow" lang={reading?.language ?? "en"}>
    <header className="pool-reading-head">
      <a href="/" aria-label="AXIGNAL"><img src="/email/logo-440.png" width={132} height={38} alt="Axignal" /></a>
    </header>
    <h1>{copy.unsubscribeTitle}</h1>
    <p className="pool-reading-intro">{copy.unsubscribeBody}</p>
    <PoolUnsubscribe token={token} copy={{ button: copy.unsubscribeButton, done: copy.unsubscribed, failed: copy.unsubscribeFailed }} />
  </main>;
}
