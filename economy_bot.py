import yfinance as yf
import telegram
import asyncio
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# 1. 특정 키워드 뉴스 수집 함수
async def get_specific_news(keyword):
    url = f"https://news.google.com/search?q={keyword}&hl=ko&gl=KR&ceid=KR%3Ako"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        article = soup.select_one('article')
        if article:
            title = article.select_one('a.J77Cte').text
            link = "https://news.google.com" + article.select_one('a')['href'][1:]
            return f"• [{keyword}] {title}\n  └ {link}"
    except: return None
    return None

# 2. 경제 지표 일정 수집 함수 (에러 원인 해결)
async def get_economy_calendar(today_str):
    url = f"https://news.google.com/search?q={today_str}+주요+경제일정+발표&hl=ko&gl=KR&ceid=KR%3Ako"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.select('article')[:3]
        if articles:
            news_list = "".join([f"• {a.select_one('a.J77Cte').text}\n" for a in articles])
            return "📅 *[오늘의 주요 경제 일정]*\n" + news_list
    except: pass
    return "📅 *[오늘의 경제 일정]*\n• [인베스팅 캘린더](https://kr.investing.com/economic-calendar/)에서 상세 일정을 확인하세요.\n"

# 3. 기업 실적 발표 수집 함수
async def get_earnings_report():
    url = "https://news.google.com/search?q=미국증시+오늘+실적발표+기업&hl=ko&gl=KR&ceid=KR%3Ako"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.select('article')[:3]
        if articles:
            return "💰 *[주요 기업 실적 발표]*\n" + "".join([f"• {a.select_one('a.J77Cte').text}\n" for a in articles])
    except: pass
    return "💰 *[실적 알림]* 현재 주요 기업 실적 뉴스가 없습니다.\n"

# 4. 메인 리포트 생성 및 전송 함수
async def send_report():
    tz_kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(tz_kst)
    hour = now_kst.hour
    today_str = now_kst.strftime("%m월 %d일")

    # 시장 지표 수집
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

    # 시간대별 맞춤 정보
    if hour == 8:
        report += "\n☀️ *[장 시작 전 체크]*\n" + await get_economy_calendar(today_str)
    elif hour == 22:
        report += "\n🌙 *[미장 개장 준비]*\n" + await get_earnings_report()
    
    report += "\n🔗 [인베스팅 경제 캘린더 보기](https://kr.investing.com/economic-calendar/)"

    # 전송
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    if token and chat_id:
        bot = telegram.Bot(token=token)
        await bot.send_message(chat_id=int(chat_id), text=report, parse_mode='Markdown', disable_web_page_preview=True)

if __name__ == "__main__":
    asyncio.run(send_report())
