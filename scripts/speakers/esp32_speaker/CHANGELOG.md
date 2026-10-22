# Lịch sử thay đổi

## v1.1.0
- Màn hình tự nghỉ để chống lưu ảnh OLED:
  - Tin mới sáng hết mức 60 giây, sau đó màn hình chờ chuyển sang độ sáng thấp.
  - Sau 5 phút không có tin thì tắt hẳn. Loa vẫn đọc bình thường.
  - Có tin mới hoặc bấm BOOT thì bật lại. Mất Wi-Fi/ntfy thì tự bật để báo lỗi.
  - Chỉnh số phút ở Setup → "Tắt màn hình sau N phút" (0 = luôn sáng).
- Thêm trang **Update** (`http://<IP>/` → Update) để nạp firmware qua Wi-Fi mà không mất cài đặt.
- Tên phiên bản trên màn hình đổi thành v1.1.0.

## v1.0.0
- Bản đầu tiên:
  - Cài Wi-Fi qua điện thoại (TradingAlert-Setup), nghe ntfy.
  - Tiếng chuông, đọc tiếng Việt qua Google TTS, hiện tin lên OLED.
  - Nút BOOT, trang /say và /status.

## Cách nạp
| File | Địa chỉ | Dùng khi |
|---|---|---|
| `firmware/trading_alert_esp32s3_merged_v1.1.0.bin` | `0x0` (bấm Erase Flash trước) | Lần đầu, hoặc mạch không lên. Xoá sạch cài đặt Wi-Fi |
| `firmware/trading_alert_app_v1.1.0.bin` | `0x10000` qua USB, hoặc qua trang Update | Cập nhật, giữ cài đặt Wi-Fi |

Nạp file `app` ở `0x0` sẽ ghi đè bootloader, làm mạch không khởi động được.
