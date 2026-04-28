import { useTranslations } from 'next-intl';
import { Sparkles, TrendingUp, TrendingDown } from 'lucide-react';
import type { MatchPrediction, Team } from '@/types/data';

interface Props {
  prediction: MatchPrediction;
  homeTeam: Team | null;
  awayTeam: Team | null;
  locale: string;
}

export function PredictionPanel({
  prediction,
  homeTeam,
  awayTeam,
  locale,
}: Props) {
  const t = useTranslations('matches');
  const isAr = locale === 'ar';

  const homeName = homeTeam
    ? isAr
      ? homeTeam.short_name.ar
      : homeTeam.short_name.en
    : '';
  const awayName = awayTeam
    ? isAr
      ? awayTeam.short_name.ar
      : awayTeam.short_name.en
    : '';

  return (
    <section className="gold-border-gradient relative overflow-hidden rounded-2xl bg-ink-900/60 p-6 backdrop-blur">
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-gold-shine text-ink-950">
            <Sparkles size={14} aria-hidden />
          </span>
          <h2 className="text-base font-semibold text-ink-50/90">
            {t('predictionTitle')}
          </h2>
        </div>
        <span className="font-mono text-[10px] uppercase tracking-wider text-ink-50/40">
          {t('modelLabel')}: {prediction.model_version}
        </span>
      </div>

      <ProbabilityBar
        homeName={homeName}
        awayName={awayName}
        homeWin={prediction.home_win_prob}
        draw={prediction.draw_prob}
        awayWin={prediction.away_win_prob}
        drawLabel={t('predictionDraw')}
      />

      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat
          label={t('predictionScore')}
          value={`${prediction.most_likely_score[0]} : ${prediction.most_likely_score[1]}`}
          mono
        />
        <Stat
          label={t('predictionXg')}
          value={`${prediction.home_xg_predicted.toFixed(2)} – ${prediction.away_xg_predicted.toFixed(2)}`}
          mono
        />
        <Stat
          label={t('predictionBtts')}
          value={`${Math.round(prediction.btts_prob * 100)}%`}
        />
        <Stat
          label={t('predictionOver25')}
          value={`${Math.round(prediction.over25_prob * 100)}%`}
        />
      </div>

      {prediction.contributions.length > 0 ? (
        <WhyPanel
          contributions={prediction.contributions}
          locale={locale}
          favorsHomeLabel={t('predictionFavorsHome')}
          favorsAwayLabel={t('predictionFavorsAway')}
          title={t('predictionWhy')}
        />
      ) : null}

      <p className="mt-5 text-[11px] text-ink-50/40">
        {t('predictionDisclaimer')}
      </p>
    </section>
  );
}

function Stat({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded-lg border border-ink-50/[0.06] bg-ink-950/40 px-3 py-2">
      <div className="text-[10px] uppercase tracking-wider text-ink-50/45">
        {label}
      </div>
      <div
        className={`mt-1 text-base text-ink-50/90 ${mono ? 'font-mono tabular-nums' : 'font-semibold'}`}
      >
        {value}
      </div>
    </div>
  );
}

function ProbabilityBar({
  homeName,
  awayName,
  homeWin,
  draw,
  awayWin,
  drawLabel,
}: {
  homeName: string;
  awayName: string;
  homeWin: number;
  draw: number;
  awayWin: number;
  drawLabel: string;
}) {
  const hp = Math.round(homeWin * 100);
  const dp = Math.round(draw * 100);
  const ap = Math.max(0, 100 - hp - dp);

  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <span className="font-medium text-ink-50/85">{homeName}</span>
          <span className="font-mono tabular-nums text-saudi-300">{hp}%</span>
        </div>
        <span className="font-mono tabular-nums text-ink-50/50">
          {drawLabel} {dp}%
        </span>
        <div className="flex items-center gap-2">
          <span className="font-mono tabular-nums text-gold-300">{ap}%</span>
          <span className="font-medium text-ink-50/85">{awayName}</span>
        </div>
      </div>
      <div className="flex h-2.5 overflow-hidden rounded-full bg-ink-950/60">
        <div
          className="bg-saudi-500 transition-[width]"
          style={{ width: `${hp}%` }}
        />
        <div
          className="bg-ink-50/15 transition-[width]"
          style={{ width: `${dp}%` }}
        />
        <div
          className="bg-gold-500 transition-[width]"
          style={{ width: `${ap}%` }}
        />
      </div>
    </div>
  );
}

function WhyPanel({
  contributions,
  locale,
  favorsHomeLabel,
  favorsAwayLabel,
  title,
}: {
  contributions: MatchPrediction['contributions'];
  locale: string;
  favorsHomeLabel: string;
  favorsAwayLabel: string;
  title: string;
}) {
  const isAr = locale === 'ar';
  const maxAbs = Math.max(
    1,
    ...contributions.map((c) => Math.abs(c.value))
  );

  return (
    <div className="mt-6 rounded-xl border border-ink-50/[0.06] bg-ink-950/40 p-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-gold-300/80">
          {title}
        </span>
      </div>
      <ol className="space-y-2.5">
        {contributions.map((c) => {
          const positive = c.value >= 0;
          const widthPct = (Math.abs(c.value) / maxAbs) * 100;
          const label = isAr ? c.label.ar : c.label.en;
          const explanation = isAr ? c.explanation.ar : c.explanation.en;
          return (
            <li key={c.feature}>
              <div className="mb-1 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-xs">
                  {positive ? (
                    <TrendingUp size={12} className="text-saudi-400" aria-hidden />
                  ) : (
                    <TrendingDown size={12} className="text-gold-400" aria-hidden />
                  )}
                  <span className="font-medium text-ink-50/85">{label}</span>
                  <span className="text-ink-50/40">
                    · {positive ? favorsHomeLabel : favorsAwayLabel}
                  </span>
                </div>
                <span
                  className={`font-mono text-xs tabular-nums ${
                    positive ? 'text-saudi-300' : 'text-gold-300'
                  }`}
                >
                  {positive ? '+' : '−'}
                  {Math.abs(c.value).toFixed(1)}pp
                </span>
              </div>
              <div className="relative h-1 overflow-hidden rounded-full bg-ink-950/60">
                <div
                  className={`absolute inset-y-0 ${
                    positive ? 'bg-saudi-500/70' : 'bg-gold-500/70'
                  } ${positive ? 'start-1/2' : 'end-1/2'}`}
                  style={{ width: `${widthPct / 2}%` }}
                />
                <div className="absolute inset-y-0 start-1/2 w-px bg-ink-50/15" />
              </div>
              <p className="mt-1.5 text-xs leading-relaxed text-ink-50/55">
                {explanation}
              </p>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
