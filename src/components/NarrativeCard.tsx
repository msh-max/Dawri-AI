import { useTranslations } from 'next-intl';
import { Sparkles, Cpu, FileText } from 'lucide-react';
import type { Narrative } from '@/types/data';

interface Props {
  narrative: Narrative;
  title: string;
  locale: string;
}

export function NarrativeCard({ narrative, title, locale }: Props) {
  const t = useTranslations('players');
  const text = locale === 'ar' ? narrative.text.ar : narrative.text.en;
  const isLlm = narrative.source === 'qwen2.5-1.5b';
  const sourceLabel = isLlm
    ? t('narrativeQwen')
    : t('narrativeTemplate');
  const SourceIcon = isLlm ? Cpu : FileText;

  return (
    <section className="gold-border-gradient relative overflow-hidden rounded-2xl bg-ink-900/60 p-6 backdrop-blur">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-gold-shine text-ink-950">
            <Sparkles size={14} aria-hidden />
          </span>
          <h2 className="text-base font-semibold text-ink-50/90">{title}</h2>
        </div>
        <span className="inline-flex items-center gap-1 rounded-full border border-ink-50/10 bg-ink-50/[0.02] px-2 py-0.5 text-[10px] uppercase tracking-wider text-ink-50/50">
          <SourceIcon size={10} aria-hidden />
          <span>
            {t('narrativeBy')} {sourceLabel}
          </span>
        </span>
      </div>
      <p className="text-sm leading-relaxed text-ink-50/80">{text}</p>
    </section>
  );
}
