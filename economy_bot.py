import yfinance as yf
import telegram
import asyncio
import os
import requests
from bs4 import BeautifulSoup

async def get_specific_news(keyword):
    """특정 키워드로 구글 뉴스에서 가장 최신 뉴스 1건을 가져옵니다."""
    url = f"https://news.google.com/search?q={keyword}&hl=ko&gl=KR&ceid=KR%3Ako"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        article = soup.select_one('article')
        if article:
            title = article.select_one('a.J77Cte').text
            link = "https://news.google.com" + article.select_one('a')['href'][1:]
            return f"• [{keyword}] {title}\n  (링크: {link})"
    except:
        return f"• [{keyword}] 뉴스 정보를 가져오지 못했습니다."
    return None

async def send_specialized_report():
    # 지표 설정 (나스닥, 골드, 실버, 구리, 비트코인)
    symbols = {
        "나스닥": "^IXIC", "골드": "GC=F", "실버": "SI=F", 
        "구리": "HG=F", "비트코인": "BTC-USD"
    }
    
    # 1. 시세 리포트 작성
    report = "📊 [전문 분야 시장 현황]\n\n"
    for name, ticker in symbols.items():
        try:
            data = yf.Ticker(ticker).history(period="2d")
            close_price = data['Close'].iloc[-1]
            pct_change = ((close_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
            emoji = "🔺" if pct_change > 0 else "🔻"
            report += f"{name}: {close_price:,.2f} ({emoji}{pct_change:.2f}%)\n"
        except:
            report += f"{name}: 시세 정보 조회 실패\n"

    # 2. 분야별 전문 뉴스 수집
    report += "\n📰 [분야별 전문 뉴스 요약]\n"
    keywords = ["나스닥 전망", "국제 금시세", "은 시세", "구리 가격", "비트코인 뉴스"]
    
    for kw in keywords:
        news_item = await get_specific_news(kw)
        if news_item:
            report += news_item + "\n\n"

    # 3. 텔레그램 전송
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')

    if token and chat_id:
        bot = telegram.Bot(token=token)
        await bot.send_message(
            chat_id=int(chat_id), 
            text=report, 
            disable_web_page_preview=True
        )
        print("🚀 전문 리포트 전송 완료!")

if __name__ == "__main__":
    asyncio.run(send_specialized_report())
