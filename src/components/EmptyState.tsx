import { Database } from 'lucide-react';

export function EmptyState({
  title,
  hint,
}: {
  title: string;
  hint?: string;
}) {
  return (
    <div className="grid place-items-center rounded-2xl border border-dashed border-ink-50/10 bg-ink-900/30 px-8 py-16 text-center">
      <div className="grid h-12 w-12 place-items-center rounded-full bg-saudi-600/10 text-gold-300 ring-1 ring-inset ring-gold-500/20">
        <Database size={20} aria-hidden />
      </div>
      <p className="mt-4 text-sm font-medium text-ink-50/80">{title}</p>
      {hint ? (
        <p className="mt-1 text-xs text-ink-50/50">{hint}</p>
      ) : null}
    </div>
  );
}
