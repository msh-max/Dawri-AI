import { useTranslations } from 'next-intl';
import { Info } from 'lucide-react';

export function SampleDataBanner({ visible }: { visible: boolean }) {
  if (!visible) return null;
  return <Inner />;
}

function Inner() {
  const t = useTranslations('common');
  return (
    <div className="border-b border-gold-500/15 bg-gold-500/[0.04]">
      <div className="mx-auto flex max-w-7xl items-start gap-2 px-6 py-2 text-xs text-gold-200/80">
        <Info size={13} aria-hidden className="mt-0.5 flex-shrink-0" />
        <span>{t('sampleBanner')}</span>
      </div>
    </div>
  );
}
