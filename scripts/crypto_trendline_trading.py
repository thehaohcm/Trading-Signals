import time
from datetime import datetime, timedelta
import numpy as np
from binance.client import Client
import schedule

# Thông tin API của Binance (thay bằng API Key và Secret Key của bạn)
API_KEY = "your_api_key_here"
API_SECRET = "your_secret_key_here"

# Khởi tạo client Binance
client = Client(API_KEY, API_SECRET)

# Thông số giao dịch
ORDER_VALUE_USDT = 100  # Giá trị mỗi lệnh mua là 100 USDT
DAILY_TRADE_LIMIT = 1  # Chỉ 1 giao dịch mỗi ngày cho mỗi coin

# Định nghĩa các coin và thông số trendline
COINS = {
    "LINKUSDT": {
        "point1_date": datetime(2024, 9, 22),
        "point2_date": datetime(2025, 2, 4),
        "point1_price": 8.08,
        "point2_price": 13.73,
        "daily_trade_count": 0,
        "last_trade_date": None
    },
    "SOLUSDT": {
        "point1_date": datetime(2022, 11, 17),
        "point2_date": datetime(2023, 8, 14),
        "point1_price": 8.00,
        "point2_price": 14.45,
        "daily_trade_count": 0,
        "last_trade_date": None
    },
    "BNBUSDT": {
        "point1_date": datetime(2024, 5, 10),
        "point2_date": datetime(2025, 2, 4),
        "point1_price": 400.00,
        "point2_price": 515.51,
        "daily_trade_count": 0,
        "last_trade_date": None
    }
}

# Tính hệ số góc (m) và hệ số chặn (b) cho từng coin
for symbol, data in COINS.items():
    days_diff = (data["point2_date"] - data["point1_date"]).days
    data["m"] = (data["point2_price"] - data["point1_price"]) / days_diff  # Hệ số góc
    data["b"] = data["point1_price"]  # Hệ số chặn (giá tại point1_date)

def reset_daily_trade_count(symbol):
    """Đặt lại số lượng giao dịch mỗi ngày cho một coin"""
    current_date = datetime.now().date()
    if COINS[symbol]["last_trade_date"] != current_date:
        COINS[symbol]["daily_trade_count"] = 0
        COINS[symbol]["last_trade_date"] = current_date

def get_trendline_price(symbol):
    """Tính giá trị của trendline tại thời điểm hiện tại cho một coin"""
    current_date = datetime.now()
    days_since_point1 = (current_date - COINS[symbol]["point1_date"]).days
    trendline_price = COINS[symbol]["m"] * days_since_point1 + COINS[symbol]["b"]
    return trendline_price

def get_current_price(symbol):
    """Lấy giá hiện tại của một coin từ Binance"""
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker["price"])

def place_buy_order(symbol):
    """Đặt lệnh mua 100 USDT giá trị cho một coin"""
    current_price = get_current_price(symbol)
    quantity = ORDER_VALUE_USDT / current_price  # Số lượng coin cần mua
    quantity = round(quantity, 3)  # Làm tròn đến 3 chữ số thập phân (theo yêu cầu của Binance)

    try:
        order = client.order_market_buy(
            symbol=symbol,
            quantity=quantity
        )
        print(f"Đã đặt lệnh mua: {quantity} {symbol[:-4]} tại giá {current_price} USDT")
        return True
    except Exception as e:
        print(f"Lỗi khi đặt lệnh mua cho {symbol}: {e}")
        return False

def trade():
    """Kiểm tra và thực hiện giao dịch cho tất cả các coin"""
    for symbol in COINS:
        # Đặt lại số lượng giao dịch nếu sang ngày mới
        reset_daily_trade_count(symbol)

        # Nếu đã đạt giới hạn giao dịch trong ngày cho coin này, bỏ qua
        if COINS[symbol]["daily_trade_count"] >= DAILY_TRADE_LIMIT:
            print(f"Đã đạt giới hạn giao dịch trong ngày cho {symbol}.")
            continue

        # Lấy giá hiện tại và giá trendline
        current_price = get_current_price(symbol)
        trendline_price = get_trendline_price(symbol)

        print(f"{symbol} | Giá hiện tại: {current_price} USDT | Giá trendline: {trendline_price} USDT")

        # Kiểm tra nếu giá hiện tại chạm hoặc thấp hơn trendline
        if current_price <= trendline_price:
            print(f"Giá của {symbol} đã chạm trendline! Đặt lệnh mua...")
            if place_buy_order(symbol):
                COINS[symbol]["daily_trade_count"] += 1
        else:
            print(f"Giá của {symbol} chưa chạm trendline. Chưa thực hiện giao dịch.")

# Lên lịch chạy script mỗi 5 phút
schedule.every(5).minutes.do(trade)

# Vòng lặp chính
print("Bắt đầu bot giao dịch...")
while True:
    schedule.run_pending()
    time.sleep(1)