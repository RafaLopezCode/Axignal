/** Presentation-only bootstrap. Without scripting, all original faces load normally. */
export const firstReadingScript = String.raw`(() => {
  const root = document.documentElement;
  if (!window.matchMedia('(max-width: 700px) and (max-height: 900px)').matches ||
      (location.hash && location.hash !== '#lab-top')) return;
  root.setAttribute('data-lab-first-reading', '');
  let released = false;
  let observer;
  let frame;
  const events = ['scroll', 'pointerdown', 'keydown', 'resize', 'pagehide'];
  const release = () => {
    if (released) return;
    released = true;
    root.removeAttribute('data-lab-first-reading');
    observer?.disconnect();
    if (frame !== undefined) cancelAnimationFrame(frame);
    events.forEach(name => window.removeEventListener(name, release));
    const ready = document.fonts?.load('400 16px "Bic Notes Lab"') ?? Promise.resolve();
    Promise.resolve(ready).catch(() => {}).then(() => {
      window.dispatchEvent(new Event('axignal:secondary-type-settled'));
    });
  };
  events.forEach(name => window.addEventListener(name, release, {passive:true}));
  const dom = document.readyState === 'loading'
    ? new Promise(resolve => document.addEventListener('DOMContentLoaded', resolve, {once:true}))
    : Promise.resolve();
  const paint = new Promise(resolve => {
    if (performance.getEntriesByName('first-contentful-paint').length ||
        !window.PerformanceObserver ||
        !PerformanceObserver.supportedEntryTypes?.includes('paint')) return resolve();
    observer = new PerformanceObserver(list => {
      if (list.getEntries().some(entry => entry.name === 'first-contentful-paint')) {
        observer.disconnect();
        resolve();
      }
    });
    observer.observe({type:'paint', buffered:true});
  });
  // Sample readiness after layout has actually requested the reading faces.
  // Reuse CSS-selected fonts instead of preparing additional optical sizes.
  Promise.all([dom, paint])
    .then(() => released ? undefined : document.fonts?.ready)
    .catch(() => {}).then(() => {
    if (released) return;
    frame = requestAnimationFrame(() => {
      frame = requestAnimationFrame(release);
    });
  });
})();`;
