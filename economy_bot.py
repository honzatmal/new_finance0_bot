import yfinance as yf
import telegram
import asyncio
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# ... (기존 뉴스/일정 추출 함수들은 동일) ...

async def send_report():
    tz_kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(tz_kst)
    hour = now_kst.hour
    today_str = now_kst.strftime("%m월 %d일")

    # 기본 리포트 구성
    symbols = {"나스닥": "^IXIC", "S&P500": "^GSPC", "골드": "GC=F", "비트코인": "BTC-USD", "원/달러": "USDKRW=X"}
    report = f"📊 *[경제 리포트 - {today_str}]*\n\n"
    report += f"🕒 *한국:* `{now_kst.strftime('%H:%M')}` | *뉴욕:* `{datetime.now(pytz.timezone('America/New_York')).strftime('%H:%M')}`\n\n"
    
    report += "📈 *[시장 지표]*\n"
    for name, ticker in symbols.items():
        try:
            data = yf.Ticker(ticker).history(period="2d")
            close, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
            diff, pct = close - prev, ((close - prev) / prev) * 100
            mark = "🔸" if diff > 0 else "🔹" if diff < 0 else "▫️"
            report += f"{name}: `{close:,.2f}` ({mark} {diff:+,.2f}, {pct:+.2f}%)\n"
        except: report += f"{name}: 조회 실패\n"

    report += "\n"

    # --- 시간대별 맞춤 정보 제공 ---
    if hour == 7:
        # 아침 7시: 오늘 전체 일정 브리핑
        report += await get_economy_calendar(today_str)
        report += "\n☀️ *[모닝 브리핑]* 오늘 하루 주요 지표를 확인하세요.\n"
    
    elif hour in [18, 21]:
        # 저녁 시간: 미장 개장 전 실적/전망 뉴스 집중
        report += await get_earnings_report()
        report += "\n🌙 *[야간 브리핑]* 미국장 개장 준비 및 기업 실적 확인.\n"
    
    else:
        # 그 외 시간 (10시, 12시, 15시): 실시간 캘린더 링크만 깔끔하게 제공
        report += "📅 [인베스팅 경제 캘린더 보기](https://kr.investing.com/economic-calendar/)\n"

    # 전송부
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    if token and chat_id:
        bot = telegram.Bot(token=token)
        await bot.send_message(chat_id=int(chat_id), text=report, parse_mode='Markdown', disable_web_page_preview=True)

if __name__ == "__main__":
    asyncio.run(send_report())
