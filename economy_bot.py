import yfinance as yf
import telegram
import asyncio
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

async def get_specific_news(keyword):
    url = f"https://news.google.com/search?q={keyword}&hl=ko&gl=KR&ceid=KR%3Ako"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers)
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
    """오늘의 주요 경제 일정을 간단히 가져옵니다."""
    # 실제 전문 API 대신 뉴스 기반으로 주요 일정을 요약해서 가져오도록 구성
    url = "https://news.google.com/search?q=오늘의+경제일정&hl=ko&gl=KR&ceid=KR%3Ako"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        first_news = soup.select_one('article')
        if first_news:
            return f"📅 [오늘의 경제 일정/전망]\n• {first_news.select_one('a.J77Cte').text}\n"
    except:
        pass
    return "📅 [오늘의 경제 일정] 주요 일정을 뉴스 링크로 확인하세요.\n"

async def send_full_report():
    # 1. 지표 설정 (환율 추가)
    symbols = {
        "나스닥": "^IXIC", "S&P500": "^GSPC", "골드": "GC=F", 
        "실버": "SI=F", "구리": "HG=F", "비트코인": "BTC-USD",
        "원/달러": "USDKRW=X" # 환율 추가
    }
    
    # 현재 시간 (KST)
    now = datetime.now()
    time_str = now.strftime("%Y-%m-%d %H:%M")
    
    # 2. 리포트 본문 작성
    full_report = f"📊 [통합 경제 리포트 - {time_str}]\n\n"
    full_report += "📈 [실시간 시장 지표]\n"
    
    for name, ticker in symbols.items():
        try:
            data = yf.Ticker(ticker).history(period="2d")
            close_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2]
            
            change_point = close_price - prev_price
            pct_change = (change_point / prev_price) * 100
            
            if change_point > 0:
                mark = "🔴"
                diff_text = f"+{change_point:,.2f}"
            elif change_point < 0:
                mark = "🔵"
                diff_text = f"{change_point:,.2f}"
            else:
                mark = "⚪"
                diff_text = "0.00"
                
            full_report += f"{name}: {close_price:,.2f} ({mark} {diff_text}, {pct_change:+.2f}%)\n"
        except:
            full_report += f"{name}: 정보 업데이트 대기 중\n"

    # 3. 경제 일정 추가
    full_report += "\n" + await get_economy_calendar()

    # 4. 전문 뉴스 수집
    full_report += "\n📰 [분야별 전문 뉴스 요약]\n"
    keywords = ["나스닥 전망", "국제 금시세", "구리 가격", "비트코인 호재"]
    for kw in keywords:
        news_item = await get_specific_news(kw)
        if news_item:
            full_report += news_item + "\n\n"

    # 5. 텔레그램 전송
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')

    if token and chat_id:
        bot = telegram.Bot(token=token)
        await bot.send_message(chat_id=int(chat_id), text=full_report, disable_web_page_preview=True)
        print(f"🚀 {time_str} 리포트 전송 완료!")

if __name__ == "__main__":
    asyncio.run(send_full_report())
