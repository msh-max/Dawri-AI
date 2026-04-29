'use client';

import { useDeferredValue, useMemo, useState } from 'react';
import { useTranslations } from 'next-intl';
import { Trophy, RotateCcw } from 'lucide-react';
import type { Fixture, MatchPrediction, Team } from '@/types/data';
import {
  simulateSeason,
  type LockedOutcome,
  type LocksMap,
  type SimResult,
} from '@/lib/simulator';

interface Props {
  teams: Team[];
  fixtures: Fixture[];
  predictions: MatchPrediction[];
  locale: string;
}

const N_SIMS = 2000;

export function TitleRace({ teams, fixtures, predictions, locale }: Props) {
  const t = useTranslations('simulator');

  const [locks, setLocks] = useState<LocksMap>({});
  const deferredLocks = useDeferredValue(locks);

  const remaining = useMemo(
    () => fixtures.filter((f) => f.status !== 'finished'),
    [fixtures]
  );

  const teamById = useMemo(() => {
    const m = new Map<string, Team>();
    for (const team of teams) m.set(team.id, team);
    return m;
  }, [teams]);

  const predById = useMemo(() => {
    const m = new Map<string, MatchPrediction>();
    for (const p of predictions) m.set(p.fixture_id, p);
    return m;
  }, [predictions]);

  // Re-run sim whenever locks change. Memo'd so we don't re-sim on
  // unrelated re-renders.
  const results: SimResult[] = useMemo(
    () =>
      simulateSeason({
        teams,
        fixtures,
        predictions,
        locks: deferredLocks,
        nSims: N_SIMS,
      }),
    [teams, fixtures, predictions, deferredLocks]
  );

  const sortedByChampion = useMemo(
    () => [...results].sort((a, b) => b.championPct - a.championPct),
    [results]
  );

  const setLock = (fixtureId: string, outcome: LockedOutcome) =>
    setLocks((cur) => {
      const next = { ...cur };
      if (outcome === null) delete next[fixtureId];
      else next[fixtureId] = outcome;
      return next;
    });

  const resetAll = () => setLocks({});
  const hasLocks = Object.keys(locks).length > 0;

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.1fr_1fr]">
      {/* LEFT: probability bars */}
      <div className="gold-border-gradient relative rounded-2xl bg-ink-900/60 p-5 backdrop-blur">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-ink-50/90">
            <Trophy size={14} className="text-gold-300" aria-hidden />
            {t('champion')}
          </h2>
          {hasLocks ? (
            <button
              onClick={resetAll}
              className="inline-flex items-center gap-1.5 rounded-full border border-ink-50/10 bg-ink-50/[0.02] px-2.5 py-1 text-[11px] text-ink-50/65 transition hover:border-gold-500/40 hover:text-gold-200"
            >
              <RotateCcw size={11} aria-hidden />
              {t('resetAll')}
            </button>
          ) : null}
        </div>

        <ul className="space-y-3">
          {sortedByChampion.map((r) => (
            <li key={r.team.id}>
              <ProbRow
                name={
                  locale === 'ar' ? r.team.name.ar : r.team.name.en
                }
                champion={r.championPct}
                topThree={r.topThreePct}
                relegation={r.relegationPct}
                expectedPoints={r.expectedPoints}
                topThreeLabel={t('topThree')}
                relegationLabel={t('relegation')}
              />
            </li>
          ))}
        </ul>

        <p className="mt-5 text-[11px] text-ink-50/40">
          {t('simulations', { n: N_SIMS })}
        </p>
      </div>

      {/* RIGHT: remaining fixtures with lockable W/D/L */}
      <div className="overflow-hidden rounded-2xl border border-ink-50/[0.06] bg-ink-900/40">
        <div className="border-b border-ink-50/[0.06] px-5 py-3 text-sm font-medium text-ink-50/80">
          {t('remainingFixtures')}
        </div>
        {remaining.length === 0 ? (
          <p className="px-5 py-10 text-center text-xs text-ink-50/50">
            {t('noRemaining')}
          </p>
        ) : (
          <ul className="divide-y divide-ink-50/[0.04]">
            {remaining.map((f) => {
              const home = teamById.get(f.home_team_id);
              const away = teamById.get(f.away_team_id);
              const homeName = home
                ? locale === 'ar'
                  ? home.short_name.ar
                  : home.short_name.en
                : f.home_team_id;
              const awayName = away
                ? locale === 'ar'
                  ? away.short_name.ar
                  : away.short_name.en
                : f.away_team_id;
              const pred = predById.get(f.id);
              const lock = locks[f.id] ?? null;
              return (
                <li
                  key={f.id}
                  className="grid grid-cols-1 gap-2 px-5 py-3 sm:grid-cols-[1fr_auto] sm:items-center"
                >
                  <div className="flex items-center justify-between gap-3 text-sm sm:justify-start sm:gap-2">
                    <span className="truncate font-medium text-ink-50/85">
                      {homeName}
                    </span>
                    <span className="text-ink-50/35">vs</span>
                    <span className="truncate font-medium text-ink-50/85">
                      {awayName}
                    </span>
                  </div>
                  <LockButtons
                    pred={pred}
                    lock={lock}
                    setLock={(o) => setLock(f.id, o)}
                    labels={{
                      H: t('lockHome'),
                      D: t('lockDraw'),
                      A: t('lockAway'),
                      AI: t('lockAi'),
                    }}
                  />
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

function ProbRow({
  name,
  champion,
  topThree,
  relegation,
  expectedPoints,
  topThreeLabel,
  relegationLabel,
}: {
  name: string;
  champion: number;
  topThree: number;
  relegation: number;
  expectedPoints: number;
  topThreeLabel: string;
  relegationLabel: string;
}) {
  return (
    <div className="rounded-lg border border-ink-50/[0.06] bg-ink-950/40 px-3 py-2.5">
      <div className="mb-1.5 flex items-center justify-between text-sm">
        <span className="font-medium text-ink-50/90">{name}</span>
        <span className="font-mono text-xs tabular-nums text-ink-50/50">
          {expectedPoints.toFixed(1)} xPts
        </span>
      </div>
      <div className="mb-1 flex items-center gap-2 text-[11px]">
        <span className="w-20 text-ink-50/50">🏆</span>
        <ProbBar value={champion} accent="gold" />
        <span className="w-10 text-end font-mono tabular-nums text-gold-300">
          {champion.toFixed(0)}%
        </span>
      </div>
      <div className="mb-1 flex items-center gap-2 text-[11px]">
        <span className="w-20 truncate text-ink-50/50" title={topThreeLabel}>
          {topThreeLabel}
        </span>
        <ProbBar value={topThree} accent="green" />
        <span className="w-10 text-end font-mono tabular-nums text-saudi-300">
          {topThree.toFixed(0)}%
        </span>
      </div>
      <div className="flex items-center gap-2 text-[11px]">
        <span className="w-20 text-ink-50/50">{relegationLabel}</span>
        <ProbBar value={relegation} accent="red" />
        <span className="w-10 text-end font-mono tabular-nums text-red-300/80">
          {relegation.toFixed(0)}%
        </span>
      </div>
    </div>
  );
}

function ProbBar({
  value,
  accent,
}: {
  value: number;
  accent: 'gold' | 'green' | 'red';
}) {
  const fill = {
    gold: 'bg-gold-shine',
    green: 'bg-saudi-500/80',
    red: 'bg-red-400/60',
  }[accent];
  return (
    <div className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-ink-50/[0.05]">
      <div
        className={`absolute inset-y-0 ${fill}`}
        style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
      />
    </div>
  );
}

function LockButtons({
  pred,
  lock,
  setLock,
  labels,
}: {
  pred: MatchPrediction | undefined;
  lock: LockedOutcome;
  setLock: (o: LockedOutcome) => void;
  labels: { H: string; D: string; A: string; AI: string };
}) {
  const aiHint = pred
    ? `${Math.round(pred.home_win_prob * 100)}/${Math.round(pred.draw_prob * 100)}/${Math.round(pred.away_win_prob * 100)}`
    : '—';

  return (
    <div className="flex items-center gap-1 justify-self-start sm:justify-self-end">
      <Btn active={lock === null} onClick={() => setLock(null)}>
        {labels.AI}
        <span className="ms-1 font-mono text-[9px] text-ink-50/40">
          {aiHint}
        </span>
      </Btn>
      <Btn
        active={lock === 'H'}
        onClick={() => setLock(lock === 'H' ? null : 'H')}
        title={labels.H}
      >
        H
      </Btn>
      <Btn
        active={lock === 'D'}
        onClick={() => setLock(lock === 'D' ? null : 'D')}
        title={labels.D}
      >
        D
      </Btn>
      <Btn
        active={lock === 'A'}
        onClick={() => setLock(lock === 'A' ? null : 'A')}
        title={labels.A}
      >
        A
      </Btn>
    </div>
  );
}

function Btn({
  active,
  onClick,
  children,
  title,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  title?: string;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`rounded-md px-2 py-1 text-[11px] font-medium transition ${
        active
          ? 'bg-gold-500/15 text-gold-200 ring-1 ring-inset ring-gold-500/40'
          : 'bg-ink-950/40 text-ink-50/55 ring-1 ring-inset ring-ink-50/[0.06] hover:bg-ink-50/[0.04] hover:text-ink-50/85'
      }`}
    >
      {children}
    </button>
  );
}
