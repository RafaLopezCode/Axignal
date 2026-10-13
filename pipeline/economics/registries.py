"""Official business registers: accounts and size from the register itself, per country.

France (INSEE/RNE via recherche-entreprises.api.gouv.fr, Etalab open licence), Norway
(Brønnøysund registers, NLOD), the United States (SEC EDGAR XBRL company facts, public
domain) and the United Kingdom (Companies House, Open Government Licence; needs a free
API key). Read only by an exact register identifier, never by name; cached per identifier
(accounts change yearly). A register that refuses or times out leaves the facts unknown.
"""

from __future__ import annotations

import base64
import json
import sqlite3
import urllib.request
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

USER_AGENT = "AXIGNAL/1.0 economic-observation contact@axignal.com"
Fetch = Callable[[str, Mapping[str, str]], Any]

#: INSEE "tranche d'effectif salarié" codes → employee range.
FR_EMPLOYEE_BANDS = {
    "00": "0", "01": "1-2", "02": "3-5", "03": "6-9", "11": "10-19", "12": "20-49",
    "21": "50-99", "22": "100-199", "31": "200-249", "32": "250-499", "41": "500-999",
    "42": "1000-1999", "51": "2000-4999", "52": "5000-9999", "53": "10000+",
}  # fmt: skip
#: Annual-accounts concepts read from SEC XBRL company facts, first present wins per fact.
SEC_TAGS = {
    "revenue": ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                "SalesRevenueNet"),
    "netProfit": ("NetIncomeLoss", "ProfitLoss"),
    "assets": ("Assets",),
}  # fmt: skip


def _urlopen(url: str, headers: Mapping[str, str]) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **headers})
    with urllib.request.urlopen(request, timeout=12) as response:
        return json.loads(response.read(25_000_000))


def _fact(value: object, *, year: str | None = None, unit: str | None = None,
          **extra: object) -> dict[str, object]:  # fmt: skip
    return {"value": value, "year": year, "unit": unit, **extra}


class OfficialRegisters:
    """{register, scheme, id, name, url, facts{name: {value, year, unit}}} per identifier."""

    def __init__(
        self,
        database_path: str | Path,
        *,
        fetch: Fetch = _urlopen,
        companies_house_key: str | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        ttl: timedelta = timedelta(days=30),
    ) -> None:
        self._fetch = fetch
        self._ch_key = companies_house_key
        self._clock = clock
        self._ttl = ttl
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS official_registers (
                    key TEXT PRIMARY KEY, payload TEXT NOT NULL, read_at TEXT NOT NULL)"""
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @property
    def schemes(self) -> tuple[str, ...]:
        return ("SIREN", "ORGNR", "SEC_CIK", *(("COMPANIES_HOUSE",) if self._ch_key else ()))

    def record(self, scheme: str, identifier: str) -> dict[str, object] | None:
        """The register's record for this identifier (cached); None when not found or off."""
        reader = {
            "SIREN": self._france,
            "ORGNR": self._norway,
            "SEC_CIK": self._sec,
            "COMPANIES_HOUSE": self._companies_house if self._ch_key else None,
        }.get(scheme)
        if reader is None:
            return None
        key = f"{scheme}:{identifier}"
        now = self._clock()
        with self._connect() as db:
            row = db.execute(
                "SELECT payload, read_at FROM official_registers WHERE key=?", (key,)
            ).fetchone()
        if row is not None and now - datetime.fromisoformat(row[1]) < self._ttl:
            cached = json.loads(row[0])
            return dict(cached) if cached else None
        payload = reader(identifier)
        if payload is not None:
            payload.update({"scheme": scheme, "id": identifier, "readAt": now.isoformat()})
        with self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO official_registers VALUES (?,?,?)",
                (key, json.dumps(payload), now.isoformat()),
            )
        return payload

    # ---- France: INSEE (Sirene) and RNE through the State's open company search -------
    def _france(self, siren: str) -> dict[str, object] | None:
        found = self._fetch(
            f"https://recherche-entreprises.api.gouv.fr/search?q={siren}&per_page=1", {}
        )
        result = next(
            (r for r in (found or {}).get("results", []) if str(r.get("siren")) == siren), None
        )
        if result is None:
            return None
        facts: dict[str, dict[str, object]] = {}
        finances = result.get("finances") or {}
        if isinstance(finances, Mapping) and finances:
            year = max(finances)
            accounts = finances[year] or {}
            if isinstance(accounts.get("ca"), int | float):
                facts["revenue"] = _fact(accounts["ca"], year=year, unit="EUR")
            if isinstance(accounts.get("resultat_net"), int | float):
                facts["netProfit"] = _fact(accounts["resultat_net"], year=year, unit="EUR")
        band = FR_EMPLOYEE_BANDS.get(str(result.get("tranche_effectif_salarie") or ""))
        if band is not None:
            facts["employeesBand"] = _fact(band, year=result.get("annee_tranche_effectif_salarie"))
        if result.get("categorie_entreprise"):
            facts["sizeCategory"] = _fact(
                result["categorie_entreprise"], year=result.get("annee_categorie_entreprise")
            )
        if result.get("date_creation"):
            facts["inception"] = _fact(str(result["date_creation"])[:4])
        facts["status"] = _fact("ACTIVE" if result.get("etat_administratif") == "A" else "CLOSED")
        if result.get("activite_principale"):
            facts["activity"] = _fact(f"NAF {result['activite_principale']}")
        if isinstance(result.get("nombre_etablissements_ouverts"), int):
            facts["establishments"] = _fact(result["nombre_etablissements_ouverts"])
        return {
            "register": "INSEE / RNE (France)",
            "name": result.get("nom_raison_sociale") or result.get("nom_complet"),
            "url": f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}",
            "rights": "Licence Ouverte / Etalab 2.0",
            "facts": facts,
        }

    # ---- Norway: Enhetsregisteret and Regnskapsregisteret ------------------------------
    def _norway(self, orgnr: str) -> dict[str, object] | None:
        unit = self._fetch(f"https://data.brreg.no/enhetsregisteret/api/enheter/{orgnr}", {})
        if not isinstance(unit, Mapping) or str(unit.get("organisasjonsnummer")) != orgnr:
            return None
        facts: dict[str, dict[str, object]] = {}
        if unit.get("harRegistrertAntallAnsatte") and isinstance(unit.get("antallAnsatte"), int):
            facts["employees"] = _fact(unit["antallAnsatte"])
        if unit.get("stiftelsesdato"):
            facts["inception"] = _fact(str(unit["stiftelsesdato"])[:4])
        industry = unit.get("naeringskode1") or {}
        if industry.get("kode"):
            facts["activity"] = _fact(f"NACE {industry['kode']}", label=industry.get("beskrivelse"))
        facts["status"] = _fact("CLOSED" if unit.get("konkurs") or unit.get("slettedato")
                                else "ACTIVE")  # fmt: skip
        try:
            accounts = self._fetch(
                f"https://data.brreg.no/regnskapsregisteret/regnskap/{orgnr}", {}
            )
        except Exception:  # no filed accounts (or unavailable): size facts stay as they are
            accounts = []
        own = [a for a in accounts or [] if a.get("regnskapstype") == "SELSKAP"] or list(
            accounts or []
        )
        if own:
            latest = max(own, key=lambda a: str((a.get("regnskapsperiode") or {}).get("tilDato")))
            period = str((latest.get("regnskapsperiode") or {}).get("tilDato") or "")[:10]
            currency = str(latest.get("valuta") or "NOK")
            result = latest.get("resultatregnskapResultat") or {}
            income = ((result.get("driftsresultat") or {}).get("driftsinntekter") or {}).get(
                "sumDriftsinntekter"
            )
            if isinstance(income, int | float):
                facts["revenue"] = _fact(income, year=period[:4], unit=currency, period=period)
            if isinstance(result.get("aarsresultat"), int | float):
                facts["netProfit"] = _fact(result["aarsresultat"], year=period[:4],
                                           unit=currency, period=period)  # fmt: skip
            assets = (latest.get("eiendeler") or {}).get("sumEiendeler")
            if isinstance(assets, int | float):
                facts["assets"] = _fact(assets, year=period[:4], unit=currency, period=period)
        return {
            "register": "Brønnøysundregistrene (Norway)",
            "name": unit.get("navn"),
            "url": f"https://data.brreg.no/enhetsregisteret/oppslag/enheter/{orgnr}",
            "rights": "Norwegian Licence for Open Government Data (NLOD)",
            "facts": facts,
        }

    # ---- United States: audited annual reports (10-K) in XBRL --------------------------
    def _sec(self, cik: str) -> dict[str, object] | None:
        number = "".join(c for c in cik if c.isdigit()).zfill(10)
        data = self._fetch(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{number}.json", {})
        gaap = ((data or {}).get("facts") or {}).get("us-gaap") or {}
        facts: dict[str, dict[str, object]] = {}
        for name, tags in SEC_TAGS.items():
            best: dict[str, Any] | None = None
            for tag in tags:
                for row in ((gaap.get(tag) or {}).get("units") or {}).get("USD", []):
                    if row.get("form") != "10-K" or not row.get("end"):
                        continue
                    if name != "assets" and not _annual(row.get("start"), row["end"]):
                        continue
                    if best is None or (row["end"], row.get("filed", "")) > (
                        best["end"],
                        best.get("filed", ""),
                    ):
                        best = row
            if best is not None:
                facts[name] = _fact(best["val"], year=str(best["end"])[:4], unit="USD",
                                    period=best["end"], filing=best.get("accn"))  # fmt: skip
        if not facts:
            return None
        return {
            "register": "SEC EDGAR (United States)",
            "name": (data or {}).get("entityName"),
            "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={number}",
            "rights": "U.S. government work, public domain",
            "facts": facts,
        }

    # ---- United Kingdom: Companies House public data API ------------------------------
    def _companies_house(self, number: str) -> dict[str, object] | None:
        token = base64.b64encode(f"{self._ch_key}:".encode()).decode()
        data = self._fetch(
            f"https://api.company-information.service.gov.uk/company/{number}",
            {"Authorization": f"Basic {token}"},
        )
        if not isinstance(data, Mapping) or str(data.get("company_number")) != number:
            return None
        facts: dict[str, dict[str, object]] = {}
        if data.get("date_of_creation"):
            facts["inception"] = _fact(str(data["date_of_creation"])[:4])
        facts["status"] = _fact("ACTIVE" if data.get("company_status") == "active" else "CLOSED")
        if data.get("sic_codes"):
            facts["activity"] = _fact("SIC " + ", ".join(map(str, data["sic_codes"][:3])))
        last = ((data.get("accounts") or {}).get("last_accounts")) or {}
        if last.get("type"):
            period = str(last.get("made_up_to") or "")[:10] or None
            facts["accountsType"] = _fact(str(last["type"]), year=(period or "")[:4] or None,
                                          period=period)  # fmt: skip
        return {
            "register": "Companies House (United Kingdom)",
            "name": data.get("company_name"),
            "url": f"https://find-and-update.company-information.service.gov.uk/company/{number}",
            "rights": "Open Government Licence v3.0",
            "facts": facts,
        }


def _annual(start: object, end: object) -> bool:
    """A fiscal-year duration (not a quarter): roughly 50 to 54 weeks."""
    try:
        days = (date.fromisoformat(str(end)) - date.fromisoformat(str(start))).days
    except ValueError:
        return False
    return 350 <= days <= 380


def registers_from_env(root: Path, values: Mapping[str, str]) -> OfficialRegisters:
    """Companies House is read only with a key file the operator provides; others are open."""
    key: str | None = None
    filename = values.get("AXIGNAL_COMPANIES_HOUSE_API_KEY_FILE", "").strip()
    if filename:
        path = Path(filename)
        try:
            if path.is_absolute() and 0 < path.stat().st_size <= 512:
                key = path.read_text(encoding="utf-8").strip() or None
        except OSError:
            key = None
    return OfficialRegisters(root / "official-registers.sqlite3", companies_house_key=key)
