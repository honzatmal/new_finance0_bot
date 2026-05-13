import yfinance as yf
import telegram
import asyncio
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# --- 뉴스 및 일정 추출 함수 ---
async def get_economy_calendar(today_str):
    """지표 일정 검색"""
    url = f"https://news.google.com/search?q={today_str}+경제지표+발표+시간&hl=ko&gl=KR&ceid=KR%3Ako"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.select('article')[:3]
        if articles:
            return "📅 *[오늘의 주요 지표 일정]*\n" + "".join([f"• {a.select_one('a.J77Cte').text}\n" for a in articles])
    except: pass
    return "📅 *[오늘의 지표 일정]*\n• [인베스팅 캘린더](https://kr.investing.com/economic-calendar/) 확인\n"

async def get_earnings_report():
    """기업 실적 발표(Earnings) 검색"""
    url = "https://news.google.com/search?q=미국증시+오늘+실적발표+기업&hl=ko&gl=KR&ceid=KR%3Ako"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.select('article')[:3]
        if articles:
            return "💰 *[주요 기업 실적 발표]*\n" + "".join([f"• {a.select_one('a.J77Cte').text}\n" for a in articles])
    except: pass
    return "💰 *[실적 알림]* 현재 발표된 주요 기업 실적 뉴스가 없습니다.\n"

async def send_report():
    # 1. 시간 설정
    tz_kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(tz_kst)
    hour = now_kst.hour
    minute = now_kst.minute
    today_str = now_kst.strftime("%m월 %d일")

    # 2. 기본 지표 수집
    symbols = {"나스닥": "^IXIC", "S&P500": "^GSPC", "골드": "GC=F", "실버": "SI=F", "비트코인": "BTC-USD", "원/달러": "USDKRW=X"}
    report = f"📊 *[경제 리포트 - {today_str}]*\n\n"
    report += f"🕒 *한국:* `{now_kst.strftime('%H:%M')}` | *뉴욕:* `{datetime.now(pytz.timezone('America/New_York')).strftime('%H:%M')}`\n\n"
    
    report += "📈 *[시장 지표]*\n"
    for name, ticker in symbols.items():
        try:
            data = yf.Ticker(ticker).history(period="2d")
            close, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
            diff = close - prev
            pct = (diff / prev) * 100
            mark = "🔸" if diff > 0 else "🔹" if diff < 0 else "▫️"
            report += f"{name}: `{close:,.2f}` ({mark} {diff:+,.2f}, {pct:+.2f}%)\n"
        except: report += f"{name}: 조회 실패\n"

    # 3. 시간대별 조건부 내용 추가 (핵심)
    report += "\n"
    if hour == 6: # 오전 06:30 발송 시
        report += await get_economy_calendar(today_str)
        report += "\n☀️ *[오늘의 투자 전략]*\n• 장 시작 전 지표 일정을 반드시 체크하세요.\n"
    
    elif hour == 22: # 오후 22:30 발송 시
        report += await get_earnings_report()
        report += "\n🌙 *[미국장 개장 알림]*\n• 주요 기업 실적과 개장 시황을 확인하세요.\n"
    
    else: # 그 외 시간 발송 시 기본 정보
        report += "🔗 [실시간 경제 캘린더 보기](https://kr.investing.com/economic-calendar/)\n"

    # 4. 텔레그램 전송
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    if token and chat_id:
        bot = telegram.Bot(token=token)
        await bot.send_message(chat_id=int(chat_id), text=report, parse_mode='Markdown', disable_web_page_preview=True)

if __name__ == "__main__":
    asyncio.run(send_report())
