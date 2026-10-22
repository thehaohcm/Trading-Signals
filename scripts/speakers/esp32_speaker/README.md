# Trading Alert Speaker (ESP32-S3)

Thiết bị nhỏ thay cho Raspberry Pi + loa Bluetooth. Nó nghe cảnh báo từ ntfy, phát tiếng chuông, đọc to bằng tiếng Việt và hiện nội dung lên màn OLED.

Phần cứng: mạch tím ESP32-S3 **N16R8** (kiểu "xiaozhi bread-compact"), loa gắn sẵn, màn OLED 0.96" SSD1306 I2C.

## 1. Nạp firmware (không cần cài phần mềm)

1. Mở **Chrome** hoặc **Edge** trên máy tính, vào https://espressif.github.io/esptool-js/
2. Đưa mạch vào chế độ nạp: **giữ nút BOOT**, cắm cáp USB-C vào máy, rồi thả nút.
   Nếu mạch có nút RESET thì cũng có thể giữ BOOT, bấm RESET, rồi thả BOOT.
3. Baudrate để `921600`, bấm **Connect**, chọn cổng `USB JTAG/serial debug unit` (macOS hiện là `cu.usbmodem…`).
4. Bấm **Erase Flash** để xoá firmware cũ (xiaozhi) và chờ xong.
5. Ở mục Flash Address nhập `0x0`, chọn file `firmware/trading_alert_esp32s3_merged.bin`, bấm **Program**.
6. Nạp xong thì rút cáp và cắm lại (hoặc bấm RESET).

> Muốn quay lại firmware xiaozhi: nạp lại bằng công cụ của xiaozhi, mạch không bị ảnh hưởng gì.

## 2. Cài Wi-Fi bằng điện thoại

1. Lần đầu khởi động, màn hình hiện `CÀI ĐẶT WI-FI`.
2. Điện thoại vào **Cài đặt → Wi-Fi** và kết nối mạng **`TradingAlert-Setup`**.
3. Trang cài đặt thường tự mở. Nếu không, mở trình duyệt vào **192.168.4.1**.
4. Bấm **Configure WiFi**, chọn Wi-Fi nhà, nhập mật khẩu rồi **Save**.
5. Thiết bị kết nối Wi-Fi, màn hình hiện `Đang nghe…` và loa đọc *"Hệ thống đọc cảnh báo Trading Signals đã sẵn sàng."*

Mặc định thiết bị đã trỏ sẵn tới `http://152.53.208.182:8088`, topic `trading_signals_alerts`, nên không cần nhập gì thêm.

## 3. Đổi cấu hình sau này

Mở trình duyệt vào **`http://<IP-hiện-trên-màn-hình>/`** rồi chọn **Setup**. Trang này dùng để đổi:

- Server, topic và token ntfy
- Âm lượng (0–21) và bật/tắt tiếng chuông
- **Chân cắm loa I2S** và chân màn hình (khi mạch có sơ đồ khác)
- Loại màn hình, xoay màn hình 180°
- **Tắt màn hình sau N phút không có tin** (mặc định 5, đặt `0` để luôn sáng)

Bấm **Save** thì thiết bị tự khởi động lại với cấu hình mới.

Các trang tiện ích:
- `http://<IP>/say?text=xin chào` để thử loa
- `http://<IP>/status` để xem trạng thái

## 4. Màn hình nghỉ (chống lưu ảnh OLED)

- Có tin mới: màn hình sáng hết mức và giữ nội dung tin trong 60 giây.
- Sau đó chuyển sang màn hình chờ (giờ, trạng thái, tin cuối) ở độ sáng thấp.
- Sau **5 phút** không có tin, màn hình **tắt hẳn**. Loa vẫn nghe và đọc tin bình thường.
- Có tin mới hoặc bấm BOOT thì màn hình bật lại.
- Mất Wi-Fi hoặc ntfy thì màn hình **tự bật** và hiện lỗi để bạn thấy.

## 5. Cập nhật firmware qua Wi-Fi (không cần cáp)

Mở `http://<IP>/` rồi chọn **Update**, chọn file `trading_alert_app_vX.Y.Z.bin` và bấm Update. Cách này giữ nguyên cài đặt Wi-Fi.

## Nút bấm

| Thao tác | Tác dụng |
|---|---|
| Bấm nhanh **BOOT** | Màn hình đang tắt thì bật lên. Đang sáng thì đọc lại tin cuối, hoặc dừng nếu đang đọc |
| **Giữ BOOT 5 giây** | Xoá Wi-Fi để cài lại, ví dụ khi mang sang nhà khác |
| Nút tăng / giảm âm lượng (nếu mạch có) | Tăng / giảm âm lượng 1 nấc, có lưu lại |

## 6. Xử lý sự cố

| Hiện tượng | Cách xử lý |
|---|---|
| Màn hình không sáng | Kiểm tra màn cắm đúng chiều (GND–VDD–SCK–SDA khớp với chữ in trên mạch). Firmware tự dò chân I2C, xem dòng `[OLED]` trong log |
| Chữ bị lộn ngược | Setup → `Xoay màn hình 180°` đổi sang `0` (hoặc `1`) |
| Có chữ nhưng không có tiếng | Sơ đồ chân loa khác mặc định (15/16/7). Hỏi shop chân BCLK/LRCK/DOUT, rồi nhập ở Setup |
| Tiếng nhỏ | Setup → Âm lượng `21` |
| Không đọc được (log có `[TTS] Lỗi`) | Mạng chặn Google Translate, hoặc Google tạm giới hạn |

**Xem log:** mở Chrome vào https://espressif.github.io/esptool-js/, bấm Connect ở mục *Console* với baud `115200`, rồi bấm RESET. Hoặc dùng `pio device monitor`.

## 7. Tự build lại (tuỳ chọn)

```bash
pip3 install platformio      # hoặc: brew install platformio
cd esp32_speaker
pio run -t upload            # build + nạp qua USB
pio device monitor           # xem log
```

Test phần chuyển chữ thành câu đọc trên máy tính:
```bash
cd test_host && g++ -std=c++17 -I../src test_text_vi.cpp ../src/text_vi.cpp -o t && ./t < cases.txt
```

## Cấu trúc

- `src/main.cpp`: Wi-Fi/cài đặt (WiFiManager), nghe ntfy (HTTP stream), hàng đợi đọc, màn hình, nút bấm
- `src/text_vi.cpp`: chuẩn hoá câu đọc tiếng Việt, giống `ntfy_speaker.py` trên Raspberry Pi
- `firmware/trading_alert_esp32s3_merged.bin`: bản đầy đủ, nạp qua USB ở `0x0` (lần đầu, xoá sạch cài đặt)
- `firmware/trading_alert_app_v*.bin`: chỉ phần ứng dụng, nạp ở `0x10000` qua USB hoặc qua trang Update (giữ cài đặt Wi-Fi)
