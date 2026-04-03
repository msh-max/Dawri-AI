"""
S&P 500 Momentum Strategy Analysis
====================================
Compares buying & holding the S&P 500 index vs. a momentum strategy that each
month buys the top-K stocks ranked by prior-month return. Optimizes K across
a grid and reports risk-adjusted metrics.

Strategy:
  - At each month-end, rank all S&P 500 constituents by their trailing 1-month return.
  - Buy the top K stocks equally weighted; hold for 1 month; rebalance.
  - Compare against SPY (S&P 500 ETF) buy-and-hold.

Note: Uses *current* S&P 500 constituents (survivorship bias caveat).
"""

import warnings, os, sys, json, time
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from scipy import stats

# ── 1. Get current S&P 500 tickers ──────────────────────────────────────────

def get_sp500_tickers():
    """Return S&P 500 constituents (as of early 2026)."""
    tickers = [
        "AAPL","ABBV","ABT","ACN","ADBE","ADI","ADM","ADP","ADSK","AEE",
        "AEP","AES","AFL","AIG","AIZ","AJG","AKAM","ALB","ALGN","ALK",
        "ALL","ALLE","AMAT","AMCR","AMD","AME","AMGN","AMP","AMT","AMZN",
        "ANET","ANSS","AON","AOS","APA","APD","APH","APTV","ARE","ATO",
        "ATVI","AVGO","AVY","AWK","AXP","AZO","BA","BAC","BAX","BBWI",
        "BBY","BDX","BEN","BF-B","BIO","BIIB","BK","BKNG","BKR","BLK",
        "BMY","BR","BRK-B","BRO","BSX","BWA","BXP","C","CAG","CAH",
        "CARR","CAT","CB","CBOE","CBRE","CCI","CCL","CDAY","CDNS","CDW",
        "CE","CEG","CF","CFG","CHD","CHRW","CHTR","CI","CINF","CL",
        "CLX","CMA","CMCSA","CME","CMG","CMI","CMS","CNC","CNP","COF",
        "COO","COP","COST","CPB","CPRT","CPT","CRL","CRM","CSCO","CSGP",
        "CSX","CTAS","CTLT","CTRA","CTSH","CTVA","CVS","CVX","CZR","D",
        "DAL","DD","DE","DFS","DG","DGX","DHI","DHR","DIS","DISH",
        "DLR","DLTR","DOV","DOW","DPZ","DRI","DTE","DUK","DVA","DVN",
        "DXC","DXCM","EA","EBAY","ECL","ED","EFX","EIX","EL","EMN",
        "EMR","ENPH","EOG","EPAM","EQIX","EQR","EQT","ES","ESS","ETN",
        "ETR","ETSY","EVRG","EW","EXC","EXPD","EXPE","EXR","F","FANG",
        "FAST","FBHS","FCX","FDS","FDX","FE","FFIV","FIS","FISV","FITB",
        "FLT","FMC","FOX","FOXA","FRC","FRT","FTNT","FTV","GD","GE",
        "GILD","GIS","GL","GLW","GM","GNRC","GOOG","GOOGL","GPC","GPN",
        "GRMN","GS","GWW","HAL","HAS","HBAN","HCA","HD","HOLX","HON",
        "HPE","HPQ","HRL","HSIC","HST","HSY","HUM","HWM","IBM","ICE",
        "IDXX","IEX","IFF","ILMN","INCY","INTC","INTU","INVH","IP","IPG",
        "IQV","IR","IRM","ISRG","IT","ITW","IVZ","J","JBHT","JCI",
        "JKHY","JNJ","JNPR","JPM","K","KDP","KEY","KEYS","KHC","KIM",
        "KLAC","KMB","KMI","KMX","KO","KR","L","LDOS","LEN","LH",
        "LHX","LIN","LKQ","LLY","LMT","LNC","LNT","LOW","LRCX","LUMN",
        "LUV","LVS","LW","LYB","LYV","MA","MAA","MAR","MAS","MCD",
        "MCHP","MCK","MCO","MDLZ","MDT","MET","META","MGM","MHK","MKC",
        "MKTX","MLM","MMC","MMM","MNST","MO","MOH","MOS","MPC","MPWR",
        "MRK","MRNA","MRO","MS","MSCI","MSFT","MSI","MTB","MTCH","MTD",
        "MU","NCLH","NDAQ","NDSN","NEE","NEM","NFLX","NI","NKE","NOC",
        "NOW","NRG","NSC","NTAP","NTRS","NUE","NVDA","NVR","NWL","NWS",
        "NWSA","NXPI","O","ODFL","OGN","OKE","OMC","ON","ORCL","ORLY",
        "OTIS","OXY","PARA","PAYC","PAYX","PCAR","PCG","PEAK","PEG","PEP",
        "PFE","PFG","PG","PGR","PH","PHM","PKG","PKI","PLD","PM",
        "PNC","PNR","PNW","POOL","PPG","PPL","PRU","PSA","PSX","PTC",
        "PVH","PWR","PXD","PYPL","QCOM","QRVO","RCL","RE","REG","REGN",
        "RF","RHI","RJF","RL","RMD","ROK","ROL","ROP","ROST","RSG",
        "RTX","RVTY","SBAC","SBNY","SBUX","SCHW","SEE","SHW","SIVB","SJM",
        "SLB","SNA","SNPS","SO","SPG","SPGI","SRE","STE","STT","STX",
        "STZ","SWK","SWKS","SYF","SYK","SYY","T","TAP","TDG","TDY",
        "TECH","TEL","TER","TFC","TFX","TGT","TMO","TMUS","TPR","TRGP",
        "TRMB","TROW","TRV","TSCO","TSLA","TSN","TT","TTWO","TXN","TXT",
        "TYL","UAL","UDR","UHS","ULTA","UNH","UNP","UPS","URI","USB",
        "V","VFC","VICI","VLO","VMC","VRSK","VRSN","VRTX","VTR","VTRS",
        "VZ","WAB","WAT","WBA","WBD","WDC","WEC","WELL","WFC","WHR",
        "WM","WMB","WMT","WRB","WRK","WST","WTW","WY","WYNN","XEL",
        "XOM","XRAY","XYL","YUM","ZBH","ZBRA","ZION","ZTS",
    ]
    return tickers


# ── 2. Download price data ──────────────────────────────────────────────────

def download_data(tickers, start="2005-01-01", end="2026-03-31"):
    """Download adjusted close prices for all tickers + SPY."""
    import yfinance as yf

    all_tickers = list(set(tickers + ["SPY"]))
    print(f"Downloading data for {len(all_tickers)} tickers ({start} → {end}) ...")

    # Download in batches to avoid timeouts
    batch_size = 50
    frames = []
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
                print(f"  Batch {i//batch_size+1} attempt {attempt} failed: {e}")
                time.sleep(2 * attempt)
        print(f"  Batch {i//batch_size+1}/{(len(all_tickers)-1)//batch_size+1} done "
              f"({len(batch)} tickers)")

    prices = pd.concat(frames, axis=1)
    # Remove duplicate columns
    prices = prices.loc[:, ~prices.columns.duplicated()]
    prices.index = pd.to_datetime(prices.index)
    print(f"Got price data: {prices.shape[0]} days × {prices.shape[1]} tickers")
    return prices


# ── 3. Compute monthly returns ──────────────────────────────────────────────

def compute_monthly_returns(prices):
    """Resample to month-end and compute simple returns."""
    monthly = prices.resample("ME").last()
    returns = monthly.pct_change().dropna(how="all")
    return returns


# ── 4. Momentum strategy ────────────────────────────────────────────────────

def momentum_strategy(monthly_prices, monthly_returns, k):
    """
    Classic 12-1 month momentum (Jegadeesh & Titman).

    Signal: cumulative return from month t-12 to t-1 (skip the most recent
    month to avoid short-term reversal noise).

    Each month:
      1. Compute the 12-1 month return for every stock.
      2. Rank and pick the top-k.
      3. Hold equal-weight for 1 month.

    Parameters
    ----------
    monthly_prices : DataFrame  – month-end prices (used for 12-1 signal)
    monthly_returns : DataFrame – month-over-month returns (used for holding-period return)
    k : int                     – number of top stocks to hold
    """
    spy_col = "SPY"
    stock_prices = monthly_prices.drop(columns=[spy_col], errors="ignore")
    stock_rets = monthly_returns.drop(columns=[spy_col], errors="ignore")

    port_returns = []
    # Align on common dates
    common_dates = stock_prices.index.intersection(stock_rets.index)
    common_dates = common_dates.sort_values()

    for idx in range(len(common_dates)):
        date = common_dates[idx]
        # Need the price 12 months and 1 month before this date in the prices index
        price_pos = stock_prices.index.get_loc(date)
        if price_pos < 12:
            continue

        p_start = stock_prices.iloc[price_pos - 12]  # price 12 months ago
        p_end = stock_prices.iloc[price_pos - 1]      # price 1 month ago (skip current)
        signal = (p_end / p_start - 1).dropna()

        if len(signal) < k:
            continue

        top_k = signal.nlargest(k).index

        # Hold those stocks for the current month
        curr = stock_rets.loc[date][top_k].dropna()
        if len(curr) == 0:
            continue
        port_returns.append((date, curr.mean()))

    result = pd.Series(dict(port_returns), name=f"Top{k}_Momentum")
    result.index = pd.to_datetime(result.index)
    return result


# ── 5. Performance metrics ──────────────────────────────────────────────────

def calc_metrics(monthly_rets, label="Strategy", rf_annual=0.03):
    """Compute standard performance metrics from a monthly return series."""
    r = monthly_rets.dropna()
    rf_m = (1 + rf_annual) ** (1/12) - 1

    total_ret = (1 + r).prod() - 1
    n_years = len(r) / 12
    cagr = (1 + total_ret) ** (1 / n_years) - 1 if n_years > 0 else 0
    vol = r.std() * np.sqrt(12)
    sharpe = (r.mean() - rf_m) / r.std() if r.std() > 0 else 0
    sortino_denom = r[r < 0].std() if (r < 0).any() else r.std()
    sortino = (r.mean() - rf_m) / sortino_denom if sortino_denom > 0 else 0

    # Max drawdown on cumulative wealth
    wealth = (1 + r).cumprod()
    peak = wealth.cummax()
    dd = (wealth - peak) / peak
    max_dd = dd.min()

    # Calmar ratio
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0

    # Win rate
    win_rate = (r > 0).mean()

    # Best / worst month
    best = r.max()
    worst = r.min()

    return {
        "Label": label,
        "CAGR": cagr,
        "Annual Vol": vol,
        "Sharpe": sharpe,
        "Sortino": sortino,
        "Max Drawdown": max_dd,
        "Calmar": calmar,
        "Win Rate": win_rate,
        "Best Month": best,
        "Worst Month": worst,
        "Total Return": total_ret,
        "Years": n_years,
    }


# ── 6. Optimize K ───────────────────────────────────────────────────────────

def optimize_k(monthly_prices, monthly_returns, k_values):
    """Run the momentum strategy for each k and collect metrics."""
    results = []
    strats = {}
    for k in k_values:
        s = momentum_strategy(monthly_prices, monthly_returns, k)
        m = calc_metrics(s, label=f"Top {k}")
        m["K"] = k
        results.append(m)
        strats[k] = s
        print(f"  K={k:3d}  CAGR={m['CAGR']:.2%}  Sharpe={m['Sharpe']:.2f}  "
              f"MaxDD={m['Max Drawdown']:.2%}")
    return pd.DataFrame(results), strats


# ── 7. Plotting ─────────────────────────────────────────────────────────────

def plot_results(spy_monthly, best_strat, best_k, metrics_df, k_values, strats, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    sns.set_theme(style="whitegrid", palette="muted")

    # --- A. Cumulative wealth: SPY vs best momentum ---
    fig, ax = plt.subplots(figsize=(14, 6))
    common = spy_monthly.index.intersection(best_strat.index)
    spy_c = (1 + spy_monthly.loc[common]).cumprod()
    mom_c = (1 + best_strat.loc[common]).cumprod()
    ax.plot(spy_c.index, spy_c.values, label="S&P 500 (SPY)", linewidth=2)
    ax.plot(mom_c.index, mom_c.values, label=f"Top-{best_k} Momentum", linewidth=2)
    ax.set_title(f"Cumulative Growth: S&P 500 vs Top-{best_k} Momentum (12-1 Signal)",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Growth of $1")
    ax.legend(fontsize=12)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:.1f}"))
    fig.tight_layout()
    fig.savefig(f"{out_dir}/cumulative_growth.png", dpi=150)
    plt.close(fig)

    # --- B. Drawdown comparison ---
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    for ax_i, (series, label) in zip(axes, [(spy_monthly.loc[common], "S&P 500"),
                                             (best_strat.loc[common], f"Top-{best_k} Momentum")]):
        wealth = (1 + series).cumprod()
        dd = (wealth - wealth.cummax()) / wealth.cummax()
        ax_i.fill_between(dd.index, dd.values, 0, alpha=0.4)
        ax_i.set_ylabel("Drawdown")
        ax_i.set_title(f"{label} Drawdown", fontweight="bold")
        ax_i.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    fig.tight_layout()
    fig.savefig(f"{out_dir}/drawdowns.png", dpi=150)
    plt.close(fig)

    # --- C. Sharpe / CAGR / MaxDD vs K ---
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    metrics_df_sorted = metrics_df.sort_values("K")
    for ax_i, col, fmt in zip(axes,
                               ["Sharpe", "CAGR", "Max Drawdown"],
                               ["{:.2f}", "{:.1%}", "{:.1%}"]):
        ax_i.plot(metrics_df_sorted["K"], metrics_df_sorted[col], "o-", linewidth=2)
        ax_i.axhline(y=calc_metrics(spy_monthly, "SPY")[col],
                      color="red", linestyle="--", label="S&P 500")
        ax_i.set_xlabel("K (# of top stocks)")
        ax_i.set_title(col, fontweight="bold")
        ax_i.legend()
        if "%" in fmt:
            ax_i.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    fig.suptitle("Momentum Strategy Metrics vs K", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(f"{out_dir}/metrics_vs_k.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # --- D. Annual returns heatmap ---
    fig, ax = plt.subplots(figsize=(14, 8))
    # Build annual returns for SPY + select K values
    showcase_ks = [k_values[0], best_k, k_values[len(k_values)//2], k_values[-1]]
    showcase_ks = sorted(set(showcase_ks))
    annual_data = {}
    for k in showcase_ks:
        s = strats[k]
        annual = s.groupby(s.index.year).apply(lambda x: (1 + x).prod() - 1)
        annual_data[f"Top-{k}"] = annual
    spy_annual = spy_monthly.groupby(spy_monthly.index.year).apply(lambda x: (1 + x).prod() - 1)
    annual_data["SPY"] = spy_annual
    annual_df = pd.DataFrame(annual_data).dropna()
    sns.heatmap(annual_df.T, annot=True, fmt=".1%", cmap="RdYlGn", center=0,
                linewidths=0.5, ax=ax)
    ax.set_title("Annual Returns Comparison", fontsize=14, fontweight="bold")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(f"{out_dir}/annual_returns_heatmap.png", dpi=150)
    plt.close(fig)

    # --- E. Rolling 12-month Sharpe ---
    fig, ax = plt.subplots(figsize=(14, 6))
    for label, series in [("S&P 500", spy_monthly.loc[common]),
                           (f"Top-{best_k} Momentum", best_strat.loc[common])]:
        rolling_mean = series.rolling(12).mean()
        rolling_std = series.rolling(12).std()
        rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(12)
        ax.plot(rolling_sharpe.index, rolling_sharpe.values, label=label, linewidth=1.5)
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.set_title("Rolling 12-Month Sharpe Ratio", fontsize=14, fontweight="bold")
    ax.set_ylabel("Sharpe Ratio")
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{out_dir}/rolling_sharpe.png", dpi=150)
    plt.close(fig)

    print(f"\nAll charts saved to {out_dir}/")


# ── 8. Main ─────────────────────────────────────────────────────────────────

def main():
    OUT_DIR = "output"
    os.makedirs(OUT_DIR, exist_ok=True)

    # Step 1: Get S&P 500 tickers
    print("=" * 70)
    print("S&P 500 MOMENTUM STRATEGY ANALYSIS (12-1 Month Signal)")
    print("=" * 70)
    tickers = get_sp500_tickers()
    print(f"\nFetched {len(tickers)} S&P 500 constituents")

    # Step 2: Download data (start 1yr earlier to have 12-month lookback from 2005)
    prices = download_data(tickers, start="2004-01-01", end="2026-03-31")

    # Step 3: Monthly prices & returns
    monthly_prices = prices.resample("ME").last()
    monthly_returns = compute_monthly_returns(prices)
    spy_monthly = monthly_returns["SPY"].dropna()
    print(f"Monthly return series: {monthly_returns.shape[0]} months × "
          f"{monthly_returns.shape[1]} tickers")
    print(f"Momentum signal: 12-1 month (past year return excluding last month)")

    # Step 4: Optimize K
    k_values = list(range(1, 21))
    print(f"\n{'─' * 70}")
    print(f"Optimizing K across {k_values} ...")
    print(f"{'─' * 70}")
    metrics_df, strats = optimize_k(monthly_prices, monthly_returns, k_values)

    # Find optimal K by Sharpe ratio
    best_idx = metrics_df["Sharpe"].idxmax()
    best_k = int(metrics_df.loc[best_idx, "K"])
    best_strat = strats[best_k]

    # Also find best by Sortino and Calmar
    best_k_sortino = int(metrics_df.loc[metrics_df["Sortino"].idxmax(), "K"])
    best_k_calmar = int(metrics_df.loc[metrics_df["Calmar"].idxmax(), "K"])

    # Step 5: SPY metrics
    spy_metrics = calc_metrics(spy_monthly, "S&P 500 (SPY)")

    # Step 6: Print summary
    print(f"\n{'=' * 70}")
    print("RESULTS SUMMARY")
    print(f"{'=' * 70}")
    print(f"\nOptimal K by Sharpe Ratio:  {best_k}")
    print(f"Optimal K by Sortino Ratio: {best_k_sortino}")
    print(f"Optimal K by Calmar Ratio:  {best_k_calmar}")

    # Comparison table
    comparison = pd.DataFrame([
        spy_metrics,
        calc_metrics(best_strat, f"Top-{best_k} Momentum (Best Sharpe)"),
    ])
    if best_k_sortino != best_k:
        comparison = pd.concat([comparison, pd.DataFrame([
            calc_metrics(strats[best_k_sortino], f"Top-{best_k_sortino} Momentum (Best Sortino)")
        ])], ignore_index=True)

    comparison = comparison.set_index("Label")
    fmt_cols = {
        "CAGR": "{:.2%}", "Annual Vol": "{:.2%}", "Sharpe": "{:.2f}",
        "Sortino": "{:.2f}", "Max Drawdown": "{:.2%}", "Calmar": "{:.2f}",
        "Win Rate": "{:.1%}", "Best Month": "{:.2%}", "Worst Month": "{:.2%}",
        "Total Return": "{:.2%}", "Years": "{:.1f}",
    }
    print(f"\n{'─' * 70}")
    print("Head-to-Head Comparison")
    print(f"{'─' * 70}")
    for col in comparison.columns:
        fmt = fmt_cols.get(col, "{}")
        vals = "  |  ".join(
            f"{idx}: {fmt.format(comparison.loc[idx, col])}"
            for idx in comparison.index
        )
        print(f"  {col:15s}  {vals}")

    # Step 7: Full K scan table
    print(f"\n{'─' * 70}")
    print("Full K Optimization Results")
    print(f"{'─' * 70}")
    display_df = metrics_df[["K", "CAGR", "Annual Vol", "Sharpe", "Sortino",
                              "Max Drawdown", "Calmar", "Win Rate"]].copy()
    for col in ["CAGR", "Annual Vol", "Max Drawdown", "Win Rate"]:
        display_df[col] = display_df[col].map(lambda x: f"{x:.2%}")
    for col in ["Sharpe", "Sortino", "Calmar"]:
        display_df[col] = display_df[col].map(lambda x: f"{x:.2f}")
    display_df["K"] = display_df["K"].astype(int)
    print(display_df.to_string(index=False))

    # SPY reference line
    print(f"\n  SPY Reference:  CAGR={spy_metrics['CAGR']:.2%}  "
          f"Sharpe={spy_metrics['Sharpe']:.2f}  "
          f"MaxDD={spy_metrics['Max Drawdown']:.2%}")

    # Step 8: Plots
    print(f"\n{'─' * 70}")
    print("Generating charts ...")
    plot_results(spy_monthly, best_strat, best_k, metrics_df, k_values, strats, OUT_DIR)

    # Step 9: Save data
    metrics_df.to_csv(f"{OUT_DIR}/momentum_k_optimization.csv", index=False)
    comparison.to_csv(f"{OUT_DIR}/head_to_head_comparison.csv")
    print(f"Data saved to {OUT_DIR}/")
    print(f"\n{'=' * 70}")
    print("ANALYSIS COMPLETE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
