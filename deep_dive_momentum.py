"""
Deep-Dive Momentum Strategy Analysis
======================================
Tests EVERY dimension that matters for a real investment strategy:
  1. Lookback periods: 3-1, 6-1, 9-1, 12-1, 18-1 month signals
  2. K values: 1 through 20
  3. Transaction costs: 0, 10, 25, 50 bps per side
  4. Tail risk: VaR, CVaR (Expected Shortfall), skewness, kurtosis
  5. Drawdown analysis: max DD, avg DD, DD duration
  6. Regime analysis: bull vs bear market performance
  7. Rolling consistency: % of rolling 1/3/5-year periods beating SPY
  8. Turnover analysis: monthly portfolio turnover rates
  9. Decade-by-decade breakdown
  10. Final composite score & recommendation
"""

import warnings, os, time, itertools
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from scipy import stats as sp_stats

OUT_DIR = "output_deep_dive"
os.makedirs(OUT_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════
# DATA LOADING (reuse tickers from main script)
# ═══════════════════════════════════════════════════════════════════════

def get_sp500_tickers():
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

def download_data(tickers, start="2003-01-01", end="2026-03-31"):
    import yfinance as yf
    all_tickers = list(set(tickers + ["SPY"]))
    print(f"Downloading {len(all_tickers)} tickers ({start} -> {end}) ...")
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
                time.sleep(2 * attempt)
        print(f"  Batch {i//batch_size+1}/{(len(all_tickers)-1)//batch_size+1}")
    prices = pd.concat(frames, axis=1)
    prices = prices.loc[:, ~prices.columns.duplicated()]
    prices.index = pd.to_datetime(prices.index)
    print(f"Got {prices.shape[0]} days x {prices.shape[1]} tickers")
    return prices


# ═══════════════════════════════════════════════════════════════════════
# GENERALIZED MOMENTUM STRATEGY
# ═══════════════════════════════════════════════════════════════════════

def momentum_strategy_general(monthly_prices, monthly_returns, k,
                               lookback=12, skip=1, cost_bps=0):
    """
    Generalized momentum strategy.
    
    Parameters
    ----------
    lookback : int - months of return to measure (e.g. 12)
    skip : int - months to skip at end (e.g. 1 for 12-1)
    cost_bps : float - one-way transaction cost in basis points
    
    Returns: (portfolio_return_series, turnover_series)
    """
    spy_col = "SPY"
    stock_prices = monthly_prices.drop(columns=[spy_col], errors="ignore")
    stock_rets = monthly_returns.drop(columns=[spy_col], errors="ignore")
    
    common_dates = stock_prices.index.intersection(stock_rets.index).sort_values()
    
    port_returns = []
    turnovers = []
    prev_holdings = set()
    
    for idx in range(len(common_dates)):
        date = common_dates[idx]
        price_pos = stock_prices.index.get_loc(date)
        min_history = lookback + skip - 1
        if price_pos < min_history:
            continue
        
        # Signal: return from t-(lookback+skip-1) to t-skip
        p_start = stock_prices.iloc[price_pos - (lookback + skip - 1)]
        p_end = stock_prices.iloc[price_pos - skip]
        signal = (p_end / p_start - 1).dropna()
        
        if len(signal) < k:
            continue
        
        top_k = set(signal.nlargest(k).index)
        
        # Turnover: fraction of portfolio that changed
        if prev_holdings:
            overlap = len(top_k & prev_holdings)
            turnover = 1.0 - overlap / max(len(top_k), len(prev_holdings))
        else:
            turnover = 1.0
        turnovers.append((date, turnover))
        
        # Return for this month
        curr = stock_rets.loc[date][list(top_k)].dropna()
        if len(curr) == 0:
            prev_holdings = top_k
            continue
        
        gross_ret = curr.mean()
        # Apply transaction costs: cost on turnover fraction, both buy and sell side
        cost = turnover * 2 * (cost_bps / 10000)
        net_ret = gross_ret - cost
        
        port_returns.append((date, net_ret))
        prev_holdings = top_k
    
    ret_series = pd.Series(dict(port_returns))
    ret_series.index = pd.to_datetime(ret_series.index)
    turn_series = pd.Series(dict(turnovers))
    turn_series.index = pd.to_datetime(turn_series.index)
    return ret_series, turn_series


# ═══════════════════════════════════════════════════════════════════════
# COMPREHENSIVE METRICS
# ═══════════════════════════════════════════════════════════════════════

def full_metrics(monthly_rets, rf_annual=0.03):
    """Compute exhaustive risk/return metrics."""
    r = monthly_rets.dropna()
    if len(r) < 12:
        return {}
    rf_m = (1 + rf_annual) ** (1/12) - 1
    excess = r - rf_m
    
    total_ret = (1 + r).prod() - 1
    n_years = len(r) / 12
    cagr = (1 + total_ret) ** (1 / n_years) - 1 if n_years > 0 else 0
    vol = r.std() * np.sqrt(12)
    sharpe = excess.mean() / r.std() if r.std() > 0 else 0
    
    downside = r[r < rf_m]
    sortino_denom = downside.std() if len(downside) > 1 else r.std()
    sortino = excess.mean() / sortino_denom if sortino_denom > 0 else 0
    
    # Drawdown analysis
    wealth = (1 + r).cumprod()
    peak = wealth.cummax()
    dd = (wealth - peak) / peak
    max_dd = dd.min()
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0
    
    # Drawdown duration (in months)
    in_dd = dd < 0
    dd_groups = (in_dd != in_dd.shift()).cumsum()
    dd_durations = in_dd.groupby(dd_groups).sum()
    dd_durations = dd_durations[dd_durations > 0]
    max_dd_duration = dd_durations.max() if len(dd_durations) > 0 else 0
    avg_dd_duration = dd_durations.mean() if len(dd_durations) > 0 else 0
    
    # Average drawdown (mean of all DD values when in drawdown)
    avg_dd = dd[dd < 0].mean() if (dd < 0).any() else 0
    
    # Tail risk
    var_5 = np.percentile(r, 5)
    cvar_5 = r[r <= var_5].mean() if (r <= var_5).any() else var_5
    var_1 = np.percentile(r, 1)
    cvar_1 = r[r <= var_1].mean() if (r <= var_1).any() else var_1
    
    # Distribution shape
    skewness = sp_stats.skew(r)
    kurt = sp_stats.kurtosis(r)  # excess kurtosis
    
    # Win rate and payoff
    win_rate = (r > 0).mean()
    avg_win = r[r > 0].mean() if (r > 0).any() else 0
    avg_loss = r[r < 0].mean() if (r < 0).any() else 0
    payoff_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    
    # Omega ratio (threshold = rf)
    gains = excess[excess > 0].sum()
    losses = abs(excess[excess < 0].sum())
    omega = gains / losses if losses > 0 else float('inf')
    
    return {
        "CAGR": cagr, "Annual Vol": vol, "Sharpe": sharpe, "Sortino": sortino,
        "Max DD": max_dd, "Avg DD": avg_dd, "Calmar": calmar,
        "Max DD Duration (mo)": max_dd_duration, "Avg DD Duration (mo)": avg_dd_duration,
        "VaR 5%": var_5, "CVaR 5%": cvar_5, "VaR 1%": var_1, "CVaR 1%": cvar_1,
        "Skewness": skewness, "Kurtosis": kurt,
        "Win Rate": win_rate, "Avg Win": avg_win, "Avg Loss": avg_loss,
        "Payoff Ratio": payoff_ratio, "Omega": omega,
        "Best Month": r.max(), "Worst Month": r.min(),
        "Total Return": total_ret, "Years": n_years,
    }


# ═══════════════════════════════════════════════════════════════════════
# ROLLING CONSISTENCY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def rolling_consistency(strat_rets, spy_rets):
    """What % of rolling 1/3/5-year windows does the strategy beat SPY?"""
    common = strat_rets.index.intersection(spy_rets.index).sort_values()
    s = strat_rets.loc[common]
    b = spy_rets.loc[common]
    
    results = {}
    for window_yr, label in [(12, "1Y"), (36, "3Y"), (60, "5Y")]:
        if len(s) < window_yr:
            results[f"Beat SPY {label}"] = np.nan
            results[f"Avg Excess {label}"] = np.nan
            continue
        s_roll = s.rolling(window_yr).apply(lambda x: (1+x).prod()-1, raw=True)
        b_roll = b.rolling(window_yr).apply(lambda x: (1+x).prod()-1, raw=True)
        valid = s_roll.dropna().index.intersection(b_roll.dropna().index)
        beat_pct = (s_roll.loc[valid] > b_roll.loc[valid]).mean()
        avg_excess = (s_roll.loc[valid] - b_roll.loc[valid]).mean()
        results[f"Beat SPY {label}"] = beat_pct
        results[f"Avg Excess {label}"] = avg_excess
    return results

# ═══════════════════════════════════════════════════════════════════════
# REGIME ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def regime_analysis(strat_rets, spy_rets):
    """Performance in bull vs bear vs crash regimes."""
    common = strat_rets.index.intersection(spy_rets.index).sort_values()
    s = strat_rets.loc[common]
    b = spy_rets.loc[common]
    
    # Define regimes based on SPY trailing 12-month return
    spy_12m = b.rolling(12).apply(lambda x: (1+x).prod()-1, raw=True)
    
    results = {}
    # Bull: SPY 12m return > 10%
    bull = spy_12m > 0.10
    bear = spy_12m < -0.10
    neutral = ~bull & ~bear
    
    for mask, label in [(bull, "Bull"), (bear, "Bear"), (neutral, "Neutral")]:
        valid = mask.dropna()
        valid = valid[valid].index.intersection(s.index)
        if len(valid) < 3:
            results[f"{label} CAGR"] = np.nan
            results[f"{label} Sharpe"] = np.nan
            continue
        sr = s.loc[valid]
        results[f"{label} CAGR"] = (1 + sr.mean()) ** 12 - 1
        results[f"{label} Sharpe"] = sr.mean() / sr.std() * np.sqrt(12) if sr.std() > 0 else 0
        results[f"{label} Months"] = len(valid)
    
    # Crash months: SPY drops > 5% in a single month
    crash_months = b[b < -0.05].index.intersection(s.index)
    if len(crash_months) > 0:
        results["Avg Return in SPY Crashes"] = s.loc[crash_months].mean()
        results["Avg SPY Return in Crashes"] = b.loc[crash_months].mean()
        results["Crash Months"] = len(crash_months)
    
    return results

# ═══════════════════════════════════════════════════════════════════════
# DECADE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def decade_analysis(strat_rets, spy_rets):
    """Break down performance by time period."""
    common = strat_rets.index.intersection(spy_rets.index).sort_values()
    s = strat_rets.loc[common]
    b = spy_rets.loc[common]
    
    periods = [
        ("2005-2009", 2005, 2009),
        ("2010-2014", 2010, 2014),
        ("2015-2019", 2015, 2019),
        ("2020-2026", 2020, 2026),
    ]
    
    results = {}
    for label, y1, y2 in periods:
        mask = (s.index.year >= y1) & (s.index.year <= y2)
        sr = s[mask]
        br = b[mask]
        if len(sr) < 6:
            continue
        n_yr = len(sr) / 12
        s_total = (1 + sr).prod() - 1
        b_total = (1 + br).prod() - 1
        results[f"{label} Strat CAGR"] = (1 + s_total) ** (1/n_yr) - 1
        results[f"{label} SPY CAGR"] = (1 + b_total) ** (1/n_yr) - 1
        results[f"{label} Strat Sharpe"] = sr.mean() / sr.std() * np.sqrt(12) if sr.std() > 0 else 0
    return results


# ═══════════════════════════════════════════════════════════════════════
# COMPOSITE SCORING
# ═══════════════════════════════════════════════════════════════════════

def composite_score(row):
    """
    Weighted composite score combining multiple objectives.
    Higher is better. Weights reflect what matters for a MAIN investment strategy:
    - Risk-adjusted return (Sharpe/Sortino) most important
    - Drawdown control critical for sticking with it
    - Consistency matters for real-world implementation
    - Tail risk management
    """
    score = 0
    # Risk-adjusted returns (40%)
    score += 0.20 * min(row.get("Sharpe", 0) / 0.5, 2.0)        # normalize to ~0.5 target
    score += 0.10 * min(row.get("Sortino", 0) / 0.8, 2.0)
    score += 0.10 * min(row.get("Calmar", 0) / 1.0, 2.0)
    
    # Absolute return (15%)
    score += 0.15 * min(row.get("CAGR", 0) / 0.20, 2.0)         # normalize to 20% target
    
    # Drawdown control (20%)
    max_dd = abs(row.get("Max DD", -1))
    score += 0.10 * max(0, (0.60 - max_dd) / 0.30)              # better if < 60%
    score += 0.05 * max(0, (24 - row.get("Max DD Duration (mo)", 24)) / 24)
    score += 0.05 * max(0, (0.15 - abs(row.get("Avg DD", -0.15))) / 0.15)
    
    # Tail risk (10%)
    cvar = abs(row.get("CVaR 5%", -0.15))
    score += 0.05 * max(0, (0.15 - cvar) / 0.15)
    skew = row.get("Skewness", 0)
    score += 0.05 * max(0, (skew + 1) / 2)                       # prefer positive skew
    
    # Consistency (10%)
    score += 0.05 * row.get("Beat SPY 3Y", 0)
    score += 0.05 * row.get("Win Rate", 0.5)
    
    # Transaction cost resilience (5%)
    score += 0.05 * max(0, 1 - row.get("Avg Turnover", 0.5))
    
    return score


# ═══════════════════════════════════════════════════════════════════════
# PLOTTING
# ═══════════════════════════════════════════════════════════════════════

def plot_deep_dive(all_results_df, spy_rets, best_config, best_strat, 
                    best_turn, lookback_compare, k_compare, cost_impact):
    sns.set_theme(style="whitegrid", palette="muted")
    
    # 1. Heatmap: Sharpe by (lookback, K)
    fig, axes = plt.subplots(1, 3, figsize=(24, 8))
    for ax, metric in zip(axes, ["Sharpe", "CAGR", "Max DD"]):
        pivot = all_results_df.pivot_table(index="K", columns="Lookback", 
                                            values=metric, aggfunc="first")
        fmt = ".2f" if metric == "Sharpe" else ".1%"
        cmap = "RdYlGn" if metric != "Max DD" else "RdYlGn_r"
        sns.heatmap(pivot, annot=True, fmt=fmt, cmap=cmap, ax=ax, linewidths=0.5)
        ax.set_title(f"{metric} by Lookback x K", fontweight="bold", fontsize=13)
        ax.set_ylabel("K (# stocks)")
        ax.set_xlabel("Lookback (months)")
    fig.suptitle("Strategy Performance Grid: Lookback Period vs Number of Stocks",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/01_heatmap_lookback_k.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    
    # 2. Cumulative growth: top 3 configs vs SPY
    fig, ax = plt.subplots(figsize=(16, 7))
    top3 = all_results_df.nlargest(3, "Composite Score")
    common = spy_rets.index
    spy_c = (1 + spy_rets).cumprod()
    ax.plot(spy_c.index, spy_c.values, label="S&P 500 (SPY)", linewidth=2.5, color="black")
    colors = ["#e74c3c", "#3498db", "#2ecc71"]
    for i, (_, row) in enumerate(top3.iterrows()):
        lb, k = int(row["Lookback"]), int(row["K"])
        label = f"Top-{k} / {lb}-1mo (Score={row['Composite Score']:.3f})"
        key = (lb, k)
        if key in lookback_compare:
            s = lookback_compare[key]
            c = s.index.intersection(common)
            sc = (1 + s.loc[c]).cumprod()
            ax.plot(sc.index, sc.values, label=label, linewidth=2, color=colors[i])
    ax.set_title("Cumulative Growth: Top 3 Configurations vs S&P 500", fontsize=14, fontweight="bold")
    ax.set_ylabel("Growth of $1")
    ax.legend(fontsize=11)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:.0f}"))
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/02_cumulative_top3.png", dpi=150)
    plt.close(fig)
    
    # 3. Transaction cost impact
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    cost_df = pd.DataFrame(cost_impact)
    for ax, metric in zip(axes, ["CAGR", "Sharpe"]):
        for k_val in cost_df["K"].unique():
            sub = cost_df[cost_df["K"] == k_val]
            ax.plot(sub["Cost_bps"], sub[metric], "o-", label=f"K={k_val}", linewidth=2)
        ax.set_xlabel("Transaction Cost (bps per side)")
        ax.set_ylabel(metric)
        ax.set_title(f"{metric} vs Transaction Costs", fontweight="bold")
        ax.legend()
        if metric == "CAGR":
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    fig.suptitle("Impact of Transaction Costs on Strategy Performance",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/03_transaction_costs.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    
    # 4. Drawdown comparison: best vs SPY
    fig, axes = plt.subplots(2, 1, figsize=(16, 8), sharex=True)
    common = spy_rets.index.intersection(best_strat.index).sort_values()
    for ax, (series, label) in zip(axes, 
            [(spy_rets.loc[common], "S&P 500"),
             (best_strat.loc[common], f"Best Strategy (Top-{best_config[1]}, {best_config[0]}-1mo)")]):
        w = (1 + series).cumprod()
        dd = (w - w.cummax()) / w.cummax()
        ax.fill_between(dd.index, dd.values, 0, alpha=0.5)
        ax.set_ylabel("Drawdown")
        ax.set_title(f"{label} Drawdown", fontweight="bold")
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/04_drawdown_comparison.png", dpi=150)
    plt.close(fig)
    
    # 5. Regime analysis bar chart
    fig, ax = plt.subplots(figsize=(12, 6))
    regimes = ["Bull", "Bear", "Neutral"]
    best_row = all_results_df.loc[all_results_df["Composite Score"].idxmax()]
    strat_vals = [best_row.get(f"{r} CAGR", 0) for r in regimes]
    x = np.arange(len(regimes))
    ax.bar(x - 0.15, strat_vals, 0.3, label=f"Best Momentum", color="#3498db")
    spy_m = full_metrics(spy_rets)
    # We don't have SPY regime data in same format, so just show strat
    ax.set_xticks(x)
    ax.set_xticklabels(regimes)
    ax.set_ylabel("Annualized Return")
    ax.set_title("Strategy Performance by Market Regime", fontweight="bold")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/05_regime_analysis.png", dpi=150)
    plt.close(fig)
    
    # 6. Composite score ranking
    fig, ax = plt.subplots(figsize=(16, 8))
    top20 = all_results_df.nlargest(20, "Composite Score").iloc[::-1]
    labels = [f"K={int(r['K'])}, LB={int(r['Lookback'])}-1" for _, r in top20.iterrows()]
    colors_bar = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(top20)))
    ax.barh(range(len(top20)), top20["Composite Score"].values, color=colors_bar)
    ax.set_yticks(range(len(top20)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Composite Score")
    ax.set_title("Top 20 Configurations by Composite Score", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/06_composite_ranking.png", dpi=150)
    plt.close(fig)
    
    # 7. Rolling beat-rate over time
    fig, ax = plt.subplots(figsize=(16, 6))
    common = spy_rets.index.intersection(best_strat.index).sort_values()
    s = best_strat.loc[common]
    b = spy_rets.loc[common]
    s_roll = s.rolling(36).apply(lambda x: (1+x).prod()-1, raw=True)
    b_roll = b.rolling(36).apply(lambda x: (1+x).prod()-1, raw=True)
    excess_roll = s_roll - b_roll
    ax.fill_between(excess_roll.index, excess_roll.values, 0,
                     where=excess_roll.values > 0, color="green", alpha=0.4, label="Beating SPY")
    ax.fill_between(excess_roll.index, excess_roll.values, 0,
                     where=excess_roll.values <= 0, color="red", alpha=0.4, label="Trailing SPY")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_title("Rolling 3-Year Excess Return vs S&P 500", fontsize=14, fontweight="bold")
    ax.set_ylabel("3-Year Excess Return")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/07_rolling_excess.png", dpi=150)
    plt.close(fig)
    
    # 8. Risk metrics comparison
    fig, axes = plt.subplots(2, 3, figsize=(20, 10))
    metrics_to_plot = ["Sharpe", "Sortino", "Calmar", "CVaR 5%", "Skewness", "Max DD Duration (mo)"]
    for ax, metric in zip(axes.flat, metrics_to_plot):
        vals = all_results_df.groupby("K")[metric].mean()
        ax.bar(vals.index, vals.values, color="#3498db", alpha=0.7)
        ax.set_xlabel("K")
        ax.set_title(metric, fontweight="bold")
    fig.suptitle("Average Risk Metrics by K (across all lookbacks)", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/08_risk_metrics_by_k.png", dpi=150)
    plt.close(fig)
    
    # 9. Annual returns heatmap for best config
    fig, ax = plt.subplots(figsize=(16, 5))
    annual_s = best_strat.groupby(best_strat.index.year).apply(lambda x: (1+x).prod()-1)
    annual_b = spy_rets.groupby(spy_rets.index.year).apply(lambda x: (1+x).prod()-1)
    annual_df = pd.DataFrame({"Best Momentum": annual_s, "SPY": annual_b}).dropna()
    sns.heatmap(annual_df.T, annot=True, fmt=".1%", cmap="RdYlGn", center=0,
                linewidths=0.5, ax=ax)
    ax.set_title(f"Annual Returns: Best Config (K={best_config[1]}, {best_config[0]}-1mo) vs SPY",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/09_annual_returns_best.png", dpi=150)
    plt.close(fig)
    
    # 10. Turnover analysis
    fig, ax = plt.subplots(figsize=(14, 5))
    turn_by_k = all_results_df.groupby("K")["Avg Turnover"].mean()
    ax.bar(turn_by_k.index, turn_by_k.values, color="#e74c3c", alpha=0.7)
    ax.set_xlabel("K (# of stocks)")
    ax.set_ylabel("Average Monthly Turnover")
    ax.set_title("Average Portfolio Turnover by K", fontweight="bold")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/10_turnover_by_k.png", dpi=150)
    plt.close(fig)
    
    print(f"All 10 charts saved to {OUT_DIR}/")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("DEEP-DIVE MOMENTUM STRATEGY ANALYSIS")
    print("Testing every dimension for optimal investment strategy")
    print("=" * 80)
    
    # ── Load Data ──
    tickers = get_sp500_tickers()
    prices = download_data(tickers, start="2003-01-01", end="2026-03-31")
    monthly_prices = prices.resample("ME").last()
    monthly_returns = monthly_prices.pct_change().dropna(how="all")
    spy_monthly = monthly_returns["SPY"].dropna()
    spy_metrics = full_metrics(spy_monthly)
    
    print(f"\nData: {monthly_returns.shape[0]} months x {monthly_returns.shape[1]} tickers")
    
    # ══════════════════════════════════════════════════════════════════
    # TEST 1: LOOKBACK x K GRID (5 lookbacks x 20 K values = 100 combos)
    # ══════════════════════════════════════════════════════════════════
    lookbacks = [3, 6, 9, 12, 18]
    k_values = list(range(1, 21))
    
    print(f"\n{'━' * 80}")
    print(f"TEST 1: Lookback x K Grid ({len(lookbacks)} x {len(k_values)} = {len(lookbacks)*len(k_values)} combinations)")
    print(f"{'━' * 80}")
    
    all_results = []
    lookback_compare = {}  # store return series for top configs
    
    for lb in lookbacks:
        print(f"\n  Lookback = {lb}-1 months:")
        for k in k_values:
            rets, turns = momentum_strategy_general(
                monthly_prices, monthly_returns, k, lookback=lb, skip=1, cost_bps=0)
            if len(rets) < 24:
                continue
            m = full_metrics(rets)
            m["Lookback"] = lb
            m["K"] = k
            m["Avg Turnover"] = turns.mean() if len(turns) > 0 else 0
            
            # Rolling consistency
            rc = rolling_consistency(rets, spy_monthly)
            m.update(rc)
            
            # Regime analysis
            ra = regime_analysis(rets, spy_monthly)
            m.update(ra)
            
            # Decade analysis
            da = decade_analysis(rets, spy_monthly)
            m.update(da)
            
            all_results.append(m)
            lookback_compare[(lb, k)] = rets
            
            print(f"    K={k:2d}  CAGR={m['CAGR']:.1%}  Sharpe={m['Sharpe']:.2f}  "
                  f"MaxDD={m['Max DD']:.1%}  Turn={m['Avg Turnover']:.1%}")
    
    all_df = pd.DataFrame(all_results)
    
    # Compute composite scores
    all_df["Composite Score"] = all_df.apply(composite_score, axis=1)
    
    # ══════════════════════════════════════════════════════════════════
    # TEST 2: TRANSACTION COST SENSITIVITY (on top configs)
    # ══════════════════════════════════════════════════════════════════
    print(f"\n{'━' * 80}")
    print("TEST 2: Transaction Cost Sensitivity")
    print(f"{'━' * 80}")
    
    top5_configs = all_df.nlargest(5, "Composite Score")[["Lookback", "K"]].values
    cost_levels = [0, 5, 10, 15, 25, 50]
    cost_impact = []
    
    for lb, k in top5_configs:
        lb, k = int(lb), int(k)
        for cost in cost_levels:
            rets, turns = momentum_strategy_general(
                monthly_prices, monthly_returns, k, lookback=lb, skip=1, cost_bps=cost)
            m = full_metrics(rets)
            cost_impact.append({
                "Lookback": lb, "K": k, "Cost_bps": cost,
                "CAGR": m.get("CAGR", 0), "Sharpe": m.get("Sharpe", 0),
                "Sortino": m.get("Sortino", 0), "Max DD": m.get("Max DD", 0),
            })
        print(f"  LB={lb}-1, K={k}: CAGR drops from "
              f"{cost_impact[-len(cost_levels)]['CAGR']:.1%} (0bps) to "
              f"{cost_impact[-1]['CAGR']:.1%} (50bps)")
    
    cost_df = pd.DataFrame(cost_impact)
    
    # ══════════════════════════════════════════════════════════════════
    # FIND THE BEST CONFIG
    # ══════════════════════════════════════════════════════════════════
    best_row = all_df.loc[all_df["Composite Score"].idxmax()]
    best_lb = int(best_row["Lookback"])
    best_k = int(best_row["K"])
    best_config = (best_lb, best_k)
    best_strat = lookback_compare[best_config]
    _, best_turn = momentum_strategy_general(
        monthly_prices, monthly_returns, best_k, lookback=best_lb, skip=1)
    
    # ══════════════════════════════════════════════════════════════════
    # PRINT RESULTS
    # ══════════════════════════════════════════════════════════════════
    
    print(f"\n{'═' * 80}")
    print("RESULTS")
    print(f"{'═' * 80}")
    
    # Top 10 by composite score
    print(f"\n{'─' * 80}")
    print("TOP 10 CONFIGURATIONS BY COMPOSITE SCORE")
    print(f"{'─' * 80}")
    top10 = all_df.nlargest(10, "Composite Score")
    cols = ["Lookback", "K", "CAGR", "Annual Vol", "Sharpe", "Sortino", "Max DD",
            "Calmar", "CVaR 5%", "Win Rate", "Avg Turnover", "Beat SPY 3Y", "Composite Score"]
    display = top10[cols].copy()
    for c in ["CAGR", "Annual Vol", "Max DD", "CVaR 5%", "Win Rate", "Avg Turnover", "Beat SPY 3Y"]:
        if c in display.columns:
            display[c] = display[c].map(lambda x: f"{x:.1%}" if pd.notna(x) else "N/A")
    for c in ["Sharpe", "Sortino", "Calmar", "Composite Score"]:
        display[c] = display[c].map(lambda x: f"{x:.3f}")
    display["Lookback"] = display["Lookback"].astype(int).astype(str) + "-1"
    display["K"] = display["K"].astype(int)
    print(display.to_string(index=False))
    
    # SPY reference
    print(f"\n  SPY Reference:  CAGR={spy_metrics['CAGR']:.2%}  Sharpe={spy_metrics['Sharpe']:.2f}  "
          f"MaxDD={spy_metrics['Max DD']:.2%}  Sortino={spy_metrics['Sortino']:.2f}")
    
    # ── Best config deep dive ──
    print(f"\n{'─' * 80}")
    print(f"RECOMMENDED STRATEGY: Top-{best_k} stocks, {best_lb}-1 month lookback")
    print(f"{'─' * 80}")
    
    bm = full_metrics(best_strat)
    rc = rolling_consistency(best_strat, spy_monthly)
    ra = regime_analysis(best_strat, spy_monthly)
    da = decade_analysis(best_strat, spy_monthly)
    
    print(f"\n  === Return Profile ===")
    print(f"  CAGR:                {bm['CAGR']:.2%}")
    print(f"  Total Return:        {bm['Total Return']:.0%}")
    print(f"  Best Month:          {bm['Best Month']:.2%}")
    print(f"  Worst Month:         {bm['Worst Month']:.2%}")
    print(f"  Win Rate:            {bm['Win Rate']:.1%}")
    print(f"  Avg Win:             {bm['Avg Win']:.2%}")
    print(f"  Avg Loss:            {bm['Avg Loss']:.2%}")
    print(f"  Payoff Ratio:        {bm['Payoff Ratio']:.2f}")
    
    print(f"\n  === Risk-Adjusted Returns ===")
    print(f"  Sharpe Ratio:        {bm['Sharpe']:.3f}")
    print(f"  Sortino Ratio:       {bm['Sortino']:.3f}")
    print(f"  Calmar Ratio:        {bm['Calmar']:.3f}")
    print(f"  Omega Ratio:         {bm['Omega']:.3f}")
    print(f"  Annual Volatility:   {bm['Annual Vol']:.2%}")
    
    print(f"\n  === Drawdown Analysis ===")
    print(f"  Max Drawdown:        {bm['Max DD']:.2%}")
    print(f"  Avg Drawdown:        {bm['Avg DD']:.2%}")
    print(f"  Max DD Duration:     {bm['Max DD Duration (mo)']:.0f} months")
    print(f"  Avg DD Duration:     {bm['Avg DD Duration (mo)']:.1f} months")
    
    print(f"\n  === Tail Risk ===")
    print(f"  VaR (5%):            {bm['VaR 5%']:.2%}")
    print(f"  CVaR/ES (5%):        {bm['CVaR 5%']:.2%}")
    print(f"  VaR (1%):            {bm['VaR 1%']:.2%}")
    print(f"  CVaR/ES (1%):        {bm['CVaR 1%']:.2%}")
    print(f"  Skewness:            {bm['Skewness']:.3f}")
    print(f"  Excess Kurtosis:     {bm['Kurtosis']:.3f}")
    
    print(f"\n  === Consistency (Rolling Windows) ===")
    for period in ["1Y", "3Y", "5Y"]:
        beat = rc.get(f"Beat SPY {period}", 0)
        exc = rc.get(f"Avg Excess {period}", 0)
        print(f"  Beat SPY ({period}):      {beat:.1%} of periods  (avg excess: {exc:.1%})")
    
    print(f"\n  === Regime Analysis ===")
    for regime in ["Bull", "Bear", "Neutral"]:
        cagr_r = ra.get(f"{regime} CAGR", 0)
        sharpe_r = ra.get(f"{regime} Sharpe", 0)
        months_r = ra.get(f"{regime} Months", 0)
        print(f"  {regime:8s}:  CAGR={cagr_r:.1%}  Sharpe={sharpe_r:.2f}  ({months_r:.0f} months)")
    crash_ret = ra.get("Avg Return in SPY Crashes", 0)
    spy_crash = ra.get("Avg SPY Return in Crashes", 0)
    n_crash = ra.get("Crash Months", 0)
    print(f"  Crashes:   Strategy={crash_ret:.2%}  SPY={spy_crash:.2%}  ({n_crash:.0f} months)")
    
    print(f"\n  === Period Breakdown ===")
    for period in ["2005-2009", "2010-2014", "2015-2019", "2020-2026"]:
        sc = da.get(f"{period} Strat CAGR", 0)
        bc = da.get(f"{period} SPY CAGR", 0)
        ss = da.get(f"{period} Strat Sharpe", 0)
        print(f"  {period}:  Strategy CAGR={sc:.1%}  SPY CAGR={bc:.1%}  Strat Sharpe={ss:.2f}")
    
    print(f"\n  === Turnover & Costs ===")
    avg_turn = best_turn.mean()
    print(f"  Avg Monthly Turnover: {avg_turn:.1%}")
    print(f"  Implied Annual Turnover: {avg_turn*12:.0%}")
    print(f"  Impact of costs on CAGR:")
    for cost in [0, 10, 25, 50]:
        r2, _ = momentum_strategy_general(
            monthly_prices, monthly_returns, best_k, lookback=best_lb, skip=1, cost_bps=cost)
        m2 = full_metrics(r2)
        print(f"    {cost:3d} bps/side: CAGR={m2['CAGR']:.2%}  Sharpe={m2['Sharpe']:.3f}")
    
    # ══════════════════════════════════════════════════════════════════
    # FINAL RECOMMENDATION
    # ══════════════════════════════════════════════════════════════════
    print(f"\n{'═' * 80}")
    print("FINAL RECOMMENDATION")
    print(f"{'═' * 80}")
    
    # Find best at 25bps cost (realistic)
    best_at_cost = None
    best_score_cost = -1
    for lb in lookbacks:
        for k in k_values:
            r, t = momentum_strategy_general(
                monthly_prices, monthly_returns, k, lookback=lb, skip=1, cost_bps=25)
            if len(r) < 24:
                continue
            m = full_metrics(r)
            m["K"] = k
            m["Lookback"] = lb
            m["Avg Turnover"] = t.mean()
            rc2 = rolling_consistency(r, spy_monthly)
            m.update(rc2)
            sc = composite_score(m)
            if sc > best_score_cost:
                best_score_cost = sc
                best_at_cost = (lb, k, m, sc)
    
    lb_r, k_r, m_r, sc_r = best_at_cost
    print(f"""
  After testing {len(lookbacks)*len(k_values)} configurations across:
    - {len(lookbacks)} lookback periods: {lookbacks}
    - {len(k_values)} K values: 1-20
    - {len(cost_levels)} transaction cost levels: {cost_levels} bps
    - 4 market regimes (bull/bear/neutral/crash)
    - 4 time periods (2005-2009, 2010-2014, 2015-2019, 2020-2026)
    - 20+ risk metrics per configuration

  ┌─────────────────────────────────────────────────────────────────┐
  │  RECOMMENDED STRATEGY (at realistic 25bps costs):              │
  │                                                                │
  │  Signal:  {lb_r}-1 month momentum (skip last month)              │
  │  Stocks:  Top {k_r} by signal, equal-weighted                    │
  │  Rebal:   Monthly                                              │
  │                                                                │
  │  Expected CAGR:      {m_r['CAGR']:>8.2%}                             │
  │  Expected Sharpe:    {m_r['Sharpe']:>8.3f}                             │
  │  Expected Sortino:   {m_r['Sortino']:>8.3f}                             │
  │  Max Drawdown:       {m_r['Max DD']:>8.2%}                             │
  │  Win Rate:           {m_r['Win Rate']:>8.1%}                             │
  │  Beat SPY (3Y):      {m_r.get('Beat SPY 3Y',0):>8.1%}                             │
  │  Composite Score:    {sc_r:>8.3f}                             │
  └─────────────────────────────────────────────────────────────────┘

  IMPORTANT CAVEATS:
  1. Survivorship bias: uses current S&P 500 members applied historically
  2. No slippage model: assumes execution at month-end close prices
  3. No capacity constraints: concentrated portfolios may have market impact
  4. Past performance does not guarantee future results
  5. A {k_r}-stock portfolio has significant single-stock risk
""")
    
    # ── Generate all charts ──
    print(f"{'─' * 80}")
    print("Generating charts...")
    plot_deep_dive(all_df, spy_monthly, best_config, best_strat,
                    best_turn, lookback_compare, k_compare=None, cost_impact=cost_impact)
    
    # ── Save data ──
    all_df.to_csv(f"{OUT_DIR}/full_grid_results.csv", index=False)
    cost_df.to_csv(f"{OUT_DIR}/cost_sensitivity.csv", index=False)
    print(f"Data saved to {OUT_DIR}/")
    print(f"\n{'═' * 80}")
    print("DEEP DIVE COMPLETE")
    print(f"{'═' * 80}")


if __name__ == "__main__":
    main()
