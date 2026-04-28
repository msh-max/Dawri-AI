'use client';

/**
 * xG flow chart — cumulative expected goals over the course of a match.
 *
 * Two stepped lines (home + away) with subtle area fills, plus dotted
 * markers wherever a goal was scored. Pure SVG; no charting library.
 */

import { useTranslations } from 'next-intl';
import { motion } from 'framer-motion';
import type { MatchEvent, XgFlowPoint } from '@/types/data';

interface Props {
  flow: XgFlowPoint[];
  events: MatchEvent[];
  homeTeamId: string;
  awayTeamId: string;
  homeName: string;
  awayName: string;
}

const W = 720;
const H = 240;
const PAD = { top: 24, right: 24, bottom: 28, left: 36 };

const HOME_COLOR = '#3ea968'; // saudi green
const AWAY_COLOR = '#c9a14a'; // gold

export function XgFlowChart({
  flow,
  events,
  homeTeamId,
  awayTeamId,
  homeName,
  awayName,
}: Props) {
  const t = useTranslations('matches');
  if (flow.length < 2) return null;

  const lastMin = Math.max(90, flow[flow.length - 1].minute);
  const maxXg = Math.max(
    1,
    ...flow.map((p) => Math.max(p.home_xg, p.away_xg))
  );

  const xScale = (m: number) =>
    PAD.left + (m / lastMin) * (W - PAD.left - PAD.right);
  const yScale = (v: number) =>
    H - PAD.bottom - (v / maxXg) * (H - PAD.top - PAD.bottom);

  // build stepped path: each segment goes horizontal then vertical
  const stepPath = (key: 'home_xg' | 'away_xg'): string => {
    const pts = flow.map((p) => ({ x: xScale(p.minute), y: yScale(p[key]) }));
    let d = `M ${pts[0].x} ${pts[0].y}`;
    for (let i = 1; i < pts.length; i++) {
      d += ` L ${pts[i].x} ${pts[i - 1].y} L ${pts[i].x} ${pts[i].y}`;
    }
    return d;
  };

  const areaPath = (key: 'home_xg' | 'away_xg'): string => {
    const line = stepPath(key);
    const last = flow[flow.length - 1];
    const baseline = yScale(0);
    return `${line} L ${xScale(last.minute)} ${baseline} L ${xScale(flow[0].minute)} ${baseline} Z`;
  };

  // gridlines every 15 mins, every 0.5 xG
  const minGrid: number[] = [];
  for (let m = 15; m < lastMin; m += 15) minGrid.push(m);
  const xgGrid: number[] = [];
  for (let v = 0.5; v <= maxXg; v += 0.5) xgGrid.push(v);

  const goalEvents = events.filter(
    (e) => e.type === 'goal' || e.type === 'own_goal' || e.type === 'penalty'
  );

  const finalHome = flow[flow.length - 1].home_xg;
  const finalAway = flow[flow.length - 1].away_xg;

  return (
    <div className="overflow-hidden rounded-2xl border border-ink-50/[0.06] bg-ink-900/40 p-5 backdrop-blur">
      <div className="mb-3 flex items-center justify-between">
        <div className="text-sm font-medium text-ink-50/80">
          {t('expectedGoalsTimeline')}
        </div>
        <div className="flex items-center gap-4 text-xs">
          <Legend color={HOME_COLOR} label={homeName} value={finalHome} />
          <Legend color={AWAY_COLOR} label={awayName} value={finalAway} />
        </div>
      </div>

      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-auto w-full"
        role="img"
        aria-label="xG flow"
      >
        {/* gridlines */}
        {xgGrid.map((v) => (
          <line
            key={`y-${v}`}
            x1={PAD.left}
            x2={W - PAD.right}
            y1={yScale(v)}
            y2={yScale(v)}
            stroke="rgba(255,255,255,0.05)"
            strokeWidth={1}
          />
        ))}
        {/* axis */}
        <line
          x1={PAD.left}
          x2={W - PAD.right}
          y1={H - PAD.bottom}
          y2={H - PAD.bottom}
          stroke="rgba(255,255,255,0.15)"
          strokeWidth={1}
        />
        {/* x-axis labels */}
        {[0, 15, 30, 45, 60, 75, 90].map((m) =>
          m > lastMin ? null : (
            <text
              key={`x-${m}`}
              x={xScale(m)}
              y={H - 8}
              textAnchor="middle"
              fontSize={10}
              fill="rgba(255,255,255,0.4)"
            >
              {m}'
            </text>
          )
        )}
        {/* y-axis labels */}
        {[0, ...xgGrid].map((v) => (
          <text
            key={`yl-${v}`}
            x={PAD.left - 6}
            y={yScale(v) + 3}
            textAnchor="end"
            fontSize={10}
            fill="rgba(255,255,255,0.4)"
          >
            {v.toFixed(1)}
          </text>
        ))}
        {/* HT line */}
        {lastMin >= 45 ? (
          <line
            x1={xScale(45)}
            x2={xScale(45)}
            y1={PAD.top}
            y2={H - PAD.bottom}
            stroke="rgba(255,255,255,0.08)"
            strokeDasharray="2 4"
          />
        ) : null}

        {/* areas */}
        <motion.path
          d={areaPath('away_xg')}
          fill={AWAY_COLOR}
          fillOpacity={0.10}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4 }}
        />
        <motion.path
          d={areaPath('home_xg')}
          fill={HOME_COLOR}
          fillOpacity={0.12}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4 }}
        />

        {/* lines */}
        <motion.path
          d={stepPath('away_xg')}
          fill="none"
          stroke={AWAY_COLOR}
          strokeWidth={1.8}
          strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.9, ease: 'easeOut' }}
        />
        <motion.path
          d={stepPath('home_xg')}
          fill="none"
          stroke={HOME_COLOR}
          strokeWidth={1.8}
          strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.9, ease: 'easeOut' }}
        />

        {/* goal markers */}
        {goalEvents.map((g, i) => {
          const isHome = g.team_id === homeTeamId;
          const color = isHome ? HOME_COLOR : AWAY_COLOR;
          // anchor to the closest flow point at or after the event
          const fp =
            flow.find((p) => p.minute >= g.minute) ?? flow[flow.length - 1];
          const cx = xScale(g.minute);
          const cy = yScale(isHome ? fp.home_xg : fp.away_xg);
          return (
            <g key={`gm-${i}`}>
              <line
                x1={cx}
                x2={cx}
                y1={cy}
                y2={H - PAD.bottom}
                stroke={color}
                strokeOpacity={0.4}
                strokeDasharray="2 3"
              />
              <circle
                cx={cx}
                cy={cy}
                r={5}
                fill="rgb(10,14,12)"
                stroke={color}
                strokeWidth={2}
              />
              <text
                x={cx}
                y={cy - 10}
                textAnchor="middle"
                fontSize={10}
                fontWeight={600}
                fill={color}
              >
                ⚽
              </text>
            </g>
          );
        })}

        {/* away suffix ignored for axis labels in RTL — the chart is
            inherently LTR (time progresses left→right). */}
      </svg>
    </div>
  );
}

function Legend({
  color,
  label,
  value,
}: {
  color: string;
  label: string;
  value: number;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <span
        className="inline-block h-2 w-2 rounded-full"
        style={{ background: color }}
      />
      <span className="text-ink-50/70">{label}</span>
      <span className="font-mono text-ink-50/85">{value.toFixed(1)}</span>
    </div>
  );
}
