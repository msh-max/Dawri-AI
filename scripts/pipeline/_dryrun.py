"""Offline dry-run with synthetic data.

Validates that the schema, slug, and merge logic all work end-to-end without
needing network access. Useful for CI smoke tests and local development on
machines that can't reach FBref/Wikidata.

Usage: python -m scripts.pipeline._dryrun
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .etl.normalize import merge_fixtures, merge_players, merge_teams
from .predict import predict_upcoming
from .schema import SeasonSnapshot, to_jsonable
from .sources.fbref import FbrefFixtureRow, FbrefPlayerRow, FbrefTeam
from .sources.wikidata import WdClub, WdPlayer

logging.basicConfig(level=logging.INFO, format="%(message)s")


SYNTHETIC_FBREF_TEAMS = [
    FbrefTeam(
        fbref_id="aaaaaaaa",
        name="Al-Hilal",
        href="https://fbref.com/en/squads/aaaaaaaa/Al-Hilal",
    ),
    FbrefTeam(
        fbref_id="bbbbbbbb",
        name="Al-Nassr",
        href="https://fbref.com/en/squads/bbbbbbbb/Al-Nassr",
    ),
]

SYNTHETIC_FBREF_PLAYERS = [
    (
        SYNTHETIC_FBREF_TEAMS[0],
        FbrefPlayerRow(
            fbref_id="p1111111",
            name="Salem Al-Dawsari",
            href="https://fbref.com/en/players/p1111111/Salem-Al-Dawsari",
            nationality="ksa SAU",
            position="MF,FW",
            age="33",
            matches=22,
            starts=20,
            minutes=1820,
            goals=12,
            assists=8,
            yellow_cards=3,
            red_cards=0,
            xg=9.4,
            xa=6.8,
        ),
    ),
    (
        SYNTHETIC_FBREF_TEAMS[1],
        FbrefPlayerRow(
            fbref_id="p2222222",
            name="Cristiano Ronaldo",
            href="https://fbref.com/en/players/p2222222/Cristiano-Ronaldo",
            nationality="por POR",
            position="FW",
            age="40",
            matches=24,
            starts=24,
            minutes=2160,
            goals=28,
            assists=4,
            yellow_cards=5,
            red_cards=1,
            xg=22.1,
            xa=3.7,
        ),
    ),
]

SYNTHETIC_WD_CLUBS = [
    WdClub(
        qid="Q221054",
        name_en="Al-Hilal",
        name_ar="نادي الهلال",
        founded_year=1957,
        logo_url="https://commons.wikimedia.org/wiki/al-hilal-crest.svg",
    ),
    WdClub(
        qid="Q221055",
        name_en="Al-Nassr",
        name_ar="نادي النصر",
        founded_year=1955,
        logo_url=None,
    ),
]

SYNTHETIC_WD_PLAYERS = [
    WdPlayer(
        qid="Q1234567",
        name_en="Salem Al-Dawsari",
        name_ar="سالم الدوسري",
        birth_date="1991-08-19",
        photo_url="https://commons.wikimedia.org/wiki/al-dawsari.jpg",
        height_cm=171,
        nationality_en="Saudi Arabia",
        nationality_ar="المملكة العربية السعودية",
    ),
    WdPlayer(
        qid="Q11571",
        name_en="Cristiano Ronaldo",
        name_ar="كريستيانو رونالدو",
        birth_date="1985-02-05",
        photo_url="https://commons.wikimedia.org/wiki/ronaldo.jpg",
        height_cm=187,
        nationality_en="Portugal",
        nationality_ar="البرتغال",
    ),
]


SYNTHETIC_FBREF_FIXTURES = [
    FbrefFixtureRow(
        fbref_match_id="abcd1234",
        date="2025-08-29",
        kickoff="17:00",
        matchweek=1,
        home_team_name="Al-Hilal",
        away_team_name="Al-Nassr",
        venue="Kingdom Arena",
        home_goals=2,
        away_goals=1,
        home_xg=2.4,
        away_xg=1.6,
    ),
    FbrefFixtureRow(
        fbref_match_id=None,
        date="2025-09-12",
        kickoff="18:00",
        matchweek=2,
        home_team_name="Al-Nassr",
        away_team_name="Al-Hilal",
        venue=None,
        home_goals=None,
        away_goals=None,
        home_xg=None,
        away_xg=None,
    ),
]


def main() -> int:
    teams = merge_teams(SYNTHETIC_FBREF_TEAMS, SYNTHETIC_WD_CLUBS)
    players = merge_players(SYNTHETIC_FBREF_PLAYERS, SYNTHETIC_WD_PLAYERS, teams)
    fixtures = merge_fixtures(SYNTHETIC_FBREF_FIXTURES, teams)
    predictions = predict_upcoming(teams, fixtures)

    snap = SeasonSnapshot(
        league_id="spl-saudi-pro-league",
        season="2025-26",
        generated_at=datetime.now(timezone.utc).isoformat(),
        teams=teams,
        players=players,
        fixtures=fixtures,
        predictions=predictions,
    )

    out_dir = Path("data-out-dryrun")
    out_dir.mkdir(exist_ok=True)
    payload = to_jsonable(snap)
    (out_dir / "season.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Sanity assertions
    assert len(teams) == 2, f"expected 2 teams, got {len(teams)}"
    assert len(players) == 2, f"expected 2 players, got {len(players)}"
    assert len(fixtures) == 2, f"expected 2 fixtures, got {len(fixtures)}"

    fx_finished = next(f for f in fixtures if f.status == "finished")
    assert fx_finished.home_team_id == "al-hilal"
    assert fx_finished.away_team_id == "al-nassr"
    assert fx_finished.home_goals == 2
    assert fx_finished.away_xg == 1.6

    fx_scheduled = next(f for f in fixtures if f.status == "scheduled")
    assert fx_scheduled.matchweek == 2
    assert fx_scheduled.home_goals is None

    # One prediction was emitted for the scheduled fixture
    assert len(predictions) == 1
    pred = predictions[0]
    assert pred.fixture_id == fx_scheduled.id
    total = pred.home_win_prob + pred.draw_prob + pred.away_win_prob
    assert 0.99 <= total <= 1.01, f"W/D/L probs do not sum to 1: {total}"
    assert 0 < pred.home_xg_predicted < 6
    assert 0 < pred.away_xg_predicted < 6
    assert len(pred.contributions) >= 1

    al_hilal = next(t for t in teams if t.id == "al-hilal")
    assert al_hilal.name.ar == "نادي الهلال"
    assert al_hilal.founded == 1957

    salem = next(p for p in players if p.id == "salem-al-dawsari")
    assert salem.name.ar == "سالم الدوسري"
    assert salem.team_id == "al-hilal"
    assert salem.position == "MF"  # MF,FW → bucket MF
    assert salem.season_stats.goals == 12
    assert salem.season_stats.xg == 9.4

    ronaldo = next(p for p in players if p.id == "cristiano-ronaldo")
    assert ronaldo.team_id == "al-nassr"
    assert ronaldo.position == "FW"
    assert ronaldo.height_cm == 187

    print("OK — dry-run produced", out_dir / "season.json")
    print(
        f"  {len(teams)} teams, {len(players)} players, {len(fixtures)} fixtures"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
