'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import Fuse from 'fuse.js';
import { Plus, Search, X } from 'lucide-react';
import type { Player, Team } from '@/types/data';
import { computePercentiles } from '@/lib/percentile';
import { RadarOverlay } from './charts/RadarOverlay';

interface Props {
  players: Player[];
  teams: Team[];
  locale: string;
}

const MAX_PLAYERS = 3;
const PLAYER_COLORS = ['#3ea968', '#c9a14a', '#5b9be2'];

export function CompareTool({ players, teams, locale }: Props) {
  const t = useTranslations('compare');
  const tp = useTranslations('players.stats');

  const teamById = useMemo(() => {
    const m = new Map<string, Team>();
    for (const t of teams) m.set(t.id, t);
    return m;
  }, [teams]);

  const playerById = useMemo(() => {
    const m = new Map<string, Player>();
    for (const p of players) m.set(p.id, p);
    return m;
  }, [players]);

  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  // Hydrate selection from `?p=a,b,c` on mount (static export doesn't
  // pre-render search params, so this is the right place).
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    const raw = params.get('p');
    if (!raw) return;
    const ids = raw
      .split(',')
      .map((s) => s.trim())
      .filter((s) => playerById.has(s))
      .slice(0, MAX_PLAYERS);
    if (ids.length > 0) setSelectedIds(ids);
  }, [playerById]);

  // Mirror selection back to URL so the comparison is shareable
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const url = new URL(window.location.href);
    if (selectedIds.length > 0) {
      url.searchParams.set('p', selectedIds.join(','));
    } else {
      url.searchParams.delete('p');
    }
    window.history.replaceState({}, '', url.toString());
  }, [selectedIds]);

  const selected = selectedIds
    .map((id) => playerById.get(id))
    .filter((p): p is Player => Boolean(p));

  // For each selected player, percentiles vs the full snapshot pool
  const series = selected.map((p) => ({
    id: p.id,
    label: locale === 'ar' ? p.name.ar : p.name.en,
    results: computePercentiles(p, players),
  }));

  const addPlayer = (id: string) => {
    setSelectedIds((cur) => {
      if (cur.includes(id) || cur.length >= MAX_PLAYERS) return cur;
      return [...cur, id];
    });
  };
  const removePlayer = (id: string) => {
    setSelectedIds((cur) => cur.filter((x) => x !== id));
  };

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center gap-2">
        {selected.map((p, i) => {
          const team = p.team_id ? teamById.get(p.team_id) ?? null : null;
          const color = PLAYER_COLORS[i % PLAYER_COLORS.length];
          return (
            <SelectedPlayerChip
              key={p.id}
              player={p}
              team={team}
              color={color}
              locale={locale}
              onRemove={() => removePlayer(p.id)}
              removeLabel={t('remove')}
            />
          );
        })}
        {selected.length < MAX_PLAYERS ? (
          <PlayerPicker
            players={players}
            excludeIds={selectedIds}
            onPick={addPlayer}
            placeholder={t('searchPlaceholder')}
            addLabel={t('addPlayer')}
            locale={locale}
          />
        ) : (
          <span className="text-xs text-ink-50/40">{t('tooMany')}</span>
        )}
      </div>

      {selected.length === 0 ? (
        <div className="grid place-items-center rounded-2xl border border-dashed border-ink-50/10 bg-ink-900/30 px-8 py-20 text-center text-sm text-ink-50/50">
          {t('empty')}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_1.2fr]">
          <div className="gold-border-gradient relative rounded-2xl bg-ink-900/60 p-6 backdrop-blur">
            <div className="grid place-items-center">
              <RadarOverlay players={series} />
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-ink-50/[0.06] bg-ink-900/40">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink-50/[0.06] text-xs uppercase tracking-wider text-ink-50/50">
                  <th className="px-4 py-3 text-start font-medium">
                    {t('statHeader')}
                  </th>
                  {selected.map((p, i) => (
                    <th
                      key={p.id}
                      className="px-3 py-3 text-end font-medium"
                      style={{ color: PLAYER_COLORS[i % PLAYER_COLORS.length] }}
                    >
                      {locale === 'ar' ? p.name.ar : p.name.en}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {series[0]?.results.map((row) => (
                  <tr
                    key={row.key}
                    className="border-b border-ink-50/[0.04] last:border-b-0"
                  >
                    <td className="px-4 py-2 text-ink-50/75">
                      {tp(row.i18nKey as 'goals')}
                    </td>
                    {series.map((s, i) => {
                      const cell = s.results.find((r) => r.key === row.key);
                      const pct = cell?.percentile;
                      const value = cell?.normalized;
                      return (
                        <td
                          key={s.id + row.key}
                          className="px-3 py-2 text-end font-mono text-xs tabular-nums"
                          style={{ color: PLAYER_COLORS[i % PLAYER_COLORS.length] }}
                        >
                          {value === null || value === undefined ? (
                            <span className="text-ink-50/25">—</span>
                          ) : (
                            <>
                              {row.perNinety ? value.toFixed(2) : value.toFixed(1)}
                              {pct !== null && pct !== undefined ? (
                                <span className="ms-1 text-[10px] text-ink-50/35">
                                  ({pct})
                                </span>
                              ) : null}
                            </>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function SelectedPlayerChip({
  player,
  team,
  color,
  locale,
  onRemove,
  removeLabel,
}: {
  player: Player;
  team: Team | null;
  color: string;
  locale: string;
  onRemove: () => void;
  removeLabel: string;
}) {
  const name = locale === 'ar' ? player.name.ar : player.name.en;
  const teamName = team
    ? locale === 'ar'
      ? team.short_name.ar
      : team.short_name.en
    : '';
  return (
    <div
      className="inline-flex items-center gap-2 rounded-full border bg-ink-900/60 ps-3 pe-1.5 py-1.5"
      style={{ borderColor: color + '60' }}
    >
      <span
        className="inline-block h-2 w-2 flex-shrink-0 rounded-full"
        style={{ background: color }}
      />
      <Link
        href={`/${locale}/players/${player.id}/`}
        className="text-sm font-medium text-ink-50/90 hover:text-gold-200"
      >
        {name}
      </Link>
      {teamName ? (
        <span className="text-xs text-ink-50/40">· {teamName}</span>
      ) : null}
      <button
        onClick={onRemove}
        className="grid h-6 w-6 place-items-center rounded-full text-ink-50/40 transition hover:bg-ink-50/[0.06] hover:text-ink-50/90"
        aria-label={removeLabel}
      >
        <X size={12} aria-hidden />
      </button>
    </div>
  );
}

function PlayerPicker({
  players,
  excludeIds,
  onPick,
  placeholder,
  addLabel,
  locale,
}: {
  players: Player[];
  excludeIds: string[];
  onPick: (id: string) => void;
  placeholder: string;
  addLabel: string;
  locale: string;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement | null>(null);

  const fuse = useMemo(
    () =>
      new Fuse(players, {
        keys: ['name.en', 'name.ar'],
        threshold: 0.35,
        ignoreLocation: true,
      }),
    [players]
  );

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  const results = useMemo(() => {
    let list = players.filter((p) => !excludeIds.includes(p.id));
    if (query.trim()) {
      list = fuse
        .search(query)
        .map((r) => r.item)
        .filter((p) => !excludeIds.includes(p.id));
    }
    return list.slice(0, 10);
  }, [players, fuse, query, excludeIds]);

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-1.5 rounded-full border border-dashed border-ink-50/15 bg-ink-50/[0.02] px-3 py-1.5 text-xs text-ink-50/70 transition hover:border-gold-500/40 hover:text-gold-200"
      >
        <Plus size={12} aria-hidden />
        <span>{addLabel}</span>
      </button>
    );
  }

  return (
    <div className="relative">
      <div className="relative">
        <Search
          size={14}
          aria-hidden
          className="pointer-events-none absolute start-3 top-1/2 -translate-y-1/2 text-ink-50/40"
        />
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onBlur={() => setTimeout(() => setOpen(false), 120)}
          placeholder={placeholder}
          className="w-64 rounded-full border border-gold-500/40 bg-ink-900/80 py-1.5 ps-9 pe-4 text-sm text-ink-50 placeholder:text-ink-50/40 focus:border-gold-500/60 focus:outline-none focus:ring-2 focus:ring-gold-500/20"
        />
      </div>
      {results.length > 0 ? (
        <ul className="absolute start-0 z-50 mt-1 max-h-80 w-72 overflow-auto rounded-xl border border-ink-50/[0.06] bg-ink-900/95 p-1 shadow-glow backdrop-blur">
          {results.map((p) => {
            const name = locale === 'ar' ? p.name.ar : p.name.en;
            return (
              <li key={p.id}>
                <button
                  onMouseDown={(e) => {
                    e.preventDefault();
                    onPick(p.id);
                    setQuery('');
                    setOpen(false);
                  }}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-start text-sm text-ink-50/85 transition hover:bg-ink-50/[0.04] hover:text-gold-200"
                >
                  {p.position ? (
                    <span className="rounded-full border border-ink-50/10 px-1.5 py-0 text-[9px] uppercase tracking-wider text-ink-50/50">
                      {p.position}
                    </span>
                  ) : null}
                  <span className="truncate">{name}</span>
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}
