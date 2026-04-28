"""Merge raw FBref + Wikidata records into canonical Team / Player records.

Matching strategy: name normalization. We strip diacritics, lowercase, and
match. For Wikidata players that don't match an FBref row we drop them
(they're not in the current squad). For FBref players that don't match a
Wikidata record we still emit a Player record using the English name only;
the Arabic translation will fall back to the English name on the frontend.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Iterable

from ..schema import (
    BilingualText,
    Player,
    PlayerSeasonStats,
    Team,
)
from ..sources.fbref import FbrefPlayerRow, FbrefTeam
from ..sources.wikidata import WdClub, WdPlayer
from .slug import to_slug

log = logging.getLogger("dawri.etl.normalize")


def _normalize_name(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def merge_teams(fbref_teams: list[FbrefTeam], wd_clubs: list[WdClub]) -> list[Team]:
    by_norm: dict[str, WdClub] = {
        _normalize_name(c.name_en): c for c in wd_clubs if c.name_en
    }
    out: list[Team] = []
    for ft in fbref_teams:
        norm = _normalize_name(ft.name)
        wc = by_norm.get(norm)
        # Fuzzy: try without "FC", "Saudi", or article prefixes
        if wc is None:
            stripped = re.sub(r"\b(fc|club|saudi|al)\b", "", norm).strip()
            for k, v in by_norm.items():
                if (
                    re.sub(r"\b(fc|club|saudi|al)\b", "", k).strip() == stripped
                    and stripped
                ):
                    wc = v
                    break
        out.append(
            Team(
                id=to_slug(ft.name),
                name=BilingualText(
                    en=ft.name,
                    ar=(wc.name_ar if wc else "") or ft.name,
                ),
                short_name=BilingualText(
                    en=_short_name(ft.name),
                    ar=(wc.name_ar if wc else "") or _short_name(ft.name),
                ),
                fbref_id=ft.fbref_id,
                wikidata_id=wc.qid if wc else None,
                founded=wc.founded_year if wc else None,
                crest_url=wc.logo_url if wc else None,
                sources={
                    "fbref": ft.href,
                    **({"wikidata": f"https://www.wikidata.org/wiki/{wc.qid}"} if wc else {}),
                },
            )
        )
    log.info("merged %d teams", len(out))
    return out


def _short_name(name: str) -> str:
    """Best-effort short name (e.g. 'Al-Hilal SFC' -> 'Al-Hilal')."""
    s = re.sub(r"\b(SFC|FC|SC|Club)\b", "", name).strip()
    return s or name


def _position_bucket(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.upper()
    if "GK" in s:
        return "GK"
    if "DF" in s or "CB" in s or "FB" in s or "WB" in s:
        return "DF"
    if "MF" in s or "DM" in s or "CM" in s or "AM" in s:
        return "MF"
    if "FW" in s or "ST" in s or "WG" in s or "RW" in s or "LW" in s:
        return "FW"
    return None


def merge_players(
    rows: Iterable[tuple[FbrefTeam, FbrefPlayerRow]],
    wd_players: list[WdPlayer],
    teams: list[Team],
) -> list[Player]:
    fbref_id_to_team_slug: dict[str, str] = {}
    for t in teams:
        if t.fbref_id:
            fbref_id_to_team_slug[t.fbref_id] = t.id

    wd_by_norm: dict[str, WdPlayer] = {
        _normalize_name(p.name_en): p for p in wd_players if p.name_en
    }

    out: list[Player] = []
    seen_slugs: set[str] = set()
    for ft, row in rows:
        team_slug = fbref_id_to_team_slug.get(ft.fbref_id)
        wd = wd_by_norm.get(_normalize_name(row.name))
        slug = to_slug(row.name)
        # disambiguate duplicates with team prefix
        if slug in seen_slugs and team_slug:
            slug = f"{slug}-{team_slug}"
        seen_slugs.add(slug)

        out.append(
            Player(
                id=slug,
                name=BilingualText(
                    en=row.name,
                    ar=(wd.name_ar if wd else "") or row.name,
                ),
                team_id=team_slug,
                position=_position_bucket(row.position),
                detailed_position=row.position,
                nationality=BilingualText(
                    en=(wd.nationality_en if wd and wd.nationality_en else (row.nationality or "")),
                    ar=(wd.nationality_ar if wd and wd.nationality_ar else (row.nationality or "")),
                )
                if (row.nationality or (wd and wd.nationality_en))
                else None,
                birth_date=wd.birth_date if wd else None,
                height_cm=wd.height_cm if wd else None,
                photo_url=wd.photo_url if wd else None,
                fbref_id=row.fbref_id,
                wikidata_id=wd.qid if wd else None,
                season_stats=PlayerSeasonStats(
                    matches=row.matches or 0,
                    starts=row.starts or 0,
                    minutes=row.minutes or 0,
                    goals=row.goals or 0,
                    assists=row.assists or 0,
                    yellow_cards=row.yellow_cards or 0,
                    red_cards=row.red_cards or 0,
                    xg=row.xg,
                    xa=row.xa,
                ),
                sources={
                    **({"fbref": row.href} if row.href else {}),
                    **({"wikidata": f"https://www.wikidata.org/wiki/{wd.qid}"} if wd else {}),
                },
            )
        )
    log.info("merged %d players", len(out))
    return out
