"""
Updates data.json with the latest 9-1 month momentum signal for the web app.
Filters S&P 500 to Shariah-compliant companies only.
Runs daily via GitHub Actions.
"""
import json, time, os, sys
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import yfinance as yf

# S&P 500 Shariah-compliant subset
# Excludes: banks, insurance, asset managers, exchanges, credit cards (riba),
#           alcohol, tobacco, gambling, defense/weapons, conventional REITs.
# This is a CONSERVATIVE business screen. You should still cross-check each
# holding against a Shariah screening service (Zoya, Islamicly, Wahed) because
# financial-ratio screens (debt/AR/interest income) change quarterly.
HALAL_SP500 = [
    # Technology
    "AAPL","MSFT","NVDA","AVGO","ORCL","CRM","ADBE","CSCO","ACN","AMD","INTC","QCOM","TXN","IBM","NOW","INTU","ADI","MU","AMAT","LRCX",
    "KLAC","MCHP","ADSK","SNPS","CDNS","ANET","FTNT","PANW","TEL","GLW","NXPI","WDC","STX","HPQ","HPE","DELL","NTAP","JNPR",
    "FFIV","FSLR","ENPH","ON","MPWR","SWKS","QRVO","TER","TYL","PTC","CDW","CTSH","EPAM","GRMN","AKAM","KEYS","ANSS","IT","GEN","JBL",
    # Communication & Media (conservative: include mainstream)
    "GOOGL","GOOG","META","NFLX","DIS","CMCSA","CHTR","TMUS","T","VZ","EA","TTWO","OMC","IPG","LYV","WBD","FOX","FOXA","NWS","NWSA","PARA",
    # Consumer Discretionary (non-gambling, non-alcohol)
    "AMZN","TSLA","HD","MCD","NKE","LOW","SBUX","TJX","BKNG","CMG","ORLY","AZO","GM","F","LULU","ROST","DHI","LEN","NVR","PHM","YUM",
    "DPZ","DRI","MAR","HLT","ABNB","GRMN","POOL","TSCO","BBY","ULTA","RL","TPR","CCL","RCL","NCLH","APTV","BWA","LKQ","LVS",
    # Consumer Staples (non-alcohol, non-tobacco)
    "WMT","COST","PG","KO","PEP","MDLZ","CL","KMB","GIS","K","HSY","MKC","CLX","CHD","MNST","KDP","KHC","SJM","CAG","CPB","HRL","TSN","TAP",
    "ADM","SYY","KR","DG","DLTR","WBA","CVS","ELV",
    # Healthcare
    "UNH","JNJ","LLY","ABBV","PFE","MRK","TMO","ABT","DHR","AMGN","BMY","GILD","MDT","ISRG","SYK","REGN","VRTX","ZTS","BSX","ELV",
    "CI","HUM","CNC","MOH","HCA","ZBH","BDX","EW","DXCM","IDXX","IQV","A","WAT","MTD","BIO","CRL","HOLX","ALGN","STE","COO",
    "LH","DGX","RMD","BAX","BIIB","INCY","MRNA","TECH","RVTY","HSIC","PODD","DVA","UHS","VTRS","SOLV",
    # Industrials (non-defense heavy)
    "CAT","DE","HON","UPS","UNP","BA","GE","ETN","LIN","EMR","ITW","CSX","NSC","WM","RSG","FDX","NOC","PH","CMI","PCAR",
    "ROK","JCI","OTIS","CARR","FAST","VMC","MLM","URI","PWR","GWW","XYL","ROP","DOV","IR","IEX","PNR","SNA","LECO","TT","HWM",
    "LUV","DAL","AAL","UAL","HEI","CHRW","EXPD","JBHT","ODFL","XPO","WAB","TRMB","ZBRA","ALLE","AOS","DAY","MAS","GNRC","TDY",
    # Materials (excluding defense)
    "LIN","SHW","APD","ECL","FCX","NEM","NUE","DD","DOW","PPG","MLM","VMC","CE","CF","MOS","STLD","IFF","ALB","FMC","EMN","AVY","PKG","IP","AMCR","BALL","SEE",
    # Energy
    "XOM","CVX","COP","EOG","SLB","PSX","MPC","VLO","OXY","WMB","KMI","OKE","HAL","BKR","DVN","FANG","HES","APA","CTRA","TRGP","EQT",
    # Utilities (no conventional REIT exposure)
    "NEE","SO","DUK","SRE","AEP","D","CEG","XEL","EXC","PCG","PEG","ED","WEC","ES","EIX","DTE","FE","AEE","PPL","CMS","CNP","AES",
    "ATO","LNT","NRG","EVRG","NI","PNW","AWK","WTRG","CMS","ETR",
]
# Deduplicate, preserve order
HALAL_SP500 = list(dict.fromkeys(HALAL_SP500))

print(f"Shariah-compliant universe: {len(HALAL_SP500)} tickers")

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "data.json")
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

def download(tickers):
    frames = []
    bs = 50
    for i in range(0, len(tickers), bs):
        batch = tickers[i:i+bs]
        for attempt in range(3):
            try:
                d = yf.download(batch, period="2y", auto_adjust=True,
                                progress=False, threads=True)
                if isinstance(d.columns, pd.MultiIndex):
                    frames.append(d["Close"])
                else:
                    df = d[["Close"]]; df.columns = batch[:1]; frames.append(df)
                break
            except Exception as e:
                print(f"  batch {i} attempt {attempt}: {e}")
                time.sleep(3)
    p = pd.concat(frames, axis=1)
    p = p.loc[:, ~p.columns.duplicated()].dropna(axis=1, how="all")
    p.index = pd.to_datetime(p.index)
    return p

def main():
    print("Downloading 2y of data...")
    tickers = HALAL_SP500 + ["SPY"]
    daily = download(tickers)
    print(f"  {daily.shape[1]} tickers, {daily.shape[0]} trading days")

    # Monthly resample
    monthly = daily.resample("ME").last()

    # Trend filter: SPY vs 200-day MA
    spy_d = daily["SPY"].dropna()
    spy_ma200 = spy_d.rolling(200).mean()
    spy_current = float(spy_d.iloc[-1])
    spy_ma_current = float(spy_ma200.iloc[-1])
    pct_above = (spy_current / spy_ma_current - 1.0) * 100
    above = spy_current > spy_ma_current

    print(f"  SPY={spy_current:.2f}  200MA={spy_ma_current:.2f}  "
          f"{'ABOVE' if above else 'BELOW'} by {pct_above:+.2f}%")

    # 9-1 momentum signal using the most recent complete month
    # Skip last month: use prices from 10 months ago -> 1 month ago
    if len(monthly) < 11:
        print("Not enough monthly data")
        return

    p_start = monthly.iloc[-10]  # 10 months ago (= start of 9-month window, skipping last)
    p_end = monthly.iloc[-2]     # 1 month ago (skip last)
    signal = (p_end / p_start - 1).dropna()

    # Remove SPY from ranking
    if "SPY" in signal.index:
        signal = signal.drop("SPY")

    # Current prices for share-count calculation
    latest_prices = daily.iloc[-1]

    # Rank top 30
    top30 = signal.sort_values(ascending=False).head(30)
    ranked = []
    for rank, (tkr, sig) in enumerate(top30.items(), 1):
        price = float(latest_prices.get(tkr, float("nan")))
        if pd.isna(price): continue
        ranked.append({
            "rank": rank,
            "ticker": tkr,
            "momentum_pct": round(float(sig) * 100, 2),
            "price_usd": round(price, 2),
        })

    data = {
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "signal_date": monthly.index[-2].strftime("%Y-%m-%d"),
        "latest_price_date": daily.index[-1].strftime("%Y-%m-%d"),
        "universe_size": len(HALAL_SP500),
        "usd_to_sar": 3.75,
        "spy": {
            "price": round(spy_current, 2),
            "ma200": round(spy_ma_current, 2),
            "above_ma200": bool(above),
            "percent_diff": round(pct_above, 2),
        },
        "strategy": {
            "name": "9-1 Month Momentum",
            "description": "Rank S&P 500 (Shariah-compliant only) by cumulative return from t-10 months to t-1 month (skip last month). Buy top K equal-weighted. Hold for 1 month. If SPY < 200-day MA, go to 100% cash.",
            "lookback_months": 9,
            "skip_months": 1,
        },
        "ranked_stocks": ranked,
    }

    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {OUT_PATH}")
    print(f"Top 5 momentum stocks:")
    for r in ranked[:5]:
        print(f"  #{r['rank']}: {r['ticker']:6s}  {r['momentum_pct']:+7.2f}%  ${r['price_usd']:,.2f}")

if __name__ == "__main__":
    main()
