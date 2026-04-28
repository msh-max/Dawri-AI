/**
 * Data loader — fetches the daily snapshot at build time.
 *
 * The pipeline writes JSON to the `data` branch of this repo. The frontend
 * pulls it via the GitHub raw URL. If the data branch doesn't exist yet
 * (e.g. before the first daily run), we fall back to a placeholder snapshot
 * so the site builds and deploys regardless.
 */

import type { DataManifest, SeasonSnapshot } from '@/types/data';

const REPO = 'msh-max/msh-max';
const DATA_BRANCH = 'data';

const RAW_BASE = `https://raw.githubusercontent.com/${REPO}/${DATA_BRANCH}`;

const PLACEHOLDER_SNAPSHOT: SeasonSnapshot = {
  league_id: 'spl-saudi-pro-league',
  season: '2025-26',
  generated_at: new Date(0).toISOString(),
  teams: [],
  players: [],
  fixtures: [],
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
    (await fetchJson<SeasonSnapshot>('season.json')) ?? PLACEHOLDER_SNAPSHOT
  );
}

export async function loadManifest(): Promise<DataManifest> {
  return (await fetchJson<DataManifest>('manifest.json')) ?? PLACEHOLDER_MANIFEST;
}

export function hasLiveData(manifest: DataManifest): boolean {
  return manifest.stage !== 'pre-data' && manifest.stage !== 'phase-0';
}
