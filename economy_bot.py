import yfinance as yf
import telegram
import asyncio
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

async def get_specific_news(keyword):
    """분야별 최신 뉴스를 가져옵니다."""
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
    except:
        return None
    return None

async def get_economy_calendar():
    """오늘의 주요 경제 일정을 날짜 기반으로 더 정확하게 검색합니다."""
    # 오늘 날짜 (KST 기준) 반영
    tz_kst = pytz.timezone('Asia/Seoul')
    today_str = datetime.now(tz_kst).strftime("%m월 %d일")
    url = f"https://news.google.com/search?q={today_str}+주요+경제일정+발표&hl=ko&gl=KR&ceid=KR%3Ako"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    calendar_header = "📅 *[오늘의 주요 경제 일정]*\n"
    investing_link = "🔗 [실시간 인베스팅 캘린더 보기](https://kr.investing.com/economic-calendar/)\n"
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.select('article')[:3] # 상위 3개 뉴스 추출
        
        if articles:
            news_list = ""
            for article in articles:
                title = article.select_one('a.J77Cte').text
                news_list += f"• {title}\n"
            return calendar_header + news_list + investing_link
    except:
        pass
    
    return calendar_header + "• 주요 발표 일정은 아래 링크에서 확인하세요.\n" + investing_link

async def send_combined_report():
    # 1. 지표 설정
    symbols = {
        "나스닥": "^IXIC", "S&P500": "^GSPC", "골드": "GC=F", 
        "실버": "SI=F", "구리": "HG=F", "비트코인": "BTC-USD",
        "원/달러": "USDKRW=X"
    }
    
    # 2. 시간 설정 (KST 및 뉴욕 시간)
    tz_kst = pytz.timezone('Asia/Seoul')
    tz_ny = pytz.timezone('America/New_York')
    now_kst = datetime.now(tz_kst)
    now_ny = datetime.now(tz_ny)
    
    time_kst_str = now_kst.strftime("%Y-%m-%d %H:%M")
    time_ny_str = now_ny.strftime("%Y-%m-%d %H:%M")
    
    # 3. 리포트 본문 구성
    full_report = f"📊 *[통합 경제 리포트]*\n\n"
    
    # [시간 정보] 최상단 배치
    full_report += f"🕒 *[시간 정보]*\n"
    full_report += f"🇰🇷 한국: `{time_kst_str}`\n"
    full_report += f"🇺🇸 뉴욕: `{time_ny_str}`\n\n"
    
    # [실시간 시장 지표] 
    full_report += "📈 *[실시간 시장 지표]*\n"
    for name, ticker in symbols.items():
        try:
            data = yf.Ticker(ticker).history(period="2d")
            close_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2]
            
            change_point = close_price - prev_price
            pct_change = (change_point / prev_price) * 100
            
            # 작은 유색 기호 적용
            if change_point > 0:
                mark, sign = "🔸", "+"
            elif change_point < 0:
                mark, sign = "🔹", ""
            else:
                mark, sign = "▫️", ""
                
            full_report += f"{name}: `{close_price:,.2f}` ({mark} {sign}{change_point:,.2f}, {pct_change:+.2f}%)\n"
        except:
            full_report += f"{name}: 업데이트 대기 중\n"

    # [경제 일정]
    full_report += "\n" + await get_economy_calendar()
    
    # [분야별 뉴스]
    full_report += "\n📰 *[분야별 전문 뉴스 요약]*\n"
    keywords = ["나스닥 전망", "국제 금시세", "구리 가격", "비트코인 호재"]
    for kw in keywords:
        news_item = await get_specific_news(kw)
        if news_item:
            full_report += news_item + "\n\n"

    # 4. 텔레그램 전송
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')

    if token and chat_id:
        bot = telegram.Bot(token=token)
        await bot.send_message(
            chat_id=int(chat_id), 
            text=full_report, 
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

if __name__ == "__main__":
    asyncio.run(send_combined_report())
