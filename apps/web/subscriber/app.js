const $ = (selector) => document.querySelector(selector)
const presentation = window.AXIGNAL_PRESENTATION.forLocale(document.documentElement.lang)

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

const state = {
  projection: null,
  focus: null,
  history: [],
  historyIndex: -1,
  depth: 0,
  camera: { x: 0, y: 0, zoom: 1 },
  pointer: null,
  cameraFrame: 0,
  size: { width: 0, height: 0 },
  worldNodes: [],
}

const app = $('.app2')
const field = $('#field')
const cameraLayer = $('#camera-layer')
const minimapNodes = $('#minimap-nodes')
const minimapWindow = $('#minimap-window')
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)')
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
const MINIMAP = { width: 156, height: 96, x0: 4, x1: 96, y0: 6, y1: 96 }

function projectionKey(kind, id) {
  return `${kind}:${id}`
}

function organizationKey() {
  return projectionKey('ORGANIZATION', state.projection.organization.id)
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
    ? { key, id: source.id, kind: 'FAXT', label: presentation.describeFact(source).label, source }
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
      label: presentation.describeFact(source).label,
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
  updateMinimap()
}

function updateMinimap() {
  const { width, height } = state.size
  if (!width || !height) return
  const { width: mapWidth, height: mapHeight, x0, x1, y0, y1 } = MINIMAP
  const zoom = state.camera.zoom
  const xLeft = ((-state.camera.x / zoom) / width) * 100
  const xRight = (((width - state.camera.x) / zoom) / width) * 100
  const yTop = ((-state.camera.y / zoom) / height) * 100
  const yBottom = (((height - state.camera.y) / zoom) / height) * 100
  const mmX = (value) => ((value - x0) / (x1 - x0)) * mapWidth
  const mmY = (value) => ((value - y0) / (y1 - y0)) * mapHeight
  minimapWindow.setAttribute('x', String(mmX(xLeft) + 2))
  minimapWindow.setAttribute('y', String(mmY(yTop) + 3))
  minimapWindow.setAttribute('width', String(mmX(xRight) - mmX(xLeft)))
  minimapWindow.setAttribute('height', String(mmY(yBottom) - mmY(yTop)))
}

function makeMark(node) {
  const mark = document.createElement('span')
  const status = node.kind === 'ORGANIZATION' ? 'ORGANIZATION' : node.source.epistemicState
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
  if (node.kind === 'ORGANIZATION') {
    label.textContent = node.label
    return label
  }

  const fact = presentation.describeFact(node.source)
  const predicate = document.createElement('span')
  predicate.textContent = fact.predicateLabel
  const value = document.createElement('span')
  value.className = 'node-value'
  if (fact.valueLabel) {
    value.textContent = fact.valueLabel
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
  minimapNodes.replaceChildren()

  for (const node of state.worldNodes) {
    cameraLayer.append(makeNode(node))
    const mini = document.createElementNS('http://www.w3.org/2000/svg', 'circle')
    mini.setAttribute('class', `mini-node${node.kind === 'ORGANIZATION' ? ' organization' : ''}`)
    mini.setAttribute('cx', String(((node.x - MINIMAP.x0) / (MINIMAP.x1 - MINIMAP.x0)) * MINIMAP.width + 4))
    mini.setAttribute('cy', String(((node.y - MINIMAP.y0) / (MINIMAP.y1 - MINIMAP.y0)) * MINIMAP.height + 3))
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
  if (record) pushHistory(key)
  state.focus = key
  render()
  if (recenter) focusCamera(key)
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

function renderReader(node) {
  const target = $('#reader')
  target.replaceChildren()
  const isOrganization = node.kind === 'ORGANIZATION'

  if (isOrganization) {
    const rootView = document.createElement('div')
    rootView.className = 'today'
    const readerHeader = makeReaderHeader(
      presentation.text('copy.today'),
      node.label,
      presentation.text('organization.identity'),
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
    summary.textContent = presentation.countDetails(state.projection.nodes.length)
    greeting.append(readerHeader.header, name, title, summary)

    const context = document.createElement('div')
    context.className = 'today-cont'
    const contextLabel = document.createElement('span')
    contextLabel.className = 'mono'
    const contextName = state.projection.context.label
    contextLabel.textContent = `${presentation.text('context.label')} · ${presentation.isImplementationValue(contextName)
      ? presentation.text('context.current')
      : contextName || presentation.text('context.current')}`
    const explanation = document.createElement('p')
    explanation.textContent = presentation.text('copy.contextExplanation')
    context.append(contextLabel, explanation)
    head.append(greeting, context)
    rootView.append(head, readerHeader.meaning)

    if (state.projection.nodes.length) {
      const cards = document.createElement('div')
      cards.className = 'today-ideas'
      for (const faxt of state.projection.nodes) {
        const card = document.createElement('article')
        card.className = 'idea'
        const title = document.createElement('h3')
        const fact = presentation.describeFact(faxt)
        title.textContent = fact.label
        const foot = document.createElement('div')
        foot.className = 'idea-foot'
        const stateLabel = document.createElement('span')
        stateLabel.className = 'state-word'
        stateLabel.textContent = fact.epistemicLabel ?? ''
        const open = document.createElement('span')
        open.className = 'act'
        open.textContent = presentation.text('action.open')
        if (fact.epistemicLabel) foot.append(stateLabel)
        foot.append(open)
        card.append(title, foot)
        card.addEventListener('click', () => navigate(projectionKey('FAXT', faxt.id)))
        card.setAttribute('role', 'button')
        card.tabIndex = 0
        card.addEventListener('keydown', (event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            navigate(projectionKey('FAXT', faxt.id))
          }
        })
        cards.append(card)
      }
      rootView.append(cards)
    }
    target.append(rootView)
    const fieldList = document.createElement('div')
    fieldList.id = 'bottom-fields'
    fieldList.className = 'reader-fields'
    const fields = [
      setReaderField(presentation.text('field.capabilities'), node.source.capabilities
        .filter((value) => !presentation.isImplementationValue(value)).join(' · ')),
      setReaderField(presentation.text('field.markets'), node.source.markets
        .filter((value) => !presentation.isImplementationValue(value)).join(' · ')),
    ].filter(Boolean)
    fieldList.append(...fields)
    rootView.append(fieldList)
    return
  }

  const focusView = document.createElement('div')
  focusView.className = 'focusview'
  const fact = presentation.describeFact(node.source)
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
  visible.forEach((key, index) => {
    const node = getNode(key)
    const item = document.createElement('button')
    item.className = `trail-item${index === state.historyIndex ? ' cur' : ''}`
    item.textContent = index === 0 ? presentation.text('copy.today') : node?.label ?? presentation.text('context.current')
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
  pill.className = `ax-pill ${node.kind === 'FAXT' ? node.source.epistemicState : 'UNKNOWN'}`
  const contextLabel = state.projection.context.label
  const displayContext = presentation.isImplementationValue(contextLabel)
    ? presentation.text('context.current')
    : contextLabel || presentation.text('context.current')
  $('#axent-xeed-label').textContent = displayContext
  $('#xeed-label').textContent = displayContext
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

function bindInteractions() {
  $('#sidebar-toggle').addEventListener('click', (event) => {
    const collapsed = $('.gov').classList.toggle('collapsed')
    app.classList.toggle('gov-off', collapsed)
    event.currentTarget.setAttribute('aria-expanded', String(!collapsed))
    const sidebarLabel = collapsed
      ? presentation.text('navigation.expandSidebar')
      : presentation.text('navigation.collapseSidebar')
    event.currentTarget.setAttribute('aria-label', sidebarLabel)
    event.currentTarget.title = sidebarLabel
    event.currentTarget.textContent = collapsed ? '»' : '«'
    requestAnimationFrame(() => { state.size = { width: field.clientWidth, height: field.clientHeight }; renderMap() })
  })
  $('#today').addEventListener('click', (event) => {
    event.preventDefault()
    navigate(organizationKey())
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

  $('#zoom-in').addEventListener('click', () => changeZoom(state.camera.zoom * 1.18))
  $('#zoom-out').addEventListener('click', () => changeZoom(state.camera.zoom / 1.18))
  $('#zoom-fit').addEventListener('click', fitCamera)
  $('#zoom-root').addEventListener('click', () => focusCamera(organizationKey()))
  $('#field-reload').addEventListener('click', () => {
    state.camera = { x: 0, y: 0, zoom: 1 }
    state.depth = 0
    renderDepth()
    updateCamera()
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
    const rect = $('#minimap').getBoundingClientRect()
    const px = ((event.clientX - rect.left) / rect.width) * MINIMAP.width
    const py = ((event.clientY - rect.top) / rect.height) * MINIMAP.height
    const x = MINIMAP.x0 + (px / MINIMAP.width) * (MINIMAP.x1 - MINIMAP.x0)
    const y = MINIMAP.y0 + (py / MINIMAP.height) * (MINIMAP.y1 - MINIMAP.y0)
    state.camera.x = state.size.width / 2 - (x / 100) * state.size.width * state.camera.zoom
    state.camera.y = state.size.height / 2 - (y / 100) * state.size.height * state.camera.zoom
    updateCamera()
  }
  $('#minimap').addEventListener('click', moveMinimap)
  $('#minimap').addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      const rect = $('#minimap').getBoundingClientRect()
      moveMinimap({ clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2 })
    }
  })
  $('#axent-composer').addEventListener('submit', (event) => event.preventDefault())
  window.addEventListener('resize', () => {
    if (!state.projection) return
    state.size = { width: field.clientWidth, height: field.clientHeight }
    renderMap()
  })
}

function displayProjection(projection) {
  state.projection = projection
  state.focus = organizationKey()
  state.history = [organizationKey()]
  state.historyIndex = 0
  app.dataset.state = 'ready'
  render()
  fitCamera()
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
