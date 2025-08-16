import pandas as pd
import yfinance as yf

def get_nasdaq100_companies():
    """
    나스닥 100 기업 목록을 가져옵니다.
    """
    # 나스닥 100 ETF (QQQ)의 구성종목을 통해 얻거나, 직접 리스트를 사용
    nasdaq100_symbols = [
        'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'GOOG', 'META', 'TSLA', 'AVGO', 'COST',
        'NFLX', 'TMUS', 'ASML', 'ADBE', 'PEP', 'LIN', 'CSCO', 'TXN', 'QCOM', 'INTU',
        'AMAT', 'CMCSA', 'HON', 'AMGN', 'VRTX', 'AMD', 'SBUX', 'GILD', 'ADP', 'ISRG',
        'MU', 'INTC', 'ADI', 'LRCX', 'MDLZ', 'PYPL', 'REGN', 'BKNG', 'KLAC', 'MELI',
        'CSX', 'SNPS', 'CDNS', 'MAR', 'ORLY', 'MRVL', 'FTNT', 'CRWD', 'ADSK', 'NXPI',
        'ROP', 'WDAY', 'ABNB', 'MNST', 'CHTR', 'TTD', 'TEAM', 'AEP', 'FAST', 'ROST',
        'KDP', 'ODFL', 'BZ', 'VRSK', 'EXC', 'DDOG', 'XEL', 'KHC', 'CTSH', 'GEHC',
        'LULU', 'CCEP', 'ON', 'DXCM', 'BIIB', 'ANSS', 'ZS', 'IDXX', 'CTAS', 'TTWO',
        'WBD', 'GFS', 'ILMN', 'MRNA', 'PCAR', 'EA', 'CDW', 'SGEN', 'ALGN', 'LCID',
        'WBA', 'ENPH', 'DLTR', 'SIRI', 'MTCH', 'PAYX', 'EBAY', 'JD', 'RIVN', 'ZM'
    ]
    
    # 회사명 매핑 딕셔너리
    company_names = {}
    
    print("나스닥 100 기업 정보를 가져오는 중...")
    for symbol in nasdaq100_symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            company_names[symbol] = info.get('longName', symbol)
        except:
            company_names[symbol] = symbol
    
    return nasdaq100_symbols, company_names

if __name__ == "__main__":
    symbols, names = get_nasdaq100_companies()
    print(f"나스닥 100 기업 수: {len(symbols)}")
    for symbol in symbols[:10]:  # 처음 10개만 출력
        print(f"{symbol}: {names[symbol]}")
