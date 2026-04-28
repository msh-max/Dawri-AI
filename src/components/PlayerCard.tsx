import Link from 'next/link';
import { useTranslations } from 'next-intl';
import type { Player, Team } from '@/types/data';

interface Props {
  player: Player;
  team?: Team | null;
  locale: string;
}

export function PlayerCard({ player, team, locale }: Props) {
  const t = useTranslations('players');
  const name = locale === 'ar' ? player.name.ar : player.name.en;
  const teamName = team
    ? locale === 'ar'
      ? team.short_name.ar
      : team.short_name.en
    : null;

  return (
    <Link
      href={`/${locale}/players/${player.id}/`}
      className="gold-border-gradient group relative flex items-center gap-4 overflow-hidden rounded-xl bg-ink-900/60 p-4 transition hover:bg-ink-900/80"
    >
      <div className="grid h-14 w-14 flex-shrink-0 place-items-center overflow-hidden rounded-full bg-gradient-to-br from-saudi-700 to-saudi-900 ring-1 ring-inset ring-gold-500/20">
        {player.photo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={player.photo_url}
            alt={name}
            className="h-full w-full object-cover"
          />
        ) : (
          <span className="text-xl">{initialsOf(name)}</span>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium text-ink-50/90 transition group-hover:text-gold-200">
          {name}
        </div>
        <div className="mt-0.5 flex items-center gap-2 text-xs text-ink-50/50">
          {player.position ? (
            <span className="rounded-full border border-ink-50/10 px-1.5 py-0.5 text-[10px] uppercase tracking-wider">
              {player.position}
            </span>
          ) : null}
          {teamName ? <span className="truncate">{teamName}</span> : null}
        </div>
      </div>
      <div className="hidden flex-shrink-0 text-end text-xs text-ink-50/50 sm:block">
        <div>
          <span className="font-mono text-ink-50/80">
            {player.season_stats.goals}
          </span>{' '}
          {t('stats.goals')}
        </div>
        <div>
          <span className="font-mono text-ink-50/80">
            {player.season_stats.assists}
          </span>{' '}
          {t('stats.assists')}
        </div>
      </div>
    </Link>
  );
}

function initialsOf(name: string): string {
  const parts = name.split(/\s+/).filter(Boolean);
  return (parts[0]?.[0] ?? '') + (parts[1]?.[0] ?? '');
}
