import Link from 'next/link';

// Tiny script: detect browser locale and redirect to the matching localized page.
// Falls back to a visible language picker if JS is disabled.
const detectScript = `
  (function () {
    try {
      var lang = (navigator.language || 'en').toLowerCase();
      var target = lang.startsWith('ar') ? './ar/' : './en/';
      window.location.replace(target);
    } catch (e) {}
  })();
`;

export default function RootIndex() {
  return (
    <>
      <script dangerouslySetInnerHTML={{ __html: detectScript }} />
      <noscript>
        <meta httpEquiv="refresh" content="0; url=./en/" />
      </noscript>
      <main className="grid min-h-dvh place-items-center bg-radial-saudi p-8">
        <div className="flex max-w-md flex-col items-center gap-6 text-center">
          <div className="text-3xl font-semibold gold-text">Dawri AI</div>
          <p className="text-ink-50/70">Choose your language · اختر لغتك</p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/en/"
              className="rounded-full bg-saudi-600 px-6 py-2.5 font-medium text-white shadow-glow transition hover:bg-saudi-500"
            >
              English
            </Link>
            <Link
              href="/ar/"
              className="rounded-full border border-gold-500/40 bg-gold-500/10 px-6 py-2.5 font-medium text-gold-200 transition hover:bg-gold-500/20"
            >
              العربية
            </Link>
          </div>
        </div>
      </main>
    </>
  );
}
