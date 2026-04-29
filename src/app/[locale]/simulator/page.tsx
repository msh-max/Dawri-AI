import { setRequestLocale, getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { TitleRace } from '@/components/TitleRace';
import { EmptyState } from '@/components/EmptyState';
import {
  getAllFixtures,
  getAllPredictions,
  getAllTeams,
} from '@/lib/datasets';
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
  const t = await getTranslations({ locale, namespace: 'simulator' });
  return { title: `${t('pageTitle')} · Dawri AI` };
}

export default async function SimulatorPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  setRequestLocale(locale);

  const [teams, fixtures, predictions, t, tc] = await Promise.all([
    getAllTeams(),
    getAllFixtures(),
    getAllPredictions(),
    getTranslations({ locale, namespace: 'simulator' }),
    getTranslations({ locale, namespace: 'common' }),
  ]);

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
        {teams.length === 0 ? (
          <EmptyState title={tc('noData')} />
        ) : (
          <TitleRace
            teams={teams}
            fixtures={fixtures}
            predictions={predictions}
            locale={locale}
          />
        )}
      </main>
      <Footer />
    </div>
  );
}
