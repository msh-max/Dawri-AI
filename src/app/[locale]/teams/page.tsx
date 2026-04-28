import { setRequestLocale, getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { TeamCard } from '@/components/TeamCard';
import { EmptyState } from '@/components/EmptyState';
import { getAllPlayers, getAllTeams } from '@/lib/datasets';
import { isLocale, locales } from '@/i18n/routing';

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
  const t = await getTranslations({ locale, namespace: 'teams' });
  return { title: `${t('pageTitle')} · Dawri AI` };
}

export default async function TeamsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  setRequestLocale(locale);

  const [teams, players, t, tc] = await Promise.all([
    getAllTeams(),
    getAllPlayers(),
    getTranslations({ locale, namespace: 'teams' }),
    getTranslations({ locale, namespace: 'common' }),
  ]);

  const playerCountByTeam = new Map<string, number>();
  for (const p of players) {
    if (!p.team_id) continue;
    playerCountByTeam.set(p.team_id, (playerCountByTeam.get(p.team_id) ?? 0) + 1);
  }

  // Sort teams by name in the active locale
  const sorted = [...teams].sort((a, b) => {
    const aN = locale === 'ar' ? a.name.ar : a.name.en;
    const bN = locale === 'ar' ? b.name.ar : b.name.en;
    return aN.localeCompare(bN, locale);
  });

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

        {sorted.length === 0 ? (
          <EmptyState title={tc('noData')} />
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {sorted.map((team) => (
              <TeamCard
                key={team.id}
                team={team}
                playerCount={playerCountByTeam.get(team.id) ?? 0}
                locale={locale}
              />
            ))}
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}
