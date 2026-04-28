import { useTranslations } from 'next-intl';
import {
  categoryColor,
  type Category,
  type MetricResult,
} from '@/lib/percentile';

const CATEGORIES: Category[] = [
  'attacking',
  'possession',
  'defending',
  'discipline',
];

export function PlayerStatsTable({
  results,
}: {
  results: MetricResult[];
}) {
  const t = useTranslations('players');

  return (
    <div className="overflow-hidden rounded-2xl border border-ink-50/[0.06] bg-ink-900/40">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-ink-50/[0.06] text-xs uppercase tracking-wider text-ink-50/50">
            <th className="px-4 py-3 text-start font-medium">
              {t('seasonStats')}
            </th>
            <th className="px-3 py-3 text-end font-medium">{t('raw')}</th>
            <th className="px-3 py-3 text-end font-medium">{t('perNinety')}</th>
            <th className="px-4 py-3 text-end font-medium">
              {t('percentile')}
            </th>
          </tr>
        </thead>
        <tbody>
          {CATEGORIES.flatMap((cat) => {
            const inCat = results.filter((r) => r.category === cat);
            if (inCat.length === 0) return [];
            return [
              <tr
                key={`${cat}-h`}
                className="border-b border-ink-50/[0.04] bg-ink-950/40"
              >
                <td
                  colSpan={4}
                  className="px-4 py-1.5 text-xs font-medium uppercase tracking-wider"
                  style={{ color: categoryColor(cat) }}
                >
                  {t(`categories.${cat}` as 'categories.attacking')}
                </td>
              </tr>,
              ...inCat.map((r) => (
                <tr
                  key={r.key}
                  className="border-b border-ink-50/[0.04] last:border-b-0"
                >
                  <td className="px-4 py-2.5 text-ink-50/80">
                    {t(`stats.${r.i18nKey}` as 'stats.goals')}
                  </td>
                  <td className="px-3 py-2.5 text-end font-mono text-ink-50/80">
                    {r.raw === null ? '—' : formatRaw(r.raw)}
                  </td>
                  <td className="px-3 py-2.5 text-end font-mono text-ink-50/60">
                    {r.perNinety && r.normalized !== null
                      ? r.normalized.toFixed(2)
                      : '—'}
                  </td>
                  <td className="px-4 py-2.5 text-end">
                    <PercentilePill value={r.percentile} />
                  </td>
                </tr>
              )),
            ];
          })}
        </tbody>
      </table>
    </div>
  );
}

function formatRaw(v: number): string {
  if (Number.isInteger(v)) return v.toString();
  return v.toFixed(1);
}

function PercentilePill({ value }: { value: number | null }) {
  if (value === null) {
    return <span className="text-ink-50/30">—</span>;
  }
  const color =
    value >= 75
      ? 'rgb(62, 169, 104)'
      : value >= 50
        ? 'rgb(201, 161, 74)'
        : value >= 25
          ? 'rgb(168, 132, 59)'
          : 'rgb(226, 91, 91)';
  return (
    <span
      className="inline-flex w-12 justify-end rounded-full bg-ink-950 px-2 py-0.5 font-mono text-xs"
      style={{ color }}
    >
      {value}
    </span>
  );
}
