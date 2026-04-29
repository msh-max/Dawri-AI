import Link from 'next/link';
import { useTranslations, useLocale } from 'next-intl';
import { Logo } from './Logo';
import { LanguageToggle } from './LanguageToggle';

export function Header() {
  const t = useTranslations('nav');
  const locale = useLocale();

  const navItems = [
    { href: `/${locale}/`, label: t('home') },
    { href: `/${locale}/matches/`, label: t('matches') },
    { href: `/${locale}/standings/`, label: t('standings') },
    { href: `/${locale}/leaderboards/`, label: t('leaderboards') },
    { href: `/${locale}/players/`, label: t('players') },
    { href: `/${locale}/teams/`, label: t('teams') },
    { href: `/${locale}/compare/`, label: t('compare') },
    { href: `/${locale}/simulator/`, label: t('simulator') },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-ink-50/[0.06] bg-ink-950/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-6">
        <Link href={`/${locale}/`} className="flex-shrink-0">
          <Logo />
        </Link>
        <nav className="hidden items-center gap-1 md:flex">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-full px-3 py-1.5 text-sm text-ink-50/70 transition hover:bg-ink-50/[0.04] hover:text-ink-50"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <LanguageToggle />
        </div>
      </div>
    </header>
  );
}
