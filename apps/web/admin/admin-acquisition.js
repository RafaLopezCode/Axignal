(() => {
  const bootstrapElement = document.getElementById('admin-bootstrap')
  if (!bootstrapElement) return
  let bootstrap = {}
  try {
    bootstrap = JSON.parse(bootstrapElement.textContent || '{}')
  } catch {
    return
  }
  if (bootstrap.currentSlug !== 'acquisition' || !bootstrap.acquisition) return
  const acquisition = bootstrap.acquisition
  const section = document.getElementById('admin-acquisition-observatory')
  const preview = document.getElementById('admin-domain-preview')
  const privacy = document.getElementById('admin-acquisition-privacy')
  const generated = document.getElementById('admin-acquisition-generated')
  const notes = document.getElementById('admin-acquisition-notes')
  const summary = document.getElementById('admin-acquisition-summary')
  const requestList = document.getElementById('admin-acquisition-request-list')
  if (!section) return
  section.hidden = false
  if (preview) preview.hidden = true
  if (privacy) privacy.textContent = acquisition.privacyClass || 'PRIVATE'
  if (generated) generated.textContent = acquisition.generatedAt || ''
  if (notes) {
    notes.replaceChildren()
    for (const value of acquisition.coverageNotes || []) {
      const p = document.createElement('p')
      p.textContent = value
      notes.append(p)
    }
  }
  const fact = (parent, label, value) => {
    const row = document.createElement('div')
    const term = document.createElement('span')
    term.textContent = label
    const data = document.createElement('strong')
    data.textContent = String(value)
    row.append(term, data)
    parent.append(row)
  }
  if (summary) {
    summary.replaceChildren()
    const panel = document.createElement('section')
    panel.className = 'admin-observatory-panel'
    const heading = document.createElement('h3')
    heading.textContent = 'Free weekly brief funnel'
    const facts = document.createElement('div')
    facts.className = 'admin-observatory-facts'
    fact(facts, 'Requests', acquisition.requestCount)
    fact(facts, 'Accepted coverage', acquisition.acceptedCount)
    fact(facts, 'Consented', acquisition.consentedCount)
    fact(facts, 'Delivery eligible', acquisition.deliveryEligibleCount)
    panel.append(heading, facts)
    summary.append(panel)
  }
  if (requestList) {
    requestList.replaceChildren()
    const requests = Array.isArray(acquisition.requests) ? acquisition.requests : []
    for (const request of requests) {
      const card = document.createElement('article')
      card.className = 'admin-xeed-card'
      const header = document.createElement('header')
      const heading = document.createElement('h3')
      heading.textContent = request.companyName
      const state = document.createElement('span')
      state.textContent = request.reviewState
      header.append(heading, state)
      const facts = document.createElement('div')
      facts.className = 'admin-observatory-facts'
      fact(facts, 'Domain', request.companyDomain)
      fact(facts, 'Coverage', request.coverageState)
      fact(facts, 'Consent', request.consentState)
      fact(facts, 'Delivery', request.deliveryEligible ? 'ELIGIBLE' : 'NOT ELIGIBLE')
      card.append(header, facts)
      requestList.append(card)
    }
  }
})()
