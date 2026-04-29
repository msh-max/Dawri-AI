/**
 * Compute league standings client-side from finished fixtures.
 *
 * Kept pure / synchronous so any page that has the snapshot can derive
 * the table without re-fetching. Sorted by Premier-League conventions:
 * points DESC, goal difference DESC, goals for DESC, name ASC.
 */

import type { Fixture, Team } from '@/types/data';

export interface StandingsRow {
  team: Team;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  points: number;
  /** last 5 results, oldest → newest, "W" | "D" | "L" */
  form: ('W' | 'D' | 'L')[];
}

export function computeStandings(
  teams: Team[],
  fixtures: Fixture[],
  locale: string = 'en'
): StandingsRow[] {
  const byId = new Map<string, StandingsRow>();
  for (const t of teams) {
    byId.set(t.id, {
      team: t,
      played: 0,
      won: 0,
      drawn: 0,
      lost: 0,
      goalsFor: 0,
      goalsAgainst: 0,
      goalDifference: 0,
      points: 0,
      form: [],
    });
  }

  const finished = fixtures
    .filter(
      (f) =>
        f.status === 'finished' &&
        f.home_goals !== null &&
        f.away_goals !== null
    )
    .sort((a, b) => a.date.localeCompare(b.date));

  for (const f of finished) {
    const home = byId.get(f.home_team_id);
    const away = byId.get(f.away_team_id);
    const hg = f.home_goals ?? 0;
    const ag = f.away_goals ?? 0;
    if (home) {
      home.played++;
      home.goalsFor += hg;
      home.goalsAgainst += ag;
      if (hg > ag) {
        home.won++;
        home.points += 3;
        home.form.push('W');
      } else if (hg === ag) {
        home.drawn++;
        home.points += 1;
        home.form.push('D');
      } else {
        home.lost++;
        home.form.push('L');
      }
    }
    if (away) {
      away.played++;
      away.goalsFor += ag;
      away.goalsAgainst += hg;
      if (ag > hg) {
        away.won++;
        away.points += 3;
        away.form.push('W');
      } else if (hg === ag) {
        away.drawn++;
        away.points += 1;
        away.form.push('D');
      } else {
        away.lost++;
        away.form.push('L');
      }
    }
  }

  const rows = Array.from(byId.values());
  for (const r of rows) {
    r.goalDifference = r.goalsFor - r.goalsAgainst;
    // keep only last 5
    r.form = r.form.slice(-5);
  }

  rows.sort((a, b) => {
    if (b.points !== a.points) return b.points - a.points;
    if (b.goalDifference !== a.goalDifference)
      return b.goalDifference - a.goalDifference;
    if (b.goalsFor !== a.goalsFor) return b.goalsFor - a.goalsFor;
    const an = locale === 'ar' ? a.team.name.ar : a.team.name.en;
    const bn = locale === 'ar' ? b.team.name.ar : b.team.name.en;
    return an.localeCompare(bn, locale);
  });

  return rows;
}
