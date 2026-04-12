"""
STRATEGY IMPROVEMENT TESTS
Baseline: S&P 500, 9-1 month momentum, Top 5, equal-weight, monthly rebalance

Tests 10 improvement techniques against the baseline to see which actually help.
"""
import warnings, os, time, json
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import yfinance as yf

OUT = "output_improvements"
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

print("="*80)
print("STRATEGY IMPROVEMENT TESTS")
print("="*80)

# Download daily data (needed for trend filter)
print("\n[1] Downloading daily data...")
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
    if (i//50+1) % 5 == 0: print(f"  Batch {i//50+1}/{(len(all_t)-1)//50+1}")

daily = pd.concat(frames, axis=1)
daily = daily.loc[:, ~daily.columns.duplicated()].dropna(axis=1, how="all")
daily.index = pd.to_datetime(daily.index)
print(f"  {daily.shape[1]} tickers, {daily.shape[0]} days")

# Compute SPY trend filter (daily)
spy_daily = daily["SPY"].dropna()
spy_200ma = spy_daily.rolling(200).mean()
spy_above_200 = (spy_daily > spy_200ma)

# Monthly resample
monthly = daily.resample("ME").last()
monthly_ret = monthly.pct_change()
stock_prices = monthly.drop(columns=["SPY"], errors="ignore")
stock_rets = monthly_ret.drop(columns=["SPY"], errors="ignore")
spy_rets = monthly_ret["SPY"].dropna()

# Daily vol for each stock (for vol-weighting and risk-adjusted signal)
daily_rets = daily.pct_change()

# Month-end SPY trend signal
month_ends = monthly.index
spy_trend_monthly = pd.Series(index=month_ends, dtype=bool)
for me in month_ends:
    nearest = spy_above_200.index[spy_above_200.index <= me]
    if len(nearest) > 0:
        spy_trend_monthly[me] = bool(spy_above_200.loc[nearest[-1]])
    else:
        spy_trend_monthly[me] = True

def vol_lookup(ticker, date, window=63):
    """Compute annualized vol from daily returns ending at `date`."""
    if ticker not in daily_rets.columns: return np.nan
    s = daily_rets[ticker].dropna()
    s = s[s.index <= date]
    if len(s) < window: return np.nan
    return s.iloc[-window:].std() * np.sqrt(252)

def run_strategy(lookback=9, skip=1, k=5, *,
                 trend_filter=False, vol_weight=False, risk_adj_signal=False,
                 dual_momentum=False, multi_lookback=False, hold_months=1,
                 vol_target=None):
    """Generic momentum strategy with optional enhancements."""
    dates = stock_prices.index
    ret_list = []
    held_top = None
    hold_counter = 0

    for i in range(len(dates)):
        if i < 12 + skip - 1: continue
        date = dates[i]

        # Compute signal
        if multi_lookback:
            # Average of 6, 9, 12 month momentum
            sigs = []
            for lb in [6, 9, 12]:
                if i - (lb+skip-1) < 0: continue
                p_s = stock_prices.iloc[i-(lb+skip-1)]
                p_e = stock_prices.iloc[i-skip]
                valid = p_s.notna() & p_e.notna() & (p_s > 0)
                s = (p_e[valid] / p_s[valid] - 1)
                sigs.append(s)
            if not sigs: continue
            signal = pd.concat(sigs, axis=1).mean(axis=1).dropna()
        else:
            p_s = stock_prices.iloc[i-(lookback+skip-1)]
            p_e = stock_prices.iloc[i-skip]
            valid = p_s.notna() & p_e.notna() & (p_s > 0)
            signal = (p_e[valid] / p_s[valid] - 1)

        # Risk-adjusted: divide by vol
        if risk_adj_signal:
            vols = pd.Series({t: vol_lookup(t, date) for t in signal.index})
            vols = vols[vols > 0]
            common = signal.index.intersection(vols.index)
            signal = signal[common] / vols[common]

        if len(signal) < k: continue

        # Dual momentum: require positive absolute return
        if dual_momentum:
            signal = signal[signal > 0]
            if len(signal) < 1:
                ret_list.append((date, 0.0))
                continue

        # Pick top K
        top = signal.nlargest(min(k, len(signal))).index

        # SPY trend filter: if market below 200MA, go to cash
        if trend_filter and date in spy_trend_monthly.index:
            if not spy_trend_monthly[date]:
                ret_list.append((date, 0.0))
                continue

        # Get next-month returns
        if date not in stock_rets.index: continue
        curr = stock_rets.loc[date, top].dropna()
        curr = curr[np.isfinite(curr)]
        curr = curr.clip(-1.0, 1.0)  # 100% monthly cap
        if len(curr) == 0: continue

        # Weighting
        if vol_weight:
            w = pd.Series({t: 1.0 / max(vol_lookup(t, date), 0.01) for t in curr.index})
            w = w / w.sum()
            r = (curr * w).sum()
        else:
            r = curr.mean()

        # Vol targeting
        if vol_target is not None:
            # Estimate portfolio vol from last 12 months
            if len(ret_list) >= 12:
                recent = pd.Series([x[1] for x in ret_list[-12:]])
                pvol = recent.std() * np.sqrt(12)
                if pvol > 0:
                    scale = min(vol_target / pvol, 1.5)
                    r = r * scale

        ret_list.append((date, r))

    s = pd.Series(dict(ret_list))
    s.index = pd.to_datetime(s.index)
    return s

def metrics(r, label=""):
    r = r.dropna()
    if len(r) < 24: return {}
    rfm = (1.03)**(1/12)-1
    ex = r - rfm
    tot = (1+r).prod()-1
    ny = len(r)/12
    cagr = (1+tot)**(1/ny)-1
    vol = r.std()*np.sqrt(12)
    sharpe = ex.mean()/r.std() if r.std()>0 else 0
    dn = r[r<rfm]
    sortino = ex.mean()/dn.std() if len(dn)>1 and dn.std()>0 else 0
    w = (1+r).cumprod()
    dd = (w-w.cummax())/w.cummax()
    maxdd = dd.min()
    calmar = cagr/abs(maxdd) if maxdd!=0 else 0
    winr = (r>0).mean()
    c = r.index.intersection(spy_rets.index)
    s_, b_ = r.loc[c], spy_rets.loc[c]
    beat5y = np.nan
    if len(s_)>=60:
        sr = s_.rolling(60).apply(lambda x:(1+x).prod()-1, raw=True)
        br = b_.rolling(60).apply(lambda x:(1+x).prod()-1, raw=True)
        v = sr.dropna().index.intersection(br.dropna().index)
        beat5y = (sr.loc[v]>br.loc[v]).mean()
    return {"Strategy":label,"CAGR":cagr,"Vol":vol,"Sharpe":sharpe,"Sortino":sortino,
            "Max DD":maxdd,"Calmar":calmar,"Win Rate":winr,"Beat SPY 5Y":beat5y,
            "Worst Mo":r.min(),"Best Mo":r.max()}

# ─────────────────────────────────────────────────────────
# RUN ALL STRATEGIES
# ─────────────────────────────────────────────────────────
print("\n[2] Running baseline + 10 improvements...")
results = {}
strats = {}

print("  Baseline (9-1, K=5)...")
strats["Baseline"] = run_strategy(9, 1, 5)
print("  1. +SPY Trend Filter (200MA)...")
strats["1: +Trend Filter"] = run_strategy(9, 1, 5, trend_filter=True)
print("  2. +Vol-Weighted...")
strats["2: +Vol Weighted"] = run_strategy(9, 1, 5, vol_weight=True)
print("  3. +Risk-Adj Signal...")
strats["3: +Risk-Adj Signal"] = run_strategy(9, 1, 5, risk_adj_signal=True)
print("  4. +Dual Momentum...")
strats["4: +Dual Momentum"] = run_strategy(9, 1, 5, dual_momentum=True)
print("  5. +Multi-Lookback (6,9,12)...")
strats["5: +Multi-Lookback"] = run_strategy(9, 1, 5, multi_lookback=True)
print("  6. +Trend + Vol-Weighted...")
strats["6: +Trend+VolW"] = run_strategy(9, 1, 5, trend_filter=True, vol_weight=True)
print("  7. +Trend + Dual Momentum...")
strats["7: +Trend+Dual"] = run_strategy(9, 1, 5, trend_filter=True, dual_momentum=True)
print("  8. ALL: Trend+VolW+Dual+MultiLB...")
strats["8: ALL Combined"] = run_strategy(9, 1, 5, trend_filter=True, vol_weight=True,
                                          dual_momentum=True, multi_lookback=True)
print("  9. K=10 + Trend Filter (more diversified)...")
strats["9: K=10+Trend"] = run_strategy(9, 1, 10, trend_filter=True)
print("  10. K=8 + Trend + Dual...")
strats["10: K=8+Trend+Dual"] = run_strategy(9, 1, 8, trend_filter=True, dual_momentum=True)

# SPY benchmark
strats["SPY"] = spy_rets

# Metrics
rows = []
for label, s in strats.items():
    m = metrics(s, label)
    if m: rows.append(m)
df = pd.DataFrame(rows).set_index("Strategy")

print("\n" + "="*110)
print("RESULTS")
print("="*110)
fmt_df = df.copy()
for col in ["CAGR","Vol","Max DD","Win Rate","Beat SPY 5Y","Worst Mo","Best Mo"]:
    fmt_df[col] = fmt_df[col].map(lambda x: f"{x:.1%}" if pd.notna(x) else "N/A")
for col in ["Sharpe","Sortino","Calmar"]:
    fmt_df[col] = fmt_df[col].map(lambda x: f"{x:.2f}")
print(fmt_df.to_string())

# Rank by Sharpe
print("\n" + "="*110)
print("RANKED BY SHARPE")
print("="*110)
ranked = df.drop("SPY", errors="ignore").sort_values("Sharpe", ascending=False)
for label, r in ranked.iterrows():
    change = ""
    if label != "Baseline":
        base = df.loc["Baseline"]
        ds = r["Sharpe"] - base["Sharpe"]
        dc = r["CAGR"] - base["CAGR"]
        dd = r["Max DD"] - base["Max DD"]
        change = f"  (ΔSharpe {ds:+.3f}  ΔCAGR {dc:+.1%}  ΔMaxDD {dd:+.1%})"
    print(f"  {label:25s} Sharpe={r['Sharpe']:.3f}  CAGR={r['CAGR']:.1%}  MaxDD={r['Max DD']:.1%}{change}")

# Save CSV
df.to_csv(f"{OUT}/improvements_results.csv")

# Cumulative chart
fig, ax = plt.subplots(figsize=(16, 9))
colors = plt.cm.tab10.colors
for i, (label, s) in enumerate(strats.items()):
    c = s.index.intersection(spy_rets.index)
    cum = (1+s.loc[c]).cumprod()
    lw = 3 if label == "Baseline" else (3 if "ALL" in label or "Trend+Dual" in label else 1.5)
    color = "black" if label == "SPY" else ("red" if label == "Baseline" else colors[i % 10])
    ls = "--" if label == "SPY" else "-"
    ax.plot(cum.index, cum.values, label=label, lw=lw, color=color, ls=ls, alpha=0.85)
ax.set_yscale("log")
ax.set_title("Strategy Improvements: Cumulative Growth (log scale)", fontsize=14, fontweight="bold")
ax.set_ylabel("Growth of $1 (log)")
ax.legend(loc="upper left", fontsize=9)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x,_: f"${x:,.0f}"))
fig.tight_layout()
fig.savefig(f"{OUT}/01_improvements_cumulative.png", dpi=140)
plt.close(fig)

# Drawdown comparison
fig, axes = plt.subplots(4, 1, figsize=(16, 11), sharex=True)
for ax, label in zip(axes, ["Baseline", "1: +Trend Filter", "7: +Trend+Dual", "8: ALL Combined"]):
    s = strats[label]
    c = s.index.intersection(spy_rets.index)
    w = (1+s.loc[c]).cumprod()
    dd = (w-w.cummax())/w.cummax()
    ax.fill_between(dd.index, dd.values, 0, alpha=0.5, color="red")
    ax.set_title(f"{label}  (Max DD: {dd.min():.1%})", fontweight="bold")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
fig.tight_layout()
fig.savefig(f"{OUT}/02_drawdowns.png", dpi=140)
plt.close(fig)

print(f"\nCharts + CSV saved to {OUT}/")
print("DONE")
