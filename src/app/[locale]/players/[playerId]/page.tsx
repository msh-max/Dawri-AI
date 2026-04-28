import { setRequestLocale, getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { Sparkles } from 'lucide-react';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { PlayerHero } from '@/components/PlayerHero';
import { PlayerStatsTable } from '@/components/PlayerStatsTable';
import {
  CategoryLegend,
  PercentilePizza,
} from '@/components/charts/PercentilePizza';
import {
  getAllPlayers,
  getPlayerById,
  getTeamById,
} from '@/lib/datasets';
import { isLocale, locales } from '@/i18n/routing';
import { computePercentiles } from '@/lib/percentile';

export async function generateStaticParams() {
  const players = await getAllPlayers();
  const out: { locale: string; playerId: string }[] = [];
  for (const locale of locales) {
    for (const p of players) out.push({ locale, playerId: p.id });
  }
  return out;
}

export const dynamicParams = false;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; playerId: string }>;
}) {
  const { locale, playerId } = await params;
  if (!isLocale(locale)) return {};
  const player = await getPlayerById(playerId);
  if (!player) return {};
  const name = locale === 'ar' ? player.name.ar : player.name.en;
  return { title: `${name} · Dawri AI` };
}

export default async function PlayerDetailPage({
  params,
}: {
  params: Promise<{ locale: string; playerId: string }>;
}) {
  const { locale, playerId } = await params;
  if (!isLocale(locale)) notFound();
  setRequestLocale(locale);

  const player = await getPlayerById(playerId);
  if (!player) notFound();
  const team = player.team_id ? await getTeamById(player.team_id) : null;
  const allPlayers = await getAllPlayers();
  const t = await getTranslations({ locale, namespace: 'players' });

  const results = computePercentiles(player, allPlayers);

  return (
    <div>
      <Header />
      <main>
        <PlayerHero player={player} team={team} locale={locale} />

        <div className="mx-auto max-w-7xl px-6 py-12">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_1.2fr]">
            <div className="gold-border-gradient relative rounded-2xl bg-ink-900/60 p-6 backdrop-blur">
              <div className="grid place-items-center">
                <PercentilePizza results={results} />
              </div>
              <div className="mt-4">
                <CategoryLegend />
              </div>
            </div>

            <div>
              <PlayerStatsTable results={results} />
            </div>
          </div>

          <section className="mt-8 gold-border-gradient relative overflow-hidden rounded-2xl bg-ink-900/60 p-6 backdrop-blur">
            <div className="mb-3 flex items-center gap-2">
              <span className="grid h-7 w-7 place-items-center rounded-lg bg-gold-shine text-ink-950">
                <Sparkles size={14} aria-hidden />
              </span>
              <h2 className="text-base font-semibold text-ink-50/90">
                {t('scoutReport')}
              </h2>
            </div>
            <p className="text-sm text-ink-50/60">
              {t('scoutReportPending')}
            </p>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
}
