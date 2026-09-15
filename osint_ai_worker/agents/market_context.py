"""Market context helpers that do not initialize any LLM client."""

import logging
from concurrent.futures import ThreadPoolExecutor

import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_live_market_prices() -> str:
    tickers = [
        ("Vàng thế giới (Gold Futures / XAUUSD)", "GC=F", "USD/ounce"),
        ("Bạc thế giới", "SI=F", "USD/ounce"),
        ("Dầu WTI", "CL=F", "USD/thùng"),
        ("Dầu Brent", "BZ=F", "USD/thùng"),
        ("DXY", "DX-Y.NYB", "điểm"),
        ("Lợi suất US10Y", "^TNX", "%"),
        ("S&P 500", "^GSPC", "điểm"),
        ("Nasdaq 100", "QQQ", "USD"),
        ("Bitcoin", "BTC-USD", "USD"),
        ("USD/VND", "USDVND=X", "VND"),
    ]

    def fetch_one(name, symbol, unit):
        try:
            ticker = yf.Ticker(symbol)
            price = ticker.fast_info.get("lastPrice")
            previous = ticker.fast_info.get("previousClose")
            if price is None:
                history = ticker.history(period="2d")
                if not history.empty:
                    price = float(history["Close"].iloc[-1])
                    if len(history) > 1:
                        previous = float(history["Close"].iloc[-2])
            change = ((price - previous) / previous * 100) if price is not None and previous else 0
            return f"- {name} [{symbol}]: {price:,.2f} {unit} ({change:+.2f}%)" if price is not None else f"- {name} [{symbol}]: Đang cập nhật"
        except Exception as error:
            logger.warning("Could not fetch %s: %s", symbol, error)
            return f"- {name} [{symbol}]: Đang cập nhật"

    with ThreadPoolExecutor(max_workers=len(tickers)) as executor:
        return "\n".join(executor.map(lambda item: fetch_one(*item), tickers))
