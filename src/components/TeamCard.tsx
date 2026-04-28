import Link from 'next/link';
import { useTranslations } from 'next-intl';
import type { Team } from '@/types/data';

export function TeamCard({
  team,
  playerCount,
  locale,
}: {
  team: Team;
  playerCount: number;
  locale: string;
}) {
  const t = useTranslations('teams');
  const name = locale === 'ar' ? team.name.ar : team.name.en;

  return (
    <Link
      href={`/${locale}/teams/${team.id}/`}
      className="gold-border-gradient group relative flex items-center gap-4 overflow-hidden rounded-xl bg-ink-900/60 p-4 transition hover:bg-ink-900/80"
    >
      <div className="grid h-12 w-12 flex-shrink-0 place-items-center overflow-hidden rounded-full bg-gradient-to-br from-saudi-700 to-saudi-900 ring-1 ring-inset ring-gold-500/20">
        {team.crest_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={team.crest_url}
            alt={name}
            className="h-8 w-8 object-contain"
          />
        ) : (
          <span className="text-lg">🛡️</span>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium text-ink-50/90 transition group-hover:text-gold-200">
          {name}
        </div>
        <div className="mt-0.5 text-xs text-ink-50/50">
          {team.founded ? (
            <span>
              {t('founded')} {team.founded}
            </span>
          ) : (
            <span>{t('playerCount', { count: playerCount })}</span>
          )}
        </div>
      </div>
    </Link>
  );
}
