import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { ArrowLeft } from 'lucide-react';
import type { Player, Team } from '@/types/data';

interface Props {
  player: Player;
  team: Team | null;
  locale: string;
}

export function PlayerHero({ player, team, locale }: Props) {
  const t = useTranslations('players');
  const tc = useTranslations('common');
  const name = locale === 'ar' ? player.name.ar : player.name.en;
  const altName = locale === 'ar' ? player.name.en : player.name.ar;
  const teamName = team
    ? locale === 'ar'
      ? team.name.ar
      : team.name.en
    : null;
  const positionLabel = player.position
    ? t(`position.${player.position}` as 'position.GK')
    : null;

  return (
    <section className="relative overflow-hidden border-b border-ink-50/[0.06]">
      <div className="pointer-events-none absolute inset-0 bg-radial-saudi opacity-70" />
      <div className="pointer-events-none absolute inset-0 bg-dotgrid opacity-30" />

      <div className="relative mx-auto max-w-7xl px-6 pb-12 pt-8">
        <Link
          href={`/${locale}/players/`}
          className="mb-8 inline-flex items-center gap-1.5 text-xs text-ink-50/60 hover:text-gold-300"
        >
          <ArrowLeft size={14} aria-hidden className="rtl:rotate-180" />
          <span>{tc('back')}</span>
        </Link>

        <div className="flex flex-col items-start gap-6 md:flex-row md:items-end md:gap-10">
          <div className="grid h-32 w-32 flex-shrink-0 place-items-center overflow-hidden rounded-2xl bg-gradient-to-br from-saudi-700 to-saudi-900 shadow-glow ring-1 ring-inset ring-gold-500/30 md:h-40 md:w-40">
            {player.photo_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={player.photo_url}
                alt={name}
                className="h-full w-full object-cover"
              />
            ) : (
              <span className="text-4xl">{initialsOf(name)}</span>
            )}
          </div>

          <div className="flex-1">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              {positionLabel ? (
                <span className="rounded-full border border-gold-500/30 bg-gold-500/[0.06] px-2.5 py-0.5 text-xs font-medium text-gold-200">
                  {positionLabel}
                </span>
              ) : null}
              {teamName ? (
                <Link
                  href={`/${locale}/teams/${player.team_id}/`}
                  className="rounded-full border border-ink-50/10 bg-ink-50/[0.02] px-2.5 py-0.5 text-xs text-ink-50/70 hover:border-gold-500/30 hover:text-gold-200"
                >
                  {teamName}
                </Link>
              ) : null}
            </div>

            <h1 className="text-balance text-4xl font-semibold leading-tight tracking-tight md:text-5xl">
              {name}
            </h1>
            {altName && altName !== name ? (
              <div className="mt-1 text-base text-ink-50/40">{altName}</div>
            ) : null}

            <dl className="mt-6 grid grid-cols-2 gap-x-8 gap-y-3 text-sm sm:grid-cols-4">
              <Field label={t('born')} value={player.birth_date} />
              <Field
                label={t('height')}
                value={player.height_cm ? `${player.height_cm} cm` : null}
              />
              <Field
                label={t('nationality')}
                value={
                  player.nationality
                    ? locale === 'ar'
                      ? player.nationality.ar
                      : player.nationality.en
                    : null
                }
              />
              <Field
                label={t('stats.minutes')}
                value={
                  player.season_stats.minutes
                    ? player.season_stats.minutes.toLocaleString()
                    : null
                }
              />
            </dl>
          </div>
        </div>
      </div>
    </section>
  );
}

function Field({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wider text-ink-50/40">
        {label}
      </dt>
      <dd className="mt-0.5 text-sm text-ink-50/85">
        {value ?? <span className="text-ink-50/30">—</span>}
      </dd>
    </div>
  );
}

function initialsOf(name: string): string {
  const parts = name.split(/\s+/).filter(Boolean);
  return (parts[0]?.[0] ?? '') + (parts[1]?.[0] ?? '');
}
