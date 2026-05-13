import yfinance as yf
import telegram
import asyncio
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# ... (get_specific_news, get_economy_calendar, get_earnings_report 함수는 동일) ...

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
    return "📅 *[오늘의 경제 일정]*\n• [인베스팅 캘린더](https://kr.investing.com/economic-calendar/) 확인\n"

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

async def send_report():
    tz_kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(tz_kst)
    hour = now_kst.hour
    today_str = now_kst.strftime("%m월 %d일")

    market_data = {
        "📊 지수/환율": {
            "원/달러": "USDKRW=X", "나스닥": "^IXIC", "S&P500": "^GSPC"
        },
        "🪙 암호화폐": {
            "비트코인": "BTC-USD", "이더리움": "ETH-USD"
        },
        "🛢️ 에너지/금속": {
            "WTI유": "CL=F", "국제금": "GC=F", "실버": "SI=F", 
            "구리": "HG=F", "플래티늄": "PL=F", "팔라듐": "PA=F"
        }
    }
    
    report = f"🔔 *[{hour}시 정각 경제 리포트]*\n"
    report += f"🇰🇷 KST: `{now_kst.strftime('%H:%M')}` | 🇺🇸 NY: `{datetime.now(pytz.timezone('America/New_York')).strftime('%H:%M')}`\n\n"
    
    for category, symbols in market_data.items():
        report += f"*{category}*\n"
        for name, ticker in symbols.items():
            try:
                # 데이터를 조금 더 넉넉하게(5일치) 가져와서 마지막 2개 유효값을 사용
                data = yf.Ticker(ticker).history(period="5d")
                # 값이 비어있을 경우(NaN) 앞의 값으로 채움
                data = data.ffill()
                
                if len(data) >= 2:
                    close = data['Close'].iloc[-1]
                    prev = data['Close'].iloc[-2]
                    pct = ((close - prev) / prev) * 100
                    mark = "🔸" if close > prev else "🔹" if close < prev else "▫️"
                    report += f"{name}: `{close:,.2f}` ({mark} {pct:+.2f}%)\n"
                else:
                    report += f"{name}: 데이터 대기 중\n"
            except Exception as e:
                report += f"{name}: 조회 오류\n"
        report += "\n"

    if hour == 8:
        report += await get_economy_calendar(today_str) + "\n"
    elif hour == 22:
        report += await get_earnings_report() + "\n"
    
    report += "🔗 [인베스팅 경제 캘린더 보기](https://kr.investing.com/economic-calendar/)"

    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    if token and chat_id:
        bot = telegram.Bot(token=token)
        await bot.send_message(chat_id=int(chat_id), text=report, parse_mode='Markdown', disable_web_page_preview=True)

if __name__ == "__main__":
    asyncio.run(send_report())
