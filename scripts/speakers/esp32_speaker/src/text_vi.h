// Chuẩn hoá nội dung cảnh báo ntfy thành câu đọc tiếng Việt (port từ ntfy_speaker.py trên Raspberry Pi).
// Thuần C++ (std::string) để có thể test trên máy tính: xem test_host/.
#pragma once
#include <string>
#include <vector>

namespace textvi {

// Ghép tiêu đề + nội dung (bỏ tiêu đề nếu trùng ý), bỏ emoji/ngoặc, đọc số/tiền/% kiểu Việt:
//   "67,250.50$" → "67250 phẩy 5 đô la", "52,500đ" → "52500 đồng", "-1.5%" → "âm 1 phẩy 5 phần trăm",
//   "BTCUSDT" → "BTC USDT", "lần 2/3" → "lần 2 trên 3".
std::string toSpeechText(const std::string& title, const std::string& message, size_t maxChars = 350);

// Cắt câu dài thành nhiều đoạn ≤ maxChars ký tự (Google TTS giới hạn ~200 ký tự/lần).
std::vector<std::string> splitChunks(const std::string& text, size_t maxChars = 180);

// Bỏ ký hiệu ngoặc/emoji để hiện lên màn hình (giữ nguyên số).
std::string cleanForDisplay(const std::string& s);

size_t utf8Length(const std::string& s);

// Mã hoá URL (percent-encoding) cho tham số query.
std::string urlEncode(const std::string& s);

}  // namespace textvi
