"""Generate a comprehensive demo SeasonSnapshot.

Produces real-looking SPL data for every page on the site:
  - 18 curated SPL clubs with full bilingual metadata
  - 10 finished matchweeks with Poisson-sampled scorelines (so the
    standings table, leaderboards, and form guides all populate)
  - 4 upcoming matchweeks scheduled for predictions / simulator
  - ~30 marquee SPL players with realistic season stats
  - Match predictions for every upcoming fixture (via the real predict
    engine) and template narratives for each match + scout report

Strengths are calibrated so Al-Hilal / Al-Nassr / Al-Ittihad / Al-Ahli
end up in the top half of the table, smaller clubs in the bottom, and
results are non-trivial (no 100% home wins). Deterministic via a fixed
RNG seed so re-runs produce identical JSON — keeps git diffs sane.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .narrate import narrate_all
from .predict import predict_upcoming
from .schema import (
    BilingualText,
    Fixture,
    MatchEvent,
    Player,
    PlayerSeasonStats,
    SeasonSnapshot,
    Team,
    XgFlowPoint,
    to_jsonable,
)
from .sources.spl_roster import SPL_CLUBS

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("dawri.demo")


# Strengths roughly tracking the modern SPL pecking order.
# Higher = better team. Used to drive xG and finished-match Poisson sampling.
STRENGTHS: dict[str, float] = {
    "al-hilal":   1.85,
    "al-nassr":   1.70,
    "al-ittihad": 1.58,
    "al-ahli":    1.55,
    "al-qadsiah": 1.30,
    "al-shabab":  1.25,
    "al-taawoun": 1.20,
    "al-ettifaq": 1.15,
    "al-khaleej": 1.10,
    "al-fateh":   1.05,
    "damac":      1.00,
    "al-fayha":   0.98,
    "al-riyadh":  0.95,
    "al-wehda":   0.92,
    "al-okhdood": 0.88,
    "al-raed":    0.85,
    "al-najma":   0.80,
    "al-kholood": 0.75,
}

DEFENCE: dict[str, float] = {
    "al-hilal":   0.75,
    "al-nassr":   0.85,
    "al-ittihad": 0.95,
    "al-ahli":    0.92,
    "al-qadsiah": 1.05,
    "al-shabab":  1.05,
    "al-taawoun": 1.10,
    "al-ettifaq": 1.10,
    "al-khaleej": 1.10,
    "al-fateh":   1.12,
    "damac":      1.15,
    "al-fayha":   1.15,
    "al-riyadh":  1.18,
    "al-wehda":   1.20,
    "al-okhdood": 1.25,
    "al-raed":    1.28,
    "al-najma":   1.30,
    "al-kholood": 1.35,
}

HOME_BOOST = 1.18
SEASON = "2025-26"


def _build_teams() -> list[Team]:
    out: list[Team] = []
    for c in SPL_CLUBS:
        out.append(
            Team(
                id=c.slug,
                name=BilingualText(en=c.name_en, ar=c.name_ar),
                short_name=BilingualText(en=c.short_en, ar=c.short_ar),
                wikidata_id=c.wikidata_qid,
                founded=c.founded,
                city=BilingualText(en=c.city_en, ar=c.city_ar),
                primary_color=c.primary_color,
                sources=(
                    {"wikidata": f"https://www.wikidata.org/wiki/{c.wikidata_qid}"}
                    if c.wikidata_qid
                    else {}
                ),
            )
        )
    return out


def _round_robin(team_ids: list[str]) -> list[list[tuple[str, str]]]:
    """Berger-style round-robin scheduler. Returns N-1 rounds of N/2 fixtures."""
    teams = list(team_ids)
    if len(teams) % 2 == 1:
        teams.append("__BYE__")
    n = len(teams)
    rounds: list[list[tuple[str, str]]] = []
    fixed = teams[0]
    rotating = teams[1:]
    for r in range(n - 1):
        round_fixtures: list[tuple[str, str]] = []
        layout = [fixed] + rotating
        for i in range(n // 2):
            home, away = layout[i], layout[n - 1 - i]
            if home == "__BYE__" or away == "__BYE__":
                continue
            # alternate home/away each matchweek so it's not always the same
            if r % 2 == 0:
                round_fixtures.append((home, away))
            else:
                round_fixtures.append((away, home))
        rounds.append(round_fixtures)
        rotating = rotating[1:] + rotating[:1]
    return rounds


def _poisson(mean: float, rng: random.Random) -> int:
    """Knuth's algorithm — fine for SPL-scale means (<5)."""
    L = math.exp(-mean)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= L:
            return k - 1


def _build_fixtures(teams: list[Team], rng: random.Random) -> list[Fixture]:
    team_ids = [t.id for t in teams]
    rounds = _round_robin(team_ids)
    # Use the first 14 matchweeks: 10 finished + 4 upcoming. SPL season opens
    # mid-August; we anchor matchweek 1 to 2025-08-22.
    season_start = date(2025, 8, 22)
    out: list[Fixture] = []
    finished_threshold = 10  # matchweeks 1..10 already played
    for mw_idx, mw in enumerate(rounds[:14], start=1):
        match_date = season_start + timedelta(weeks=mw_idx - 1)
        for home_id, away_id in mw:
            kickoff_iso = f"{match_date.isoformat()}T17:00:00Z"
            home_xg_base = STRENGTHS[home_id] * DEFENCE[away_id] * HOME_BOOST
            away_xg_base = STRENGTHS[away_id] * DEFENCE[home_id]
            if mw_idx <= finished_threshold:
                # add a little noise so xg differs from goals
                home_xg = round(max(0.1, rng.gauss(home_xg_base, 0.4)), 2)
                away_xg = round(max(0.1, rng.gauss(away_xg_base, 0.4)), 2)
                home_g = _poisson(home_xg_base, rng)
                away_g = _poisson(away_xg_base, rng)
                status = "finished"
            else:
                home_xg = None
                away_xg = None
                home_g = None
                away_g = None
                status = "scheduled"

            # Cap absurd scorelines for plausibility.
            if home_g is not None:
                home_g = min(home_g, 6)
                away_g = min(away_g, 6)

            home_t = next(t for t in teams if t.id == home_id)

            events: list[MatchEvent] = []
            xg_flow: list[XgFlowPoint] = []
            if status == "finished":
                # Sprinkle a goal event per goal so match pages look alive.
                for i in range(home_g or 0):
                    minute = 5 + int(80 * rng.random())
                    events.append(
                        MatchEvent(minute=minute, team_id=home_id, type="goal")
                    )
                for i in range(away_g or 0):
                    minute = 5 + int(80 * rng.random())
                    events.append(
                        MatchEvent(minute=minute, team_id=away_id, type="goal")
                    )
                events.sort(key=lambda e: e.minute)
                # 5-point xG flow chart
                for minute in (15, 30, 60, 75, 90):
                    xg_flow.append(
                        XgFlowPoint(
                            minute=minute,
                            home_xg=round((home_xg or 0) * minute / 90.0, 2),
                            away_xg=round((away_xg or 0) * minute / 90.0, 2),
                        )
                    )

            out.append(
                Fixture(
                    id=f"{match_date.isoformat()}-{home_id}-vs-{away_id}",
                    date=match_date.isoformat(),
                    kickoff=kickoff_iso,
                    matchweek=mw_idx,
                    home_team_id=home_id,
                    away_team_id=away_id,
                    venue=home_t.city,
                    home_goals=home_g,
                    away_goals=away_g,
                    home_xg=home_xg,
                    away_xg=away_xg,
                    status=status,
                    events=events,
                    xg_flow=xg_flow,
                    sources={},
                )
            )
    return out


# Hand-curated marquee players (real, current-ish SPL stars) spread across
# the top clubs. Stats are illustrative — calibrated to feel plausible
# rather than actual numbers.
PLAYERS_SEED: list[dict] = [
    # Al-Hilal
    {"id": "salem-al-dawsari", "team": "al-hilal", "pos": "FW", "det": "LW", "no": 10,
     "name": ("Salem Al-Dawsari", "سالم الدوسري"), "nat": ("Saudi Arabia", "السعودية"),
     "dob": "1991-08-19", "h": 173, "foot": "right",
     "stats": dict(matches=10, starts=10, minutes=890, goals=6, assists=4,
        yellow_cards=2, red_cards=0, xg=5.4, xa=3.8, shots=28, shots_on_target=14,
        progressive_carries=64, progressive_passes=78, pass_completion_pct=82.1)},
    {"id": "ruben-neves", "team": "al-hilal", "pos": "MF", "det": "DM", "no": 8,
     "name": ("Rúben Neves", "روبن نيفيز"), "nat": ("Portugal", "البرتغال"),
     "dob": "1997-03-13", "h": 180, "foot": "right",
     "stats": dict(matches=10, starts=10, minutes=900, goals=2, assists=3,
        yellow_cards=4, red_cards=0, xg=1.8, xa=2.6, progressive_passes=145,
        tackles=27, interceptions=18, pass_completion_pct=88.9)},
    {"id": "aleksandar-mitrovic", "team": "al-hilal", "pos": "FW", "det": "ST", "no": 9,
     "name": ("Aleksandar Mitrović", "ألكسندر ميتروفيتش"), "nat": ("Serbia", "صربيا"),
     "dob": "1994-09-16", "h": 189, "foot": "right",
     "stats": dict(matches=10, starts=9, minutes=820, goals=12, assists=2,
        yellow_cards=3, red_cards=0, xg=10.8, xa=1.9, shots=42, shots_on_target=24,
        aerials_won_pct=66.4)},
    {"id": "yassine-bounou", "team": "al-hilal", "pos": "GK", "det": "GK", "no": 1,
     "name": ("Yassine Bounou", "ياسين بونو"), "nat": ("Morocco", "المغرب"),
     "dob": "1991-04-05", "h": 195, "foot": "right",
     "stats": dict(matches=10, starts=10, minutes=900, goals=0, assists=0,
        yellow_cards=1, red_cards=0, xg=0.0, xa=0.1, save_pct=78.5, clean_sheets=5)},
    {"id": "joao-cancelo", "team": "al-hilal", "pos": "DF", "det": "RB", "no": 7,
     "name": ("João Cancelo", "جواو كانسيلو"), "nat": ("Portugal", "البرتغال"),
     "dob": "1994-05-27", "h": 182, "foot": "right",
     "stats": dict(matches=9, starts=9, minutes=810, goals=1, assists=4,
        yellow_cards=2, red_cards=0, xg=0.8, xa=3.2, progressive_carries=72,
        progressive_passes=88, pass_completion_pct=84.6, tackles=18, interceptions=10)},
    # Al-Nassr
    {"id": "cristiano-ronaldo", "team": "al-nassr", "pos": "FW", "det": "ST", "no": 7,
     "name": ("Cristiano Ronaldo", "كريستيانو رونالدو"), "nat": ("Portugal", "البرتغال"),
     "dob": "1985-02-05", "h": 187, "foot": "right",
     "stats": dict(matches=10, starts=10, minutes=900, goals=14, assists=3,
        yellow_cards=2, red_cards=0, xg=12.6, xa=2.5, shots=58, shots_on_target=32,
        aerials_won_pct=51.2)},
    {"id": "sadio-mane", "team": "al-nassr", "pos": "FW", "det": "LW", "no": 19,
     "name": ("Sadio Mané", "ساديو ماني"), "nat": ("Senegal", "السنغال"),
     "dob": "1992-04-10", "h": 175, "foot": "right",
     "stats": dict(matches=10, starts=9, minutes=820, goals=7, assists=4,
        yellow_cards=1, red_cards=0, xg=6.4, xa=3.6, shots=34, shots_on_target=18,
        progressive_carries=82, pass_completion_pct=78.8)},
    {"id": "marcelo-brozovic", "team": "al-nassr", "pos": "MF", "det": "DM", "no": 77,
     "name": ("Marcelo Brozović", "مارسيلو بروزوفيتش"), "nat": ("Croatia", "كرواتيا"),
     "dob": "1992-11-16", "h": 181, "foot": "right",
     "stats": dict(matches=10, starts=10, minutes=890, goals=2, assists=4,
        yellow_cards=3, red_cards=0, xg=1.6, xa=3.1, progressive_passes=128,
        tackles=24, interceptions=15, pass_completion_pct=87.4)},
    {"id": "aymeric-laporte", "team": "al-nassr", "pos": "DF", "det": "CB", "no": 14,
     "name": ("Aymeric Laporte", "أيمريك لابورت"), "nat": ("Spain", "إسبانيا"),
     "dob": "1994-05-27", "h": 191, "foot": "left",
     "stats": dict(matches=10, starts=10, minutes=900, goals=1, assists=1,
        yellow_cards=2, red_cards=0, xg=1.1, xa=0.4, tackles=14, interceptions=22,
        aerials_won_pct=68.2, pass_completion_pct=89.8)},
    # Al-Ittihad
    {"id": "karim-benzema", "team": "al-ittihad", "pos": "FW", "det": "ST", "no": 9,
     "name": ("Karim Benzema", "كريم بنزيمة"), "nat": ("France", "فرنسا"),
     "dob": "1987-12-19", "h": 185, "foot": "right",
     "stats": dict(matches=10, starts=10, minutes=890, goals=9, assists=5,
        yellow_cards=1, red_cards=0, xg=8.9, xa=4.4, shots=44, shots_on_target=22,
        pass_completion_pct=80.5)},
    {"id": "n-golo-kante", "team": "al-ittihad", "pos": "MF", "det": "CM", "no": 7,
     "name": ("N'Golo Kanté", "إنغولو كانتي"), "nat": ("France", "فرنسا"),
     "dob": "1991-03-29", "h": 168, "foot": "right",
     "stats": dict(matches=10, starts=10, minutes=890, goals=2, assists=3,
        yellow_cards=2, red_cards=0, xg=1.4, xa=2.4, progressive_passes=92,
        tackles=42, interceptions=28, pass_completion_pct=85.9)},
    {"id": "houssem-aouar", "team": "al-ittihad", "pos": "MF", "det": "AM", "no": 8,
     "name": ("Houssem Aouar", "حسام عوار"), "nat": ("Algeria", "الجزائر"),
     "dob": "1998-06-30", "h": 175, "foot": "right",
     "stats": dict(matches=10, starts=8, minutes=720, goals=4, assists=3,
        yellow_cards=2, red_cards=0, xg=3.2, xa=2.6, progressive_carries=58,
        pass_completion_pct=83.2)},
    {"id": "moussa-diaby", "team": "al-ittihad", "pos": "FW", "det": "LW", "no": 19,
     "name": ("Moussa Diaby", "موسى ديابي"), "nat": ("France", "فرنسا"),
     "dob": "1999-07-07", "h": 170, "foot": "right",
     "stats": dict(matches=10, starts=9, minutes=820, goals=6, assists=4,
        yellow_cards=1, red_cards=0, xg=5.8, xa=3.2, shots=32, shots_on_target=16,
        progressive_carries=92, pass_completion_pct=80.4)},
    # Al-Ahli
    {"id": "riyad-mahrez", "team": "al-ahli", "pos": "FW", "det": "RW", "no": 7,
     "name": ("Riyad Mahrez", "رياض محرز"), "nat": ("Algeria", "الجزائر"),
     "dob": "1991-02-21", "h": 179, "foot": "left",
     "stats": dict(matches=10, starts=10, minutes=880, goals=5, assists=6,
        yellow_cards=2, red_cards=0, xg=4.8, xa=5.1, shots=36, shots_on_target=18,
        progressive_carries=78, pass_completion_pct=82.4)},
    {"id": "ivan-toney", "team": "al-ahli", "pos": "FW", "det": "ST", "no": 17,
     "name": ("Ivan Toney", "إيفان توني"), "nat": ("England", "إنجلترا"),
     "dob": "1996-03-16", "h": 179, "foot": "right",
     "stats": dict(matches=10, starts=10, minutes=890, goals=11, assists=2,
        yellow_cards=2, red_cards=0, xg=9.4, xa=1.8, shots=46, shots_on_target=26,
        aerials_won_pct=58.3, pass_completion_pct=72.6)},
    {"id": "edouard-mendy", "team": "al-ahli", "pos": "GK", "det": "GK", "no": 1,
     "name": ("Édouard Mendy", "إدوارد ميندي"), "nat": ("Senegal", "السنغال"),
     "dob": "1992-03-01", "h": 197, "foot": "right",
     "stats": dict(matches=10, starts=10, minutes=900, goals=0, assists=0,
        yellow_cards=0, red_cards=0, xg=0.0, xa=0.0, save_pct=74.2, clean_sheets=4)},
    {"id": "firas-al-buraikan", "team": "al-ahli", "pos": "FW", "det": "ST", "no": 11,
     "name": ("Firas Al-Buraikan", "فراس البريكان"), "nat": ("Saudi Arabia", "السعودية"),
     "dob": "1999-05-14", "h": 180, "foot": "right",
     "stats": dict(matches=10, starts=8, minutes=720, goals=6, assists=2,
        yellow_cards=1, red_cards=0, xg=5.4, xa=1.6, shots=28, shots_on_target=14)},
    # Al-Qadsiah
    {"id": "ezequiel-fernandez", "team": "al-qadsiah", "pos": "MF", "det": "CM", "no": 5,
     "name": ("Ezequiel Fernández", "إزكيل فيرنانديز"), "nat": ("Argentina", "الأرجنتين"),
     "dob": "2002-06-12", "h": 178, "foot": "right",
     "stats": dict(matches=10, starts=10, minutes=890, goals=3, assists=2,
        yellow_cards=4, red_cards=0, xg=2.4, xa=1.8, progressive_passes=78,
        tackles=28, interceptions=14, pass_completion_pct=85.4)},
    {"id": "pierre-emerick-aubameyang", "team": "al-qadsiah", "pos": "FW", "det": "ST", "no": 9,
     "name": ("Pierre-Emerick Aubameyang", "بيير-إيمريك أوباميانغ"), "nat": ("Gabon", "الغابون"),
     "dob": "1989-06-18", "h": 187, "foot": "right",
     "stats": dict(matches=10, starts=10, minutes=890, goals=8, assists=3,
        yellow_cards=1, red_cards=0, xg=7.6, xa=2.4, shots=40, shots_on_target=20)},
    # Al-Shabab
    {"id": "yannick-carrasco", "team": "al-shabab", "pos": "FW", "det": "LW", "no": 21,
     "name": ("Yannick Carrasco", "يانيك كاراسكو"), "nat": ("Belgium", "بلجيكا"),
     "dob": "1993-09-04", "h": 181, "foot": "left",
     "stats": dict(matches=10, starts=9, minutes=810, goals=4, assists=3,
        yellow_cards=2, red_cards=0, xg=3.6, xa=2.8, shots=24, shots_on_target=12,
        progressive_carries=64)},
    # Al-Ettifaq
    {"id": "georginio-wijnaldum", "team": "al-ettifaq", "pos": "MF", "det": "CM", "no": 5,
     "name": ("Georginio Wijnaldum", "جورجينيو فينالدوم"), "nat": ("Netherlands", "هولندا"),
     "dob": "1990-11-11", "h": 175, "foot": "right",
     "stats": dict(matches=10, starts=10, minutes=890, goals=3, assists=2,
        yellow_cards=2, red_cards=0, xg=2.8, xa=1.9, progressive_passes=88,
        pass_completion_pct=86.4)},
    {"id": "moussa-dembele", "team": "al-ettifaq", "pos": "FW", "det": "ST", "no": 9,
     "name": ("Moussa Dembélé", "موسى ديمبيلي"), "nat": ("France", "فرنسا"),
     "dob": "1996-07-12", "h": 184, "foot": "right",
     "stats": dict(matches=10, starts=9, minutes=810, goals=6, assists=2,
        yellow_cards=1, red_cards=0, xg=5.2, xa=1.4, shots=28, shots_on_target=14)},
    # Al-Taawoun
    {"id": "alvaro-medran", "team": "al-taawoun", "pos": "MF", "det": "AM", "no": 10,
     "name": ("Álvaro Medrán", "ألفارو مدران"), "nat": ("Spain", "إسبانيا"),
     "dob": "1994-03-15", "h": 180, "foot": "left",
     "stats": dict(matches=10, starts=10, minutes=890, goals=4, assists=5,
        yellow_cards=3, red_cards=0, xg=3.8, xa=4.2, progressive_passes=92,
        pass_completion_pct=82.6)},
    # Al-Khaleej
    {"id": "fabio-martins", "team": "al-khaleej", "pos": "FW", "det": "RW", "no": 11,
     "name": ("Fábio Martins", "فابيو مارتينز"), "nat": ("Portugal", "البرتغال"),
     "dob": "1993-05-23", "h": 169, "foot": "left",
     "stats": dict(matches=10, starts=9, minutes=810, goals=4, assists=3,
        yellow_cards=2, red_cards=0, xg=3.4, xa=2.6, shots=22, shots_on_target=10)},
    # Al-Fateh
    {"id": "marwan-al-sahafi", "team": "al-fateh", "pos": "MF", "det": "CM", "no": 8,
     "name": ("Marwan Al-Sahafi", "مروان الصحفي"), "nat": ("Saudi Arabia", "السعودية"),
     "dob": "1995-04-17", "h": 178, "foot": "right",
     "stats": dict(matches=10, starts=10, minutes=890, goals=2, assists=4,
        yellow_cards=4, red_cards=0, xg=1.8, xa=3.4, progressive_passes=72,
        tackles=22, pass_completion_pct=83.1)},
    # Damac
    {"id": "georges-mikautadze", "team": "damac", "pos": "FW", "det": "ST", "no": 17,
     "name": ("Georges Mikautadze", "جورج ميكاوتادزه"), "nat": ("Georgia", "جورجيا"),
     "dob": "2000-10-31", "h": 179, "foot": "left",
     "stats": dict(matches=10, starts=9, minutes=820, goals=5, assists=2,
        yellow_cards=2, red_cards=0, xg=4.6, xa=1.4, shots=26, shots_on_target=12)},
    # Al-Fayha
    {"id": "fashion-sakala", "team": "al-fayha", "pos": "FW", "det": "RW", "no": 11,
     "name": ("Fashion Sakala", "فاشن ساكالا"), "nat": ("Zambia", "زامبيا"),
     "dob": "1997-05-08", "h": 178, "foot": "right",
     "stats": dict(matches=10, starts=8, minutes=720, goals=3, assists=2,
        yellow_cards=1, red_cards=0, xg=2.8, xa=1.6, shots=20, shots_on_target=10)},
    # Al-Riyadh
    {"id": "ever-banega", "team": "al-riyadh", "pos": "MF", "det": "CM", "no": 6,
     "name": ("Éver Banega", "إيفر بانيغا"), "nat": ("Argentina", "الأرجنتين"),
     "dob": "1988-06-29", "h": 175, "foot": "right",
     "stats": dict(matches=10, starts=9, minutes=820, goals=2, assists=4,
        yellow_cards=4, red_cards=0, xg=1.6, xa=3.6, progressive_passes=76,
        pass_completion_pct=84.4)},
    # Al-Wehda
    {"id": "odion-ighalo", "team": "al-wehda", "pos": "FW", "det": "ST", "no": 24,
     "name": ("Odion Ighalo", "أوديون إيغالو"), "nat": ("Nigeria", "نيجيريا"),
     "dob": "1989-06-16", "h": 188, "foot": "right",
     "stats": dict(matches=10, starts=9, minutes=810, goals=4, assists=1,
        yellow_cards=1, red_cards=0, xg=3.6, xa=0.8, shots=22, shots_on_target=11)},
]


def _build_players() -> list[Player]:
    out: list[Player] = []
    for p in PLAYERS_SEED:
        out.append(
            Player(
                id=p["id"],
                name=BilingualText(en=p["name"][0], ar=p["name"][1]),
                team_id=p["team"],
                position=p["pos"],
                detailed_position=p["det"],
                jersey_number=p.get("no"),
                nationality=BilingualText(en=p["nat"][0], ar=p["nat"][1]),
                birth_date=p.get("dob"),
                height_cm=p.get("h"),
                foot=p.get("foot"),
                season_stats=PlayerSeasonStats(**p["stats"]),
                sources={},
            )
        )
    return out


def build_snapshot(seed: int = 42) -> SeasonSnapshot:
    rng = random.Random(seed)
    teams = _build_teams()
    fixtures = _build_fixtures(teams, rng)
    players = _build_players()
    predictions = predict_upcoming(teams, fixtures)
    narrate_all(teams, players, fixtures, predictions, use_llm=False)
    # Pin generated_at to a fixed value so the bundled JSON has stable diffs.
    return SeasonSnapshot(
        league_id="spl-saudi-pro-league",
        season=SEASON,
        generated_at="2026-05-01T12:00:00+00:00",
        teams=teams,
        players=players,
        fixtures=fixtures,
        predictions=predictions,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the bundled demo snapshot")
    parser.add_argument("--output", type=Path, required=True, help="Output directory")
    parser.add_argument("--seed", type=int, default=9)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    snap = build_snapshot(seed=args.seed)

    season_path = args.output / "season.json"
    season_path.write_text(
        json.dumps(to_jsonable(snap), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    log.info(
        "wrote %s (teams=%d, players=%d, fixtures=%d, predictions=%d)",
        season_path,
        len(snap.teams),
        len(snap.players),
        len(snap.fixtures),
        len(snap.predictions),
    )

    finished = sum(1 for f in snap.fixtures if f.status == "finished")
    scheduled = sum(1 for f in snap.fixtures if f.status == "scheduled")

    manifest = {
        "generated_at": snap.generated_at,
        "version": "0.5.0-demo",
        "stage": "phase-5",
        "narration_source": "template",
        "league": snap.league_id,
        "season": snap.season,
        "team_count": len(snap.teams),
        "player_count": len(snap.players),
        "fixture_count": len(snap.fixtures),
        "fixture_finished": finished,
        "fixture_scheduled": scheduled,
        "prediction_count": len(snap.predictions),
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    for name, payload in [
        ("teams.json", [to_jsonable(t) for t in snap.teams]),
        ("players.json", [to_jsonable(p) for p in snap.players]),
        ("fixtures.json", [to_jsonable(f) for f in snap.fixtures]),
        ("predictions.json", [to_jsonable(p) for p in snap.predictions]),
    ]:
        (args.output / name).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
