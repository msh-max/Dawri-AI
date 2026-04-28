"""FBref scraper.

FBref (https://fbref.com) is the most complete free source of advanced
football stats. It powers Stats Perform / Opta data and offers SPL coverage
under competition id 70.

Quirk worth knowing: FBref hides most stats tables inside HTML comments
(<!-- ... -->) to deter scraping. We strip the comment markers before
parsing. This is fair use under their non-commercial terms with attribution.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Iterator

from bs4 import BeautifulSoup, Comment

from ..cache import HttpCache

log = logging.getLogger("dawri.sources.fbref")

# Saudi Pro League competition id on FBref
COMP_ID = 70
COMP_SLUG = "Saudi-Professional-League"
BASE_URL = "https://fbref.com"


@dataclass
class FbrefTeam:
    fbref_id: str
    name: str
    href: str  # absolute URL to the team page


@dataclass
class FbrefPlayerRow:
    fbref_id: str | None
    name: str
    href: str | None
    nationality: str | None
    position: str | None
    age: str | None
    matches: int | None
    starts: int | None
    minutes: int | None
    goals: int | None
    assists: int | None
    yellow_cards: int | None
    red_cards: int | None
    xg: float | None
    xa: float | None


def _strip_comments(html: str) -> str:
    """FBref wraps optional tables in HTML comments. Reveal them."""
    soup = BeautifulSoup(html, "lxml")
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        # Replace the comment with its content if it looks like a table fragment
        if "<table" in str(c):
            c.replace_with(BeautifulSoup(str(c), "lxml"))
    return str(soup)


def _parse_int(s: str | None) -> int | None:
    if s is None:
        return None
    s = s.strip().replace(",", "")
    if not s or s == "-":
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _parse_float(s: str | None) -> float | None:
    if s is None:
        return None
    s = s.strip().replace(",", "")
    if not s or s == "-":
        return None
    try:
        return float(s)
    except ValueError:
        return None


_FBREF_TEAM_HREF_RE = re.compile(r"^/en/squads/([0-9a-f]{8})/")
_FBREF_PLAYER_HREF_RE = re.compile(r"^/en/players/([0-9a-f]{8})/")


def list_teams(cache: HttpCache) -> list[FbrefTeam]:
    """Scrape the season standings table for the list of SPL teams."""
    url = f"{BASE_URL}/en/comps/{COMP_ID}/{COMP_SLUG}-Stats"
    res = cache.get(url)
    if res.status_code != 200:
        log.warning("FBref comp page returned %s", res.status_code)
        return []
    html = _strip_comments(res.text)
    soup = BeautifulSoup(html, "lxml")

    teams: dict[str, FbrefTeam] = {}
    # Standings table id is "results<season>{COMP_ID}1_overall" or similar.
    # Be permissive: find every link that matches a team URL.
    for a in soup.select('a[href^="/en/squads/"]'):
        href = a.get("href") or ""
        match = _FBREF_TEAM_HREF_RE.match(href)
        if not match:
            continue
        fbref_id = match.group(1)
        name = a.get_text(strip=True)
        if not name or len(name) < 2:
            continue
        # de-dupe by fbref_id
        if fbref_id not in teams:
            teams[fbref_id] = FbrefTeam(
                fbref_id=fbref_id,
                name=name,
                href=f"{BASE_URL}{href}",
            )
    log.info("FBref: found %d teams", len(teams))
    return list(teams.values())


def list_players_for_team(
    cache: HttpCache, team: FbrefTeam
) -> list[FbrefPlayerRow]:
    """Scrape the standard stats table from a team's squad page."""
    res = cache.get(team.href)
    if res.status_code != 200:
        log.warning(
            "FBref team page %s returned %s", team.fbref_id, res.status_code
        )
        return []
    html = _strip_comments(res.text)
    soup = BeautifulSoup(html, "lxml")

    # The standard stats table has id="stats_standard_<comp>" and contains
    # one row per player. The exact id varies, so we scan tables.
    tables = soup.select('table[id^="stats_standard_"]')
    if not tables:
        log.warning("FBref: no standard stats table on %s", team.href)
        return []
    table = tables[0]

    rows: list[FbrefPlayerRow] = []
    for tr in table.select("tbody > tr"):
        if "thead" in (tr.get("class") or []):
            continue
        cells = {
            (td.get("data-stat") or ""): td for td in tr.find_all(["td", "th"])
        }
        name_cell = cells.get("player")
        if name_cell is None:
            continue
        a = name_cell.find("a")
        href = a.get("href") if a else None
        fbref_id: str | None = None
        if href:
            m = _FBREF_PLAYER_HREF_RE.match(href)
            if m:
                fbref_id = m.group(1)
        name = name_cell.get_text(strip=True)
        if not name:
            continue

        rows.append(
            FbrefPlayerRow(
                fbref_id=fbref_id,
                name=name,
                href=f"{BASE_URL}{href}" if href else None,
                nationality=_text_or_none(cells.get("nationality")),
                position=_text_or_none(cells.get("position")),
                age=_text_or_none(cells.get("age")),
                matches=_parse_int(_text_or_none(cells.get("games"))),
                starts=_parse_int(_text_or_none(cells.get("games_starts"))),
                minutes=_parse_int(_text_or_none(cells.get("minutes"))),
                goals=_parse_int(_text_or_none(cells.get("goals"))),
                assists=_parse_int(_text_or_none(cells.get("assists"))),
                yellow_cards=_parse_int(
                    _text_or_none(cells.get("cards_yellow"))
                ),
                red_cards=_parse_int(_text_or_none(cells.get("cards_red"))),
                xg=_parse_float(_text_or_none(cells.get("xg"))),
                xa=_parse_float(_text_or_none(cells.get("xg_assist"))),
            )
        )
    log.info("FBref: %s → %d players", team.name, len(rows))
    return rows


def _text_or_none(cell) -> str | None:
    if cell is None:
        return None
    txt = cell.get_text(strip=True)
    return txt or None


def iter_all_player_rows(cache: HttpCache) -> Iterator[tuple[FbrefTeam, FbrefPlayerRow]]:
    """Yield (team, player_row) for the entire SPL."""
    teams = list_teams(cache)
    for team in teams:
        for row in list_players_for_team(cache, team):
            yield team, row
