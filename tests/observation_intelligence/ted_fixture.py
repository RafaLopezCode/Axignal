"""Offline TED stand-in: TED-shaped notices filtered by the adapter's own expert query.

Notices follow the observed Search API v3 shape (multilingual maps, repeated
code lists, eForms notice types). CPV matching is exact, as an expert query is.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


def _notice(
    number: str,
    kind: str,
    title: str,
    buyer: str,
    places: list[str],
    cpv: list[str],
    published: str,
    deadline: str | None = None,
    winner: str | None = None,
) -> dict[str, Any]:
    notice: dict[str, Any] = {
        "publication-number": number,
        "notice-type": kind,
        "notice-title": {"spa": title, "eng": title},
        "buyer-name": {"spa": [buyer]},
        "classification-cpv": [*cpv, *cpv],
        "place-of-performance": places,
        "publication-date": f"{published}+02:00",
    }
    if deadline:
        notice["deadline-receipt-tender-date-lot"] = [f"{deadline}+02:00"]
    if winner:
        notice["winner-name"] = {"spa": [winner]}
    return notice


CORPUS: tuple[dict[str, Any], ...] = (
    # Spain, open calls matching declared PV/electrical capability codes.
    _notice("700101-2026", "cn-standard", "Instalación fotovoltaica de autoconsumo en edificios municipales",
            "Ayuntamiento de Getafe", ["ESP", "ES300"], ["09332000", "45311000"], "2026-09-28", "2026-10-27"),
    _notice("700102-2026", "cn-standard", "Suministro e instalación de módulos fotovoltaicos en depuradoras",
            "Empresa Municipal de Aguas de Córdoba", ["ESP", "ES613"], ["09331200"], "2026-09-30", "2026-11-03"),
    # Closed call: demand evidence, never an open opportunity.
    _notice("690001-2026", "cn-standard", "Instalación eléctrica en polideportivo",
            "Ayuntamiento de Burgos", ["ESP", "ES412"], ["45310000"], "2026-08-20", "2026-09-15"),
    # Awards revealing concentrated public demand in Comunitat Valenciana (ES52).
    _notice("610001-2026", "can-standard", "Cubiertas solares en colegios públicos",
            "Ayuntamiento de Castelló de la Plana", ["ESP", "ES522"], ["45261215", "45261210"], "2026-06-10",
            winner="Instalaciones Turia SL"),
    _notice("620002-2026", "can-standard", "Autoconsumo fotovoltaico en edificios provinciales",
            "Diputación de Valencia", ["ESP", "ES523"], ["09332000", "45261210"], "2026-07-02",
            winner="Solar Mediterránea SA"),
    _notice("630003-2026", "can-standard", "Plantas fotovoltaicas en instalaciones deportivas",
            "Ayuntamiento de Elche", ["ESP", "ES521"], ["09331200"], "2026-07-21",
            winner="Instalaciones Turia SL"),
    _notice("640004-2026", "can-standard", "Instalación eléctrica en edificio administrativo",
            "Comunidad de Madrid", ["ESP", "ES300"], ["45311000"], "2026-05-11", winner="Electromad SL"),
    # Only reachable through codes revealed by the ES52 awards (roof-covering work).
    _notice("705005-2026", "cn-standard", "Sustitución de cubierta con integración fotovoltaica en mercado municipal",
            "Ayuntamiento de Alicante", ["ESP", "ES521"], ["45261210"], "2026-10-01", "2026-11-10"),
    # France, refrigeration demand for a different Xeed and capability.
    _notice("701010-2026", "cn-standard", "Maintenance des installations frigorifiques du CHU",
            "Centre Hospitalier Universitaire de Rennes", ["FRA", "FRH03"], ["50730000"], "2026-09-25", "2026-10-30"),
    _notice("615020-2026", "can-standard", "Chambres froides pour la cuisine centrale",
            "Ville de Lille", ["FRA", "FRE11"], ["42513000"], "2026-06-15", winner="Froid du Nord SAS"),
)  # fmt: skip

_IN = re.compile(r"([a-z-]+) IN \(([^)]*)\)")
_GTE = re.compile(r"([a-z-]+)>=(\d{8})")


class FixtureTedTransport:
    def __init__(self, corpus: tuple[Mapping[str, Any], ...] = CORPUS) -> None:
        self.corpus = corpus
        self.bodies: list[Mapping[str, Any]] = []

    def post(self, body: Mapping[str, Any]) -> tuple[int, Mapping[str, Any]]:
        self.bodies.append(body)
        query = str(body["query"])
        lists = {name: values.split() for name, values in _IN.findall(query)}
        floors = {name: value for name, value in _GTE.findall(query)}

        def keep(notice: Mapping[str, Any]) -> bool:
            if "classification-cpv" in lists and not set(notice["classification-cpv"]) & set(
                lists["classification-cpv"]
            ):
                return False
            if "place-of-performance" in lists and not any(
                place == wanted or (len(wanted) != 3 and place.startswith(wanted))
                for place in notice["place-of-performance"]
                for wanted in lists["place-of-performance"]
            ):
                return False
            if "notice-type" in lists and notice["notice-type"] not in lists["notice-type"]:
                return False
            for field, floor in floors.items():
                values = notice.get(field)
                values = values if isinstance(values, list) else [values]
                if not any(v and v[:10].replace("-", "") >= floor for v in values):
                    return False
            return True

        hits = sorted(
            (n for n in self.corpus if keep(n)),
            key=lambda n: str(n["publication-date"]),
            reverse=True,
        )
        limit = int(body.get("limit", 20))
        return 200, {"notices": hits[:limit], "totalNoticeCount": len(hits), "timedOut": False}
