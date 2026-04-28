import { cn } from '@/lib/cn';

export function Logo({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-gold-shine shadow-gold-glow">
        <svg
          viewBox="0 0 24 24"
          width="18"
          height="18"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-ink-950"
          aria-hidden
        >
          <path d="M12 2v20M2 12h20M5.5 5.5l13 13M18.5 5.5l-13 13" />
          <circle cx="12" cy="12" r="9" />
        </svg>
      </span>
      <span className="flex items-baseline gap-1.5 text-lg font-semibold tracking-tight">
        <span className="gold-text">Dawri</span>
        <span className="text-ink-50/80">AI</span>
      </span>
    </div>
  );
}
