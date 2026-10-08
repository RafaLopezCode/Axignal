from pathlib import Path

ROUTE = Path("deploy/production/traefik/axignal-public-seo.yml")


def test_public_seo_router_exposes_only_expected_public_surface() -> None:
    text = ROUTE.read_text(encoding="utf-8")
    required = (
        "Path(`/sitemap.xml`)",
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
