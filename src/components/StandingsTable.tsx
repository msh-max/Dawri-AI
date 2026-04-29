import Link from 'next/link';
import { useTranslations } from 'next-intl';
import type { StandingsRow } from '@/lib/standings';

interface Props {
  rows: StandingsRow[];
  locale: string;
}

export function StandingsTable({ rows, locale }: Props) {
  const t = useTranslations('standings');
  return (
    <div className="overflow-hidden rounded-2xl border border-ink-50/[0.06] bg-ink-900/40">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-ink-50/[0.06] text-xs uppercase tracking-wider text-ink-50/50">
              <th className="px-3 py-3 text-start font-medium">{t('rank')}</th>
              <th className="px-3 py-3 text-start font-medium">{t('team')}</th>
              <th className="px-2 py-3 text-end font-medium" title={t('playedFull')}>
                {t('played')}
              </th>
              <th className="px-2 py-3 text-end font-medium" title={t('wonFull')}>
                {t('won')}
              </th>
              <th className="px-2 py-3 text-end font-medium" title={t('drawnFull')}>
                {t('drawn')}
              </th>
              <th className="px-2 py-3 text-end font-medium" title={t('lostFull')}>
                {t('lost')}
              </th>
              <th className="px-2 py-3 text-end font-medium">{t('goalsFor')}</th>
              <th className="px-2 py-3 text-end font-medium">{t('goalsAgainst')}</th>
              <th className="px-2 py-3 text-end font-medium">{t('goalDifference')}</th>
              <th className="px-3 py-3 text-end font-semibold text-gold-200">{t('points')}</th>
              <th className="hidden px-3 py-3 text-end font-medium sm:table-cell">
                {t('form')}
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => {
              const teamName =
                locale === 'ar' ? r.team.name.ar : r.team.name.en;
              return (
                <tr
                  key={r.team.id}
                  className="border-b border-ink-50/[0.04] last:border-b-0 transition hover:bg-ink-50/[0.02]"
                >
                  <td className="px-3 py-2.5 text-ink-50/50">{i + 1}</td>
                  <td className="px-3 py-2.5">
                    <Link
                      href={`/${locale}/teams/${r.team.id}/`}
                      className="flex items-center gap-2 text-ink-50/90 transition hover:text-gold-200"
                    >
                      <span className="grid h-6 w-6 flex-shrink-0 place-items-center overflow-hidden rounded-full bg-gradient-to-br from-saudi-700 to-saudi-900 ring-1 ring-inset ring-gold-500/15">
                        {r.team.crest_url ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={r.team.crest_url}
                            alt={teamName}
                            className="h-4 w-4 object-contain"
                          />
                        ) : (
                          <span className="text-[9px]">🛡️</span>
                        )}
                      </span>
                      <span className="truncate">{teamName}</span>
                    </Link>
                  </td>
                  <td className="px-2 py-2.5 text-end font-mono text-ink-50/75 tabular-nums">
                    {r.played}
                  </td>
                  <td className="px-2 py-2.5 text-end font-mono text-ink-50/75 tabular-nums">
                    {r.won}
                  </td>
                  <td className="px-2 py-2.5 text-end font-mono text-ink-50/75 tabular-nums">
                    {r.drawn}
                  </td>
                  <td className="px-2 py-2.5 text-end font-mono text-ink-50/75 tabular-nums">
                    {r.lost}
                  </td>
                  <td className="px-2 py-2.5 text-end font-mono text-ink-50/75 tabular-nums">
                    {r.goalsFor}
                  </td>
                  <td className="px-2 py-2.5 text-end font-mono text-ink-50/75 tabular-nums">
                    {r.goalsAgainst}
                  </td>
                  <td
                    className={`px-2 py-2.5 text-end font-mono tabular-nums ${
                      r.goalDifference > 0
                        ? 'text-saudi-300'
                        : r.goalDifference < 0
                          ? 'text-gold-300'
                          : 'text-ink-50/60'
                    }`}
                  >
                    {r.goalDifference > 0 ? '+' : ''}
                    {r.goalDifference}
                  </td>
                  <td className="px-3 py-2.5 text-end font-mono text-base font-semibold tabular-nums text-gold-200">
                    {r.points}
                  </td>
                  <td className="hidden px-3 py-2.5 text-end sm:table-cell">
                    <FormPills form={r.form} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FormPills({ form }: { form: ('W' | 'D' | 'L')[] }) {
  if (form.length === 0)
    return <span className="text-ink-50/30">—</span>;
  return (
    <div className="inline-flex items-center gap-1">
      {form.map((r, i) => (
        <span
          key={i}
          className={`grid h-5 w-5 place-items-center rounded-md text-[10px] font-bold ${
            r === 'W'
              ? 'bg-saudi-500/20 text-saudi-300'
              : r === 'D'
                ? 'bg-ink-50/[0.08] text-ink-50/60'
                : 'bg-gold-500/15 text-gold-300'
          }`}
          title={r}
        >
          {r}
        </span>
      ))}
    </div>
  );
}
