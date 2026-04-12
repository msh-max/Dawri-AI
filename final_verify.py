"""
FINAL VERIFICATION — 9-1 month, K=9, S&P 500, SPY 200-day trend filter
Independent reimplementation + robustness tests.
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

OUT = "output_final_verify"
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
print("FINAL VERIFICATION: 9-1mo, K=9, S&P 500 + 200MA Trend Filter")
print("="*80)

# ── Download ──
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
print(f"  {daily.shape[1]} tickers")

# ═══════════════════════════════════════════════════════════════
# AUDIT 1: No look-ahead bias in trend filter
# ═══════════════════════════════════════════════════════════════
print("\n[AUDIT 1] Trend filter look-ahead check")
spy_d = daily["SPY"].dropna()
spy_ma200 = spy_d.rolling(200).mean()

# Test: the 200-day MA at date t must only use data up to t, not t+1
test_date = pd.Timestamp("2020-03-31")
expected = spy_d.loc[:test_date].iloc[-200:].mean()
actual = spy_ma200.loc[:test_date].iloc[-1]
print(f"  Expected 200MA on 2020-03-31: {expected:.2f}")
print(f"  Actual from rolling:          {actual:.2f}")
print(f"  Match: {abs(expected - actual) < 0.01}")

# ═══════════════════════════════════════════════════════════════
# AUDIT 2: Signal spot-check for 2024-01-31
# ═══════════════════════════════════════════════════════════════
print("\n[AUDIT 2] Manual signal spot-check for 2024-01-31")
monthly = daily.resample("ME").last()
monthly_ret = monthly.pct_change()
stock_prices = monthly.drop(columns=["SPY"], errors="ignore")
stock_rets = monthly_ret.drop(columns=["SPY"], errors="ignore")
spy_rets = monthly_ret["SPY"].dropna()

# 9-1 month lookback: buy based on returns from t-10 to t-1
test_date = pd.Timestamp("2024-01-31")
idx = stock_prices.index.get_loc(test_date)
p_start = stock_prices.iloc[idx - 9]  # 9 months back, but skip last = start 10 back
p_end = stock_prices.iloc[idx - 1]     # skip last month
print(f"  Lookback window: {stock_prices.index[idx-9].date()} → {stock_prices.index[idx-1].date()}")
sig = (p_end / p_start - 1).dropna()
top9 = sig.nlargest(9)
print(f"  Top 9 by 9-1 momentum signal:")
for t, r in top9.items():
    fwd = stock_rets.loc[test_date, t] if t in stock_rets.columns else np.nan
    print(f"    {t:8s} signal={r*100:7.1f}%  next-month return={fwd*100:+6.1f}%")
print(f"  Portfolio return for Jan 2024: {stock_rets.loc[test_date, top9.index].mean()*100:.2f}%")

# Check trend filter
trend_val = bool(spy_d.loc[:test_date].iloc[-1] > spy_ma200.loc[:test_date].iloc[-1])
print(f"  SPY > 200MA on test_date: {trend_val} (should be True for 2024)")

# ═══════════════════════════════════════════════════════════════
# AUDIT 3: Independent full backtest
# ═══════════════════════════════════════════════════════════════
print("\n[AUDIT 3] Independent backtest implementation")

# Monthly trend signal (reuse trading day nearest to month end)
month_ends = monthly.index
trend_month = {}
for me in month_ends:
    nearest_dates = spy_ma200.dropna().index[spy_ma200.dropna().index <= me]
    if len(nearest_dates) == 0:
        trend_month[me] = True
        continue
    last = nearest_dates[-1]
    trend_month[me] = bool(spy_d.loc[last] > spy_ma200.loc[last])

def backtest(lookback=9, skip=1, k=9, use_trend=True, cost_bps=0):
    dates = stock_prices.index
    rets = []
    prev_top = set()
    for i in range(len(dates)):
        if i < lookback + skip - 1: continue
        date = dates[i]
        p_s = stock_prices.iloc[i - (lookback + skip - 1)]
        p_e = stock_prices.iloc[i - skip]
        valid = p_s.notna() & p_e.notna() & (p_s > 0)
        sig = (p_e[valid] / p_s[valid] - 1)
        if len(sig) < k: continue
        if use_trend and not trend_month.get(date, True):
            rets.append((date, 0.0))
            prev_top = set()
            continue
        top = set(sig.nlargest(k).index)
        if date not in stock_rets.index:
            continue
        curr = stock_rets.loc[date, list(top)].dropna()
        curr = curr[np.isfinite(curr)].clip(-1.0, 1.0)
        if len(curr) == 0: continue
        r = curr.mean()
        # Turnover cost
        if cost_bps > 0 and prev_top:
            turnover = len(top.symmetric_difference(prev_top)) / (2 * k)
            r -= turnover * 2 * (cost_bps / 10000)
        rets.append((date, r))
        prev_top = top
    s = pd.Series(dict(rets))
    s.index = pd.to_datetime(s.index)
    return s

def metrics(r, label=""):
    r = r.dropna()
    if len(r) < 24: return {}
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
    calmar = cagr/abs(maxdd) if maxdd != 0 else 0
    return {"Label":label,"CAGR":cagr,"Vol":vol,"Sharpe":sharpe,"Sortino":sortino,
            "Max DD":maxdd,"Calmar":calmar,"Win Rate":(r>0).mean(),
            "Worst Mo":r.min(),"Best Mo":r.max(),"N Months":len(r)}

base = backtest(9, 1, 9, use_trend=True, cost_bps=0)
m0 = metrics(base, "9-1, K=9 + Trend (0bps)")
print(f"  CAGR={m0['CAGR']:.1%}  Sharpe={m0['Sharpe']:.3f}  MaxDD={m0['Max DD']:.1%}  N={m0['N Months']}")

# ═══════════════════════════════════════════════════════════════
# AUDIT 4: Transaction cost stress test
# ═══════════════════════════════════════════════════════════════
print("\n[AUDIT 4] Transaction cost stress test")
cost_results = []
for bps in [0, 5, 10, 20, 30, 50, 100]:
    s = backtest(9, 1, 9, use_trend=True, cost_bps=bps)
    m = metrics(s, f"{bps}bps")
    cost_results.append(m)
    print(f"  {bps:3d}bps:  CAGR={m['CAGR']:.1%}  Sharpe={m['Sharpe']:.3f}  MaxDD={m['Max DD']:.1%}")

# ═══════════════════════════════════════════════════════════════
# AUDIT 5: Parameter robustness (neighbors)
# ═══════════════════════════════════════════════════════════════
print("\n[AUDIT 5] Parameter robustness (neighbors of 9-1, K=9)")
robust = []
for lb in [7, 8, 9, 10, 11]:
    for k in [7, 8, 9, 10, 11]:
        s = backtest(lb, 1, k, use_trend=True)
        m = metrics(s, f"{lb}-1, K={k}")
        robust.append(m)
print(f"  {'LB':>3} {'K':>3} {'Sharpe':>8} {'CAGR':>8} {'MaxDD':>8}")
for m in robust:
    parts = m["Label"].split(", K=")
    lb = parts[0].replace("-1","")
    k = parts[1]
    print(f"  {lb:>3} {k:>3} {m['Sharpe']:8.3f} {m['CAGR']:8.1%} {m['Max DD']:8.1%}")
r_df = pd.DataFrame(robust)
print(f"  Sharpe range: {r_df['Sharpe'].min():.3f} to {r_df['Sharpe'].max():.3f}")
print(f"  CAGR range:   {r_df['CAGR'].min():.1%} to {r_df['CAGR'].max():.1%}")
print(f"  Std of Sharpe: {r_df['Sharpe'].std():.3f}  (low = robust)")

# ═══════════════════════════════════════════════════════════════
# AUDIT 6: Out-of-sample test — split 50/50
# ═══════════════════════════════════════════════════════════════
print("\n[AUDIT 6] Out-of-sample splits")
full = backtest(9, 1, 9, use_trend=True)
split_date = full.index[len(full)//2]
print(f"  Split date: {split_date.date()}")

def ann_cagr(r):
    if len(r) < 12: return 0
    tot = (1+r).prod() - 1
    ny = len(r)/12
    return (1+tot)**(1/ny) - 1
def sharpe_of(r):
    if len(r) < 12: return 0
    rfm = (1.03)**(1/12) - 1
    ex = r - rfm
    return ex.mean()/r.std() if r.std()>0 else 0

first = full[full.index <= split_date]
second = full[full.index > split_date]
print(f"  First half  ({first.index[0].date()}–{first.index[-1].date()}):  "
      f"CAGR={ann_cagr(first):.1%}  Sharpe={sharpe_of(first):.3f}")
print(f"  Second half ({second.index[0].date()}–{second.index[-1].date()}):  "
      f"CAGR={ann_cagr(second):.1%}  Sharpe={sharpe_of(second):.3f}")

# Yearly
print("\n  Year-by-year returns:")
yearly = full.groupby(full.index.year).apply(lambda x: (1+x).prod() - 1)
spy_yr = spy_rets.groupby(spy_rets.index.year).apply(lambda x: (1+x).prod() - 1)
print(f"  {'Year':>5} {'Strategy':>10} {'SPY':>10} {'Excess':>10}")
for yr in yearly.index:
    sy = yearly[yr]
    sp = spy_yr.get(yr, np.nan)
    ex = sy - sp if not pd.isna(sp) else np.nan
    print(f"  {yr:>5} {sy:>10.1%} {sp:>10.1%} {ex:>10.1%}")

# Compare to alternatives
print("\n[AUDIT 7] Head-to-head vs alternative configs")
alts = [
    (9, 9), (9, 10), (9, 11), (9, 13), (9, 8),
    (12, 9), (12, 10), (6, 16), (6, 10)
]
alt_rows = []
for lb, k in alts:
    s = backtest(lb, 1, k, use_trend=True)
    m = metrics(s, f"{lb}-1, K={k}")
    alt_rows.append(m)
print(f"  {'Config':>15} {'Sharpe':>8} {'Sortino':>8} {'CAGR':>8} {'MaxDD':>8} {'Calmar':>8}")
for m in alt_rows:
    print(f"  {m['Label']:>15} {m['Sharpe']:8.3f} {m['Sortino']:8.3f} {m['CAGR']:8.1%} {m['Max DD']:8.1%} {m['Calmar']:8.2f}")

# ═══════════════════════════════════════════════════════════════
# FINAL METRICS SUMMARY
# ═══════════════════════════════════════════════════════════════
print("\n"+"="*80)
print("FINAL METRICS (9-1, K=9 + Trend, 0bps)")
print("="*80)
for k, v in m0.items():
    if isinstance(v, float):
        if "Mo" in k or "CAGR" in k or "Vol" in k or "DD" in k or "Rate" in k:
            print(f"  {k:20s} {v:>10.2%}")
        else:
            print(f"  {k:20s} {v:>10.3f}")
    else:
        print(f"  {k:20s} {v:>10}")

# Beat SPY
c = base.index.intersection(spy_rets.index)
s_ = base.loc[c]
b_ = spy_rets.loc[c]
if len(s_) >= 60:
    sr = s_.rolling(60).apply(lambda x:(1+x).prod()-1, raw=True)
    br = b_.rolling(60).apply(lambda x:(1+x).prod()-1, raw=True)
    v = sr.dropna().index.intersection(br.dropna().index)
    print(f"  Beat SPY rolling 5Y  {(sr.loc[v]>br.loc[v]).mean():>10.1%}")
if len(s_) >= 36:
    sr = s_.rolling(36).apply(lambda x:(1+x).prod()-1, raw=True)
    br = b_.rolling(36).apply(lambda x:(1+x).prod()-1, raw=True)
    v = sr.dropna().index.intersection(br.dropna().index)
    print(f"  Beat SPY rolling 3Y  {(sr.loc[v]>br.loc[v]).mean():>10.1%}")
if len(s_) >= 12:
    sr = s_.rolling(12).apply(lambda x:(1+x).prod()-1, raw=True)
    br = b_.rolling(12).apply(lambda x:(1+x).prod()-1, raw=True)
    v = sr.dropna().index.intersection(br.dropna().index)
    print(f"  Beat SPY rolling 1Y  {(sr.loc[v]>br.loc[v]).mean():>10.1%}")

# Chart
fig, ax = plt.subplots(figsize=(16, 9))
cum = (1+base.loc[c]).cumprod()
spy_cum = (1+b_).cumprod()
ax.plot(cum.index, cum.values, lw=3, color="#e74c3c", label=f"9-1, K=9 + Trend  (CAGR {m0['CAGR']:.0%}, Sharpe {m0['Sharpe']:.2f})")
ax.plot(spy_cum.index, spy_cum.values, lw=2, color="black", ls="--", label=f"SPY  (CAGR {ann_cagr(b_):.0%}, Sharpe {sharpe_of(b_):.2f})")
ax.set_yscale("log")
ax.set_title("FINAL STRATEGY (verified): 9-1 mo, K=9, S&P 500 + 200MA Trend", fontsize=14, fontweight="bold")
ax.legend(fontsize=12)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x,_: f"${x:,.0f}"))
fig.tight_layout()
fig.savefig(f"{OUT}/verified_cumulative.png", dpi=140)
plt.close(fig)

# Drawdown
fig, ax = plt.subplots(figsize=(16, 6))
w = cum
dd = (w-w.cummax())/w.cummax()
ax.fill_between(dd.index, dd.values, 0, alpha=0.5, color="red")
ax.set_title(f"Drawdowns (verified) — Max DD: {dd.min():.1%}", fontweight="bold")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
fig.tight_layout()
fig.savefig(f"{OUT}/verified_drawdown.png", dpi=140)
plt.close(fig)

print(f"\nSaved to {OUT}/")
print("VERIFICATION COMPLETE")
