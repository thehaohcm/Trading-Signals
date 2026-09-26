import numpy as np
import requests

SYMBOL = "ADAUSDT"
MAX_SLIPPAGE_PCT = 0.0015  # Chấp nhận trượt giá tối đa 0.15% (0.0015)
PARTICIPATION_RATE = 0.03  # Chỉ chiếm tối đa 3% volume trung bình phút
BASE_URL = "https://api.binance.com"


def get_market_metrics(symbol):
    # 1. Lấy dữ liệu 20 nến 1m gần nhất
    kline_url = f"{BASE_URL}/api/v3/klines"
    kline_res = requests.get(
        kline_url, params={"symbol": symbol, "interval": "1m", "limit": 21}
    ).json()

    # Quote volume (USDT) của 20 nến đã đóng
    closed_volumes = [float(k[7]) for k in kline_res[:-1]]
    current_kline_vol = float(kline_res[-1][7])
    avg_vol_1m = np.mean(closed_volumes)

    # 2. Lấy Order Book L2 (Depth 100 levels)
    depth_url = f"{BASE_URL}/api/v3/depth"
    depth_res = requests.get(
        depth_url, params={"symbol": symbol, "limit": 100}
    ).json()

    asks = [
        (float(price), float(qty)) for price, qty in depth_res.get("asks", [])
    ]
    best_ask = asks[0][0]
    max_acceptable_price = best_ask * (1 + MAX_SLIPPAGE_PCT)

    # Tính tổng thanh khoản có sẵn trong phạm vi trượt giá cho phép
    liquid_usdt_in_depth = 0.0
    for price, qty in asks:
        if price <= max_acceptable_price:
            liquid_usdt_in_depth += price * qty
        else:
            break

    return {
        "best_ask": best_ask,
        "avg_vol_1m": avg_vol_1m,
        "current_kline_vol": current_kline_vol,
        "depth_liquidity_usdt": liquid_usdt_in_depth,
    }


def calculate_entry_sizes(symbol, pivot_price, user_max_budget=20000):
    metrics = get_market_metrics(symbol)

    best_ask = metrics["best_ask"]
    depth_liq = metrics["depth_liquidity_usdt"]
    avg_vol_1m = metrics["avg_vol_1m"]
    curr_vol = metrics["current_kline_vol"]

    # Đánh giá xung lực Volume
    vol_surge_ratio = curr_vol / (avg_vol_1m if avg_vol_1m > 0 else 1)

    # 1. Kích thước Market Order ngay lập tức (Chỉ ăn tối đa 15% depth trong vùng trượt giá)
    safe_market_size = depth_liq * 0.15

    # 2. Kích thước giải ngân theo dòng tiền (TWAP trong 5-10 phút)
    safe_twap_per_min = avg_vol_1m * PARTICIPATION_RATE
    recommended_twap_total = (
        safe_twap_per_min * 5
    )  # Rải đều lệnh trong 5 phút

    print(f"=== PHÂN TÍCH TÍN HIỆU BREAKOUT PIVOT: {pivot_price} ===")
    print(f"Giá thị trường hiện tại: {best_ask:.4f}")
    print(f"Thanh khoản có sẵn trong biên độ trượt giá 0.15%: {depth_liq:,.2f} USDT")
    print(
        f"Volume nến 1m hiện tại so với TB 20 nến: {vol_surge_ratio:.2f}x ({curr_vol:,.2f} / {avg_vol_1m:,.2f} USDT)"
    )
    print("-" * 50)

    # Đề xuất thực thi
    print("CHIẾN LƯỢC VÀO TIỀN:")
    if vol_surge_ratio < 1.0:
        print(
            "CẢNH BÁO: Volume breakout yếu (< 1.0x SMA20), nguy cơ Fakeout cao. Nên giảm 50% quy mô dự kiến."
        )

    print(
        f"1. Lệnh Market khớp NGAY: Tối đa {min(safe_market_size, user_max_budget):,.2f} USDT (đảm bảo trượt giá < 0.15%)"
    )
    print(
        f"2. Chẻ lệnh TWAP (5 phút): Rải {min(recommended_twap_total, user_max_budget):,.2f} USDT (~{safe_twap_per_min:,.2f} USDT/phút)"
    )
    print(
        f"3. Lệnh Limit retest Pivot ({pivot_price}): Đặt chờ tại Pivot với phần vốn còn lại."
    )


# Giả sử phát hiện breakout Pivot tại mức giá 0.8500
calculate_entry_sizes(
    symbol=SYMBOL, pivot_price=0.8500, user_max_budget=15000
)