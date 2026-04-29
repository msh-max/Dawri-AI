import { setRequestLocale, getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { Sparkles } from 'lucide-react';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { MatchHero } from '@/components/MatchHero';
import { MatchEventsTimeline } from '@/components/MatchEventsTimeline';
import { NarrativeCard } from '@/components/NarrativeCard';
import { PredictionPanel } from '@/components/PredictionPanel';
import { XgFlowChart } from '@/components/charts/XgFlowChart';
import {
  getAllFixtures,
  getFixtureById,
  getPredictionForFixture,
  getTeamById,
} from '@/lib/datasets';
import { isLocale, locales } from '@/i18n/routing';

export async function generateStaticParams() {
  const fixtures = await getAllFixtures();
  const out: { locale: string; matchId: string }[] = [];
  for (const locale of locales) {
    for (const f of fixtures) out.push({ locale, matchId: f.id });
  }
  return out;
}

export const dynamicParams = false;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; matchId: string }>;
}) {
  const { locale, matchId } = await params;
  if (!isLocale(locale)) return {};
  const fixture = await getFixtureById(matchId);
  if (!fixture) return {};
  const home = await getTeamById(fixture.home_team_id);
  const away = await getTeamById(fixture.away_team_id);
  const homeName = home
    ? locale === 'ar'
      ? home.short_name.ar
      : home.short_name.en
    : fixture.home_team_id;
  const awayName = away
    ? locale === 'ar'
      ? away.short_name.ar
      : away.short_name.en
    : fixture.away_team_id;
  return { title: `${homeName} vs ${awayName} · Dawri AI` };
}

export default async function MatchDetailPage({
  params,
}: {
  params: Promise<{ locale: string; matchId: string }>;
}) {
  const { locale, matchId } = await params;
  if (!isLocale(locale)) notFound();
  setRequestLocale(locale);

  const fixture = await getFixtureById(matchId);
  if (!fixture) notFound();
  const [homeTeam, awayTeam, prediction, t] = await Promise.all([
    getTeamById(fixture.home_team_id),
    getTeamById(fixture.away_team_id),
    getPredictionForFixture(matchId),
    getTranslations({ locale, namespace: 'matches' }),
  ]);

  const homeName = homeTeam
    ? locale === 'ar'
      ? homeTeam.short_name.ar
      : homeTeam.short_name.en
    : fixture.home_team_id;
  const awayName = awayTeam
    ? locale === 'ar'
      ? awayTeam.short_name.ar
      : awayTeam.short_name.en
    : fixture.away_team_id;

  const isFinished = fixture.status === 'finished';
  const hasFlow = isFinished && fixture.xg_flow.length >= 2;
  const hasEvents = fixture.events.length > 0;

  return (
    <div>
      <Header />
      <main>
        <MatchHero
          fixture={fixture}
          homeTeam={homeTeam}
          awayTeam={awayTeam}
          locale={locale}
        />

        <div className="mx-auto max-w-7xl space-y-6 px-6 py-12">
          {!isFinished && prediction ? (
            <PredictionPanel
              prediction={prediction}
              homeTeam={homeTeam}
              awayTeam={awayTeam}
              locale={locale}
            />
          ) : null}

          {!isFinished && fixture.preview ? (
            <NarrativeCard
              narrative={fixture.preview}
              title={t('matchPreview')}
              locale={locale}
            />
          ) : null}

          {hasFlow ? (
            <XgFlowChart
              flow={fixture.xg_flow}
              events={fixture.events}
              homeTeamId={fixture.home_team_id}
              awayTeamId={fixture.away_team_id}
              homeName={homeName}
              awayName={awayName}
            />
          ) : null}

          {isFinished && fixture.recap ? (
            <NarrativeCard
              narrative={fixture.recap}
              title={t('matchRecap')}
              locale={locale}
            />
          ) : null}

          {hasEvents ? (
            <MatchEventsTimeline
              fixture={fixture}
              homeTeam={homeTeam}
              awayTeam={awayTeam}
              locale={locale}
            />
          ) : null}

          {!isFinished && !prediction ? (
            <section className="gold-border-gradient relative overflow-hidden rounded-2xl bg-ink-900/60 p-6 backdrop-blur">
              <div className="mb-3 flex items-center gap-2">
                <span className="grid h-7 w-7 place-items-center rounded-lg bg-gold-shine text-ink-950">
                  <Sparkles size={14} aria-hidden />
                </span>
                <h2 className="text-base font-semibold text-ink-50/90">
                  {t('prediction')}
                </h2>
              </div>
              <p className="text-sm text-ink-50/60">
                {t('predictionPending')}
              </p>
            </section>
          ) : null}
        </div>
      </main>
      <Footer />
    </div>
  );
}
