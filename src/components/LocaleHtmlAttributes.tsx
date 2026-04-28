'use client';

import { useEffect } from 'react';
import type { Locale } from '@/i18n/routing';

export function LocaleHtmlAttributes({ locale }: { locale: Locale }) {
  useEffect(() => {
    const el = document.documentElement;
    el.lang = locale;
    el.dir = locale === 'ar' ? 'rtl' : 'ltr';
  }, [locale]);
  return null;
}
