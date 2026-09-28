const $ = (selector) => document.querySelector(selector)
const SVG = 'http://www.w3.org/2000/svg'
const FIELD_CENTER = { x: 500, y: 298 }

const state = {
  projection: null,
  focus: null,
  history: [],
  historyIndex: -1,
  depth: 'GLANCE',
  camera: { x: 0, y: 0, zoom: 1 },
  pointer: null,
  noticeTimer: 0,
  cameraFrame: 0,
}

const field = $('#field')
const cameraLayer = $('#camera-layer')
const minimapNodes = $('#minimap-nodes')
const minimapWindow = $('#minimap-window')

function svg(tag, attributes = {}, text = '') {
  const element = document.createElementNS(SVG, tag)
  for (const [name, value] of Object.entries(attributes)) element.setAttribute(name, String(value))
  if (text) element.textContent = text
  return element
}

function text(element, value) {
  element.textContent = value == null ? '' : String(value)
}

function displayList(target, values) {
  target.replaceChildren()
  if (!values.length) {
    const item = document.createElement('li')
    item.className = 'unavailable'
    item.textContent = 'Unavailable in this context'
    target.append(item)
    return
  }
  for (const value of values) {
    const item = document.createElement('li')
    item.textContent = value
    target.append(item)
  }
}

function projectionKey(kind, id) {
  return `${kind}:${id}`
}

function organizationKey() {
  return projectionKey('ORGANIZATION', state.projection.organization.id)
}

function nodePosition(index, count) {
  const angle = -Math.PI / 4 + (Math.PI * 2 * index) / Math.max(count, 1)
  const radius = count === 1 ? 226 : Math.min(244, 172 + count * 9)
  return {
    x: FIELD_CENTER.x + Math.cos(angle) * radius,
    y: FIELD_CENTER.y + Math.sin(angle) * radius * 0.72,
  }
}

function getNode(id) {
  if (!state.projection) return null
  if (id === organizationKey()) {
    return {
      key: id,
      id: state.projection.organization.id,
      kind: 'ORGANIZATION',
      label: state.projection.organization.name,
      epistemicState: null,
      currentness: null,
      observedAt: null,
    }
  }
  const node = state.projection.nodes.find((item) => projectionKey('FAXT', item.id) === id)
  return node ? { ...node, key: id } : null
}

function updateCamera() {
  const { x, y, zoom } = state.camera
  cameraLayer.setAttribute('transform', `translate(${x} ${y}) scale(${zoom})`)
  const width = 152 / zoom
  const height = 88 / zoom
  const left = Math.max(4, Math.min(156 - width, 4 + (-x / zoom / 1000) * 152))
  const top = Math.max(4, Math.min(92 - height, 4 + (-y / zoom / 600) * 88))
  minimapWindow.setAttribute('x', String(left + 4))
  minimapWindow.setAttribute('y', String(top + 4))
  minimapWindow.setAttribute('width', String(width))
  minimapWindow.setAttribute('height', String(height))
}

function drawMap() {
  const projection = state.projection
  if (!projection) return
  const nodes = projection.nodes
  cameraLayer.replaceChildren()
  minimapNodes.replaceChildren()

  const contextBoundary = svg('g', { 'aria-label': 'Presentation boundary for this authorized Xeed context' })
  const root = { ...FIELD_CENTER }
  if (nodes.length) {
    contextBoundary.append(svg('circle', {
      class: 'context-boundary',
      cx: root.x,
      cy: root.y,
      r: 235,
      'aria-hidden': 'true',
    }))
  }

  const positions = new Map()
  nodes.forEach((node, index) => positions.set(node.id, nodePosition(index, nodes.length)))
  cameraLayer.append(contextBoundary)

  const rootNode = svg('g', {
    class: `node organization${state.focus === organizationKey() ? ' selected' : ''}`,
    transform: `translate(${root.x} ${root.y})`,
    role: 'button',
    tabindex: '0',
    'data-id': projection.organization.id,
    'data-key': organizationKey(),
    'aria-label': `Global Organization: ${projection.organization.name}`,
    'aria-pressed': state.focus === organizationKey() ? 'true' : 'false',
  })
  rootNode.append(svg('circle', { r: 29 }))
  rootNode.append(svg('text', { class: 'node-marker', x: 0, y: 3, 'text-anchor': 'middle' }, 'ORG'))
  if (state.focus === organizationKey()) {
    rootNode.append(svg('text', { class: 'node-label', x: 0, y: 52, 'text-anchor': 'middle' }, projection.organization.name))
    rootNode.append(svg('text', { class: 'node-meta', x: 0, y: 68, 'text-anchor': 'middle' }, 'GLOBAL · CANONICAL'))
  }
  bindNode(rootNode, organizationKey())
  cameraLayer.append(rootNode)

  nodes.forEach((node, index) => {
    const point = positions.get(node.id)
    const nodeKey = projectionKey('FAXT', node.id)
    const isFocused = state.focus === nodeKey
    const group = svg('g', {
      class: `node${isFocused ? ' selected' : ''}`,
      transform: `translate(${point.x} ${point.y})`,
      role: 'button',
      tabindex: '0',
      'data-id': node.id,
      'data-key': projectionKey('FAXT', node.id),
      'aria-pressed': isFocused ? 'true' : 'false',
      'aria-label': `FAXT: ${node.label}. Explicitly referenced in this Xeed context. Subject kind unknown.`,
    })
    group.append(svg('circle', { r: 13 }))
    group.append(svg('text', { class: 'node-marker', x: 0, y: 3, 'text-anchor': 'middle' }, 'F'))
    if (isFocused || state.focus === organizationKey()) {
      const labelAnchor = point.x > FIELD_CENTER.x ? 'end' : 'start'
      const labelX = point.x > FIELD_CENTER.x ? -21 : 21
      const [predicate, ...valueParts] = node.label.split(' · ')
      group.append(svg('text', { class: 'node-label', x: labelX, y: -5, 'text-anchor': labelAnchor }, predicate))
      group.append(svg('text', { class: 'node-label node-value', x: labelX, y: 17, 'text-anchor': labelAnchor }, valueParts.join(' · ')))
      group.append(svg('text', { class: 'node-meta', x: labelX, y: 34, 'text-anchor': labelAnchor }, `${node.epistemicState} · ${node.currentness}`))
    }
    bindNode(group, nodeKey)
    cameraLayer.append(group)

    minimapNodes.append(
      svg('circle', { class: 'mini-node', cx: 80 + (point.x - root.x) * 0.12, cy: 48 + (point.y - root.y) * 0.12, r: 2.5 }),
    )
  })
  minimapNodes.append(svg('circle', { class: 'mini-node organization', cx: 80, cy: 48, r: 3.5 }))

  if (!nodes.length) {
    cameraLayer.append(
      svg('text', { class: 'empty-field', x: 500, y: 410, 'text-anchor': 'middle' },
        'No FAXT references are available in this authorized Xeed context.'),
    )
  }

  text($('#field-count'), `${nodes.length} explicit FAXT reference${nodes.length === 1 ? '' : 's'}`)
  updateCamera()
}

function bindNode(element, id) {
  element.addEventListener('pointerdown', (event) => event.stopPropagation())
  element.addEventListener('click', (event) => {
    event.stopPropagation()
    navigate(id)
  })
  element.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      navigate(id)
    }
  })
}

function pushHistory(id) {
  if (state.history[state.historyIndex] === id) return
  state.history = state.history.slice(0, state.historyIndex + 1)
  state.history.push(id)
  state.historyIndex = state.history.length - 1
}

function navigate(id, { record = true, recenter = true } = {}) {
  if (!getNode(id)) return
  if (record) pushHistory(id)
  state.focus = id
  if (recenter) {
    const node = id === organizationKey()
      ? FIELD_CENTER
      : nodePosition(state.projection.nodes.findIndex((item) => projectionKey('FAXT', item.id) === id), state.projection.nodes.length)
    animateCamera({
      x: 500 - node.x * 1.22,
      y: 300 - node.y * 1.22,
      zoom: 1.22,
    })
  }
  render()
}

function animateCamera(target) {
  window.cancelAnimationFrame(state.cameraFrame)
  const from = { ...state.camera }
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduceMotion) {
    state.camera = target
    updateCamera()
    return
  }
  const started = performance.now()
  const duration = 360
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

function setField(target, value, { unknown = false, state: epistemic = null } = {}) {
  const wrapper = document.createElement('div')
  wrapper.className = 'field-value'
  const term = document.createElement('dt')
  term.textContent = target
  const detail = document.createElement('dd')
  detail.textContent = value == null || value === '' ? 'Unavailable in this context' : String(value)
  if (unknown || value == null || value === '') detail.classList.add('unknown-value')
  if (epistemic) {
    detail.className = 'state-word'
    detail.dataset.state = epistemic
    detail.textContent = epistemic
  }
  wrapper.append(term, detail)
  return wrapper
}

function renderBottomContext(node) {
  const target = $('#bottom-fields')
  target.replaceChildren()
  const isOrganization = node.kind === 'ORGANIZATION'
  text($('#bottom-title'), isOrganization ? node.label : node.label)
  text($('#selected-kind'), isOrganization ? 'GLOBAL ORGANIZATION' : 'CANONICAL FAXT')

  if (isOrganization) {
    target.append(setField('Canonical identity', node.id))
    target.append(setField('Identity scope', 'Global AXIGLAND Organization'))
    target.append(setField('Capabilities', state.projection.organization.capabilities.join(' · ') || null))
    target.append(setField('Markets', state.projection.organization.markets.join(' · ') || null))
    target.append(setField('Relationships in this Xeed', null, { unknown: true }))
  } else {
    const fields = [
      setField('Canonical identity', node.id),
      setField('Predicate', node.predicate),
      setField('Object or value', node.objectOrValue),
      setField('Subject identifier · kind unknown', node.subjectId, { unknown: true }),
      setField('Epistemic state', node.epistemicState, { state: node.epistemicState }),
      setField('Currentness', node.currentness, { unknown: node.currentness === 'UNKNOWN' }),
      setField('Observed at · source timestamp', node.observedAt),
    ]
    target.append(...fields)
    const limitation = document.createElement('p')
    limitation.className = 'depth-limitation unavailable-detail'
    limitation.textContent = state.depth === 'PROVE'
      ? 'Evidence details are unavailable. An evidence reference is not authority to disclose or dereference Evidence.'
      : 'Subject kind and resolution remain unknown. Context membership is not an economic Relationship.'
    target.append(limitation)
  }

  if (state.depth === 'REASON') {
    const limitation = document.createElement('p')
    limitation.className = 'depth-limitation'
    limitation.textContent = 'Canonical derivation is unavailable in this context; no semantic Relationship or INXIGHT is inferred.'
    target.append(limitation)
  }
  if (state.depth === 'PROVE' && isOrganization) {
    const limitation = document.createElement('p')
    limitation.className = 'depth-limitation'
    limitation.textContent = 'Evidence and provenance are unavailable in this slice.'
    target.append(limitation)
  }
}

function renderHistory() {
  const list = $('#history-list')
  list.replaceChildren()
  const entries = state.history.slice(0, state.historyIndex + 1)
  entries.forEach((id, index) => {
    const node = getNode(id)
    const item = document.createElement('li')
    item.textContent = node?.label ?? (node?.kind === 'ORGANIZATION' ? state.projection.organization.name : 'Unavailable')
    if (index < entries.length - 1) item.className = 'history-past'
    list.append(item)
  })
  $('#history-back').disabled = state.historyIndex <= 0
  $('#history-forward').disabled = state.historyIndex >= state.history.length - 1
}

function render() {
  if (!state.projection) return
  const node = getNode(state.focus)
  if (!node) return
  drawMap()
  renderBottomContext(node)
  renderHistory()
  text($('#axent-selection'), node.label)
  text($('#axent-identity'), `${node.kind} · ${node.id}`)
  $('#axent-identity').dataset.activeXeedId = state.projection.context.id
  $('#axent-identity').dataset.activeCanonicalId = node.id
  for (const button of document.querySelectorAll('[data-depth]')) {
    button.setAttribute('aria-pressed', button.dataset.depth === state.depth ? 'true' : 'false')
  }
}

function showNotice(message) {
  const notice = $('#notice')
  text(notice, message)
  notice.classList.add('visible')
  window.clearTimeout(state.noticeTimer)
  state.noticeTimer = window.setTimeout(() => notice.classList.remove('visible'), 2400)
}

function setDepth(depth) {
  state.depth = depth
  render()
  if (depth === 'REASON') showNotice('Derivation remains unavailable without canonical Relationship/INXIGHT authority.')
  if (depth === 'PROVE') showNotice('Evidence disclosure and provenance remain unavailable.')
}

function screenToWorld(event) {
  const rect = field.getBoundingClientRect()
  return {
    x: (event.clientX - rect.left) / rect.width * 1000,
    y: (event.clientY - rect.top) / rect.height * 600,
  }
}

function changeZoom(nextZoom, point = { x: 500, y: 300 }) {
  const zoom = Math.max(0.65, Math.min(2.25, nextZoom))
  const factor = zoom / state.camera.zoom
  state.camera = {
    x: point.x - (point.x - state.camera.x) * factor,
    y: point.y - (point.y - state.camera.y) * factor,
    zoom,
  }
  updateCamera()
}

function bindInteractions() {
  $('#sidebar-toggle').addEventListener('click', (event) => {
    const button = event.currentTarget
    const collapsed = document.querySelector('.workspace').classList.toggle('sidebar-collapsed')
    button.setAttribute('aria-expanded', String(!collapsed))
    button.setAttribute('aria-label', collapsed ? 'Expand sidebar' : 'Collapse sidebar')
    button.title = collapsed ? 'Expand sidebar' : 'Collapse sidebar'
    button.textContent = collapsed ? '»' : '«'
  })
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
  for (const button of document.querySelectorAll('[data-depth]')) {
    button.addEventListener('click', () => setDepth(button.dataset.depth))
  }
  $('#zoom-in').addEventListener('click', () => changeZoom(state.camera.zoom * 1.18))
  $('#zoom-out').addEventListener('click', () => changeZoom(state.camera.zoom / 1.18))
  $('#zoom-reset').addEventListener('click', () => {
    state.camera = { x: 0, y: 0, zoom: 1 }
    updateCamera()
  })

  field.addEventListener('pointerdown', (event) => {
    if (event.target.closest?.('.node')) return
    state.pointer = { id: event.pointerId, last: screenToWorld(event) }
    field.setPointerCapture(event.pointerId)
    field.classList.add('is-panning')
  })
  field.addEventListener('pointermove', (event) => {
    if (!state.pointer || state.pointer.id !== event.pointerId) return
    const next = screenToWorld(event)
    state.camera.x += next.x - state.pointer.last.x
    state.camera.y += next.y - state.pointer.last.y
    state.pointer.last = next
    updateCamera()
  })
  const stopPan = () => {
    state.pointer = null
    field.classList.remove('is-panning')
  }
  field.addEventListener('pointerup', stopPan)
  field.addEventListener('pointercancel', stopPan)
  field.addEventListener('wheel', (event) => {
    event.preventDefault()
    const point = screenToWorld(event)
    changeZoom(state.camera.zoom * Math.exp(-event.deltaY * 0.0012), point)
  }, { passive: false })

  $('#minimap').addEventListener('click', (event) => {
    const rect = event.currentTarget.getBoundingClientRect()
    const x = (event.clientX - rect.left) / rect.width * 1000
    const y = (event.clientY - rect.top) / rect.height * 600
    state.camera.x = 500 - x * state.camera.zoom
    state.camera.y = 300 - y * state.camera.zoom
    updateCamera()
  })
}

function displayProjection(projection) {
  state.projection = projection
  state.focus = organizationKey()
  state.history = [organizationKey()]
  state.historyIndex = 0
  text($('#context-label'), projection.context.label ?? 'Authorized private context')
  text($('#organization-name'), projection.organization.name)
  displayList($('#capabilities'), projection.organization.capabilities)
  displayList($('#markets'), projection.organization.markets)
  $('#load-state').hidden = true
  render()
}

async function start() {
  bindInteractions()
  const demoState = new URLSearchParams(window.location.search).get('demo')
  const endpoint = demoState === 'empty'
    ? '/api/demo/empty'
    : demoState === 'unavailable'
      ? '/api/demo/unavailable'
      : '/api/subscriber-context'
  try {
    const response = await fetch(endpoint, { credentials: 'same-origin', cache: 'no-store' })
    if (!response.ok) throw new Error('unavailable')
    displayProjection(await response.json())
    if (demoState === 'empty') showNotice('This authorized Xeed has no explicit FAXT references in this test/dev authority.')
  } catch {
    text($('#load-state'), 'AXIGLAND projection unavailable.')
    $('#load-state').classList.add('error-state')
    document.querySelector('.workspace').dataset.state = 'unavailable'
  }
}

start()
