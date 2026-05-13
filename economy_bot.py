import yfinance as yf
import telegram
import asyncio
import os
import requests
from bs4 import BeautifulSoup

async def get_specific_news(keyword):
    """분야별 최신 뉴스를 1건씩 가져옵니다."""
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

async def send_combined_report():
    # 1. 지표 설정
    symbols = {
        "나스닥": "^IXIC", "S&P500": "^GSPC", "골드": "GC=F", 
        "실버": "SI=F", "구리": "HG=F", "비트코인": "BTC-USD"
    }
    
    # 2. 리포트 본문 작성
    full_report = "📊 [통합 경제 리포트 및 전문 분야 현황]\n\n"
    full_report += "📈 [실시간 시장 지표]\n"
    
    for name, ticker in symbols.items():
        try:
            data = yf.Ticker(ticker).history(period="2d")
            close_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2]
            
            # 등락 포인트 및 등락율 계산
            change_point = close_price - prev_price
            pct_change = (change_point / prev_price) * 100
            
            # 🔴 상승 / 🔵 하락 기호 및 텍스트 설정 (요청 반영)
            if change_point > 0:
                mark = "🔴"
                diff_text = f"+{change_point:,.2f}"
            elif change_point < 0:
                mark = "🔵"
                diff_text = f"{change_point:,.2f}" # 마이너스 기호 포함
            else:
                mark = "⚪"
                diff_text = "0.00"
                
            # 형식: 나스닥: 16,000.00 (🔴 -20.00, -0.71%)
            full_report += f"{name}: {close_price:,.2f} ({mark} {diff_text}, {pct_change:+.2f}%)\n"
        except:
            full_report += f"{name}: 시세 정보 실패\n"

    # 3. 전문 분야 뉴스 수집
    full_report += "\n📰 [분야별 전문 뉴스 요약]\n"
    keywords = ["나스닥 전망", "국제 금시세", "은 시세", "구리 가격", "비트코인 호재"]
    
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
            disable_web_page_preview=True
        )
        print("🚀 포인트/퍼센트 통합 리포트 전송 성공!")

if __name__ == "__main__":
    asyncio.run(send_combined_report())
