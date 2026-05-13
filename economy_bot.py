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
        except:
            report += f"{name}: 조회 실패\n"

    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')

    if token and chat_id:
        try:
            bot = telegram.Bot(token=token)
            # 여기에 결과를 출력하도록 추가했습니다.
            await bot.send_message(chat_id=int(chat_id), text=report)
            print("🚀 [성공] 텔레그램으로 메시지를 보냈습니다!")
        except Exception as e:
            print(f"❌ [실패] 텔레그램 전송 에러: {e}")
            print(f"현재 사용중인 챗 ID: {chat_id}")
    else:
        print("⚠️ [에러] Secrets 설정(TOKEN 또는 ID)을 확인해주세요.")

if __name__ == "__main__":
    asyncio.run(send_message())
