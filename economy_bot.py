import yfinance as yf
import telegram
import asyncio
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# --- 뉴스 및 일정 추출 함수 ---
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

# --- 메인 리포트 생성 및 전송 함수 ---
async def send_report():
    tz_kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(tz_kst)
    hour = now_kst.hour
    today_str = now_kst.strftime("%m월 %d일")

    # 모든 지표 카테고리 구성
    market_data = {
        "📊 지수/환율": {
            "원/달러": "USDKRW=X", "국내선물": "KMK=F", "나스닥": "^IXIC", "S&P500": "^GSPC"
        },
        "🏦 미 국채 수익률 (%)": {
            "1년물": "^IRX", "2년물": "^ZT=F", "5년물": "^FVX", "10년물": "^TNX", "30년물": "^TYX"
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
                data = yf.Ticker(ticker).history(period="5d")
                data = data.ffill()
                
                if not data.empty and len(data) >= 2:
                    close = data['Close'].iloc[-1]
                    prev = data['Close'].iloc[-2]
                    
                    # 변동 포인트 계산
                    diff = close - prev
                    
                    # 국채 금리 표시 보정 로직
                    display_close = close
                    display_diff = diff
                    if ticker in ["^IRX", "^FVX", "^TNX", "^TYX"]:
                        if close > 10:
                            display_close = close / 10
                            display_diff = diff / 10
                    
                    pct = (diff / prev) * 100
                    mark = "🔸" if diff > 0 else "🔹" if diff < 0 else "▫️"
                    sign = "+" if diff > 0 else ""
                    
                    # 수치 표시 형식 결정
                    if "국채" in category:
                        report += f"{name}: `{display_close:.2f}%` ({mark} {sign}{display_diff:+.2f}, {pct:+.2f}%)"
                    else:
                        report += f"{name}: `{close:,.2f}` ({mark} {sign}{diff:,.2f}, {pct:+.2f}%)"
                    
                    report += "\n"
                else:
                    report += f"{name}: 데이터 대기 중\n"
            except:
                report += f"{name}: 조회 오류\n"
        report += "\n"

    # 시간대별 맞춤 정보
    if hour == 8:
        report += await get_economy_calendar(today_str) + "\n"
    elif hour == 22:
        report += await get_earnings_report() + "\n"
    
    report += "🔗 [인베스팅 경제 캘린더 보기](https://kr.investing.com/economic-calendar/)"

    # 전송
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    if token and chat_id:
        bot = telegram.Bot(token=token)
        await bot.send_message(chat_id=int(chat_id), text=report, parse_mode='Markdown', disable_web_page_preview=True)

if __name__ == "__main__":
    asyncio.run(send_report())
