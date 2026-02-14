#!/usr/bin/env python3
"""台灣 ETF 即時報價查詢"""

import requests
import sys

def get_etf_price(symbol):
    """查詢 ETF 價格（使用 Yahoo Finance）"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.TW"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        price = data['chart']['result'][0]['meta']['regularMarketPrice']
        return price
    except Exception as e:
        return f"查詢失敗: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方式: python3 fetch_tw_etf.py 0050")
        sys.exit(1)
    
    symbol = sys.argv[1]
    price = get_etf_price(symbol)
    print(f"{symbol} 最新價格: NT${price}")
