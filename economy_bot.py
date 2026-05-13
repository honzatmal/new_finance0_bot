import yfinance as yf
import telegram
import asyncio
import os

async def send_message():
    # 대상 지표 설정
    symbols = {
        "나스닥": "^IXIC", 
        "S&P500": "^GSPC", 
        "유로FX": "EURUSD=X",
        "골드": "GC=F", 
        "실버": "SI=F", 
        "WTI유": "CL=F",
        "비트코인": "BTC-USD", 
        "이더리움": "ETH-USD"
    }
    
    report = "📊 [오늘의 주요 경제 지표]\n\n"
    
    for name, ticker in symbols.items():
        try:
            # 최근 2일간의 데이터를 가져와 변동률 계산
            data = yf.Ticker(ticker).history(period="2d")
            if len(data) >= 2:
                close_price = data['Close'].iloc[-1]
                prev_price = data['Close'].iloc[-2]
                change = close_price - prev_price
                pct_change = (change / prev_price) * 100
                
                emoji = "🔺" if change > 0 else "🔻"
                # 지표별 맞춤 포맷 (환율/원자재는 소수점 2자리, 지수는 정수 등)
                report += f"{name}: {close_price:,.2f} ({emoji}{pct_change:.2f}%)\n"
        except Exception as e:
            report += f"{name}: 데이터 불러오기 실패\n"

    # GitHub Secrets에서 정보 가져오기
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')

    if token and chat_id:
        bot = telegram.Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=report)
    else:
        print("에러: TELEGRAM_TOKEN 또는 CHAT_ID가 설정되지 않았습니다.")

if __name__ == "__main__":
    asyncio.run(send_message())
