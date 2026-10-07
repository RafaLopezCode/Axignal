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
