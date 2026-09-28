/*
 * Subscriber presentation semantics.
 * Canonical identifiers map to semantic keys; locale copy is a separate layer.
 * Add a populated BCP-47 locale here without changing canonical values.
 */
;(function attachPresentation(root) {
  const COPY = Object.freeze({
    en: Object.freeze({
      'organization.label': 'Organization',
      'organization.identity': 'Organization in the shared world',
      'organization.meaning': 'This view brings together the organization and information available in this context.',
      'organization.empty': 'Nothing is linked to this view yet.',
      'page.title': 'AXIGNAL · AXIGLAND',
      'page.description': 'AXIGNAL view of shared economic knowledge and current context.',
      'navigation.logoToday': 'AXIGNAL · Today',
      'navigation.axentGuide': 'AXENT context guide',
      'context.label': 'Context',
      'context.current': 'Current context',
      'context.private': 'Private view',
      'context.create': '+ New context',
      'field.information': 'Information',
      'field.detail': 'Detail',
      'field.knowledge': 'What AXIGNAL knows',
      'field.capabilities': 'Capabilities',
      'field.markets': 'Markets',
      'field.lastObserved': 'Last observed',
      'field.currentness': 'Freshness',
      'fact.unspecified': 'Information',
      'predicate.manufactures': 'Makes',
      'predicate.servesMarket': 'Serves a market',
      'predicate.maintainsStandard': 'Maintains a standard',
      'epistemic.observed': 'Observed',
      'epistemic.declared': 'Declared',
      'epistemic.inferred': 'Inferred',
      'epistemic.corroborated': 'Corroborated',
      'epistemic.contradicted': 'Conflicting information',
      'epistemic.stale': 'May be out of date',
      'epistemic.unknown': 'Not established',
      'currentness.current': 'Marked as current',
      'currentness.stale': 'This information may be out of date.',
      'currentness.unknown': "How current this information is hasn't been verified.",
      'date.lastObserved': 'Last observed',
      'action.open': 'OPEN →',
      'error.load': "This view couldn't be loaded.",
      'demo.sample': 'DEMO · EXAMPLE DATA',
      'navigation.account': 'Account',
      'navigation.workspaceNavigation': 'Workspace navigation',
      'navigation.axiglandField': 'AXIGLAND cognitive field',
      'navigation.knowledgeDepth': 'Knowledge and depth',
      'navigation.trail': 'Focus trail',
      'navigation.back': 'Back',
      'navigation.forward': 'Forward',
      'navigation.home': 'Home',
      'navigation.questionsExplore': 'Questions to explore',
      'navigation.context': 'Context',
      'navigation.organization': 'Organization',
      'navigation.connections': 'Connections',
      'navigation.questions': 'Questions',
      'navigation.guide': 'View guide',
      'navigation.askAXENT': 'Ask AXENT',
      'navigation.axentConversation': 'AXENT conversation',
      'navigation.askPlaceholder': 'Not active in this view',
      'navigation.cognitiveDepth': 'Cognitive depth',
      'navigation.focus': 'Focus',
      'navigation.field': 'AXIGLAND field',
      'navigation.trail': 'Focus trail',
      'navigation.timeline': 'Timeline',
      'navigation.workspace': 'Workspace',
      'navigation.memory': 'Memory',
      'navigation.scope': 'Scope',
      'navigation.uncertainty': 'Uncertainty',
      'navigation.research': 'Research',
      'navigation.epistemic': 'Knowledge',
      'navigation.createContext': '+ New context',
      'navigation.contextScope': 'Private · current context',
      'navigation.today': 'Today',
      'navigation.governance': 'Governance',
      'navigation.glance': 'Glance',
      'navigation.meaning': 'Meaning',
      'navigation.inference': 'Inference',
      'navigation.evidence': 'Evidence',
      'navigation.depth': 'Depth',
      'navigation.capabilities': 'capabilities',
      'navigation.markets': 'markets',
      'navigation.signals': 'signals',
      'navigation.activity': 'activity',
      'navigation.youAreHere': 'you are here',
      'navigation.centerFocus': 'Center on current focus',
      'navigation.zoomIn': 'Zoom in',
      'navigation.zoomOut': 'Zoom out',
      'navigation.fitField': 'Fit the field',
      'navigation.centerOrganization': 'Center on Organization',
      'navigation.resetField': 'Reset field view',
      'navigation.fieldControls': 'Field controls',
      'navigation.fieldMinimap': 'Field minimap',
      'navigation.dragZoomHint': 'Drag to move · scroll to zoom',
      'navigation.details': 'Details',
      'navigation.time': 'Time',
      'navigation.timeline': 'Timeline',
      'navigation.collapseSidebar': 'Collapse sidebar',
      'navigation.expandSidebar': 'Expand sidebar',
      'navigation.organizationHome': 'Home — organization',
      'navigation.understand': 'Understand',
      'navigation.reason': 'Reason',
      'navigation.prove': 'Prove',
      'navigation.whyMatters': 'Why does this matter?',
      'navigation.whyFollowing': 'Why was I following this?',
      'navigation.whatChanged': 'What changed?',
      'navigation.compareGermany': 'Compare with Germany',
      'navigation.whatUnknown': 'What remains unknown?',
      'navigation.explainSimply': 'Explain simply',
      'navigation.askAboutInformation': 'Ask about this information',
      'navigation.ask': 'Ask',
      'navigation.historySession': 'This session only',
      'navigation.here': 'you are here',
      'navigation.then': 'Then',
      'navigation.now': 'Now',
      'copy.today': 'Today',
      'copy.details.one': '1 detail is in this context.',
      'copy.details.many': '{count} details are in this context.',
      'copy.contextExplanation': 'This view shows the organization and information available in this context.',
      'copy.factMeaning': 'A detail held in this context.',
      'copy.moreDetails': 'More details',
      'copy.currentnessUnknown': "How current this information is hasn't been verified.",
      'copy.connectionsEmpty': '',
      'copy.currentRead': 'Current view',
    }),
  })

  const PREDICATE_KEYS = Object.freeze({
    MANUFACTURES: 'predicate.manufactures',
    SERVES_MARKET: 'predicate.servesMarket',
    MAINTAINS_STANDARD: 'predicate.maintainsStandard',
  })

  const EPISTEMIC_KEYS = Object.freeze({
    OBSERVED: 'epistemic.observed',
    DECLARED: 'epistemic.declared',
    INFERRED: 'epistemic.inferred',
    CORROBORATED: 'epistemic.corroborated',
    CONTRADICTED: 'epistemic.contradicted',
    STALE: 'epistemic.stale',
    UNKNOWN: 'epistemic.unknown',
  })

  const CURRENTNESS_KEYS = Object.freeze({
    CURRENT: 'currentness.current',
    STALE: 'currentness.stale',
    UNKNOWN: 'currentness.unknown',
  })

  function canonicalBcp47Locale(locale) {
    if (typeof locale !== 'string' || !locale.trim()) return 'en'
    try {
      const [canonical] = Intl.getCanonicalLocales(locale.trim().replaceAll('_', '-'))
      const language = canonical.split('-')[0].toLowerCase()
      return Object.hasOwn(COPY, language) ? language : 'en'
    } catch {
      return 'en'
    }
  }

  function requestedLocale() {
    const htmlLocale = root.document?.documentElement?.lang
    const browserLocale = root.navigator?.languages?.[0] ?? root.navigator?.language
    return canonicalBcp47Locale(htmlLocale || browserLocale || 'en')
  }

  function isImplementationValue(value) {
    if (typeof value !== 'string') return true
    const text = value.trim()
    if (!text) return true
    return (
      /^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$/.test(text) ||
      /^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$/.test(text) ||
      /^[a-z]+(?:[A-Z][a-z0-9]*)+$/.test(text) ||
      /^(?:org|xeed|faxt|subject|tenant|principal|evidence|demo)(?:[-_:][A-Za-z0-9-]+)+$/i.test(text)
    )
  }

  function forLocale(locale = requestedLocale()) {
    const resolvedLocale = canonicalBcp47Locale(locale)
    const messages = COPY[resolvedLocale]
    const text = (key, values = {}) => {
      const template = messages[key] ?? COPY.en[key] ?? ''
      return template.replace(/\{(\w+)\}/g, (_match, name) => String(values[name] ?? ''))
    }

    function describeFact(node) {
      const predicateKey = PREDICATE_KEYS[node?.predicate] ?? 'fact.unspecified'
      const predicateLabel = text(predicateKey)
      const valueLabel = isImplementationValue(node?.objectOrValue) ? null : node.objectOrValue.trim()
      const label = valueLabel ? `${predicateLabel} · ${valueLabel}` : predicateLabel
      const epistemicKey = EPISTEMIC_KEYS[node?.epistemicState]
      const currentnessKey = CURRENTNESS_KEYS[node?.currentness]
      const date = node?.observedAt ? new Date(node.observedAt) : null
      const observedAt = date && !Number.isNaN(date.valueOf())
        ? new Intl.DateTimeFormat(resolvedLocale, { dateStyle: 'medium', timeZone: 'UTC' }).format(date)
        : null

      return Object.freeze({
        predicateKey,
        predicateLabel,
        valueLabel,
        label,
        epistemicLabel: epistemicKey ? text(epistemicKey) : null,
        currentnessLabel: currentnessKey ? text(currentnessKey) : null,
        observedAt,
      })
    }

    function countDetails(count) {
      if (count === 1) return text('copy.details.one')
      return text('copy.details.many', { count: new Intl.NumberFormat(resolvedLocale).format(count) })
    }

    return Object.freeze({
      locale: resolvedLocale,
      text,
      describeFact,
      countDetails,
      isImplementationValue,
      formatDate(value) {
        const date = value ? new Date(value) : null
        return date && !Number.isNaN(date.valueOf())
          ? new Intl.DateTimeFormat(resolvedLocale, { dateStyle: 'medium', timeZone: 'UTC' }).format(date)
          : null
      },
    })
  }

  root.AXIGNAL_PRESENTATION = Object.freeze({
    canonicalBcp47Locale,
    forLocale,
    predicateKeys: PREDICATE_KEYS,
    epistemicKeys: EPISTEMIC_KEYS,
    currentnessKeys: CURRENTNESS_KEYS,
  })
})(globalThis)
