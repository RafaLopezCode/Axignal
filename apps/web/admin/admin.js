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
    if (breadcrumb) breadcrumb.textContent = current.label
    if (title) title.textContent = current.label
    if (eyebrow) eyebrow.textContent = current.eyebrow
    if (description) description.textContent = current.description
    if (domain) domain.textContent = current.label
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
