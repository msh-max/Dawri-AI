"""Wikidata enrichment.

Wikidata gives us the cleanest source of bilingual labels (Arabic + English),
biographical data, and Commons photo URLs for SPL clubs and players. We hit
the public SPARQL endpoint with two queries: one for clubs that participate
in the Saudi Pro League, and one for players linked to those clubs.

Free, well-licensed, attribution-friendly.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from ..cache import HttpCache

log = logging.getLogger("dawri.sources.wikidata")

SPARQL_URL = "https://query.wikidata.org/sparql"

# The SPL entity has been renamed multiple times on Wikidata (Saudi Premier
# League → Saudi Professional League → Roshn Saudi League). Different clubs
# point P118 at different historical entities. Union over the known set.
SPL_QIDS: tuple[str, ...] = (
    "Q221054",   # Saudi Professional League (legacy main entity)
    "Q23950",    # Saudi Premier League / earlier rebrand
    "Q104954",   # Saudi Pro League (alt)
    "Q15978525", # Roshn Saudi League (current sponsor name)
)
# Used by `to_jsonable` callers / logging only; first entry stays canonical.
SPL_QID = SPL_QIDS[0]

_VALUES_BLOCK = " ".join(f"wd:{q}" for q in SPL_QIDS)

CLUBS_QUERY = f"""
SELECT DISTINCT ?club ?clubLabel ?clubLabelAr ?founded ?logo WHERE {{
  VALUES ?league {{ {_VALUES_BLOCK} }}
  ?club wdt:P118 ?league .
  OPTIONAL {{ ?club wdt:P571 ?founded }}
  OPTIONAL {{ ?club wdt:P154 ?logo }}
  OPTIONAL {{ ?club rdfs:label ?clubLabelAr FILTER (lang(?clubLabelAr) = "ar") }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
"""

PLAYERS_QUERY = f"""
SELECT DISTINCT ?player ?playerLabel ?playerLabelAr ?dob ?image ?heightCm ?footLabel ?nationalityLabel ?nationalityLabelAr WHERE {{
  VALUES ?league {{ {_VALUES_BLOCK} }}
  ?player wdt:P54 ?club .
  ?club wdt:P118 ?league .
  OPTIONAL {{ ?player wdt:P569 ?dob }}
  OPTIONAL {{ ?player wdt:P18 ?image }}
  OPTIONAL {{ ?player wdt:P2048 ?heightCm }}
  OPTIONAL {{ ?player wdt:P741 ?foot }}
  OPTIONAL {{ ?player wdt:P27 ?nationality }}
  OPTIONAL {{ ?player rdfs:label ?playerLabelAr FILTER (lang(?playerLabelAr) = "ar") }}
  OPTIONAL {{ ?nationality rdfs:label ?nationalityLabelAr FILTER (lang(?nationalityLabelAr) = "ar") }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT 3000
"""


@dataclass
class WdClub:
    qid: str
    name_en: str
    name_ar: str | None
    founded_year: int | None
    logo_url: str | None


@dataclass
class WdPlayer:
    qid: str
    name_en: str
    name_ar: str | None
    birth_date: str | None
    photo_url: str | None
    height_cm: int | None
    nationality_en: str | None
    nationality_ar: str | None


def _qid_from_uri(uri: str) -> str:
    return uri.rsplit("/", 1)[-1]


def _query(cache: HttpCache, sparql: str) -> dict:
    """Run a SPARQL query, returning the parsed JSON bindings block."""
    res = cache.get(
        SPARQL_URL,
        params={"query": sparql, "format": "json"},
    )
    if res.status_code != 200:
        log.warning("Wikidata SPARQL returned %s", res.status_code)
        return {"results": {"bindings": []}}
    try:
        return json.loads(res.text)
    except json.JSONDecodeError as e:
        log.warning("Wikidata SPARQL parse error: %s", e)
        return {"results": {"bindings": []}}


def fetch_clubs(cache: HttpCache) -> list[WdClub]:
    data = _query(cache, CLUBS_QUERY)
    out: list[WdClub] = []
    for b in data.get("results", {}).get("bindings", []):
        qid = _qid_from_uri(b["club"]["value"])
        founded_raw = b.get("founded", {}).get("value")
        founded_year: int | None = None
        if founded_raw:
            try:
                founded_year = int(founded_raw[:4])
            except ValueError:
                pass
        out.append(
            WdClub(
                qid=qid,
                name_en=b.get("clubLabel", {}).get("value", ""),
                name_ar=(b.get("clubLabelAr") or {}).get("value"),
                founded_year=founded_year,
                logo_url=(b.get("logo") or {}).get("value"),
            )
        )
    log.info("Wikidata: %d clubs", len(out))
    return out


def fetch_players(cache: HttpCache) -> list[WdPlayer]:
    data = _query(cache, PLAYERS_QUERY)
    out: dict[str, WdPlayer] = {}
    for b in data.get("results", {}).get("bindings", []):
        qid = _qid_from_uri(b["player"]["value"])
        if qid in out:
            continue
        height_raw = b.get("heightCm", {}).get("value")
        try:
            height_cm = int(float(height_raw)) if height_raw else None
        except ValueError:
            height_cm = None
        dob = b.get("dob", {}).get("value")
        if dob and len(dob) >= 10:
            dob = dob[:10]  # YYYY-MM-DD
        out[qid] = WdPlayer(
            qid=qid,
            name_en=b.get("playerLabel", {}).get("value", ""),
            name_ar=(b.get("playerLabelAr") or {}).get("value"),
            birth_date=dob,
            photo_url=(b.get("image") or {}).get("value"),
            height_cm=height_cm,
            nationality_en=(b.get("nationalityLabel") or {}).get("value"),
            nationality_ar=(b.get("nationalityLabelAr") or {}).get("value"),
        )
    log.info("Wikidata: %d players", len(out))
    return list(out.values())
