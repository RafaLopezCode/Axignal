"use client";
import "./globals.css";
import "./typography.css";

// Root recovery is deliberately independent of locale, navigation and runtime
// providers. Retrying renders the page; it never submits an economic command.
export default function GlobalError({ retry }: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  return <html lang="es"><head><title>Retomar AXIGNAL</title></head><body>
    <main id="main" className="root-recovery">
      <a href="/" aria-label="AXIGNAL · Inicio"><img src="/brand/logo-light.svg" alt="AXIGNAL" width={180} height={54} /></a>
      <span className="eyebrow">AXIGNAL / RECUPERAR LA EXPERIENCIA</span>
      <h1>Retomemos el hilo.</h1>
      <p>No pudimos abrir la experiencia. Puedes volver a intentarlo o regresar al inicio.</p>
      <div className="recovery-actions">
        <button className="button primary" onClick={retry}>Volver a intentar</button>
        <a className="button secondary" href="/">Volver al inicio</a>
      </div>
    </main>
  </body></html>;
}
