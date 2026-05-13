import yfinance as yf
import telegram
import asyncio

async def send_message():
    # 대상 심볼 설정
    symbols = {
        "나스닥": "^IXIC", "S&P500": "^GSPC", "유로FX": "EURUSD=X",
        "골드": "GC=F", "실버": "SI=F", "WTI": "CL=F",
        "비트코인": "BTC-USD", "이더리움": "ETH-USD"
    }
    
    report = "📊 [오늘의 주요 경제 지표]\n\n"
    
    for name, ticker in symbols.items():
        data = yf.Ticker(ticker).history(period="2d")
        if len(data) >= 2:
            close_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2]
            change = close_price - prev_price
            pct_change = (change / prev_price) * 100
            
            emoji = "🔺" if change > 0 else "🔻"
            report += f"{name}: {close_price:,.2f} ({emoji}{pct_change:.2f}%)\n"

    # 텔레그램 전송
    bot = telegram.Bot(token='본인의_봇_토큰')
    await bot.send_message(chat_id='본인의_채팅_ID', text=report)

if __name__ == "__main__":
    asyncio.run(send_message())
