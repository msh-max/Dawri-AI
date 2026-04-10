"""
US Large-Cap (>$10B) Momentum Strategy Analysis
=================================================
Same momentum analysis but on ALL US-listed stocks with >$10B market cap
(~946 stocks vs 500 for S&P 500 only).

Compares:
  - Multiple lookback periods: 6-1, 9-1, 12-1 months
  - K = 1 through 20
  - Benchmark: SPY (S&P 500 ETF)

Outputs: cumulative growth, annual returns heatmap, metrics vs K,
         drawdowns, rolling Sharpe, lookback comparison.
"""

import warnings, os, time, json
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from scipy import stats as sp_stats

OUT_DIR = "output_largecap"
os.makedirs(OUT_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════
# DATA
# ═══════════════════════════════════════════════════════════════════════

def load_tickers():
    with open("us_largecap_tickers.json") as f:
        return json.load(f)

def download_data(tickers, start="2003-01-01", end="2026-03-31"):
    import yfinance as yf
    all_tickers = list(set(tickers + ["SPY"]))
    print(f"Downloading {len(all_tickers)} tickers ({start} -> {end}) ...")
    batch_size = 50
    frames = []
    total_batches = (len(all_tickers) - 1) // batch_size + 1
    for i in range(0, len(all_tickers), batch_size):
        batch = all_tickers[i:i + batch_size]
        attempt = 0
        while attempt < 3:
            try:
                data = yf.download(batch, start=start, end=end,
                                   auto_adjust=True, progress=False, threads=True)
                if isinstance(data.columns, pd.MultiIndex):
                    close = data["Close"]
                else:
                    close = data[["Close"]]
                    close.columns = batch[:1]
                frames.append(close)
                break
            except Exception as e:
                attempt += 1
                time.sleep(2 * attempt)
        bn = i // batch_size + 1
        if bn % 5 == 0 or bn == total_batches:
            print(f"  Batch {bn}/{total_batches}")
    prices = pd.concat(frames, axis=1)
    prices = prices.loc[:, ~prices.columns.duplicated()]
    prices.index = pd.to_datetime(prices.index)
    # Drop columns that are all NaN
    prices = prices.dropna(axis=1, how="all")
    print(f"Got {prices.shape[0]} days x {prices.shape[1]} tickers")
    return prices

# ═══════════════════════════════════════════════════════════════════════
# MOMENTUM STRATEGY
# ═══════════════════════════════════════════════════════════════════════

def momentum_strategy(monthly_prices, monthly_returns, k, lookback=12, skip=1):
    spy_col = "SPY"
    stock_prices = monthly_prices.drop(columns=[spy_col], errors="ignore")
    stock_rets = monthly_returns.drop(columns=[spy_col], errors="ignore")
    common_dates = stock_prices.index.intersection(stock_rets.index).sort_values()

    port_returns = []
    min_hist = lookback + skip - 1

    for idx in range(len(common_dates)):
        date = common_dates[idx]
        price_pos = stock_prices.index.get_loc(date)
        if price_pos < min_hist:
            continue
        p_start = stock_prices.iloc[price_pos - (lookback + skip - 1)]
        p_end = stock_prices.iloc[price_pos - skip]
        signal = (p_end / p_start - 1).dropna()
        if len(signal) < k:
            continue
        top_k = signal.nlargest(k).index
        curr = stock_rets.loc[date][top_k].dropna()
        if len(curr) == 0:
            continue
        port_returns.append((date, curr.mean()))

    result = pd.Series(dict(port_returns))
    result.index = pd.to_datetime(result.index)
    return result

# ═══════════════════════════════════════════════════════════════════════
# METRICS
# ═══════════════════════════════════════════════════════════════════════

def calc_metrics(monthly_rets, label="Strategy", rf_annual=0.03):
    r = monthly_rets.dropna()
    if len(r) < 12:
        return {"Label": label}
    rf_m = (1 + rf_annual) ** (1/12) - 1
    total_ret = (1 + r).prod() - 1
    n_years = len(r) / 12
    cagr = (1 + total_ret) ** (1 / n_years) - 1
    vol = r.std() * np.sqrt(12)
    sharpe = (r.mean() - rf_m) / r.std() if r.std() > 0 else 0
    downside = r[r < rf_m]
    sort_d = downside.std() if len(downside) > 1 else r.std()
    sortino = (r.mean() - rf_m) / sort_d if sort_d > 0 else 0
    wealth = (1 + r).cumprod()
    dd = (wealth - wealth.cummax()) / wealth.cummax()
    max_dd = dd.min()
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0
    win_rate = (r > 0).mean()
    return {
        "Label": label, "CAGR": cagr, "Annual Vol": vol, "Sharpe": sharpe,
        "Sortino": sortino, "Max Drawdown": max_dd, "Calmar": calmar,
        "Win Rate": win_rate, "Best Month": r.max(), "Worst Month": r.min(),
        "Total Return": total_ret, "Years": n_years,
    }

# ═══════════════════════════════════════════════════════════════════════
# PLOTTING
# ═══════════════════════════════════════════════════════════════════════

def plot_all(spy_monthly, strats_by_config, metrics_by_config, lookbacks, k_values):
    sns.set_theme(style="whitegrid", palette="muted")

    # Identify best config per lookback by Sharpe
    best_per_lb = {}
    for lb in lookbacks:
        best_sharpe = -999
        best_k_lb = k_values[0]
        for k in k_values:
            m = metrics_by_config.get((lb, k))
            if m and m.get("Sharpe", -999) > best_sharpe:
                best_sharpe = m["Sharpe"]
                best_k_lb = k
        best_per_lb[lb] = best_k_lb

    # Overall best by Sharpe
    best_sharpe_overall = -999
    best_config = (12, 8)
    for (lb, k), m in metrics_by_config.items():
        if m.get("Sharpe", -999) > best_sharpe_overall:
            best_sharpe_overall = m["Sharpe"]
            best_config = (lb, k)
    best_lb, best_k = best_config
    best_strat = strats_by_config[best_config]

    # ── 1. Cumulative Growth: best per lookback vs SPY ──
    fig, ax = plt.subplots(figsize=(16, 7))
    spy_c = (1 + spy_monthly).cumprod()
    ax.plot(spy_c.index, spy_c.values, label="S&P 500 (SPY)", linewidth=2.5, 
            color="black", linestyle="--")
    colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"]
    for i, lb in enumerate(lookbacks):
        k = best_per_lb[lb]
        s = strats_by_config[(lb, k)]
        common = spy_monthly.index.intersection(s.index)
        sc = (1 + s.loc[common]).cumprod()
        m = metrics_by_config[(lb, k)]
        ax.plot(sc.index, sc.values, 
                label=f"{lb}-1mo, Top-{k} (Sharpe={m['Sharpe']:.2f}, CAGR={m['CAGR']:.0%})",
                linewidth=2, color=colors[i % len(colors)])
    ax.set_title("Cumulative Growth: US Large-Cap (>$10B) Momentum vs S&P 500",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Growth of $1")
    ax.legend(fontsize=10, loc="upper left")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/01_cumulative_growth.png", dpi=150)
    plt.close(fig)

    # ── 2. Metrics vs K for each lookback (Sharpe, CAGR, MaxDD) ──
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    spy_m = calc_metrics(spy_monthly, "SPY")
    for ax, metric in zip(axes, ["Sharpe", "CAGR", "Max Drawdown"]):
        for i, lb in enumerate(lookbacks):
            vals = []
            for k in k_values:
                m = metrics_by_config.get((lb, k), {})
                vals.append(m.get(metric, np.nan))
            ax.plot(k_values, vals, "o-", label=f"{lb}-1mo", 
                    linewidth=2, color=colors[i % len(colors)])
        ax.axhline(y=spy_m.get(metric, 0), color="black", linestyle="--", 
                   label="S&P 500", linewidth=1.5)
        ax.set_xlabel("K (# of top stocks)")
        ax.set_title(metric, fontweight="bold", fontsize=13)
        ax.legend(fontsize=9)
        if metric in ["CAGR", "Max Drawdown"]:
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    fig.suptitle("US Large-Cap Momentum: Metrics vs K by Lookback Period",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/02_metrics_vs_k.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # ── 3. Heatmap: Sharpe by (lookback, K) ──
    fig, axes = plt.subplots(1, 3, figsize=(24, 8))
    for ax, metric in zip(axes, ["Sharpe", "CAGR", "Max Drawdown"]):
        data = {}
        for lb in lookbacks:
            data[f"{lb}-1"] = {}
            for k in k_values:
                m = metrics_by_config.get((lb, k), {})
                data[f"{lb}-1"][k] = m.get(metric, np.nan)
        df = pd.DataFrame(data)
        df.index.name = "K"
        fmt = ".2f" if metric == "Sharpe" else ".1%"
        cmap = "RdYlGn" if metric != "Max Drawdown" else "RdYlGn_r"
        sns.heatmap(df, annot=True, fmt=fmt, cmap=cmap, ax=ax, linewidths=0.5)
        ax.set_title(f"{metric}", fontweight="bold", fontsize=13)
        ax.set_ylabel("K (# stocks)")
    fig.suptitle("Performance Heatmap: Lookback Period vs Number of Stocks (US >$10B Universe)",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/03_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # ── 4. Annual Returns Heatmap ──
    fig, ax = plt.subplots(figsize=(18, 7))
    annual_data = {}
    # Show best per lookback + SPY
    for lb in lookbacks:
        k = best_per_lb[lb]
        s = strats_by_config[(lb, k)]
        annual = s.groupby(s.index.year).apply(lambda x: (1 + x).prod() - 1)
        annual_data[f"{lb}-1 / Top-{k}"] = annual
    spy_annual = spy_monthly.groupby(spy_monthly.index.year).apply(
        lambda x: (1 + x).prod() - 1)
    annual_data["SPY"] = spy_annual
    annual_df = pd.DataFrame(annual_data).dropna()
    sns.heatmap(annual_df.T, annot=True, fmt=".1%", cmap="RdYlGn", center=0,
                linewidths=0.5, ax=ax)
    ax.set_title("Annual Returns: Best Momentum per Lookback vs S&P 500 (US >$10B Universe)",
                 fontsize=13, fontweight="bold")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/04_annual_returns.png", dpi=150)
    plt.close(fig)

    # ── 5. Drawdown Comparison ──
    fig, axes = plt.subplots(2, 1, figsize=(16, 8), sharex=True)
    common = spy_monthly.index.intersection(best_strat.index).sort_values()
    for ax, (series, label) in zip(axes,
            [(spy_monthly.loc[common], "S&P 500"),
             (best_strat.loc[common], f"Best: Top-{best_k}, {best_lb}-1mo")]):
        w = (1 + series).cumprod()
        dd_s = (w - w.cummax()) / w.cummax()
        ax.fill_between(dd_s.index, dd_s.values, 0, alpha=0.5)
        ax.set_ylabel("Drawdown")
        ax.set_title(f"{label} Drawdown", fontweight="bold")
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/05_drawdowns.png", dpi=150)
    plt.close(fig)

    # ── 6. Rolling 12-month Sharpe ──
    fig, ax = plt.subplots(figsize=(16, 6))
    common = spy_monthly.index.intersection(best_strat.index).sort_values()
    for label, series in [("S&P 500", spy_monthly.loc[common]),
                           (f"Top-{best_k}, {best_lb}-1mo", best_strat.loc[common])]:
        rm = series.rolling(12).mean()
        rs = series.rolling(12).std()
        rsharpe = (rm / rs) * np.sqrt(12)
        ax.plot(rsharpe.index, rsharpe.values, label=label, linewidth=1.5)
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.set_title("Rolling 12-Month Sharpe Ratio (US >$10B Universe)", 
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Sharpe Ratio")
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/06_rolling_sharpe.png", dpi=150)
    plt.close(fig)

    # ── 7. Sortino / Calmar heatmap ──
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    for ax, metric in zip(axes, ["Sortino", "Calmar"]):
        data = {}
        for lb in lookbacks:
            data[f"{lb}-1"] = {}
            for k in k_values:
                m = metrics_by_config.get((lb, k), {})
                data[f"{lb}-1"][k] = m.get(metric, np.nan)
        df = pd.DataFrame(data)
        df.index.name = "K"
        sns.heatmap(df, annot=True, fmt=".2f", cmap="RdYlGn", ax=ax, linewidths=0.5)
        ax.set_title(metric, fontweight="bold", fontsize=13)
        ax.set_ylabel("K (# stocks)")
    fig.suptitle("Risk-Adjusted Metrics: Lookback vs K (US >$10B Universe)",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/07_sortino_calmar_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"\nAll 7 charts saved to {OUT_DIR}/")
    return best_config

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("US LARGE-CAP (>$10B MARKET CAP) MOMENTUM STRATEGY ANALYSIS")
    print("=" * 80)

    tickers = load_tickers()
    print(f"\nUniverse: {len(tickers)} US stocks with >$10B market cap")

    prices = download_data(tickers, start="2003-01-01", end="2026-03-31")
    monthly_prices = prices.resample("ME").last()
    monthly_returns = monthly_prices.pct_change().dropna(how="all")
    spy_monthly = monthly_returns["SPY"].dropna()

    # Count how many stocks have data at each point
    stock_rets = monthly_returns.drop(columns=["SPY"], errors="ignore")
    counts = stock_rets.count(axis=1)
    print(f"\nMonthly data: {len(monthly_returns)} months")
    print(f"Stocks with data: min={counts.min()}, max={counts.max()}, "
          f"recent={counts.iloc[-1]}")

    # ── Run all combinations ──
    lookbacks = [6, 9, 12]
    k_values = list(range(1, 21))

    print(f"\n{'━' * 80}")
    print(f"Testing {len(lookbacks)} lookbacks x {len(k_values)} K values "
          f"= {len(lookbacks)*len(k_values)} combinations")
    print(f"{'━' * 80}")

    metrics_by_config = {}
    strats_by_config = {}

    for lb in lookbacks:
        print(f"\n  Lookback = {lb}-1 months:")
        for k in k_values:
            s = momentum_strategy(monthly_prices, monthly_returns, k, 
                                   lookback=lb, skip=1)
            m = calc_metrics(s, f"LB{lb}_K{k}")
            metrics_by_config[(lb, k)] = m
            strats_by_config[(lb, k)] = s
            print(f"    K={k:2d}  CAGR={m.get('CAGR',0):.1%}  "
                  f"Sharpe={m.get('Sharpe',0):.2f}  "
                  f"MaxDD={m.get('Max Drawdown',0):.1%}")

    # ── SPY reference ──
    spy_m = calc_metrics(spy_monthly, "SPY")

    # ── Print summary ──
    print(f"\n{'═' * 80}")
    print("RESULTS SUMMARY")
    print(f"{'═' * 80}")

    # Find best by Sharpe
    best_sharpe = -999
    best_config_sharpe = None
    best_sortino = -999
    best_config_sortino = None
    for (lb, k), m in metrics_by_config.items():
        if m.get("Sharpe", -999) > best_sharpe:
            best_sharpe = m["Sharpe"]
            best_config_sharpe = (lb, k)
        if m.get("Sortino", -999) > best_sortino:
            best_sortino = m["Sortino"]
            best_config_sortino = (lb, k)

    print(f"\n  Best by Sharpe:  LB={best_config_sharpe[0]}-1, K={best_config_sharpe[1]}  "
          f"(Sharpe={best_sharpe:.3f})")
    print(f"  Best by Sortino: LB={best_config_sortino[0]}-1, K={best_config_sortino[1]}  "
          f"(Sortino={best_sortino:.3f})")
    print(f"  SPY Reference:   CAGR={spy_m['CAGR']:.2%}  Sharpe={spy_m['Sharpe']:.2f}  "
          f"MaxDD={spy_m['Max Drawdown']:.2%}")

    # Full table per lookback
    for lb in lookbacks:
        print(f"\n{'─' * 80}")
        print(f"Lookback = {lb}-1 months")
        print(f"{'─' * 80}")
        rows = []
        for k in k_values:
            m = metrics_by_config[(lb, k)]
            rows.append({
                "K": k,
                "CAGR": f"{m.get('CAGR',0):.2%}",
                "Vol": f"{m.get('Annual Vol',0):.2%}",
                "Sharpe": f"{m.get('Sharpe',0):.2f}",
                "Sortino": f"{m.get('Sortino',0):.2f}",
                "MaxDD": f"{m.get('Max Drawdown',0):.2%}",
                "Calmar": f"{m.get('Calmar',0):.2f}",
                "WinRate": f"{m.get('Win Rate',0):.1%}",
            })
        print(pd.DataFrame(rows).to_string(index=False))

    # ── Generate charts ──
    print(f"\n{'─' * 80}")
    print("Generating charts...")
    best_config = plot_all(spy_monthly, strats_by_config, metrics_by_config, 
                           lookbacks, k_values)

    # ── Save data ──
    all_rows = []
    for (lb, k), m in metrics_by_config.items():
        row = dict(m)
        row["Lookback"] = lb
        row["K_val"] = k
        all_rows.append(row)
    pd.DataFrame(all_rows).to_csv(f"{OUT_DIR}/all_results.csv", index=False)
    print(f"Data saved to {OUT_DIR}/")

    # ── Head-to-head: best config vs SPY ──
    lb_b, k_b = best_config
    bm = metrics_by_config[(lb_b, k_b)]
    print(f"\n{'═' * 80}")
    print(f"HEAD-TO-HEAD: Top-{k_b} / {lb_b}-1mo  vs  S&P 500")
    print(f"{'═' * 80}")
    for metric in ["CAGR", "Annual Vol", "Sharpe", "Sortino", "Max Drawdown",
                    "Calmar", "Win Rate", "Best Month", "Worst Month", "Total Return"]:
        sv = spy_m.get(metric, 0)
        bv = bm.get(metric, 0)
        if metric in ["CAGR", "Annual Vol", "Max Drawdown", "Win Rate", 
                       "Best Month", "Worst Month", "Total Return"]:
            print(f"  {metric:15s}  SPY: {sv:.2%}   Strategy: {bv:.2%}")
        else:
            print(f"  {metric:15s}  SPY: {sv:.2f}   Strategy: {bv:.2f}")

    print(f"\n{'═' * 80}")
    print("ANALYSIS COMPLETE")
    print(f"{'═' * 80}")


if __name__ == "__main__":
    main()
