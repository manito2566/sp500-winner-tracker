from __future__ import annotations
import pandas as pd

TRADING_WINDOWS = {"1M": 21, "3M": 63, "6M": 126, "12M": 252}

def normalize_ticker(value: str) -> str:
    """Convert TradingView symbols such as NASDAQ:NVDA to Yahoo symbols."""
    ticker = str(value).strip().upper()
    if ":" in ticker:
        ticker = ticker.rsplit(":", 1)[-1]
    ticker = ticker.strip().replace("/", "-")
    if ticker in {"BRK.B", "BRK/B"}: ticker = "BRK-B"
    if ticker in {"BF.B", "BF/B"}: ticker = "BF-B"
    return ticker

def period_return(series: pd.Series, sessions: int) -> float:
    clean = series.dropna()
    if len(clean) <= sessions: return float("nan")
    return float(clean.iloc[-1] / clean.iloc[-sessions - 1] - 1)

def rsi(series: pd.Series, length: int = 14) -> float:
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / length, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / length, adjust=False).mean()
    if loss.iloc[-1] == 0: return 100.0
    return float(100 - 100 / (1 + gain.iloc[-1] / loss.iloc[-1]))

def analyze(prices: pd.DataFrame, ticker: str, benchmark: str = "SPY") -> dict | None:
    stock = prices[ticker].dropna(); bench = prices[benchmark].reindex(stock.index).ffill().dropna()
    stock, bench = stock.align(bench, join="inner")
    if len(stock) < 210: return None
    ema = {n: float(stock.ewm(span=n, adjust=False).mean().iloc[-1]) for n in (20, 50, 100, 200)}
    bench_ema200 = float(bench.ewm(span=200, adjust=False).mean().iloc[-1])
    relative = stock / bench
    relative_ema50 = float(relative.ewm(span=50, adjust=False).mean().iloc[-1])
    rs = {label: period_return(stock, days) - period_return(bench, days) for label, days in TRADING_WINDOWS.items()}
    current_rsi = rsi(stock); drawdown = float(stock.iloc[-1] / stock.cummax().iloc[-1] - 1)
    market = "Risk-on" if bench.iloc[-1] >= bench_ema200 else "Risk-off"
    score = (10 if rs["1M"] > 0 else 0) + (20 if rs["3M"] > 0 else 0) + (15 if rs["6M"] > 0 else 0)
    score += (15 if stock.iloc[-1] > ema[50] else 0) + (15 if ema[20] > ema[50] > ema[100] > ema[200] else 0)
    score += (15 if relative.iloc[-1] > relative_ema50 else 0) + (10 if 35 <= current_rsi <= 70 else 0)
    if market == "Risk-off": score = max(0, score - 10)
    reasons, risks = [], []
    (reasons if rs["3M"] > 0 else risks).append("ชนะ Benchmark 3 เดือน" if rs["3M"] > 0 else "แพ้ Benchmark 3 เดือน")
    (reasons if ema[20] > ema[50] > ema[100] > ema[200] else risks).append("EMA เรียงตัวขาขึ้น" if ema[20] > ema[50] > ema[100] > ema[200] else "EMA ยังไม่เรียงตัวขาขึ้น")
    if stock.iloc[-1] < ema[50]: risks.append("ราคาต่ำกว่า EMA50")
    if drawdown <= -0.15: risks.append("Drawdown มากกว่า 15%")
    if current_rsi > 70: risks.append("RSI ร้อนแรงเกินไป")
    if market == "Risk-off": risks.append("Benchmark ต่ำกว่า EMA200")
    if score >= 75 and rs["3M"] > 0: status, action = "Leader", "ติดตามต่อ/รอจังหวะตามแผน"
    elif score >= 55: status, action = "Watch", "เฝ้าดู Relative Strength และ EMA50"
    elif drawdown <= -0.15 or stock.iloc[-1] < ema[100]: status, action = "Review/Exit", "ทบทวนสมมติฐานและขนาดสถานะ"
    else: status, action = "Warning", "งดเพิ่มสถานะจนกว่าจะฟื้น"
    return {"Ticker": ticker, "Status": status, "Action": action, "Score": score, "Price": float(stock.iloc[-1]),
            "RSI": current_rsi, "Drawdown": drawdown, "EMA20": ema[20], "EMA50": ema[50], "EMA100": ema[100], "EMA200": ema[200],
            "RS 1M": rs["1M"], "RS 3M": rs["3M"], "RS 6M": rs["6M"], "RS 12M": rs["12M"], "Market": market,
            "Reasons": " • ".join(reasons) or "ยังไม่มีปัจจัยสนับสนุน", "Risks": " • ".join(risks) or "ไม่พบสัญญาณเสี่ยงตามกฎ", "Updated": stock.index[-1].date()}

