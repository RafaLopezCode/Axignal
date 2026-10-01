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
      'context.activeAccessibleName': 'Active Xeed: {name}',
      'context.availableXeeds': 'Available Xeeds',
      'context.searchLabel': 'Search Xeeds',
      'context.searchPlaceholder': 'Search by Xeed name',
      'context.noMatches': 'No matching Xeeds.',
      'context.switchUnavailable': 'Other Xeeds are not available in this demonstration.',
      'context.create': 'New Xeed',
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
      'epistemic.potential': 'Potential',
      'epistemic.historical': 'Historical',
      'epistemic.unknown': 'Not established',
      'currentness.current': 'Marked as current',
      'currentness.stale': 'This information may be out of date.',
      'currentness.unknown': "How current this information is hasn't been verified.",
      'date.lastObserved': 'Last observed',
      'action.open': 'OPEN',
      'today.heading': 'What deserves your attention now',
      'today.subheading': 'Up to three material developments, with what AXIGNAL knows and when it was observed.',
      'today.why': 'Why it matters',
      'today.showHow': 'Show how AXIGNAL knows',
      'today.openMap': 'View in map',
      'today.empty': 'Nothing material is ready from the currently observed state.',
      'today.partial': 'Useful evidence exists, but no material development is ready to surface yet.',
      'today.currentObservation': 'Current observation',
      'mobile.navigation': 'Mobile value navigation',
      'mobile.context': 'Current Xignal',
      'mobile.openAxent': 'Open contextual AXENT',
      'mobile.closeAxent': 'Close AXENT',
      'mobile.openXignal': 'Open Xignal',
      'mobile.why': 'Why it matters',
      'mobile.timelineTitle': 'Timeline',
      'mobile.timelineCurrent': 'Current temporal context',
      'mobile.timelineUnavailable': 'Historical timeline is not exposed by this projection.',
      'mobile.axent': 'AXENT',
      'today.why.manufactures': 'This capability changes what the organization can supply and which markets may matter.',
      'today.why.servesMarket': 'This market connection changes where demand and competitive context should be examined.',
      'today.why.maintainsStandard': 'This standard can change eligibility, trust and the economic relationships worth testing.',
      'today.why.default': 'This information changes the economic picture enough to deserve attention.',
      'error.load': "This view couldn't be loaded.",
      'demo.sample': 'DEMO · EXAMPLE DATA',
      'navigation.account': 'Account',
      'navigation.workspaceNavigation': 'Workspace navigation',
      'navigation.axiglandField': 'AXIGLAND cognitive field',
      'navigation.knowledgeDepth': 'Knowledge and depth',
      'navigation.trail': 'Focus trail',
      'navigation.hiddenStops': '{count} earlier stops hidden',
      'navigation.back': 'Back',
      'navigation.forward': 'Forward',
      'navigation.home': 'Home',
      'navigation.questionsExplore': 'Questions to explore',
      'navigation.context': 'Context',
      'navigation.organization': 'Organization',
      'navigation.connections': 'Connections',
      'connections.fixture': 'Synthetic links · demo',
      'connections.empty': 'No synthetic links from this focus.',
      'connections.linkAccessibleName': '{relation}: {label}; synthetic UX fixture.',
      'connections.type.supports': 'Supports',
      'connections.type.observes': 'Observes',
      'connections.type.compares': 'Compares',
      'connections.type.intersects': 'Intersects',
      'accessible.kicker': 'Non-graph view',
      'accessible.title': 'Relationships and evidence',
      'accessible.focusPath': 'Focus path',
      'accessible.focus': 'Current focus',
      'accessible.relationships': 'Relationships',
      'accessible.relationshipsEmpty': 'No material relationships are available from this focus.',
      'accessible.relationState': 'Relationship state',
      'accessible.openRelated': 'Open related item',
      'accessible.time': 'Time and currentness',
      'accessible.evidence': 'Evidence',
      'accessible.showEvidence': 'Show evidence context',
      'accessible.hideEvidence': 'Hide evidence context',
      'accessible.evidenceUnavailable': 'Evidence access is not exposed by this projection.',
      'accessible.evidenceAvailable': 'Evidence context is available for this item.',
      'accessible.canonicalState': 'Canonical projection status',
      'accessible.observedAt': 'Observed',
      'accessible.currentness': 'Currentness',
      'accessible.epistemicState': 'Knowledge state',
      'accessible.organizationState': 'Organization context',
      'navigation.hideText': 'Hide text',
      'navigation.showText': 'Show text',
      'navigation.questions': 'Questions',
      'navigation.guide': 'View guide',
      'navigation.askAXENT': 'Ask AXENT',
      'navigation.axentConversation': 'AXENT conversation',
      'navigation.currentInvestigation': 'Current focus · {label}',
      'navigation.previousInvestigations': 'Previous investigation',
      'navigation.noConversationForFocus': 'No AXENT conversation exists for this focus yet.',
      'navigation.resumeInvestigation': 'Resume',
      'navigation.askPlaceholder': 'Not active in this view',
      'navigation.cognitiveDepth': 'Cognitive depth',
      'navigation.focus': 'Focus',
      'navigation.field': 'AXIGLAND field',
      'navigation.trail': 'Focus trail',
      'navigation.timeline': 'Timeline',
      'navigation.workspace': 'Workspace',
      'navigation.xeed': 'Xeed',
      'navigation.memory': 'Memory',
      'navigation.scope': 'Scope',
      'navigation.uncertainty': 'Uncertainty',
      'navigation.research': 'Research',
      'navigation.epistemic': 'Knowledge',
      'navigation.createContext': 'Plant Xeed',
      'navigation.createXeed': 'Plant Xeed',
      'navigation.contextScope': 'This view',
      'navigation.memoryUnavailable': 'No memory setting is shown in this view.',
      'navigation.uncertaintyUnavailable': 'No uncertainty setting is shown in this view.',
      'navigation.today': 'Today',
      'navigation.governance': 'Governance',
      'navigation.advancedControls': 'Advanced controls',
      'navigation.moreQuestions': 'More questions',
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
      'navigation.dragZoomHint': 'Drag to pan · wheel/trackpad pans · Ctrl/⌘ + wheel zooms · +/- zoom · 0 fit',
      'spatial.world': 'World',
      'spatial.neighborhood': 'Neighborhood',
      'spatial.relationProof': 'Relation / proof',
      'spatial.status': '{level} · labels {labels} · relations {relations}',
      'spatial.fieldAccessibleName': 'AXIGLAND field. Spatial scale: {level}. Visible labels: {labels}. Visible relationships: {relations}.',
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
      'preferences.label': 'Settings',
      'locale.label': 'Display language',
      'locale.note': 'In this UX lab, the choice is local to this browser. English and Spanish are complete interface languages; other choices are layout previews only.',
      'locale.auto': 'Automatic · supported browser language',
      'locale.en': 'English',
      'locale.es': 'Español',
      'locale.de': 'Deutsch · layout preview',
      'locale.ja': '日本語 · layout preview',
      'locale.ar': 'العربية · layout preview',
      'fixture.youRole': 'You · test data',
      'fixture.axentRole': 'AXENT · test data',
      'fixture.accountUnavailable': 'Account identity unavailable · synthetic test state',
      'fixture.accountLabel': 'QA operator · synthetic',
      'fixture.interactionHint': 'Synthetic test interaction · no live AXENT reasoning or provider call.',
      'fixture.compareRegions': 'Compare regions',
      'fixture.whatUnverified': 'What remains unverified?',
      'fixture.composerPlaceholder': 'Ask a question in this synthetic scenario',
    }),
  })

  const SPANISH_COPY = Object.freeze(root.AXIGNAL_ES_COPY ?? {})
  const COMPLETE_COPY = Object.freeze({
    en: COPY.en,
    es: SPANISH_COPY,
  })

  // A deliberately partial lab catalog for copy-length, script, and direction
  // stress. Missing keys fall back to English; this is not a translation set.
  const LOCALE_STRESS_COPY = Object.freeze({
    de: Object.freeze({
      'organization.label': 'Organisation',
      'connections.fixture': 'Synthetische Demo-Verbindungen',
      'connections.empty': 'Für diesen Fokus gibt es keine synthetischen Verbindungen.',
      'connections.linkAccessibleName': '{relation}: {label}; synthetische UX-Demo-Verbindung.',
      'connections.type.supports': 'Unterstützt',
      'connections.type.observes': 'Beobachtet',
      'connections.type.compares': 'Vergleicht',
      'connections.type.intersects': 'Überschneidet sich mit',
      'navigation.hideText': 'Beschriftungen ausblenden',
      'navigation.showText': 'Beschriftungen einblenden',
      'organization.identity': 'Organisation in der gemeinsam genutzten Welt',
      'organization.meaning': 'Diese Ansicht zeigt die Organisation und alle Informationen, die in diesem Kontext verfügbar sind.',
      'context.private': 'Persönlicher Arbeitskontext',
      'predicate.manufactures': 'Stellt Produkte und Komponenten her',
      'predicate.servesMarket': 'Bedient einen bestimmten Zielmarkt',
      'predicate.maintainsStandard': 'Erfüllt einen geltenden Standard',
      'navigation.today': 'Heutige Übersicht',
      'navigation.createContext': 'Xeed anlegen',
      'navigation.createXeed': 'Xeed anlegen',
      'navigation.workspace': 'Persönlicher Arbeitsbereich',
      'navigation.governance': 'Einstellungen und Zuständigkeiten',
      'navigation.scope': 'Geltungsbereich dieser Ansicht',
      'navigation.memory': 'Kontextbezogenes Gedächtnis',
      'navigation.research': 'Weitere Recherche durchführen',
      'navigation.uncertainty': 'Verbleibende Unsicherheit',
      'navigation.meaning': 'Bedeutung und Einordnung',
      'navigation.context': 'Aktiver privater Arbeitskontext',
      'navigation.inference': 'Abgeleitete Zusammenhänge',
      'navigation.evidence': 'Nachvollziehbare Belege',
      'navigation.depth': 'Detailtiefe der Darstellung',
      'navigation.capabilities': 'Vorhandene Fähigkeiten',
      'navigation.markets': 'Bediente Zielmärkte',
      'navigation.signals': 'Wirtschaftliche Signale',
      'navigation.activity': 'Zeitliche Aktivitäten',
      'navigation.trail': 'Bisheriger Navigationsverlauf',
      'navigation.hiddenStops': '{count} frühere Stationen ausgeblendet',
      'navigation.back': 'Einen Schritt zurück',
      'navigation.forward': 'Einen Schritt weiter',
      'navigation.details': 'Zusätzliche Einzelheiten',
      'navigation.time': 'Zeitliche Entwicklung',
      'navigation.timeline': 'Chronologischer Zeitverlauf',
      'navigation.then': 'Früherer Beobachtungszeitpunkt',
      'navigation.now': 'Aktuelle Ansicht',
      'navigation.guide': 'Kontextbezogene Orientierung',
      'navigation.questions': 'Mögliche nächste Fragen',
      'navigation.askAboutInformation': 'Frage zu diesen Informationen stellen',
      'navigation.ask': 'Frage absenden',
      'navigation.zoomIn': 'Ansicht vergrößern',
      'navigation.zoomOut': 'Ansicht verkleinern',
      'navigation.fitField': 'Alle Knoten passend einblenden',
      'navigation.resetField': 'Feldansicht vollständig zurücksetzen',
      'copy.contextExplanation': 'Diese Ansicht zeigt die globale Organisation und sämtliche Informationen, die im aktuell ausgewählten privaten Kontext verfügbar sind.',
      'copy.details.many': '{count} verfügbare Informationseinträge gehören zu diesem Ansichtskontext.',
    }),
    ja: Object.freeze({
      'organization.label': '組織',
      'connections.fixture': '合成デモの接続',
      'connections.empty': 'このフォーカスに合成データの接続はありません。',
      'connections.linkAccessibleName': '{relation}: {label}。合成 UX データです。',
      'connections.type.supports': '支援',
      'connections.type.observes': '観測',
      'connections.type.compares': '比較',
      'connections.type.intersects': '交差',
      'navigation.hideText': 'ラベルを非表示',
      'navigation.showText': 'ラベルを表示',
      'organization.identity': '共有された世界の組織',
      'organization.meaning': 'このビューには、組織とこのコンテキストで利用できる情報が表示されます。',
      'context.private': 'プライベートビュー',
      'predicate.manufactures': '製造',
      'predicate.servesMarket': '市場にサービスを提供',
      'predicate.maintainsStandard': '規格を維持',
      'navigation.today': '今日',
      'navigation.createContext': 'Xeedを作成',
      'navigation.createXeed': 'Xeedを作成',
      'navigation.workspace': 'ワークスペース',
      'navigation.governance': 'ガバナンス',
      'navigation.scope': '対象範囲',
      'navigation.memory': 'メモリー',
      'navigation.research': '調査',
      'navigation.uncertainty': '不確実性',
      'navigation.meaning': '意味',
      'navigation.context': 'コンテキスト',
      'navigation.inference': '推論',
      'navigation.evidence': '証拠',
      'navigation.depth': '深さ',
      'navigation.capabilities': '能力',
      'navigation.markets': '市場',
      'navigation.signals': 'シグナル',
      'navigation.activity': 'アクティビティ',
      'navigation.trail': 'フォーカス履歴',
      'navigation.hiddenStops': '前の{count}件を省略',
      'navigation.back': '戻る',
      'navigation.forward': '進む',
      'navigation.home': 'ホーム',
      'navigation.details': '詳細',
      'navigation.time': '時間',
      'navigation.timeline': 'タイムライン',
      'navigation.then': '過去',
      'navigation.now': '現在',
      'navigation.guide': 'コンテキストガイド',
      'navigation.questions': '質問',
      'navigation.askAboutInformation': 'この情報について質問',
      'navigation.ask': '質問する',
      'navigation.zoomIn': '拡大',
      'navigation.zoomOut': '縮小',
      'navigation.fitField': '全体を表示',
      'navigation.resetField': '表示をリセット',
      'copy.contextExplanation': 'このビューでは、共有された組織と、このコンテキストに明示的に含まれる情報を確認できます。',
      'copy.details.many': 'このコンテキストには{count}件の詳細があります。',
    }),
    ar: Object.freeze({
      'organization.label': 'المؤسسة',
      'connections.fixture': 'روابط تجريبية اصطناعية',
      'connections.empty': 'لا توجد روابط اصطناعية لهذا العنصر.',
      'connections.linkAccessibleName': '{relation}: {label}؛ رابط اصطناعي للاختبار.',
      'connections.type.supports': 'يدعم',
      'connections.type.observes': 'يراقب',
      'connections.type.compares': 'يقارن',
      'connections.type.intersects': 'يتقاطع مع',
      'navigation.hideText': 'إخفاء التسميات',
      'navigation.showText': 'إظهار التسميات',
      'organization.identity': 'المؤسسة في العالم المشترك',
      'organization.meaning': 'يعرض هذا المنظور المؤسسة والمعلومات المتاحة ضمن هذا السياق.',
      'context.private': 'منظور خاص',
      'predicate.manufactures': 'تصنّع',
      'predicate.servesMarket': 'تخدم سوقًا',
      'predicate.maintainsStandard': 'تحافظ على معيار',
      'navigation.today': 'اليوم',
      'navigation.createContext': 'إنشاء Xeed',
      'navigation.createXeed': 'إنشاء Xeed',
      'navigation.workspace': 'مساحة العمل',
      'navigation.governance': 'الحوكمة',
      'navigation.scope': 'النطاق',
      'navigation.memory': 'الذاكرة',
      'navigation.research': 'البحث',
      'navigation.uncertainty': 'عدم اليقين',
      'navigation.meaning': 'المعنى',
      'navigation.context': 'السياق',
      'navigation.inference': 'الاستدلال',
      'navigation.evidence': 'الأدلة',
      'navigation.depth': 'مستوى التفاصيل',
      'navigation.capabilities': 'القدرات',
      'navigation.markets': 'الأسواق',
      'navigation.signals': 'الإشارات',
      'navigation.activity': 'النشاط',
      'navigation.trail': 'مسار التركيز',
      'navigation.hiddenStops': 'تم إخفاء {count} محطات سابقة',
      'navigation.back': 'رجوع',
      'navigation.forward': 'تقدّم',
      'navigation.home': 'الرئيسية',
      'navigation.details': 'التفاصيل',
      'navigation.time': 'الوقت',
      'navigation.timeline': 'الخط الزمني',
      'navigation.then': 'سابقًا',
      'navigation.now': 'الآن',
      'navigation.guide': 'دليل السياق',
      'navigation.questions': 'أسئلة للاستكشاف',
      'navigation.askAboutInformation': 'اسأل عن هذه المعلومات',
      'navigation.ask': 'اسأل',
      'navigation.zoomIn': 'تكبير العرض',
      'navigation.zoomOut': 'تصغير العرض',
      'navigation.fitField': 'إظهار المجال كاملًا',
      'navigation.resetField': 'إعادة ضبط عرض المجال',
      'copy.contextExplanation': 'يعرض هذا المنظور المؤسسة المشتركة والمعلومات المتاحة صراحةً ضمن هذا السياق.',
      'copy.details.many': 'توجد {count} تفاصيل في هذا السياق.',
    }),
  })

  // A locale is supported for automatic/user locale authority only when its
  // complete UI catalog exists. Partial UX-lab profiles are explicit previews.
  const SUPPORTED_LOCALES = Object.freeze(Object.keys(COMPLETE_COPY))
  const LAYOUT_PREVIEW_LOCALES = Object.freeze([
    ...new Set([...SUPPORTED_LOCALES, ...Object.keys(LOCALE_STRESS_COPY)]),
  ])

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
    POTENTIAL: 'epistemic.potential',
    HISTORICAL: 'epistemic.historical',
    UNKNOWN: 'epistemic.unknown',
  })

  const CURRENTNESS_KEYS = Object.freeze({
    CURRENT: 'currentness.current',
    STALE: 'currentness.stale',
    UNKNOWN: 'currentness.unknown',
  })

  function supportedLocale(locale) {
    if (typeof locale !== 'string' || !locale.trim()) return null
    try {
      const [canonical] = Intl.getCanonicalLocales(locale.trim().replaceAll('_', '-'))
      const language = canonical.split('-')[0].toLowerCase()
      return SUPPORTED_LOCALES.includes(language) ? language : null
    } catch {
      return null
    }
  }

  function canonicalBcp47Locale(locale) {
    return supportedLocale(locale) ?? 'en'
  }

  function layoutPreviewLocale(locale) {
    if (typeof locale !== 'string' || !locale.trim()) return null
    try {
      const [canonical] = Intl.getCanonicalLocales(locale.trim().replaceAll('_', '-'))
      const language = canonical.split('-')[0].toLowerCase()
      return LAYOUT_PREVIEW_LOCALES.includes(language) ? language : null
    } catch {
      return null
    }
  }

  function canonicalLayoutPreviewLocale(locale) {
    return layoutPreviewLocale(locale) ?? 'en'
  }

  function resolveLocale(userLocale, browserLocales = [], fallbackLocale = 'en') {
    const explicit = supportedLocale(userLocale)
    if (explicit) return explicit
    const browserPreferences = Array.isArray(browserLocales) ? browserLocales : [browserLocales]
    for (const preference of browserPreferences) {
      const resolved = supportedLocale(preference)
      if (resolved) return resolved
    }
    return supportedLocale(fallbackLocale) ?? 'en'
  }

  function requestedLocale() {
    const browserLocales = root.navigator?.languages ?? [root.navigator?.language]
    return resolveLocale(null, browserLocales)
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

  function createPresentation(resolvedLocale, messages) {
    const text = (key, values = {}) => {
      const template = messages[key] ?? COMPLETE_COPY.en[key] ?? ''
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
      direction: resolvedLocale === 'ar' ? 'rtl' : 'ltr',
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

  function forLocale(locale = requestedLocale()) {
    const resolvedLocale = canonicalBcp47Locale(locale)
    return createPresentation(resolvedLocale, COMPLETE_COPY[resolvedLocale])
  }

  function forLayoutPreview(locale = 'en') {
    const resolvedLocale = canonicalLayoutPreviewLocale(locale)
    const messages = COMPLETE_COPY[resolvedLocale]
      ?? { ...COMPLETE_COPY.en, ...(LOCALE_STRESS_COPY[resolvedLocale] ?? {}) }
    return createPresentation(resolvedLocale, messages)
  }

  root.AXIGNAL_PRESENTATION = Object.freeze({
    canonicalBcp47Locale,
    isSupportedLocale: (locale) => supportedLocale(locale) !== null,
    resolveLocale,
    supportedLocales: SUPPORTED_LOCALES,
    canonicalLayoutPreviewLocale,
    isLayoutPreviewLocale: (locale) => layoutPreviewLocale(locale) !== null,
    layoutPreviewLocales: LAYOUT_PREVIEW_LOCALES,
    forLocale,
    forLayoutPreview,
    predicateKeys: PREDICATE_KEYS,
    epistemicKeys: EPISTEMIC_KEYS,
    currentnessKeys: CURRENTNESS_KEYS,
  })
})(globalThis)
