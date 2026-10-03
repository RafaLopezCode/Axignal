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
            : current.slug === 'axent-brain'
              ? 'AO-06 COGNITIVE OBSERVATORY'
              : current.slug === 'governance'
                ? 'AO-07 GOVERNANCE CONTROL'
                : current.slug === 'customers-crm'
                  ? 'AO-09 CUSTOMER OPERATIONS'
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
      heading.textContent = current.slug === 'axigland-quality' ? 'AXIGLAND runtime evidence' : 'Cross-observation evidence'
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
        empty.innerHTML = '<strong>No governed Observation Focus runtime evidence observed</strong><p>This does not prove that zero Observation Focuses exist. It means the connected Learning/Admin evidence sources do not currently identify one.</p>'
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
        addFact(facts, 'First useful Signal', xeed.firstUsefulXignalAt, xeed.firstUsefulXignalAt ? 'KNOWN' : 'UNKNOWN')
        addFact(facts, 'Time to first value (ms)', xeed.timeToFirstUsefulXignalMs, xeed.timeToFirstUsefulXignalMs == null ? 'UNKNOWN' : 'KNOWN')
        addFact(facts, 'Observations reused', xeed.observationsReused, 'KNOWN')
        addFact(facts, 'Observations added', xeed.observationsAdded, 'KNOWN')
        addFact(facts, 'Reuse ratio', xeed.reuseRatio, xeed.reuseRatio == null ? 'UNKNOWN' : 'KNOWN')
        addFact(facts, 'Signals emitted', xeed.xignalsEmitted, 'KNOWN')
        addFact(facts, 'Canonical admissions', xeed.canonicalAdmissions, 'KNOWN')
        addFact(facts, 'Direct event cost coverage', xeed.directCostCompleteness, xeed.directCostCompleteness)
        addFact(facts, 'Shared cost attribution', xeed.sharedCostCompleteness, xeed.sharedCostCompleteness)
        addFact(facts, 'Triggered cost attribution', xeed.triggeredCostCompleteness, xeed.triggeredCostCompleteness)
        addFact(facts, 'Revenue attribution', xeed.revenueAttributionCompleteness, xeed.revenueAttributionCompleteness)

        const details = document.createElement('details')
        details.className = 'admin-metric-lineage'
        const detailsSummary = document.createElement('summary')
        detailsSummary.textContent = 'Diagnose this Observation Focus'
        const body = document.createElement('p')
        const costs = (xeed.knownCostsByCurrency || []).map(([currency, amount]) => `${amount} µ${currency}`).join(', ')
        body.textContent = `Observed direct costs: ${costs || 'UNKNOWN'} · unknown-cost events: ${xeed.unknownCostEventCount} · failed events: ${xeed.failedEventCount} · partial events: ${xeed.partialEventCount} · shared: ${xeed.sharedCostReason} · triggered: ${xeed.triggeredCostReason} · learning lineage: ${(xeed.sourceLearningEventIds || []).join(', ') || 'None'}`
        details.append(detailsSummary, body)

        card.append(header, facts, details)
        xeedList.append(card)
      }
    }
  }


  const brainObservatory = bootstrap.brainObservatory
  const brainSection = document.getElementById('admin-brain-observatory')
  const brainCompleteness = document.getElementById('admin-brain-completeness')
  const brainAsOf = document.getElementById('admin-brain-asof')
  const brainNotes = document.getElementById('admin-brain-notes')
  const brainSummary = document.getElementById('admin-brain-summary')
  const providerList = document.getElementById('admin-provider-list')

  if (current?.slug === 'axent-brain' && brainObservatory && brainSection) {
    brainSection.hidden = false
    if (domainPreview) domainPreview.hidden = true
    if (brainCompleteness) brainCompleteness.textContent = brainObservatory.completeness || 'UNKNOWN'
    if (brainAsOf) brainAsOf.textContent = brainObservatory.asOf ? `As of ${brainObservatory.asOf}` : ''

    if (brainNotes) {
      brainNotes.replaceChildren()
      for (const noteText of brainObservatory.coverageNotes || []) {
        const note = document.createElement('p')
        note.textContent = noteText
        brainNotes.append(note)
      }
    }

    if (brainSummary) {
      brainSummary.replaceChildren()

      const executionPanel = document.createElement('section')
      executionPanel.className = 'admin-observatory-panel'
      const executionHeading = document.createElement('h3')
      executionHeading.textContent = 'Brain execution evidence'
      executionPanel.append(executionHeading)
      const executionFacts = document.createElement('div')
      executionFacts.className = 'admin-observatory-facts'
      addFact(executionFacts, 'Learning events', brainObservatory.learningEventCount, 'KNOWN')
      addFact(executionFacts, 'Cognitive events', brainObservatory.cognitiveEventCount, 'KNOWN')
      addFact(executionFacts, 'Deterministic', brainObservatory.deterministicEventCount, 'KNOWN')
      addFact(executionFacts, 'Structured evaluator', brainObservatory.structuredEvaluatorEventCount, 'KNOWN')
      addFact(executionFacts, 'Adaptive research', brainObservatory.adaptiveResearchEventCount, 'KNOWN')
      addFact(executionFacts, 'Failed', brainObservatory.failedEventCount, 'KNOWN')
      addFact(executionFacts, 'Partial', brainObservatory.partialEventCount, 'KNOWN')
      addFact(executionFacts, 'Semantic judgments produced', brainObservatory.semanticJudgmentsProduced, 'KNOWN')
      addFact(executionFacts, 'Research objectives resolved', brainObservatory.researchObjectivesResolved, 'KNOWN')
      addFact(executionFacts, 'Useful-output events', brainObservatory.usefulOutputEventCount, 'KNOWN')
      addFact(executionFacts, 'Cost coverage', brainObservatory.costCompleteness, brainObservatory.costCompleteness)
      addFact(executionFacts, 'Latency coverage', brainObservatory.latencyCompleteness, brainObservatory.latencyCompleteness)
      addFact(executionFacts, 'Average observed latency (ms)', brainObservatory.averageLatencyMs, brainObservatory.latencyCompleteness)
      addFact(executionFacts, 'Provider-attributed events', brainObservatory.providerAttributedEventCount, 'KNOWN')
      addFact(executionFacts, 'Cognitive events without provider identity', brainObservatory.providerUnattributedCognitiveEventCount, 'KNOWN')
      executionPanel.append(executionFacts)
      brainSummary.append(executionPanel)

      const control = brainObservatory.control || {}
      const controlPanel = document.createElement('section')
      controlPanel.className = 'admin-observatory-panel'
      const controlHeading = document.createElement('h3')
      controlHeading.textContent = 'Research control & Knowledge Frontier'
      controlPanel.append(controlHeading)
      const controlFacts = document.createElement('div')
      controlFacts.className = 'admin-observatory-facts'
      addFact(controlFacts, 'Research objective', control.researchObjectiveState, control.researchObjectiveCompleteness)
      addFact(controlFacts, 'Routing', control.routingState, control.routingCompleteness)
      addFact(controlFacts, 'Stop reason', control.stopState, control.stopCompleteness)
      addFact(controlFacts, 'Budget', control.budgetState, control.budgetCompleteness)
      addFact(controlFacts, 'No progress', control.noProgressState, control.noProgressCompleteness)
      addFact(controlFacts, 'Retry', control.retryState, control.retryCompleteness)
      addFact(controlFacts, 'Abstention', control.abstentionState, control.abstentionCompleteness)
      addFact(controlFacts, 'Knowledge Frontier', control.knowledgeFrontierState, control.knowledgeFrontierCompleteness)
      addFact(controlFacts, 'Unresolved gap', control.unresolvedGapState, control.unresolvedGapCompleteness)
      controlPanel.append(controlFacts)

      const controlLineage = document.createElement('details')
      controlLineage.className = 'admin-metric-lineage'
      const controlLineageSummary = document.createElement('summary')
      controlLineageSummary.textContent = 'Inspect research-control lineage'
      const controlLineageBody = document.createElement('p')
      controlLineageBody.textContent = `Admin records: ${(control.sourceAdminRecordIds || []).join(', ') || 'None observed'} · Learning events: ${(control.sourceLearningEventIds || []).join(', ') || 'None observed'}`
      controlLineage.append(controlLineageSummary, controlLineageBody)
      controlPanel.append(controlLineage)
      brainSummary.append(controlPanel)
    }

    if (providerList) {
      providerList.replaceChildren()
      const providers = Array.isArray(brainObservatory.providerSlices) ? brainObservatory.providerSlices : []
      if (!providers.length) {
        const empty = document.createElement('article')
        empty.className = 'admin-observatory-empty'
        const strong = document.createElement('strong')
        strong.textContent = 'No provider-attributed cognitive usage observed'
        const body = document.createElement('p')
        body.textContent = 'This is not a claim of zero cognitive work. Provider identity or usage may be unavailable and remains explicit above.'
        empty.append(strong, body)
        providerList.append(empty)
      }
      for (const provider of providers) {
        const card = document.createElement('article')
        card.className = 'admin-xeed-card admin-provider-card'
        const header = document.createElement('header')
        const heading = document.createElement('h3')
        heading.textContent = `${provider.provider} · ${provider.providerVersion}`
        const state = document.createElement('span')
        state.textContent = provider.operationClass
        header.append(heading, state)

        const facts = document.createElement('div')
        facts.className = 'admin-observatory-facts'
        addFact(facts, 'Events', provider.eventCount, 'KNOWN')
        addFact(facts, 'Completed', provider.completedCount, 'KNOWN')
        addFact(facts, 'Partial', provider.partialCount, 'KNOWN')
        addFact(facts, 'Failed', provider.failedCount, 'KNOWN')
        addFact(facts, 'Cost coverage', provider.costCompleteness, provider.costCompleteness)
        addFact(facts, 'Latency coverage', provider.latencyCompleteness, provider.latencyCompleteness)
        addFact(facts, 'Average latency (ms)', provider.averageLatencyMs, provider.latencyCompleteness)
        addFact(facts, 'Input units observed', provider.totalInputUnits, provider.knownInputUnitEventCount ? 'PARTIAL' : 'UNKNOWN')
        addFact(facts, 'Output units observed', provider.totalOutputUnits, provider.knownOutputUnitEventCount ? 'PARTIAL' : 'UNKNOWN')
        addFact(facts, 'Semantic judgments', provider.semanticJudgmentsProduced, 'KNOWN')
        addFact(facts, 'Research objectives resolved', provider.researchObjectivesResolved, 'KNOWN')
        addFact(facts, 'Useful-output events', provider.usefulOutputEventCount, 'KNOWN')

        const details = document.createElement('details')
        details.className = 'admin-metric-lineage'
        const detailsSummary = document.createElement('summary')
        detailsSummary.textContent = 'Inspect provider slice'
        const detailsBody = document.createElement('p')
        const costs = (provider.knownCostsByCurrency || []).map(([currency, amount]) => `${amount} µ${currency}`).join(', ')
        detailsBody.textContent = `Comparable only with matching key: ${provider.comparisonKey} · policy: ${provider.policyId}@${provider.policyVersion} · observed cost: ${costs || 'UNKNOWN'} · unknown-cost events: ${provider.unknownCostEventCount} · lineage: ${(provider.sourceLearningEventIds || []).join(', ') || 'None'}`
        details.append(detailsSummary, detailsBody)
        card.append(header, facts, details)
        providerList.append(card)
      }
    }
  }


  const governance = bootstrap.governance
  const governanceSection = document.getElementById('admin-governance-observatory')
  const governanceCompleteness = document.getElementById('admin-governance-completeness')
  const governanceAsOf = document.getElementById('admin-governance-asof')
  const governanceNotes = document.getElementById('admin-governance-notes')
  const governanceSummary = document.getElementById('admin-governance-summary')
  const policyList = document.getElementById('admin-policy-list')
  const policyChangeList = document.getElementById('admin-policy-change-list')
  const alertList = document.getElementById('admin-alert-list')
  const auditList = document.getElementById('admin-audit-list')

  if (current?.slug === 'governance' && governance && governanceSection) {
    governanceSection.hidden = false
    if (domainPreview) domainPreview.hidden = true
    if (governanceCompleteness) governanceCompleteness.textContent = governance.completeness || 'UNKNOWN'
    if (governanceAsOf) governanceAsOf.textContent = governance.asOf ? `As of ${governance.asOf}` : ''

    if (governanceNotes) {
      governanceNotes.replaceChildren()
      for (const noteText of governance.coverageNotes || []) {
        const note = document.createElement('p')
        note.textContent = noteText
        governanceNotes.append(note)
      }
    }

    if (governanceSummary) {
      governanceSummary.replaceChildren()
      const panel = document.createElement('section')
      panel.className = 'admin-observatory-panel'
      const heading = document.createElement('h3')
      heading.textContent = 'Governance invariants'
      const facts = document.createElement('div')
      facts.className = 'admin-observatory-facts'
      addFact(facts, 'Unsupported canonical write targets', governance.unsupportedCanonicalWriteTargetCount, 'KNOWN')
      addFact(facts, 'Registered policy families', (governance.policies || []).length, 'KNOWN')
      addFact(facts, 'Alert classes', (governance.alerts || []).length, 'KNOWN')
      addFact(facts, 'Privileged audit records', (governance.auditRecords || []).length, 'KNOWN')
      panel.append(heading, facts)
      governanceSummary.append(panel)
    }

    if (policyList) {
      policyList.replaceChildren()
      const title = document.createElement('h3')
      title.textContent = 'Versioned policy registry'
      policyList.append(title)
      for (const policy of governance.policies || []) {
        const card = document.createElement('article')
        card.className = 'admin-xeed-card'
        const header = document.createElement('header')
        const heading = document.createElement('h3')
        heading.textContent = policy.family
        const state = document.createElement('span')
        state.textContent = policy.completeness || 'UNKNOWN'
        header.append(heading, state)
        const facts = document.createElement('div')
        facts.className = 'admin-observatory-facts'
        addFact(facts, 'Policy ID', policy.policyId, policy.completeness)
        addFact(facts, 'Version', policy.policyVersion, policy.completeness)
        addFact(facts, 'Effective at', policy.effectiveAt, policy.completeness)
        addFact(facts, 'Governed changes', policy.changeCount, 'KNOWN')
        const details = document.createElement('details')
        details.className = 'admin-metric-lineage'
        const summary = document.createElement('summary')
        summary.textContent = 'Inspect policy lineage'
        const body = document.createElement('p')
        body.textContent = `Code SHA: ${policy.codeSha || 'UNKNOWN'} · source refs: ${(policy.sourceRefs || []).join(', ') || 'None observed'}`
        details.append(summary, body)
        card.append(header, facts, details)
        policyList.append(card)
      }
    }


    if (policyChangeList) {
      policyChangeList.replaceChildren()
      const title = document.createElement('h3')
      title.textContent = 'Governed policy changes'
      policyChangeList.append(title)
      const changes = Array.isArray(governance.policyChanges) ? governance.policyChanges : []
      if (!changes.length) {
        const empty = document.createElement('article')
        empty.className = 'admin-observatory-empty'
        const strong = document.createElement('strong')
        strong.textContent = 'No policy promotion or rollback observed'
        const body = document.createElement('p')
        body.textContent = 'Active policy may still exist as a pre-governance baseline; absence of history is not absence of policy.'
        empty.append(strong, body)
        policyChangeList.append(empty)
      }
      for (const change of changes) {
        const card = document.createElement('article')
        card.className = 'admin-xeed-card'
        const header = document.createElement('header')
        const heading = document.createElement('h3')
        heading.textContent = `${change.family} · ${change.kind}`
        const state = document.createElement('span')
        state.textContent = change.effectiveAt
        header.append(heading, state)
        const facts = document.createElement('div')
        facts.className = 'admin-observatory-facts'
        addFact(facts, 'Actor', change.actor, 'KNOWN')
        addFact(facts, 'Before', `${change.beforePolicyId}@${change.beforeVersion}`, 'KNOWN')
        addFact(facts, 'After', `${change.afterPolicyId}@${change.afterVersion}`, 'KNOWN')
        addFact(facts, 'Effective version', change.afterVersion, 'KNOWN')
        const details = document.createElement('details')
        details.className = 'admin-metric-lineage'
        const summary = document.createElement('summary')
        summary.textContent = 'Inspect governance decision'
        const body = document.createElement('p')
        body.textContent = `Decision: ${change.decisionId} · reason: ${change.reason} · effective at: ${change.effectiveAt}`
        details.append(summary, body)
        card.append(header, facts, details)
        policyChangeList.append(card)
      }
    }

    if (alertList) {
      alertList.replaceChildren()
      const title = document.createElement('h3')
      title.textContent = 'Governed alerts'
      alertList.append(title)
      for (const alert of governance.alerts || []) {
        const card = document.createElement('article')
        card.className = 'admin-xeed-card'
        const header = document.createElement('header')
        const heading = document.createElement('h3')
        heading.textContent = alert.alertClass
        const state = document.createElement('span')
        state.textContent = alert.completeness || 'UNKNOWN'
        header.append(heading, state)
        const facts = document.createElement('div')
        facts.className = 'admin-observatory-facts'
        addFact(facts, 'Count', alert.count, alert.completeness)
        addFact(facts, 'Evidence', alert.reason, alert.completeness)
        const details = document.createElement('details')
        details.className = 'admin-metric-lineage'
        const summary = document.createElement('summary')
        summary.textContent = 'Inspect alert lineage'
        const body = document.createElement('p')
        body.textContent = `Source refs: ${(alert.sourceRefs || []).join(', ') || 'None observed'}`
        details.append(summary, body)
        card.append(header, facts, details)
        alertList.append(card)
      }
    }

    if (auditList) {
      auditList.replaceChildren()
      const title = document.createElement('h3')
      title.textContent = 'Privileged action audit'
      auditList.append(title)
      const records = Array.isArray(governance.auditRecords) ? governance.auditRecords : []
      if (!records.length) {
        const empty = document.createElement('article')
        empty.className = 'admin-observatory-empty'
        const strong = document.createElement('strong')
        strong.textContent = 'No privileged governance commands observed'
        const body = document.createElement('p')
        body.textContent = 'Zero audit records means no recorded AO-07 command activity, not that governance controls are absent.'
        empty.append(strong, body)
        auditList.append(empty)
      }
      for (const audit of records) {
        const card = document.createElement('article')
        card.className = 'admin-xeed-card'
        const header = document.createElement('header')
        const heading = document.createElement('h3')
        heading.textContent = `${audit.action} · ${audit.target}`
        const state = document.createElement('span')
        state.textContent = audit.outcome
        header.append(heading, state)
        const facts = document.createElement('div')
        facts.className = 'admin-observatory-facts'
        addFact(facts, 'Actor', audit.actorPrincipalId, 'KNOWN')
        addFact(facts, 'Result', audit.resultCode, 'KNOWN')
        addFact(facts, 'Before', audit.beforeRef, audit.beforeRef ? 'KNOWN' : 'NOT_APPLICABLE')
        addFact(facts, 'After', audit.afterRef, audit.afterRef ? 'KNOWN' : 'NOT_APPLICABLE')
        const details = document.createElement('details')
        details.className = 'admin-metric-lineage'
        const summary = document.createElement('summary')
        summary.textContent = 'Inspect authorization and reason'
        const body = document.createElement('p')
        body.textContent = `Command: ${audit.commandId} · required scope: ${audit.requiredScope} · reason: ${audit.reason} · approval: ${audit.approvalRef || 'not supplied'}`
        details.append(summary, body)
        card.append(header, facts, details)
        auditList.append(card)
      }
    }
  }



  const customerOperations = bootstrap.customerOperations
  const customerOperationsNotes = document.getElementById('admin-customer-operations-notes')
  const customerOperationsSummary = document.getElementById('admin-customer-operations-summary')
  const customerAccountList = document.getElementById('admin-customer-account-list')

  if (current?.slug === 'customers-crm' && customerOperations) {
    if (customerOperationsNotes) {
      customerOperationsNotes.replaceChildren()
      for (const noteText of customerOperations.coverageNotes || []) {
        const note = document.createElement('p')
        note.textContent = noteText
        customerOperationsNotes.append(note)
      }
    }

    if (customerOperationsSummary) {
      customerOperationsSummary.replaceChildren()
      const panel = document.createElement('section')
      panel.className = 'admin-observatory-panel'
      const heading = document.createElement('h3')
      heading.textContent = 'AXIGNAL account / subscription authority'
      panel.append(heading)
      const facts = document.createElement('div')
      facts.className = 'admin-observatory-facts'
      addFact(facts, 'Accounts', customerOperations.accountCount, 'KNOWN')
      addFact(facts, 'Active', customerOperations.activeAccountCount, 'KNOWN')
      addFact(facts, 'Suspended', customerOperations.suspendedAccountCount, 'KNOWN')
      addFact(facts, 'Cancelled', customerOperations.cancelledAccountCount, 'KNOWN')
      addFact(facts, 'Entitled organizations', customerOperations.totalEntitledXeeds, 'KNOWN')
      addFact(facts, 'MRR', customerOperations.mrrEur, customerOperations.mrrEur ? 'KNOWN' : 'UNKNOWN')
      addFact(facts, 'Payment authority', customerOperations.paymentAuthority, 'BOUNDARY')
      panel.append(facts)

      const funnel = document.createElement('details')
      funnel.className = 'admin-metric-lineage'
      const funnelSummary = document.createElement('summary')
      funnelSummary.textContent = 'Inspect product funnel'
      const funnelBody = document.createElement('p')
      funnelBody.textContent = (customerOperations.funnelCounts || [])
        .map(([stage, count]) => `${stage}: ${count}`)
        .join(' · ')
      funnel.append(funnelSummary, funnelBody)
      panel.append(funnel)
      customerOperationsSummary.append(panel)
    }

    if (customerAccountList) {
      customerAccountList.replaceChildren()
      const customers = Array.isArray(customerOperations.customers) ? customerOperations.customers : []
      if (!customers.length) {
        const empty = document.createElement('article')
        empty.className = 'admin-observatory-empty'
        const strong = document.createElement('strong')
        strong.textContent = 'No AXIGNAL service accounts recorded'
        const body = document.createElement('p')
        body.textContent = 'Account state is first-party service authority. AXIGLAND observations never create accounts or entitlements.'
        empty.append(strong, body)
        customerAccountList.append(empty)
      }
      for (const account of customers) {
        const card = document.createElement('article')
        card.className = 'admin-xeed-card'
        const header = document.createElement('header')
        const heading = document.createElement('h3')
        heading.textContent = account.displayName
        const state = document.createElement('span')
        state.textContent = `${account.accountStatus} · ${account.subscriptionStatus}`
        header.append(heading, state)

        const facts = document.createElement('div')
        facts.className = 'admin-observatory-facts'
        addFact(facts, 'Account', account.accountId, 'PRIVATE_SERVICE')
        addFact(facts, 'Tenant', account.tenantId, 'PRIVATE_SERVICE')
        addFact(facts, 'Plan', `${account.planCode} · ${account.planVersion}`, 'KNOWN')
        addFact(facts, 'Organization capacity', account.xeedCapacity, 'KNOWN')
        addFact(facts, 'Active organizations', account.activeXeedCount, 'KNOWN')
        addFact(facts, 'Users', account.userCount, 'KNOWN')
        addFact(facts, 'Payment', account.paymentState, account.paymentState === 'EXTERNAL_PENDING' ? 'UNKNOWN' : 'KNOWN')
        addFact(facts, 'MRR', account.mrrEur, account.mrrEur ? 'KNOWN' : 'UNKNOWN')
        addFact(facts, 'Pricing hypothesis', `€${account.pricingHypothesisMonthlyEur}/mo`, 'HYPOTHESIS')
        addFact(facts, 'Lifecycle events', account.eventCount, 'KNOWN')

        const details = document.createElement('details')
        details.className = 'admin-metric-lineage'
        const summary = document.createElement('summary')
        summary.textContent = 'Inspect service authority'
        const body = document.createElement('p')
        body.textContent = `Entitled organizations: ${(account.entitledXeedIds || []).join(', ') || 'none'} · Funnel: ${(account.funnelStages || []).join(' → ') || 'SIGNUP only'} · CUSTOMER_ACCOUNT_STATE != ORGANIZATION_STATE.`
        details.append(summary, body)
        card.append(header, facts, details)
        customerAccountList.append(card)
      }
    }
  }

  const commercial = bootstrap.commercial
  const commercialSection = document.getElementById('admin-commercial-observatory')
  const commercialPrivacy = document.getElementById('admin-commercial-privacy')
  const commercialGenerated = document.getElementById('admin-commercial-generated')
  const commercialNotes = document.getElementById('admin-commercial-notes')
  const commercialSummary = document.getElementById('admin-commercial-summary')
  const commercialCompanyList = document.getElementById('admin-commercial-company-list')

  if (current?.slug === 'customers-crm' && commercial && commercialSection) {
    commercialSection.hidden = false
    if (domainPreview) domainPreview.hidden = true
    if (commercialPrivacy) commercialPrivacy.textContent = commercial.privacyClass || 'PRIVATE_FIRST_PARTY'
    if (commercialGenerated) commercialGenerated.textContent = commercial.generatedAt ? `Generated ${commercial.generatedAt}` : ''

    if (commercialNotes) {
      commercialNotes.replaceChildren()
      for (const noteText of commercial.coverageNotes || []) {
        const note = document.createElement('p')
        note.textContent = noteText
        commercialNotes.append(note)
      }
    }

    if (commercialSummary) {
      commercialSummary.replaceChildren()
      const panel = document.createElement('section')
      panel.className = 'admin-observatory-panel'
      const heading = document.createElement('h3')
      heading.textContent = 'AXIGNAL first-party commercial state'
      panel.append(heading)
      const facts = document.createElement('div')
      facts.className = 'admin-observatory-facts'
      addFact(facts, 'Prospects', commercial.prospectCount, 'KNOWN')
      addFact(facts, 'Companies', commercial.companyCount, 'KNOWN')
      addFact(facts, 'Contacts', commercial.contactCount, 'KNOWN')
      addFact(facts, 'Opportunities', commercial.opportunityCount, 'KNOWN')
      addFact(facts, 'Deals', commercial.dealCount, 'KNOWN')
      addFact(facts, 'Open follow-ups', commercial.openTaskCount, 'KNOWN')
      addFact(facts, 'Commercial notes', commercial.noteCount, 'KNOWN')
      addFact(facts, 'Audit records', commercial.auditCount, 'KNOWN')
      addFact(facts, 'PII in projection', commercial.piiVisible ? 'VISIBLE' : 'EXCLUDED', 'KNOWN')
      panel.append(facts)

      const originDetails = document.createElement('details')
      originDetails.className = 'admin-metric-lineage'
      const originSummary = document.createElement('summary')
      originSummary.textContent = 'Inspect provenance classes'
      const originBody = document.createElement('p')
      originBody.textContent = (commercial.originCounts || [])
        .map(([origin, count]) => `${origin}: ${count}`)
        .join(' · ') || 'Origin breakdown unavailable for this scope.'
      originDetails.append(originSummary, originBody)
      panel.append(originDetails)
      commercialSummary.append(panel)
    }

    if (commercialCompanyList) {
      commercialCompanyList.replaceChildren()
      const companies = Array.isArray(commercial.companies) ? commercial.companies : []
      if (!companies.length) {
        const empty = document.createElement('article')
        empty.className = 'admin-observatory-empty'
        const strong = document.createElement('strong')
        strong.textContent = 'No AXIGNAL commercial companies recorded'
        const body = document.createElement('p')
        body.textContent = 'This is private first-party business state. AXIGLAND observations do not silently create commercial relationships.'
        empty.append(strong, body)
        commercialCompanyList.append(empty)
      }
      for (const company of companies) {
        const card = document.createElement('article')
        card.className = 'admin-xeed-card'
        const header = document.createElement('header')
        const heading = document.createElement('h3')
        heading.textContent = company.displayName
        const state = document.createElement('span')
        state.textContent = company.origin
        header.append(heading, state)

        const facts = document.createElement('div')
        facts.className = 'admin-observatory-facts'
        addFact(facts, 'Acquisition source', company.acquisitionSource, 'KNOWN')
        addFact(facts, 'Consent basis', company.consentBasis, 'KNOWN')
        addFact(facts, 'Contacts', company.contactCount, 'KNOWN')
        addFact(facts, 'Opportunities', company.opportunityCount, 'KNOWN')
        addFact(facts, 'Open follow-ups', company.openTaskCount, 'KNOWN')
        addFact(facts, 'Notes', company.noteCount, 'KNOWN')
        addFact(facts, 'AXIGNAL account ref', company.accountId, company.accountId ? 'KNOWN' : 'UNKNOWN')
        addFact(facts, 'Observed Organization ref', company.observedOrganizationId, company.observedOrganizationId ? 'EXPLICIT_REFERENCE' : 'UNKNOWN')

        const details = document.createElement('details')
        details.className = 'admin-metric-lineage'
        const summary = document.createElement('summary')
        summary.textContent = 'Inspect authority boundary'
        const body = document.createElement('p')
        body.textContent = `Commercial company ${company.companyId} is AXIGNAL private operating state. Organization reference is navigation/deduplication only and grants no canonical write authority.`
        details.append(summary, body)

        card.append(header, facts, details)
        commercialCompanyList.append(card)
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

  const integrations = bootstrap.integrations
  const integrationSection = document.getElementById('admin-integration-observatory')
  const integrationPrivacy = document.getElementById('admin-integration-privacy')
  const integrationAsOf = document.getElementById('admin-integration-asof')
  const integrationNotes = document.getElementById('admin-integration-notes')
  const integrationList = document.getElementById('admin-integration-list')

  if (current?.slug === 'integrations' && integrations && integrationSection) {
    integrationSection.hidden = false
    if (domainPreview) domainPreview.hidden = true
    if (integrationPrivacy) integrationPrivacy.textContent = integrations.privacyClass || 'PRIVATE OPERATIONS'
    if (integrationAsOf) integrationAsOf.textContent = integrations.asOf ? `As of ${integrations.asOf}` : ''
    if (integrationNotes) {
      integrationNotes.replaceChildren()
      for (const noteText of integrations.coverageNotes || []) {
        const note = document.createElement('p')
        note.textContent = noteText
        integrationNotes.append(note)
      }
    }
    if (integrationList) {
      integrationList.replaceChildren()
      const entries = Array.isArray(integrations.integrations) ? integrations.integrations : []
      if (!entries.length) {
        const empty = document.createElement('article')
        empty.className = 'admin-observatory-empty'
        const heading = document.createElement('strong')
        heading.textContent = 'No integration definitions are registered'
        const body = document.createElement('p')
        body.textContent = 'This registry has no governed integration entries yet. It does not verify or infer configuration outside this registry.'
        empty.append(heading, body)
        integrationList.append(empty)
      }
      for (const item of entries) {
        const article = document.createElement('article')
        article.className = 'admin-integration-entry'
        const header = document.createElement('header')
        const title = document.createElement('h3')
        title.textContent = item.provider || item.integrationId
        const state = document.createElement('span')
        state.textContent = item.enabled ? 'ENABLED' : 'DISABLED'
        header.append(title, state)

        const purpose = document.createElement('p')
        purpose.className = 'admin-integration-purpose'
        purpose.textContent = item.purpose || 'Purpose unavailable'

        const facts = document.createElement('dl')
        facts.className = 'admin-integration-facts'
        const addDetail = (label, value) => {
          const wrapper = document.createElement('div')
          const term = document.createElement('dt')
          term.textContent = label
          const description = document.createElement('dd')
          description.textContent = value == null || value === '' ? 'UNKNOWN' : String(value)
          wrapper.append(term, description)
          facts.append(wrapper)
        }
        addDetail('Environment', item.environment)
        addDetail('Owner', item.owner)
        addDetail('Credential', item.credentialConfigured ? item.credentialState : 'MISSING')
        addDetail('Connection health', item.health)
        addDetail('Data direction', item.direction)
        addDetail('Granted scopes', (item.scopes || []).join(', ') || 'None declared')
        addDetail('Webhook capability', item.webhookCapable ? 'Available' : 'Not declared')
        addDetail('Webhook endpoint', item.webhookConfigured ? 'Configured' : 'Missing')
        addDetail('Health freshness window', `${item.healthFreshnessSeconds} seconds`)
        addDetail('Last verified', item.lastVerifiedAt)
        addDetail('Last success', item.lastSuccessAt)
        addDetail('Last failure', item.lastFailureAt)
        addDetail('Failure category', item.failureCategory)
        addDetail('Rate limit posture', item.rateLimitPosture)

        const boundary = document.createElement('details')
        boundary.className = 'admin-metric-lineage'
        const summary = document.createElement('summary')
        summary.textContent = 'Inspect authority boundary'
        const body = document.createElement('p')
        body.textContent = item.authorityBoundary || 'Authority boundary is UNKNOWN.'
        boundary.append(summary, body)

        article.append(header, purpose, facts, boundary)
        integrationList.append(article)
      }
    }

    const apiOperations = bootstrap.apiOperations
    const apiPrivacy = document.getElementById('admin-api-operations-privacy')
    const apiGenerated = document.getElementById('admin-api-operations-generated')
    const apiNotes = document.getElementById('admin-api-operations-notes')
    const apiSummary = document.getElementById('admin-api-operations-summary')
    const apiList = document.getElementById('admin-api-operations-list')
    if (apiOperations) {
      if (apiPrivacy) apiPrivacy.textContent = apiOperations.privacyClass || 'PRIVATE OPERATIONS'
      if (apiGenerated) apiGenerated.textContent = apiOperations.generatedAt ? 'As of ' + apiOperations.generatedAt : ''
      if (apiNotes) {
        apiNotes.replaceChildren()
        for (const noteText of apiOperations.coverageNotes || []) {
          const note = document.createElement('p')
          note.textContent = noteText
          apiNotes.append(note)
        }
      }
      if (apiSummary) {
        apiSummary.replaceChildren()
        const webhooks = apiOperations.webhooks || {}
        const facts = [
          ['Webhook inbox', webhooks.received],
          ['Succeeded', webhooks.succeeded],
          ['Retry pending', webhooks.retryPending],
          ['Dead letter', webhooks.deadLetter],
          ['Rejected', webhooks.rejected],
        ]
        for (const pair of facts) {
          const card = document.createElement('article')
          card.className = 'admin-observatory-stat'
          const strong = document.createElement('strong')
          strong.textContent = pair[1] == null ? 'UNKNOWN' : String(pair[1])
          const span = document.createElement('span')
          span.textContent = pair[0]
          card.append(strong, span)
          apiSummary.append(card)
        }
      }
      if (apiList) {
        apiList.replaceChildren()
        for (const item of apiOperations.endpoints || []) {
          const article = document.createElement('article')
          article.className = 'admin-integration-entry'
          const header = document.createElement('header')
          const title = document.createElement('h3')
          title.textContent = item.method + ' ' + item.pathTemplate
          const state = document.createElement('span')
          state.textContent = item.exposure || 'UNKNOWN'
          header.append(title, state)

          const facts = document.createElement('dl')
          facts.className = 'admin-integration-facts'
          const addDetail = (label, value) => {
            const wrapper = document.createElement('div')
            const term = document.createElement('dt')
            term.textContent = label
            const description = document.createElement('dd')
            description.textContent = value == null || value === '' ? 'UNKNOWN' : String(value)
            wrapper.append(term, description)
            facts.append(wrapper)
          }
          addDetail('Schema', item.schemaVersion)
          addDetail('Requests', item.requestCount)
          addDetail('Errors', item.errorCount)
          addDetail('Error rate', item.errorRate == null ? null : (item.errorRate * 100).toFixed(1) + '%')
          addDetail('Average latency', item.averageLatencyMs == null ? null : item.averageLatencyMs + ' ms')
          addDetail('Last status', item.lastStatusCode)
          addDetail('Last observed', item.lastObservedAt)
          addDetail('Quota remaining', item.quotaRemaining)
          addDetail('Rate limited', item.rateLimited)

          const boundary = document.createElement('details')
          boundary.className = 'admin-metric-lineage'
          const summary = document.createElement('summary')
          summary.textContent = 'Inspect API authority boundary'
          const body = document.createElement('p')
          body.textContent = item.authorityBoundary || 'Authority boundary is UNKNOWN.'
          boundary.append(summary, body)
          article.append(header, facts, boundary)
          apiList.append(article)
        }
      }
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
