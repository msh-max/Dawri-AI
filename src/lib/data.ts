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

const REPO = 'msh-max/msh-max';
const DATA_BRANCH = 'data';

const RAW_BASE = `https://raw.githubusercontent.com/${REPO}/${DATA_BRANCH}`;

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

export async function loadSeasonSnapshot(): Promise<SeasonSnapshot> {
  return (
    (await fetchJson<SeasonSnapshot>('season.json')) ?? SAMPLE_SNAPSHOT
  );
}

export async function loadManifest(): Promise<DataManifest> {
  return (await fetchJson<DataManifest>('manifest.json')) ?? PLACEHOLDER_MANIFEST;
}

export function hasLiveData(manifest: DataManifest): boolean {
  return manifest.stage !== 'pre-data' && manifest.stage !== 'phase-0';
}

export async function isUsingSampleData(): Promise<boolean> {
  const live = await fetchJson<SeasonSnapshot>('season.json');
  return live === null;
}
