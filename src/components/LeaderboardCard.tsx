import Link from 'next/link';
import type { Player, Team } from '@/types/data';

interface Entry {
  player: Player;
  team: Team | null;
  value: number;
  display: string;
}

interface Props {
  title: string;
  entries: Entry[];
  locale: string;
  accentColor?: string;
}

export function LeaderboardCard({
  title,
  entries,
  locale,
  accentColor = '#c9a14a',
}: Props) {
  return (
    <section className="gold-border-gradient relative overflow-hidden rounded-2xl bg-ink-900/60 p-5 backdrop-blur">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-ink-50/90">{title}</h2>
        <span
          className="h-1.5 w-12 rounded-full"
          style={{ background: accentColor, opacity: 0.7 }}
        />
      </div>
      {entries.length === 0 ? (
        <p className="text-xs text-ink-50/40">—</p>
      ) : (
        <ol className="space-y-2">
          {entries.map((e, i) => {
            const playerName =
              locale === 'ar' ? e.player.name.ar : e.player.name.en;
            const teamName = e.team
              ? locale === 'ar'
                ? e.team.short_name.ar
                : e.team.short_name.en
              : '';
            return (
              <li key={e.player.id}>
                <Link
                  href={`/${locale}/players/${e.player.id}/`}
                  className="group flex items-center gap-3 rounded-lg px-2 py-1.5 transition hover:bg-ink-50/[0.03]"
                >
                  <span className="w-4 text-center font-mono text-xs text-ink-50/40">
                    {i + 1}
                  </span>
                  <div className="grid h-7 w-7 flex-shrink-0 place-items-center overflow-hidden rounded-full bg-gradient-to-br from-saudi-700 to-saudi-900 ring-1 ring-inset ring-gold-500/15">
                    {e.player.photo_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={e.player.photo_url}
                        alt={playerName}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <span className="text-[10px]">⚽</span>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm text-ink-50/85 transition group-hover:text-gold-200">
                      {playerName}
                    </div>
                    <div className="truncate text-[11px] text-ink-50/45">
                      {teamName}
                    </div>
                  </div>
                  <span
                    className="font-mono text-sm font-semibold tabular-nums"
                    style={{ color: accentColor }}
                  >
                    {e.display}
                  </span>
                </Link>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
