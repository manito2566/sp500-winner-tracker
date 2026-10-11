import io
import pandas as pd
import streamlit as st
import yfinance as yf
from tracker import analyze, normalize_ticker

st.set_page_config(page_title="S&P 500 Winner Tracker", layout="wide")

@st.cache_data(ttl=900, show_spinner=False)
def load_prices(tickers, benchmark, period):
    symbols = list(dict.fromkeys([x.upper().strip() for x in tickers] + [benchmark]))
    raw = yf.download(symbols, period=period, auto_adjust=True, progress=False)
    if raw.empty: return pd.DataFrame()
    close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    return close.dropna(how="all")

st.title("S&P 500 Winner Tracker")
st.caption("ติดตามความแข็งแรงเทียบตลาด พร้อมเหตุผลและความเสี่ยง — ไม่ใช่คำแนะนำซื้อขาย")
with st.sidebar:
    st.header("ข้อมูลและเกณฑ์")
    upload = st.file_uploader("อัปโหลด watchlist CSV", type="csv")
    default = pd.read_csv(io.StringIO("Ticker\nNVDA\nMU\n"))
    watch = pd.read_csv(upload) if upload else default
    if "Ticker" not in watch.columns:
        st.error("CSV ต้องมีคอลัมน์ Ticker"); st.stop()
    tickers = st.text_area("Ticker คั่นด้วย comma", ",".join(watch["Ticker"].dropna().astype(str)))
    benchmark = normalize_ticker(st.text_input("Benchmark", "SPY"))
    period = st.selectbox("ช่วงข้อมูล", ["2y", "5y", "10y"], index=0)

raw_symbols = [x for x in tickers.replace("\n", ",").split(",") if x.strip()]
symbols = list(dict.fromkeys(normalize_ticker(x) for x in raw_symbols if normalize_ticker(x)))
if not symbols:
    st.info("กรุณาใส่ Ticker อย่างน้อยหนึ่งตัว"); st.stop()
converted = [f"{raw.strip()} → {normalize_ticker(raw)}" for raw in raw_symbols if raw.strip().upper() != normalize_ticker(raw)]
if converted:
    st.sidebar.caption("แปลงรูปแบบ TradingView อัตโนมัติ: " + ", ".join(converted[:8]) + (" …" if len(converted) > 8 else ""))
with st.spinner("กำลังประมวลผลข้อมูลตลาด..."):
    prices = load_prices(symbols, benchmark, period)
if prices.empty or benchmark not in prices.columns:
    st.error("โหลด Benchmark ไม่สำเร็จ กรุณาตรวจ Ticker หรืออินเทอร์เน็ต"); st.stop()

rows = [analyze(prices, ticker, benchmark) for ticker in symbols if ticker in prices.columns]
df = pd.DataFrame(row for row in rows if row)
input_order = {ticker: index for index, ticker in enumerate(symbols)}
missing = sorted(set(symbols) - set(df.get("Ticker", [])))
if df.empty:
    st.error("ข้อมูลย้อนหลังไม่เพียงพอสำหรับวิเคราะห์ EMA200"); st.stop()
if missing: st.warning("ข้าม Ticker ที่ไม่พบหรือข้อมูลไม่พอ: " + ", ".join(missing))

c1,c2,c3,c4 = st.columns(4)
c1.metric("หุ้นที่วิเคราะห์", len(df)); c2.metric("Leader", int((df.Status=="Leader").sum()))
c3.metric("ต้องทบทวน", int(df.Status.isin(["Warning","Review/Exit"]).sum())); c4.metric("Market Regime", df.Market.mode().iloc[0])
all_status = ["Leader","Watch","Warning","Review/Exit"]
filter_col, sort_col, direction_col = st.columns([2, 1.5, 1])
with filter_col:
    selected = st.multiselect("กรองสถานะ", all_status, default=all_status)
sort_options = {
    "ลำดับที่กรอก": "Input order", "คะแนน": "Score", "ราคา": "Price",
    "RS 1 เดือน": "RS 1M", "RS 3 เดือน": "RS 3M", "RS 6 เดือน": "RS 6M",
    "RS 12 เดือน": "RS 12M", "RSI": "RSI", "Drawdown": "Drawdown", "สถานะ": "Status"
}
with sort_col:
    sort_label = st.selectbox("จัดเรียงตาม", list(sort_options), index=1)
with direction_col:
    direction = st.selectbox("ทิศทาง", ["มาก → น้อย", "น้อย → มาก"], index=0)
view = df[df.Status.isin(selected)].copy()
view["Input order"] = view["Ticker"].map(input_order)
status_rank = {"Leader": 4, "Watch": 3, "Warning": 2, "Review/Exit": 1}
view["Status rank"] = view["Status"].map(status_rank)
sort_key = "Status rank" if sort_options[sort_label] == "Status" else sort_options[sort_label]
ascending = direction == "น้อย → มาก"
if sort_key == "Input order": ascending = True
view = view.sort_values([sort_key, "Ticker"], ascending=[ascending, True], kind="stable")
view.insert(0, "อันดับ", range(1, len(view) + 1))
st.subheader("สถานะและเหตุผล")
cols = ["อันดับ","Ticker","Status","Action","Score","Price","RS 1M","RS 3M","RS 6M","RS 12M","RSI","Drawdown","Market","Reasons","Risks","Updated"]
fmt = {"Price":"{:.2f}","RS 1M":"{:.1%}","RS 3M":"{:.1%}","RS 6M":"{:.1%}","RS 12M":"{:.1%}","RSI":"{:.1f}","Drawdown":"{:.1%}"}
st.dataframe(view[cols].style.format(fmt), use_container_width=True, height=430)
left,right = st.columns(2)
with left:
    st.subheader("Relative Strength"); st.bar_chart(view.set_index("Ticker")[["RS 1M","RS 3M","RS 6M"]])
with right:
    st.subheader("คะแนนระบบ"); st.bar_chart(view.set_index("Ticker")["Score"])
st.download_button("ดาวน์โหลดรายงาน CSV", df.to_csv(index=False).encode("utf-8-sig"), "tracker_report.csv", "text/csv")
with st.expander("หลักการจัดสถานะ"):
    st.markdown("คะแนนมาจาก Relative Strength 1/3/6 เดือน, ราคาเทียบ EMA50, การเรียงตัว EMA, แนวโน้ม Relative Strength และ RSI โดยลดคะแนนเมื่อ Benchmark ต่ำกว่า EMA200")
