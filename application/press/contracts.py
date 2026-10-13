"""Press feeds and the items they syndicate.

Publishers offer RSS/Atom feeds for syndication: a headline, its link and its date. The
index keeps only that (never article text) and links to the publisher. A feed that
refuses automated access is not read and never bypassed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PressFeed:
    feed_id: str
    outlet: str
    url: str
    country: str  # EU/ES
    language: str
    topics: tuple[str, ...]  # e.g. ("business",), ("energy",), ("marketing",)


@dataclass(frozen=True, slots=True)
class PressItem:
    feed_id: str
    outlet: str
    title: str
    url: str
    published_at: datetime
    language: str
    country: str

    @property
    def key(self) -> str:
        return self.url


#: Publisher feeds verified 2026-10-12/13 (EU, US, CA, GB, LatAm, AU, IN) to answer automated reads. Extend by data, not code
#: paths; a feed that later refuses (403/406/WAF) is skipped, never worked around.
FEEDS: tuple[PressFeed, ...] = (
    PressFeed("europapress-economia", "Europa Press", "https://www.europapress.es/rss/rss.aspx?ch=00136", "EU/ES", "es", ("business",)),
    PressFeed("europapress-portada", "Europa Press", "https://www.europapress.es/rss/rss.aspx", "EU/ES", "es", ("general",)),
    PressFeed("expansion-empresas", "Expansión", "https://e00-expansion.uecdn.es/rss/empresas.xml", "EU/ES", "es", ("business",)),
    PressFeed("elconfidencial-empresas", "El Confidencial", "https://rss.elconfidencial.com/empresas/", "EU/ES", "es", ("business",)),
    PressFeed("lavanguardia-economia", "La Vanguardia", "https://www.lavanguardia.com/rss/economia.xml", "EU/ES", "es", ("business",)),
    PressFeed("abc-economia", "ABC", "https://www.abc.es/rss/2.0/economia/", "EU/ES", "es", ("business",)),
    PressFeed("elmundo-economia", "El Mundo", "https://e00-elmundo.uecdn.es/elmundo/rss/economia.xml", "EU/ES", "es", ("business",)),
    PressFeed("elpais-economia", "El País", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia/portada", "EU/ES", "es", ("business",)),
    PressFeed("20minutos-economia", "20minutos", "https://www.20minutos.es/rss/economia/", "EU/ES", "es", ("business",)),
    PressFeed("elperiodicodelaenergia", "El Periódico de la Energía", "https://elperiodicodelaenergia.com/feed/", "EU/ES", "es", ("energy",)),
    PressFeed("marketingdirecto", "Marketing Directo", "https://www.marketingdirecto.com/feed", "EU/ES", "es", ("marketing",)),
    PressFeed("agroinformacion", "Agroinformación", "https://agroinformacion.com/feed/", "EU/ES", "es", ("agrifood",)),
    PressFeed("handelsblatt-unternehmen", "Handelsblatt", "https://www.handelsblatt.com/contentexport/feed/unternehmen", "EU/DE", "de", ("business",)),
    PressFeed("faz-wirtschaft", "FAZ", "https://www.faz.net/rss/aktuell/wirtschaft/", "EU/DE", "de", ("business",)),
    PressFeed("spiegel-wirtschaft", "Der Spiegel", "https://www.spiegel.de/wirtschaft/index.rss", "EU/DE", "de", ("business",)),
    PressFeed("tagesschau-wirtschaft", "tagesschau", "https://www.tagesschau.de/wirtschaft/index~rss2.xml", "EU/DE", "de", ("business",)),
    PressFeed("zeit-wirtschaft", "Die Zeit", "https://newsfeed.zeit.de/wirtschaft/index", "EU/DE", "de", ("business",)),
    PressFeed("wiwo-unternehmen", "WirtschaftsWoche", "https://www.wiwo.de/contentexport/feed/rss/unternehmen", "EU/DE", "de", ("business",)),
    PressFeed("lemonde-economie", "Le Monde", "https://www.lemonde.fr/economie/rss_full.xml", "EU/FR", "fr", ("business",)),
    PressFeed("lefigaro-economie", "Le Figaro", "https://www.lefigaro.fr/rss/figaro_economie.xml", "EU/FR", "fr", ("business",)),
    PressFeed("latribune", "La Tribune", "https://www.latribune.fr/feed.xml", "EU/FR", "fr", ("business",)),
    PressFeed("ilsole24ore-economia", "Il Sole 24 Ore", "https://www.ilsole24ore.com/rss/economia.xml", "EU/IT", "it", ("business",)),
    PressFeed("repubblica-economia", "la Repubblica", "https://www.repubblica.it/rss/economia/rss2.0.xml", "EU/IT", "it", ("business",)),
    PressFeed("corriere-economia", "Corriere della Sera", "https://xml2.corriereobjects.it/rss/economia.xml", "EU/IT", "it", ("business",)),
    PressFeed("eco-sapo", "ECO", "https://eco.sapo.pt/feed/", "EU/PT", "pt", ("business",)),
    PressFeed("jornaldenegocios", "Jornal de Negócios", "https://www.jornaldenegocios.pt/rss", "EU/PT", "pt", ("business",)),
    PressFeed("cnbc-business", "CNBC", "https://www.cnbc.com/id/10001147/device/rss/rss.html", "US", "en", ("business",)),
    PressFeed("marketwatch-top", "MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_topstories", "US", "en", ("business",)),
    PressFeed("nyt-business", "The New York Times", "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml", "US", "en", ("business",)),
    PressFeed("npr-business", "NPR", "https://feeds.npr.org/1006/rss.xml", "US", "en", ("business",)),
    PressFeed("businesswire", "Business Wire", "https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEFtRWQ==", "US", "en", ("press_release",)),
    PressFeed("prnewswire", "PR Newswire", "https://www.prnewswire.com/rss/news-releases-list.rss", "US", "en", ("press_release",)),
    PressFeed("globeandmail-business", "The Globe and Mail", "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/", "CA", "en", ("business",)),
    PressFeed("financialpost", "Financial Post", "https://financialpost.com/feed", "CA", "en", ("business",)),
    PressFeed("bbc-business", "BBC", "https://feeds.bbci.co.uk/news/business/rss.xml", "GB", "en", ("business",)),
    PressFeed("guardian-business", "The Guardian", "https://www.theguardian.com/uk/business/rss", "GB", "en", ("business",)),
    PressFeed("cityam", "City A.M.", "https://www.cityam.com/feed/", "GB", "en", ("business",)),
    PressFeed("elfinanciero-mx", "El Financiero", "https://www.elfinanciero.com.mx/arc/outboundfeeds/rss/?outputType=xml", "MX", "es", ("business",)),
    PressFeed("expansion-mx", "Expansión México", "https://expansion.mx/rss", "MX", "es", ("business",)),
    PressFeed("infobae-economia", "Infobae", "https://www.infobae.com/arc/outboundfeeds/rss/category/economia/", "AR", "es", ("business",)),
    PressFeed("portafolio", "Portafolio", "https://www.portafolio.co/rss/economia.xml", "CO", "es", ("business",)),
    PressFeed("df-chile", "Diario Financiero", "https://www.df.cl/noticias/site/list/port/rss.xml", "CL", "es", ("business",)),
    PressFeed("valor", "Valor Econômico", "https://pox.globo.com/rss/valor", "BR", "pt", ("business",)),
    PressFeed("infomoney", "InfoMoney", "https://www.infomoney.com.br/feed/", "BR", "pt", ("business",)),
    PressFeed("abc-au-business", "ABC News (AU)", "https://www.abc.net.au/news/feed/51892/rss.xml", "AU", "en", ("business",)),
    PressFeed("economictimes", "The Economic Times", "https://economictimes.indiatimes.com/rssfeedsdefault.cms", "IN", "en", ("business",)),
    # 2026-10-13: global coverage (NO, NL, IE, SE, DK) and sector press (technology,
    # construction, marketing); each validated live: robots.txt allows, the feed parses.
    PressFeed("e24", "E24", "https://e24.no/rss2/", "NO", "nb", ("business",)),
    PressFeed("tu", "Teknisk Ukeblad", "https://www.tu.no/rss", "NO", "nb", ("technology",)),
    PressFeed("smh-business", "The Sydney Morning Herald", "https://www.smh.com.au/rss/business.xml", "AU", "en", ("business",)),
    PressFeed("itnews-au", "iTnews", "https://www.itnews.com.au/RSS/rss.ashx", "AU", "en", ("technology",)),
    PressFeed("betakit", "BetaKit", "https://betakit.com/feed/", "CA", "en", ("technology",)),
    PressFeed("construction-enquirer", "The Construction Enquirer", "https://www.constructionenquirer.com/feed/", "GB", "en", ("construction",)),
    PressFeed("thisismoney", "This is Money", "https://www.thisismoney.co.uk/money/index.rss", "GB", "en", ("business",)),
    PressFeed("computerweekly", "Computer Weekly", "https://www.computerweekly.com/rss/All-Computer-Weekly-content.xml", "GB", "en", ("technology",)),
    PressFeed("bfm-economie", "BFM", "https://www.bfmtv.com/rss/economie/", "EU/FR", "fr", ("business",)),
    PressFeed("usine-digitale", "L'Usine Digitale", "https://www.usine-digitale.fr/rss", "EU/FR", "fr", ("technology",)),
    PressFeed("challenges", "Challenges", "https://www.challenges.fr/rss.xml", "EU/FR", "fr", ("business",)),
    PressFeed("heise", "heise online", "https://www.heise.de/rss/heise-atom.xml", "EU/DE", "de", ("technology",)),
    PressFeed("t3n", "t3n", "https://t3n.de/rss.xml", "EU/DE", "de", ("technology",)),
    PressFeed("horizont", "HORIZONT", "https://www.horizont.net/news/feed/", "EU/DE", "de", ("marketing",)),
    PressFeed("techcrunch", "TechCrunch", "https://techcrunch.com/feed/", "US", "en", ("technology",)),
    PressFeed("constructiondive", "Construction Dive", "https://www.constructiondive.com/feeds/news/", "US", "en", ("construction",)),
    PressFeed("marketingdive", "Marketing Dive", "https://www.marketingdive.com/feeds/news/", "US", "en", ("marketing",)),
    PressFeed("nos-economie", "NOS", "https://feeds.nos.nl/nosnieuwseconomie", "EU/NL", "nl", ("business",)),
    PressFeed("rte-business", "RTÉ", "https://www.rte.ie/feeds/rss/?index=/news/business/", "EU/IE", "en", ("business",)),
    PressFeed("di", "Dagens industri", "https://www.di.se/rss", "EU/SE", "sv", ("business",)),
    PressFeed("borsen", "Børsen", "https://borsen.dk/rss", "EU/DK", "da", ("business",)),
)  # fmt: skip

#: Wires that distribute releases organizations write about themselves (their own voice).
RELEASE_FEEDS = frozenset(f.feed_id for f in FEEDS if "press_release" in f.topics)
