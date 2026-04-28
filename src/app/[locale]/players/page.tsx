import { setRequestLocale, getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { PlayersBrowser } from '@/components/PlayersBrowser';
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
  const t = await getTranslations({ locale, namespace: 'players' });
  return { title: `${t('pageTitle')} · Dawri AI` };
}

export default async function PlayersPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  setRequestLocale(locale);

  const [players, teams, t] = await Promise.all([
    getAllPlayers(),
    getAllTeams(),
    getTranslations({ locale, namespace: 'players' }),
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
        <PlayersBrowser players={players} teams={teams} locale={locale} />
      </main>
      <Footer />
    </div>
  );
}
