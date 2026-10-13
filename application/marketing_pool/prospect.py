"""From a study to a message: recipient, evidenced findings, quality gate, draft contract.

Deterministic first: which address, which findings and whether there is enough specific
value are decided here; a model only phrases the message from the numbered findings it
is handed, in the organization's language, and must cite which ones it used.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from application.marketing_pool.personas import Persona

#: Kind → family, as the subscriber observatory groups them (lib/observation-families.ts).
FAMILY_OF_KIND = {
    "PUBLIC_PRESENCE": "presence",
    "WEB_REPRESENTATION": "presence",
    "REPRESENTATION_GAP": "presence",
    "SEARCH_VISIBILITY": "presence",
    "GENERATIVE_VISIBILITY": "presence",
    "ACTIVITY": "value",
    "DECLARED_LOCATION": "markets",
    "DECLARED_SERVICE_AREA": "markets",
    "IDENTITY_HINT": "organization",
    "DEMAND": "demand",
    "MENTION": "reputation",
    "RELATIONSHIP": "relationships",
    "COMPETITION": "relationships",
    "CONTEXT_SIGNAL": "context",
    "ECONOMIC_FACT": "economics",
}
#: A message goes out only when it could not be sent to another organization unchanged.
MIN_FINDINGS = 4
MIN_FAMILIES = 3
MAX_FINDINGS = 12

#: Role addresses, best first; personal-looking addresses are never chosen.
_ROLES = (
    "partners", "partner", "marketing", "business", "hello", "hola", "hallo", "bonjour",
    "ciao", "info", "contact", "contacto", "kontakt", "contatto", "contato", "office",
    "studio", "agency", "agencia", "agence", "agentur", "team", "equipo", "mail",
    "sales", "ventas", "comercial", "enquiries", "inquiries",
)  # fmt: skip
_NEVER = ("noreply", "no-reply", "donotreply", "privacy", "privacidad", "datenschutz",
          "gdpr", "rgpd", "dpo", "legal", "abuse", "postmaster", "careers", "jobs",
          "empleo", "rrhh", "hr", "billing", "facturacion", "support", "soporte")  # fmt: skip


def recipient(emails: Sequence[str], domain: str) -> str | None:
    """The role address the organization publishes on its own domain, best role first."""
    own = [
        e.lower()
        for e in emails
        if "@" in e and e.lower().rsplit("@", 1)[1].removeprefix("www.").endswith(domain)
    ]
    ranked: list[tuple[int, str]] = []
    for email in own:
        local = email.split("@", 1)[0]
        if any(word in local for word in _NEVER):
            continue
        rank = next((i for i, role in enumerate(_ROLES) if local == role), None)
        if rank is not None:
            ranked.append((rank, email))
    return min(ranked)[1] if ranked else None


@dataclass(frozen=True, slots=True)
class Finding:
    family: str
    kind: str
    code: str
    statement: str
    state: str
    source: str | None
    value: object = None

    def line(self, number: int) -> str:
        value = "" if self.value in (None, "", [], {}) else f" | value: {self.value}"
        return (
            f"[{number}] {self.family} | {self.kind}:{self.code} | {self.statement}{value} "
            f"| {self.state} | source: {self.source or 'n/a'}"
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "family": self.family, "kind": self.kind, "code": self.code,
            "statement": self.statement, "state": self.state, "source": self.source,
            "value": self.value,
        }  # fmt: skip


def findings(view: Mapping[str, Any], lead: Sequence[str] = ()) -> list[Finding]:
    """Evidenced findings worth telling it about: sourced, not unknowns, lead families first."""
    out: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    held = view.get("discoveries")
    for d in held if isinstance(held, list) else []:
        if not isinstance(d, Mapping):
            continue
        kind, code = str(d.get("kind") or ""), str(d.get("code") or "")
        family = FAMILY_OF_KIND.get(kind)
        state = str(d.get("epistemicState") or "")
        source = d.get("sourceUrl") or d.get("source")
        if family is None or state == "UNKNOWN" or not source or (kind, code) in seen:
            continue
        if kind == "WEB_REPRESENTATION" or code == "PUBLIC_WEBSITE_OBSERVED":
            continue  # the container of the checks; each gap is its own finding
        detail = d.get("detail") if isinstance(d.get("detail"), Mapping) else {}
        seen.add((kind, code))
        out.append(
            Finding(
                family, kind, code, str(d.get("statement") or code)[:300], state,
                str(source), detail.get("value") if isinstance(detail, Mapping) else None,
            )
        )  # fmt: skip
    order = {family: i for i, family in enumerate(lead)}
    out.sort(key=lambda f: (order.get(f.family, len(order)), f.state != "OBSERVED"))
    return out[:MAX_FINDINGS]


def gate(selected: Sequence[Finding]) -> str | None:
    """Why there is not enough specific value to write; None when there is."""
    if len(selected) < MIN_FINDINGS:
        return "TOO_FEW_EVIDENCED_FINDINGS"
    if len({f.family for f in selected}) < MIN_FAMILIES:
        return "TOO_FEW_FAMILIES"
    return None


def site_text(view: Mapping[str, Any]) -> str:
    """What its own site says it does: title, description and activity statements."""
    parts: list[str] = []
    held = view.get("discoveries")
    for d in held if isinstance(held, list) else []:
        if isinstance(d, Mapping) and d.get("kind") in {"PUBLIC_PRESENCE", "ACTIVITY"}:
            parts += [str(d.get("statement") or ""), str(d.get("excerpt") or "")]
    return re.sub(r"\s+", " ", " ".join(parts))[:4000]


INSTRUCTION = (
    "You write one short first-party email from AXIGNAL to an organization AXIGNAL has "
    "observed from the outside. Write in the requested language, plainly and warmly, as "
    "one professional to another. Use ONLY the numbered findings given; never add a fact, "
    "number, ranking, client name or claim that is not in them. Findings marked POTENTIAL "
    "must be phrased as possibilities, never as facts. Do not say their website is bad; "
    "state what was measured and where. Do not claim they need or want anything. Mention "
    "at most 4 findings, the most specific ones, each with a few words of why it matters "
    "to them. Then one sentence on what AXIGNAL could add for them, then invite them to see "
    "the full reading. No greetings with invented names, no signature, no footer, no links: "
    "those are added separately; start directly with the first sentence, without any "
    "salutation (one is added). Subject under 70 characters, body under 170 words."
)
SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["subject", "body", "findings_used"],
    "properties": {
        "subject": {"type": "string"},
        "body": {"type": "string"},
        "findings_used": {"type": "array", "items": {"type": "integer"}},
    },
}


def prompt(name: str, language: str, persona_: Persona, selected: Sequence[Finding]) -> str:
    lines = [
        f"Organization: {name}",
        f"Language: {language}",
        f"They are: {persona_.label}",
        f"What AXIGNAL could add for them: {persona_.value_angle}",
        "Findings:",
        *(f.line(i) for i, f in enumerate(selected, 1)),
    ]
    return "\n".join(lines)


_READ = {
    "es": "Ver la lectura completa: {link}",
    "en": "See the full reading: {link}",
    "fr": "Voir la lecture complète : {link}",
    "de": "Die vollständige Auswertung: {link}",
    "it": "Vedi la lettura completa: {link}",
    "pt": "Ver a leitura completa: {link}",
}
_NOTICE = {
    "es": "Le escribimos porque esta dirección figura como contacto en {domain}. "
    "Si no desea más correos:",
    "en": "We are writing because this address is published as a contact on {domain}. "
    "To receive no further emails:",
    "fr": "Nous vous écrivons car cette adresse est publiée comme contact sur {domain}. "
    "Pour ne plus recevoir de courriels :",
    "de": "Wir schreiben Ihnen, weil diese Adresse auf {domain} als Kontakt veröffentlicht "
    "ist. Keine weiteren E-Mails:",
    "it": "Le scriviamo perché questo indirizzo è pubblicato come contatto su {domain}. "
    "Per non ricevere altre email:",
    "pt": "Escrevemos porque este endereço está publicado como contacto em {domain}. "
    "Para não receber mais emails:",
}
LANGUAGES = tuple(_READ)


def language_of(declared: str | None, country: str | None) -> str:
    """The site's declared language when supported; otherwise the country's; else English."""
    if declared and declared[:2].lower() in _READ:
        return declared[:2].lower()
    by_country = {"ES": "es", "MX": "es", "AR": "es", "CO": "es", "CL": "es", "FR": "fr",
                  "BE": "fr", "DE": "de", "AT": "de", "CH": "de", "IT": "it", "PT": "pt",
                  "BR": "pt"}  # fmt: skip
    return by_country.get((country or "").upper(), "en")


#: Who the message is for, without naming anyone: the head of the area that would buy.
_AREA = {
    "SEO_GEO_AGENCY": {"es": "SEO", "en": "SEO", "fr": "SEO", "de": "SEO", "it": "SEO",
                       "pt": "SEO"},
    "DIGITAL_MARKETING_AGENCY": {"es": "marketing", "en": "marketing", "fr": "marketing",
                                 "de": "Marketing", "it": "marketing", "pt": "marketing"},
    "REPUTATION_PR_AGENCY": {"es": "comunicación", "en": "communications",
                             "fr": "communication", "de": "Kommunikation",
                             "it": "comunicazione", "pt": "comunicação"},
    "B2B_CONSULTANCY": {"es": "desarrollo de negocio", "en": "business development",
                        "fr": "développement commercial", "de": "Geschäftsentwicklung",
                        "it": "sviluppo commerciale", "pt": "desenvolvimento de negócio"},
}  # fmt: skip
_ATTENTION = {
    "es": "A la atención del responsable de {area} de {name}",
    "en": "For the attention of the head of {area} at {name}",
    "fr": "À l'attention du responsable {area} de {name}",
    "de": "Zu Händen der Leitung {area}, {name}",
    "it": "All'attenzione del responsabile {area} di {name}",
    "pt": "À atenção do responsável de {area} da {name}",
}


def salutation(language: str, persona_id: str, name: str) -> str:
    """The opening line: addressed to a role at the organization, never to a person."""
    areas = _AREA.get(persona_id, _AREA["DIGITAL_MARKETING_AGENCY"])
    template = _ATTENTION.get(language, _ATTENTION["en"])
    return template.format(area=areas.get(language, areas["en"]), name=name)


def legal_notice(language: str, *, sender: str, address: str, domain: str) -> str:
    """Who writes, from where, why to this address, and how to stop it (before the link)."""
    notice = _NOTICE.get(language, _NOTICE["en"]).format(domain=domain)
    return f"{sender} · AXIGNAL · {address}\n{notice}"


def footer(
    language: str,
    *,
    link: str,
    sender: str,
    address: str,
    domain: str,
    unsubscribe: str,
    signature: str | None = None,
) -> str:
    """The plain-text close: link, signature, then the legal notice and the opt-out link."""
    read = _READ.get(language, _READ["en"]).format(link=link)
    notice = legal_notice(language, sender=sender, address=address, domain=domain)
    signed = f"\n\n{signature}" if signature else ""
    return f"{read}{signed}\n\n—\n{notice} {unsubscribe}"


def accept_draft(
    answer: Mapping[str, Any], selected: Sequence[Finding]
) -> dict[str, object] | None:
    """A usable draft: bounded, citing at least two given findings, no links of its own."""
    subject, body = answer.get("subject"), answer.get("body")
    used = answer.get("findings_used")
    if not isinstance(subject, str) or not isinstance(body, str) or not isinstance(used, list):
        return None
    cited = sorted({i for i in used if isinstance(i, int) and 1 <= i <= len(selected)})
    subject, body = subject.strip(), body.strip()
    if (
        len(cited) < 2
        or not 5 <= len(subject) <= 90
        or not 200 <= len(body) <= 1600
        or re.search(r"https?://|www\.", body)
    ):
        return None
    return {
        "subject": subject,
        "body": body,
        "findingsUsed": [selected[i - 1].to_wire() for i in cited],
    }
