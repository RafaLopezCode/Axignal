"""Readers of official journals: public, keyless APIs and feeds, titles and links only.

* BOE (Spain): the daily summary API; sections I (general provisions) and III (other
  provisions, which carry collective agreements and sector resolutions).
* EUR-Lex (EU): the Publications Office SPARQL endpoint; regulations, directives and
  decisions by document date, titles in the six product languages.
* Federal Register (US): final and proposed rules.
* legislation.gov.uk (UK): the new legislation feed.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from application.regulation import RegulationItem

USER_AGENT = "AXIGNAL/1.0 regulation-observation (+https://axignal.com)"
Fetch = Callable[[str, str], bytes]
EUR_LEX_LANGUAGES = {"ENG": "en", "SPA": "es", "FRA": "fr", "DEU": "de", "ITA": "it", "POR": "pt"}


def _urlopen(url: str, accept: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(request, timeout=60) as response:
        return bytes(response.read(30_000_000))


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def read_boe(day: date, fetch: Fetch = _urlopen) -> list[RegulationItem]:
    body = fetch(
        f"https://www.boe.es/datosabiertos/api/boe/sumario/{day:%Y%m%d}", "application/json"
    )
    data = json.loads(body)
    out: list[RegulationItem] = []
    for diario in _list(((data.get("data") or {}).get("sumario") or {}).get("diario")):
        for section in _list(diario.get("seccion")):
            if str(section.get("codigo")) not in {"1", "3"}:
                continue
            kind = "GENERAL_PROVISION" if str(section.get("codigo")) == "1" else "OTHER_PROVISION"
            for department in _list(section.get("departamento")):
                issuer = department.get("nombre")
                epigraphs = _list(department.get("epigrafe"))
                groups = [e.get("item") for e in epigraphs] or [department.get("item")]
                for group in groups:
                    for item in _list(group):
                        identifier, title = item.get("identificador"), item.get("titulo")
                        if not identifier or not title:
                            continue
                        out.append(
                            RegulationItem(
                                "BOE", str(identifier), str(title)[:600], day, "EU/ES",
                                str(issuer) if issuer else None,
                                str(item.get("url_html") or item.get("url_pdf") or ""),
                                "es", kind,
                            )
                        )  # fmt: skip
    return out


def read_federal_register(since: date, fetch: Fetch = _urlopen) -> list[RegulationItem]:
    out: list[RegulationItem] = []
    url: str | None = "https://www.federalregister.gov/api/v1/documents.json?" + urllib.parse.urlencode(
        [("conditions[publication_date][gte]", since.isoformat()),
         ("conditions[type][]", "RULE"), ("conditions[type][]", "PRORULE"),
         ("per_page", "1000"), ("order", "newest"),
         *[("fields[]", f) for f in ("title", "html_url", "publication_date", "agencies",
                                       "type", "document_number")]]
    )  # fmt: skip
    for _page in range(3):
        if not url:
            break
        data = json.loads(fetch(url, "application/json"))
        for row in data.get("results") or []:
            agencies = [a.get("name") for a in row.get("agencies") or [] if a.get("name")]
            out.append(
                RegulationItem(
                    "FEDERAL_REGISTER", str(row["document_number"]), str(row["title"])[:600],
                    date.fromisoformat(row["publication_date"]), "US",
                    agencies[0] if agencies else None, str(row["html_url"]), "en",
                    "RULE" if row.get("type") == "Rule" else "PROPOSED_RULE",
                )
            )  # fmt: skip
        url = data.get("next_page_url")
    return out


def read_legislation_gov_uk(fetch: Fetch = _urlopen) -> list[RegulationItem]:
    root = ET.fromstring(fetch("https://www.legislation.gov.uk/new/data.feed",
                               "application/atom+xml"))  # fmt: skip
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out: list[RegulationItem] = []
    for entry in root.findall("a:entry", ns):
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        identifier = (entry.findtext("a:id", default="", namespaces=ns) or "").strip()
        when = (entry.findtext("a:published", default="", namespaces=ns)
                or entry.findtext("a:updated", default="", namespaces=ns) or "")  # fmt: skip
        link = entry.find("a:link[@rel='alternate']", ns)
        if link is None:
            link = entry.find("a:link", ns)
        if not title or not identifier or not when:
            continue
        out.append(
            RegulationItem(
                "LEGISLATION_GOV_UK", identifier, title[:600],
                datetime.fromisoformat(when.replace("Z", "+00:00")).date(), "GB", None,
                str(link.get("href") if link is not None else identifier), "en", "LEGISLATION",
            )
        )  # fmt: skip
    return out


def read_eur_lex(since: date, fetch: Fetch = _urlopen) -> list[RegulationItem]:
    """Regulations (R), directives (L) and decisions (D) dated since ``since``, per language."""
    out: list[RegulationItem] = []
    for code, language in EUR_LEX_LANGUAGES.items():
        query = (
            "PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>\n"
            "SELECT DISTINCT ?celex ?date ?title WHERE {\n"
            " ?w cdm:resource_legal_id_celex ?celex ; cdm:work_date_document ?date .\n"
            f' FILTER(?date >= "{since.isoformat()}"^^xsd:date)\n'
            ' FILTER(REGEX(STR(?celex), "^3[0-9]{4}[RL][0-9]"))\n'
            " ?e cdm:expression_belongs_to_work ?w ; cdm:expression_title ?title ;\n"
            "    cdm:expression_uses_language "
            f"<http://publications.europa.eu/resource/authority/language/{code}> .\n"
            "} LIMIT 3000"
        )
        url = "https://publications.europa.eu/webapi/rdf/sparql?" + urllib.parse.urlencode(
            {"query": query, "format": "application/sparql-results+json"}
        )
        data = json.loads(fetch(url, "application/sparql-results+json"))
        for row in (data.get("results") or {}).get("bindings") or []:
            celex = row["celex"]["value"]
            kind = {"R": "REGULATION", "L": "DIRECTIVE", "D": "DECISION"}.get(celex[5:6])
            out.append(
                RegulationItem(
                    "EUR_LEX", f"{celex}:{language}",
                    " ".join(row["title"]["value"].split())[:600],
                    date.fromisoformat(row["date"]["value"][:10]), "EU", None,
                    f"https://eur-lex.europa.eu/legal-content/{language.upper()}/TXT/"
                    f"?uri=CELEX:{celex}", language, kind,
                )
            )  # fmt: skip
    return out
