import { setRequestLocale, getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { MatchCard } from '@/components/MatchCard';
import { EmptyState } from '@/components/EmptyState';
import { getAllFixtures, getAllTeams } from '@/lib/datasets';
import { isLocale, locales } from '@/i18n/routing';
import type { Fixture, Team } from '@/types/data';

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) return {};
  const t = await getTranslations({ locale, namespace: 'matches' });
  return { title: `${t('pageTitle')} · Dawri AI` };
}

const MS_DAY = 24 * 60 * 60 * 1000;

function bucketize(fixtures: Fixture[]): {
  today: Fixture[];
  upcoming: Fixture[];
  recent: Fixture[];
} {
  // We don't know "today" in a static-export build — approximate using the
  // most recent finished match's date as the reference point so the buckets
  // make sense relative to whatever the latest snapshot contains.
  const finishedDates = fixtures
    .filter((f) => f.status === 'finished' && f.date)
    .map((f) => Date.parse(f.date + 'T00:00:00Z'))
    .sort((a, b) => b - a);

  const ref =
    finishedDates[0] ??
    Math.min(
      ...fixtures.map((f) => Date.parse(f.date + 'T00:00:00Z') || Date.now())
    );

  const today: Fixture[] = [];
  const upcoming: Fixture[] = [];
  const recent: Fixture[] = [];

  for (const f of fixtures) {
    const t = Date.parse(f.date + 'T00:00:00Z');
    if (Number.isNaN(t)) continue;
    const diff = t - ref;
    if (Math.abs(diff) < MS_DAY) today.push(f);
    else if (diff > 0) upcoming.push(f);
    else recent.push(f);
  }

  upcoming.sort((a, b) => a.date.localeCompare(b.date));
  recent.sort((a, b) => b.date.localeCompare(a.date));

  return { today, upcoming, recent };
}

export default async function MatchesPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  setRequestLocale(locale);

  const [fixtures, teams, t, tc] = await Promise.all([
    getAllFixtures(),
    getAllTeams(),
    getTranslations({ locale, namespace: 'matches' }),
    getTranslations({ locale, namespace: 'common' }),
  ]);

  const teamById = new Map<string, Team>();
  for (const team of teams) teamById.set(team.id, team);

  const buckets = bucketize(fixtures);

  return (
    <div>
      <Header />
      <main className="mx-auto max-w-7xl px-6 py-12">
        <div className="mb-8 max-w-2xl">
          <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">
            {t('pageTitle')}
          </h1>
          <p className="mt-2 text-ink-50/60">{t('pageSubtitle')}</p>
        </div>

        {fixtures.length === 0 ? (
          <EmptyState title={t('noFixtures')} hint={tc('noData')} />
        ) : (
          <div className="space-y-10">
            <FixtureGroup
              title={t('today')}
              fixtures={buckets.today}
              teamById={teamById}
              locale={locale}
            />
            <FixtureGroup
              title={t('upcoming')}
              fixtures={buckets.upcoming}
              teamById={teamById}
              locale={locale}
            />
            <FixtureGroup
              title={t('recent')}
              fixtures={buckets.recent}
              teamById={teamById}
              locale={locale}
            />
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}

function FixtureGroup({
  title,
  fixtures,
  teamById,
  locale,
}: {
  title: string;
  fixtures: Fixture[];
  teamById: Map<string, Team>;
  locale: string;
}) {
  if (fixtures.length === 0) return null;
  return (
    <section>
      <h2 className="mb-4 text-xs font-medium uppercase tracking-wider text-gold-300/80">
        {title}
      </h2>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {fixtures.map((f) => (
          <MatchCard
            key={f.id}
            fixture={f}
            homeTeam={teamById.get(f.home_team_id) ?? null}
            awayTeam={teamById.get(f.away_team_id) ?? null}
            locale={locale}
          />
        ))}
      </div>
    </section>
  );
}
