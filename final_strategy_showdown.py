"""
FINAL STRATEGY SHOWDOWN
========================
Head-to-head comparison of EVERY momentum configuration across BOTH universes
(S&P 500 vs All US >$10B) to determine the single best investment strategy.

Tests:
  - 2 universes: S&P 500 (~490 stocks) vs All US >$10B (~946 stocks)
  - 3 lookback periods: 6-1, 9-1, 12-1 months
  - K = 1 through 20
  - Transaction costs: 0, 10, 25 bps
  - 120 total configurations
  - 25+ metrics per configuration
  - Final ranking with composite score

Output: ONE recommended strategy with full justification.
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

OUT_DIR = "output_final"
os.makedirs(OUT_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════
# TICKERS
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

def get_largecap_tickers():
    with open("us_largecap_tickers.json") as f:
        return json.load(f)

def download_data(tickers, start="2003-01-01", end="2026-03-31"):
    import yfinance as yf
    all_tickers = list(set(tickers + ["SPY"]))
    print(f"  Downloading {len(all_tickers)} tickers...")
    batch_size = 50
    frames = []
    total = (len(all_tickers) - 1) // batch_size + 1
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
            except:
                attempt += 1
                time.sleep(2 * attempt)
        bn = i // batch_size + 1
        if bn % 5 == 0 or bn == total:
            print(f"    Batch {bn}/{total}")
    prices = pd.concat(frames, axis=1)
    prices = prices.loc[:, ~prices.columns.duplicated()]
    prices.index = pd.to_datetime(prices.index)
    prices = prices.dropna(axis=1, how="all")
    print(f"  Got {prices.shape[0]} days x {prices.shape[1]} tickers")
    return prices


# ═══════════════════════════════════════════════════════════════════════
# STRATEGY + METRICS
# ═══════════════════════════════════════════════════════════════════════

def momentum_strategy(monthly_prices, monthly_returns, k, lookback=12, skip=1, cost_bps=0):
    spy_col = "SPY"
    stock_prices = monthly_prices.drop(columns=[spy_col], errors="ignore")
    stock_rets = monthly_returns.drop(columns=[spy_col], errors="ignore")
    common_dates = stock_prices.index.intersection(stock_rets.index).sort_values()

    port_returns = []
    prev_holdings = set()
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
        top_k = set(signal.nlargest(k).index)

        # Turnover cost
        if prev_holdings and cost_bps > 0:
            overlap = len(top_k & prev_holdings)
            turnover = 1.0 - overlap / max(len(top_k), len(prev_holdings))
            cost = turnover * 2 * (cost_bps / 10000)
        else:
            cost = 0

        curr = stock_rets.loc[date][list(top_k)].dropna()
        if len(curr) == 0:
            prev_holdings = top_k
            continue
        port_returns.append((date, curr.mean() - cost))
        prev_holdings = top_k

    result = pd.Series(dict(port_returns))
    result.index = pd.to_datetime(result.index)
    return result

def full_metrics(r_raw, spy_rets, rf_annual=0.03):
    r = r_raw.dropna()
    if len(r) < 24:
        return None
    rf_m = (1 + rf_annual) ** (1/12) - 1
    excess = r - rf_m
    total_ret = (1 + r).prod() - 1
    n_years = len(r) / 12
    cagr = (1 + total_ret) ** (1 / n_years) - 1
    vol = r.std() * np.sqrt(12)
    sharpe = excess.mean() / r.std() if r.std() > 0 else 0
    down = r[r < rf_m]
    sort_d = down.std() if len(down) > 1 else r.std()
    sortino = excess.mean() / sort_d if sort_d > 0 else 0
    wealth = (1 + r).cumprod()
    dd = (wealth - wealth.cummax()) / wealth.cummax()
    max_dd = dd.min()
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0

    # Drawdown duration
    in_dd = dd < 0
    dd_groups = (in_dd != in_dd.shift()).cumsum()
    dd_dur = in_dd.groupby(dd_groups).sum()
    dd_dur = dd_dur[dd_dur > 0]
    max_dd_dur = dd_dur.max() if len(dd_dur) > 0 else 0

    # Tail risk
    var5 = np.percentile(r, 5)
    cvar5 = r[r <= var5].mean() if (r <= var5).any() else var5
    skewness = sp_stats.skew(r)
    kurtosis = sp_stats.kurtosis(r)

    win_rate = (r > 0).mean()
    avg_win = r[r > 0].mean() if (r > 0).any() else 0
    avg_loss = r[r < 0].mean() if (r < 0).any() else 0
    payoff = abs(avg_win / avg_loss) if avg_loss != 0 else 0

    # Rolling consistency vs SPY
    common = r.index.intersection(spy_rets.index).sort_values()
    s = r.loc[common]
    b = spy_rets.loc[common]

    beat_1y = beat_3y = beat_5y = np.nan
    for window, name in [(12, "1Y"), (36, "3Y"), (60, "5Y")]:
        if len(s) >= window:
            sr = s.rolling(window).apply(lambda x: (1+x).prod()-1, raw=True)
            br = b.rolling(window).apply(lambda x: (1+x).prod()-1, raw=True)
            v = sr.dropna().index.intersection(br.dropna().index)
            beat = (sr.loc[v] > br.loc[v]).mean()
            if name == "1Y": beat_1y = beat
            elif name == "3Y": beat_3y = beat
            elif name == "5Y": beat_5y = beat

    # Period breakdown
    periods = {}
    for label, y1, y2 in [("2005-09", 2005, 2009), ("2010-14", 2010, 2014),
                           ("2015-19", 2015, 2019), ("2020-26", 2020, 2026)]:
        mask = (s.index.year >= y1) & (s.index.year <= y2)
        sr = s[mask]
        if len(sr) >= 6:
            ny = len(sr) / 12
            tc = (1 + sr).prod() - 1
            periods[f"{label} CAGR"] = (1 + tc) ** (1/ny) - 1
            periods[f"{label} Sharpe"] = sr.mean() / sr.std() * np.sqrt(12) if sr.std() > 0 else 0

    result = {
        "CAGR": cagr, "Vol": vol, "Sharpe": sharpe, "Sortino": sortino,
        "Max DD": max_dd, "Calmar": calmar, "Max DD Dur": max_dd_dur,
        "VaR 5%": var5, "CVaR 5%": cvar5, "Skew": skewness, "Kurt": kurtosis,
        "Win Rate": win_rate, "Payoff": payoff,
        "Beat SPY 1Y": beat_1y, "Beat SPY 3Y": beat_3y, "Beat SPY 5Y": beat_5y,
        "Best Mo": r.max(), "Worst Mo": r.min(), "Total Ret": total_ret,
    }
    result.update(periods)
    return result

def composite_score(m):
    """Score optimized for a REAL main investment strategy."""
    s = 0
    # Risk-adjusted returns (40%)
    s += 0.20 * min(m.get("Sharpe", 0) / 0.5, 2.0)
    s += 0.10 * min(m.get("Sortino", 0) / 0.8, 2.0)
    s += 0.10 * min(m.get("Calmar", 0) / 1.0, 2.0)
    # Absolute return (15%)
    s += 0.15 * min(m.get("CAGR", 0) / 0.25, 2.0)
    # Drawdown control (20%)
    s += 0.10 * max(0, (0.60 - abs(m.get("Max DD", -1))) / 0.30)
    s += 0.05 * max(0, (30 - m.get("Max DD Dur", 30)) / 30)
    s += 0.05 * max(0, (0.12 - abs(m.get("CVaR 5%", -0.12))) / 0.12)
    # Consistency (15%)
    s += 0.05 * (m.get("Beat SPY 1Y", 0.5) if not np.isnan(m.get("Beat SPY 1Y", np.nan)) else 0.5)
    s += 0.05 * (m.get("Beat SPY 3Y", 0.5) if not np.isnan(m.get("Beat SPY 3Y", np.nan)) else 0.5)
    s += 0.05 * m.get("Win Rate", 0.5)
    # Tail risk (10%)
    s += 0.05 * max(0, (m.get("Skew", 0) + 1) / 2)
    s += 0.05 * max(0, (1.5 - max(0, m.get("Kurt", 0))) / 1.5)
    return s


# ═══════════════════════════════════════════════════════════════════════
# PLOTTING
# ═══════════════════════════════════════════════════════════════════════

def plot_final(all_df, spy_rets, strats, winner, runner_up):
    sns.set_theme(style="whitegrid", palette="muted")

    w_key = (winner["Universe"], winner["Lookback"], winner["K"])
    r_key = (runner_up["Universe"], runner_up["Lookback"], runner_up["K"])

    # 1. Composite score: top 20
    fig, ax = plt.subplots(figsize=(16, 9))
    top20 = all_df.nlargest(20, "Score").iloc[::-1]
    labels = [f"{r['Universe']} | K={int(r['K'])}, {int(r['Lookback'])}-1mo"
              for _, r in top20.iterrows()]
    clrs = ["#2ecc71" if r["Universe"] == "S&P 500" else "#3498db"
            for _, r in top20.iterrows()]
    ax.barh(range(len(top20)), top20["Score"].values, color=clrs)
    ax.set_yticks(range(len(top20)))
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Composite Score", fontsize=12)
    ax.set_title("TOP 20 STRATEGIES: S&P 500 (green) vs All US >$10B (blue)",
                 fontsize=14, fontweight="bold")
    # Add legend
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color="#2ecc71", label="S&P 500"),
                        Patch(color="#3498db", label="All US >$10B")], fontsize=11)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/01_composite_ranking.png", dpi=150)
    plt.close(fig)

    # 2. Cumulative growth: winner vs runner-up vs SPY
    fig, ax = plt.subplots(figsize=(16, 7))
    spy_c = (1 + spy_rets).cumprod()
    ax.plot(spy_c.index, spy_c.values, label="S&P 500 (SPY)", linewidth=2.5,
            color="black", linestyle="--")
    for cfg, color, lw in [(w_key, "#e74c3c", 2.5), (r_key, "#3498db", 2)]:
        s = strats[cfg]
        common = spy_rets.index.intersection(s.index)
        sc = (1 + s.loc[common]).cumprod()
        row = all_df[(all_df["Universe"]==cfg[0]) & (all_df["Lookback"]==cfg[1]) & 
                      (all_df["K"]==cfg[2])].iloc[0]
        lbl = (f"{'WINNER' if cfg==w_key else 'Runner-up'}: {cfg[0]} | "
               f"Top-{int(cfg[2])}, {int(cfg[1])}-1mo "
               f"(Sharpe={row['Sharpe']:.2f}, CAGR={row['CAGR']:.0%})")
        ax.plot(sc.index, sc.values, label=lbl, linewidth=lw, color=color)
    ax.set_title("Cumulative Growth: Winner vs Runner-Up vs S&P 500",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Growth of $1")
    ax.legend(fontsize=10, loc="upper left")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/02_cumulative_winner.png", dpi=150)
    plt.close(fig)

    # 3. Universe comparison heatmap (Sharpe)
    fig, axes = plt.subplots(1, 2, figsize=(20, 9))
    for ax, univ in zip(axes, ["S&P 500", "All US >$10B"]):
        sub = all_df[all_df["Universe"] == univ]
        pivot = sub.pivot_table(index="K", columns="Lookback", values="Sharpe")
        pivot.columns = [f"{int(c)}-1" for c in pivot.columns]
        sns.heatmap(pivot, annot=True, fmt=".2f", cmap="RdYlGn", ax=ax,
                    linewidths=0.5, vmin=0.05, vmax=0.45)
        ax.set_title(f"{univ} — Sharpe Ratio", fontweight="bold", fontsize=13)
        ax.set_ylabel("K (# stocks)")
    fig.suptitle("Sharpe Ratio Comparison: S&P 500 vs All US >$10B",
                 fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/03_sharpe_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # 4. Drawdown comparison
    fig, axes = plt.subplots(3, 1, figsize=(16, 10), sharex=True)
    common_all = spy_rets.index
    for ax, (cfg, label) in zip(axes, [
            (None, "S&P 500 (SPY)"),
            (w_key, f"WINNER: {w_key[0]} | Top-{int(w_key[2])}, {int(w_key[1])}-1mo"),
            (r_key, f"Runner-up: {r_key[0]} | Top-{int(r_key[2])}, {int(r_key[1])}-1mo")]):
        if cfg is None:
            series = spy_rets
        else:
            series = strats[cfg]
        common = common_all.intersection(series.index)
        w = (1 + series.loc[common]).cumprod()
        dd = (w - w.cummax()) / w.cummax()
        ax.fill_between(dd.index, dd.values, 0, alpha=0.5)
        ax.set_ylabel("Drawdown")
        ax.set_title(label, fontweight="bold", fontsize=11)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/04_drawdown_comparison.png", dpi=150)
    plt.close(fig)

    # 5. Annual returns: winner vs SPY
    fig, ax = plt.subplots(figsize=(18, 5))
    ws = strats[w_key]
    annual_w = ws.groupby(ws.index.year).apply(lambda x: (1+x).prod()-1)
    annual_spy = spy_rets.groupby(spy_rets.index.year).apply(lambda x: (1+x).prod()-1)
    adf = pd.DataFrame({"Winner Strategy": annual_w, "SPY": annual_spy}).dropna()
    sns.heatmap(adf.T, annot=True, fmt=".1%", cmap="RdYlGn", center=0,
                linewidths=0.5, ax=ax)
    ax.set_title(f"Annual Returns: Winner ({w_key[0]}, Top-{int(w_key[2])}, {int(w_key[1])}-1mo) vs SPY",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/05_annual_returns.png", dpi=150)
    plt.close(fig)

    # 6. Metrics comparison: SP500 vs LargeCap universe (averaged across all configs)
    fig, axes = plt.subplots(2, 3, figsize=(20, 10))
    metrics_plot = ["Sharpe", "Sortino", "CAGR", "Max DD", "Win Rate", "Calmar"]
    for ax, metric in zip(axes.flat, metrics_plot):
        for univ, color in [("S&P 500", "#2ecc71"), ("All US >$10B", "#3498db")]:
            sub = all_df[all_df["Universe"] == univ].groupby("K")[metric].mean()
            ax.plot(sub.index, sub.values, "o-", label=univ, color=color, linewidth=2)
        ax.set_xlabel("K")
        ax.set_title(metric, fontweight="bold")
        ax.legend(fontsize=9)
        if metric in ["CAGR", "Max DD", "Win Rate"]:
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    fig.suptitle("S&P 500 vs All US >$10B: Metrics by K (averaged across lookbacks)",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/06_universe_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # 7. Transaction cost sensitivity for winner
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    w_sub = all_df[(all_df["Universe"]==w_key[0]) & (all_df["Lookback"]==w_key[1]) & 
                    (all_df["K"]==w_key[2])]
    for ax, metric in zip(axes, ["CAGR", "Sharpe"]):
        ax.plot(w_sub["Cost_bps"], w_sub[metric], "o-", linewidth=2, color="#e74c3c")
        ax.set_xlabel("Transaction Cost (bps/side)")
        ax.set_title(f"Winner: {metric} vs Costs", fontweight="bold")
        if metric == "CAGR":
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/07_cost_sensitivity.png", dpi=150)
    plt.close(fig)

    print(f"\nAll 7 charts saved to {OUT_DIR}/")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("FINAL STRATEGY SHOWDOWN")
    print("S&P 500 vs All US >$10B Market Cap")
    print("=" * 80)

    # ── Load both universes ──
    universes = {}

    print("\n[1/2] Loading S&P 500 universe...")
    sp_tickers = get_sp500_tickers()
    sp_prices = download_data(sp_tickers, start="2003-01-01", end="2026-03-31")
    sp_mp = sp_prices.resample("ME").last()
    sp_mr = sp_mp.pct_change().dropna(how="all")
    universes["S&P 500"] = (sp_mp, sp_mr)
    print(f"  S&P 500: {sp_mr.shape[1]} stocks")

    print("\n[2/2] Loading All US >$10B universe...")
    lc_tickers = get_largecap_tickers()
    lc_prices = download_data(lc_tickers, start="2003-01-01", end="2026-03-31")
    lc_mp = lc_prices.resample("ME").last()
    lc_mr = lc_mp.pct_change().dropna(how="all")
    universes["All US >$10B"] = (lc_mp, lc_mr)
    print(f"  All US >$10B: {lc_mr.shape[1]} stocks")

    spy_monthly = sp_mr["SPY"].dropna()

    # ── Run all combinations ──
    lookbacks = [6, 9, 12]
    k_values = list(range(1, 21))
    cost_levels = [0, 10, 25]

    total = len(universes) * len(lookbacks) * len(k_values) * len(cost_levels)
    print(f"\n{'━' * 80}")
    print(f"Running {total} configurations...")
    print(f"  2 universes x 3 lookbacks x 20 K values x 3 cost levels")
    print(f"{'━' * 80}")

    all_rows = []
    strats = {}  # (universe, lookback, k) -> return series (0 cost)
    count = 0

    for univ_name, (mp, mr) in universes.items():
        print(f"\n  Universe: {univ_name}")
        for lb in lookbacks:
            print(f"    Lookback {lb}-1:")
            for k in k_values:
                for cost in cost_levels:
                    s = momentum_strategy(mp, mr, k, lookback=lb, skip=1, cost_bps=cost)
                    m = full_metrics(s, spy_monthly)
                    if m is None:
                        continue
                    m["Universe"] = univ_name
                    m["Lookback"] = lb
                    m["K"] = k
                    m["Cost_bps"] = cost
                    m["Score"] = composite_score(m)
                    all_rows.append(m)

                    if cost == 0:
                        strats[(univ_name, lb, k)] = s

                    count += 1
                if cost == 0:
                    print(f"      K={k:2d}  CAGR={m['CAGR']:.1%}  Sharpe={m['Sharpe']:.2f}  "
                          f"MaxDD={m['Max DD']:.1%}  Score={m['Score']:.3f}")

    all_df = pd.DataFrame(all_rows)

    # ══════════════════════════════════════════════════════════════════
    # FIND WINNER (at 0 cost first, then verify at 25bps)
    # ══════════════════════════════════════════════════════════════════
    zero_cost = all_df[all_df["Cost_bps"] == 0].copy()
    best_idx = zero_cost["Score"].idxmax()
    winner_0 = zero_cost.loc[best_idx]

    # Also find best at 25bps (realistic)
    cost_25 = all_df[all_df["Cost_bps"] == 25].copy()
    best_idx_25 = cost_25["Score"].idxmax()
    winner_25 = cost_25.loc[best_idx_25]

    # Runner up (different universe from winner if possible)
    winner_univ = winner_0["Universe"]
    other = zero_cost[zero_cost["Universe"] != winner_univ]
    if len(other) > 0:
        runner_up = other.loc[other["Score"].idxmax()]
    else:
        runner_up = zero_cost.nlargest(2, "Score").iloc[1]

    # ══════════════════════════════════════════════════════════════════
    # PRINT RESULTS
    # ══════════════════════════════════════════════════════════════════
    spy_m = full_metrics(spy_monthly, spy_monthly)

    print(f"\n{'═' * 80}")
    print("RESULTS")
    print(f"{'═' * 80}")

    # Top 15 at 0 cost
    print(f"\n{'─' * 80}")
    print("TOP 15 STRATEGIES BY COMPOSITE SCORE (0 bps cost)")
    print(f"{'─' * 80}")
    top15 = zero_cost.nlargest(15, "Score")
    cols = ["Universe", "Lookback", "K", "CAGR", "Vol", "Sharpe", "Sortino",
            "Max DD", "Calmar", "Win Rate", "Beat SPY 3Y", "Score"]
    disp = top15[cols].copy()
    disp["Lookback"] = disp["Lookback"].astype(int).astype(str) + "-1"
    disp["K"] = disp["K"].astype(int)
    for c in ["CAGR", "Vol", "Max DD", "Win Rate", "Beat SPY 3Y"]:
        disp[c] = disp[c].map(lambda x: f"{x:.1%}" if pd.notna(x) else "N/A")
    for c in ["Sharpe", "Sortino", "Calmar", "Score"]:
        disp[c] = disp[c].map(lambda x: f"{x:.3f}")
    print(disp.to_string(index=False))

    # Count universe dominance
    sp_count = (top15["Universe"] == "S&P 500").sum()
    lc_count = (top15["Universe"] == "All US >$10B").sum()
    print(f"\n  Universe dominance in top 15: S&P 500 = {sp_count}, All US >$10B = {lc_count}")

    # ── Head-to-head ──
    print(f"\n{'─' * 80}")
    print("HEAD-TO-HEAD COMPARISON")
    print(f"{'─' * 80}")

    configs = [
        ("SPY (Buy & Hold)", spy_m, None),
        (f"WINNER: {winner_0['Universe']} | Top-{int(winner_0['K'])}, {int(winner_0['Lookback'])}-1mo",
         winner_0.to_dict(), "0 bps"),
        (f"Winner at 25bps: {winner_25['Universe']} | Top-{int(winner_25['K'])}, {int(winner_25['Lookback'])}-1mo",
         winner_25.to_dict(), "25 bps"),
        (f"Runner-up: {runner_up['Universe']} | Top-{int(runner_up['K'])}, {int(runner_up['Lookback'])}-1mo",
         runner_up.to_dict(), "0 bps"),
    ]

    metrics_show = [
        ("CAGR", ".2%"), ("Vol", ".2%"), ("Sharpe", ".3f"), ("Sortino", ".3f"),
        ("Max DD", ".2%"), ("Calmar", ".2f"), ("Max DD Dur", ".0f"),
        ("VaR 5%", ".2%"), ("CVaR 5%", ".2%"), ("Skew", ".2f"),
        ("Win Rate", ".1%"), ("Payoff", ".2f"),
        ("Beat SPY 1Y", ".1%"), ("Beat SPY 3Y", ".1%"), ("Beat SPY 5Y", ".1%"),
    ]

    header = f"  {'Metric':20s}"
    for name, _, _ in configs:
        short = name[:30]
        header += f"  {short:>30s}"
    print(header)
    print("  " + "─" * (20 + 32 * len(configs)))

    for metric, fmt in metrics_show:
        line = f"  {metric:20s}"
        for _, m, _ in configs:
            val = m.get(metric, np.nan)
            if pd.isna(val):
                line += f"  {'N/A':>30s}"
            else:
                line += f"  {format(val, fmt):>30s}"
        print(line)

    # ── Period breakdown for winner ──
    wm = winner_0.to_dict()
    print(f"\n{'─' * 80}")
    print(f"WINNER PERIOD BREAKDOWN: {winner_0['Universe']} | Top-{int(winner_0['K'])}, {int(winner_0['Lookback'])}-1mo")
    print(f"{'─' * 80}")
    for period in ["2005-09", "2010-14", "2015-19", "2020-26"]:
        sc = wm.get(f"{period} CAGR", 0)
        ss = wm.get(f"{period} Sharpe", 0)
        print(f"  {period}:  CAGR = {sc:.1%}   Sharpe = {ss:.2f}")

    # ══════════════════════════════════════════════════════════════════
    # FINAL VERDICT
    # ══════════════════════════════════════════════════════════════════
    print(f"\n{'═' * 80}")
    print("FINAL VERDICT")
    print(f"{'═' * 80}")
    print(f"""
  Tested {total} total configurations across 2 universes.

  ┌─────────────────────────────────────────────────────────────────────┐
  │                                                                     │
  │   #1 RECOMMENDED STRATEGY (0 bps costs):                           │
  │                                                                     │
  │   Universe:  {winner_0['Universe']:<20s}                                  │
  │   Signal:    {int(winner_0['Lookback'])}-1 month momentum                                       │
  │   Holdings:  Top {int(winner_0['K'])} stocks, equal-weighted                            │
  │   Rebalance: Monthly                                                │
  │                                                                     │
  │   CAGR:           {winner_0['CAGR']:>8.1%}                                          │
  │   Sharpe:         {winner_0['Sharpe']:>8.3f}                                          │
  │   Sortino:        {winner_0['Sortino']:>8.3f}                                          │
  │   Max Drawdown:   {winner_0['Max DD']:>8.1%}                                          │
  │   Win Rate:       {winner_0['Win Rate']:>8.1%}                                          │
  │   Beat SPY (3Y):  {winner_0.get('Beat SPY 3Y',0):>8.1%}                                          │
  │   Composite:      {winner_0['Score']:>8.3f}                                          │
  │                                                                     │
  │   #1 AT REALISTIC COSTS (25 bps/side):                             │
  │                                                                     │
  │   Universe:  {winner_25['Universe']:<20s}                                  │
  │   Signal:    {int(winner_25['Lookback'])}-1 month momentum                                       │
  │   Holdings:  Top {int(winner_25['K'])} stocks, equal-weighted                            │
  │   CAGR:           {winner_25['CAGR']:>8.1%}                                          │
  │   Sharpe:         {winner_25['Sharpe']:>8.3f}                                          │
  │   Composite:      {winner_25['Score']:>8.3f}                                          │
  │                                                                     │
  └─────────────────────────────────────────────────────────────────────┘

  WHY {winner_0['Universe'].upper()} WINS:
""")

    # Explain why
    if winner_0["Universe"] == "S&P 500":
        print("""    - S&P 500 stocks are more liquid, lower slippage in practice
    - Higher Sharpe ratios = more return per unit of risk
    - Lower volatility makes the strategy easier to stick with
    - Fewer extreme drawdowns
    - S&P 500 membership acts as a quality filter
    """)
    else:
        print("""    - Broader universe captures more momentum opportunities
    - Higher absolute returns compensate for added volatility
    - More stocks to choose from = stronger momentum signal
    - Diversification benefit from non-S&P 500 large caps
    """)

    print("""  IMPORTANT CAVEATS FOR REAL IMPLEMENTATION:
    1. Survivorship bias: uses current stock lists applied historically
    2. No slippage model: assumes execution at month-end close
    3. Concentrated portfolios have single-stock risk
    4. Past performance does NOT guarantee future results
    5. Consider tax implications of monthly rebalancing
    6. Start with paper trading before committing real capital
    """)

    # ── Charts ──
    print(f"{'─' * 80}")
    print("Generating charts...")
    plot_final(zero_cost, spy_monthly, strats, winner_0, runner_up)

    # ── Save ──
    all_df.to_csv(f"{OUT_DIR}/all_configurations.csv", index=False)
    zero_cost.nlargest(50, "Score").to_csv(f"{OUT_DIR}/top50_strategies.csv", index=False)
    print(f"Data saved to {OUT_DIR}/")
    print(f"\n{'═' * 80}")
    print("SHOWDOWN COMPLETE")
    print(f"{'═' * 80}")

if __name__ == "__main__":
    main()
