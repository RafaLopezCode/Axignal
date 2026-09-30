const $ = (selector) => document.querySelector(selector)
const LUCIDE_SPRITE = '/assets/icons/lucide/axignal-ui.svg#'
function axignalIcon(name) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  svg.classList.add('ax-icon')
  svg.setAttribute('aria-hidden', 'true')
  svg.setAttribute('focusable', 'false')
  const use = document.createElementNS('http://www.w3.org/2000/svg', 'use')
  use.setAttribute('href', `${LUCIDE_SPRITE}${name}`)
  svg.append(use)
  return svg
}
const LOCALE_PREFERENCE_KEY = 'axignal.synthetic-ui-locale'
const isLoopbackScenario = window.location.hostname === '127.0.0.1'
  && Boolean(new URLSearchParams(window.location.search).get('scenario'))
let storedLocale = null
if (isLoopbackScenario) {
  try {
    storedLocale = window.localStorage.getItem(LOCALE_PREFERENCE_KEY)
    // Layout-stress profiles are not complete UI languages. Clear any legacy
    // preview persisted as though it were a user locale; previews stay explicit.
    if (storedLocale && !window.AXIGNAL_PRESENTATION.isSupportedLocale(storedLocale)) {
      window.localStorage.removeItem(LOCALE_PREFERENCE_KEY)
      storedLocale = null
    }
  } catch {
    storedLocale = null
  }
}
const browserLocalePreferences = navigator.languages?.length
  ? navigator.languages
  : [navigator.language]
let presentation = window.AXIGNAL_PRESENTATION.forLocale(
  window.AXIGNAL_PRESENTATION.resolveLocale(
    window.AXIGNAL_PRESENTATION.isSupportedLocale(storedLocale) ? storedLocale : null,
    browserLocalePreferences,
    'en',
  ),
)
let explicitUserLocale = isLoopbackScenario
  && window.AXIGNAL_PRESENTATION.isSupportedLocale(storedLocale)
  ? window.AXIGNAL_PRESENTATION.canonicalBcp47Locale(storedLocale)
  : null

document.documentElement.lang = presentation.locale
document.documentElement.dir = presentation.direction

function applyPresentationCopy() {
  for (const element of document.querySelectorAll('[data-copy]')) {
    element.textContent = presentation.text(element.dataset.copy)
  }
  for (const element of document.querySelectorAll('[data-copy-aria-label]')) {
    element.setAttribute('aria-label', presentation.text(element.dataset.copyAriaLabel))
  }
  for (const element of document.querySelectorAll('[data-copy-placeholder]')) {
    element.setAttribute('placeholder', presentation.text(element.dataset.copyPlaceholder))
  }
  for (const element of document.querySelectorAll('[data-copy-title]')) {
    element.setAttribute('title', presentation.text(element.dataset.copyTitle))
  }
  for (const element of document.querySelectorAll('[data-copy-content]')) {
    element.setAttribute('content', presentation.text(element.dataset.copyContent))
  }
}

applyPresentationCopy()

const state = {
  projection: null,
  focus: null,
  history: [],
  historyIndex: -1,
  depth: 0,
  bottomTabCollapsed: false,
  camera: { x: 0, y: 0, zoom: 1 },
  pointer: null,
  cameraFrame: 0,
  size: { width: 0, height: 0 },
  worldNodes: [],
  uxLab: null,
  axentMessages: [],
}

function applyUiLocale(locale, { persist = false, selectionValue = locale } = {}) {
  const resolvedLocale = window.AXIGNAL_PRESENTATION.canonicalLayoutPreviewLocale(locale)
  presentation = window.AXIGNAL_PRESENTATION.forLayoutPreview(resolvedLocale)
  document.documentElement.lang = presentation.locale
  document.documentElement.dir = presentation.direction
  app.dataset.uiLocale = presentation.locale
  applyPresentationCopy()
  const selector = $('#ui-locale')
  if (selector) selector.value = selectionValue
  if (persist && state.uxLab && isLoopbackScenario) {
    try {
      if (window.AXIGNAL_PRESENTATION.isSupportedLocale(resolvedLocale)) {
        window.localStorage.setItem(LOCALE_PREFERENCE_KEY, resolvedLocale)
        explicitUserLocale = resolvedLocale
      } else {
        window.localStorage.removeItem(LOCALE_PREFERENCE_KEY)
        explicitUserLocale = null
      }
    } catch {
      // Keep the in-page preference usable when browser storage is unavailable.
    }
  }
  if (state.projection) render()
}

const app = $('.app2')
const field = $('#field')
const cameraLayer = $('#camera-layer')
const minimapNodes = $('#minimap-nodes')
const minimapRelationships = $('#minimap-relationships')
const minimapWindow = $('#minimap-window')
const relationshipLayer = $('#relationship-layer')
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)')
const OVERVIEW_LABEL_ZOOM = 0.78
const FIELD_SLOTS = [
  { x: 24, y: 34 },
  { x: 76, y: 58 },
  { x: 38, y: 78 },
  { x: 82, y: 28 },
  { x: 64, y: 18 },
  { x: 16, y: 66 },
  { x: 88, y: 76 },
  { x: 34, y: 18 },
]
const MINIMAP = { width: 160, height: 96, inset: 8 }
const EPISTEMIC_STATES = new Set([
  'OBSERVED', 'CORROBORATED', 'INFERRED', 'POTENTIAL', 'UNKNOWN', 'STALE', 'CONTRADICTED', 'HISTORICAL',
])

function epistemicStateClass(value) {
  return EPISTEMIC_STATES.has(value) ? value.toLowerCase() : 'unknown'
}

function minimapBounds(nodes = state.worldNodes) {
  if (!nodes.length) return { x0: 0, x1: 100, y0: 0, y1: 100 }
  const axisBounds = (values) => {
    const minimum = Math.min(...values)
    const maximum = Math.max(...values)
    const extent = Math.max(maximum - minimum, 12)
    const center = (minimum + maximum) / 2
    return [center - extent / 2, center + extent / 2]
  }
  const [x0, x1] = axisBounds(nodes.map((node) => node.x))
  const [y0, y1] = axisBounds(nodes.map((node) => node.y))
  return { x0, x1, y0, y1 }
}

function minimapPoint(x, y, bounds) {
  const spanX = MINIMAP.width - 2 * MINIMAP.inset
  const spanY = MINIMAP.height - 2 * MINIMAP.inset
  return {
    x: MINIMAP.inset + ((x - bounds.x0) / (bounds.x1 - bounds.x0)) * spanX,
    y: MINIMAP.inset + ((y - bounds.y0) / (bounds.y1 - bounds.y0)) * spanY,
  }
}

function projectionKey(kind, id) {
  return `${kind}:${id}`
}

function organizationKey() {
  return projectionKey('ORGANIZATION', state.projection.organization.id)
}

function describeFactForView(source) {
  const override = state.uxLab?.presentationOverrides?.epistemicState?.[source.id]
  const currentness = state.uxLab?.presentationOverrides?.currentness?.[source.id]
  const fact = presentation.describeFact({
    ...source,
    ...(override ? { epistemicState: override } : {}),
    ...(currentness ? { currentness } : {}),
  })
  if (override === 'POTENTIAL') return Object.freeze({ ...fact, epistemicLabel: 'Possible · synthetic' })
  if (override === 'UNKNOWN') return Object.freeze({ ...fact, epistemicLabel: 'Not established · synthetic' })
  return fact
}

function getNode(key) {
  if (!state.projection) return null
  if (key === organizationKey()) {
    const node = state.projection.organization
    return {
      key,
      id: node.id,
      kind: 'ORGANIZATION',
      label: presentation.isImplementationValue(node.name)
        ? presentation.text('organization.label')
        : node.name,
      source: node,
    }
  }
  const source = state.projection.nodes.find((item) => projectionKey('FAXT', item.id) === key)
  return source
    ? { key, id: source.id, kind: 'FAXT', label: describeFactForView(source).label, source }
    : null
}

function focusedNode() {
  return getNode(state.focus) ?? getNode(organizationKey())
}

function depthName(value) {
  if (value < 0.7) return presentation.text('navigation.glance')
  if (value < 1.5) return presentation.text('navigation.understand')
  if (value < 2.4) return presentation.text('navigation.reason')
  return presentation.text('navigation.prove')
}

function worldPositions() {
  const references = state.projection?.nodes ?? []
  const nodes = [{ ...getNode(organizationKey()), x: 50, y: 48 }]
  references.forEach((source, index) => {
    const slot = FIELD_SLOTS[index % FIELD_SLOTS.length]
    const row = Math.floor(index / FIELD_SLOTS.length)
    nodes.push({
      key: projectionKey('FAXT', source.id),
      id: source.id,
      kind: 'FAXT',
      label: describeFactForView(source).label,
      source,
      x: slot.x,
      y: Math.max(10, Math.min(90, slot.y + row * 4)),
    })
  })
  return nodes
}

function cameraPoint(node) {
  return {
    x: state.camera.x + (node.x / 100) * state.size.width * state.camera.zoom,
    y: state.camera.y + (node.y / 100) * state.size.height * state.camera.zoom,
  }
}

function updateCamera() {
  for (const element of cameraLayer.querySelectorAll('.anch')) {
    const node = state.worldNodes.find((item) => item.key === element.dataset.key)
    if (!node) continue
    const point = cameraPoint(node)
    element.style.left = `${point.x}px`
    element.style.top = `${point.y}px`
  }
  layoutLabels()
  renderRelationships()
  updateMinimap()
}

function rectanglesOverlap(first, second, clearance = 4) {
  return first.left < second.right + clearance
    && first.right + clearance > second.left
    && first.top < second.bottom + clearance
    && first.bottom + clearance > second.top
}

function segmentIntersectsRectangle(start, end, rect) {
  const dx = end.x - start.x
  const dy = end.y - start.y
  const p = [-dx, dx, -dy, dy]
  const q = [start.x - rect.left, rect.right - start.x, start.y - rect.top, rect.bottom - start.y]
  let lower = 0
  let upper = 1
  for (let index = 0; index < p.length; index += 1) {
    if (p[index] === 0) {
      if (q[index] < 0) return false
      continue
    }
    const ratio = q[index] / p[index]
    if (p[index] < 0) lower = Math.max(lower, ratio)
    else upper = Math.min(upper, ratio)
    if (lower > upper) return false
  }
  return true
}

function labelPriority(node, connectedToFocus) {
  if (node.key === state.focus) return 0
  if (node.kind === 'ORGANIZATION') return 1
  if (connectedToFocus.has(node.id)) return 2
  return 3
}

function layoutLabels() {
  const fieldBounds = field.getBoundingClientRect()
  const focus = state.worldNodes.find((node) => node.key === state.focus)
  const connectedToFocus = new Set()
  if (focus && state.uxLab) {
    for (const edge of state.uxLab.edges ?? []) {
      if (edge.source === focus.id) connectedToFocus.add(edge.target)
      if (edge.target === focus.id) connectedToFocus.add(edge.source)
    }
  }

  const nodes = [...cameraLayer.querySelectorAll('.anch')]
    .map((element) => ({
      element,
      label: element.querySelector('.anch-lbl'),
      mark: element.querySelector('.dot'),
      node: state.worldNodes.find((item) => item.key === element.dataset.key),
    }))
    .filter((item) => item.label && item.mark && item.node)
  const occupiedNodes = nodes.map(({ mark, node }) => {
    const rect = mark.getBoundingClientRect()
    return {
      key: node.key,
      rect: {
        left: rect.left - 3,
        right: rect.right + 3,
        top: rect.top - 3,
        bottom: rect.bottom + 3,
      },
    }
  })
  const ordered = nodes.sort((first, second) =>
    labelPriority(first.node, connectedToFocus) - labelPriority(second.node, connectedToFocus)
    || first.node.y - second.node.y
    || first.node.x - second.node.x
    || first.node.key.localeCompare(second.node.key),
  )
  const occupiedLabels = []
  const sides = ['right', 'left', 'below', 'above']
  const fixedObstacles = [...field.querySelectorAll('.canvas-tools, .minimap, .here, .zone')]
    .map((element) => element.getBoundingClientRect())
  const edgeSegments = (state.uxLab?.edges ?? []).flatMap((edge) => {
    const source = state.worldNodes.find((node) => node.id === edge.source)
    const target = state.worldNodes.find((node) => node.id === edge.target)
    if (!source || !target) return []
    const start = cameraPoint(source)
    const end = cameraPoint(target)
    return [{
      start: { x: fieldBounds.left + start.x, y: fieldBounds.top + start.y },
      end: { x: fieldBounds.left + end.x, y: fieldBounds.top + end.y },
    }]
  })

  for (const item of ordered) {
    const { label, node } = item
    const preferred = label.dataset.preferredSide ?? 'right'
    const candidates = [preferred, ...sides.filter((side) => side !== preferred)]
    const mark = item.mark.getBoundingClientRect()
    const labelBounds = label.getBoundingClientRect()
    const priority = labelPriority(node, connectedToFocus)
    const centerX = mark.left + mark.width / 2
    const centerY = mark.top + mark.height / 2
    const gap = 15
    const candidateBounds = (side) => {
      let left = centerX - labelBounds.width / 2
      let top = centerY - labelBounds.height / 2
      if (side === 'right') {
        left = centerX + gap
      } else if (side === 'left') {
        left = centerX - gap - labelBounds.width
      } else if (side === 'below') {
        top = centerY + gap
      } else {
        top = centerY - gap - labelBounds.height
      }
      return {
        left,
        right: left + labelBounds.width,
        top,
        bottom: top + labelBounds.height,
      }
    }
    let accepted = null
    let attentionFallback = null

    if (state.camera.zoom < OVERVIEW_LABEL_ZOOM && priority > 1) {
      for (const side of sides) label.classList.remove(`side-${side}`)
      label.classList.add(`side-${preferred}`, 'is-decluttered')
      label.dataset.layoutVisibility = 'semantic-zoom-hidden'
      continue
    }

    for (const side of candidates) {
      const rect = candidateBounds(side)
      const insideField = rect.left >= fieldBounds.left + 2
        && rect.right <= fieldBounds.right - 2
        && rect.top >= fieldBounds.top + 2
        && rect.bottom <= fieldBounds.bottom - 2
      const overlapsNode = occupiedNodes.some((occupied) =>
        occupied.key !== node.key && rectanglesOverlap(rect, occupied.rect),
      )
      const overlapsLabel = occupiedLabels.some((occupied) => rectanglesOverlap(rect, occupied))
      const overlapsObstacle = fixedObstacles.some((occupied) => rectanglesOverlap(rect, occupied))
      const overlapsEdge = edgeSegments.some((segment) =>
        segmentIntersectsRectangle(segment.start, segment.end, rect),
      )
      if (insideField && !overlapsNode && !overlapsLabel && !overlapsObstacle && !attentionFallback) {
        attentionFallback = { side, rect }
      }
      if (insideField && !overlapsNode && !overlapsLabel && !overlapsObstacle && !overlapsEdge) {
        accepted = { side, rect }
        break
      }
    }

    if (accepted) {
      for (const side of sides) label.classList.remove(`side-${side}`)
      label.classList.add(`side-${accepted.side}`)
      label.classList.remove('is-decluttered')
      occupiedLabels.push(accepted.rect)
      label.dataset.layoutVisibility = 'visible'
      continue
    }

    if (attentionFallback && priority <= 2) {
      for (const side of sides) label.classList.remove(`side-${side}`)
      label.classList.add(`side-${attentionFallback.side}`)
      label.classList.remove('is-decluttered')
      label.dataset.layoutVisibility = 'visible-edge-overlap'
      occupiedLabels.push(attentionFallback.rect)
      continue
    }

    for (const candidate of sides) label.classList.remove(`side-${candidate}`)
    label.classList.add(`side-${preferred}`)
    if (priority === 0) {
      label.classList.remove('is-decluttered')
      occupiedLabels.push(candidateBounds(preferred))
      label.dataset.layoutVisibility = 'priority-visible'
    } else {
      label.classList.add('is-decluttered')
      label.dataset.layoutVisibility = 'attention-decluttered'
    }
  }
}

function renderRelationships() {
  if (!relationshipLayer) return
  relationshipLayer.replaceChildren()
  const edges = state.uxLab?.edges ?? []
  relationshipLayer.setAttribute('viewBox', `0 0 ${state.size.width} ${state.size.height}`)
  for (const edge of edges) {
    const source = state.worldNodes.find((node) => node.id === edge.source)
    const target = state.worldNodes.find((node) => node.id === edge.target)
    if (!source || !target) continue
    const start = cameraPoint(source)
    const end = cameraPoint(target)
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line')
    line.setAttribute('x1', String(start.x))
    line.setAttribute('y1', String(start.y))
    line.setAttribute('x2', String(end.x))
    line.setAttribute('y2', String(end.y))
    const focus = state.worldNodes.find((node) => node.key === state.focus)
    const isAttentionEdge = focus && (edge.source === focus.id || edge.target === focus.id)
    line.setAttribute(
      'class',
      `lab-edge edge-${edge.type} epistemic-${epistemicStateClass(edge.epistemicState)} ${isAttentionEdge ? 'is-attention' : 'is-attenuated'}`,
    )
    line.dataset.synthetic = String(edge.syntheticFixture)
    relationshipLayer.append(line)
  }
}

function renderConnections(focus) {
  const section = $('#connection-section')
  const list = $('#connection-list')
  const empty = $('#connections-empty')
  list.replaceChildren()
  if (!state.uxLab) {
    section.hidden = true
    return
  }

  const focusId = focus?.id
  const edges = (state.uxLab.edges ?? []).filter((edge) =>
    edge.syntheticFixture === true && (edge.source === focusId || edge.target === focusId),
  )
  for (const edge of edges) {
    const targetId = edge.source === focusId ? edge.target : edge.source
    const target = state.worldNodes.find((node) => node.id === targetId)
    if (!target) continue
    const relation = presentation.text(`connections.type.${edge.type}`)
    const accessibleName = presentation.text('connections.linkAccessibleName', {
      relation,
      label: target.label,
    })
    const button = document.createElement('button')
    button.className = `conn-btn epistemic-${epistemicStateClass(edge.epistemicState)}`
    button.type = 'button'
    button.dataset.synthetic = 'true'
    button.setAttribute('aria-label', accessibleName)
    button.title = accessibleName
    const stateDot = document.createElement('span')
    stateDot.className = 'conn-state-dot'
    stateDot.setAttribute('aria-hidden', 'true')
    const relationLabel = document.createElement('i')
    relationLabel.textContent = relation
    const targetLabel = document.createElement('b')
    targetLabel.textContent = target.label
    button.append(stateDot, relationLabel, targetLabel)
    button.addEventListener('click', () => navigate(target.key))
    list.append(button)
  }

  section.hidden = false
  empty.hidden = list.childElementCount > 0
}

function renderBottomTabVisibility() {
  $('.bottom').classList.toggle('collapsed', state.bottomTabCollapsed)
  const key = state.bottomTabCollapsed ? 'navigation.showText' : 'navigation.hideText'
  const label = presentation.text(key)
  const toggle = $('#labels-toggle')
  toggle.textContent = label
  toggle.title = label
  toggle.setAttribute('aria-label', label)
  toggle.setAttribute('aria-expanded', String(!state.bottomTabCollapsed))
}

function updateMinimap() {
  const { width, height } = state.size
  if (!width || !height) return
  const bounds = minimapBounds()
  const zoom = state.camera.zoom
  const xLeft = ((-state.camera.x / zoom) / width) * 100
  const xRight = (((width - state.camera.x) / zoom) / width) * 100
  const yTop = ((-state.camera.y / zoom) / height) * 100
  const yBottom = (((height - state.camera.y) / zoom) / height) * 100
  const cameraTopLeft = minimapPoint(xLeft, yTop, bounds)
  const cameraBottomRight = minimapPoint(xRight, yBottom, bounds)
  const mapRight = MINIMAP.width - MINIMAP.inset
  const mapBottom = MINIMAP.height - MINIMAP.inset
  const left = Math.max(MINIMAP.inset, Math.min(mapRight, cameraTopLeft.x))
  const top = Math.max(MINIMAP.inset, Math.min(mapBottom, cameraTopLeft.y))
  const right = Math.max(MINIMAP.inset, Math.min(mapRight, cameraBottomRight.x))
  const bottom = Math.max(MINIMAP.inset, Math.min(mapBottom, cameraBottomRight.y))
  minimapWindow.setAttribute('x', String(left))
  minimapWindow.setAttribute('y', String(top))
  minimapWindow.setAttribute('width', String(Math.max(0, right - left)))
  minimapWindow.setAttribute('height', String(Math.max(0, bottom - top)))
  if (!minimapRelationships) return
  minimapRelationships.replaceChildren()
  for (const edge of state.uxLab?.edges ?? []) {
    const source = state.worldNodes.find((node) => node.id === edge.source)
    const target = state.worldNodes.find((node) => node.id === edge.target)
    if (!source || !target) continue
    const point = (node) => minimapPoint(node.x, node.y, bounds)
    const start = point(source)
    const end = point(target)
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line')
    line.setAttribute('x1', String(start.x))
    line.setAttribute('y1', String(start.y))
    line.setAttribute('x2', String(end.x))
    line.setAttribute('y2', String(end.y))
    line.setAttribute('class', `mini-edge edge-${edge.type} epistemic-${epistemicStateClass(edge.epistemicState)}`)
    line.dataset.synthetic = String(edge.syntheticFixture)
    minimapRelationships.append(line)
  }
}

function makeMark(node) {
  const mark = document.createElement('span')
  const status = node.kind === 'ORGANIZATION'
    ? 'ORGANIZATION'
    : state.uxLab?.presentationOverrides?.epistemicState?.[node.id] ?? node.source.epistemicState
  mark.className = `dot mk ${status}`
  mark.setAttribute('aria-hidden', 'true')
  const halo = document.createElement('span')
  halo.className = 'halo'
  mark.append(halo)
  return mark
}

function nodeLabel(node) {
  const label = document.createElement('span')
  const isRight = node.x < 55
  const side = Math.abs(node.x - 50) < 9
    ? 'below'
    : isRight ? 'right' : 'left'
  label.className = `anch-lbl side-${side}`
  label.dataset.preferredSide = side
  label.dir = 'auto'
  if (node.kind === 'ORGANIZATION') {
    label.textContent = node.label
    return label
  }

  const fact = describeFactForView(node.source)
  const predicate = document.createElement('span')
  predicate.textContent = fact.predicateLabel
  const value = document.createElement('span')
  value.className = 'node-value'
  if (fact.valueLabel) {
    value.textContent = fact.valueLabel
    value.dir = 'auto'
    label.append(predicate, value)
  } else {
    label.append(predicate)
  }
  return label
}

function makeNode(node) {
  const element = document.createElement('button')
  const selected = state.focus === node.key
  const dimmed = state.focus !== organizationKey() && state.focus !== node.key
  element.type = 'button'
  element.className = `anch ${node.kind === 'ORGANIZATION' ? 'organization anchor' : 'anchor'}${selected ? ' is-focus' : ''}${dimmed ? ' dim' : ''}`
  element.dataset.id = node.id
  element.dataset.key = node.key
  element.dataset.kind = node.kind
  element.dataset.worldX = String(node.x)
  element.dataset.worldY = String(node.y)
  element.title = node.label
  element.setAttribute('aria-pressed', String(selected))
  if (node.kind === 'ORGANIZATION') {
    element.setAttribute('aria-label', `${presentation.text('organization.label')}: ${node.label}`)
  } else {
    element.setAttribute('aria-label', node.label)
  }
  element.append(makeMark(node), nodeLabel(node))
  element.addEventListener('pointerdown', (event) => event.stopPropagation())
  element.addEventListener('click', (event) => {
    event.stopPropagation()
    navigate(node.key)
  })
  element.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      navigate(node.key)
    }
  })
  return element
}

function renderMap() {
  if (!state.projection) return
  state.size = { width: field.clientWidth, height: field.clientHeight }
  state.worldNodes = worldPositions()
  cameraLayer.replaceChildren()
  if (relationshipLayer) cameraLayer.append(relationshipLayer)
  minimapNodes.replaceChildren()
  minimapRelationships?.replaceChildren()
  const mapBounds = minimapBounds(state.worldNodes)

  for (const node of state.worldNodes) {
    cameraLayer.append(makeNode(node))
    const mini = document.createElementNS('http://www.w3.org/2000/svg', 'circle')
    const epistemicState = node.kind === 'ORGANIZATION'
      ? 'UNKNOWN'
      : state.uxLab?.presentationOverrides?.epistemicState?.[node.id] ?? node.source.epistemicState
    mini.setAttribute(
      'class',
      `mini-node epistemic-${epistemicStateClass(epistemicState)}${node.kind === 'ORGANIZATION' ? ' organization' : ''}`,
    )
    const mapPoint = minimapPoint(node.x, node.y, mapBounds)
    mini.setAttribute('cx', String(mapPoint.x))
    mini.setAttribute('cy', String(mapPoint.y))
    mini.setAttribute('r', node.kind === 'ORGANIZATION' ? '3.5' : '2.7')
    minimapNodes.append(mini)
  }

  const empty = $('#empty-field')
  if (empty) empty.remove()
  if (state.projection.nodes.length === 0) {
    const message = document.createElement('p')
    message.id = 'empty-field'
    message.className = 'empty-field'
    message.textContent = presentation.text('organization.empty')
    field.append(message)
  }
  updateCamera()
}

function pushHistory(key) {
  if (state.history[state.historyIndex] === key) return
  state.history = state.history.slice(0, state.historyIndex + 1)
  state.history.push(key)
  state.historyIndex = state.history.length - 1
}

function animateCamera(target) {
  window.cancelAnimationFrame(state.cameraFrame)
  const from = { ...state.camera }
  if (reduceMotion.matches) {
    state.camera = target
    updateCamera()
    return
  }
  const started = performance.now()
  const duration = 440
  const tick = (now) => {
    const progress = Math.min(1, (now - started) / duration)
    const eased = 1 - Math.pow(1 - progress, 3)
    state.camera = {
      x: from.x + (target.x - from.x) * eased,
      y: from.y + (target.y - from.y) * eased,
      zoom: from.zoom + (target.zoom - from.zoom) * eased,
    }
    updateCamera()
    if (progress < 1) state.cameraFrame = window.requestAnimationFrame(tick)
  }
  state.cameraFrame = window.requestAnimationFrame(tick)
}

function focusCamera(key) {
  const node = state.worldNodes.find((item) => item.key === key)
  if (!node) return
  const zoom = 1.22
  animateCamera({
    x: state.size.width / 2 - (node.x / 100) * state.size.width * zoom,
    y: state.size.height / 2 - (node.y / 100) * state.size.height * zoom,
    zoom,
  })
}

function navigate(key, { record = true, recenter = true } = {}) {
  if (!getNode(key)) return
  setBottomView('reader')
  if (record) pushHistory(key)
  state.focus = key
  render()
  if (recenter) focusCamera(key)
}

function setBottomView(view, restoreFocus = false) {
  const showPreferences = view === 'preferences' && Boolean(state.uxLab)
  if (showPreferences) state.bottomTabCollapsed = false
  $('#reader').hidden = showPreferences
  $('#preferences-view').hidden = !showPreferences
  $('.bottom').classList.toggle('preferences-open', showPreferences)
  renderBottomTabVisibility()
  $('#preferences-open').setAttribute('aria-expanded', String(showPreferences))
  if (restoreFocus) $('#preferences-open').focus()
  else if (showPreferences) $('#ui-locale').focus()
}

function setReaderField(target, value) {
  if (value == null || value === '') return null
  const wrapper = document.createElement('div')
  wrapper.className = 'reader-field'
  const term = document.createElement('dt')
  term.textContent = target
  const detail = document.createElement('dd')
  detail.textContent = String(value)
  wrapper.append(term, detail)
  return wrapper
}

function makeReaderHeader(kickerText, titleText, meaningText, kind) {
  const header = document.createElement('div')
  header.className = 'reader-head'
  const kicker = document.createElement('span')
  kicker.className = 'mono'
  kicker.id = 'reader-kicker'
  kicker.textContent = kickerText
  const stateLabel = document.createElement('span')
  stateLabel.className = 'reader-state'
  stateLabel.id = 'selected-kind'
  stateLabel.textContent = kind === 'ORGANIZATION'
    ? presentation.text('organization.label')
    : presentation.text('field.information')
  header.append(kicker, stateLabel)

  const title = document.createElement('h1')
  title.id = 'bottom-title'
  title.textContent = titleText
  const meaning = document.createElement('p')
  meaning.id = 'reader-meaning'
  meaning.className = 'reader-meaning'
  meaning.textContent = meaningText
  return { header, title, meaning }
}

function todayFixtureItems() {
  const whyKey = (predicate) => ({
    MANUFACTURES: 'today.why.manufactures',
    SERVES_MARKET: 'today.why.servesMarket',
    MAINTAINS_STANDARD: 'today.why.maintainsStandard',
  })[predicate] ?? 'today.why.default'

  return [...state.projection.nodes]
    .map((source) => {
      const fact = describeFactForView(source)
      const observed = source.observedAt ? new Date(source.observedAt) : null
      return {
        source,
        fact,
        key: projectionKey('FAXT', source.id),
        observedSort: observed && !Number.isNaN(observed.valueOf()) ? observed.valueOf() : Number.NEGATIVE_INFINITY,
        why: presentation.text(whyKey(source.predicate)),
      }
    })
    .sort((first, second) => second.observedSort - first.observedSort || first.source.id.localeCompare(second.source.id))
    .slice(0, 3)
}

function openTodayEvidence(key) {
  navigate(key, { recenter: false })
  state.depth = 3
  renderDepth()
  $('#depth-slider').focus({ preventScroll: true })
}

function renderReader(node) {
  const target = $('#reader')
  target.replaceChildren()
  const isOrganization = node.kind === 'ORGANIZATION'

  if (isOrganization) {
    const rootView = document.createElement('div')
    rootView.className = 'today'
    const readerHeader = makeReaderHeader(
      presentation.text('copy.today'),
      presentation.text('today.heading'),
      presentation.text('today.subheading'),
      node.kind,
    )
    const head = document.createElement('header')
    head.className = 'today-top'
    const greeting = document.createElement('div')
    greeting.className = 'today-greet'
    const name = document.createElement('span')
    name.className = 'co'
    name.textContent = presentation.text('copy.today')
    const title = readerHeader.title
    const summary = document.createElement('p')
    summary.className = 'turn'
    summary.textContent = node.label
    greeting.append(name, title, summary)

    const context = document.createElement('div')
    context.className = 'today-cont'
    const contextLabel = document.createElement('span')
    contextLabel.className = 'mono'
    const contextName = state.projection.context.label
    contextLabel.textContent = `${presentation.text('context.label')} · ${presentation.isImplementationValue(contextName)
      ? presentation.text('context.current')
      : contextName || presentation.text('context.current')}`
    const explanation = document.createElement('p')
    explanation.textContent = presentation.text('today.subheading')
    context.append(contextLabel, explanation)
    head.append(greeting, context)
    rootView.append(head)

    const todayItems = todayFixtureItems()
    if (todayItems.length) {
      const cards = document.createElement('div')
      cards.className = 'today-ideas'
      for (const item of todayItems) {
        const card = document.createElement('article')
        card.className = 'idea today-item'

        const eyebrow = document.createElement('div')
        eyebrow.className = 'today-item-eyebrow'
        eyebrow.textContent = presentation.text('today.currentObservation')

        const title = document.createElement('h3')
        title.textContent = item.fact.label

        const whyLabel = document.createElement('span')
        whyLabel.className = 'today-why-label'
        whyLabel.textContent = presentation.text('today.why')

        const why = document.createElement('p')
        why.className = 'stmt'
        why.textContent = item.why

        const meta = document.createElement('div')
        meta.className = 'today-meta'
        const stateLabel = document.createElement('span')
        stateLabel.className = 'state-word'
        stateLabel.textContent = item.fact.epistemicLabel ?? ''
        const dateLabel = document.createElement('span')
        dateLabel.textContent = item.fact.observedAt ?? item.fact.currentnessLabel ?? ''
        if (item.fact.epistemicLabel) meta.append(stateLabel)
        if (dateLabel.textContent) meta.append(dateLabel)

        const actions = document.createElement('div')
        actions.className = 'today-actions'
        const evidence = document.createElement('button')
        evidence.className = 'today-primary'
        evidence.type = 'button'
        evidence.textContent = presentation.text('today.showHow')
        evidence.addEventListener('click', () => openTodayEvidence(item.key))

        const open = document.createElement('button')
        open.className = 'today-secondary'
        open.type = 'button'
        open.append(presentation.text('today.openMap'), axignalIcon('arrow-right'))
        open.addEventListener('click', () => navigate(item.key, { recenter: false }))

        actions.append(evidence, open)
        card.append(eyebrow, title, whyLabel, why, meta, actions)
        cards.append(card)
      }
      rootView.append(cards)
    } else {
      const empty = document.createElement('p')
      empty.className = 'today-empty'
      empty.textContent = state.projection.nodes.length
        ? presentation.text('today.partial')
        : presentation.text('today.empty')
      rootView.append(empty)
    }
    target.append(rootView)
    return
  }

  const focusView = document.createElement('div')
  focusView.className = 'focusview'
  const fact = describeFactForView(node.source)
  const readerHeader = makeReaderHeader(
    presentation.text('context.current'),
    fact.label,
    presentation.text('copy.factMeaning'),
    node.kind,
  )
  const kicker = document.createElement('span')
  kicker.className = 'kicker'
  kicker.textContent = presentation.text('field.information')
  const columns = document.createElement('div')
  columns.className = 'fv-cols'
  const direct = document.createElement('div')
  direct.className = 'reader-fields'
  direct.id = 'bottom-fields'
  direct.append(...[
    setReaderField(presentation.text('field.detail'), fact.valueLabel),
    setReaderField(presentation.text('field.knowledge'), fact.epistemicLabel),
    setReaderField(presentation.text('field.currentness'), fact.currentnessLabel),
    setReaderField(presentation.text('field.lastObserved'), presentation.formatDate(node.source.observedAt)),
  ].filter(Boolean))
  columns.append(direct)
  focusView.append(readerHeader.header, kicker, readerHeader.title, readerHeader.meaning, columns)
  target.append(focusView)
}

function renderHistory() {
  const list = $('#history-list')
  list.replaceChildren()
  const visible = state.history.slice(0, state.historyIndex + 1)
  const displayedIndexes = visible.length > 3
    ? [0, visible.length - 1]
    : visible.map((_key, index) => index)
  const hiddenCount = visible.length - displayedIndexes.length
  $('.trail').classList.toggle('is-compacted', hiddenCount > 0)
  displayedIndexes.forEach((index, displayIndex) => {
    const key = visible[index]
    if (displayIndex > 0) {
      const separator = document.createElement('span')
      separator.className = 'trail-sep'
      separator.textContent = '/'
      separator.setAttribute('aria-hidden', 'true')
      list.append(separator)
    }
    if (displayIndex === 1 && hiddenCount > 0) {
      const hidden = document.createElement('span')
      const hiddenLabels = visible.slice(1, -1).map((hiddenKey) => getNode(hiddenKey)?.label)
      hidden.className = 'trail-more'
      hidden.textContent = `+${new Intl.NumberFormat(presentation.locale).format(hiddenCount)}`
      hidden.title = hiddenLabels.filter(Boolean).join(' / ')
      hidden.setAttribute('role', 'note')
      hidden.setAttribute('aria-label', presentation.text('navigation.hiddenStops', { count: hiddenCount }))
      list.append(hidden)
      const separator = document.createElement('span')
      separator.className = 'trail-sep'
      separator.textContent = '/'
      separator.setAttribute('aria-hidden', 'true')
      list.append(separator)
    }
    const node = getNode(key)
    const item = document.createElement('button')
    item.className = `trail-item${index === state.historyIndex ? ' cur' : ''}`
    item.textContent = index === 0 ? presentation.text('copy.today') : node?.label ?? presentation.text('context.current')
    item.title = item.textContent
    item.setAttribute('aria-current', String(index === state.historyIndex))
    item.addEventListener('click', () => {
      state.historyIndex = index
      navigate(key, { record: false })
    })
    list.append(item)
  })
  $('#history-back').disabled = state.historyIndex <= 0
  $('#history-forward').disabled = state.historyIndex >= state.history.length - 1
}

function renderDepth() {
  const percent = (state.depth / 3) * 100
  $('#depth-fill').style.height = `${percent}%`
  $('#depth-knob').style.top = `${percent}%`
  $('#depth-slider').setAttribute('aria-valuenow', state.depth.toFixed(2))
  $('#depth-word').textContent = depthName(state.depth)
  for (const stop of document.querySelectorAll('[data-depth]')) {
    stop.classList.toggle('on', state.depth >= Number(stop.dataset.depth) - 0.001)
  }
  $('#research-depth .gv-rv').firstChild.textContent = depthName(state.depth)
}

function render() {
  if (!state.projection) return
  const node = focusedNode()
  renderMap()
  renderReader(node)
  renderConnections(node)
  renderBottomTabVisibility()
  renderHistory()
  $('#here-label').textContent = getNode(organizationKey()).label
  $('#axent-moves-focus').textContent = node.kind === 'ORGANIZATION'
    ? presentation.text('organization.label')
    : node.label
  $('#axent-pill-label').textContent = node.label
  const pill = $('#axent-active-context')
  pill.dataset.activeXeedId = state.projection.context.id
  pill.dataset.activeKind = node.kind
  pill.dataset.activeCanonicalId = node.id
  const activeState = state.uxLab?.presentationOverrides?.epistemicState?.[node.id]
    ?? node.source?.epistemicState
  pill.className = `ax-pill ${node.kind === 'FAXT' ? activeState : 'UNKNOWN'}`
  const contextLabel = state.projection.context.label
  const displayContext = presentation.isImplementationValue(contextLabel)
    ? presentation.text('context.current')
    : contextLabel || presentation.text('context.current')
  $('#axent-xeed-label').textContent = displayContext
  $('#xeed-label').textContent = displayContext
  for (const move of document.querySelectorAll('#axent-moves .ax-move')) {
    move.dataset.activeXeedId = state.projection.context.id
    move.dataset.activeKind = node.kind
    move.dataset.activeCanonicalId = node.id
  }
  renderAxentTranscript(node)
  const activeViewName = presentation.text('context.activeAccessibleName', { name: displayContext })
  $('#xeed-current').setAttribute('aria-label', activeViewName)
  $('#xeed-rail').setAttribute('aria-label', activeViewName)
  $('#xeed-rail').title = activeViewName
  const onToday = node.kind === 'ORGANIZATION'
  $('.bottom').classList.toggle('today-open', onToday && !state.bottomTabCollapsed)
  $('#today').setAttribute('aria-current', String(onToday))
  $('#today-rail').setAttribute('aria-current', String(onToday))
  renderDepth()
}

function fitCamera() {
  const nodes = state.worldNodes
  if (!nodes.length) return
  const xs = nodes.map((node) => node.x)
  const ys = nodes.map((node) => node.y)
  const minX = Math.min(...xs) - 7
  const maxX = Math.max(...xs) + 7
  const minY = Math.min(...ys) - 8
  const maxY = Math.max(...ys) + 8
  const boundsWidth = ((maxX - minX) / 100) * state.size.width
  const boundsHeight = ((maxY - minY) / 100) * state.size.height
  const zoom = Math.max(0.5, Math.min(2.8, Math.min(
    state.size.width / boundsWidth,
    state.size.height / boundsHeight,
  ) * 0.96))
  const midX = (minX + maxX) / 2
  const midY = (minY + maxY) / 2
  animateCamera({
    x: state.size.width / 2 - (midX / 100) * state.size.width * zoom,
    y: state.size.height / 2 - (midY / 100) * state.size.height * zoom,
    zoom,
  })
}

function resetFieldView() {
  const organization = organizationKey()
  state.focus = organization
  state.history = [organization]
  state.historyIndex = 0
  state.depth = 0
  render()
  fitCamera()
}

function changeZoom(nextZoom, point = { x: state.size.width / 2, y: state.size.height / 2 }) {
  const zoom = Math.max(0.5, Math.min(2.8, nextZoom))
  const worldX = (point.x - state.camera.x) / state.camera.zoom
  const worldY = (point.y - state.camera.y) / state.camera.zoom
  state.camera = {
    x: point.x - worldX * zoom,
    y: point.y - worldY * zoom,
    zoom,
  }
  updateCamera()
}

function screenPoint(event) {
  const rect = field.getBoundingClientRect()
  return { x: event.clientX - rect.left, y: event.clientY - rect.top }
}

function setSidebarCollapsed(collapsed) {
  const sidebar = $('.gov')
  const toggle = $('#sidebar-toggle')
  const compactViewport = window.matchMedia('(max-width: 900px)').matches
  sidebar.classList.toggle('collapsed', collapsed)
  app.classList.toggle('gov-off', collapsed && !compactViewport)
  toggle.setAttribute('aria-expanded', String(!collapsed))
  const label = presentation.text(collapsed ? 'navigation.expandSidebar' : 'navigation.collapseSidebar')
  toggle.setAttribute('aria-label', label)
  toggle.title = label
  toggle.querySelector('use').setAttribute('href', `${LUCIDE_SPRITE}${collapsed ? 'panel-left-open' : 'panel-left-close'}`)
  requestAnimationFrame(() => {
    state.size = { width: field.clientWidth, height: field.clientHeight }
    renderMap()
  })
}

function setXeedMenuOpen(open, focusSearch = false) {
  if (!state.uxLab) return
  const selector = $('#xeed-current')
  const menu = $('#lab-contexts')
  menu.hidden = !open
  selector.setAttribute('aria-expanded', String(open))
  if (open && focusSearch) $('#lab-context-search').focus()
  if (!open && document.activeElement === $('#lab-context-search')) selector.focus()
}

function bindInteractions() {
  const sidebarBreakpoint = window.matchMedia('(max-width: 900px)')
  setSidebarCollapsed(sidebarBreakpoint.matches)
  sidebarBreakpoint.addEventListener('change', (event) => setSidebarCollapsed(event.matches))
  $('#preferences-open').addEventListener('click', () => setBottomView('preferences'))
  $('#preferences-close').addEventListener('click', () => setBottomView('reader', true))
  $('#preferences-view').addEventListener('keydown', (event) => {
    if (event.key === 'Escape') setBottomView('reader', true)
  })
  $('#ui-locale').addEventListener('change', (event) => {
    if (!state.uxLab) return
    if (event.currentTarget.value === 'auto') {
      try {
        window.localStorage.removeItem(LOCALE_PREFERENCE_KEY)
      } catch {
        // Browser selection still applies for this page load.
      }
      explicitUserLocale = null
      applyUiLocale(
        window.AXIGNAL_PRESENTATION.resolveLocale(null, browserLocalePreferences, 'en'),
        { selectionValue: 'auto' },
      )
      return
    }
    applyUiLocale(event.currentTarget.value, { persist: true })
  })
  $('#sidebar-toggle').addEventListener('click', (event) => {
    setSidebarCollapsed(!$('.gov').classList.contains('collapsed'))
  })
  $('.gv-logo').addEventListener('click', (event) => {
    event.preventDefault()
    const todayUrl = new URL('#today', window.location.href)
    if (todayUrl.href === window.location.href) {
      window.location.reload()
      return
    }
    window.location.assign(todayUrl.href)
  })
  $('#today').addEventListener('click', (event) => {
    event.preventDefault()
    navigate(organizationKey())
  })
  $('#today-rail').addEventListener('click', () => navigate(organizationKey()))
  $('#governance-rail').addEventListener('click', () => {
    setSidebarCollapsed(false)
    const advanced = $('#governance-section')
    advanced.open = true
    advanced.querySelector('summary').focus()
  })
  const xeedSelector = $('#xeed-current')
  xeedSelector.addEventListener('click', () => {
    setXeedMenuOpen(xeedSelector.getAttribute('aria-expanded') !== 'true', true)
  })
  xeedSelector.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowDown' && state.uxLab) {
      event.preventDefault()
      setXeedMenuOpen(true, true)
    }
  })
  $('#lab-context-search').addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      event.preventDefault()
      setXeedMenuOpen(false)
    }
  })
  document.addEventListener('pointerdown', (event) => {
    if (!event.target.closest?.('#xeed-current, #lab-contexts')) setXeedMenuOpen(false)
  })
  $('#research-depth').addEventListener('click', () => $('#depth-slider').focus())
  $('#history-back').addEventListener('click', () => {
    if (state.historyIndex > 0) {
      state.historyIndex -= 1
      navigate(state.history[state.historyIndex], { record: false })
    }
  })
  $('#history-forward').addEventListener('click', () => {
    if (state.historyIndex < state.history.length - 1) {
      state.historyIndex += 1
      navigate(state.history[state.historyIndex], { record: false })
    }
  })
  $('#history-home').addEventListener('click', () => navigate(organizationKey()))
  for (const stop of document.querySelectorAll('[data-depth]')) {
    stop.addEventListener('click', () => { state.depth = Number(stop.dataset.depth); renderDepth() })
  }

  const slider = $('#depth-slider')
  const depthLens = $('.lens')
  depthLens.addEventListener('focusin', () => depthLens.classList.add('is-expanded'))
  depthLens.addEventListener('focusout', (event) => {
    if (!depthLens.contains(event.relatedTarget)) depthLens.classList.remove('is-expanded')
  })
  const setDepthFromPointer = (clientY) => {
    const rect = slider.getBoundingClientRect()
    state.depth = Math.max(0, Math.min(1, (clientY - rect.top) / rect.height)) * 3
    renderDepth()
  }
  slider.addEventListener('pointerdown', (event) => {
    slider.setPointerCapture(event.pointerId)
    setDepthFromPointer(event.clientY)
  })
  slider.addEventListener('pointermove', (event) => {
    if (slider.hasPointerCapture(event.pointerId)) setDepthFromPointer(event.clientY)
  })
  slider.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowUp' || event.key === 'ArrowRight') state.depth = Math.min(3, state.depth + 0.5)
    else if (event.key === 'ArrowDown' || event.key === 'ArrowLeft') state.depth = Math.max(0, state.depth - 0.5)
    else if (event.key === 'Home') state.depth = 0
    else if (event.key === 'End') state.depth = 3
    else return
    event.preventDefault()
    renderDepth()
  })

  $('#zoom-in').addEventListener('click', () => changeZoom(state.camera.zoom * 1.3))
  $('#zoom-out').addEventListener('click', () => changeZoom(state.camera.zoom / 1.3))
  $('#zoom-fit').addEventListener('click', fitCamera)
  $('#zoom-root').addEventListener('click', () => focusCamera(organizationKey()))
  $('#field-reload').addEventListener('click', resetFieldView)
  $('#labels-toggle').addEventListener('click', () => {
    state.bottomTabCollapsed = !state.bottomTabCollapsed
    renderBottomTabVisibility()
  })
  $('#here').addEventListener('click', () => focusCamera(organizationKey()))

  field.addEventListener('pointerdown', (event) => {
    if (event.target.closest?.('.anch, .canvas-tools, .here, .minimap, .trail, .lens-stop')) return
    state.pointer = { id: event.pointerId, last: screenPoint(event) }
    field.setPointerCapture(event.pointerId)
    field.classList.add('panning')
  })
  field.addEventListener('pointermove', (event) => {
    if (!state.pointer || state.pointer.id !== event.pointerId) return
    const next = screenPoint(event)
    state.camera.x += next.x - state.pointer.last.x
    state.camera.y += next.y - state.pointer.last.y
    state.pointer.last = next
    updateCamera()
  })
  const stopPan = () => { state.pointer = null; field.classList.remove('panning') }
  field.addEventListener('pointerup', stopPan)
  field.addEventListener('pointercancel', stopPan)
  field.addEventListener('wheel', (event) => {
    event.preventDefault()
    changeZoom(state.camera.zoom * Math.exp(-event.deltaY * 0.0016), screenPoint(event))
  }, { passive: false })

  const moveMinimap = (event) => {
    const rect = $('#minimap svg').getBoundingClientRect()
    const bounds = minimapBounds()
    const px = Math.max(
      MINIMAP.inset,
      Math.min(MINIMAP.width - MINIMAP.inset, ((event.clientX - rect.left) / rect.width) * MINIMAP.width),
    )
    const py = Math.max(
      MINIMAP.inset,
      Math.min(MINIMAP.height - MINIMAP.inset, ((event.clientY - rect.top) / rect.height) * MINIMAP.height),
    )
    const x = bounds.x0 + ((px - MINIMAP.inset) / (MINIMAP.width - 2 * MINIMAP.inset)) * (bounds.x1 - bounds.x0)
    const y = bounds.y0 + ((py - MINIMAP.inset) / (MINIMAP.height - 2 * MINIMAP.inset)) * (bounds.y1 - bounds.y0)
    state.camera.x = state.size.width / 2 - (x / 100) * state.size.width * state.camera.zoom
    state.camera.y = state.size.height / 2 - (y / 100) * state.size.height * state.camera.zoom
    updateCamera()
  }
  const minimap = $('#minimap')
  let minimapPointer = null
  let suppressMinimapClick = false
  minimap.addEventListener('pointerdown', (event) => {
    if (event.button !== 0) return
    minimapPointer = { id: event.pointerId, x: event.clientX, y: event.clientY, moved: false }
    minimap.setPointerCapture(event.pointerId)
    event.preventDefault()
    moveMinimap(event)
  })
  minimap.addEventListener('pointermove', (event) => {
    if (!minimapPointer || minimapPointer.id !== event.pointerId) return
    if (Math.hypot(event.clientX - minimapPointer.x, event.clientY - minimapPointer.y) > 3) {
      minimapPointer.moved = true
    }
    moveMinimap(event)
  })
  const finishMinimapPointer = (event) => {
    if (!minimapPointer || minimapPointer.id !== event.pointerId) return
    suppressMinimapClick = minimapPointer.moved
    minimapPointer = null
  }
  minimap.addEventListener('pointerup', finishMinimapPointer)
  minimap.addEventListener('pointercancel', finishMinimapPointer)
  minimap.addEventListener('click', (event) => {
    if (suppressMinimapClick) {
      suppressMinimapClick = false
      return
    }
    if (event.detail === 0) return
    moveMinimap(event)
  })
  $('#minimap').addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      const rect = $('#minimap').getBoundingClientRect()
      moveMinimap({ clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2 })
    }
  })
  $('#axent-composer').addEventListener('submit', (event) => {
    event.preventDefault()
    if (!state.uxLab?.composerEnabled) return
    const input = $('#axent-input')
    const value = input.value.trim()
    if (!value) return
    appendFixtureMessage('you', value)
    appendFixtureMessage('axent', state.uxLab.fixtureReply)
    input.value = ''
  })
  window.addEventListener('resize', () => {
    if (!state.projection) return
    state.size = { width: field.clientWidth, height: field.clientHeight }
    renderMap()
  })
}

function displayProjection(projection) {
  state.projection = projection
  state.uxLab = projection.uxLab ?? null
  const organization = organizationKey()
  const initialHistory = state.uxLab?.initialHistory ?? [projection.organization.id]
  state.history = initialHistory.map((id) => projection.nodes.some((node) => node.id === id)
    ? projectionKey('FAXT', id)
    : organization)
  state.historyIndex = state.history.length - 1
  const requestedFocus = state.uxLab?.initialFocus
  state.focus = requestedFocus && projection.nodes.some((node) => node.id === requestedFocus)
    ? projectionKey('FAXT', requestedFocus)
    : organization
  if (state.uxLab) configureUxLab()
  app.dataset.state = 'ready'
  render()
  fitCamera()
}

function axentScopeForNode(node = focusedNode()) {
  return Object.freeze({
    xeedId: state.projection.context.id,
    objectId: node.id,
    objectKind: node.kind,
    label: node.label,
  })
}

function axentScopeKey(scope) {
  return `${scope.xeedId}|${scope.objectKind}|${scope.objectId}`
}

function keyForAxentScope(scope) {
  if (!scope || scope.xeedId !== state.projection.context.id) return null
  if (scope.objectKind === 'ORGANIZATION' && scope.objectId === state.projection.organization.id) {
    return organizationKey()
  }
  if (scope.objectKind === 'FAXT' && state.projection.nodes.some((node) => node.id === scope.objectId)) {
    return projectionKey('FAXT', scope.objectId)
  }
  return null
}

function appendFixtureMessageElement(container, message) {
  const element = document.createElement('div')
  element.className = `ax-msg ${message.role === 'axent' ? 'is-axent' : 'is-you'}`
  element.dataset.syntheticFixture = 'true'
  element.dataset.scopeXeedId = message.scope.xeedId
  element.dataset.scopeKind = message.scope.objectKind
  element.dataset.scopeCanonicalId = message.scope.objectId
  element.dataset.occurredAt = message.occurredAt
  const roleLabel = document.createElement('span')
  roleLabel.className = 'role'
  const role = message.role === 'you'
    ? presentation.text('fixture.youRole')
    : presentation.text('fixture.axentRole')
  const when = presentation.formatDate(message.occurredAt)
  roleLabel.textContent = when ? `${role} · ${when}` : role
  const text = document.createElement('p')
  text.textContent = message.text
  text.dir = 'auto'
  element.append(roleLabel, text)
  container.append(element)
}

function renderAxentTranscript(node = focusedNode()) {
  const log = $('#axent-transcript')
  log.replaceChildren()
  const currentScope = axentScopeForNode(node)
  const currentKey = axentScopeKey(currentScope)
  const current = state.axentMessages.filter((message) => axentScopeKey(message.scope) === currentKey)
  const previous = state.axentMessages.filter((message) => axentScopeKey(message.scope) !== currentKey)

  const currentHeading = document.createElement('div')
  currentHeading.className = 'ax-thread-heading'
  currentHeading.textContent = presentation.text('navigation.currentInvestigation', { label: node.label })
  log.append(currentHeading)

  if (current.length) {
    for (const message of current) appendFixtureMessageElement(log, message)
  } else {
    const empty = document.createElement('p')
    empty.className = 'ax-thread-empty'
    empty.textContent = presentation.text('navigation.noConversationForFocus')
    log.append(empty)
  }

  if (previous.length) {
    const separator = document.createElement('div')
    separator.className = 'ax-continuity-label'
    separator.textContent = presentation.text('navigation.previousInvestigations')
    log.append(separator)

    const groups = new Map()
    for (const message of previous) {
      const key = axentScopeKey(message.scope)
      if (!groups.has(key)) groups.set(key, [])
      groups.get(key).push(message)
    }

    for (const messages of groups.values()) {
      const scope = messages[0].scope
      const section = document.createElement('section')
      section.className = 'ax-continuity'
      section.dataset.scopeXeedId = scope.xeedId
      section.dataset.scopeKind = scope.objectKind
      section.dataset.scopeCanonicalId = scope.objectId

      const head = document.createElement('div')
      head.className = 'ax-continuity-head'
      const meta = document.createElement('span')
      const last = messages.at(-1)
      const when = presentation.formatDate(last.occurredAt)
      meta.textContent = `${scope.label}${when ? ` · ${when}` : ''}`
      const resume = document.createElement('button')
      resume.type = 'button'
      resume.className = 'ax-continuity-resume'
      resume.textContent = presentation.text('navigation.resumeInvestigation')
      const target = keyForAxentScope(scope)
      resume.disabled = !target
      resume.addEventListener('click', () => {
        if (target) navigate(target, { recenter: false })
      })
      head.append(meta, resume)
      section.append(head)
      for (const message of messages) appendFixtureMessageElement(section, message)
      log.append(section)
    }
  }

  log.scrollTop = 0
}

function appendFixtureMessage(role, content) {
  if (!state.projection || !state.uxLab) return
  state.axentMessages.push({
    role,
    text: content,
    syntheticFixture: true,
    scope: axentScopeForNode(),
    occurredAt: new Date().toISOString(),
  })
  renderAxentTranscript()
}

function configureUxLab() {
  const lab = state.uxLab
  const labAccount = $('#lab-account')
  labAccount.hidden = false
  $('#preferences-open').hidden = false
  $('#lab-account-label').textContent = lab.accountLabelKey
    ? presentation.text(lab.accountLabelKey)
    : lab.accountLabel ?? presentation.text('fixture.accountUnavailable')
  $('#ui-locale').value = explicitUserLocale ?? 'auto'

  const contexts = $('#lab-contexts')
  const list = $('#lab-context-list')
  contexts.hidden = true
  $('#xeed-current').disabled = false
  const search = $('#lab-context-search')
  search.hidden = !lab.contextSearch
  const emptyState = $('#lab-context-empty')
  list.replaceChildren()
  for (const [index, context] of lab.contexts.entries()) {
    const label = context.label
    const button = document.createElement('button')
    button.type = 'button'
    button.className = 'lab-context'
    button.setAttribute('role', 'option')
    button.setAttribute('aria-selected', String(index === 0))
    button.disabled = index !== 0
    button.textContent = label
    button.title = label
    button.addEventListener('click', () => {
      // Only the context already represented by the authorized projection is
      // selectable. Other fixture labels do not grant Xeed read authority.
      setXeedMenuOpen(false)
    })
    list.append(button)
  }
  search.addEventListener('input', () => {
    const query = search.value.toLocaleLowerCase(presentation.locale)
    let visibleCount = 0
    for (const button of list.querySelectorAll('.lab-context')) {
      button.hidden = !button.textContent.toLocaleLowerCase(presentation.locale).includes(query)
      if (!button.hidden) visibleCount += 1
    }
    emptyState.hidden = visibleCount > 0
  })

  const research = $('#research-depth')
  const governanceAvailable = Boolean(lab.governanceAvailable)
  research.disabled = !governanceAvailable
  research.classList.toggle('is-unavailable', !governanceAvailable)
  research.dataset.capability = governanceAvailable ? 'AVAILABLE' : 'UNAVAILABLE'
  const account = document.querySelector('.gv-account span:last-child')
  if (account && lab.accountLabel) account.textContent = lab.accountLabel

  const track = $('#mer-track')
  for (const tick of track.querySelectorAll('.lab-timeline-tick')) tick.remove()
  for (const [index, item] of lab.timeline.entries()) {
    const tick = document.createElement('span')
    tick.className = `lab-timeline-tick tick-${index + 1}`
    tick.title = item.label
    tick.setAttribute('aria-hidden', 'true')
    track.append(tick)
  }

  const moves = $('#axent-moves')
  const heading = moves.querySelector('.mono')
  moves.replaceChildren(heading)
  const availableMoves = lab.moves.filter((move) => move.available)
  const primaryMoves = availableMoves.slice(0, 2)
  const secondaryMoves = availableMoves.slice(2)
  const createMoveButton = (move) => {
    const button = document.createElement('button')
    button.type = 'button'
    button.className = 'ax-move'
    button.textContent = move.copyKey ? presentation.text(move.copyKey) : move.label
    button.dataset.capability = 'SYNTHETIC_FIXTURE'
    button.addEventListener('click', () => {
      appendFixtureMessage('you', move.label)
      appendFixtureMessage('axent', lab.fixtureReply)
    })
    return button
  }
  for (const move of primaryMoves) moves.append(createMoveButton(move))
  if (secondaryMoves.length) {
    const more = document.createElement('details')
    more.className = 'ax-more-moves'
    const summary = document.createElement('summary')
    summary.textContent = presentation.text('navigation.moreQuestions')
    more.append(summary)
    const body = document.createElement('div')
    body.className = 'ax-more-moves-body'
    for (const move of secondaryMoves) body.append(createMoveButton(move))
    more.append(body)
    moves.append(more)
  }
  state.axentMessages = lab.messages.map((message) => ({
    ...message,
    scope: Object.freeze({ ...message.scope }),
  }))
  renderAxentTranscript()
  const input = $('#axent-input')
  const submit = $('#axent-ask')
  input.disabled = !lab.composerEnabled
  submit.disabled = !lab.composerEnabled
  input.placeholder = lab.composerPlaceholderKey
    ? presentation.text(lab.composerPlaceholderKey)
    : lab.composerPlaceholder || presentation.text('navigation.askPlaceholder')
  $('#axent-composer').dataset.syntheticFixture = 'true'
  $('.ax-hint').textContent = lab.composerEnabled
    ? presentation.text('fixture.interactionHint')
    : ''
}

async function start() {
  bindInteractions()
  const scenario = new URLSearchParams(window.location.search).get('scenario')
  const demoState = new URLSearchParams(window.location.search).get('demo')
  const endpoint = scenario
    ? `/api/subscriber-context?scenario=${encodeURIComponent(scenario)}`
    : demoState === 'empty'
      ? '/api/demo/empty'
      : demoState === 'unavailable'
        ? '/api/demo/unavailable'
        : '/api/subscriber-context'
  try {
    if (scenario && window.location.hostname !== '127.0.0.1') throw new Error('lab requires loopback')
    const response = await fetch(endpoint, { credentials: 'same-origin', cache: 'no-store' })
    if (!response.ok) throw new Error('unavailable')
    const projection = await response.json()
    if (projection.uxLab && (
      window.location.hostname !== '127.0.0.1'
      || projection.realityLevel !== 'SYNTHETIC_PRESENTATION_LAB'
    )) throw new Error('synthetic fixture outside local lab')
    displayProjection(projection)
  } catch {
    app.dataset.state = 'unavailable'
    const message = document.createElement('p')
    message.className = 'field-unavailable'
    message.setAttribute('role', 'status')
    message.textContent = presentation.text('error.load')
    field.append(message)
    $('#bottom-title').textContent = presentation.text('error.load')
    $('#selected-kind').textContent = presentation.text('context.label')
    $('#bottom-fields').replaceChildren()
  }
}

start()
