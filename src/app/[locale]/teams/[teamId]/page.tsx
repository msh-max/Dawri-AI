import Link from 'next/link';
import { setRequestLocale, getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { PlayerCard } from '@/components/PlayerCard';
import { EmptyState } from '@/components/EmptyState';
import {
  getAllTeams,
  getPlayersForTeam,
  getTeamById,
} from '@/lib/datasets';
import { isLocale, locales } from '@/i18n/routing';
import type { Player, Position } from '@/types/data';

export async function generateStaticParams() {
  const teams = await getAllTeams();
  const out: { locale: string; teamId: string }[] = [];
  for (const locale of locales) {
    for (const t of teams) out.push({ locale, teamId: t.id });
  }
  return out;
}

export const dynamicParams = false;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; teamId: string }>;
}) {
  const { locale, teamId } = await params;
  if (!isLocale(locale)) return {};
  const team = await getTeamById(teamId);
  if (!team) return {};
  const name = locale === 'ar' ? team.name.ar : team.name.en;
  return { title: `${name} · Dawri AI` };
}

const POSITION_ORDER: Position[] = ['GK', 'DF', 'MF', 'FW'];

export default async function TeamDetailPage({
  params,
}: {
  params: Promise<{ locale: string; teamId: string }>;
}) {
  const { locale, teamId } = await params;
  if (!isLocale(locale)) notFound();
  setRequestLocale(locale);

  const team = await getTeamById(teamId);
  if (!team) notFound();
  const players = await getPlayersForTeam(teamId);
  const t = await getTranslations({ locale, namespace: 'teams' });
  const tp = await getTranslations({ locale, namespace: 'players' });
  const tc = await getTranslations({ locale, namespace: 'common' });

  const grouped = new Map<Position | 'OTHER', Player[]>();
  for (const p of players) {
    const key: Position | 'OTHER' = (p.position ?? 'OTHER') as
      | Position
      | 'OTHER';
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key)!.push(p);
  }
  for (const list of grouped.values()) {
    list.sort((a, b) => b.season_stats.minutes - a.season_stats.minutes);
  }

  const name = locale === 'ar' ? team.name.ar : team.name.en;
  const altName = locale === 'ar' ? team.name.en : team.name.ar;

  return (
    <div>
      <Header />
      <main>
        <section className="relative overflow-hidden border-b border-ink-50/[0.06]">
          <div className="pointer-events-none absolute inset-0 bg-radial-saudi opacity-70" />
          <div className="pointer-events-none absolute inset-0 bg-dotgrid opacity-30" />
          <div className="relative mx-auto max-w-7xl px-6 pb-10 pt-8">
            <Link
              href={`/${locale}/teams/`}
              className="mb-8 inline-flex items-center gap-1.5 text-xs text-ink-50/60 hover:text-gold-300"
            >
              <ArrowLeft size={14} aria-hidden className="rtl:rotate-180" />
              <span>{tc('back')}</span>
            </Link>
            <div className="flex items-end gap-6">
              <div className="grid h-24 w-24 flex-shrink-0 place-items-center overflow-hidden rounded-2xl bg-gradient-to-br from-saudi-700 to-saudi-900 shadow-glow ring-1 ring-inset ring-gold-500/30">
                {team.crest_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={team.crest_url}
                    alt={name}
                    className="h-16 w-16 object-contain"
                  />
                ) : (
                  <span className="text-3xl">🛡️</span>
                )}
              </div>
              <div>
                <h1 className="text-balance text-3xl font-semibold tracking-tight md:text-4xl">
                  {name}
                </h1>
                {altName && altName !== name ? (
                  <div className="mt-1 text-sm text-ink-50/40">{altName}</div>
                ) : null}
                <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-ink-50/60">
                  {team.founded ? (
                    <span>
                      {t('founded')} {team.founded}
                    </span>
                  ) : null}
                  <span>{t('playerCount', { count: players.length })}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <div className="mx-auto max-w-7xl px-6 py-12">
          <h2 className="mb-6 text-lg font-semibold tracking-tight">
            {t('squad')}
          </h2>

          {players.length === 0 ? (
            <EmptyState title={t('noSquad')} />
          ) : (
            <div className="space-y-8">
              {POSITION_ORDER.map((pos) => {
                const list = grouped.get(pos);
                if (!list || list.length === 0) return null;
                return (
                  <section key={pos}>
                    <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-gold-300/80">
                      {tp(`position.${pos}` as 'position.GK')}
                    </h3>
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                      {list.map((p) => (
                        <PlayerCard
                          key={p.id}
                          player={p}
                          team={team}
                          locale={locale}
                        />
                      ))}
                    </div>
                  </section>
                );
              })}
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
