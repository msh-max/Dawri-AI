"""Dawri AI daily pipeline entry point.

Stages (Phase 1 implements 1, 2, and 6):
  1. scrape   — pull from FBref + Wikidata
  2. etl      — merge into canonical Team / Player records
  3. predict  — TODO (Phase 4)
  4. explain  — TODO (Phase 4)
  5. narrate  — TODO (Phase 5, local Qwen2.5-1.5B)
  6. snapshot — write canonical JSON the frontend reads
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .cache import HttpCache
from .etl.normalize import merge_fixtures, merge_players, merge_teams
from .narrate import narrate_all
from .predict import predict_upcoming
from .schema import BilingualText, Fixture, SeasonSnapshot, Team, to_jsonable
from .sources import fbref, wikidata
from .sources.spl_roster import SPL_CLUBS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("dawri.pipeline")


def _synthesise_matchweek(teams: list[Team], *, season: str) -> list[Fixture]:
    """Pair the curated roster up into a single upcoming matchweek.

    Pure scaffolding: paired in roster order, kicked off on the next Friday.
    Real fixtures from FBref always win when available — this exists purely
    so a demo deploy never renders an empty matches/predictions surface.
    """
    if len(teams) < 2:
        return []
    today = datetime.now(timezone.utc).date()
    days_until_friday = (4 - today.weekday()) % 7 or 7
    kickoff_date = today + timedelta(days=days_until_friday)
    out: list[Fixture] = []
    pairs = list(zip(teams[0::2], teams[1::2]))
    for idx, (home, away) in enumerate(pairs):
        date_iso = kickoff_date.isoformat()
        out.append(
            Fixture(
                id=f"{date_iso}-{home.id}-vs-{away.id}",
                date=date_iso,
                kickoff=f"{date_iso}T18:00:00Z",
                matchweek=1,
                home_team_id=home.id,
                away_team_id=away.id,
                venue=home.city,
                status="scheduled",
                sources={},
            )
        )
        _ = idx  # keep mypy quiet
    return out


def _curated_team_fallback() -> list[Team]:
    return [
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
        for c in SPL_CLUBS
    ]


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    log.info("wrote %s", path)


def run(
    output_dir: Path,
    cache_dir: Path,
    season: str = "2025-26",
    use_llm: bool = False,
) -> None:
    cache = HttpCache(cache_dir=cache_dir)

    log.info("[1/6] scrape — FBref")
    fbref_teams = fbref.list_teams(cache)
    fbref_rows: list[tuple[fbref.FbrefTeam, fbref.FbrefPlayerRow]] = []
    for ft in fbref_teams:
        for row in fbref.list_players_for_team(cache, ft):
            fbref_rows.append((ft, row))

    log.info("[1/6] scrape — Wikidata")
    wd_clubs = wikidata.fetch_clubs(cache)
    wd_players = wikidata.fetch_players(cache)

    log.info("[1/6] scrape — fixtures")
    fbref_fixtures = fbref.list_fixtures(cache)

    log.info("[2/6] etl")
    teams = merge_teams(fbref_teams, wd_clubs)
    players = merge_players(fbref_rows, wd_players, teams)
    fixtures = merge_fixtures(fbref_fixtures, teams)

    if not teams:
        log.warning(
            "live sources produced 0 teams — falling back to curated SPL roster "
            "so the snapshot still ships real club identities"
        )
        teams = _curated_team_fallback()

    if not fixtures and teams:
        log.warning(
            "no live fixtures — synthesising an upcoming matchweek so the "
            "predict/narrate stages still have something to chew on"
        )
        fixtures = _synthesise_matchweek(teams, season=season)

    log.info("[3/6] predict")
    predictions = predict_upcoming(teams, fixtures)

    log.info("[5/6] narrate")
    narrate_all(teams, players, fixtures, predictions, use_llm=use_llm)

    log.info("[6/6] snapshot")
    snapshot = SeasonSnapshot(
        league_id="spl-saudi-pro-league",
        season=season,
        generated_at=datetime.now(timezone.utc).isoformat(),
        teams=teams,
        players=players,
        fixtures=fixtures,
        predictions=predictions,
    )

    _write_json(
        output_dir / "season.json",
        to_jsonable(snapshot),
    )
    _write_json(
        output_dir / "teams.json",
        [to_jsonable(t) for t in teams],
    )
    _write_json(
        output_dir / "players.json",
        [to_jsonable(p) for p in players],
    )
    _write_json(
        output_dir / "fixtures.json",
        [to_jsonable(f) for f in fixtures],
    )
    _write_json(
        output_dir / "predictions.json",
        [to_jsonable(p) for p in predictions],
    )
    _write_json(
        output_dir / "manifest.json",
        {
            "generated_at": snapshot.generated_at,
            "version": "0.5.0",
            "stage": "phase-5",
            "narration_source": "qwen2.5-1.5b" if use_llm else "template",
            "league": snapshot.league_id,
            "season": snapshot.season,
            "team_count": len(teams),
            "player_count": len(players),
            "fixture_count": len(fixtures),
            "prediction_count": len(predictions),
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Dawri AI daily pipeline")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(".pipeline-cache"),
        help="Directory for HTTP cache (default: .pipeline-cache)",
    )
    parser.add_argument("--season", default="2025-26")
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Run scout reports + previews through the local Qwen LLM. "
        "Without this flag, the pipeline emits deterministic template prose.",
    )
    args = parser.parse_args()

    log.info("Dawri AI pipeline → %s (use_llm=%s)", args.output, args.use_llm)
    run(
        output_dir=args.output.resolve(),
        cache_dir=args.cache_dir.resolve(),
        season=args.season,
        use_llm=args.use_llm,
    )
    log.info("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
