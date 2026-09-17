# NotebookLM giữa phiên

Service `notebooklm_worker` tạo một bản tin NotebookLM mỗi ngày. Nó chạy tách khỏi `osint_worker`, là nơi xử lý Telegram, signal extraction và các tác vụ dùng LLM.

Lịch chạy:

- 20:00 GMT+7: bản tin tổng hợp phiên Mỹ

Worker lưu một claim theo ngày trong PostgreSQL để chống tạo trùng cho job tự động. Nút tạo thủ công gọi endpoint POST và có thể tạo podcast ngoài lịch 20:00 GMT+7.

Các file `.m4a` được lưu trong `static/podcasts` và xuất hiện cùng podcast Edge-TTS hiện tại.
API trạng thái gọi vào `notebooklm_worker:8082`; endpoint POST được dùng cho nút tạo thủ công, còn job tự động lúc 20:00 GMT+7 vẫn bị giới hạn một lần mỗi ngày.

## Cấu hình server

1. Cài `notebooklm-py` trong image worker thông qua `requirements.txt`.
2. Đặt các biến sau trong `osint_ai_worker/.env`:

```env
NOTEBOOKLM_PODCAST_ENABLED=true
NOTEBOOKLM_NOTEBOOK=6216025a-b47e-4aeb-92db-57be9f8dddc3
NOTEBOOKLM_STORAGE=/app/notebooklm/storage_state.json
NOTEBOOKLM_PROFILE=default
NOTEBOOKLM_SOURCE_DAYS=2
```

3. Đặt file xác thực NotebookLM của đúng Google account tại:

```text
osint_ai_worker/notebooklm/storage_state.json
```

Có thể lấy file này từ profile local đã đăng nhập hoặc đăng nhập NotebookLM trên server theo hướng dẫn của `notebooklm-py`. Không commit file này vào Git.

4. Deploy lại worker:

```bash
./deploy.sh
```

Job sẽ tự bỏ qua khi `NOTEBOOKLM_PODCAST_ENABLED=false`. Lỗi NotebookLM chỉ được ghi log và không làm dừng các job OSINT hoặc podcast Edge-TTS hiện tại.