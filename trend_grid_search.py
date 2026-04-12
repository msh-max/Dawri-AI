"""
TREND-FILTERED GRID SEARCH
Find the best (lookback, K) combination for S&P 500 with SPY 200-day trend filter.
Tests lookback = 3, 6, 9, 12, 18 x K = 1..20 = 100 configs.
"""
import warnings, os, time
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import yfinance as yf

OUT = "output_trend_grid"
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
print("TREND-FILTERED GRID SEARCH")
print("="*80)

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
    if (i//50+1) % 5 == 0: print(f"  Batch {i//50+1}/{(len(all_t)-1)//50+1}")

daily = pd.concat(frames, axis=1)
daily = daily.loc[:, ~daily.columns.duplicated()].dropna(axis=1, how="all")
daily.index = pd.to_datetime(daily.index)

# Trend filter
spy_daily = daily["SPY"].dropna()
spy_200ma = spy_daily.rolling(200).mean()
spy_above = (spy_daily > spy_200ma)

monthly = daily.resample("ME").last()
monthly_ret = monthly.pct_change()
stock_prices = monthly.drop(columns=["SPY"], errors="ignore")
stock_rets = monthly_ret.drop(columns=["SPY"], errors="ignore")
spy_rets = monthly_ret["SPY"].dropna()

# Monthly trend signal
spy_trend_monthly = pd.Series(index=monthly.index, dtype=bool)
for me in monthly.index:
    nearest = spy_above.index[spy_above.index <= me]
    spy_trend_monthly[me] = bool(spy_above.loc[nearest[-1]]) if len(nearest) > 0 else True

def run(lookback, k, trend=True):
    dates = stock_prices.index
    out = []
    for i in range(len(dates)):
        if i < lookback + 1 - 1: continue
        date = dates[i]
        p_s = stock_prices.iloc[i-lookback]
        p_e = stock_prices.iloc[i-1]
        valid = p_s.notna() & p_e.notna() & (p_s > 0)
        sig = (p_e[valid] / p_s[valid] - 1)
        if len(sig) < k: continue
        if trend and date in spy_trend_monthly.index and not spy_trend_monthly[date]:
            out.append((date, 0.0))
            continue
        top = sig.nlargest(k).index
        if date not in stock_rets.index: continue
        curr = stock_rets.loc[date, top].dropna()
        curr = curr[np.isfinite(curr)].clip(-1.0, 1.0)
        if len(curr) == 0: continue
        out.append((date, curr.mean()))
    s = pd.Series(dict(out))
    s.index = pd.to_datetime(s.index)
    return s

def metrics(r):
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
    return {"CAGR":cagr,"Vol":vol,"Sharpe":sharpe,"Sortino":sortino,
            "Max DD":maxdd,"Calmar":calmar,"Win Rate":winr,"Beat SPY 5Y":beat5y,
            "Worst Mo":r.min(),"Best Mo":r.max()}

# Grid search
print("\n[2] Running 5 lookbacks x 20 K values = 100 configs...")
rows = []
strats = {}
for lb in [3, 6, 9, 12, 18]:
    print(f"  Lookback {lb}-1...")
    for k in range(1, 21):
        s = run(lb, k, trend=True)
        m = metrics(s)
        if not m: continue
        m["Lookback"] = lb
        m["K"] = k
        rows.append(m)
        strats[(lb, k)] = s

df = pd.DataFrame(rows)
df["Composite"] = (
    df["Sharpe"].rank(pct=True) * 0.30 +
    df["Sortino"].rank(pct=True) * 0.15 +
    df["Calmar"].rank(pct=True) * 0.25 +
    df["CAGR"].rank(pct=True) * 0.15 +
    (-df["Max DD"]).rank(pct=True) * 0.15
)

# Top 15 by Sharpe
print("\n"+"="*100)
print("TOP 15 BY SHARPE (with trend filter)")
print("="*100)
top = df.sort_values("Sharpe", ascending=False).head(15)
print(f"{'LB':>3} {'K':>3} {'Sharpe':>8} {'Sortino':>8} {'CAGR':>8} {'MaxDD':>8} {'Calmar':>7} {'Vol':>7} {'WinR':>7} {'Composite':>10}")
for _, r in top.iterrows():
    print(f"{int(r['Lookback']):3d} {int(r['K']):3d} {r['Sharpe']:8.3f} {r['Sortino']:8.3f} {r['CAGR']:8.1%} {r['Max DD']:8.1%} {r['Calmar']:7.2f} {r['Vol']:7.1%} {r['Win Rate']:7.1%} {r['Composite']:10.3f}")

# Top 15 by Composite
print("\n"+"="*100)
print("TOP 15 BY COMPOSITE SCORE")
print("="*100)
topc = df.sort_values("Composite", ascending=False).head(15)
print(f"{'LB':>3} {'K':>3} {'Sharpe':>8} {'Sortino':>8} {'CAGR':>8} {'MaxDD':>8} {'Calmar':>7} {'Vol':>7} {'WinR':>7} {'Composite':>10}")
for _, r in topc.iterrows():
    print(f"{int(r['Lookback']):3d} {int(r['K']):3d} {r['Sharpe']:8.3f} {r['Sortino']:8.3f} {r['CAGR']:8.1%} {r['Max DD']:8.1%} {r['Calmar']:7.2f} {r['Vol']:7.1%} {r['Win Rate']:7.1%} {r['Composite']:10.3f}")

# Heatmaps
sns.set_theme(style="white")
fig, axes = plt.subplots(2, 3, figsize=(22, 12))
for ax, (metric, cmap, fmt) in zip(axes.flat, [
        ("Sharpe", "RdYlGn", ".2f"),
        ("Sortino", "RdYlGn", ".2f"),
        ("CAGR", "RdYlGn", ".1%"),
        ("Max DD", "RdYlGn", ".1%"),
        ("Calmar", "RdYlGn", ".2f"),
        ("Composite", "RdYlGn", ".2f")]):
    pivot = df.pivot_table(index="K", columns="Lookback", values=metric)
    sns.heatmap(pivot, annot=True, fmt=fmt, cmap=cmap, ax=ax, linewidths=0.3, cbar=True)
    ax.set_title(f"{metric} (Trend-Filtered)", fontweight="bold")
    ax.set_xlabel("Lookback (months, skip 1)")
fig.suptitle("Trend-Filtered Grid Search: S&P 500 Universe", fontsize=16, fontweight="bold", y=1.00)
fig.tight_layout()
fig.savefig(f"{OUT}/01_heatmap.png", dpi=140, bbox_inches="tight")
plt.close(fig)

# Top 5 cumulative
best_sharpe = df.sort_values("Sharpe", ascending=False).head(5)
fig, ax = plt.subplots(figsize=(16, 9))
for _, r in best_sharpe.iterrows():
    key = (int(r["Lookback"]), int(r["K"]))
    s = strats[key]
    c = s.index.intersection(spy_rets.index)
    cum = (1+s.loc[c]).cumprod()
    ax.plot(cum.index, cum.values, lw=2.5,
            label=f"LB={key[0]}-1, K={key[1]}: Sharpe={r['Sharpe']:.2f}, CAGR={r['CAGR']:.0%}, MaxDD={r['Max DD']:.0%}")
spy_c = (1+spy_rets).cumprod()
ax.plot(spy_c.index, spy_c.values, lw=2, color="black", ls="--", label="SPY")
ax.set_yscale("log")
ax.set_title("Top 5 Trend-Filtered Strategies", fontsize=14, fontweight="bold")
ax.legend(fontsize=10)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x,_: f"${x:,.0f}"))
fig.tight_layout()
fig.savefig(f"{OUT}/02_top5_cumulative.png", dpi=140)
plt.close(fig)

df.to_csv(f"{OUT}/full_grid.csv", index=False)
print(f"\nSaved to {OUT}/")
print("DONE")
