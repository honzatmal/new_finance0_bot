import yfinance as yf
import telegram
import asyncio
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# ... (기존 get_economy_calendar, get_earnings_report 함수 유지) ...

async def send_report():
    tz_kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(tz_kst)
    hour = now_kst.hour
    today_str = now_kst.strftime("%m월 %d일")

    # 1. 기본 시장 지표 수집
    symbols = {"나스닥": "^IXIC", "S&P500": "^GSPC", "비트코인": "BTC-USD", "원/달러": "USDKRW=X", "국제금": "GC=F"}
    
    report = f"🔔 *[{hour}시 정각 리포트]*\n"
    report += f"🇰🇷 KST: `{now_kst.strftime('%H:%M')}` | 🇺🇸 NY: `{datetime.now(pytz.timezone('America/New_York')).strftime('%H:%M')}`\n\n"
    
    report += "📈 *현재 시장 지표*\n"
    for name, ticker in symbols.items():
        try:
            data = yf.Ticker(ticker).history(period="2d")
            close, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
            diff, pct = close - prev, ((close - prev) / prev) * 100
            mark = "🔸" if diff > 0 else "🔹" if diff < 0 else "▫️"
            report += f"{name}: `{close:,.2f}` ({mark} {pct:+.2f}%)\n"
        except: report += f"{name}: 데이터 오류\n"

    # 2. 시간대별 특화 정보 (도배 방지용 로직)
    if hour == 8:
        report += "\n☀️ *[장 시작 전 체크]*\n" + await get_economy_calendar(today_str)
    elif hour == 22:
        report += "\n🌙 *[미장 개장 준비]*\n" + await get_earnings_report()
    elif hour in [12, 18]:
        report += "\n📰 *[중간 뉴스 요약]*\n"
        news = await get_specific_news("증시 시황")
        if news: report += news
    
    report += "\n🔗 [실시간 경제 캘린더 보기](https://kr.investing.com/economic-calendar/)"

    # 3. 전송
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    if token and chat_id:
        bot = telegram.Bot(token=token)
        await bot.send_message(chat_id=int(chat_id), text=report, parse_mode='Markdown', disable_web_page_preview=True)

if __name__ == "__main__":
    asyncio.run(send_report())
