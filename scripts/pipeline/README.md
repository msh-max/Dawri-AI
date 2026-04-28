# Dawri AI · data pipeline

Python pipeline that runs daily inside GitHub Actions. It scrapes free data
sources, builds canonical JSON, trains lightweight ML for predictions, and
uses a small local LLM (Qwen2.5-1.5B-Instruct via `llama-cpp-python`) to
generate scout reports and match previews in both Arabic and English.

## Stages

1. **scrape** — FBref, SPL official site, Wikidata, API-Football free tier
2. **etl** — normalize into canonical players / matches / events tables
3. **predict** — xgboost models for W/D/L, score, BTTS, O/U, player props,
   Monte Carlo for the title-race simulator
4. **explain** — SHAP values → bilingual templated sentences ("Why?" panel)
5. **narrate** — local Qwen2.5-1.5B writes scout reports + match previews
6. **snapshot** — emit JSON to `$DATA_DIR`

Output is committed to the `data` branch which the static frontend fetches
from at build/runtime via GitHub raw URLs.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r scripts/pipeline/requirements.txt
python scripts/pipeline/run.py --output ./data-out
```

## Status

Phase 0: scaffold only. Stages will land one at a time in subsequent PRs.
