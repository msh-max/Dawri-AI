"""Narrative generation for Dawri AI.

Two execution modes, picked at runtime:

  1. **Template** (default, deterministic, free, fast)
       Bilingual prose composed from the structured data we already have:
       percentile ranks for players, prediction probabilities for matches.
       No model download. Runs in <1s for the whole league.

  2. **Local LLM** — Qwen2.5-1.5B-Instruct (Q4_K_M GGUF)
       Loaded via llama-cpp-python on the CPU runner. ~600MB on disk,
       ~3 tok/sec on Actions runners. Used for richer prose when the
       caller passes use_llm=True. The template output is fed to the
       model as a "rewrite this in a more engaging voice" prompt so we
       get richer text without hallucinated facts.

The shape of the output is identical in both modes — a Narrative with a
bilingual `text` and a `source` tag — so the frontend renders the same
way regardless of which mode produced it.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable

from .schema import (
    BilingualText,
    Fixture,
    MatchPrediction,
    Narrative,
    Player,
    Team,
)

log = logging.getLogger("dawri.narrate")

# --------------------------------------------------------------------------
# Optional LLM backend
# --------------------------------------------------------------------------

# We keep the heavy import inside try/except so the pipeline still runs
# in environments where llama-cpp-python isn't installed (eg. dryrun in CI
# or local dev without the model).
try:  # pragma: no cover — optional dep
    from llama_cpp import Llama  # type: ignore[import-untyped]

    _LLAMA_AVAILABLE = True
except Exception:  # noqa: BLE001
    Llama = None  # type: ignore[assignment]
    _LLAMA_AVAILABLE = False


_QWEN_REPO = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
_QWEN_FILE = "qwen2.5-1.5b-instruct-q4_k_m.gguf"


class _LlmBackend:
    """Lazy holder for the loaded model so we only pay the cost once."""

    def __init__(self) -> None:
        self._model: Llama | None = None  # type: ignore[name-defined]

    def get(self) -> "Llama | None":  # type: ignore[name-defined]
        if not _LLAMA_AVAILABLE:
            return None
        if self._model is not None:
            return self._model
        try:
            from huggingface_hub import hf_hub_download  # type: ignore[import-untyped]
            path = hf_hub_download(repo_id=_QWEN_REPO, filename=_QWEN_FILE)
            log.info("loading Qwen2.5-1.5B GGUF from %s", path)
            self._model = Llama(  # type: ignore[call-arg]
                model_path=path,
                n_ctx=2048,
                n_threads=2,
                verbose=False,
            )
            return self._model
        except Exception as e:  # noqa: BLE001
            log.warning("LLM unavailable: %s — falling back to templates", e)
            return None


_BACKEND = _LlmBackend()


def _llm_rewrite(prompt: str, max_tokens: int = 220) -> str | None:
    """Run a single-turn instruction prompt; return None if LLM disabled."""
    model = _BACKEND.get()
    if model is None:
        return None
    try:
        resp = model.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise football analyst. Rewrite the "
                        "user's draft in a more engaging voice. NEVER add new "
                        "facts, numbers, or names that aren't in the draft."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.55,
        )
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:  # noqa: BLE001
        log.warning("LLM call failed: %s", e)
        return None


# --------------------------------------------------------------------------
# Player scout reports — template
# --------------------------------------------------------------------------


def _team_label(team_id: str | None, teams_by_id: dict[str, Team], lang: str) -> str:
    if not team_id or team_id not in teams_by_id:
        return ""
    t = teams_by_id[team_id]
    return t.short_name.ar if lang == "ar" else t.short_name.en


def _per_90(value: float | None, minutes: int) -> float | None:
    if value is None or minutes <= 0:
        return None
    return value * 90 / minutes


def _percentile_rank(values: list[float], target: float) -> int:
    if not values:
        return 50
    below = sum(1 for v in values if v < target)
    equal = sum(1 for v in values if v == target)
    return round((below + equal / 2) / len(values) * 100)


def _player_strengths_weaknesses(
    player: Player, peers: list[Player]
) -> tuple[list[str], list[str]]:
    """Return (strengths_keys, weaknesses_keys) using percentiles vs peers."""
    pool = [p for p in peers if p.position == player.position and p.id != player.id and p.season_stats.minutes >= 270]
    if len(pool) < 3:
        return [], []
    s = player.season_stats

    def pct(key: str, value: float | None) -> tuple[str, int] | None:
        if value is None:
            return None
        peers_v: list[float] = []
        for p in pool:
            ps = p.season_stats
            v = {
                "goals_p90": _per_90(ps.goals, ps.minutes),
                "assists_p90": _per_90(ps.assists, ps.minutes),
                "xg_p90": _per_90(ps.xg, ps.minutes) if ps.xg is not None else None,
                "xa_p90": _per_90(ps.xa, ps.minutes) if ps.xa is not None else None,
                "pass_pct": ps.pass_completion_pct,
                "tackles_p90": _per_90(ps.tackles, ps.minutes) if ps.tackles is not None else None,
                "interceptions_p90": _per_90(ps.interceptions, ps.minutes) if ps.interceptions is not None else None,
                "aerials": ps.aerials_won_pct,
                "prog_carries_p90": _per_90(ps.progressive_carries, ps.minutes) if ps.progressive_carries is not None else None,
                "prog_passes_p90": _per_90(ps.progressive_passes, ps.minutes) if ps.progressive_passes is not None else None,
            }[key]
            if v is not None:
                peers_v.append(v)
        if not peers_v:
            return None
        return key, _percentile_rank(peers_v, value)

    candidates: list[tuple[str, int]] = []
    for key, value in (
        ("goals_p90", _per_90(s.goals, s.minutes)),
        ("assists_p90", _per_90(s.assists, s.minutes)),
        ("xg_p90", _per_90(s.xg, s.minutes) if s.xg is not None else None),
        ("xa_p90", _per_90(s.xa, s.minutes) if s.xa is not None else None),
        ("pass_pct", s.pass_completion_pct),
        ("tackles_p90", _per_90(s.tackles, s.minutes) if s.tackles is not None else None),
        ("interceptions_p90", _per_90(s.interceptions, s.minutes) if s.interceptions is not None else None),
        ("aerials", s.aerials_won_pct),
        ("prog_carries_p90", _per_90(s.progressive_carries, s.minutes) if s.progressive_carries is not None else None),
        ("prog_passes_p90", _per_90(s.progressive_passes, s.minutes) if s.progressive_passes is not None else None),
    ):
        if value is None:
            continue
        result = pct(key, value)
        if result:
            candidates.append(result)

    candidates.sort(key=lambda kv: kv[1], reverse=True)
    strengths = [k for k, p in candidates if p >= 75][:3]
    weaknesses = [k for k, p in reversed(candidates) if p <= 25][:2]
    return strengths, weaknesses


_LABELS_EN: dict[str, str] = {
    "goals_p90": "goalscoring",
    "assists_p90": "creating chances",
    "xg_p90": "shot quality",
    "xa_p90": "chance quality created",
    "pass_pct": "passing accuracy",
    "tackles_p90": "tackling",
    "interceptions_p90": "reading the game",
    "aerials": "aerial duels",
    "prog_carries_p90": "progressive carrying",
    "prog_passes_p90": "progressive passing",
}

_LABELS_AR: dict[str, str] = {
    "goals_p90": "التهديف",
    "assists_p90": "صناعة الفرص",
    "xg_p90": "جودة التسديد",
    "xa_p90": "جودة الفرص الممنوحة",
    "pass_pct": "دقة التمرير",
    "tackles_p90": "التدخّلات",
    "interceptions_p90": "قراءة اللعب",
    "aerials": "الكرات الهوائية",
    "prog_carries_p90": "التقدّم بالكرة",
    "prog_passes_p90": "التمرير التقدّمي",
}


def _join_human(items: list[str], lang: str) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if lang == "ar":
        return "، ".join(items[:-1]) + "، و" + items[-1]
    return ", ".join(items[:-1]) + " and " + items[-1]


def _scout_template(player: Player, peers: list[Player], teams_by_id: dict[str, Team]) -> Narrative:
    s = player.season_stats
    team_en = _team_label(player.team_id, teams_by_id, "en")
    team_ar = _team_label(player.team_id, teams_by_id, "ar")
    strengths, weaknesses = _player_strengths_weaknesses(player, peers)
    name_en = player.name.en
    name_ar = player.name.ar
    pos_en = {"GK": "goalkeeper", "DF": "defender", "MF": "midfielder", "FW": "forward"}.get(player.position or "", "player")
    # Arabic position label as a definite noun-phrase so it reads naturally
    # when followed by an adjective.
    pos_ar = {
        "GK": "كحارس مرمى أساسي",
        "DF": "كمدافع أساسي",
        "MF": "كلاعب وسط أساسي",
        "FW": "كمهاجم أساسي",
    }.get(player.position or "", "كلاعب أساسي")

    if s.minutes <= 0:
        en = (
            f"{name_en} hasn't logged minutes for {team_en} this season — too "
            "early for a percentile-based read."
        )
        ar = (
            f"لم يخض {name_ar} أيّ دقائق مع {team_ar} هذا الموسم بعد — لا توجد "
            "بيانات كافية لتقييم مئيني الآن."
        )
    elif strengths:
        s_en = _join_human([_LABELS_EN[k] for k in strengths], "en")
        s_ar = _join_human([_LABELS_AR[k] for k in strengths], "ar")
        opener_en = (
            f"{name_en} has been {team_en}'s {pos_en} of choice this season, "
            f"with {s.minutes:,} minutes across {s.matches} matches."
        )
        opener_ar = (
            f"حضر {name_ar} {pos_ar} في صفوف {team_ar} هذا الموسم، "
            f"بـ{s.minutes:,} دقيقة في {s.matches} مباراة."
        )

        strength_en = f"He grades top-25% versus positional peers in {s_en}."
        strength_ar = f"ويُصنّف ضمن أعلى 25٪ من نظرائه في مركزه في {s_ar}."

        if weaknesses:
            w_en = _join_human([_LABELS_EN[k] for k in weaknesses], "en")
            w_ar = _join_human([_LABELS_AR[k] for k in weaknesses], "ar")
            weakness_en = f" The trade-off is below-average output in {w_en}."
            weakness_ar = f" في المقابل، إنتاجه في {w_ar} دون المتوسط."
        else:
            weakness_en = ""
            weakness_ar = ""

        en = f"{opener_en} {strength_en}{weakness_en}"
        ar = f"{opener_ar} {strength_ar}{weakness_ar}"
    else:
        en = (
            f"{name_en} has logged {s.minutes:,} minutes for {team_en} but "
            "doesn't yet rank in the top quartile of any tracked metric "
            "versus positional peers."
        )
        ar = (
            f"خاض {name_ar} {s.minutes:,} دقيقة مع {team_ar}، إلّا أنّه لم "
            "يدخل بعد ضمن الربع الأعلى في أيّ من المقاييس المتاحة مقارنةً "
            "بنظرائه في مركزه."
        )

    return Narrative(
        text=BilingualText(en=en.strip(), ar=ar.strip()),
        generated_at=datetime.now(timezone.utc).isoformat(),
        source="template",
    )


# --------------------------------------------------------------------------
# Match preview / recap — template
# --------------------------------------------------------------------------


def _preview_template(
    fixture: Fixture, prediction: MatchPrediction | None, teams_by_id: dict[str, Team]
) -> Narrative:
    home_en = _team_label(fixture.home_team_id, teams_by_id, "en") or fixture.home_team_id
    home_ar = _team_label(fixture.home_team_id, teams_by_id, "ar") or fixture.home_team_id
    away_en = _team_label(fixture.away_team_id, teams_by_id, "en") or fixture.away_team_id
    away_ar = _team_label(fixture.away_team_id, teams_by_id, "ar") or fixture.away_team_id

    if prediction is None:
        en = f"{home_en} host {away_en}. Prediction will appear once the model has data on both sides."
        ar = f"يستضيف {home_ar} فريق {away_ar}. ستظهر التنبؤات بمجرّد توفر البيانات الكافية للنموذج."
        return Narrative(
            text=BilingualText(en=en, ar=ar),
            generated_at=datetime.now(timezone.utc).isoformat(),
            source="template",
        )

    h = round(prediction.home_win_prob * 100)
    d = round(prediction.draw_prob * 100)
    a = round(prediction.away_win_prob * 100)
    score_h, score_a = prediction.most_likely_score
    favored_en = home_en if h > a else (away_en if a > h else "neither side")
    favored_ar = home_ar if h > a else (away_ar if a > h else "أي من الفريقين")

    en = (
        f"{home_en} vs {away_en}: the model favors {favored_en} with a "
        f"{max(h, a)}% win probability ({h}/{d}/{a} W/D/L). "
        f"Expected goals lean {prediction.home_xg_predicted:.1f}–{prediction.away_xg_predicted:.1f}, "
        f"with {score_h}–{score_a} the most likely scoreline."
    )
    ar = (
        f"{home_ar} ضدّ {away_ar}: يُرجّح النموذج فوز {favored_ar} باحتمالية "
        f"{max(h, a)}٪ ({h}/{d}/{a} ف/ت/خ). "
        f"الأهداف المتوقّعة {prediction.home_xg_predicted:.1f}–{prediction.away_xg_predicted:.1f}، "
        f"والنتيجة الأرجح {score_h}–{score_a}."
    )
    return Narrative(
        text=BilingualText(en=en, ar=ar),
        generated_at=datetime.now(timezone.utc).isoformat(),
        source="template",
    )


def _recap_template(fixture: Fixture, teams_by_id: dict[str, Team]) -> Narrative:
    home_en = _team_label(fixture.home_team_id, teams_by_id, "en") or fixture.home_team_id
    home_ar = _team_label(fixture.home_team_id, teams_by_id, "ar") or fixture.home_team_id
    away_en = _team_label(fixture.away_team_id, teams_by_id, "en") or fixture.away_team_id
    away_ar = _team_label(fixture.away_team_id, teams_by_id, "ar") or fixture.away_team_id
    hg = fixture.home_goals or 0
    ag = fixture.away_goals or 0

    if hg > ag:
        result_en = f"{home_en} beat {away_en} {hg}–{ag}"
        result_ar = f"فاز {home_ar} على {away_ar} {hg}–{ag}"
    elif ag > hg:
        result_en = f"{away_en} won {ag}–{hg} at {home_en}"
        result_ar = f"فاز {away_ar} على أرض {home_ar} {ag}–{hg}"
    else:
        result_en = f"{home_en} and {away_en} drew {hg}–{ag}"
        result_ar = f"تعادل {home_ar} مع {away_ar} {hg}–{ag}"

    xg_clause_en = ""
    xg_clause_ar = ""
    if fixture.home_xg is not None and fixture.away_xg is not None:
        xg_clause_en = (
            f", with xG of {fixture.home_xg:.1f}–{fixture.away_xg:.1f} backing up the result"
        )
        xg_clause_ar = (
            f"، بأهداف متوقّعة {fixture.home_xg:.1f}–{fixture.away_xg:.1f} تدعم النتيجة"
        )

    en = result_en + xg_clause_en + "."
    ar = result_ar + xg_clause_ar + "."
    return Narrative(
        text=BilingualText(en=en, ar=ar),
        generated_at=datetime.now(timezone.utc).isoformat(),
        source="template",
    )


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------


def narrate_player(
    player: Player, peers: list[Player], teams_by_id: dict[str, Team], use_llm: bool = False
) -> Narrative:
    base = _scout_template(player, peers, teams_by_id)
    if not use_llm:
        return base
    rewritten_en = _llm_rewrite(
        f"Rewrite this scouting note in 2–3 sentences, English, no new facts:\n\n{base.text.en}"
    )
    rewritten_ar = _llm_rewrite(
        f"أعد صياغة الملاحظة الكشفية التالية في جملتين أو ثلاث، بالعربية، دون إضافة حقائق جديدة:\n\n{base.text.ar}"
    )
    if rewritten_en and rewritten_ar:
        return Narrative(
            text=BilingualText(en=rewritten_en, ar=rewritten_ar),
            generated_at=base.generated_at,
            source="qwen2.5-1.5b",
        )
    return base


def narrate_preview(
    fixture: Fixture,
    prediction: MatchPrediction | None,
    teams_by_id: dict[str, Team],
    use_llm: bool = False,
) -> Narrative:
    base = _preview_template(fixture, prediction, teams_by_id)
    if not use_llm:
        return base
    rewritten_en = _llm_rewrite(
        f"Rewrite this match preview in 2 sentences, English, no new facts:\n\n{base.text.en}"
    )
    rewritten_ar = _llm_rewrite(
        f"أعد صياغة معاينة المباراة التالية في جملتين، بالعربية، دون إضافة حقائق جديدة:\n\n{base.text.ar}"
    )
    if rewritten_en and rewritten_ar:
        return Narrative(
            text=BilingualText(en=rewritten_en, ar=rewritten_ar),
            generated_at=base.generated_at,
            source="qwen2.5-1.5b",
        )
    return base


def narrate_recap(
    fixture: Fixture, teams_by_id: dict[str, Team], use_llm: bool = False
) -> Narrative:
    base = _recap_template(fixture, teams_by_id)
    if not use_llm:
        return base
    rewritten_en = _llm_rewrite(
        f"Rewrite this match recap in 2 sentences, English, no new facts:\n\n{base.text.en}"
    )
    rewritten_ar = _llm_rewrite(
        f"أعد صياغة ملخّص المباراة التالي في جملتين، بالعربية، دون إضافة حقائق جديدة:\n\n{base.text.ar}"
    )
    if rewritten_en and rewritten_ar:
        return Narrative(
            text=BilingualText(en=rewritten_en, ar=rewritten_ar),
            generated_at=base.generated_at,
            source="qwen2.5-1.5b",
        )
    return base


def narrate_all(
    teams: list[Team],
    players: list[Player],
    fixtures: list[Fixture],
    predictions: Iterable[MatchPrediction],
    use_llm: bool = False,
) -> tuple[list[Player], list[Fixture]]:
    """Walk every player and fixture, attaching narratives in place."""
    teams_by_id = {t.id: t for t in teams}
    pred_by_fixture: dict[str, MatchPrediction] = {p.fixture_id: p for p in predictions}

    log.info("narrate: %d players, %d fixtures (use_llm=%s)", len(players), len(fixtures), use_llm)

    for p in players:
        p.scout_report = narrate_player(p, players, teams_by_id, use_llm=use_llm)

    for f in fixtures:
        if f.status == "finished":
            f.recap = narrate_recap(f, teams_by_id, use_llm=use_llm)
        else:
            f.preview = narrate_preview(
                f, pred_by_fixture.get(f.id), teams_by_id, use_llm=use_llm
            )

    return players, fixtures
