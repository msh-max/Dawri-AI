# Dawri AI

> AI-powered analytics, predictions, and deep insights for the **Saudi Pro League** —
> bilingual (Arabic + English), refreshed every day, 100% free, hosted on GitHub Pages.

**Live site:** `https://msh-max.github.io/Dawri-AI/` *(Phase 0 scaffold)*

---

## What it is

A premium-grade football analytics platform focused on the SPL:

- **Player Intelligence** — percentile pizza charts, shot maps, form trends, and AI-generated scout reports for every player
- **Match Predictions** — W/D/L probabilities, expected scorelines, BTTS, O/U, and per-player props, each with a transparent **"Why?" panel** powered by SHAP feature contributions
- **Compare mode** — overlay up to three players on a shared radar
- **Title race simulator** — interactive Monte Carlo over the rest of the season
- **Full bilingual** — Arabic with proper RTL, not a translation hack

Everything is precomputed once a day and served as static JSON. No backend, no paid APIs.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 15 (static export), TypeScript, Tailwind, shadcn/ui patterns, Framer Motion |
| Charts | visx, D3, Recharts |
| i18n | next-intl with full RTL |
| Pipeline | Python 3.11 in GitHub Actions — scrapers, pandas, xgboost, SHAP |
| Narratives | Qwen2.5-1.5B-Instruct (GGUF, CPU) via llama-cpp-python |
| Hosting | GitHub Pages from `out/` artifact |

## Architecture

```
GitHub repo (public)
├── Next.js source (this branch)
├── /scripts/pipeline   — daily Python ETL
└── data branch         — orphan branch with daily JSON snapshots

GitHub Actions
├── deploy-site.yml     — on push: build + deploy to Pages
└── daily-refresh.yml   — cron 03:00 UTC: scrape → predict → narrate → commit

GitHub Pages → https://msh-max.github.io/Dawri-AI/
```

## Data sources

All free, all attributed:

- [FBref](https://fbref.com) — advanced stats (xG, progressive passes, etc.)
- [SPL official site](https://spl.com.sa) — fixtures, official table, lineups
- [Wikidata](https://www.wikidata.org) — bilingual names, photos, biographies
- [API-Football](https://www.api-football.com) — free tier (100 req/day) for live status

## Development

```bash
# Install
npm install

# Run dev server
npm run dev   # → http://localhost:3000

# Build static site
npm run build
# Output in ./out
```

```bash
# Run the data pipeline locally
python -m venv .venv && source .venv/bin/activate
pip install -r scripts/pipeline/requirements.txt
python scripts/pipeline/run.py --output ./data-out
```

## Roadmap

- [x] **Phase 0** — scaffold, design system, bilingual setup, deploy workflow
- [ ] **Phase 1** — scrapers + canonical JSON for SPL players & fixtures
- [ ] **Phase 2** — player pages with radar/pizza + shot maps
- [ ] **Phase 3** — match pages with xG flow + post-match analysis
- [ ] **Phase 4** — prediction model + SHAP "Why?" layer
- [ ] **Phase 5** — local LLM scout reports & match previews
- [ ] **Phase 6** — compare, leaderboards, title-race simulator
- [ ] **Phase 7** — polish, perf, accessibility audit

## License

Code: MIT. Data: each source's terms (FBref non-commercial w/ attribution, etc.).
Predictions are probabilistic. Past performance does not guarantee future results.
