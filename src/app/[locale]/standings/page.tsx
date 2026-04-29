import { setRequestLocale, getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { StandingsTable } from '@/components/StandingsTable';
import { EmptyState } from '@/components/EmptyState';
import { getAllFixtures, getAllTeams } from '@/lib/datasets';
import { isLocale, locales } from '@/i18n/routing';
import { computeStandings } from '@/lib/standings';

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
  const t = await getTranslations({ locale, namespace: 'standings' });
  return { title: `${t('pageTitle')} · Dawri AI` };
}

export default async function StandingsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  setRequestLocale(locale);

  const [teams, fixtures, t] = await Promise.all([
    getAllTeams(),
    getAllFixtures(),
    getTranslations({ locale, namespace: 'standings' }),
  ]);

  const rows = computeStandings(teams, fixtures, locale);
  const anyPlayed = rows.some((r) => r.played > 0);

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
        {anyPlayed ? (
          <StandingsTable rows={rows} locale={locale} />
        ) : (
          <EmptyState title={t('noStandings')} />
        )}
      </main>
      <Footer />
    </div>
  );
}
