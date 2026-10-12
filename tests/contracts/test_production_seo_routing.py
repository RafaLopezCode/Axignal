from pathlib import Path

ROUTE = Path("deploy/production/traefik/axignal-public-seo.yml")


def test_public_seo_router_exposes_only_expected_public_surface() -> None:
    text = ROUTE.read_text(encoding="utf-8")
    required = (
        "Path(`/sitemap.xml`)",
        # Home language versions, published prices and the assistant summary (audit 2026-10-12).
        "Path(`/es`)",
        "Path(`/en`)",
        "Path(`/fr`)",
        "Path(`/de`)",
        "Path(`/it`)",
        "Path(`/pt`)",
        "Path(`/pricing`)",
        "Path(`/llms.txt`)",
        "Path(`/robots.txt`)",
        "PathPrefix(`/knowledge`)",
        "PathPrefix(`/es/knowledge`)",
        "PathPrefix(`/en/knowledge`)",
        "PathPrefix(`/fr/knowledge`)",
        "PathPrefix(`/de/knowledge`)",
        "PathPrefix(`/it/knowledge`)",
        "PathPrefix(`/pt/knowledge`)",
        "Path(`/contact`)",
        "Path(`/gdpr`)",
        "Path(`/policies`)",
        "PathPrefix(`/policies/`)",
        "PathPrefix(`/_next/`)",
        "PathPrefix(`/brand/`)",
        "http://127.0.0.1:18182",
        "priority: 200",
    )
    for fragment in required:
        assert fragment.replace("\\", "") in text
    forbidden = (
        "PathPrefix(`/admin",
        "PathPrefix(`/api",
        "PathPrefix(`/account",
        "PathPrefix(`/login",
        "PathPrefix(`/signup",
        "PathPrefix(`/panorama",
    )
    for fragment in forbidden:
        assert fragment.replace("\\", "") not in text


def test_public_seo_router_reuses_canonical_host_and_security_policy() -> None:
    text = ROUTE.read_text(encoding="utf-8")
    assert "axignal-landing-canonical" in text
    assert "axignal-landing-security" in text
    assert "certResolver: letsencrypt" in text


def test_public_edge_answers_unknown_paths_with_404_not_the_legacy_landing() -> None:
    # Spec 060: a soft 404 served the retired static landing (index,follow) for any
    # unknown path (/pricing, /demo, /admin...), competing with the real home page.
    for conf in (
        Path("deploy/production/subscriber-edge-nginx.conf"),
        Path("deploy/production/docker/landing-nginx.conf"),
    ):
        text = conf.read_text(encoding="utf-8")
        assert "/index.html;" not in text.replace("index index.html;", ""), conf
        assert "try_files $uri $uri/ =404;" in text, conf
        assert "error_page 404 /404.html;" in text, conf
    page = Path("apps/web/landing/404.html").read_text(encoding="utf-8")
    assert '<meta name="robots" content="noindex, follow">' in page
    assert 'href="/"' in page


def test_the_retired_static_landing_is_redirected_not_served() -> None:
    """The pre-launch landing (old design, outdated legal notice) must not reappear."""
    from pathlib import Path

    conf = (
        Path(__file__).resolve().parents[2] / "deploy/production/docker/landing-nginx.conf"
    ).read_text(encoding="utf-8")
    assert "location = /index.html { return 301 /; }" in conf
    assert "location ~ ^/(es|en|fr|de|it|pt)/$ { return 301 /$1; }" in conf
    assert "location ^~ /legal/ { return 301 /policies; }" in conf
    assert "location ^~ /legal/privacidad-rgpd { return 301 /policies/privacy; }" in conf
    assert "storyboard-data\.json|marketing\.js|newsletter\.js)$ { return 404; }" in conf


def test_the_subscriber_edge_config_carries_the_legacy_redirects() -> None:
    """The subscriber overlay replaces the landing nginx config in production."""
    from pathlib import Path

    edge = (
        Path(__file__).resolve().parents[2] / "deploy/production/subscriber-edge-nginx.conf"
    ).read_text(encoding="utf-8")
    assert "location = /index.html { return 301 /; }" in edge
    assert "location ^~ /legal/aviso-legal { return 301 /policies/legal; }" in edge
    assert "location ~ ^/(es|en|fr|de|it|pt)/$ { return 301 /$1; }" in edge
