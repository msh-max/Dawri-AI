/**
 * Browser-side Monte Carlo for the rest of the season.
 *
 * For each remaining fixture we either:
 *   - sample home_goals ~ Poisson(home_xg), away_goals ~ Poisson(away_xg)
 *     using the prediction's expected goals, OR
 *   - apply a user-locked outcome (H/D/A) with a representative scoreline.
 *
 * After playing out every remaining fixture we sort the table (Pts, GD,
 * GF) and tally final positions. With ~80 SPL fixtures × 2,000 sims the
 * full pass takes < 100 ms in any modern browser.
 */

import type { Fixture, MatchPrediction, Team } from '@/types/data';
import { computeStandings, type StandingsRow } from './standings';

export type LockedOutcome = 'H' | 'D' | 'A' | null;

export type LocksMap = Record<string, LockedOutcome>;

export interface SimResult {
  team: Team;
  championPct: number;
  topThreePct: number;
  relegationPct: number;
  /** distribution of final positions, length = teams.length */
  positionHistogram: number[];
  expectedPoints: number;
}

const DEFAULT_SIMS = 2000;
const RELEGATION_SLOTS = 3; // SPL bottom-3 are relegated
const TOP_SLOTS = 3;

// Poisson sampler using Knuth's algorithm. Adequate for lambda <= ~30.
function poisson(lambda: number, rand: () => number): number {
  if (lambda <= 0) return 0;
  const L = Math.exp(-lambda);
  let k = 0;
  let p = 1;
  do {
    k++;
    p *= rand();
  } while (p > L);
  return k - 1;
}

function lockToScore(outcome: LockedOutcome): [number, number] {
  switch (outcome) {
    case 'H':
      return [2, 1];
    case 'A':
      return [1, 2];
    case 'D':
      return [1, 1];
    default:
      return [0, 0];
  }
}

function mulberry32(seed: number): () => number {
  let a = seed | 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

interface MutableRow {
  id: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  points: number;
}

function rowsToMutable(rows: StandingsRow[]): MutableRow[] {
  return rows.map((r) => ({
    id: r.team.id,
    played: r.played,
    won: r.won,
    drawn: r.drawn,
    lost: r.lost,
    goalsFor: r.goalsFor,
    goalsAgainst: r.goalsAgainst,
    points: r.points,
  }));
}

function applyResult(row: MutableRow, scored: number, conceded: number): void {
  row.played++;
  row.goalsFor += scored;
  row.goalsAgainst += conceded;
  if (scored > conceded) {
    row.won++;
    row.points += 3;
  } else if (scored < conceded) {
    row.lost++;
  } else {
    row.drawn++;
    row.points += 1;
  }
}

function sortFinal(table: MutableRow[]): MutableRow[] {
  return [...table].sort((a, b) => {
    if (b.points !== a.points) return b.points - a.points;
    const aGd = a.goalsFor - a.goalsAgainst;
    const bGd = b.goalsFor - b.goalsAgainst;
    if (bGd !== aGd) return bGd - aGd;
    if (b.goalsFor !== a.goalsFor) return b.goalsFor - a.goalsFor;
    return a.id.localeCompare(b.id);
  });
}

export interface SimulateInput {
  teams: Team[];
  fixtures: Fixture[];
  predictions: MatchPrediction[];
  locks?: LocksMap;
  nSims?: number;
  seed?: number;
}

export function simulateSeason({
  teams,
  fixtures,
  predictions,
  locks = {},
  nSims = DEFAULT_SIMS,
  seed = 42,
}: SimulateInput): SimResult[] {
  const rand = mulberry32(seed);

  const finishedRows = computeStandings(teams, fixtures);
  const finishedById = new Map<string, StandingsRow>();
  for (const r of finishedRows) finishedById.set(r.team.id, r);

  const remaining = fixtures.filter((f) => f.status !== 'finished');
  const predById = new Map<string, MatchPrediction>();
  for (const p of predictions) predById.set(p.fixture_id, p);

  const teamCount = teams.length;
  const teamIndex = new Map<string, number>();
  teams.forEach((t, i) => teamIndex.set(t.id, i));

  // Accumulators
  const championCount = new Array(teamCount).fill(0);
  const topThreeCount = new Array(teamCount).fill(0);
  const relegationCount = new Array(teamCount).fill(0);
  const positionHist = teams.map(() => new Array(teamCount).fill(0));
  const pointsSum = new Array(teamCount).fill(0);

  for (let s = 0; s < nSims; s++) {
    const table = rowsToMutable(finishedRows);
    const idToRow = new Map<string, MutableRow>();
    for (const r of table) idToRow.set(r.id, r);

    for (const f of remaining) {
      const home = idToRow.get(f.home_team_id);
      const away = idToRow.get(f.away_team_id);
      if (!home || !away) continue;

      const lock = locks[f.id] ?? null;
      let hg: number;
      let ag: number;
      if (lock) {
        [hg, ag] = lockToScore(lock);
      } else {
        const pred = predById.get(f.id);
        const homeXg = pred?.home_xg_predicted ?? 1.4;
        const awayXg = pred?.away_xg_predicted ?? 1.2;
        hg = poisson(homeXg, rand);
        ag = poisson(awayXg, rand);
      }
      applyResult(home, hg, ag);
      applyResult(away, ag, hg);
    }

    const sorted = sortFinal(table);
    sorted.forEach((row, position) => {
      const idx = teamIndex.get(row.id);
      if (idx === undefined) return;
      pointsSum[idx] += row.points;
      positionHist[idx][position]++;
      if (position === 0) championCount[idx]++;
      if (position < TOP_SLOTS) topThreeCount[idx]++;
      if (position >= teamCount - RELEGATION_SLOTS) relegationCount[idx]++;
    });
  }

  return teams.map((team, i) => ({
    team,
    championPct: (championCount[i] / nSims) * 100,
    topThreePct: (topThreeCount[i] / nSims) * 100,
    relegationPct: (relegationCount[i] / nSims) * 100,
    positionHistogram: positionHist[i].map((c) => (c / nSims) * 100),
    expectedPoints: pointsSum[i] / nSims,
  }));
}
