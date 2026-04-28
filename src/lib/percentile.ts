/**
 * Percentile + per-90 computation.
 *
 * Used by player pages to show how a player ranks against positional peers
 * for each metric. The pizza chart consumes the percentile output directly.
 *
 * Conventions:
 *   - "per-90" means a cumulative stat scaled by minutes/90.
 *   - A minimum-minutes threshold (default 270) excludes low-sample noise
 *     from the comparison pool but still ranks the target player.
 *   - For "negative" stats (yellow cards, red cards) we invert the rank:
 *     fewer cards = higher percentile.
 *
 * The exported MetricResult is fully serializable so it can flow from a
 * server component into a client component (e.g. the PercentilePizza).
 */

import type { Player, PlayerSeasonStats, Position } from '@/types/data';

export type Category = 'attacking' | 'possession' | 'defending' | 'discipline';

interface MetricDef {
  key: string;
  category: Category;
  /** translation key under players.stats.* */
  i18nKey: string;
  /** is this stat cumulative (so we should normalize per-90)? */
  perNinety: boolean;
  /** for stats where lower is better (cards), invert the percentile rank */
  invert?: boolean;
  /** which positions this metric is meaningful for; empty = all */
  positions?: Position[];
  extract: (s: PlayerSeasonStats) => number | null;
}

const METRICS: MetricDef[] = [
  // Attacking
  { key: 'goals', category: 'attacking', i18nKey: 'goals', perNinety: true, extract: s => s.goals },
  { key: 'assists', category: 'attacking', i18nKey: 'assists', perNinety: true, extract: s => s.assists },
  { key: 'xg', category: 'attacking', i18nKey: 'xg', perNinety: true, extract: s => s.xg },
  { key: 'xa', category: 'attacking', i18nKey: 'xa', perNinety: true, extract: s => s.xa },
  { key: 'shots', category: 'attacking', i18nKey: 'shots', perNinety: true, extract: s => s.shots ?? null },
  { key: 'shots_on_target', category: 'attacking', i18nKey: 'shotsOnTarget', perNinety: true, extract: s => s.shots_on_target ?? null },

  // Possession
  { key: 'pass_completion_pct', category: 'possession', i18nKey: 'passCompletion', perNinety: false, extract: s => s.pass_completion_pct ?? null },
  { key: 'progressive_passes', category: 'possession', i18nKey: 'progressivePasses', perNinety: true, extract: s => s.progressive_passes ?? null },
  { key: 'progressive_carries', category: 'possession', i18nKey: 'progressiveCarries', perNinety: true, extract: s => s.progressive_carries ?? null },

  // Defending
  { key: 'tackles', category: 'defending', i18nKey: 'tackles', perNinety: true, extract: s => s.tackles ?? null },
  { key: 'interceptions', category: 'defending', i18nKey: 'interceptions', perNinety: true, extract: s => s.interceptions ?? null },
  { key: 'aerials_won_pct', category: 'defending', i18nKey: 'aerialsWonPct', perNinety: false, extract: s => s.aerials_won_pct ?? null },

  // Discipline (lower is better)
  { key: 'yellow_cards', category: 'discipline', i18nKey: 'yellowCards', perNinety: true, invert: true, extract: s => s.yellow_cards },
  { key: 'red_cards', category: 'discipline', i18nKey: 'redCards', perNinety: true, invert: true, extract: s => s.red_cards },
];

/** Serializable per-metric result safe to pass through server/client boundary. */
export interface MetricResult {
  key: string;
  category: Category;
  i18nKey: string;
  perNinety: boolean;
  /** raw value (e.g. 12 goals) */
  raw: number | null;
  /** normalized value (per-90 if applicable, otherwise same as raw) */
  normalized: number | null;
  /** percentile rank vs positional peers, 0–100 */
  percentile: number | null;
}

const DEFAULT_MIN_MINUTES = 270;

function perNinetyValue(raw: number, minutes: number): number {
  if (minutes <= 0) return 0;
  return (raw * 90) / minutes;
}

function normalize(stat: PlayerSeasonStats, m: MetricDef): number | null {
  const raw = m.extract(stat);
  if (raw === null || raw === undefined) return null;
  if (!m.perNinety) return raw;
  if (stat.minutes <= 0) return null;
  return perNinetyValue(raw, stat.minutes);
}

function percentileRank(value: number, sortedPool: number[]): number {
  if (sortedPool.length === 0) return 50;
  let below = 0;
  let equal = 0;
  for (const v of sortedPool) {
    if (v < value) below++;
    else if (v === value) equal++;
    else break;
  }
  const rank = (below + equal / 2) / sortedPool.length;
  return Math.round(rank * 100);
}

export function computePercentiles(
  player: Player,
  pool: Player[],
  options: { minMinutes?: number } = {}
): MetricResult[] {
  const minMinutes = options.minMinutes ?? DEFAULT_MIN_MINUTES;

  const eligiblePool = pool.filter(
    (p) =>
      p.position === player.position &&
      p.season_stats.minutes >= minMinutes &&
      p.id !== player.id
  );

  return METRICS.map((m) => {
    const raw = m.extract(player.season_stats);
    const normalized = normalize(player.season_stats, m);
    if (normalized === null) {
      return {
        key: m.key,
        category: m.category,
        i18nKey: m.i18nKey,
        perNinety: m.perNinety,
        raw,
        normalized: null,
        percentile: null,
      };
    }
    const peerValues = eligiblePool
      .map((p) => normalize(p.season_stats, m))
      .filter((v): v is number => v !== null)
      .sort((a, b) => a - b);

    let percentile: number | null;
    if (peerValues.length < 3) {
      percentile = null;
    } else {
      let pct = percentileRank(normalized, peerValues);
      if (m.invert) pct = 100 - pct;
      percentile = pct;
    }

    return {
      key: m.key,
      category: m.category,
      i18nKey: m.i18nKey,
      perNinety: m.perNinety,
      raw,
      normalized,
      percentile,
    };
  });
}

export function categoryColor(category: Category): string {
  switch (category) {
    case 'attacking':
      return '#e25b5b';
    case 'possession':
      return '#5b9be2';
    case 'defending':
      return '#3ea968';
    case 'discipline':
      return '#c9a14a';
  }
}
