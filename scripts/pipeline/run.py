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
from datetime import datetime, timezone
from pathlib import Path

from .cache import HttpCache
from .etl.normalize import merge_fixtures, merge_players, merge_teams
from .schema import SeasonSnapshot, to_jsonable
from .sources import fbref, wikidata

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("dawri.pipeline")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    log.info("wrote %s", path)


def run(output_dir: Path, cache_dir: Path, season: str = "2025-26") -> None:
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

    log.info("[6/6] snapshot")
    snapshot = SeasonSnapshot(
        league_id="spl-saudi-pro-league",
        season=season,
        generated_at=datetime.now(timezone.utc).isoformat(),
        teams=teams,
        players=players,
        fixtures=fixtures,
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
        output_dir / "manifest.json",
        {
            "generated_at": snapshot.generated_at,
            "version": "0.3.0",
            "stage": "phase-3",
            "league": snapshot.league_id,
            "season": snapshot.season,
            "team_count": len(teams),
            "player_count": len(players),
            "fixture_count": len(fixtures),
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
    args = parser.parse_args()

    log.info("Dawri AI pipeline → %s", args.output)
    run(
        output_dir=args.output.resolve(),
        cache_dir=args.cache_dir.resolve(),
        season=args.season,
    )
    log.info("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
