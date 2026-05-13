import yfinance as yf
import telegram
import asyncio
import os

async def send_message():
    # 지표 설정
    symbols = {
        "나스닥": "^IXIC", "S&P500": "^GSPC", "유로FX": "EURUSD=X",
        "골드": "GC=F", "실버": "SI=F", "WTI유": "CL=F",
        "비트코인": "BTC-USD", "이더리움": "ETH-USD"
    }
    
    report = "📊 [오늘의 주요 경제 지표]\n\n"
    
    for name, ticker in symbols.items():
        try:
            data = yf.Ticker(ticker).history(period="2d")
            if not data.empty and len(data) >= 2:
                close_price = data['Close'].iloc[-1]
                prev_price = data['Close'].iloc[-2]
                change = close_price - prev_price
                pct_change = (change / prev_price) * 100
                emoji = "🔺" if change > 0 else "🔻"
                report += f"{name}: {close_price:,.2f} ({emoji}{pct_change:.2f}%)\n"
        except Exception:
            report += f"{name}: 데이터 조회 실패\n"

    # 환경 변수에서 토큰과 ID 가져오기
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')

    if token and chat_id:
        bot = telegram.Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=report)
    else:
        print("에러: 토큰이나 챗 ID가 설정되지 않았습니다.")

if __name__ == "__main__":
    asyncio.run(send_message())
