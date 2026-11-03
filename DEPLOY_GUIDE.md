# HƯỚNG DẪN TRIỂN KHAI HỆ THỐNG TRADING SIGNALS (DEPLOYMENT GUIDELINE)

Tài liệu này hướng dẫn cách triển khai toàn bộ hệ thống hoặc từng module lên **Server VPS (hoặc Server IP mới sau này)**.

---

## 1. Kiến trúc hệ thống quy tập trên VPS

| Dịch vụ / Module | Công nghệ / Quản lý | Cổng (Port) | Đường dẫn trên VPS |
| :--- | :--- | :--- | :--- |
| **Web UI (SPA)** | Nginx Container (`osint_web`) | `80`, `3000` | `/home/thehaohcm/osint_ai_worker/dist` |
| **Trading API** | Go Backend Container (`trading_api`) | `8080` | `/home/thehaohcm/trading_api` |
| **OSINT AI Worker** | Python Worker Container | `8081` (nội bộ) | `/home/thehaohcm/osint_ai_worker` |
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

> **Ghi chú**: Tất cả các script (`deploy.sh`, `deploy_web.sh`, `osint_ai_worker/deploy.sh`, `trading_api/deploy.sh`, `scripts/deploy.sh`) đều **tự động ưu tiên đọc file `.env` ở thư mục gốc này**. Bạn không cần phải đi sửa từng file lẻ.

*(Tùy chọn: Nếu muốn đồng bộ file con cho gọn gàng, bạn có thể cập nhật thêm `trading_api/.env` và `scripts/.env` với cùng `DEPLOY_HOST`).*

---

## 3. Các lệnh Deploy

Tất cả các tác vụ triển khai đều có thể gọi từ script master ở thư mục gốc:

### A. Deploy TOÀN BỘ lên Server mới (Khuyên dùng khi mới dựng server)
```bash
./deploy.sh all
```
*Lệnh này sẽ tự động chạy tuần tự: Deploy Trading API → Deploy OSINT AI Worker → Build & Deploy Web UI Nginx → Upload Scripts, tạo Python venv, kích hoạt daemon 24/24 và cài đặt 6 cronjob.*

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
- **Hoặc chạy trực tiếp script bên trong `trading_api/`:**
  ```bash
  cd trading_api
  ./deploy.sh
  ```
- Script sẽ tự động build lại Docker image `trading_api` và chạy lại container trên port 8080, tự động chạy migration database.

#### 3. Cập nhật OSINT AI Worker (trích xuất tín hiệu, nhận định vĩ mô, podcast):
Khi bạn sửa code trong `osint_ai_worker/` (ví dụ `osint_ai_worker.py`, `agents/gemini_client.py`):
```bash
./deploy.sh worker
```
- Lưu ý: `./deploy.sh all` cũng deploy worker; còn `./deploy.sh api` hay `./deploy.sh web` thì **không** đụng đến worker.

#### 4. Cập nhật Python Scripts, 24/7 Alert Daemon hoặc Cronjob:
Khi bạn sửa `alert.py`, các script quét coin/forex/chứng khoán trong `scripts/`:
```bash
./deploy.sh scripts
```
- Script sẽ tự động: Nén và đẩy mã nguồn vào `/home/thehaohcm/scripts` → Cập nhật virtualenv `pip install -r requirements.txt` → Khởi động lại service systemd `trading-alert.service` → Cập nhật lịch trình `crontab`.

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

---

## 🔐 Bảo mật & cấu hình mới (11/2026)

### 1. Xác thực Clerk thật cho Go API
Các endpoint ghi / đặt lệnh / cấu hình giờ yêu cầu **JWT Clerk hợp lệ** (trước đây chỉ cần header khác rỗng). Frontend tự gắn token qua `src/utils/authFetch.js`.

Thêm vào `trading_api/.env` (đã thêm sẵn `CLERK_ISSUER`):

| Biến | Ý nghĩa |
|---|---|
| `CLERK_ISSUER` | vd `https://hot-sunbird-569.clerk.accounts.dev` (hoặc dùng `CLERK_PUBLISHABLE_KEY=pk_...` để tự suy ra) |
| `ADMIN_CLERK_USER_IDS` | user_id Clerk được làm admin, phân tách bằng dấu phẩy (Clerk Dashboard → Users). **Để trống = mọi tài khoản Clerk đăng nhập được đều là admin** → nên đặt |

Chưa cấu hình issuer → các endpoint cần quyền trả `401` (fail-closed). `GET /api/settings` không còn trả khoá API/secret/mật khẩu.

### 2. SL phía sàn Binance
Mỗi vị thế thật có đúng **1 lệnh SL phủ tổng khối lượng**, tự dời lên theo trailing; huỷ khi đóng vị thế. Lỗi đặt SL → cảnh báo `[CẦN XỬ LÝ THỦ CÔNG]`. Nút đóng vị thế thủ công trên web huỷ SL rồi chỉ bán đúng khối lượng của vị thế, và **chỉ đóng trong DB khi sàn thành công**.

### 3. Biến môi trường tuỳ chỉnh cho `scripts/alert.py` (đều có mặc định)

| Nhóm | Biến (mặc định) |
|---|---|
| Lọc breakout giả | `BREAKOUT_FILTER_ENABLED`(1), `BREAKOUT_CONFIRM_MARGIN_PCT`(0.05), `BREAKOUT_HOLD_SEC`(crypto 30 / VN-US 120 / khác 60), `BREAKOUT_MAX_CHASE_PCT`(2), `BREAKOUT_MIN_VOL_RATIO`(1.2, crypto/futures), `BREAKOUT_MAX_WAIT_SEC`(900) |
| Cổng rủi ro danh mục | `MAX_OPEN_POSITIONS`(10), `MAX_OPEN_REAL_POSITIONS`(5), `MAX_DAILY_SL_TOTAL`(6), `DAILY_LOSS_CAP_USD`/`WEEKLY_LOSS_CAP_USD`/`DAILY_LOSS_CAP_VND`/`WEEKLY_LOSS_CAP_VND`(0 = tắt) — đặt `0` để tắt từng giới hạn |
| SL theo biến động | `ATR_SL_MULT`(0 = tắt; vd `2` → SL = 2×ATR(14,1h), kẹp [sl_pct, 4×sl_pct]) |
| Lọc altcoin theo BTC | `BTC_REGIME_FILTER`(1) |
| AI | `AI_STALE_HOURS`(48), `AI_STATUS_CONFIRM_RUNS`(2, đặt cho worker), `ASSET_OVERRIDE_EXPIRE_DAYS`(21), `ASSET_OVERRIDE_DISAGREE_DAYS`(14) |
| Luồng quản lý vị thế | `POSITION_MANAGER_INTERVAL_SEC`(8), `POSITION_MANAGER_THREAD`(1) |
| SL sàn | `EXCHANGE_STOP_MIN_MOVE_PCT`(0.1) |

### 4. Deploy
Script deploy dùng `StrictHostKeyChecking=accept-new` (ghi nhận host key lần đầu, các lần sau phải khớp) và không còn đưa mật khẩu lên dòng lệnh. Khuyến nghị dùng khoá SSH: `DEPLOY_SSH_KEY=~/.ssh/id_ed25519` trong `.env`. Đặt `DEPLOY_STRICT_HOST_KEY=no` để quay lại hành vi cũ.

Thứ tự deploy: **Go API** (chạy migration 033–037) → **worker AI** → **alert.py** (script) → **frontend** (`deploy_web.sh`, đã gồm `nginx.conf` mới với rate-limit + security headers). HTTPS: xem `nginx.tls.conf.example`.

### 5. Kiểm thử
```bash
python3 -m unittest discover -s scripts/tests -v            # engine, lọc breakout giả, cổng rủi ro, SL sàn (sàn giả)
cd osint_ai_worker && python3 -m unittest discover -s tests # hysteresis trạng thái AI
cd trading_api && go test ./...                             # xác thực Clerk, lọc settings, client Binance
```

## 🧭 Cập nhật bảo mật đợt 2 & công cụ mới

- **Đăng nhập bắt buộc (Clerk)** cho: `/api/chat`, `/journal`, `/journal/batch-prices`, `/take-notes` (mọi người dùng đã đăng nhập). `user_id` kiểu Clerk (`user_...`) phải trùng người đăng nhập, nếu không trả 403. Ghi vào `/priceAlerts` chỉ admin (`ADMIN_CLERK_USER_IDS`). GET `/priceAlerts` vẫn công khai.
- **Community (diễn đàn)**: POST/PUT/DELETE trên `/community/posts` và `/community/comments` giờ cần đăng nhập; chỉ chủ bài/comment hoặc admin được sửa/xoá (trước đây AI PHÁT HIỆN: ai cũng xoá/sửa được bài của người khác, không cần đăng nhập — đã sửa). `user_id` khi tạo bài/comment lấy theo người đăng nhập, không tin giá trị client gửi lên.
- **Quản trị tin tức (news-items/news-groups)**: các thao tác POST/PUT/DELETE/toggle giờ cần admin (`ADMIN_CLERK_USER_IDS`). GET vẫn công khai.
- **Đóng vị thế THẬT trên Futures** từ UI: huỷ SL của sàn rồi đóng bằng lệnh MARKET `reduceOnly` (hỗ trợ one-way và hedge mode); lỗi sàn → vị thế giữ nguyên trong DB.
- **Python requirements** có trần phiên bản (cùng major) để `pip install` không tự nhảy bản lớn gây vỡ.
- **CSP** đang ở chế độ `Content-Security-Policy-Report-Only` (nginx.conf): chưa chặn gì. Mở DevTools → Console, nếu sau 1–2 tuần không có cảnh báo thì đổi tên header thành `Content-Security-Policy`.
- **Backtest**: `python3 scripts/backtest.py --symbols BTCUSDT,ETHUSDT --interval 15m --days 90` (thêm `--grid` để thử lưới tham số, `--ai-summary` để nhờ AI nhận xét **1 lần** cho tất cả symbol). Phép tính chạy bằng code, không tốn token.
- **Backtest cổ phiếu VN**: thêm `--vn-exchange hose|hnx|upcom` + `--csv file.csv` (chưa có nguồn nến VN online, phải tự xuất CSV). Mô phỏng T+2 (không bán được 2 phiên đầu), biên độ trần/sàn theo sàn, lô 100, thuế bán 0.1%.
- `./deploy.sh all` chạy test trước, rồi deploy theo thứ tự **API → Worker AI → alert.py (scripts) → Web**, và đợi `/health` của API trước khi đi tiếp (`SKIP_TESTS=1`, `SKIP_HEALTHCHECK=1` để bỏ qua).
