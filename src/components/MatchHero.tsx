import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { ArrowLeft, MapPin } from 'lucide-react';
import type { Fixture, Team } from '@/types/data';

interface Props {
  fixture: Fixture;
  homeTeam: Team | null;
  awayTeam: Team | null;
  locale: string;
}

export function MatchHero({ fixture, homeTeam, awayTeam, locale }: Props) {
  const t = useTranslations('matches');
  const tc = useTranslations('common');
  const isFinished = fixture.status === 'finished';
  const homeName = teamLabel(homeTeam, locale, fixture.home_team_id);
  const awayName = teamLabel(awayTeam, locale, fixture.away_team_id);
  const venueName = fixture.venue
    ? locale === 'ar'
      ? fixture.venue.ar
      : fixture.venue.en
    : null;

  return (
    <section className="relative overflow-hidden border-b border-ink-50/[0.06]">
      <div className="pointer-events-none absolute inset-0 bg-radial-saudi opacity-70" />
      <div className="pointer-events-none absolute inset-0 bg-dotgrid opacity-30" />

      <div className="relative mx-auto max-w-7xl px-6 pb-12 pt-8">
        <Link
          href={`/${locale}/matches/`}
          className="mb-8 inline-flex items-center gap-1.5 text-xs text-ink-50/60 hover:text-gold-300"
        >
          <ArrowLeft size={14} aria-hidden className="rtl:rotate-180" />
          <span>{tc('back')}</span>
        </Link>

        <div className="mb-6 flex flex-wrap items-center gap-3 text-xs text-ink-50/50">
          {fixture.matchweek ? (
            <span className="rounded-full border border-gold-500/20 bg-gold-500/[0.06] px-2.5 py-0.5 text-gold-200">
              {t('matchweek', { n: fixture.matchweek })}
            </span>
          ) : null}
          <span>{formatDate(fixture.date, locale)}</span>
          {fixture.kickoff ? (
            <>
              <span className="text-ink-50/30">·</span>
              <span>{formatTime(fixture.kickoff, locale)}</span>
            </>
          ) : null}
          {venueName ? (
            <>
              <span className="text-ink-50/30">·</span>
              <span className="inline-flex items-center gap-1">
                <MapPin size={11} aria-hidden />
                {venueName}
              </span>
            </>
          ) : null}
        </div>

        <div className="grid grid-cols-1 items-center gap-6 md:grid-cols-[1fr_auto_1fr]">
          <TeamDisplay team={homeTeam} name={homeName} locale={locale} />
          <ScoreBox fixture={fixture} isFinished={isFinished} />
          <TeamDisplay
            team={awayTeam}
            name={awayName}
            locale={locale}
            reverse
          />
        </div>
      </div>
    </section>
  );
}

function TeamDisplay({
  team,
  name,
  locale,
  reverse = false,
}: {
  team: Team | null;
  name: string;
  locale: string;
  reverse?: boolean;
}) {
  const inner = (
    <>
      <div className="grid h-20 w-20 flex-shrink-0 place-items-center overflow-hidden rounded-2xl bg-gradient-to-br from-saudi-700 to-saudi-900 shadow-glow ring-1 ring-inset ring-gold-500/30">
        {team?.crest_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={team.crest_url}
            alt={name}
            className="h-12 w-12 object-contain"
          />
        ) : (
          <span className="text-3xl">🛡️</span>
        )}
      </div>
      <div className={reverse ? 'text-end' : 'text-start'}>
        <div className="text-lg font-semibold tracking-tight text-ink-50/95 md:text-xl">
          {team ? (
            <Link
              href={`/${locale}/teams/${team.id}/`}
              className="transition hover:text-gold-200"
            >
              {name}
            </Link>
          ) : (
            name
          )}
        </div>
        {team?.founded ? (
          <div className="mt-0.5 text-xs text-ink-50/40">
            {team.founded}
          </div>
        ) : null}
      </div>
    </>
  );

  return (
    <div
      className={`flex items-center gap-4 ${
        reverse ? 'flex-row-reverse text-end justify-self-end' : 'justify-self-start'
      }`}
    >
      {inner}
    </div>
  );
}

function ScoreBox({
  fixture,
  isFinished,
}: {
  fixture: Fixture;
  isFinished: boolean;
}) {
  const t = useTranslations('matches.status');
  if (isFinished) {
    return (
      <div className="flex flex-col items-center">
        <div className="rounded-xl border border-gold-500/20 bg-ink-950/70 px-5 py-2 font-mono text-3xl tabular-nums text-ink-50/95">
          <span>{fixture.home_goals ?? '-'}</span>
          <span className="mx-3 text-ink-50/30">:</span>
          <span>{fixture.away_goals ?? '-'}</span>
        </div>
        <span className="mt-2 text-[10px] uppercase tracking-wider text-saudi-300">
          {t('finished')}
        </span>
      </div>
    );
  }
  return (
    <div className="flex flex-col items-center">
      <div className="rounded-xl border border-ink-50/[0.06] bg-ink-950/40 px-5 py-2 text-base text-ink-50/70">
        {t(fixture.status)}
      </div>
    </div>
  );
}

function teamLabel(
  team: Team | null,
  locale: string,
  fallbackId: string
): string {
  if (!team) return fallbackId;
  return locale === 'ar' ? team.name.ar : team.name.en;
}

function formatDate(iso: string, locale: string): string {
  try {
    return new Date(iso + 'T00:00:00Z').toLocaleDateString(
      locale === 'ar' ? 'ar' : 'en-GB',
      { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' }
    );
  } catch {
    return iso;
  }
}

function formatTime(iso: string, locale: string): string {
  try {
    return new Date(iso).toLocaleTimeString(
      locale === 'ar' ? 'ar' : 'en-GB',
      { hour: '2-digit', minute: '2-digit' }
    );
  } catch {
    return '';
  }
}
