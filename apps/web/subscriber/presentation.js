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
      'epistemic.unknown': 'Not established',
      'currentness.current': 'Marked as current',
      'currentness.stale': 'This information may be out of date.',
      'currentness.unknown': "How current this information is hasn't been verified.",
      'date.lastObserved': 'Last observed',
      'action.open': 'OPEN',
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
      'navigation.hideText': 'Hide text',
      'navigation.showText': 'Show text',
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
      'preferences.label': 'Settings',
      'locale.label': 'Display language · preview',
      'locale.note': 'Synthetic layout preview only. This is not a complete translation or an account setting.',
      'locale.auto': 'Automatic · browser preference',
      'locale.en': 'English · baseline',
      'locale.es': 'Español · sample copy',
      'locale.de': 'Deutsch · text expansion',
      'locale.ja': '日本語 · CJK layout',
      'locale.ar': 'العربية · RTL layout',
    }),
  })

  // A deliberately partial lab catalog for copy-length, script, and direction
  // stress. Missing keys fall back to English; this is not a translation set.
  const LOCALE_STRESS_COPY = Object.freeze({
    es: Object.freeze({
      'organization.label': 'Organización',
      'connections.fixture': 'Enlaces sintéticos · demo',
      'connections.empty': 'No hay enlaces sintéticos en este foco.',
      'connections.linkAccessibleName': '{relation}: {label}; relación sintética de demostración.',
      'connections.type.supports': 'Apoya',
      'connections.type.observes': 'Observa',
      'connections.type.compares': 'Compara',
      'connections.type.intersects': 'Se cruza con',
      'navigation.hideText': 'Ocultar texto',
      'navigation.showText': 'Mostrar texto',
      'organization.identity': 'Organización en el mundo compartido',
      'organization.meaning': 'Esta vista reúne la organización y la información disponible en este contexto.',
      'context.private': 'Vista privada',
      'predicate.manufactures': 'Fabrica',
      'predicate.servesMarket': 'Atiende a un mercado',
      'predicate.maintainsStandard': 'Mantiene una norma',
      'navigation.today': 'Hoy',
      'navigation.workspace': 'Espacio de trabajo',
      'navigation.xeed': 'Xeed',
      'navigation.createContext': 'Crear Xeed',
      'navigation.createXeed': 'Crear Xeed',
      'navigation.governance': 'Gobernanza',
      'navigation.scope': 'Alcance',
      'navigation.memory': 'Memoria',
      'navigation.research': 'Investigación',
      'navigation.uncertainty': 'Incertidumbre',
      'navigation.meaning': 'Significado',
      'navigation.context': 'Contexto',
      'navigation.inference': 'Inferencia',
      'navigation.evidence': 'Evidencia',
      'navigation.depth': 'Profundidad',
      'navigation.capabilities': 'Capacidades',
      'navigation.markets': 'Mercados',
      'navigation.signals': 'Señales',
      'navigation.activity': 'Actividad',
      'navigation.trail': 'Recorrido de enfoque',
      'navigation.hiddenStops': '{count} pasos anteriores ocultos',
      'navigation.back': 'Atrás',
      'navigation.forward': 'Adelante',
      'navigation.home': 'Inicio',
      'navigation.details': 'Detalles',
      'navigation.time': 'Tiempo',
      'navigation.timeline': 'Línea temporal',
      'navigation.then': 'Antes',
      'navigation.now': 'Ahora',
      'navigation.guide': 'Guía de contexto',
      'navigation.questions': 'Preguntas',
      'navigation.askAboutInformation': 'Preguntar sobre esta información',
      'navigation.ask': 'Preguntar',
      'navigation.zoomIn': 'Acercar',
      'navigation.zoomOut': 'Alejar',
      'navigation.fitField': 'Ajustar el campo',
      'navigation.resetField': 'Restablecer la vista del campo',
      'copy.contextExplanation': 'Esta vista muestra la organización y la información disponible en este contexto.',
      'copy.details.many': 'Hay {count} detalles en este contexto.',
    }),
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

  const SUPPORTED_LOCALES = Object.freeze(['en', ...Object.keys(LOCALE_STRESS_COPY)])

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

  function forLocale(locale = requestedLocale()) {
    const resolvedLocale = canonicalBcp47Locale(locale)
    const messages = { ...COPY.en, ...(LOCALE_STRESS_COPY[resolvedLocale] ?? {}) }
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

  root.AXIGNAL_PRESENTATION = Object.freeze({
    canonicalBcp47Locale,
    isSupportedLocale: (locale) => supportedLocale(locale) !== null,
    resolveLocale,
    supportedLocales: SUPPORTED_LOCALES,
    forLocale,
    predicateKeys: PREDICATE_KEYS,
    epistemicKeys: EPISTEMIC_KEYS,
    currentnessKeys: CURRENTNESS_KEYS,
  })
})(globalThis)
