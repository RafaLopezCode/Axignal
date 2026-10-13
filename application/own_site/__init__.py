"""What an organization's own website shows beyond its text — global by construction.

Every organization anywhere has a website; what it loads and links is evidence in any
country and any language:

- the technology it runs on (code, frames and forms it loads from vendors): its observed
  technology suppliers (RELATIONSHIP, OBSERVED: the page loads their code; a contract,
  plan or spend is not established);
- the clients and partners it shows under a "clients" or "partners" heading (logo walls),
  and the certifications and partner badges it claims (DECLARED: its own claim);
- whether it is hiring (job postings, a careers page or an applicant-tracking vendor):
  an operating signal (activity family);
- the review profiles it links and the rating it publishes about itself (reputation:
  DECLARED, its own voice, never independent).

Deterministic and cost-free: no model call, nothing fetched beyond the pages already read.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any
from urllib.parse import urlsplit

from application.activity import boards_on
from application.first_observation.contracts import Discovery, DiscoveryKind
from application.first_observation.site import PageReading

OWN_SITE_VERSION = "own-site-v1"

#: host suffix -> (vendor, category). Categories name what the organization buys.
VENDORS: dict[str, tuple[str, str]] = {
    "googletagmanager.com": ("Google Tag Manager", "ANALYTICS"),
    "google-analytics.com": ("Google Analytics", "ANALYTICS"),
    "plausible.io": ("Plausible", "ANALYTICS"),
    "matomo.cloud": ("Matomo", "ANALYTICS"),
    "static.hotjar.com": ("Hotjar", "ANALYTICS"),
    "clarity.ms": ("Microsoft Clarity", "ANALYTICS"),
    "cdn.segment.com": ("Segment", "ANALYTICS"),
    "cdn.amplitude.com": ("Amplitude", "ANALYTICS"),
    "cdn.mxpnl.com": ("Mixpanel", "ANALYTICS"),
    "googleadservices.com": ("Google Ads", "ADVERTISING"),
    "googlesyndication.com": ("Google Ads", "ADVERTISING"),
    "doubleclick.net": ("Google Ads", "ADVERTISING"),
    "connect.facebook.net": ("Meta Ads", "ADVERTISING"),
    "snap.licdn.com": ("LinkedIn Ads", "ADVERTISING"),
    "analytics.tiktok.com": ("TikTok Ads", "ADVERTISING"),
    "bat.bing.com": ("Microsoft Ads", "ADVERTISING"),
    "static.ads-twitter.com": ("X Ads", "ADVERTISING"),
    "js.hs-scripts.com": ("HubSpot", "CRM_MARKETING"),
    "js.hsforms.net": ("HubSpot", "CRM_MARKETING"),
    "js.hs-analytics.net": ("HubSpot", "CRM_MARKETING"),
    "forms.hsforms.com": ("HubSpot", "CRM_MARKETING"),
    "pardot.com": ("Salesforce", "CRM_MARKETING"),
    "salesforce.com": ("Salesforce", "CRM_MARKETING"),
    "force.com": ("Salesforce", "CRM_MARKETING"),
    "munchkin.marketo.net": ("Marketo", "CRM_MARKETING"),
    "zohopublic.com": ("Zoho", "CRM_MARKETING"),
    "pipedrive.com": ("Pipedrive", "CRM_MARKETING"),
    "activehosted.com": ("ActiveCampaign", "EMAIL_MARKETING"),
    "list-manage.com": ("Mailchimp", "EMAIL_MARKETING"),
    "chimpstatic.com": ("Mailchimp", "EMAIL_MARKETING"),
    "klaviyo.com": ("Klaviyo", "EMAIL_MARKETING"),
    "sendinblue.com": ("Brevo", "EMAIL_MARKETING"),
    "brevo.com": ("Brevo", "EMAIL_MARKETING"),
    "cdn.shopify.com": ("Shopify", "ECOMMERCE"),
    "myshopify.com": ("Shopify", "ECOMMERCE"),
    "woocommerce.com": ("WooCommerce", "ECOMMERCE"),
    "prestashop.com": ("PrestaShop", "ECOMMERCE"),
    "magento.com": ("Adobe Commerce", "ECOMMERCE"),
    "js.stripe.com": ("Stripe", "PAYMENTS"),
    "paypal.com": ("PayPal", "PAYMENTS"),
    "paypalobjects.com": ("PayPal", "PAYMENTS"),
    "adyen.com": ("Adyen", "PAYMENTS"),
    "klarna.com": ("Klarna", "PAYMENTS"),
    "redsys.es": ("Redsys", "PAYMENTS"),
    "static.wixstatic.com": ("Wix", "CMS"),
    "parastorage.com": ("Wix", "CMS"),
    "squarespace.com": ("Squarespace", "CMS"),
    "squarespace-cdn.com": ("Squarespace", "CMS"),
    "website-files.com": ("Webflow", "CMS"),
    "webflow.com": ("Webflow", "CMS"),
    "hubspotusercontent-na1.net": ("HubSpot CMS", "CMS"),
    "ctfassets.net": ("Contentful", "CMS"),
    "cdn.sanity.io": ("Sanity", "CMS"),
    "wp.com": ("WordPress.com", "CMS"),
    "widget.intercom.io": ("Intercom", "SUPPORT_CHAT"),
    "js.intercomcdn.com": ("Intercom", "SUPPORT_CHAT"),
    "zdassets.com": ("Zendesk", "SUPPORT_CHAT"),
    "client.crisp.chat": ("Crisp", "SUPPORT_CHAT"),
    "embed.tawk.to": ("Tawk.to", "SUPPORT_CHAT"),
    "js.driftt.com": ("Drift", "SUPPORT_CHAT"),
    "freshchat.com": ("Freshworks", "SUPPORT_CHAT"),
    "livechatinc.com": ("LiveChat", "SUPPORT_CHAT"),
    "consent.cookiebot.com": ("Cookiebot", "CONSENT"),
    "cdn.cookielaw.org": ("OneTrust", "CONSENT"),
    "onetrust.com": ("OneTrust", "CONSENT"),
    "cdn.iubenda.com": ("iubenda", "CONSENT"),
    "usercentrics.eu": ("Usercentrics", "CONSENT"),
    "didomi.io": ("Didomi", "CONSENT"),
    "cdnjs.cloudflare.com": ("Cloudflare", "HOSTING_CDN"),
    "challenges.cloudflare.com": ("Cloudflare", "HOSTING_CDN"),
    "cloudfront.net": ("Amazon Web Services", "HOSTING_CDN"),
    "amazonaws.com": ("Amazon Web Services", "HOSTING_CDN"),
    "azureedge.net": ("Microsoft Azure", "HOSTING_CDN"),
    "vercel-insights.com": ("Vercel", "HOSTING_CDN"),
    "netlify.app": ("Netlify", "HOSTING_CDN"),
    "akamaihd.net": ("Akamai", "HOSTING_CDN"),
    "calendly.com": ("Calendly", "SCHEDULING"),
    "assets.calendly.com": ("Calendly", "SCHEDULING"),
    "typeform.com": ("Typeform", "FORMS"),
    "jotform.com": ("Jotform", "FORMS"),
    "player.vimeo.com": ("Vimeo", "VIDEO"),
    "youtube.com": ("YouTube", "VIDEO"),
    "youtube-nocookie.com": ("YouTube", "VIDEO"),
    "fast.wistia.com": ("Wistia", "VIDEO"),
    "maps.googleapis.com": ("Google Maps", "MAPS"),
    "api.mapbox.com": ("Mapbox", "MAPS"),
    "algolia.net": ("Algolia", "SEARCH"),
    "algolianet.com": ("Algolia", "SEARCH"),
    "recaptcha.net": ("Google reCAPTCHA", "SECURITY"),
    "hcaptcha.com": ("hCaptcha", "SECURITY"),
}
#: Applicant-tracking vendors: a link or frame to them means a hiring process.
HIRING_VENDORS: dict[str, str] = {
    "greenhouse.io": "Greenhouse", "lever.co": "Lever", "workable.com": "Workable",
    "personio.de": "Personio", "personio.com": "Personio", "teamtailor.com": "Teamtailor",
    "smartrecruiters.com": "SmartRecruiters", "recruitee.com": "Recruitee",
    "ashbyhq.com": "Ashby", "bamboohr.com": "BambooHR", "join.com": "JOIN",
    "myworkdayjobs.com": "Workday", "successfactors.com": "SAP SuccessFactors",
    "jobvite.com": "Jobvite", "breezy.hr": "Breezy HR", "factorialhr.com": "Factorial",
    "softgarden.io": "softgarden", "welcomekit.co": "Welcome to the Jungle",
    "welcometothejungle.com": "Welcome to the Jungle", "infojobs.net": "InfoJobs",
}  # fmt: skip
#: Review platforms: a link to them names where its customers review it.
REVIEW_PLATFORMS: dict[str, str] = {
    "trustpilot.com": "Trustpilot", "g2.com": "G2", "capterra.com": "Capterra",
    "capterra.es": "Capterra", "capterra.fr": "Capterra", "capterra.de": "Capterra",
    "glassdoor.com": "Glassdoor", "glassdoor.es": "Glassdoor", "kununu.com": "kununu",
    "tripadvisor.com": "Tripadvisor", "tripadvisor.es": "Tripadvisor", "yelp.com": "Yelp",
    "trustedshops.com": "Trusted Shops", "trustedshops.de": "Trusted Shops",
    "reviews.io": "REVIEWS.io", "feefo.com": "Feefo", "ekomi.com": "eKomi",
    "avis-verifies.com": "Avis Vérifiés", "clutch.co": "Clutch", "sortlist.com": "Sortlist",
    "goodfirms.co": "GoodFirms", "producthunt.com": "Product Hunt",
}  # fmt: skip
_GENERATORS = re.compile(
    r"\b(WordPress|Drupal|Joomla|Wix|Squarespace|Webflow|Ghost|TYPO3|Shopify|PrestaShop|"
    r"Magento|HubSpot|Duda|Jimdo|Framer|Hugo|Gatsby|Next\.js|Nuxt|Elementor|Divi)\b",
    re.IGNORECASE,
)
_CAREERS = re.compile(
    r"\b(careers?|jobs?|join[- ]us|work[- ]with[- ]us|vacanc|empleo|trabaja|[uú]nete|"
    r"ofertas[- ]de[- ]empleo|karriere|stellen|jobs?-und|carri[eè]res?|recrutement|"
    r"rejoignez|lavora[- ]con[- ]noi|carriere|carreiras?|trabalhe|vacatures|werken[- ]bij)\b",
    re.IGNORECASE,
)
#: Headings of a client wall: plural or idiomatic, so "customer experience" is not one.
_CLIENTS = re.compile(
    r"\b(clients|clientes|clienti|kunden|klanten|customers|referenz\w*|referencias|"
    r"r[eé]f[eé]rences|trusted by|they trust|trust us|conf[ií]an en|nos avalan|"
    r"font confiance|ci hanno scelto|casos? de [eé]xito|case stud\w*|success stor\w*|"
    r"brands we|marcas que|companies that|empresas que)\b",
    re.IGNORECASE,
)
_PARTNERS = re.compile(
    r"\b(partners?|partenaires?|socios|alianzas?|aliados|collaboriamo|colaboramos con|"
    r"member of|miembros? de)\b",
    re.IGNORECASE,
)
#: Headings of a certification wall: its badges are claimed credentials, not partners.
_CERTIFICATIONS = re.compile(
    r"(certifica|certifié|zertifi|accredit|acredita|homologa|normas iso|iso standards)",
    re.IGNORECASE,
)
_GENERIC_ALT = re.compile(
    r"^(logo|logotipo|logotype|image|imagen|img|banner|photo|foto|picture|partner|"
    r"client|cliente|kunde|inicio|home|start|accueil|autor|author|stars?|\W*|\d+|"
    r"(icono?|icon|flecha|arrow)\b.*|.*\.(png|jpe?g|svg|webp|gif))$",
    re.IGNORECASE,
)
MAX_ALT_WORDS = 5
_LOGO_WORDS = re.compile(r"\b(logo(tipo|type)?( de| of| von| di| du)?|icon)\b", re.IGNORECASE)
_CREDENTIALS = re.compile(
    r"\b(ISO\s?/?\s?(?:IEC\s)?\d{4,5}(?::\d{4})?|SOC\s?2(?:\s?Type\s?I{1,2})?|PCI[\s-]DSS|"
    r"B\s?Corp(?:oration)?|EcoVadis|Great Place to Work|CMMI|HIPAA|Cyber Essentials(?: Plus)?|"
    r"Google (?:Premier )?Partner|Meta Business Partner|HubSpot (?:Solutions |Elite |Diamond |"
    r"Platinum |Gold )?Partner|Microsoft (?:Gold |Solutions )?Partner|AWS (?:Advanced |Premier )?"
    r"(?:Consulting |Select |Technology )?Partner|Salesforce (?:Consulting )?Partner|"
    r"Shopify (?:Plus )?Partner|Semrush (?:Agency )?Partner)\b",
    re.IGNORECASE,
)
MAX_TECH = 20
MAX_NAMES = 12


def _match(host: str, table: Mapping[str, str] | Mapping[str, tuple[str, str]]) -> str | None:
    """The most specific table key the host equals or ends with."""
    parts = host.lower().split(".")
    for i in range(len(parts) - 1):
        suffix = ".".join(parts[i:])
        if suffix in table:
            return suffix
    return None


def _strings(value: object) -> list[str]:
    return [str(v) for v in value] if isinstance(value, list) else []


def _items(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def technology(pages: Sequence[PageReading]) -> list[Discovery]:
    """Vendors whose code the site loads: observed technology suppliers."""
    found: dict[str, dict[str, Any]] = {}
    for page in pages:
        for host in _strings(page.signals.get("resourceHosts")):
            key = _match(host, VENDORS)
            if key is None:
                continue
            vendor, category = VENDORS[key]
            entry = found.setdefault(vendor, {"category": category, "hosts": [], "page": page})
            if host not in entry["hosts"]:
                entry["hosts"].append(host)
        generator = page.signals.get("generator")
        named = _GENERATORS.search(str(generator)) if isinstance(generator, str) else None
        if named:
            vendor = named.group(1)
            found.setdefault(vendor, {"category": "CMS", "hosts": [], "page": page,
                                      "generator": str(generator)[:80]})  # fmt: skip
    out: list[Discovery] = []
    for vendor, entry in list(found.items())[:MAX_TECH]:
        page = entry["page"]
        assert isinstance(page, PageReading)
        generator = entry.get("generator")
        out.append(
            Discovery(
                DiscoveryKind.RELATIONSHIP,
                "TECHNOLOGY_SUPPLIER_OBSERVED",
                vendor,
                "OBSERVED",
                page.url,
                f'<meta name="generator" content="{generator}">'
                if generator
                else "loads " + ", ".join(map(str, entry["hosts"]))[:200],
                page.observed_at,
                {
                    "category": entry["category"],
                    "hosts": entry["hosts"],
                    "role": "SUPPLIER",
                    "ownSiteVersion": OWN_SITE_VERSION,
                    "limitation": "Its website loads this vendor's technology; a contract, plan "
                    "or spend is not established.",
                },
            )
        )
    return out


def _wall_names(alts: Iterable[str]) -> list[str]:
    names: list[str] = []
    for alt in alts:
        name = _LOGO_WORDS.sub("", alt).strip(" -|:·,")
        if (
            2 <= len(name) <= 60
            and len(name.split()) <= MAX_ALT_WORDS  # a sentence is not a brand
            and not _GENERIC_ALT.match(name)
            and name not in names
        ):
            names.append(name)
    return names


def logo_walls(pages: Sequence[PageReading], own_names: Iterable[str] = ()) -> list[Discovery]:
    """Clients and partners the site shows as logos under a clients/partners heading."""
    own = {n.casefold() for n in own_names if n}
    out: list[Discovery] = []
    seen: set[tuple[str, str]] = set()
    for page in pages:
        by_heading: dict[str, list[str]] = {}
        for pair in _items(page.signals.get("imageAlts")):
            if isinstance(pair, list | tuple) and len(pair) == 2:
                by_heading.setdefault(str(pair[0]), []).append(str(pair[1]))
        for heading, alts in by_heading.items():
            role = (
                None if _CERTIFICATIONS.search(heading)
                else "PARTNER" if _PARTNERS.search(heading)
                else "CLIENT" if _CLIENTS.search(heading)
                else None
            )  # fmt: skip
            names = [n for n in _wall_names(alts) if n.casefold() not in own]
            if role is None or len(names) < 3:  # one image under a heading is not a wall
                continue
            for name in names[:MAX_NAMES]:
                if (role, name.casefold()) in seen:
                    continue
                seen.add((role, name.casefold()))
                out.append(
                    Discovery(
                        DiscoveryKind.RELATIONSHIP,
                        f"{role}_DECLARED",
                        name,
                        "DECLARED",
                        page.url,
                        f"{heading}: {name}"[:200],
                        page.observed_at,
                        {
                            "role": role,
                            "heading": heading[:120],
                            "ownSiteVersion": OWN_SITE_VERSION,
                            "limitation": "Shown by the organization itself as a "
                            + ("partner" if role == "PARTNER" else "client")
                            + "; the counterparty has not confirmed it.",
                        },
                    )
                )
    return out


def credentials(pages: Sequence[PageReading]) -> list[Discovery]:
    """Certifications and partner badges the site claims (text and image alternatives)."""
    out: list[Discovery] = []
    seen: set[str] = set()
    for page in pages:
        pairs = [(str(p[0]), str(p[1])) for p in _items(page.signals.get("imageAlts"))
                 if isinstance(p, list | tuple) and len(p) == 2]  # fmt: skip
        badges = [alt for heading, alt in pairs if _CERTIFICATIONS.search(heading)]
        for line in [*page.text.splitlines(), *(alt for _, alt in pairs)]:
            labels = [m.group(1) for m in _CREDENTIALS.finditer(line)]
            if not labels and line in badges:
                labels = _wall_names([line])[:1]
            for raw in labels:
                label = re.sub(r"\s+", " ", raw).strip()
                key = re.sub(r"[\s/]", "", label).casefold()
                if key in seen:
                    continue
                seen.add(key)
                out.append(
                    Discovery(
                        DiscoveryKind.CREDENTIAL,
                        "CERTIFICATION_CLAIMED",
                        label,
                        "DECLARED",
                        page.url,
                        line[:200],
                        page.observed_at,
                        {
                            "ownSiteVersion": OWN_SITE_VERSION,
                            "limitation": "Claimed on its own website; the issuer's register "
                            "has not been checked.",
                        },
                    )
                )
    return out[:12]


def hiring(pages: Sequence[PageReading]) -> list[Discovery]:
    """Whether it is hiring: job postings it publishes, a careers page, a hiring vendor."""
    out: list[Discovery] = []
    jobs: list[dict[str, object]] = []
    job_page: PageReading | None = None
    for page in pages:
        for job in _items(page.signals.get("jobPostings")):
            if isinstance(job, Mapping) and job.get("title"):
                jobs.append(dict(job))
                job_page = job_page or page
    if jobs and job_page is not None:
        out.append(
            Discovery(
                DiscoveryKind.OPERATING_SIGNAL,
                "JOB_POSTINGS_PUBLISHED",
                str(len(jobs)),
                "DECLARED",
                job_page.url,
                "; ".join(str(j["title"]) for j in jobs[:5])[:200],
                job_page.observed_at,
                {"count": len(jobs), "titles": [str(j["title"]) for j in jobs[:10]],
                 "ownSiteVersion": OWN_SITE_VERSION},
            )
        )  # fmt: skip
    vendors: dict[str, PageReading] = {}
    careers: tuple[str, PageReading] | None = None
    for page in pages:
        hosts = [*_strings(page.signals.get("resourceHosts")),
                 *_strings(page.signals.get("externalLinkHosts"))]  # fmt: skip
        for host in hosts:
            key = _match(host, HIRING_VENDORS)
            if key is not None:
                vendors.setdefault(HIRING_VENDORS[key], page)
        for url, text in page.links:
            if careers is None and (_CAREERS.search(text) or _CAREERS.search(urlsplit(url).path)):
                careers = (url, page)
    if careers is not None or vendors or boards_on(pages):
        careers_url = careers[0] if careers is not None else None
        page = careers[1] if careers is not None else next(iter(vendors.values()), pages[0])
        out.append(
            Discovery(
                DiscoveryKind.OPERATING_SIGNAL,
                "HIRING_CHANNEL_PUBLISHED",
                ", ".join(vendors) or (careers_url or ""),
                "DECLARED",
                careers_url or page.url,
                None,
                page.observed_at,
                {
                    "careersPage": careers_url,
                    "hiringVendors": sorted(vendors),
                    "jobBoards": [f"{v}:{t}" for v, t in boards_on(pages)],
                    "ownSiteVersion": OWN_SITE_VERSION,
                    "limitation": "A careers channel shows a hiring process exists; open "
                    "positions are not established unless it publishes them.",
                },
            )
        )
    return out


def reputation(pages: Sequence[PageReading]) -> list[Discovery]:
    """Review profiles it links and the rating it publishes about itself."""
    out: list[Discovery] = []
    platforms: dict[str, PageReading] = {}
    for page in pages:
        hosts = [*_strings(page.signals.get("externalLinkHosts"))]
        for link in _strings(page.signals.get("sameAs")):
            hosts.append((urlsplit(link).hostname or "").lower())
        for host in hosts:
            key = _match(host, REVIEW_PLATFORMS)
            if key is not None:
                platforms.setdefault(REVIEW_PLATFORMS[key], page)
    for platform, page in sorted(platforms.items()):
        out.append(
            Discovery(
                DiscoveryKind.RATING,
                "REVIEW_PROFILE_LINKED",
                platform,
                "DECLARED",
                page.url,
                None,
                page.observed_at,
                {"platform": platform, "ownSiteVersion": OWN_SITE_VERSION,
                 "limitation": "It links its profile on this platform; the rating there has "
                 "not been read."},
            )
        )  # fmt: skip
    for page in pages:
        ratings = page.signals.get("ratings") or []
        rating = ratings[0] if isinstance(ratings, list) and ratings else None
        if isinstance(rating, Mapping):
            out.append(
                Discovery(
                    DiscoveryKind.RATING,
                    "RATING_SELF_PUBLISHED",
                    f"{rating.get('value')}/{rating.get('best')}",
                    "DECLARED",
                    page.url,
                    f"schema.org aggregateRating: {rating.get('value')}/{rating.get('best')} "
                    f"({rating.get('count')})",
                    page.observed_at,
                    {**dict(rating), "ownSiteVersion": OWN_SITE_VERSION,
                     "limitation": "A rating the organization publishes about itself, not an "
                     "independent review."},
                )
            )  # fmt: skip
            break
    return out


def own_site_discoveries(
    pages: Sequence[PageReading], own_names: Iterable[str] = ()
) -> list[Discovery]:
    """Every own-site signal, in family order: relationships, value, activity, reputation."""
    if not pages:
        return []
    return [
        *technology(pages),
        *logo_walls(pages, own_names),
        *credentials(pages),
        *hiring(pages),
        *reputation(pages),
    ]
