(() => {
  const STATUS_URL = '/api/acquisition/status'
  const EVENT_URL = '/api/acquisition/events'
  const SESSION_KEY = 'axignal.acquisition.session.v1'
  const initialUrl = new URL(window.location.href)
  const utm = {
    utmSource: initialUrl.searchParams.get('utm_source'),
    utmMedium: initialUrl.searchParams.get('utm_medium'),
    utmCampaign: initialUrl.searchParams.get('utm_campaign'),
    utmContent: initialUrl.searchParams.get('utm_content'),
    utmTerm: initialUrl.searchParams.get('utm_term')
  }
  let enabled = false
  let lastChapter = null

  function token(bytes = 12) {
    const data = new Uint8Array(bytes)
    crypto.getRandomValues(data)
    return Array.from(data, value => value.toString(16).padStart(2, '0')).join('')
  }

  function sessionRef() {
    let value = sessionStorage.getItem(SESSION_KEY)
    if (!value) {
      value = 'session:' + token(16)
      sessionStorage.setItem(SESSION_KEY, value)
    }
    return value
  }

  function eventId() {
    return 'mkt:' + token(16)
  }

  async function send(kind, extra = {}) {
    if (!enabled) return
    const body = {
      eventId: eventId(),
      sessionRef: sessionRef(),
      kind,
      occurredAt: new Date().toISOString(),
      surface: 'landing',
      locale: (document.documentElement.lang || 'en').slice(0, 2),
      path: window.location.pathname,
      referrer: document.referrer || null,
      ...utm,
      ...extra
    }
    try {
      await fetch(EVENT_URL, {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
        body: JSON.stringify(body),
        keepalive: true
      })
    } catch {
      // Telemetry must never degrade the public product.
    }
  }

  async function boot() {
    try {
      const response = await fetch(STATUS_URL, {headers: {Accept: 'application/json'}})
      const data = await response.json()
      enabled = response.ok && data.enabled === true && data.model === 'OBSERVED_TOUCH_V1'
    } catch {
      enabled = false
    }
    if (!enabled) return
    void send('LANDING_VIEWED')
    const chapter = Number(document.body.dataset.chapter || 0)
    if (chapter >= 1 && chapter <= 15) {
      lastChapter = chapter
      void send('CHAPTER_VIEWED', {chapter})
    }
  }

  const observer = new MutationObserver(() => {
    if (!enabled) return
    const chapter = Number(document.body.dataset.chapter || 0)
    if (chapter >= 1 && chapter <= 15 && chapter !== lastChapter) {
      lastChapter = chapter
      void send('CHAPTER_VIEWED', {chapter})
    }
  })
  observer.observe(document.body, {attributes: true, attributeFilter: ['data-chapter']})

  document.addEventListener('click', event => {
    if (!enabled || !(event.target instanceof Element)) return
    const target = event.target.closest('button,a')
    if (!target) return
    let cta = null
    if (target.matches('[data-newsletter-trigger]')) cta = 'weekly-brief-request'
    else if (target.matches('.seed-cta')) cta = 'plant-xeed'
    else if (target.matches('.login,.mobile-login')) cta = 'login'
    if (cta) void send('CTA_ACTIVATED', {cta})
  })

  window.AXIGNAL_ACQUISITION = Object.freeze({
    sessionRef,
    markWeeklyBriefOpened: () => send('WEEKLY_BRIEF_OPENED', {cta: 'weekly-brief-request'})
  })

  void boot()
})()
