'use client';

/**
 * Multi-player radar overlay.
 *
 * Each player is a translucent polygon at a unique color; the union shows
 * who edges who across every metric. Pure SVG; sized to the same 320×320
 * viewbox the PercentilePizza uses so the visual language stays consistent.
 */

import { useTranslations } from 'next-intl';
import { motion } from 'framer-motion';
import type { MetricResult } from '@/lib/percentile';

const PLAYER_COLORS = ['#3ea968', '#c9a14a', '#5b9be2'];

const CENTER = 160;
const INNER = 18;
const OUTER = 130;
const LABEL_RADIUS = 150;

interface PlayerSeries {
  id: string;
  label: string;
  results: MetricResult[];
}

interface Props {
  players: PlayerSeries[];
  size?: number;
}

export function RadarOverlay({ players, size = 360 }: Props) {
  const t = useTranslations('players.stats');
  if (players.length === 0) return null;

  // Use the metric ordering from the first player; assume all share the
  // same metric set (true because `computePercentiles` always uses the
  // same canonical METRICS list).
  const metricOrder = players[0].results.map((r) => ({
    key: r.key,
    i18nKey: r.i18nKey,
  }));
  const n = metricOrder.length;
  if (n === 0) return null;

  const sliceAngle = (2 * Math.PI) / n;

  const polygonFor = (results: MetricResult[]): string => {
    const points: string[] = [];
    for (let i = 0; i < metricOrder.length; i++) {
      const angle = i * sliceAngle - Math.PI / 2;
      const r = results.find((x) => x.key === metricOrder[i].key);
      const pct = r?.percentile ?? 0;
      const radius = INNER + (OUTER - INNER) * (pct / 100);
      const x = CENTER + radius * Math.cos(angle);
      const y = CENTER + radius * Math.sin(angle);
      points.push(`${x},${y}`);
    }
    return points.join(' ');
  };

  return (
    <div className="flex flex-col items-center gap-3">
      <svg
        viewBox="0 0 320 320"
        style={{ width: size, height: size }}
        role="img"
        aria-label="Player comparison radar"
        className="overflow-visible"
      >
        {/* concentric guides */}
        {[25, 50, 75, 100].map((p) => (
          <circle
            key={p}
            cx={CENTER}
            cy={CENTER}
            r={INNER + (OUTER - INNER) * (p / 100)}
            fill="none"
            stroke="rgba(255,255,255,0.05)"
            strokeWidth={p === 50 ? 1 : 0.5}
            strokeDasharray={p === 50 ? '2 4' : undefined}
          />
        ))}
        {/* axis lines */}
        {metricOrder.map((_, i) => {
          const angle = i * sliceAngle - Math.PI / 2;
          const x = CENTER + OUTER * Math.cos(angle);
          const y = CENTER + OUTER * Math.sin(angle);
          return (
            <line
              key={i}
              x1={CENTER}
              y1={CENTER}
              x2={x}
              y2={y}
              stroke="rgba(255,255,255,0.04)"
              strokeWidth={0.5}
            />
          );
        })}

        {/* one polygon per player, painted in ordered z-stack */}
        {players.map((p, idx) => {
          const color = PLAYER_COLORS[idx % PLAYER_COLORS.length];
          return (
            <motion.polygon
              key={p.id}
              points={polygonFor(p.results)}
              fill={color}
              fillOpacity={0.18}
              stroke={color}
              strokeWidth={1.6}
              initial={{ opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: idx * 0.08 }}
              style={{ transformOrigin: `${CENTER}px ${CENTER}px` }}
            />
          );
        })}

        {/* metric labels around the perimeter */}
        {metricOrder.map((m, i) => {
          const angle = i * sliceAngle - Math.PI / 2 + sliceAngle / 2;
          const x = CENTER + LABEL_RADIUS * Math.cos(angle);
          const y = CENTER + LABEL_RADIUS * Math.sin(angle);
          const label = t(m.i18nKey as 'goals');
          return (
            <text
              key={m.key}
              x={x}
              y={y}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={9}
              fill="rgba(255,255,255,0.45)"
            >
              {label}
            </text>
          );
        })}
      </svg>
      <ul className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-xs">
        {players.map((p, idx) => (
          <li key={p.id} className="flex items-center gap-1.5">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: PLAYER_COLORS[idx % PLAYER_COLORS.length] }}
            />
            <span className="text-ink-50/75">{p.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
