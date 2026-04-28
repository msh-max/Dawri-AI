"""Canonical data schema for Dawri AI.

These dataclasses are the single source of truth for the data shape that
flows from scrapers through ETL, into JSON, and gets typed on the frontend
(see src/types/data.ts which mirrors this).

Every record carries a `source` map noting *where* each field came from, so
attribution is preserved end-to-end.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class BilingualText:
    en: str
    ar: str

    def to_dict(self) -> dict[str, str]:
        return {"en": self.en, "ar": self.ar}


@dataclass
class Team:
    """A Saudi Pro League club for a given season."""

    id: str  # stable slug, e.g. "al-hilal"
    name: BilingualText
    short_name: BilingualText
    fbref_id: str | None = None
    wikidata_id: str | None = None  # e.g. "Q221054"
    founded: int | None = None
    city: BilingualText | None = None
    crest_url: str | None = None
    primary_color: str | None = None  # hex, e.g. "#1E4FAD"
    sources: dict[str, str] = field(default_factory=dict)


@dataclass
class PlayerSeasonStats:
    """Aggregated season stats for a player at a given team."""

    matches: int = 0
    starts: int = 0
    minutes: int = 0
    goals: int = 0
    assists: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    xg: float | None = None
    xa: float | None = None
    npxg: float | None = None
    progressive_carries: int | None = None
    progressive_passes: int | None = None
    shots: int | None = None
    shots_on_target: int | None = None
    pass_completion_pct: float | None = None
    tackles: int | None = None
    interceptions: int | None = None
    aerials_won_pct: float | None = None
    save_pct: float | None = None  # GK only
    clean_sheets: int | None = None  # GK only


@dataclass
class Player:
    id: str  # slug, e.g. "salem-al-dawsari"
    name: BilingualText
    team_id: str | None
    position: str | None  # FW, MF, DF, GK
    detailed_position: str | None = None  # e.g. "RW", "CB"
    jersey_number: int | None = None
    nationality: BilingualText | None = None
    birth_date: str | None = None  # ISO YYYY-MM-DD
    height_cm: int | None = None
    foot: str | None = None  # left | right | both
    photo_url: str | None = None
    fbref_id: str | None = None
    wikidata_id: str | None = None
    season_stats: PlayerSeasonStats = field(default_factory=PlayerSeasonStats)
    sources: dict[str, str] = field(default_factory=dict)


@dataclass
class Fixture:
    id: str  # e.g. "2025-08-29-al-hilal-al-nassr"
    date: str  # ISO YYYY-MM-DD
    kickoff: str | None  # ISO datetime UTC
    matchweek: int | None
    home_team_id: str
    away_team_id: str
    venue: BilingualText | None = None
    home_goals: int | None = None
    away_goals: int | None = None
    status: str = "scheduled"  # scheduled | live | finished | postponed
    fbref_match_id: str | None = None
    sources: dict[str, str] = field(default_factory=dict)


@dataclass
class SeasonSnapshot:
    """Top-level container written to disk as season.json."""

    league_id: str
    season: str  # e.g. "2025-26"
    generated_at: str  # ISO datetime
    teams: list[Team]
    players: list[Player]
    fixtures: list[Fixture]


def to_jsonable(obj: Any) -> Any:
    """Recursively convert dataclasses (and BilingualText) to plain dicts."""
    if isinstance(obj, BilingualText):
        return obj.to_dict()
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    return obj
