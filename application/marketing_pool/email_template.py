"""The marketing pool email: the Observer at work, the findings with their sources, one CTA.

Email-client safe by construction: table layout, inline styles, PNG images hosted on the
public site (no SVG, no web fonts required), a plain-text alternative carrying the same
words, light colour scheme only. Every string is escaped; findings keep their epistemic
state visible (an OBSERVED fact never looks like a POTENTIAL one).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from html import escape
from urllib.parse import urlsplit

INK = "#141a2b"
TEXT = "#2b3140"
MUTED = "#687078"
LINE = "#e3e6ec"
PAPER = "#f4f5f8"
BLUE = "#1846d1"
SOFT_BLUE = "#eef2fc"
POTENTIAL = "#8a7fb0"
SERIF = "Georgia, 'Times New Roman', serif"
SANS = "'Helvetica Neue', Helvetica, Arial, sans-serif"

LABELS: dict[str, dict[str, str]] = {
    "es": {
        "eyebrow": "Lectura independiente", "section": "Lo que hemos observado",
        "cta": "Ver la lectura completa", "source": "Fuente", "observed": "observado",
        "OBSERVED": "Observado", "DECLARED": "Declarado por su web",
        "POTENTIAL": "Potencial · a confirmar", "signoff": "Un saludo,",
        "presence": "Presencia", "reputation": "Reputación", "value": "Valor",
        "markets": "Mercados", "relationships": "Relaciones", "demand": "Demanda",
        "economics": "Economía", "organization": "Organización", "context": "Contexto",
    },
    "en": {
        "eyebrow": "Independent reading", "section": "What we observed",
        "cta": "See the full reading", "source": "Source", "observed": "observed",
        "OBSERVED": "Observed", "DECLARED": "Declared by its website",
        "POTENTIAL": "Potential · to confirm", "signoff": "Best regards,",
        "presence": "Presence", "reputation": "Reputation", "value": "Value",
        "markets": "Markets", "relationships": "Relationships", "demand": "Demand",
        "economics": "Economics", "organization": "Organization", "context": "Context",
    },
    "fr": {
        "eyebrow": "Lecture indépendante", "section": "Ce que nous avons observé",
        "cta": "Voir la lecture complète", "source": "Source", "observed": "observé",
        "OBSERVED": "Observé", "DECLARED": "Déclaré par son site",
        "POTENTIAL": "Potentiel · à confirmer", "signoff": "Bien cordialement,",
        "presence": "Présence", "reputation": "Réputation", "value": "Valeur",
        "markets": "Marchés", "relationships": "Relations", "demand": "Demande",
        "economics": "Économie", "organization": "Organisation", "context": "Contexte",
    },
    "de": {
        "eyebrow": "Unabhängige Auswertung", "section": "Was wir beobachtet haben",
        "cta": "Vollständige Auswertung ansehen", "source": "Quelle", "observed": "beobachtet",
        "OBSERVED": "Beobachtet", "DECLARED": "Von der Website erklärt",
        "POTENTIAL": "Potenziell · zu bestätigen", "signoff": "Mit freundlichen Grüßen",
        "presence": "Präsenz", "reputation": "Reputation", "value": "Wert",
        "markets": "Märkte", "relationships": "Beziehungen", "demand": "Nachfrage",
        "economics": "Wirtschaft", "organization": "Organisation", "context": "Kontext",
    },
    "it": {
        "eyebrow": "Lettura indipendente", "section": "Cosa abbiamo osservato",
        "cta": "Vedi la lettura completa", "source": "Fonte", "observed": "osservato",
        "OBSERVED": "Osservato", "DECLARED": "Dichiarato dal suo sito",
        "POTENTIAL": "Potenziale · da confermare", "signoff": "Cordiali saluti,",
        "presence": "Presenza", "reputation": "Reputazione", "value": "Valore",
        "markets": "Mercati", "relationships": "Relazioni", "demand": "Domanda",
        "economics": "Economia", "organization": "Organizzazione", "context": "Contesto",
    },
    "pt": {
        "eyebrow": "Leitura independente", "section": "O que observámos",
        "cta": "Ver a leitura completa", "source": "Fonte", "observed": "observado",
        "OBSERVED": "Observado", "DECLARED": "Declarado pelo seu site",
        "POTENTIAL": "Potencial · a confirmar", "signoff": "Com os melhores cumprimentos,",
        "presence": "Presença", "reputation": "Reputação", "value": "Valor",
        "markets": "Mercados", "relationships": "Relações", "demand": "Procura",
        "economics": "Economia", "organization": "Organização", "context": "Contexto",
    },
}  # fmt: skip


#: "{role} of Axignal.com" as each language says it.
_ROLE_OF = {
    "es": "{role} de Axignal.com", "en": "{role}, Axignal.com", "fr": "{role} d'Axignal.com",
    "de": "{role}, Axignal.com", "it": "{role} di Axignal.com", "pt": "{role} da Axignal.com",
}  # fmt: skip


def signature_role(language: str, role: str | None) -> str | None:
    return None if not role else _ROLE_OF.get(language, _ROLE_OF["en"]).format(role=role)


def _labels(language: str) -> dict[str, str]:
    return LABELS.get(language, LABELS["en"])


def _paragraphs(body: str) -> list[str]:
    blocks = [b.strip() for b in body.replace("\r\n", "\n").split("\n\n")]
    return [b for b in blocks if b]


def _finding(item: Mapping[str, object], labels: Mapping[str, str]) -> str:
    state = str(item.get("state") or "")
    potential = state == "POTENTIAL"
    accent = POTENTIAL if potential else BLUE
    border = f"border-left:3px {'dashed' if potential else 'solid'} {accent};"
    family = labels.get(str(item.get("family") or ""), str(item.get("family") or ""))
    source = str(item.get("source") or "")
    host = (urlsplit(source).hostname or "").removeprefix("www.")
    source_html = (
        f'<a href="{escape(source, quote=True)}" style="color:{MUTED};text-decoration:underline;">'
        f"{escape(host)}</a>"
        if host
        else ""
    )
    meta = escape(labels.get(state, state))
    if source_html:
        meta += f" &nbsp;·&nbsp; {escape(labels['source'])}: {source_html}"
    return (
        f'<tr><td style="padding:0 0 12px 0;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:#ffffff;border:1px solid {LINE};border-radius:10px;{border}">'
        f'<tr><td style="padding:14px 16px 14px 16px;">'
        f'<div style="font-family:{SANS};font-size:11px;letter-spacing:1.4px;'
        f'text-transform:uppercase;color:{accent};font-weight:bold;">{escape(family)}</div>'
        f'<div style="font-family:{SANS};font-size:15px;line-height:1.5;color:{INK};'
        f'padding-top:4px;">{escape(str(item.get("statement") or ""))}</div>'
        f'<div style="font-family:{SANS};font-size:12px;color:{MUTED};padding-top:6px;">'
        f"{meta}</div></td></tr></table></td></tr>"
    )


def render_html(
    *,
    language: str,
    domain: str,
    studied_on: str | None,
    subject: str,
    body: str,
    findings: Sequence[Mapping[str, object]],
    reading_url: str,
    unsubscribe_url: str,
    sender_name: str,
    legal_text: str,
    sender_role: str | None = None,
    asset_origin: str,
) -> str:
    labels = _labels(language)
    origin = asset_origin.rstrip("/")
    preheader = escape(_paragraphs(body)[0][:140] if _paragraphs(body) else subject)
    eyebrow = labels["eyebrow"]
    subject_line = domain + (f" · {labels['observed']} {studied_on[:10]}" if studied_on else "")
    paragraphs = "".join(
        f'<p style="margin:0 0 16px 0;font-family:{SANS};font-size:16px;line-height:1.6;'
        f'color:{TEXT};">{escape(p).replace(chr(10), "<br>")}</p>'
        for p in _paragraphs(body)
    )
    cards = "".join(_finding(item, labels) for item in findings[:4])
    role = signature_role(language, sender_role)
    role_html = f'<br><span style="color:{MUTED};">{escape(role)}</span>' if role else ""
    legal = escape(legal_text).replace("\n", "<br>")
    return f"""<!doctype html>
<html lang="{escape(language)}" xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>{escape(subject)}</title>
<style>
@media (max-width:620px) {{
  .shell {{ width:100% !important; border-radius:0 !important; }}
  .pad {{ padding-left:20px !important; padding-right:20px !important; }}
  .hero-text, .hero-art {{ display:block !important; width:100% !important; text-align:left !important; }}
  .hero-art img {{ width:150px !important; margin:8px 0 0 0 !important; }}
  .title {{ font-size:25px !important; }}
}}
a {{ color:{BLUE}; }}
</style>
</head>
<body style="margin:0;padding:0;background:{PAPER};-webkit-text-size-adjust:100%;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:{PAPER};">{preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAPER};">
<tr><td align="center" style="padding:28px 12px;">
<table role="presentation" class="shell" width="600" cellpadding="0" cellspacing="0"
 style="width:600px;max-width:600px;background:#ffffff;border:1px solid {LINE};border-radius:16px;">
<tr><td class="pad" style="padding:24px 36px 0 36px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
    <td style="vertical-align:middle;">
      <img src="{origin}/email/logo-440.png" width="120" height="35" alt="Axignal"
       style="display:block;width:120px;height:auto;border:0;">
    </td>
  </tr></table>
  <div style="height:1px;background:{LINE};margin:18px 0 0 0;line-height:1px;">&nbsp;</div>
</td></tr>
<tr><td class="pad" style="padding:22px 36px 4px 36px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
    <td class="hero-text" style="vertical-align:middle;width:62%;">
      <div style="font-family:{SANS};font-size:11px;letter-spacing:1.6px;text-transform:uppercase;
       color:{BLUE};font-weight:bold;">{escape(eyebrow)}</div>
      <div style="font-family:{SANS};font-size:12px;color:{MUTED};padding-top:3px;">{escape(subject_line)}</div>
      <h1 class="title" style="margin:10px 0 0 0;font-family:{SERIF};font-weight:normal;
       font-size:29px;line-height:1.2;color:{INK};">{escape(subject)}</h1>
    </td>
    <td class="hero-art" align="right" style="vertical-align:bottom;width:38%;">
      <img src="{origin}/email/observer-laptop-480.png" width="180" alt=""
       style="display:block;width:180px;max-width:100%;height:auto;border:0;margin-left:auto;">
    </td>
  </tr></table>
</td></tr>
<tr><td class="pad" style="padding:18px 36px 4px 36px;">{paragraphs}</td></tr>
<tr><td class="pad" style="padding:4px 36px 8px 36px;">
  <div style="font-family:{SANS};font-size:11px;letter-spacing:1.6px;text-transform:uppercase;
   color:{MUTED};padding:0 0 12px 0;">{escape(labels["section"])}</div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{cards}</table>
</td></tr>
<tr><td class="pad" style="padding:12px 36px 8px 36px;">
  <table role="presentation" cellpadding="0" cellspacing="0"><tr>
    <td style="background:{BLUE};border-radius:999px;">
      <a href="{escape(reading_url, quote=True)}" style="display:inline-block;padding:13px 26px;
       font-family:{SANS};font-size:15px;font-weight:bold;color:#ffffff;text-decoration:none;">
       {escape(labels["cta"])} &rarr;</a>
    </td>
  </tr></table>
</td></tr>
<tr><td class="pad" style="padding:22px 36px 30px 36px;">
  <p style="margin:0;font-family:{SANS};font-size:15px;line-height:1.6;color:{TEXT};">
   {escape(labels["signoff"])}<br><strong style="color:{INK};">{escape(sender_name)}</strong>{role_html}</p>
  <a href="{origin}/" style="display:inline-block;margin-top:14px;text-decoration:none;">
   <img src="{origin}/email/logo-440.png" width="132" height="38" alt="Axignal"
    style="display:block;width:132px;height:auto;border:0;"></a>
</td></tr>
</table>
<table role="presentation" width="600" class="shell" cellpadding="0" cellspacing="0"
 style="width:600px;max-width:600px;">
<tr><td class="pad" style="padding:18px 36px 8px 36px;font-family:{SANS};font-size:11px;
 line-height:1.6;color:{MUTED};">{legal}<br>
 <a href="{escape(unsubscribe_url, quote=True)}" style="color:{MUTED};">{escape(unsubscribe_url)}</a>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""
