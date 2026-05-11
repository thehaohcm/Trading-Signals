import time
from vnstock import Quote
from pygame import mixer
import os

# Khởi tạo âm thanh (Bạn có thể thay file 'beep.mp3' bằng file âm thanh của mình)
mixer.init()

def play_alert(symbol):
    # Sử dụng âm thanh mặc định hoặc file riêng
    # Nếu không có file, có thể dùng print('\a') để kêu bíp mặc định của hệ thống
    print("\a") 
    print(f">>> CẢNH BÁO: PHÁT HIỆN LỆNH LỚN CHO {symbol}! <<<")

def monitor_stocks(symbols, threshold=5000):
    last_processed_time = {symbol: set() for symbol in symbols}
    
    print(f"Bắt đầu theo dõi {symbols} với ngưỡng lệnh > {threshold}...")
    
    while True:
        try:
            for symbol in symbols:
                # Khởi tạo Quote cho từng symbol
                q = Quote(symbol=symbol, source='kbs')
                
                # Lấy dữ liệu khớp lệnh trong ngày (intraday) - lấy 50 ticks gần nhất để có đủ dữ liệu
                df = q.intraday(page_size=50, show_log=False)
                
                if df.empty:
                    continue
                
                # Lấy các giao dịch gần nhất (giả sử df được sắp xếp theo thời gian tăng dần)
                recent_trades = df.tail(10)  # Kiểm tra 10 giao dịch gần nhất
                
                for _, trade in recent_trades.iterrows():
                    current_time = trade['time']
                    volume = trade['volume']
                    price = trade['price']
                    side = trade.get('side', 'N/A')
                    
                    # Kiểm tra nếu là lệnh mới và đạt ngưỡng khối lượng
                    if current_time not in last_processed_time[symbol] and volume >= threshold and side != 'N/A':
                        print(f"[{current_time}] {symbol}: {side} {volume:,} cp tại giá {price}")
                        play_alert(symbol)
                        last_processed_time[symbol].add(current_time)
                        
                        # Giới hạn bộ nhớ, chỉ giữ 100 thời gian gần nhất
                        if len(last_processed_time[symbol]) > 100:
                            last_processed_time[symbol].pop()
            
            # Nghỉ 15 giây trước khi quét lượt tiếp theo để tránh bị khóa API (Rate limit)
            time.sleep(15)
            
        except Exception as e:
            print(f"Lỗi kết nối: {e}")
            time.sleep(5)

if __name__ == "__main__":
    watch_list = ['HCM', 'GEX', 'VHM']
    monitor_stocks(watch_list, threshold=5000)