"""Public website text as typed state for System One (ADR-0090 amendment 2026-10-16).

The CTO decided that public website text may reach the semantic provider: Jev needs the
source text to answer narrow questions well (TypeSafe guidance: "give each question enough
relevant state"), and controlled vocabulary alone left most activities unread. Minimization
still applies (GDPR): contact data never leaves, sentences about people are dropped, and
the text is bounded. Business text (what the organization offers) is what is sent.
"""

from __future__ import annotations

import re

#: Per-field bound, so one long page cannot dominate a batch.
MAX_FIELD_CHARS = 1_800

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
_URL = re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE)
#: Phone-like runs: optional +, then 7 or more digits with common separators.
_PHONE = re.compile(r"\+?\d[\d\s().-]{6,}\d")
#: Sentences about people: roles, honorifics and founding stories (six languages).
_PERSON_SENTENCE = re.compile(
    r"\b(founded by|co-?founder|founder|ceo|cto|cfo|managing director|our team|meet the|"
    r"fundad[ao] por|fundador(a|es)?|cofundador|director(a)? general|gerente|nuestro equipo|"
    r"fondateur|fond[ée]e? par|g[ée]rant|notre [ée]quipe|gegr[üu]ndet von|gr[üu]nder|"
    r"gesch[äa]ftsf[üu]hrer|unser team|fondat[ao] da|fondatore|il nostro team|"
    r"a nossa equipa)\b"
    r"|\b(mr|mrs|ms|dr|dra|sr|sra|mme|sig|dott|herr|frau)\s+[A-ZÁÉÍÓÚÄÖÜÑ]",
    re.IGNORECASE,
)
#: An honorific's dot is not the end of a sentence ("Dr. Ana García").
_HONORIFIC_DOT = re.compile(r"\b(Mr|Mrs|Ms|Dr|Dra|Sr|Sra|Mme|Sig|Dott)\.\s", re.IGNORECASE)
_SENTENCE = re.compile(r"[^.!?\n]+[.!?]?")


def public_text(text: str, limit: int = MAX_FIELD_CHARS) -> str:
    """Business text from a public page: contact data removed, people's sentences dropped."""
    cleaned = text or ""
    for pattern in (_EMAIL, _URL, _PHONE):
        cleaned = pattern.sub(" ", cleaned)
    cleaned = _HONORIFIC_DOT.sub(lambda m: m.group(1) + " ", cleaned)
    kept = [
        sentence.strip()
        for sentence in _SENTENCE.findall(cleaned)
        if sentence.strip() and not _PERSON_SENTENCE.search(sentence)
    ]
    return re.sub(r"\s{2,}", " ", " ".join(kept)).strip()[:limit]
