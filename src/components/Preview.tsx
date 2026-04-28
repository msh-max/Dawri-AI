'use client';

import { motion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import { Star, Swords, Table2, Clock } from 'lucide-react';

export function Preview() {
  const t = useTranslations('preview');

  return (
    <section id="preview" className="relative mx-auto max-w-7xl px-6 py-24">
      <div className="mx-auto mb-14 max-w-2xl text-center">
        <div className="mb-3 text-xs font-medium uppercase tracking-wider text-gold-300/80">
          {t('sectionEyebrow')}
        </div>
        <h2 className="text-balance text-3xl font-semibold tracking-tight md:text-4xl">
          {t('sectionTitle')}
        </h2>
        <p className="mt-4 text-ink-50/70">{t('sectionSubtitle')}</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Player of the Week */}
        <motion.article
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.5 }}
          className="gold-border-gradient relative overflow-hidden rounded-2xl bg-ink-900/60 p-6 backdrop-blur"
        >
          <PlaceholderHeader Icon={Star} label={t('playerOfWeek')} />
          <div className="mt-5 flex items-center gap-4">
            <div className="grid h-16 w-16 flex-shrink-0 place-items-center rounded-full bg-gradient-to-br from-saudi-700 to-saudi-900 ring-1 ring-inset ring-gold-500/20">
              <span className="text-2xl">⚽</span>
            </div>
            <div>
              <div className="text-base font-medium text-ink-50/90">—</div>
              <div className="text-xs text-ink-50/50">{t('comingSoon')}</div>
            </div>
          </div>
          {/* fake radar shimmer */}
          <div className="mt-5 grid h-32 place-items-center rounded-lg border border-ink-50/[0.06] bg-ink-950/60">
            <RadarPlaceholder />
          </div>
          <p className="mt-3 text-xs text-ink-50/50">{t('placeholderText')}</p>
        </motion.article>

        {/* Top Match Today */}
        <motion.article
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.5, delay: 0.05 }}
          className="gold-border-gradient relative overflow-hidden rounded-2xl bg-ink-900/60 p-6 backdrop-blur"
        >
          <PlaceholderHeader Icon={Swords} label={t('topMatch')} />
          <div className="mt-5 grid grid-cols-3 items-center gap-2">
            <TeamCrest />
            <div className="text-center text-2xl font-semibold text-ink-50/90">
              —
            </div>
            <TeamCrest />
          </div>
          <div className="mt-5 space-y-2">
            <ProbBar label={t('winProbability')} percent={48} />
            <ProbBar label={t('expectedGoals')} percent={62} muted />
          </div>
          <p className="mt-3 text-xs text-ink-50/50">{t('placeholderText')}</p>
        </motion.article>

        {/* League Snapshot */}
        <motion.article
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="gold-border-gradient relative overflow-hidden rounded-2xl bg-ink-900/60 p-6 backdrop-blur"
        >
          <PlaceholderHeader Icon={Table2} label={t('leagueSnapshot')} />
          <ul className="mt-5 space-y-2 text-sm">
            {[1, 2, 3, 4, 5].map((i) => (
              <li
                key={i}
                className="flex items-center justify-between rounded-md border border-ink-50/[0.04] bg-ink-950/40 px-3 py-2"
              >
                <span className="flex items-center gap-3">
                  <span className="w-5 text-xs text-ink-50/50">{i}</span>
                  <span className="h-3 w-3 rounded-full bg-saudi-700" />
                  <span className="text-ink-50/70">—</span>
                </span>
                <span className="font-mono text-xs text-ink-50/40">— pts</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-ink-50/50">{t('placeholderText')}</p>
        </motion.article>
      </div>
    </section>
  );
}

function PlaceholderHeader({
  Icon,
  label,
}: {
  Icon: typeof Star;
  label: string;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2 text-sm font-medium text-ink-50/80">
        <Icon size={14} className="text-gold-300" aria-hidden />
        <span>{label}</span>
      </div>
      <span className="inline-flex items-center gap-1 rounded-full border border-gold-500/20 bg-gold-500/[0.06] px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-gold-200">
        <Clock size={10} aria-hidden />
      </span>
    </div>
  );
}

function TeamCrest() {
  return (
    <div className="grid place-items-center">
      <div className="grid h-14 w-14 place-items-center rounded-full bg-gradient-to-br from-saudi-700 to-saudi-900 ring-1 ring-inset ring-gold-500/20">
        <span className="text-lg">🛡️</span>
      </div>
    </div>
  );
}

function ProbBar({
  label,
  percent,
  muted = false,
}: {
  label: string;
  percent: number;
  muted?: boolean;
}) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs text-ink-50/60">
        <span>{label}</span>
        <span className="font-mono">—</span>
      </div>
      <div className="relative h-1.5 overflow-hidden rounded-full bg-ink-50/[0.06]">
        <div
          className={`absolute inset-y-0 ${
            muted ? 'bg-saudi-700/70' : 'bg-gold-shine'
          } animate-shimmer bg-[length:200%_100%]`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

function RadarPlaceholder() {
  return (
    <svg
      viewBox="0 0 120 120"
      className="h-full w-full opacity-50"
      aria-hidden
    >
      {[40, 28, 16].map((r, i) => (
        <polygon
          key={i}
          points={hexagonPoints(60, 60, r)}
          fill="none"
          stroke="currentColor"
          strokeOpacity={0.08 + i * 0.05}
          className="text-gold-400"
        />
      ))}
      <polygon
        points="60,28 92,46 88,82 60,98 32,82 28,46"
        fill="rgba(201,161,74,0.15)"
        stroke="rgb(201 161 74)"
        strokeWidth={1.2}
      />
    </svg>
  );
}

function hexagonPoints(cx: number, cy: number, r: number) {
  const pts: string[] = [];
  for (let i = 0; i < 6; i++) {
    const a = (Math.PI / 3) * i - Math.PI / 2;
    pts.push(`${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`);
  }
  return pts.join(' ');
}
