'use client';

import { motion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import {
  UserSearch,
  TrendingUp,
  Layers,
  Trophy,
  Globe,
  Eye,
  type LucideIcon,
} from 'lucide-react';

const items: { key: string; Icon: LucideIcon }[] = [
  { key: 'playerProfiles', Icon: UserSearch },
  { key: 'matchPreview', Icon: TrendingUp },
  { key: 'compare', Icon: Layers },
  { key: 'titleRace', Icon: Trophy },
  { key: 'bilingual', Icon: Globe },
  { key: 'transparent', Icon: Eye },
];

export function Features() {
  const t = useTranslations('features');

  return (
    <section id="features" className="relative mx-auto max-w-7xl px-6 py-24">
      <div className="mx-auto mb-14 max-w-2xl text-center">
        <div className="mb-3 text-xs font-medium uppercase tracking-wider text-gold-300/80">
          {t('sectionEyebrow')}
        </div>
        <h2 className="text-balance text-3xl font-semibold tracking-tight md:text-4xl">
          {t('sectionTitle')}
        </h2>
        <p className="mt-4 text-ink-50/70">{t('sectionSubtitle')}</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map(({ key, Icon }, idx) => (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 0.5, delay: idx * 0.05 }}
            className="gold-border-gradient relative overflow-hidden rounded-2xl bg-ink-900/60 p-6 backdrop-blur transition hover:bg-ink-900/80"
          >
            <div className="mb-4 inline-grid h-10 w-10 place-items-center rounded-lg bg-saudi-600/15 text-gold-300 ring-1 ring-inset ring-gold-500/20">
              <Icon size={18} aria-hidden />
            </div>
            <h3 className="mb-2 text-lg font-semibold tracking-tight">
              {t(`items.${key}.title` as 'items.playerProfiles.title')}
            </h3>
            <p className="text-sm leading-relaxed text-ink-50/70">
              {t(`items.${key}.description` as 'items.playerProfiles.description')}
            </p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
