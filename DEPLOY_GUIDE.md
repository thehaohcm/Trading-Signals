# HƯỚNG DẪN TRIỂN KHAI HỆ THỐNG TRADING SIGNALS (DEPLOYMENT GUIDELINE)

Tài liệu này hướng dẫn cách triển khai toàn bộ hệ thống hoặc từng module lên **Server VPS (hoặc Server IP mới sau này)**, cũng như lên các nền tảng Cloud (**Fly.io** và **Vercel**).

---

## 1. Kiến trúc hệ thống quy tập trên VPS

| Dịch vụ / Module | Công nghệ / Quản lý | Cổng (Port) | Đường dẫn trên VPS |
| :--- | :--- | :--- | :--- |
| **Web UI (SPA)** | Nginx Container (`osint_web`) | `80`, `3000` | `/home/thehaohcm/osint_ai_worker/dist` |
| **Trading API** | Go Backend Container (`trading_api`) | `8080` | `/home/thehaohcm/trading_api` |
| **Database** | PostgreSQL Container (`osint_postgres`) | `5432` | DB: `thehaohcm_trading_signal_db` |
| **Push Notification** | Ntfy Container (`osint_ntfy`) | `8088` | `http://127.0.0.1:8088` |
| **Alert Engine (24/24)** | Python Daemon (`trading-alert.service`) | Background | `/home/thehaohcm/scripts/alert.py` |
| **Tự động quét (Cron)** | Hệ thống Cron (`crontab -l`) | Theo lịch | `/home/thehaohcm/scripts/` |

---

## 2. Khi có Server mới: Cần sửa IP ở đâu?

Hệ thống được thiết kế để sử dụng **1 file cấu hình trung tâm duy nhất** ở thư mục gốc:

### 👉 File chính cần sửa: `.env` (Tại thư mục gốc project)
Mở file `.env` ở thư mục gốc và chỉ cần thay đổi địa chỉ IP:
```ini
# Cấu hình IP và thông tin SSH của Server mới
DEPLOY_HOST=your_server_ip           # <-- Thay bằng IP server mới của bạn
DEPLOY_USER=thehaohcm                # <-- Username SSH trên server mới
DEPLOY_PASSWORD=your_ssh_password    # <-- Mật khẩu SSH
DEPLOY_PORT=22                       # <-- Port SSH (mặc định 22)

# Cấu hình kết nối Database từ máy cá nhân lên Server mới
DB_HOST=your_server_ip               # <-- Thay bằng IP server mới
DB_USER=thehaohcm
DB_PASSWORD=your_db_password
DB_NAME=thehaohcm_trading_signal_db
DB_PORT=5432
```

> **Ghi chú**: Tất cả các script (`deploy.sh`, `deploy_web.sh`, `trading_api/deploy_server.sh`, `scripts/deploy_scripts_to_vps.sh`) đều **tự động ưu tiên đọc file `.env` ở thư mục gốc này**. Bạn không cần phải đi sửa từng file lẻ.

*(Tùy chọn: Nếu muốn đồng bộ file con cho gọn gàng, bạn có thể cập nhật thêm `trading_api/.env` và `scripts/.env` với cùng `DEPLOY_HOST`).*

---

## 3. Các lệnh Deploy

Tất cả các tác vụ triển khai đều có thể gọi từ script master ở thư mục gốc:

### A. Deploy TOÀN BỘ lên Server mới (Khuyên dùng khi mới dựng server)
```bash
./deploy.sh all
```
*Lệnh này sẽ tự động chạy tuần tự: Deploy Trading API → Build & Deploy Web UI Nginx → Upload Scripts, tạo Python venv, kích hoạt daemon 24/24 và cài đặt 6 cronjob.*

---

### B. Deploy TỪNG MODULE riêng biệt khi cập nhật tính năng

#### 1. Cập nhật giao diện Web UI:
Khi bạn chỉnh sửa code Vue trong thư mục `src/`:
```bash
./deploy.sh web
```
- Script sẽ tự động: `npm run build` → Nén `dist/` và `nginx.conf` → Đẩy lên VPS → Reload/Khởi động lại container `osint_web`.

#### 2. Cập nhật Trading API (Go Backend):
Khi bạn thêm route mới hoặc cập nhật logic trong thư mục `trading_api/`:
- **Từ thư mục gốc:**
  ```bash
  ./deploy.sh api
  ```
- **Hoặc thao tác trực tiếp bên trong `trading_api/`:**
  ```bash
  cd trading_api
  ./deploy.sh server     # Deploy lên VPS Server
  ./deploy.sh fly        # Deploy lên Fly.io
  ./deploy.sh all        # Deploy lên CẢ HAI (VPS + Fly.io)
  ```
- Script sẽ tự động build lại Docker image `trading_api` và chạy lại container trên port 8080, tự động chạy migration database.

#### 3. Cập nhật Python Scripts, 24/7 Alert Daemon hoặc Cronjob:
Khi bạn sửa `alert.py`, các script quét coin/forex/chứng khoán trong `scripts/`:
```bash
./deploy.sh scripts
```
- Script sẽ tự động: Nén và đẩy mã nguồn vào `/home/thehaohcm/scripts` → Cập nhật virtualenv `pip install -r requirements.txt` → Khởi động lại service systemd `trading-alert.service` → Cập nhật lịch trình `crontab`.

#### 4. Deploy lên Cloud bên ngoài (Fly.io & Vercel):
```bash
./deploy.sh fly        # Triển khai Trading API lên Fly.io
./deploy.sh vercel     # Triển khai Web UI lên Vercel
```

---

## 4. Chi tiết các Cronjob và Daemon trên Server

### Danh sách 6 Cronjob tự động (chạy dưới user `thehaohcm`):
1. **`run_crypto.sh`**: Chạy mỗi 4 tiếng (`0 */4 * * *`)
2. **`fetch_potential_world_stocks.py`**: Chạy mỗi 4 tiếng từ Thứ 2 đến Thứ 6 (`0 */4 * * 1-5`)
3. **`run_forex.sh`**: Chạy mỗi 4 tiếng từ Thứ 2 đến Thứ 6 (`0 */4 * * 1-5`)
4. **`rrg_assets_chart.py`**: Sinh biểu đồ RRG tài sản mỗi ngày lúc 00:05 (`5 0 * * *`)
5. **`rrg_crypto_chart.py`**: Sinh biểu đồ RRG tiền số mỗi ngày lúc 00:05 (`5 0 * * *`)
6. **`fetch_highest_interest_rate.py`**: Lấy lãi suất ngân hàng cao nhất mỗi Chủ Nhật (`0 0 * * 0`)

### Daemon chạy ngầm 24/24 (`trading-alert.service`):
- Chạy: `python3 -u alert.py >> alert.log 2>&1`
- Tự động quét 43 mã Breakout Radar, quản lý vị thế nhồi lệnh tự động, bắn thông báo Slack và Ntfy Push Notification liên tục 24/7.
- Tự động restart trong 5s nếu gặp lỗi mạng, tự động chạy khi server reboot.

---

## 5. Các lệnh kiểm tra & Debug nhanh trên VPS

Khi SSH vào server (`ssh <username>@<your_server_ip>`):

```bash
# 1. Kiểm tra trạng thái các container Docker:
docker ps

# 2. Xem log thời gian thực của Trading API:
docker logs -f trading_api

# 3. Xem log thời gian thực của Web Nginx:
docker logs -f osint_web

# 4. Kiểm tra trạng thái daemon Alert 24/24:
sudo systemctl status trading-alert.service

# 5. Xem log quét của Alert 24/24:
tail -f /home/thehaohcm/scripts/alert.log

# 6. Xem danh sách cronjob đang hoạt động:
crontab -l

# 7. Xem log chạy của cronjob:
tail -f /home/thehaohcm/scripts/cron.log
```
