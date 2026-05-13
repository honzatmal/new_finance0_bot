import yfinance as yf
import telegram
import asyncio
import os

async def send_message():
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
            report += f"{name}: 조회 실패\n"

    # 이 부분이 핵심입니다. 텍스트를 직접 넣지 마세요.
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')

    if token and chat_id:
        bot = telegram.Bot(token=token)
        await bot.send_message(chat_id=int(chat_id), text=report)
    else:
        print("에러: Secrets 설정이 누락되었습니다.")

if __name__ == "__main__":
    asyncio.run(send_message())
