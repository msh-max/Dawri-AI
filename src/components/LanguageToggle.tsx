'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLocale, useTranslations } from 'next-intl';
import { Languages } from 'lucide-react';
import { locales, localeNames, type Locale } from '@/i18n/routing';

export function LanguageToggle() {
  const currentLocale = useLocale() as Locale;
  const pathname = usePathname() ?? '/';
  const t = useTranslations('languageToggle');

  const otherLocale: Locale = currentLocale === 'en' ? 'ar' : 'en';
  // Replace the leading /<locale>/ segment with the other locale.
  const newPath = pathname.replace(
    new RegExp(`^/${currentLocale}(/|$)`),
    `/${otherLocale}$1`
  );

  return (
    <Link
      href={newPath || `/${otherLocale}/`}
      className="inline-flex items-center gap-1.5 rounded-full border border-ink-50/10 bg-ink-50/[0.02] px-3 py-1.5 text-xs font-medium text-ink-50/80 transition hover:border-gold-500/40 hover:text-gold-200"
      aria-label={t('switchTo', { language: localeNames[otherLocale] })}
    >
      <Languages size={14} aria-hidden />
      <span>{localeNames[otherLocale]}</span>
    </Link>
  );
}
