/**
 * Data loader — fetches the daily snapshot at build time.
 *
 * The pipeline writes JSON to the `data` branch of this repo. The frontend
 * pulls it via the GitHub raw URL. If the data branch doesn't exist yet
 * (e.g. before the first daily run), we fall back to a small bundled
 * sample so the site builds, deploys, and looks alive even pre-pipeline.
 */

import type { DataManifest, SeasonSnapshot } from '@/types/data';
import sampleSeason from '@/data/sample-season.json';

const REPO = 'msh-max/Dawri-AI';
const DATA_BRANCH = 'data';
// The daily-refresh workflow writes snapshots into `data-out/` on the data
// branch (see .github/workflows/daily-refresh.yml). Fetch from there, not the
// branch root, otherwise every request 404s and the site silently falls back
// to the bundled sample dataset.
const DATA_PREFIX = 'data-out';

const RAW_BASE = `https://raw.githubusercontent.com/${REPO}/${DATA_BRANCH}/${DATA_PREFIX}`;

// Cast-via-unknown so the JSON literal satisfies the SeasonSnapshot type
// without TS narrowing the optional fields out of existence.
const SAMPLE_SNAPSHOT = sampleSeason as unknown as SeasonSnapshot & {
  is_sample?: boolean;
};

const PLACEHOLDER_MANIFEST: DataManifest = {
  generated_at: new Date(0).toISOString(),
  version: '0.0.0',
  stage: 'pre-data',
  league: 'spl-saudi-pro-league',
  season: '2025-26',
};

async function fetchJson<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${RAW_BASE}/${path}`, {
      // Build-time fetch; revalidate not needed for static export.
      cache: 'force-cache',
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

function isSnapshotEmpty(s: SeasonSnapshot | null): boolean {
  if (!s) return true;
  // A "successful" fetch can still hand back an empty scaffold while the
  // upstream scrapers are blocked or returning zero rows. Treat that as
  // sample-grade so the UI doesn't render an empty league.
  return (s.teams?.length ?? 0) === 0;
}

export async function loadSeasonSnapshot(): Promise<SeasonSnapshot> {
  const live = await fetchJson<SeasonSnapshot>('season.json');
  return isSnapshotEmpty(live) ? SAMPLE_SNAPSHOT : (live as SeasonSnapshot);
}

export async function loadManifest(): Promise<DataManifest> {
  return (await fetchJson<DataManifest>('manifest.json')) ?? PLACEHOLDER_MANIFEST;
}

export function hasLiveData(manifest: DataManifest): boolean {
  return manifest.stage !== 'pre-data' && manifest.stage !== 'phase-0';
}

export async function isUsingSampleData(): Promise<boolean> {
  const live = await fetchJson<SeasonSnapshot>('season.json');
  return isSnapshotEmpty(live);
}
