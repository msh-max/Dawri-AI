'use client';

import { motion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import { ArrowRight, Sparkles } from 'lucide-react';

const stats = [
  { key: 'players', value: '320+' },
  { key: 'matches', value: '306' },
  { key: 'metrics', value: '120+' },
  { key: 'refresh', value: '24h' },
] as const;

export function Hero() {
  const t = useTranslations('hero');

  return (
    <section className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-radial-saudi" />
      <div className="pointer-events-none absolute inset-0 bg-dotgrid opacity-40" />

      <div className="relative mx-auto max-w-7xl px-6 pb-24 pt-20 md:pt-28">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mx-auto max-w-3xl text-center"
        >
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-gold-500/30 bg-gold-500/[0.06] px-3 py-1 text-xs font-medium text-gold-200">
            <Sparkles size={12} aria-hidden />
            <span>{t('eyebrow')}</span>
          </div>

          <h1 className="text-balance text-5xl font-semibold leading-[1.05] tracking-tight md:text-7xl">
            <span className="block text-ink-50">{t('titleLine1')}</span>
            <span className="block text-ink-50">{t('titleLine2')}</span>
            <span className="block gold-text">{t('titleAccent')}</span>
          </h1>

          <p className="mx-auto mt-7 max-w-xl text-balance text-base text-ink-50/70 md:text-lg">
            {t('subtitle')}
          </p>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
            <a
              href="#preview"
              className="group inline-flex items-center gap-2 rounded-full bg-saudi-600 px-6 py-3 text-sm font-medium text-white shadow-glow transition hover:bg-saudi-500"
            >
              {t('ctaPrimary')}
              <ArrowRight
                size={16}
                aria-hidden
                className="transition group-hover:translate-x-0.5 rtl:rotate-180 rtl:group-hover:-translate-x-0.5"
              />
            </a>
            <a
              href="#features"
              className="inline-flex items-center gap-2 rounded-full border border-ink-50/10 bg-ink-50/[0.02] px-6 py-3 text-sm font-medium text-ink-50/80 transition hover:border-gold-500/40 hover:text-gold-200"
            >
              {t('ctaSecondary')}
            </a>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.15 }}
          className="mx-auto mt-16 grid max-w-3xl grid-cols-2 gap-3 md:grid-cols-4"
        >
          {stats.map((s) => (
            <div
              key={s.key}
              className="gold-border-gradient relative rounded-xl bg-ink-900/60 p-4 text-center backdrop-blur"
            >
              <div className="text-2xl font-semibold gold-text">{s.value}</div>
              <div className="mt-1 text-xs text-ink-50/60">
                {t(`stats.${s.key}` as 'stats.players')}
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
