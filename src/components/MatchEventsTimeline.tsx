import Link from 'next/link';
import { useTranslations } from 'next-intl';
import type { Fixture, MatchEvent, Team } from '@/types/data';

interface Props {
  fixture: Fixture;
  homeTeam: Team | null;
  awayTeam: Team | null;
  locale: string;
}

const EVENT_GLYPH: Record<MatchEvent['type'], string> = {
  goal: '⚽',
  own_goal: '🥅',
  penalty: '🅿️',
  yellow: '🟨',
  red: '🟥',
  sub: '🔁',
};

export function MatchEventsTimeline({
  fixture,
  homeTeam,
  awayTeam,
  locale,
}: Props) {
  const t = useTranslations('matches');
  if (fixture.events.length === 0) return null;

  const sorted = [...fixture.events].sort((a, b) => a.minute - b.minute);

  return (
    <div className="overflow-hidden rounded-2xl border border-ink-50/[0.06] bg-ink-900/40">
      <div className="border-b border-ink-50/[0.06] px-5 py-3 text-sm font-medium text-ink-50/80">
        {t('keyEvents')}
      </div>
      <ol className="divide-y divide-ink-50/[0.04]">
        {sorted.map((e, i) => {
          const isHome = e.team_id === fixture.home_team_id;
          const team = isHome ? homeTeam : awayTeam;
          const playerName = e.player_name
            ? locale === 'ar'
              ? e.player_name.ar
              : e.player_name.en
            : '—';
          const detail = e.detail
            ? locale === 'ar'
              ? e.detail.ar
              : e.detail.en
            : null;

          return (
            <li
              key={i}
              className="grid grid-cols-[60px_1fr_auto] items-center gap-3 px-5 py-3 text-sm"
            >
              <div className="font-mono text-xs text-ink-50/50">
                {e.minute}'
              </div>
              <div
                className={`flex items-center gap-2 ${
                  !isHome ? 'flex-row-reverse text-end justify-self-end' : ''
                }`}
              >
                <span aria-hidden className="text-base">
                  {EVENT_GLYPH[e.type]}
                </span>
                <div className={!isHome ? 'text-end' : 'text-start'}>
                  {e.player_id ? (
                    <Link
                      href={`/${locale}/players/${e.player_id}/`}
                      className="font-medium text-ink-50/90 transition hover:text-gold-200"
                    >
                      {playerName}
                    </Link>
                  ) : (
                    <span className="font-medium text-ink-50/90">
                      {playerName}
                    </span>
                  )}
                  {detail ? (
                    <div className="text-xs text-ink-50/50">{detail}</div>
                  ) : null}
                </div>
              </div>
              <div className="text-[10px] uppercase tracking-wider text-ink-50/40">
                {team
                  ? locale === 'ar'
                    ? team.short_name.ar
                    : team.short_name.en
                  : ''}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
