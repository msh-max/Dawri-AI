"""One-off helper: regenerate the predictions block of the bundled sample.

Run with:
    python -m scripts.pipeline._generate_sample_predictions

It loads src/data/sample-season.json, rebuilds the predictions list using
the real prediction engine (so the sample stays consistent with what the
pipeline would actually produce), and rewrites the file in place.
"""

from __future__ import annotations

import json
from pathlib import Path

from .predict import predict_upcoming
from .schema import (
    BilingualText,
    Fixture,
    MatchEvent,
    Team,
    XgFlowPoint,
    to_jsonable,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_PATH = REPO_ROOT / "src" / "data" / "sample-season.json"


def _bt(d: dict | None) -> BilingualText | None:
    if not d:
        return None
    return BilingualText(en=d.get("en", ""), ar=d.get("ar", ""))


def _team_from_dict(d: dict) -> Team:
    return Team(
        id=d["id"],
        name=BilingualText(**d["name"]),
        short_name=BilingualText(**d["short_name"]),
        fbref_id=d.get("fbref_id"),
        wikidata_id=d.get("wikidata_id"),
        founded=d.get("founded"),
        city=_bt(d.get("city")),
        crest_url=d.get("crest_url"),
        primary_color=d.get("primary_color"),
        sources=d.get("sources", {}),
    )


def _fixture_from_dict(d: dict) -> Fixture:
    return Fixture(
        id=d["id"],
        date=d["date"],
        kickoff=d.get("kickoff"),
        matchweek=d.get("matchweek"),
        home_team_id=d["home_team_id"],
        away_team_id=d["away_team_id"],
        venue=_bt(d.get("venue")),
        home_goals=d.get("home_goals"),
        away_goals=d.get("away_goals"),
        home_xg=d.get("home_xg"),
        away_xg=d.get("away_xg"),
        status=d.get("status", "scheduled"),
        fbref_match_id=d.get("fbref_match_id"),
        events=[
            MatchEvent(
                minute=e["minute"],
                team_id=e["team_id"],
                type=e["type"],
                player_id=e.get("player_id"),
                player_name=_bt(e.get("player_name")),
                detail=_bt(e.get("detail")),
            )
            for e in d.get("events", [])
        ],
        xg_flow=[XgFlowPoint(**p) for p in d.get("xg_flow", [])],
        sources=d.get("sources", {}),
    )


def main() -> int:
    data = json.loads(SAMPLE_PATH.read_text("utf-8"))
    teams = [_team_from_dict(t) for t in data["teams"]]
    fixtures = [_fixture_from_dict(f) for f in data["fixtures"]]
    predictions = predict_upcoming(teams, fixtures)

    data["predictions"] = [to_jsonable(p) for p in predictions]
    SAMPLE_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(predictions)} sample predictions to {SAMPLE_PATH}")
    for p in predictions:
        print(
            f"  {p.fixture_id}: W/D/L "
            f"{p.home_win_prob:.0%}/{p.draw_prob:.0%}/{p.away_win_prob:.0%} "
            f"score {p.most_likely_score}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
