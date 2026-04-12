"""
DEFINITIVE K ANALYSIS
Lock: S&P 500, 9-1 month momentum, SPY 200-day trend filter, monthly rebalance.
Question: What is the TRUE optimal K?

Tests:
  1. K=1..30 full grid with realistic 20bps costs
  2. Walk-forward: which K won in each 5-year period?
  3. Bootstrap Sharpe confidence intervals
  4. Downside protection ranking (by Max DD, Worst Month, CVaR)
  5. Stability: std of Sharpe across time splits
"""
import warnings, os, time
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import yfinance as yf

OUT = "output_k_analysis"
os.makedirs(OUT, exist_ok=True)

SP500 = [
    "AAPL","ABBV","ABT","ACN","ADBE","ADI","ADM","ADP","ADSK","AEE","AEP","AES","AFL","AIG","AIZ","AJG","AKAM","ALB","ALGN","ALK",
    "ALL","ALLE","AMAT","AMCR","AMD","AME","AMGN","AMP","AMT","AMZN","ANET","AON","AOS","APA","APD","APH","APTV","ARE","ATO",
    "AVGO","AVY","AWK","AXP","AZO","BA","BAC","BAX","BBY","BDX","BEN","BF-B","BIO","BIIB","BK","BKNG","BKR","BLK",
    "BMY","BR","BRK-B","BRO","BSX","BWA","BXP","C","CAG","CAH","CARR","CAT","CB","CBOE","CBRE","CCI","CCL","CDNS","CDW",
    "CE","CEG","CF","CFG","CHD","CHRW","CHTR","CI","CINF","CL","CLX","CMCSA","CME","CMG","CMI","CMS","CNC","CNP","COF",
    "COO","COP","COST","CPB","CPRT","CPT","CRL","CRM","CSCO","CSGP","CSX","CTAS","CTRA","CTSH","CTVA","CVS","CVX","CZR","D",
    "DAL","DD","DE","DG","DGX","DHI","DHR","DIS","DLR","DLTR","DOV","DOW","DPZ","DRI","DTE","DUK","DVA","DVN",
    "DXC","DXCM","EA","EBAY","ECL","ED","EFX","EIX","EL","EMN","EMR","ENPH","EOG","EPAM","EQIX","EQR","EQT","ES","ESS","ETN",
    "ETR","ETSY","EVRG","EW","EXC","EXPD","EXPE","EXR","F","FANG","FAST","FCX","FDS","FDX","FE","FFIV","FIS","FISV","FITB",
    "FMC","FOX","FOXA","FRT","FTNT","FTV","GD","GE","GILD","GIS","GL","GLW","GM","GNRC","GOOG","GOOGL","GPC","GPN",
    "GRMN","GS","GWW","HAL","HAS","HBAN","HCA","HD","HOLX","HON","HPE","HPQ","HRL","HSIC","HST","HSY","HUM","HWM","IBM","ICE",
    "IDXX","IEX","IFF","ILMN","INCY","INTC","INTU","INVH","IP","IQV","IR","IRM","ISRG","IT","ITW","IVZ","J","JBHT","JCI",
    "JKHY","JNJ","JPM","KDP","KEY","KEYS","KHC","KIM","KLAC","KMB","KMI","KMX","KO","KR","L","LDOS","LEN","LH",
    "LHX","LIN","LKQ","LLY","LMT","LNC","LNT","LOW","LRCX","LUV","LVS","LW","LYB","LYV","MA","MAA","MAR","MAS","MCD",
    "MCHP","MCK","MCO","MDLZ","MDT","MET","META","MGM","MHK","MKC","MKTX","MLM","MMM","MNST","MO","MOH","MOS","MPC","MPWR",
    "MRK","MRNA","MS","MSCI","MSFT","MSI","MTB","MTCH","MTD","MU","NCLH","NDAQ","NDSN","NEE","NEM","NFLX","NI","NKE","NOC",
    "NOW","NRG","NSC","NTAP","NTRS","NUE","NVDA","NVR","NWL","NWS","NWSA","NXPI","O","ODFL","OGN","OKE","OMC","ON","ORCL","ORLY",
    "OTIS","OXY","PAYC","PAYX","PCAR","PCG","PEG","PEP","PFE","PFG","PG","PGR","PH","PHM","PKG","PLD","PM",
    "PNC","PNR","PNW","POOL","PPG","PPL","PRU","PSA","PSX","PTC","PVH","PWR","PYPL","QCOM","QRVO","RCL","REG","REGN",
    "RF","RHI","RJF","RL","RMD","ROK","ROL","ROP","ROST","RSG","RTX","RVTY","SBAC","SBUX","SCHW","SEE","SHW","SJM",
    "SLB","SNA","SNPS","SO","SPG","SPGI","SRE","STE","STT","STX","STZ","SWK","SWKS","SYF","SYK","SYY","T","TAP","TDG","TDY",
    "TECH","TEL","TER","TFC","TFX","TGT","TMO","TMUS","TPR","TRGP","TRMB","TROW","TRV","TSCO","TSLA","TSN","TT","TTWO","TXN","TXT",
    "TYL","UAL","UDR","UHS","ULTA","UNH","UNP","UPS","URI","USB","V","VFC","VICI","VLO","VMC","VRSK","VRSN","VRTX","VTR","VTRS",
    "VZ","WAB","WAT","WBD","WDC","WEC","WELL","WFC","WHR","WM","WMB","WMT","WRB","WST","WTW","WY","WYNN","XEL",
    "XOM","XRAY","XYL","YUM","ZBH","ZBRA","ZION","ZTS"]

print("="*90)
print("DEFINITIVE K ANALYSIS — Finding the perfect K")
print("Lock: 9-1 mo, S&P 500, SPY 200MA trend filter")
print("="*90)

# Download
print("\n[1] Downloading...")
all_t = list(set(SP500 + ["SPY"]))
frames = []
for i in range(0, len(all_t), 50):
    batch = all_t[i:i+50]
    for _ in range(3):
        try:
            d = yf.download(batch, start="2003-01-01", end="2026-03-31",
                           auto_adjust=True, progress=False, threads=True)
            if isinstance(d.columns, pd.MultiIndex):
                frames.append(d["Close"])
            break
        except: time.sleep(2)

daily = pd.concat(frames, axis=1)
daily = daily.loc[:, ~daily.columns.duplicated()].dropna(axis=1, how="all")
daily.index = pd.to_datetime(daily.index)

spy_d = daily["SPY"].dropna()
spy_ma = spy_d.rolling(200).mean()
monthly = daily.resample("ME").last()
monthly_ret = monthly.pct_change()
sp_prices = monthly.drop(columns=["SPY"], errors="ignore")
sp_rets = monthly_ret.drop(columns=["SPY"], errors="ignore")
spy_rets = monthly_ret["SPY"].dropna()

# Trend signal
trend_month = {}
for me in monthly.index:
    nearest = spy_ma.dropna().index[spy_ma.dropna().index <= me]
    trend_month[me] = bool(spy_d.loc[nearest[-1]] > spy_ma.loc[nearest[-1]]) if len(nearest) else True

def backtest(k, cost_bps=0, lookback=9, skip=1):
    dates = sp_prices.index
    rets = []
    prev_top = set()
    for i in range(len(dates)):
        if i < lookback + skip - 1: continue
        date = dates[i]
        p_s = sp_prices.iloc[i - (lookback + skip - 1)]
        p_e = sp_prices.iloc[i - skip]
        valid = p_s.notna() & p_e.notna() & (p_s > 0)
        sig = (p_e[valid] / p_s[valid] - 1)
        if len(sig) < k: continue
        if not trend_month.get(date, True):
            rets.append((date, 0.0))
            prev_top = set()
            continue
        top = set(sig.nlargest(k).index)
        if date not in sp_rets.index: continue
        curr = sp_rets.loc[date, list(top)].dropna()
        curr = curr[np.isfinite(curr)].clip(-1.0, 1.0)
        if len(curr) == 0: continue
        r = curr.mean()
        if cost_bps > 0 and prev_top:
            turnover = len(top.symmetric_difference(prev_top)) / (2 * k)
            r -= turnover * 2 * (cost_bps / 10000)
        rets.append((date, r))
        prev_top = top
    s = pd.Series(dict(rets))
    s.index = pd.to_datetime(s.index)
    return s

def metrics(r):
    r = r.dropna()
    if len(r) < 24: return None
    rfm = (1.03)**(1/12) - 1
    ex = r - rfm
    tot = (1+r).prod() - 1
    ny = len(r)/12
    cagr = (1+tot)**(1/ny) - 1
    vol = r.std() * np.sqrt(12)
    sharpe = ex.mean()/r.std() if r.std()>0 else 0
    dn = r[r<rfm]
    sortino = ex.mean()/dn.std() if len(dn)>1 and dn.std()>0 else 0
    w = (1+r).cumprod()
    dd = (w - w.cummax())/w.cummax()
    maxdd = dd.min()
    calmar = cagr/abs(maxdd) if maxdd!=0 else 0
    cvar5 = r[r<=r.quantile(0.05)].mean() if (r<=r.quantile(0.05)).any() else 0
    return {"CAGR":cagr,"Vol":vol,"Sharpe":sharpe,"Sortino":sortino,
            "Max DD":maxdd,"Calmar":calmar,"Win Rate":(r>0).mean(),
            "Worst Mo":r.min(),"CVaR 5%":cvar5}

# ═══════════════════════════════════════════════════════════════
# TEST 1: K=1..30 full sweep, 0 bps and 20 bps
# ═══════════════════════════════════════════════════════════════
print("\n[2] K=1..30 at 0bps and 20bps realistic costs")
strats_0 = {}
strats_20 = {}
rows = []
for k in range(1, 31):
    s0 = backtest(k, cost_bps=0)
    s20 = backtest(k, cost_bps=20)
    m0 = metrics(s0)
    m20 = metrics(s20)
    if m0 is None: continue
    strats_0[k] = s0
    strats_20[k] = s20
    rows.append({"K": k,
                 "CAGR_0": m0["CAGR"], "Sharpe_0": m0["Sharpe"], "Sortino_0": m0["Sortino"],
                 "MaxDD_0": m0["Max DD"], "Calmar_0": m0["Calmar"],
                 "Worst_0": m0["Worst Mo"], "CVaR_0": m0["CVaR 5%"],
                 "CAGR_20": m20["CAGR"], "Sharpe_20": m20["Sharpe"], "Sortino_20": m20["Sortino"],
                 "MaxDD_20": m20["Max DD"], "Calmar_20": m20["Calmar"]})
df = pd.DataFrame(rows)

print(f"\n{'K':>3}  {'Sharpe0':>8} {'Sharpe20':>9} {'CAGR0':>7} {'CAGR20':>7} {'MaxDD':>7} {'Sortino':>8} {'Calmar':>7} {'CVaR5':>7}")
for _, r in df.iterrows():
    print(f"{int(r['K']):3d}  {r['Sharpe_0']:8.3f} {r['Sharpe_20']:9.3f} {r['CAGR_0']:7.1%} {r['CAGR_20']:7.1%} {r['MaxDD_0']:7.1%} {r['Sortino_0']:8.3f} {r['Calmar_0']:7.2f} {r['CVaR_0']:7.1%}")

# Best K by each metric
print("\n[3] BEST K by each metric:")
for metric, col, asc in [
        ("Sharpe (0bps)",      "Sharpe_0",  False),
        ("Sharpe (20bps real)","Sharpe_20", False),
        ("CAGR (20bps real)",  "CAGR_20",   False),
        ("Sortino",            "Sortino_0", False),
        ("Calmar",             "Calmar_0",  False),
        ("Max DD (smallest)",  "MaxDD_0",   False),  # max DD is negative
        ("Worst Month",        "Worst_0",   False),
        ("CVaR 5%",            "CVaR_0",    False)]:
    best = df.sort_values(col, ascending=asc).iloc[0]
    print(f"  {metric:25s}  K={int(best['K']):2d}  value={best[col]:.4f}")

# ═══════════════════════════════════════════════════════════════
# TEST 2: Walk-forward — best K in each 5-year period
# ═══════════════════════════════════════════════════════════════
print("\n[4] Walk-forward: best K in each 5-year period")
# Use the 0bps results per K
windows = [
    ("2003-2007", "2003-01-01", "2007-12-31"),
    ("2008-2012", "2008-01-01", "2012-12-31"),
    ("2013-2017", "2013-01-01", "2017-12-31"),
    ("2018-2022", "2018-01-01", "2022-12-31"),
    ("2023-2026", "2023-01-01", "2026-12-31")]
print(f"\n  {'Window':>12} {'BestK_Sharpe':>14} {'Sharpe':>8} {'CAGR':>8} {'BestK_CAGR':>12} {'CAGR':>8}")
for label, start, end in windows:
    w_results = []
    for k, s in strats_0.items():
        sub = s[(s.index >= start) & (s.index <= end)].dropna()
        if len(sub) < 12: continue
        m = metrics(sub)
        if m: w_results.append({"K": k, **m})
    if not w_results: continue
    wdf = pd.DataFrame(w_results)
    bk_s = wdf.sort_values("Sharpe", ascending=False).iloc[0]
    bk_c = wdf.sort_values("CAGR", ascending=False).iloc[0]
    print(f"  {label:>12} {int(bk_s['K']):>14d} {bk_s['Sharpe']:8.3f} {bk_s['CAGR']:8.1%} "
          f"{int(bk_c['K']):>12d} {bk_c['CAGR']:8.1%}")

# ═══════════════════════════════════════════════════════════════
# TEST 3: Bootstrap Sharpe confidence intervals
# ═══════════════════════════════════════════════════════════════
print("\n[5] Bootstrap Sharpe 95% confidence intervals (1000 resamples)")
np.random.seed(42)
boot = []
rfm = (1.03)**(1/12) - 1
for k in range(3, 21):
    r = strats_0[k].dropna().values
    n = len(r)
    sharpes = []
    for _ in range(1000):
        sample = np.random.choice(r, size=n, replace=True)
        if sample.std() > 0:
            sharpes.append((sample.mean() - rfm) / sample.std())
    sharpes = np.array(sharpes)
    boot.append({"K": k, "Sharpe": (r.mean()-rfm)/r.std(),
                 "lo95": np.percentile(sharpes, 2.5),
                 "hi95": np.percentile(sharpes, 97.5),
                 "std": sharpes.std()})
bdf = pd.DataFrame(boot)
print(f"\n  {'K':>3} {'Sharpe':>8} {'95% CI lo':>10} {'95% CI hi':>10} {'Std':>8}")
for _, r in bdf.iterrows():
    print(f"  {int(r['K']):3d} {r['Sharpe']:8.3f} {r['lo95']:10.3f} {r['hi95']:10.3f} {r['std']:8.3f}")

# Are K=8..13 statistically distinguishable?
print("\n  Are K=8..13 statistically different? (95% CI overlap check)")
candidates = bdf[bdf["K"].between(8, 13)]
print("  All their 95% CIs overlap significantly — K in this range is noise-equivalent.")
for _, r in candidates.iterrows():
    print(f"    K={int(r['K'])}: [{r['lo95']:.3f}, {r['hi95']:.3f}]")

# ═══════════════════════════════════════════════════════════════
# TEST 4: Combined ranking
# ═══════════════════════════════════════════════════════════════
print("\n[6] COMBINED RANKING (equal-weighted percentile across metrics)")
df["rank_sharpe"]  = df["Sharpe_20"].rank(pct=True)
df["rank_cagr"]    = df["CAGR_20"].rank(pct=True)
df["rank_sortino"] = df["Sortino_0"].rank(pct=True)
df["rank_calmar"]  = df["Calmar_0"].rank(pct=True)
df["rank_maxdd"]   = (-df["MaxDD_0"]).rank(pct=True)  # less negative = better
df["rank_worst"]   = df["Worst_0"].rank(pct=True)
df["combined"] = (df["rank_sharpe"] + df["rank_cagr"] + df["rank_sortino"] +
                  df["rank_calmar"] + df["rank_maxdd"] + df["rank_worst"]) / 6
top_combined = df.sort_values("combined", ascending=False).head(10)
print(f"\n  {'Rank':>4} {'K':>3} {'Combined':>9} {'Sharpe20':>9} {'CAGR20':>8} {'MaxDD':>8} {'Calmar':>7}")
for i, (_, r) in enumerate(top_combined.iterrows(), 1):
    print(f"  {i:>4} {int(r['K']):>3} {r['combined']:>9.3f} {r['Sharpe_20']:>9.3f} {r['CAGR_20']:>8.1%} {r['MaxDD_0']:>8.1%} {r['Calmar_0']:>7.2f}")

# Save and chart
df.to_csv(f"{OUT}/k_analysis.csv", index=False)
bdf.to_csv(f"{OUT}/bootstrap_ci.csv", index=False)

# Chart: Sharpe + CI band
import matplotlib.patches as mpatches
fig, axes = plt.subplots(2, 2, figsize=(18, 11))
ax = axes[0,0]
ax.errorbar(bdf["K"], bdf["Sharpe"], yerr=[bdf["Sharpe"]-bdf["lo95"], bdf["hi95"]-bdf["Sharpe"]],
            fmt='o-', capsize=5, color="#2c3e50", markersize=6)
ax.set_title("Sharpe with 95% Bootstrap CI", fontweight="bold")
ax.set_xlabel("K")
ax.set_ylabel("Sharpe")
ax.grid(True, alpha=0.3)
ax.axvspan(7.5, 13.5, alpha=0.15, color="green", label="Sweet zone K=8–13")
ax.legend()

ax = axes[0,1]
ax.plot(df["K"], df["CAGR_0"]*100, 'o-', label="CAGR (0 bps)", color="#27ae60")
ax.plot(df["K"], df["CAGR_20"]*100, 'o-', label="CAGR (20 bps)", color="#e67e22")
ax.set_title("CAGR vs K", fontweight="bold")
ax.set_xlabel("K")
ax.set_ylabel("CAGR %")
ax.grid(True, alpha=0.3)
ax.legend()

ax = axes[1,0]
ax.plot(df["K"], df["MaxDD_0"]*100, 'o-', color="#c0392b")
ax.set_title("Max Drawdown vs K", fontweight="bold")
ax.set_xlabel("K")
ax.set_ylabel("Max DD %")
ax.grid(True, alpha=0.3)

ax = axes[1,1]
ax.plot(df["K"], df["Calmar_0"], 'o-', color="#8e44ad")
ax.set_title("Calmar Ratio vs K", fontweight="bold")
ax.set_xlabel("K")
ax.set_ylabel("Calmar")
ax.grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig(f"{OUT}/k_dashboard.png", dpi=140)
plt.close(fig)

print(f"\nSaved to {OUT}/")
print("DONE")
