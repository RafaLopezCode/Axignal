(() => {
  const bootstrapElement = document.getElementById('admin-bootstrap')
  const app = document.getElementById('admin-app')
  if (!bootstrapElement || !app) return

  let bootstrap
  try {
    bootstrap = JSON.parse(bootstrapElement.textContent || '{}')
  } catch {
    app.dataset.state = 'error'
    return
  }

  const nav = document.getElementById('admin-nav')
  const principal = document.getElementById('admin-principal')
  const roles = document.getElementById('admin-role-summary')
  const breadcrumb = document.getElementById('admin-breadcrumb-current')
  const title = document.getElementById('admin-title')
  const eyebrow = document.getElementById('admin-eyebrow')
  const description = document.getElementById('admin-description')
  const domain = document.getElementById('axent-domain')
  const scopeList = document.getElementById('admin-scope-list')
  const availability = document.getElementById('admin-availability')

  const items = Array.isArray(bootstrap.navigation) ? bootstrap.navigation : []
  const current = items.find((item) => item.slug === bootstrap.currentSlug) || items[0]

  document.documentElement.dataset.axignalMode = 'admin'
  app.dataset.state = 'ready'
  app.dataset.currentDomain = current?.slug || 'none'

  if (principal) principal.textContent = bootstrap.principalId || 'Admin'
  if (roles) {
    const values = Array.isArray(bootstrap.roles) ? bootstrap.roles : []
    roles.textContent = values.length ? values.join(' · ') : 'No active Admin role'
  }

  if (nav) {
    const section = document.createElement('section')
    section.className = 'admin-nav-section'
    const cap = document.createElement('span')
    cap.className = 'admin-nav-cap'
    cap.textContent = 'AXIGNAL OPERATIONS'
    section.append(cap)

    for (const item of items) {
      const link = document.createElement('a')
      link.className = 'admin-nav-link'
      link.href = `/admin/${encodeURIComponent(item.slug)}`
      link.textContent = item.label
      link.dataset.adminDomain = item.slug
      if (item.slug === current?.slug) link.setAttribute('aria-current', 'page')
      section.append(link)
    }
    nav.replaceChildren(section)
  }

  if (current) {
    document.title = `AXIGNAL · Admin · ${current.label}`
    if (availability) {
      availability.textContent =
        current.slug === 'command-center'
          ? 'AO-04 EXECUTIVE PROJECTION'
          : current.slug === 'xeeds' || current.slug === 'axigland-quality'
            ? 'AO-05 RUNTIME OBSERVATORY'
            : 'ADMIN DOMAIN'
    }
    if (breadcrumb) breadcrumb.textContent = current.label
    if (title) title.textContent = current.label
    if (eyebrow) eyebrow.textContent = current.eyebrow
    if (description) description.textContent = current.description
    if (domain) domain.textContent = current.label
  }

  const commandCenter = bootstrap.commandCenter
  const commandCenterSection = document.getElementById('admin-command-center')
  const domainPreview = document.getElementById('admin-domain-preview')
  const metricGroups = document.getElementById('admin-metric-groups')
  const commandCompleteness = document.getElementById('command-center-completeness')
  const commandAsOf = document.getElementById('command-center-asof')

  const renderMetricValue = (metric) => {
    if (metric.value == null) return metric.completeness || 'UNKNOWN'
    if (metric.unit === 'CURRENCY') return `${metric.value} ${metric.currency || ''}`.trim()
    if (metric.unit === 'RATIO') return metric.value
    return metric.value
  }

  if (current?.slug === 'command-center' && commandCenter && commandCenterSection && metricGroups) {
    commandCenterSection.hidden = false
    if (domainPreview) domainPreview.hidden = true
    if (commandCompleteness) commandCompleteness.textContent = commandCenter.completeness || 'UNKNOWN'
    if (commandAsOf) commandAsOf.textContent = commandCenter.asOf ? `As of ${commandCenter.asOf}` : ''
    const byGroup = new Map()
    for (const metric of commandCenter.metrics || []) {
      const values = byGroup.get(metric.group) || []
      values.push(metric)
      byGroup.set(metric.group, values)
    }
    metricGroups.replaceChildren()
    for (const [group, metrics] of byGroup) {
      const section = document.createElement('section')
      section.className = 'admin-metric-group'
      const heading = document.createElement('h3')
      heading.textContent = group
      section.append(heading)
      const grid = document.createElement('div')
      grid.className = 'admin-metric-grid'
      for (const metric of metrics) {
        const card = document.createElement('article')
        card.className = 'admin-metric-card'
        card.dataset.completeness = metric.completeness || 'UNKNOWN'

        const label = document.createElement('span')
        label.className = 'admin-metric-label'
        label.textContent = metric.label

        const value = document.createElement('strong')
        value.className = 'admin-metric-value'
        value.textContent = renderMetricValue(metric)

        const state = document.createElement('span')
        state.className = 'admin-metric-state'
        state.textContent = metric.completeness || 'UNKNOWN'

        const details = document.createElement('details')
        details.className = 'admin-metric-lineage'
        const summary = document.createElement('summary')
        summary.textContent = 'Why is this number here?'
        const body = document.createElement('dl')
        const rows = [
          ['Definition', metric.purpose],
          ['Window', metric.defaultWindow],
          ['Metric definition', metric.expectedMethodologyVersion],
          ['Source method', metric.methodologyVersion || 'Unavailable'],
          ['Period start', metric.periodStart || 'Unavailable'],
          ['Period end', metric.periodEnd || 'Unavailable'],
          ['Comparison', metric.comparisonState],
          ['Source projection', metric.sourceProjectionId],
          ['Source record types', (metric.sourceRecordTypes || []).join(', ')],
          ['Source records', (metric.sourceRecordIds || []).join(', ') || 'None observed'],
          ['Unknown / partial reason', metric.unknownReason || '—'],
        ]
        for (const [term, descriptionText] of rows) {
          const dt = document.createElement('dt')
          const dd = document.createElement('dd')
          dt.textContent = term
          dd.textContent = descriptionText || '—'
          body.append(dt, dd)
        }
        details.append(summary, body)
        card.append(label, value, state, details)
        grid.append(card)
      }
      section.append(grid)
      metricGroups.append(section)
    }
  }

  const observatory = bootstrap.xeedObservatory
  const observatorySection = document.getElementById('admin-observatory')
  const observatoryCompleteness = document.getElementById('admin-observatory-completeness')
  const observatoryAsOf = document.getElementById('admin-observatory-asof')
  const observatoryNotes = document.getElementById('admin-observatory-notes')
  const observatorySummary = document.getElementById('admin-observatory-summary')
  const xeedList = document.getElementById('admin-xeed-list')

  const valueOrUnknown = (value, completeness) => {
    if (value === null || value === undefined || value === '') return completeness || 'UNKNOWN'
    return String(value)
  }

  const addFact = (container, label, value, completeness = 'KNOWN') => {
    const row = document.createElement('div')
    row.className = 'admin-observatory-fact'
    const term = document.createElement('span')
    term.textContent = label
    const strong = document.createElement('strong')
    strong.textContent = valueOrUnknown(value, completeness)
    const state = document.createElement('em')
    state.textContent = completeness
    row.append(term, strong, state)
    container.append(row)
  }

  if (
    (current?.slug === 'xeeds' || current?.slug === 'axigland-quality') &&
    observatory &&
    observatorySection
  ) {
    observatorySection.hidden = false
    if (domainPreview) domainPreview.hidden = true
    if (observatoryCompleteness) observatoryCompleteness.textContent = observatory.completeness || 'UNKNOWN'
    if (observatoryAsOf) observatoryAsOf.textContent = observatory.asOf ? `As of ${observatory.asOf}` : ''

    if (observatoryNotes) {
      observatoryNotes.replaceChildren()
      for (const noteText of observatory.coverageNotes || []) {
        const note = document.createElement('p')
        note.textContent = noteText
        observatoryNotes.append(note)
      }
    }

    if (observatorySummary) {
      observatorySummary.replaceChildren()
      const axigland = observatory.axigland || {}
      const summary = document.createElement('section')
      summary.className = 'admin-observatory-panel'
      const heading = document.createElement('h3')
      heading.textContent = current.slug === 'axigland-quality' ? 'AXIGLAND runtime evidence' : 'Cross-Xeed evidence'
      summary.append(heading)
      const facts = document.createElement('div')
      facts.className = 'admin-observatory-facts'
      addFact(facts, 'Canonical admissions emitted', axigland.canonicalAdmissionEvents, 'KNOWN')
      addFact(facts, 'Observations reused', axigland.observationsReused, 'KNOWN')
      addFact(facts, 'Observations added', axigland.observationsAdded, 'KNOWN')
      addFact(facts, 'Reuse ratio', axigland.reuseRatio, axigland.reuseRatio == null ? 'UNKNOWN' : 'KNOWN')
      addFact(facts, 'AXIGLAND growth', axigland.growthState, axigland.growthCompleteness)
      addFact(facts, 'Currentness', axigland.currentnessState, axigland.currentnessCompleteness)
      addFact(facts, 'Provenance', axigland.provenanceState, axigland.provenanceCompleteness)
      addFact(facts, 'Contradictions', axigland.contradictionState, axigland.contradictionCompleteness)
      addFact(facts, 'Identity resolution', axigland.identityResolutionState, axigland.identityResolutionCompleteness)
      summary.append(facts)

      const lineage = document.createElement('details')
      lineage.className = 'admin-metric-lineage'
      const lineageSummary = document.createElement('summary')
      lineageSummary.textContent = 'Inspect AXIGLAND runtime lineage'
      const pre = document.createElement('p')
      pre.textContent = `Learning events: ${(axigland.sourceLearningEventIds || []).join(', ') || 'None observed'} · Admin records: ${(axigland.sourceAdminRecordIds || []).join(', ') || 'None observed'}`
      lineage.append(lineageSummary, pre)
      summary.append(lineage)
      observatorySummary.append(summary)
    }

    if (xeedList) {
      xeedList.replaceChildren()
      const xeeds = Array.isArray(observatory.xeeds) ? observatory.xeeds : []
      if (!xeeds.length) {
        const empty = document.createElement('article')
        empty.className = 'admin-observatory-empty'
        empty.innerHTML = '<strong>No governed Xeed runtime evidence observed</strong><p>This does not prove that zero Xeeds exist. It means the connected Learning/Admin evidence sources do not currently identify one.</p>'
        xeedList.append(empty)
      }
      for (const xeed of xeeds) {
        const card = document.createElement('article')
        card.className = 'admin-xeed-card'
        const header = document.createElement('header')
        const heading = document.createElement('h3')
        heading.textContent = xeed.xeedId
        const state = document.createElement('span')
        state.textContent = valueOrUnknown(xeed.lifecycleState, xeed.lifecycleCompleteness)
        header.append(heading, state)

        const facts = document.createElement('div')
        facts.className = 'admin-observatory-facts'
        addFact(facts, 'Learning events', xeed.learningEventCount, 'KNOWN')
        addFact(facts, 'Currentness', xeed.currentnessState, xeed.currentnessCompleteness)
        addFact(facts, 'Observation coverage', xeed.observationCoverageState, xeed.observationCoverageCompleteness)
        addFact(facts, 'First activity', xeed.firstActivityAt, xeed.firstActivityAt ? 'KNOWN' : 'UNKNOWN')
        addFact(facts, 'First useful Xignal', xeed.firstUsefulXignalAt, xeed.firstUsefulXignalAt ? 'KNOWN' : 'UNKNOWN')
        addFact(facts, 'Time to first value (ms)', xeed.timeToFirstUsefulXignalMs, xeed.timeToFirstUsefulXignalMs == null ? 'UNKNOWN' : 'KNOWN')
        addFact(facts, 'Observations reused', xeed.observationsReused, 'KNOWN')
        addFact(facts, 'Observations added', xeed.observationsAdded, 'KNOWN')
        addFact(facts, 'Reuse ratio', xeed.reuseRatio, xeed.reuseRatio == null ? 'UNKNOWN' : 'KNOWN')
        addFact(facts, 'Xignals emitted', xeed.xignalsEmitted, 'KNOWN')
        addFact(facts, 'Canonical admissions', xeed.canonicalAdmissions, 'KNOWN')
        addFact(facts, 'Direct event cost coverage', xeed.directCostCompleteness, xeed.directCostCompleteness)
        addFact(facts, 'Shared cost attribution', xeed.sharedCostCompleteness, xeed.sharedCostCompleteness)
        addFact(facts, 'Triggered cost attribution', xeed.triggeredCostCompleteness, xeed.triggeredCostCompleteness)
        addFact(facts, 'Revenue attribution', xeed.revenueAttributionCompleteness, xeed.revenueAttributionCompleteness)

        const details = document.createElement('details')
        details.className = 'admin-metric-lineage'
        const detailsSummary = document.createElement('summary')
        detailsSummary.textContent = 'Diagnose this Xeed'
        const body = document.createElement('p')
        const costs = (xeed.knownCostsByCurrency || []).map(([currency, amount]) => `${amount} µ${currency}`).join(', ')
        body.textContent = `Observed direct costs: ${costs || 'UNKNOWN'} · unknown-cost events: ${xeed.unknownCostEventCount} · failed events: ${xeed.failedEventCount} · partial events: ${xeed.partialEventCount} · shared: ${xeed.sharedCostReason} · triggered: ${xeed.triggeredCostReason} · learning lineage: ${(xeed.sourceLearningEventIds || []).join(', ') || 'None'}`
        details.append(detailsSummary, body)

        card.append(header, facts, details)
        xeedList.append(card)
      }
    }
  }

  if (scopeList) {
    const scopes = Array.isArray(bootstrap.scopes) ? bootstrap.scopes : []
    scopeList.replaceChildren()
    for (const scope of scopes) {
      const pill = document.createElement('span')
      pill.className = 'admin-scope-pill'
      pill.textContent = scope
      scopeList.append(pill)
    }
  }

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return
    const links = [...document.querySelectorAll('.admin-nav-link')]
    if (!links.length) return
    const active = document.activeElement
    const currentIndex = links.indexOf(active)
    if (currentIndex < 0) return
    event.preventDefault()
    const delta = event.key === 'ArrowDown' ? 1 : -1
    const target = (currentIndex + delta + links.length) % links.length
    links[target].focus()
  })
})()
