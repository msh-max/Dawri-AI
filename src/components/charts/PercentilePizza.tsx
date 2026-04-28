'use client';

/**
 * Percentile pizza chart — FBref-style radial bar chart.
 *
 * Each segment represents one metric. The segment's RADIUS encodes the
 * player's percentile rank (0–100 vs positional peers). The COLOR encodes
 * the metric category (attacking / possession / defending / discipline).
 *
 * Pure SVG, no charting library — keeps the bundle lean.
 */

import { useTranslations } from 'next-intl';
import { motion } from 'framer-motion';
import { categoryColor, type MetricResult } from '@/lib/percentile';

interface Props {
  results: MetricResult[];
  size?: number;
  /** small: hide labels (for cards); full: show labels */
  variant?: 'small' | 'full';
}

const CENTER = 160;
const INNER = 30;
const OUTER = 130;
const LABEL_RADIUS = 148;

export function PercentilePizza({
  results,
  size = 360,
  variant = 'full',
}: Props) {
  const t = useTranslations('players.stats');

  // Filter out metrics with no data so the segments aren't broken.
  const segments = results.filter((r) => r.percentile !== null);
  const n = segments.length;

  if (n === 0) {
    return (
      <div
        style={{ width: size, height: size }}
        className="grid place-items-center rounded-full border border-ink-50/10 bg-ink-900/40 text-xs text-ink-50/40"
      >
        No comparable peers yet
      </div>
    );
  }

  const sliceAngle = (2 * Math.PI) / n;
  const isSmall = variant === 'small';

  return (
    <svg
      viewBox="0 0 320 320"
      style={{ width: size, height: size }}
      className="overflow-visible"
      role="img"
      aria-label="Percentile pizza chart"
    >
      {/* concentric guide rings */}
      {[25, 50, 75, 100].map((p) => {
        const r = INNER + (OUTER - INNER) * (p / 100);
        return (
          <circle
            key={p}
            cx={CENTER}
            cy={CENTER}
            r={r}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={p === 50 ? 1 : 0.5}
            strokeDasharray={p === 50 ? '2 4' : undefined}
          />
        );
      })}

      {/* segments */}
      {segments.map((seg, i) => {
        const start = i * sliceAngle - Math.PI / 2;
        const end = start + sliceAngle;
        const pad = sliceAngle * 0.06;
        const r =
          INNER + (OUTER - INNER) * Math.max(0, Math.min(1, (seg.percentile ?? 0) / 100));
        const color = categoryColor(seg.category);
        const path = arcPath(CENTER, CENTER, INNER, r, start + pad, end - pad);

        return (
          <motion.path
            key={seg.key}
            d={path}
            fill={color}
            fillOpacity={0.85}
            stroke={color}
            strokeWidth={0.5}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.025, duration: 0.4 }}
            style={{ transformOrigin: `${CENTER}px ${CENTER}px` }}
          />
        );
      })}

      {/* labels */}
      {!isSmall &&
        segments.map((seg, i) => {
          const angle = i * sliceAngle - Math.PI / 2 + sliceAngle / 2;
          const x = CENTER + LABEL_RADIUS * Math.cos(angle);
          const y = CENTER + LABEL_RADIUS * Math.sin(angle);
          const label = t(seg.i18nKey as 'goals');
          return (
            <g key={`l-${seg.key}`}>
              <text
                x={x}
                y={y}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={9}
                fill="rgba(255,255,255,0.55)"
              >
                {label}
              </text>
              <text
                x={x}
                y={y + 11}
                textAnchor="middle"
                fontSize={10}
                fontWeight="600"
                fill={categoryColor(seg.category)}
              >
                {seg.percentile}
              </text>
            </g>
          );
        })}

      {/* center disc */}
      <circle
        cx={CENTER}
        cy={CENTER}
        r={INNER - 2}
        fill="rgba(10,14,12,0.9)"
        stroke="rgba(201,161,74,0.25)"
      />
    </svg>
  );
}

/**
 * Build an SVG arc-path that fills from inner radius to outer radius
 * between two angles. Drawn as a closed wedge.
 */
function arcPath(
  cx: number,
  cy: number,
  innerR: number,
  outerR: number,
  startAngle: number,
  endAngle: number
): string {
  const x1o = cx + outerR * Math.cos(startAngle);
  const y1o = cy + outerR * Math.sin(startAngle);
  const x2o = cx + outerR * Math.cos(endAngle);
  const y2o = cy + outerR * Math.sin(endAngle);
  const x1i = cx + innerR * Math.cos(startAngle);
  const y1i = cy + innerR * Math.sin(startAngle);
  const x2i = cx + innerR * Math.cos(endAngle);
  const y2i = cy + innerR * Math.sin(endAngle);
  const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;
  return [
    `M ${x1i} ${y1i}`,
    `L ${x1o} ${y1o}`,
    `A ${outerR} ${outerR} 0 ${largeArc} 1 ${x2o} ${y2o}`,
    `L ${x2i} ${y2i}`,
    `A ${innerR} ${innerR} 0 ${largeArc} 0 ${x1i} ${y1i}`,
    'Z',
  ].join(' ');
}

export function CategoryLegend() {
  const t = useTranslations('players.categories');
  const items: { key: 'attacking' | 'possession' | 'defending' | 'discipline' }[] = [
    { key: 'attacking' },
    { key: 'possession' },
    { key: 'defending' },
    { key: 'discipline' },
  ];
  return (
    <ul className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-xs">
      {items.map((it) => (
        <li key={it.key} className="flex items-center gap-1.5">
          <span
            className="inline-block h-2 w-2 rounded-full"
            style={{ background: categoryColor(it.key) }}
          />
          <span className="text-ink-50/70">{t(it.key)}</span>
        </li>
      ))}
    </ul>
  );
}
