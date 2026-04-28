"""Dawri AI daily pipeline entry point.

This is the orchestrator that runs end-to-end every day:
  1. scrape   — pull raw HTML/JSON from FBref, SPL official site, Wikidata
  2. etl      — normalize into canonical players / matches / events tables
  3. predict  — train models, generate W/D/L + score + props predictions
  4. explain  — compute SHAP feature contributions, render bilingual sentences
  5. narrate  — local LLM (Qwen2.5-1.5B GGUF) writes scout reports + previews
  6. snapshot — write everything to JSON for the static frontend to consume

The frontend reads these JSON files directly from the `data` branch via
GitHub raw URLs.

Phase 0: this file is a scaffold. Each step logs and writes a placeholder
manifest so the workflow is wired up end-to-end before real scrapers land.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("dawri.pipeline")


def write_manifest(out_dir: Path) -> None:
    """Write a tiny manifest file so the frontend can detect 'data is live'."""
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0-scaffold",
        "stage": "phase-0",
        "status": "pipeline-not-yet-implemented",
        "league": "spl-saudi-pro-league",
        "season": "2025-26",
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log.info("Wrote manifest to %s", out_dir / "manifest.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Dawri AI daily pipeline")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Directory to write JSON artifacts",
    )
    args = parser.parse_args()

    log.info("Starting Dawri AI pipeline")
    log.info("Output directory: %s", args.output)

    # Stages — each will become a real module under scripts/pipeline/.
    log.info("[1/6] scrape — TODO")
    log.info("[2/6] etl — TODO")
    log.info("[3/6] predict — TODO")
    log.info("[4/6] explain — TODO")
    log.info("[5/6] narrate — TODO")
    log.info("[6/6] snapshot")

    write_manifest(args.output)
    log.info("Pipeline finished (scaffold mode)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
