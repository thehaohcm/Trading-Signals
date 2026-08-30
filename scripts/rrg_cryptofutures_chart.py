import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as PathEffects
from datetime import datetime
import psycopg2
import random
from dotenv import load_dotenv

load_dotenv()

# --- 1. CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, '../www')
OUTPUT_FILENAME = 'futures_rrgchart.png'
os.makedirs(OUTPUT_DIR, exist_ok=True)
image_filename = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)

# Danh sách mặc định nếu DB trống
tickers = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']

try:
    print("Kết nối DB lấy danh sách Futures Watchlist...")
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST'), database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASSWORD'),
        port=os.environ.get('DB_PORT')
    )
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT symbol FROM public.futures_watchlist;")
    rows = cur.fetchall()
    
    db_tickers = [row[0] for row in rows if row[0] not in tickers]
    tickers.extend(db_tickers)
    print(f"Tổng cộng có {len(tickers)} mã Futures cần vẽ RRG.")
    cur.close(); conn.close()
except Exception as e:
    print(f"Lỗi DB: {e}. Sử dụng danh sách mặc định.")

# --- 2. FETCH BINANCE FUTURES DATA ---
print("Đang tải dữ liệu từ Binance Futures API...")
df_close = pd.DataFrame()

for symbol in tickers:
    try:
        url = "https://fapi.binance.com/fapi/v1/klines"
        params = {"symbol": symbol, "interval": "1d", "limit": 150} # Cần 150 ngày để RRG đủ độ mượt
        res = requests.get(url, params=params)
        data = res.json()
        
        # Chỉ lấy giá đóng cửa
        closes = [float(k[4]) for k in data]
        if len(closes) == 150:
            df_close[symbol] = closes
    except Exception as e:
        pass

if df_close.empty:
    print("Không lấy được dữ liệu. Thoát script.")
    exit()

# --- 3. TÍNH TOÁN RRG (SMOOTHED) ---
def calculate_rrg_smoothed(series, window_ratio=100, window_mom=25, smooth_window=3):
    rs_scaled = 100 * series 
    
    # RS-Ratio
    mean_r = rs_scaled.rolling(window=window_ratio).mean()
    std_r = rs_scaled.rolling(window=window_ratio).std(ddof=0)
    rsr_raw = 100 + ((rs_scaled - mean_r) / std_r)
    
    # ROC của RS-Ratio
    roc = 100 * ((rsr_raw / rsr_raw.shift(1)) - 1)
    
    # RS-Momentum
    mean_m = roc.rolling(window=window_mom).mean()
    std_m = roc.rolling(window=window_mom).std(ddof=0)
    rsm_raw = 100 + ((roc - mean_m) / std_m)
    
    # Smoothing
    rsr_smoothed = rsr_raw.rolling(window=smooth_window).mean()
    rsm_smoothed = rsm_raw.rolling(window=smooth_window).mean()
    
    return pd.DataFrame({'RSR': rsr_smoothed, 'RSM': rsm_smoothed}).dropna()

rrg_data = {}
colors = {'BTCUSDT': '#f7931a', 'ETHUSDT': '#627eea', 'BNBUSDT': '#f3ba2f', 'SOLUSDT': '#14f195'}

for col in df_close.columns:
    df_res = calculate_rrg_smoothed(df_close[col])
    if not df_res.empty:
        rrg_data[col] = df_res
        if col not in colors:
            colors[col] = "#{:06x}".format(random.randint(0, 0xFFFFFF))

# --- 4. VẼ BIỂU ĐỒ (AUTO-ZOOM NHỎ GỌN) ---
fig, ax = plt.subplots(figsize=(8.5, 8.5))
ax.axhline(100, color='#475569', lw=1.2, zorder=2)
ax.axvline(100, color='#475569', lw=1.2, zorder=2)

all_x, all_y = [], []
tail_length = 7

for ticker, df_res in rrg_data.items():
    if len(df_res) < tail_length: continue
    recent = df_res.tail(tail_length)
    x, y = recent['RSR'], recent['RSM']
    
    all_x.extend(x.values)
    all_y.extend(y.values)
    
    c = colors.get(ticker, '#334155')
    
    # Vẽ đuôi và điểm hiện tại
    ax.plot(x, y, color=c, alpha=0.6, lw=1.8, zorder=3)
    ax.scatter(x.iloc[-1], y.iloc[-1], s=70, color=c, edgecolors='white', linewidth=1.2, zorder=5)
    
    # Nhãn tên (Cắt bỏ đuôi USDT cho gọn)
    display_name = ticker.replace("USDT", "")
    txt = ax.text(x.iloc[-1] + 0.04, y.iloc[-1] + 0.04, display_name, 
                  fontsize=9, fontweight='bold', color=c, zorder=6)
    txt.set_path_effects([PathEffects.withStroke(linewidth=2.5, foreground='white')])

# Logic Auto-Zoom
if all_x:
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    
    span_x = max(max_x - min_x, 1.5)
    span_y = max(max_y - min_y, 1.5)
    pad = max(max(span_x, span_y) * 0.18, 0.8)
    
    center_x = (max_x + min_x) / 2
    center_y = (max_y + min_y) / 2
    max_range = max(span_x, span_y) / 2 + pad
    max_range = max(max_range, 1.8)

    ax.set_xlim(center_x - max_range, center_x + max_range)
    ax.set_ylim(center_y - max_range, center_y + max_range)
    
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    alpha_quad = 0.06
    
    ax.fill_between([100, xlim[1]], 100, ylim[1], color='green', alpha=alpha_quad)  # Leading
    ax.fill_between([100, xlim[1]], ylim[0], 100, color='#B8860B', alpha=alpha_quad)# Weakening
    ax.fill_between([xlim[0], 100], ylim[0], 100, color='red', alpha=alpha_quad)    # Lagging
    ax.fill_between([xlim[0], 100], 100, ylim[1], color='blue', alpha=alpha_quad)   # Improving

    ax.text(xlim[1]*0.99, ylim[1]*0.99, 'LEADING', color='#16a34a', ha='right', va='top', alpha=0.6, fontweight='bold', fontsize=11)
    ax.text(xlim[1]*0.99, ylim[0]*1.01, 'WEAKENING', color='#ca8a04', ha='right', va='bottom', alpha=0.6, fontweight='bold', fontsize=11)
    ax.text(xlim[0]*1.01, ylim[0]*1.01, 'LAGGING', color='#dc2626', ha='left', va='bottom', alpha=0.6, fontweight='bold', fontsize=11)
    ax.text(xlim[0]*1.01, ylim[1]*0.99, 'IMPROVING', color='#2563eb', ha='left', va='top', alpha=0.6, fontweight='bold', fontsize=11)

now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
ax.set_title('RRG - Perpetual Futures', fontsize=13, fontweight='bold', pad=10)
ax.text(1, 1.01, f'Updated: {now_str}', transform=ax.transAxes, ha='right', color='#64748b', fontsize=8.5)
ax.set_xlabel('Trend (RS-Ratio)', fontsize=10, fontweight='600')
ax.set_ylabel('Momentum (RS-Momentum)', fontsize=10, fontweight='600')
ax.grid(True, linestyle='--', alpha=0.4, color='#cbd5e1')

plt.tight_layout()
plt.savefig(image_filename, dpi=110, bbox_inches='tight')
print(f'✅ Đã lưu chart Futures tại: {image_filename}')