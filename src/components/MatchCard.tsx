import Link from 'next/link';
import { useTranslations } from 'next-intl';
import type { Fixture, Team } from '@/types/data';

interface Props {
  fixture: Fixture;
  homeTeam: Team | null;
  awayTeam: Team | null;
  locale: string;
}

export function MatchCard({ fixture, homeTeam, awayTeam, locale }: Props) {
  const t = useTranslations('matches');

  const homeName = teamLabel(homeTeam, locale, fixture.home_team_id);
  const awayName = teamLabel(awayTeam, locale, fixture.away_team_id);
  const isFinished = fixture.status === 'finished';

  return (
    <Link
      href={`/${locale}/matches/${fixture.id}/`}
      className="gold-border-gradient group relative block overflow-hidden rounded-xl bg-ink-900/60 p-4 transition hover:bg-ink-900/80"
    >
      <div className="mb-3 flex items-center justify-between text-[10px] uppercase tracking-wider">
        <span className="text-ink-50/40">
          {fixture.matchweek
            ? t('matchweek', { n: fixture.matchweek })
            : formatDate(fixture.date, locale)}
        </span>
        <StatusBadge status={fixture.status} />
      </div>

      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
        <TeamSide team={homeTeam} name={homeName} side="home" />
        <ScoreOrTime
          fixture={fixture}
          isFinished={isFinished}
          locale={locale}
        />
        <TeamSide team={awayTeam} name={awayName} side="away" />
      </div>

      {isFinished &&
      (fixture.home_xg !== null || fixture.away_xg !== null) ? (
        <div className="mt-3 flex items-center justify-between text-[10px] text-ink-50/50">
          <span>
            xG{' '}
            <span className="font-mono text-ink-50/75">
              {(fixture.home_xg ?? 0).toFixed(1)}
            </span>
          </span>
          <span>
            xG{' '}
            <span className="font-mono text-ink-50/75">
              {(fixture.away_xg ?? 0).toFixed(1)}
            </span>
          </span>
        </div>
      ) : null}
    </Link>
  );
}

function StatusBadge({ status }: { status: Fixture['status'] }) {
  const t = useTranslations('matches.status');
  const map: Record<Fixture['status'], string> = {
    scheduled: 'border-ink-50/10 text-ink-50/50',
    live: 'border-red-400/40 bg-red-400/10 text-red-300 animate-pulse',
    finished: 'border-saudi-500/30 bg-saudi-500/10 text-saudi-300',
    postponed: 'border-gold-500/30 bg-gold-500/10 text-gold-200',
  };
  return (
    <span
      className={`rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider ${map[status]}`}
    >
      {t(status)}
    </span>
  );
}

function TeamSide({
  team,
  name,
  side,
}: {
  team: Team | null;
  name: string;
  side: 'home' | 'away';
}) {
  const align = side === 'home' ? 'text-start' : 'text-end';
  return (
    <div className={`flex items-center gap-2 ${side === 'away' ? 'flex-row-reverse' : ''}`}>
      <div className="grid h-8 w-8 flex-shrink-0 place-items-center overflow-hidden rounded-full bg-gradient-to-br from-saudi-700 to-saudi-900 ring-1 ring-inset ring-gold-500/15">
        {team?.crest_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={team.crest_url}
            alt={name}
            className="h-5 w-5 object-contain"
          />
        ) : (
          <span className="text-[10px]">🛡️</span>
        )}
      </div>
      <div className={`min-w-0 flex-1 ${align}`}>
        <div className="truncate text-sm font-medium text-ink-50/90">
          {name}
        </div>
      </div>
    </div>
  );
}

function ScoreOrTime({
  fixture,
  isFinished,
  locale,
}: {
  fixture: Fixture;
  isFinished: boolean;
  locale: string;
}) {
  if (isFinished) {
    return (
      <div className="rounded-md bg-ink-950/60 px-3 py-1.5 font-mono text-base tabular-nums text-ink-50/95">
        <span>{fixture.home_goals ?? '-'}</span>
        <span className="mx-1.5 text-ink-50/30">:</span>
        <span>{fixture.away_goals ?? '-'}</span>
      </div>
    );
  }
  return (
    <div className="rounded-md border border-ink-50/[0.08] bg-ink-950/40 px-3 py-1.5 text-center text-xs">
      <div className="text-ink-50/60">{formatTime(fixture.kickoff, locale)}</div>
    </div>
  );
}

function teamLabel(team: Team | null, locale: string, fallbackId: string): string {
  if (!team) return fallbackId;
  return locale === 'ar' ? team.short_name.ar : team.short_name.en;
}

function formatDate(iso: string, locale: string): string {
  try {
    return new Date(iso + 'T00:00:00Z').toLocaleDateString(
      locale === 'ar' ? 'ar' : 'en-GB',
      { day: 'numeric', month: 'short' }
    );
  } catch {
    return iso;
  }
}

function formatTime(iso: string | null, locale: string): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleTimeString(
      locale === 'ar' ? 'ar' : 'en-GB',
      { hour: '2-digit', minute: '2-digit' }
    );
  } catch {
    return '—';
  }
}
