# ntfy Speaker — đọc cảnh báo Trading Signals qua loa (Raspberry Pi)

Raspberry Pi nghe server **ntfy** 24/24. Khi `alert.py` gửi cảnh báo, Pi phát tiếng chuông rồi **đọc nội dung bằng tiếng Việt** qua loa Bluetooth hoặc jack 3.5mm.

```
alert.py ──► ntfy (VPS :8088) ──HTTP stream──► Raspberry Pi ──► 🔔 + giọng đọc tiếng Việt ──► loa
```

## Tính năng
- Giữ một kết nối stream tới ntfy, nên tin đến là đọc ngay, không phải hỏi server liên tục. Rớt mạng thì tự kết nối lại.
- Không đọc trùng: khi kết nối lại chỉ lấy tin sau tin cuối đã nhận. Tin cũ hơn 5 phút bị bỏ qua.
- Chuẩn hoá chữ cho dễ nghe: `67,250.50$` đọc thành "67250 phẩy 5 đô la", `92,300đ` thành "92300 đồng", `-2.0%` thành "âm 2 phần trăm", `BTCUSDT` thành "BTC USDT".
- Giọng đọc: dùng **Google TTS** (tự nhiên, cần internet). Mất mạng tới Google thì tự chuyển sang **espeak-ng** (offline, giọng máy).
- Tin **khẩn** (priority 5: cắt lỗ, lỗi lệnh thật) có tiếng chuông riêng và vẫn được đọc trong **giờ yên lặng**.
- Tự kết nối lại loa Bluetooth khi loa ngủ (đặt `BT_SPEAKER_MAC`).

## Cài đặt
Dùng Raspberry Pi 3 trở lên, chạy Raspberry Pi OS Bookworm.

```bash
# Copy thư mục này lên Pi (VD bằng scp), rồi trên Pi:
cd raspberry_pi_speaker
bash install.sh
nano ~/ntfy-speaker/.env          # sửa NTFY_SERVER_URL=http://<IP-VPS>:8088
systemctl --user restart ntfy-speaker
```

**Đọc thử loa:**
```bash
~/ntfy-speaker/venv/bin/python ~/ntfy-speaker/ntfy_speaker.py --test
```

**Gửi một cảnh báo thử từ máy bất kỳ:**
```bash
curl -H "Title: Test BTCUSDT" -H "Priority: high" \
     -d "Đã vào lệnh mua tầng 1 BTCUSDT tại giá 67,250.50\$" \
     http://<IP-VPS>:8088/trading_signals_alerts
```

**Xem log:** `journalctl --user-unit ntfy-speaker -f`

## Tự chạy lại khi rút điện / cắm điện lại
`install.sh` đã cấu hình sẵn, **không cần làm gì thêm**:
- Script chạy như **systemd user service** (`systemctl --user enable`), có `Restart=always`: crash thì tự chạy lại sau 10 giây.
- `loginctl enable-linger` cho service tự khởi động ngay khi Pi boot xong, **không cần đăng nhập** hay mở màn hình.
- Pi boot xong nhưng Wi-Fi/mạng chưa có: script tự thử kết nối lại (2s → 4s → … tối đa 60s), có mạng là nghe tiếp.
- Kết nối được ntfy, loa đọc **"Hệ thống đọc cảnh báo Trading Signals đã sẵn sàng"** để bạn biết Pi đã chạy (tắt bằng `STARTUP_ANNOUNCE=false`).

Kiểm tra sau khi cắm điện lại:
```bash
systemctl --user status ntfy-speaker          # phải là "active (running)"
journalctl --user-unit ntfy-speaker -b          # log từ lần khởi động này
loginctl show-user "$USER" --property=Linger  # phải là Linger=yes
```

> **Rút điện đột ngột có thể làm hỏng thẻ SD** theo thời gian. Nếu Pi chỉ dùng để đọc cảnh báo, nên bật chế độ chỉ đọc:
> `sudo raspi-config` → Performance Options → Overlay File System → Enable. Khi đó mọi thay đổi (kể cả `.env`) sẽ mất sau khi khởi động lại, nên hãy cấu hình xong xuôi rồi mới bật, và tắt overlay mỗi khi cần sửa.

## Chọn loa

### Jack 3.5mm
```bash
sudo raspi-config        # System Options → Audio → chọn Headphones
amixer set Master 90%    # chỉnh âm lượng
```

### Loa Bluetooth
Nên dùng bản Raspberry Pi OS có PipeWire (bản Desktop có sẵn). Với bản Lite, cài thêm:
```bash
sudo apt install pipewire pipewire-pulse wireplumber libspa-0.2-bluetooth
```

**Cách nhanh — dùng script chọn loa:**
```bash
bash bt-speaker.sh            # quét → chọn loa từ danh sách → pair, trust, connect, đặt làm đầu ra, lưu MAC vào .env
bash bt-speaker.sh status     # xem loa đang kết nối & đầu ra âm thanh
bash bt-speaker.sh reconnect  # kết nối lại loa đã lưu
```

**Hoặc làm thủ công với bluetoothctl** (pair loa một lần):
```bash
bluetoothctl
  power on
  scan on                 # bật chế độ pair trên loa, chờ thấy tên loa
  pair AA:BB:CC:DD:EE:FF
  trust AA:BB:CC:DD:EE:FF # để tự kết nối lại về sau
  connect AA:BB:CC:DD:EE:FF
  exit
```
Thêm `BT_SPEAKER_MAC=AA:BB:CC:DD:EE:FF` vào `~/ntfy-speaker/.env` để script tự kết nối lại khi loa ngủ.

## Cấu hình (`~/ntfy-speaker/.env`)
| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `NTFY_SERVER_URL` | (bắt buộc) | `http://<IP-VPS>:8088` |
| `NTFY_TOPIC` | `trading_signals_alerts` | Topic mà `alert.py` gửi vào |
| `NTFY_TOKEN` | | Token, nếu server ntfy bật xác thực |
| `TTS_ENGINES` | `gtts,espeak` | Thứ tự thử các giọng đọc |
| `QUIET_HOURS` | | Ví dụ `23:00-07:00`: trong khung giờ này chỉ đọc tin khẩn |
| `MAX_AGE_SECONDS` | `300` | Bỏ qua tin cũ hơn N giây |
| `CHIME` | `true` | Phát chuông trước khi đọc |
| `BT_SPEAKER_MAC` | | MAC loa Bluetooth để tự kết nối lại |
| `AUDIO_PLAYER` | tự chọn | Ép dùng một lệnh phát cụ thể, ví dụ `aplay` |

## Lưu ý
- Pi phải truy cập được cổng ntfy của VPS (mặc định `8088`). Kiểm tra bằng `curl http://<IP-VPS>:8088/v1/health`.
- Pi chỉ nhận đúng những gì `alert.py` gửi lên ntfy. Hiện `alert.py` **không** gửi cổ phiếu Mỹ và lợi suất trái phiếu lên ntfy (xem `is_ntfy_allowed_asset`).
