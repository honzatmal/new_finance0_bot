import yfinance as yf
import telegram
import asyncio
import os
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup

async def get_news():
    """구글 뉴스에서 주요 경제 뉴스 3건을 가져옵니다."""
    url = "https://news.google.com/search?q=경제%20주요뉴스&hl=ko&gl=KR&ceid=KR%3Ako"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    news_list = []
    articles = soup.select('article')[:3]
    for article in articles:
        title = article.select_one('a.J77Cte').text
        link = "https://news.google.com" + article.select_one('a')['href'][1:]
        news_list.append(f"• {title}\n  (바로가기: {link})")
    return "\n\n".join(news_list)

def create_chart(symbols):
    """주요 지표의 5일 변동성을 차트로 생성합니다."""
    plt.figure(figsize=(10, 6))
    for name, ticker in symbols.items():
        data = yf.Ticker(ticker).history(period="5d")
        if not data.empty:
            # 첫날 가격을 100으로 기준 잡고 수익률 비교
            normalized = (data['Close'] / data['Close'].iloc[0]) * 100
            plt.plot(normalized.index, normalized, label=name, marker='o')
    
    plt.title("Economic Indicators (Last 5 Days, Baseline=100)")
    plt.legend()
    plt.grid(True)
    plt.savefig('report_chart.png')
    plt.close()

async def send_rich_report():
    symbols = {
        "나스닥": "^IXIC", "S&P500": "^GSPC", "골드": "GC=F", "WTI유": "CL=F"
    }
    
    # 1. 텍스트 보고서 작성
    report = "📊 [오늘의 주요 경제 리포트]\n\n"
    for name, ticker in symbols.items():
        data = yf.Ticker(ticker).history(period="2d")
        close_price = data['Close'].iloc[-1]
        pct_change = ((close_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
        emoji = "🔺" if pct_change > 0 else "🔻"
        report += f"{name}: {close_price:,.2f} ({emoji}{pct_change:.2f}%)\n"

    # 2. 뉴스 추가
    news_text = await get_news()
    report += f"\n📰 [어제/오늘의 주요 뉴스]\n{news_text}"

    # 3. 차트 생성
    create_chart(symbols)

    # 4. 텔레그램 전송
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')

    if token and chat_id:
        bot = telegram.Bot(token=token)
        # 차트 이미지 전송
        with open('report_chart.png', 'rb') as f:
            await bot.send_photo(chat_id=int(chat_id), photo=f, caption="📈 주요 지표 5일 추이")
        # 텍스트 리포트 전송
        await bot.send_message(chat_id=int(chat_id), text=report, disable_web_page_preview=True)
        print("🚀 전송 완료!")

if __name__ == "__main__":
    asyncio.run(send_rich_report())
