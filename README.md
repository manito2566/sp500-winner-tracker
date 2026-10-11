# S&P 500 Winner Tracker

MVP สำหรับติดตามหุ้นที่เคยชนะ S&P 500 โดยคำนวณ Relative Strength หลายช่วงเวลา, EMA, RSI, Drawdown, Market Regime และจัดสถานะ Leader/Watch/Warning/Review พร้อมเหตุผลและความเสี่ยง

แอปที่เผยแพร่แล้ว: https://sp500-winner-tracker.streamlit.app/

## เริ่มใช้งาน

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

หากติดตั้งชุดพร้อมใช้งานจากโฟลเดอร์นี้แล้ว สามารถเปิดด้วย:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

อัปโหลด `watchlist.csv` ของจริงผ่านแถบด้านซ้าย หรือกรอก Ticker โดยคั่นด้วย comma ระบบจะใช้ SPY เป็น Benchmark

## ข้อจำกัด

- ข้อมูลราคาเหมาะสำหรับการวิจัย ไม่ใช่ระบบเรียลไทม์
- ยังไม่มีข่าว ปฏิทินผลประกอบการ TradingView Webhook หรือการส่งคำสั่งซื้อขาย
- ต้องทดสอบเพิ่มเติมก่อนใช้เงินจริง

## ตรวจสอบแกนคำนวณ

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_tracker.py
```

## นำขึ้นเว็บโฮสต์

- Streamlit Community Cloud: เชื่อม GitHub repository และเลือก `app.py` เป็นไฟล์เริ่มต้น
- Render: repository นี้มี `render.yaml` และ `Dockerfile` พร้อมสำหรับสร้าง Web Service
- Docker: `docker build -t winner-tracker .` แล้วรัน `docker run -p 8501:8501 winner-tracker`

ไม่ควรอัปโหลด `.venv`, `.env` หรือ `.streamlit/secrets.toml` ขึ้น repository
