import { setRequestLocale, getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { LeaderboardCard } from '@/components/LeaderboardCard';
import { EmptyState } from '@/components/EmptyState';
import { getAllPlayers, getAllTeams } from '@/lib/datasets';
import { isLocale, locales } from '@/i18n/routing';
import type { Player, Team } from '@/types/data';

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
  const t = await getTranslations({ locale, namespace: 'leaderboards' });
  return { title: `${t('pageTitle')} · Dawri AI` };
}

const TOP_N = 5;
const MIN_MINUTES = 270;

interface Entry {
  player: Player;
  team: Team | null;
  value: number;
  display: string;
}

function topBy(
  players: Player[],
  teamById: Map<string, Team>,
  extract: (p: Player) => number | null | undefined,
  format: (v: number) => string,
  filter: (p: Player) => boolean = () => true
): Entry[] {
  return players
    .filter(filter)
    .map((p) => {
      const value = extract(p);
      if (value === null || value === undefined) return null;
      return {
        player: p,
        team: p.team_id ? teamById.get(p.team_id) ?? null : null,
        value,
        display: format(value),
      };
    })
    .filter((e): e is Entry => e !== null)
    .sort((a, b) => b.value - a.value)
    .slice(0, TOP_N);
}

export default async function LeaderboardsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  setRequestLocale(locale);

  const [players, teams, t, tc] = await Promise.all([
    getAllPlayers(),
    getAllTeams(),
    getTranslations({ locale, namespace: 'leaderboards' }),
    getTranslations({ locale, namespace: 'common' }),
  ]);

  const teamById = new Map<string, Team>();
  for (const team of teams) teamById.set(team.id, team);

  const eligible = (p: Player) => p.season_stats.minutes >= MIN_MINUTES;

  const topScorers = topBy(
    players,
    teamById,
    (p) => p.season_stats.goals,
    (v) => v.toString()
  );
  const topAssists = topBy(
    players,
    teamById,
    (p) => p.season_stats.assists,
    (v) => v.toString()
  );
  const topGA = topBy(
    players,
    teamById,
    (p) => p.season_stats.goals + p.season_stats.assists,
    (v) => v.toString()
  );
  const topXg = topBy(
    players,
    teamById,
    (p) => p.season_stats.xg,
    (v) => v.toFixed(1)
  );
  const topXa = topBy(
    players,
    teamById,
    (p) => p.season_stats.xa,
    (v) => v.toFixed(1)
  );
  const topPasser = topBy(
    players,
    teamById,
    (p) => p.season_stats.pass_completion_pct,
    (v) => `${v.toFixed(1)}%`,
    eligible
  );
  const topTacklers = topBy(
    players,
    teamById,
    (p) => {
      const tk = p.season_stats.tackles;
      const min = p.season_stats.minutes;
      if (tk === null || tk === undefined || min <= 0) return null;
      return (tk * 90) / min;
    },
    (v) => v.toFixed(2),
    eligible
  );
  const topInterceptors = topBy(
    players,
    teamById,
    (p) => {
      const ic = p.season_stats.interceptions;
      const min = p.season_stats.minutes;
      if (ic === null || ic === undefined || min <= 0) return null;
      return (ic * 90) / min;
    },
    (v) => v.toFixed(2),
    eligible
  );

  const anyData = players.length > 0;

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

        {!anyData ? (
          <EmptyState title={tc('noData')} />
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            <LeaderboardCard
              title={t('topScorers')}
              entries={topScorers}
              locale={locale}
              accentColor="#e25b5b"
            />
            <LeaderboardCard
              title={t('topAssists')}
              entries={topAssists}
              locale={locale}
              accentColor="#5b9be2"
            />
            <LeaderboardCard
              title={t('topGoalContributions')}
              entries={topGA}
              locale={locale}
              accentColor="#c9a14a"
            />
            <LeaderboardCard
              title={t('topXg')}
              entries={topXg}
              locale={locale}
              accentColor="#e25b5b"
            />
            <LeaderboardCard
              title={t('topXa')}
              entries={topXa}
              locale={locale}
              accentColor="#5b9be2"
            />
            <LeaderboardCard
              title={t('topPasser')}
              entries={topPasser}
              locale={locale}
              accentColor="#3ea968"
            />
            <LeaderboardCard
              title={t('topTacklers')}
              entries={topTacklers}
              locale={locale}
              accentColor="#3ea968"
            />
            <LeaderboardCard
              title={t('topInterceptors')}
              entries={topInterceptors}
              locale={locale}
              accentColor="#3ea968"
            />
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}
