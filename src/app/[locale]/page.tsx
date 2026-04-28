import { setRequestLocale } from 'next-intl/server';
import { Header } from '@/components/Header';
import { Hero } from '@/components/Hero';
import { Features } from '@/components/Features';
import { Preview } from '@/components/Preview';
import { Footer } from '@/components/Footer';
import { isLocale } from '@/i18n/routing';
import { notFound } from 'next/navigation';

export default async function LocaleHome({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  setRequestLocale(locale);

  return (
    <div className="bg-pitch-pattern">
      <Header />
      <main>
        <Hero />
        <Features />
        <Preview />
      </main>
      <Footer />
    </div>
  );
}
