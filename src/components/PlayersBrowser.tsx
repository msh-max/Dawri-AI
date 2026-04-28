'use client';

import { useMemo, useState } from 'react';
import { useTranslations } from 'next-intl';
import Fuse from 'fuse.js';
import { Search, SlidersHorizontal } from 'lucide-react';
import type { Player, Position, Team } from '@/types/data';
import { PlayerCard } from './PlayerCard';
import { EmptyState } from './EmptyState';

interface Props {
  players: Player[];
  teams: Team[];
  locale: string;
}

const POSITIONS: Position[] = ['GK', 'DF', 'MF', 'FW'];

export function PlayersBrowser({ players, teams, locale }: Props) {
  const t = useTranslations('players');
  const tc = useTranslations('common');
  const [query, setQuery] = useState('');
  const [position, setPosition] = useState<Position | 'ALL'>('ALL');

  const teamById = useMemo(() => {
    const m = new Map<string, Team>();
    for (const t of teams) m.set(t.id, t);
    return m;
  }, [teams]);

  const fuse = useMemo(
    () =>
      new Fuse(players, {
        keys: ['name.en', 'name.ar', 'detailed_position'],
        threshold: 0.35,
        ignoreLocation: true,
      }),
    [players]
  );

  const filtered = useMemo(() => {
    let result = players;
    if (query.trim()) {
      result = fuse.search(query).map((r) => r.item);
    }
    if (position !== 'ALL') {
      result = result.filter((p) => p.position === position);
    }
    // Stable sort: more minutes first
    return [...result].sort(
      (a, b) => b.season_stats.minutes - a.season_stats.minutes
    );
  }, [players, fuse, query, position]);

  if (players.length === 0) {
    return <EmptyState title={tc('noData')} />;
  }

  return (
    <div>
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search
            size={16}
            aria-hidden
            className="pointer-events-none absolute start-3 top-1/2 -translate-y-1/2 text-ink-50/40"
          />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('searchPlaceholder')}
            className="w-full rounded-full border border-ink-50/10 bg-ink-900/60 py-2.5 ps-10 pe-4 text-sm text-ink-50 placeholder:text-ink-50/40 focus:border-gold-500/40 focus:outline-none focus:ring-2 focus:ring-gold-500/20"
          />
        </div>
        <div className="flex items-center gap-2 text-xs">
          <SlidersHorizontal
            size={14}
            aria-hidden
            className="text-ink-50/40"
          />
          <button
            onClick={() => setPosition('ALL')}
            className={pillClass(position === 'ALL')}
          >
            {t('positionAll')}
          </button>
          {POSITIONS.map((p) => (
            <button
              key={p}
              onClick={() => setPosition(p)}
              className={pillClass(position === p)}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState title={t('noResults')} hint={t('noResultsHint')} />
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((p) => (
            <PlayerCard
              key={p.id}
              player={p}
              team={p.team_id ? teamById.get(p.team_id) ?? null : null}
              locale={locale}
            />
          ))}
        </div>
      )}

      <div className="mt-6 text-center text-xs text-ink-50/40">
        {filtered.length} / {players.length}
      </div>
    </div>
  );
}

function pillClass(active: boolean): string {
  return [
    'rounded-full border px-3 py-1 transition',
    active
      ? 'border-gold-500/50 bg-gold-500/10 text-gold-200'
      : 'border-ink-50/10 bg-ink-900/40 text-ink-50/60 hover:border-gold-500/30 hover:text-gold-200',
  ].join(' ');
}
