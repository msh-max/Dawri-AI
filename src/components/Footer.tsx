import { useTranslations } from 'next-intl';
import { Github } from 'lucide-react';

export function Footer() {
  const t = useTranslations('footer');

  return (
    <footer className="border-t border-ink-50/[0.06] bg-ink-950">
      <div className="mx-auto grid max-w-7xl gap-6 px-6 py-10 md:grid-cols-3">
        <div>
          <div className="mb-2 text-sm font-semibold gold-text">Dawri AI</div>
          <p className="text-sm text-ink-50/60">{t('tagline')}</p>
        </div>
        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-50/50">
            {t('dataSources')}
          </div>
          <p className="text-xs leading-relaxed text-ink-50/60">
            {t('attribution')}
          </p>
        </div>
        <div className="md:text-end">
          <a
            href="https://github.com/msh-max/Dawri-AI"
            target="_blank"
            rel="noreferrer noopener"
            className="inline-flex items-center gap-1.5 text-xs text-ink-50/60 hover:text-gold-300"
          >
            <Github size={14} aria-hidden />
            <span>{t('viewSource')}</span>
          </a>
          <p className="mt-3 text-[11px] text-ink-50/40">{t('disclaimer')}</p>
        </div>
      </div>
    </footer>
  );
}
