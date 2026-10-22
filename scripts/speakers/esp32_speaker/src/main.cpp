// ============================================================================
//  Trading Alert Speaker — ESP32-S3 (N16R8) + loa I2S + OLED 0.96" SSD1306
//  Nghe cảnh báo từ ntfy và đọc to bằng tiếng Việt (Google TTS), hiện lên màn hình.
//
//  - Lần đầu cắm điện: thiết bị phát Wi-Fi "TradingAlert-Setup" → điện thoại kết nối,
//    trang cài đặt tự mở (hoặc vào 192.168.4.1) → chọn Wi-Fi nhà + cấu hình ntfy.
//  - Đã có Wi-Fi: vào http://<IP-thiết-bị>/ để đổi cấu hình (ntfy, âm lượng, chân cắm).
//  - Nút BOOT: bấm nhanh = đọc lại tin cuối; giữ 5 giây = xoá Wi-Fi, vào chế độ cài đặt.
//  - Thử loa: http://<IP>/say?text=xin%20chao
// ============================================================================
#include <Arduino.h>
#include <ArduinoJson.h>
#include <LittleFS.h>
#include <Preferences.h>
#include <U8g2lib.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <WiFiManager.h>
#include <Wire.h>
#include <time.h>

#include <algorithm>
#include <deque>
#include <memory>
#include <string>
#include <vector>

#include "Audio.h"
#include "text_vi.h"

#define FW_VERSION "1.1.0"
static const char* AP_NAME = "TradingAlert-Setup";
static const char* HOSTNAME = "trading-alert";
static const int BOOT_BUTTON = 0;

// ───────────────────────── Cấu hình (lưu trong NVS) ─────────────────────────

struct Config {
    String server = "http://152.53.208.182:8088";
    String topic = "trading_signals_alerts";
    String token = "";
    int volume = 16;  // 0..21
    bool chime = true;
    bool announce = true;
    int maxAge = 300;  // bỏ tin cũ hơn N giây (khi vừa kết nối lại)
    // Chân cắm — mặc định theo mạch "xiaozhi bread-compact" (ESP32-S3 + loa I2S + OLED I2C)
    int spkBclk = 15, spkLrck = 16, spkDout = 7;
    int oledSda = 41, oledScl = 42;  // -1 = tự dò
    int oledType = 0;                // 0 = SSD1306, 1 = SH1106, 2 = không có màn hình
    bool oledFlip = true;            // xoay màn hình 180°
    int screenOffMin = 5;            // tắt màn hình sau N phút không có tin (0 = luôn sáng)
    int btnVolUp = 40, btnVolDown = 39;  // -1 = không dùng
} cfg;

Preferences prefs;

static void loadConfig() {
    prefs.begin("talert", true);
    cfg.server = prefs.getString("server", cfg.server);
    cfg.topic = prefs.getString("topic", cfg.topic);
    cfg.token = prefs.getString("token", cfg.token);
    cfg.volume = prefs.getInt("volume", cfg.volume);
    cfg.chime = prefs.getBool("chime", cfg.chime);
    cfg.announce = prefs.getBool("announce", cfg.announce);
    cfg.maxAge = prefs.getInt("maxage", cfg.maxAge);
    cfg.spkBclk = prefs.getInt("bclk", cfg.spkBclk);
    cfg.spkLrck = prefs.getInt("lrck", cfg.spkLrck);
    cfg.spkDout = prefs.getInt("dout", cfg.spkDout);
    cfg.oledSda = prefs.getInt("sda", cfg.oledSda);
    cfg.oledScl = prefs.getInt("scl", cfg.oledScl);
    cfg.oledType = prefs.getInt("oledtype", cfg.oledType);
    cfg.oledFlip = prefs.getBool("oledflip", cfg.oledFlip);
    cfg.screenOffMin = prefs.getInt("screenoff", cfg.screenOffMin);
    cfg.btnVolUp = prefs.getInt("volup", cfg.btnVolUp);
    cfg.btnVolDown = prefs.getInt("voldn", cfg.btnVolDown);
    prefs.end();
    cfg.volume = constrain(cfg.volume, 0, 21);
}

static void saveConfig() {
    prefs.begin("talert", false);
    prefs.putString("server", cfg.server);
    prefs.putString("topic", cfg.topic);
    prefs.putString("token", cfg.token);
    prefs.putInt("volume", cfg.volume);
    prefs.putBool("chime", cfg.chime);
    prefs.putBool("announce", cfg.announce);
    prefs.putInt("maxage", cfg.maxAge);
    prefs.putInt("bclk", cfg.spkBclk);
    prefs.putInt("lrck", cfg.spkLrck);
    prefs.putInt("dout", cfg.spkDout);
    prefs.putInt("sda", cfg.oledSda);
    prefs.putInt("scl", cfg.oledScl);
    prefs.putInt("oledtype", cfg.oledType);
    prefs.putBool("oledflip", cfg.oledFlip);
    prefs.putInt("screenoff", cfg.screenOffMin);
    prefs.putInt("volup", cfg.btnVolUp);
    prefs.putInt("voldn", cfg.btnVolDown);
    prefs.end();
}

static void saveVolume() {
    prefs.begin("talert", false);
    prefs.putInt("volume", cfg.volume);
    prefs.end();
}

// ───────────────────────── Màn hình OLED ─────────────────────────

U8G2* oled = nullptr;
static const int LINE_H = 16;  // font unifont cao 16px → 4 dòng trên màn 128x64

static bool i2cHasOled(int sda, int scl) {
    if (sda < 0 || scl < 0) return false;
    Wire.begin(sda, scl);
    bool found = false;
    for (uint8_t addr : {0x3C, 0x3D}) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) { found = true; break; }
    }
    Wire.end();
    return found;
}

static void setupDisplay() {
    if (cfg.oledType == 2) return;
    int sda = cfg.oledSda, scl = cfg.oledScl;
    if (!i2cHasOled(sda, scl)) {
        // Tự dò các cặp chân I2C hay gặp (bỏ qua chân Flash/PSRAM 26-37, USB 19/20, BOOT 0)
        static const int pairs[][2] = {{41, 42}, {42, 41}, {4, 5}, {5, 4}, {8, 9}, {9, 8}, {17, 18}, {18, 17},
                                       {1, 2}, {2, 1}, {21, 47}, {47, 21}, {38, 39}, {39, 38}, {11, 12}, {12, 11},
                                       {13, 14}, {14, 13}, {10, 11}, {6, 7}, {7, 6}, {45, 46}, {47, 48}, {48, 47}};
        sda = scl = -1;
        for (auto& p : pairs) {
            // không đụng tới chân loa đã cấu hình
            if (p[0] == cfg.spkBclk || p[0] == cfg.spkLrck || p[0] == cfg.spkDout || p[1] == cfg.spkBclk ||
                p[1] == cfg.spkLrck || p[1] == cfg.spkDout)
                continue;
            if (i2cHasOled(p[0], p[1])) { sda = p[0]; scl = p[1]; break; }
        }
        if (sda < 0) {
            Serial.println("[OLED] Không tìm thấy màn hình I2C (0x3C/0x3D)");
            return;
        }
        Serial.printf("[OLED] Tự dò được màn hình: SDA=%d SCL=%d\n", sda, scl);
    }
    const u8g2_cb_t* rot = cfg.oledFlip ? U8G2_R2 : U8G2_R0;
    if (cfg.oledType == 1)
        oled = new U8G2_SH1106_128X64_NONAME_F_HW_I2C(rot, U8X8_PIN_NONE, scl, sda);
    else
        oled = new U8G2_SSD1306_128X64_NONAME_F_HW_I2C(rot, U8X8_PIN_NONE, scl, sda);
    oled->begin();
    oled->enableUTF8Print();
    oled->setFont(u8g2_font_unifont_t_vietnamese2);
    oled->setFontPosBottom();
}

// Ngắt dòng theo độ rộng pixel (giữ nguyên tiếng Việt có dấu)
static std::vector<String> wrapText(const String& text, size_t maxLines) {
    std::vector<String> lines;
    if (!oled) return lines;
    String cur;
    int i = 0, n = text.length();
    while (i < n && lines.size() < maxLines) {
        int j = text.indexOf(' ', i);
        if (j < 0) j = n;
        String word = text.substring(i, j);
        String cand = cur.length() ? cur + " " + word : word;
        if (oled->getUTF8Width(cand.c_str()) <= 128) {
            cur = cand;
        } else {
            if (cur.length()) lines.push_back(cur);
            cur = word;
            // từ quá dài (VD mã dài) → cắt cứng theo ký tự
            while (oled->getUTF8Width(cur.c_str()) > 128 && lines.size() < maxLines) {
                int cut = cur.length();
                while (cut > 1 && oled->getUTF8Width(cur.substring(0, cut).c_str()) > 128) {
                    cut--;
                    while (cut > 1 && (cur[cut] & 0xC0) == 0x80) cut--;  // không cắt giữa ký tự UTF-8
                }
                lines.push_back(cur.substring(0, cut));
                cur = cur.substring(cut);
            }
        }
        i = j + 1;
    }
    if (cur.length() && lines.size() < maxLines) lines.push_back(cur);
    return lines;
}

bool screenOff = false;  // màn hình đang nghỉ (tắt hẳn)
bool idleScreenRedraw = false;  // vẽ lại màn hình chờ ngay ở vòng lặp tới

static void screenWake() {
    if (oled && screenOff) {
        oled->setPowerSave(0);
        Serial.println("[MÀN HÌNH] Bật lại");
    }
    screenOff = false;
}

static void screenSleep() {
    if (oled && !screenOff) {
        oled->clearDisplay();
        oled->setPowerSave(1);
        Serial.println("[MÀN HÌNH] Nghỉ (tắt) — bấm BOOT hoặc có tin mới sẽ bật lại");
    }
    screenOff = true;
}

static void drawLines(const std::vector<String>& lines, bool invertFirst = false) {
    if (!oled) return;
    screenWake();
    oled->setContrast(255);
    oled->clearBuffer();
    for (size_t k = 0; k < lines.size() && k < 4; k++) {
        int y = (k + 1) * LINE_H;
        if (k == 0 && invertFirst) {
            oled->drawBox(0, 0, 128, LINE_H);
            oled->setDrawColor(0);
            oled->drawUTF8(0, y, lines[k].c_str());
            oled->setDrawColor(1);
        } else {
            oled->drawUTF8(0, y, lines[k].c_str());
        }
    }
    oled->sendBuffer();
}

static void showStatus(const String& a, const String& b = "", const String& c = "", const String& d = "") {
    Serial.printf("[MÀN HÌNH] %s | %s | %s | %s\n", a.c_str(), b.c_str(), c.c_str(), d.c_str());
    drawLines({a, b, c, d}, true);
}

// ───────────────────────── Âm thanh ─────────────────────────

Audio audio;

// Tạo tiếng chuông WAV (mono 16-bit 22.05 kHz) vào LittleFS, giống tiếng chuông trên Raspberry Pi
static void buildChime(const char* path, bool urgent) {
    if (LittleFS.exists(path)) return;
    const int sr = 22050;
    std::vector<std::pair<float, float>> notes;  // (tần số, giây)
    if (urgent) notes = {{988, 0.14f}, {0, 0.06f}, {988, 0.14f}, {0, 0.06f}, {988, 0.14f}, {0, 0.06f}, {1319, 0.30f}};
    else notes = {{880, 0.12f}, {1319, 0.22f}};
    std::vector<int16_t> pcm;
    for (auto& nt : notes) {
        int len = (int)(nt.second * sr);
        for (int i = 0; i < len; i++) {
            float env = 1.0f;
            int fade = sr / 100;  // 10ms fade in/out để không bị "bụp"
            if (i < fade) env = (float)i / fade;
            if (len - i < fade) env = (float)(len - i) / fade;
            float v = nt.first > 0 ? sinf(2.0f * PI * nt.first * i / sr) * 0.45f * env : 0.0f;
            pcm.push_back((int16_t)(v * 32767));
        }
    }
    File f = LittleFS.open(path, "w");
    if (!f) return;
    uint32_t dataLen = pcm.size() * 2, riffLen = 36 + dataLen, byteRate = sr * 2, sr32 = sr;
    uint16_t fmt = 1, ch = 1, align = 2, bits = 16;
    uint32_t fmtLen = 16;
    f.write((const uint8_t*)"RIFF", 4); f.write((uint8_t*)&riffLen, 4); f.write((const uint8_t*)"WAVEfmt ", 8);
    f.write((uint8_t*)&fmtLen, 4); f.write((uint8_t*)&fmt, 2); f.write((uint8_t*)&ch, 2); f.write((uint8_t*)&sr32, 4);
    f.write((uint8_t*)&byteRate, 4); f.write((uint8_t*)&align, 2); f.write((uint8_t*)&bits, 2);
    f.write((const uint8_t*)"data", 4); f.write((uint8_t*)&dataLen, 4);
    f.write((const uint8_t*)pcm.data(), dataLen);
    f.close();
}

static void audioInfo(Audio::msg_t m) {
    if (m.e == Audio::evt_info || m.e == Audio::evt_eof || m.e == Audio::evt_log)
        Serial.printf("[AUDIO] %s: %s\n", m.s ? m.s : "", m.msg ? m.msg : "");
}

// ───────────────────────── Hàng đợi đọc tin ─────────────────────────

struct Alert {
    String title, message;
    int priority = 3;
};

std::deque<Alert> alertQueue;
Alert lastAlert;
bool hasLastAlert = false;

enum PlayState { IDLE, PLAY_CHIME, PLAY_SPEECH };
PlayState playState = IDLE;
std::vector<std::string> chunks;
size_t chunkIdx = 0;
uint32_t stepStartedMs = 0;
uint32_t lastActivityMs = 0;
String lastShownTitle;

static void enqueueAlert(const Alert& a) {
    while (alertQueue.size() >= 10) {
        Serial.println("[QUEUE] Hàng đợi đầy — bỏ tin cũ nhất");
        alertQueue.pop_front();
    }
    alertQueue.push_back(a);
}

static void enqueueSpeech(const String& text) {
    Alert a;
    a.message = text;
    a.priority = 3;
    enqueueAlert(a);
}

static void showAlert(const Alert& a) {
    String title = textvi::cleanForDisplay(a.title.c_str()).c_str();
    String body = textvi::cleanForDisplay(a.message.c_str()).c_str();
    std::vector<String> lines;
    if (title.length()) {
        lines = wrapText(title, 2);
        for (auto& l : wrapText(body, 4 - lines.size())) lines.push_back(l);
    } else {
        lines = wrapText(body, 4);
    }
    drawLines(lines, title.length() > 0);
    lastShownTitle = title;
}

bool chunkRetried = false;   // đã thử đường dự phòng (HTTPS) cho đoạn hiện tại chưa
bool useHttpsTts = false;    // nhớ lại nếu đường HTTP (cổng 80) của Google không dùng được

static bool connectTts(const std::string& c, bool https) {
    if (!https) return audio.connecttospeech(c.c_str(), "vi");
    std::string url = "https://translate.google.com/translate_tts?ie=UTF-8&tl=vi&client=tw-ob&q=" + textvi::urlEncode(c);
    return audio.connecttohost(url.c_str());
}

static bool startChunk() {
    while (chunkIdx < chunks.size()) {
        const std::string& c = chunks[chunkIdx];
        Serial.printf("[TTS] (%u/%u) %s\n", (unsigned)(chunkIdx + 1), (unsigned)chunks.size(), c.c_str());
        stepStartedMs = millis();
        chunkRetried = false;
        if (connectTts(c, useHttpsTts)) return true;
        if (connectTts(c, !useHttpsTts)) { useHttpsTts = !useHttpsTts; chunkRetried = true; return true; }
        Serial.println("[TTS] Lỗi kết nối Google TTS — bỏ đoạn này");
        chunkIdx++;
    }
    return false;
}

static void startAlert(const Alert& a) {
    showAlert(a);
    std::string text = textvi::toSpeechText(a.title.c_str(), a.message.c_str());
    chunks = textvi::splitChunks(text, 180);
    chunkIdx = 0;
    lastActivityMs = millis();
    Serial.printf("[ĐỌC] %s\n", text.c_str());
    if (cfg.chime && LittleFS.exists("/chime.wav")) {
        stepStartedMs = millis();
        if (audio.connecttoFS(LittleFS, a.priority >= 5 ? "/chime_urgent.wav" : "/chime.wav")) {
            playState = PLAY_CHIME;
            return;
        }
    }
    playState = startChunk() ? PLAY_SPEECH : IDLE;
}

static void playerLoop() {
    uint32_t now = millis();
    switch (playState) {
        case IDLE:
            if (!alertQueue.empty()) {
                Alert a = alertQueue.front();
                alertQueue.pop_front();
                startAlert(a);
            }
            break;
        case PLAY_CHIME:
            if (!audio.isRunning() || now - stepStartedMs > 5000) {
                if (audio.isRunning()) audio.stopSong();
                playState = startChunk() ? PLAY_SPEECH : IDLE;
            }
            break;
        case PLAY_SPEECH:
            if (!audio.isRunning() && now - stepStartedMs < 1500 && !chunkRetried && chunkIdx < chunks.size()) {
                // Dừng gần như ngay lập tức = Google không trả âm thanh → thử đường còn lại (HTTP ↔ HTTPS)
                Serial.println("[TTS] Không nhận được âm thanh — thử lại qua đường dự phòng");
                chunkRetried = true;
                stepStartedMs = now;
                if (connectTts(chunks[chunkIdx], !useHttpsTts)) { useHttpsTts = !useHttpsTts; break; }
            }
            if (!audio.isRunning() || now - stepStartedMs > 30000) {
                if (audio.isRunning()) audio.stopSong();
                chunkIdx++;
                if (!startChunk()) {
                    playState = IDLE;
                    lastActivityMs = millis();
                }
            }
            break;
    }
}

// ───────────────────────── Nghe ntfy (HTTP stream) ─────────────────────────

struct NtfyStream {
    std::unique_ptr<WiFiClient> client;
    enum { DISCONNECTED, HEADERS, BODY } state = DISCONNECTED;
    String line, lastId;
    uint32_t lastDataMs = 0, nextTryMs = 0, backoffMs = 2000;
    bool everConnected = false, announced = false;
    std::deque<String> seenIds;

    bool parseUrl(String& host, uint16_t& port, String& basePath, bool& tls) {
        String u = cfg.server;
        u.trim();
        tls = u.startsWith("https://");
        if (u.startsWith("http://")) u = u.substring(7);
        else if (tls) u = u.substring(8);
        int slash = u.indexOf('/');
        basePath = slash >= 0 ? u.substring(slash) : "";
        if (basePath.endsWith("/")) basePath.remove(basePath.length() - 1);
        String hp = slash >= 0 ? u.substring(0, slash) : u;
        int colon = hp.indexOf(':');
        host = colon >= 0 ? hp.substring(0, colon) : hp;
        port = colon >= 0 ? hp.substring(colon + 1).toInt() : (tls ? 443 : 80);
        return host.length() > 0;
    }

    void scheduleRetry(const char* why) {
        Serial.printf("[NTFY] %s — thử lại sau %lus\n", why, (unsigned long)(backoffMs / 1000));
        if (client) client->stop();
        state = DISCONNECTED;
        nextTryMs = millis() + backoffMs;
        backoffMs = std::min<uint32_t>(backoffMs * 2, 60000);
    }

    void connect() {
        String host, basePath;
        uint16_t port;
        bool tls;
        if (!parseUrl(host, port, basePath, tls)) { scheduleRetry("Địa chỉ server ntfy không hợp lệ"); return; }
        if (tls) {
            auto* sc = new WiFiClientSecure();
            sc->setInsecure();  // ntfy tự host thường dùng chứng chỉ tự ký
            client.reset(sc);
        } else {
            client.reset(new WiFiClient());
        }
        client->setTimeout(5);
        Serial.printf("[NTFY] Kết nối %s:%u%s/%s/json\n", host.c_str(), port, basePath.c_str(), cfg.topic.c_str());
        if (!client->connect(host.c_str(), port, 5000)) { scheduleRetry("Không kết nối được server ntfy"); return; }
        String path = basePath + "/" + cfg.topic + "/json";
        if (lastId.length()) path += String("?since=") + lastId;
        // HTTP/1.0 → server trả luồng thường (không chunked), mỗi dòng là 1 sự kiện JSON
        String req = String("GET ") + path + " HTTP/1.0\r\nHost: " + host + "\r\nUser-Agent: TradingAlert-ESP32/" FW_VERSION "\r\n";
        if (cfg.token.length()) req += String("Authorization: Bearer ") + cfg.token + "\r\n";
        req += "\r\n";
        client->print(req);
        state = HEADERS;
        line = "";
        lastDataMs = millis();
    }

    void handleLine(const String& l) {
        if (state == HEADERS) {
            if (l.startsWith("HTTP/")) {
                int code = l.substring(9, 12).toInt();
                if (code == 401 || code == 403) { backoffMs = 60000; scheduleRetry("ntfy từ chối (sai token / không có quyền đọc topic)"); }
                else if (code != 200) scheduleRetry((String("ntfy trả lỗi HTTP ") + String(code)).c_str());
            } else if (l.length() == 0) {
                state = BODY;
            }
            return;
        }
        if (l.length() == 0) return;
        JsonDocument doc;
        if (deserializeJson(doc, l)) return;
        const char* ev = doc["event"] | "";
        if (!strcmp(ev, "open")) {
            backoffMs = 2000;
            everConnected = true;
            Serial.println("[NTFY] ✅ Đang nghe cảnh báo...");
            showStatus("Trading Alert", "Đang nghe...", WiFi.localIP().toString(), "");
            if (cfg.announce && !announced) {
                announced = true;
                enqueueSpeech("Hệ thống đọc cảnh báo Trading Signals đã sẵn sàng.");
            }
            return;
        }
        if (strcmp(ev, "message")) return;  // keepalive, poll_request...
        String id = doc["id"] | "";
        if (id.length()) {
            lastId = id;
            for (auto& s : seenIds)
                if (s == id) return;
            seenIds.push_back(id);
            if (seenIds.size() > 50) seenIds.pop_front();
        }
        time_t evTime = (time_t)doc["time"].as<long long>();
        time_t now = time(nullptr);
        if (now > 1600000000 && evTime > 0 && now - evTime > cfg.maxAge) {
            Serial.printf("[NTFY] Bỏ tin cũ %lds\n", (long)(now - evTime));
            return;
        }
        Alert a;
        a.title = (const char*)(doc["title"] | "");
        a.message = (const char*)(doc["message"] | "");
        a.priority = doc["priority"] | 3;
        Serial.printf("[NTFY] 📩 %s | %s\n", a.title.c_str(), a.message.c_str());
        lastAlert = a;
        hasLastAlert = true;
        enqueueAlert(a);
    }

    void loop() {
        if (WiFi.status() != WL_CONNECTED) {
            if (state != DISCONNECTED) { if (client) client->stop(); state = DISCONNECTED; }
            return;
        }
        uint32_t now = millis();
        if (state == DISCONNECTED) {
            if ((int32_t)(now - nextTryMs) >= 0) connect();
            return;
        }
        int budget = 2048;  // đọc tối đa N byte mỗi vòng để không làm nghẽn âm thanh
        while (client->available() && budget-- > 0) {
            char c = client->read();
            lastDataMs = now;
            if (c == '\r') continue;
            if (c == '\n') {
                String l = line;
                line = "";
                handleLine(l);
                if (state == DISCONNECTED) return;
            } else if (line.length() < 8192) {
                line += c;
            }
        }
        if (!client->connected() && !client->available()) { scheduleRetry("Mất kết nối ntfy"); return; }
        // ntfy gửi keepalive ~45s/lần; im lặng quá 100s → coi như rớt kết nối
        if (now - lastDataMs > 100000) scheduleRetry("Không nhận được keepalive");
    }
} ntfy;

// ───────────────────────── Wi-Fi + trang cài đặt ─────────────────────────

WiFiManager wm;
std::vector<std::unique_ptr<WiFiManagerParameter>> params;
WiFiManagerParameter *pServer, *pTopic, *pToken, *pVolume, *pChime, *pAnnounce, *pBclk, *pLrck, *pDout, *pSda, *pScl,
    *pOledType, *pOledFlip, *pVolUp, *pVolDn, *pScreenOff;
bool restartPending = false;

static WiFiManagerParameter* addParam(const char* id, const char* label, const String& value, int len) {
    params.emplace_back(new WiFiManagerParameter(id, label, value.c_str(), len));
    wm.addParameter(params.back().get());
    return params.back().get();
}

static int paramInt(WiFiManagerParameter* p, int def) {
    String v = p->getValue();
    v.trim();
    if (!v.length()) return def;
    return v.toInt();
}

static void onSaveParams() {
    cfg.server = pServer->getValue(); cfg.server.trim();
    cfg.topic = pTopic->getValue(); cfg.topic.trim();
    cfg.token = pToken->getValue(); cfg.token.trim();
    cfg.volume = constrain(paramInt(pVolume, cfg.volume), 0, 21);
    cfg.chime = paramInt(pChime, 1) != 0;
    cfg.announce = paramInt(pAnnounce, 1) != 0;
    cfg.spkBclk = paramInt(pBclk, cfg.spkBclk);
    cfg.spkLrck = paramInt(pLrck, cfg.spkLrck);
    cfg.spkDout = paramInt(pDout, cfg.spkDout);
    cfg.oledSda = paramInt(pSda, cfg.oledSda);
    cfg.oledScl = paramInt(pScl, cfg.oledScl);
    cfg.oledType = constrain(paramInt(pOledType, cfg.oledType), 0, 2);
    cfg.oledFlip = paramInt(pOledFlip, 1) != 0;
    cfg.screenOffMin = max(0, paramInt(pScreenOff, cfg.screenOffMin));
    cfg.btnVolUp = paramInt(pVolUp, cfg.btnVolUp);
    cfg.btnVolDown = paramInt(pVolDn, cfg.btnVolDown);
    saveConfig();
    Serial.println("[CÀI ĐẶT] Đã lưu cấu hình — khởi động lại để áp dụng");
    restartPending = true;
}

static void setupWebRoutes() {
    // Thử loa: http://<IP>/say?text=xin chao
    wm.server->on("/say", [] {
        String t = wm.server->arg("text");
        if (!t.length()) t = "Xin chào, đây là thiết bị đọc cảnh báo Trading Signals.";
        enqueueSpeech(t);
        wm.server->send(200, "text/plain; charset=utf-8", String("OK: ") + t);
    });
    wm.server->on("/status", [] {
        String s = String("Trading Alert " FW_VERSION "\nIP: ") + WiFi.localIP().toString() + "\nntfy: " + cfg.server + "/" +
                   cfg.topic + "\nĐang nghe: " + String(ntfy.state == NtfyStream::BODY ? "có" : "không") +
                   "\nÂm lượng: " + String(cfg.volume) + "/21\nTin chờ đọc: " + String(alertQueue.size()) + "\n";
        wm.server->send(200, "text/plain; charset=utf-8", s);
    });
}

static void setupWifi() {
    WiFi.mode(WIFI_STA);
    wm.setHostname(HOSTNAME);
    wm.setTitle("Trading Alert");
    wm.setDarkMode(true);
    wm.setConnectTimeout(20);
    wm.setSaveParamsCallback(onSaveParams);
    wm.setWebServerCallback(setupWebRoutes);
    std::vector<const char*> menu = {"wifi", "param", "info", "update", "restart"};  // "update" = nạp firmware mới qua Wi-Fi
    wm.setMenu(menu);

    pServer = addParam("server", "Server ntfy (VD http://IP:8088)", cfg.server, 120);
    pTopic = addParam("topic", "Topic", cfg.topic, 64);
    pToken = addParam("token", "Token ntfy (để trống nếu không có)", cfg.token, 80);
    pVolume = addParam("volume", "Âm lượng 0-21", String(cfg.volume), 3);
    pChime = addParam("chime", "Tiếng chuông trước khi đọc (1/0)", String(cfg.chime ? 1 : 0), 2);
    pAnnounce = addParam("announce", "Đọc 'đã sẵn sàng' khi khởi động (1/0)", String(cfg.announce ? 1 : 0), 2);
    pBclk = addParam("bclk", "Chân loa I2S BCLK", String(cfg.spkBclk), 3);
    pLrck = addParam("lrck", "Chân loa I2S LRCK/WS", String(cfg.spkLrck), 3);
    pDout = addParam("dout", "Chân loa I2S DOUT/DIN", String(cfg.spkDout), 3);
    pSda = addParam("sda", "Chân OLED SDA (-1 = tự dò)", String(cfg.oledSda), 3);
    pScl = addParam("scl", "Chân OLED SCL (-1 = tự dò)", String(cfg.oledScl), 3);
    pOledType = addParam("oledtype", "Màn hình: 0=SSD1306, 1=SH1106, 2=không có", String(cfg.oledType), 2);
    pOledFlip = addParam("oledflip", "Xoay màn hình 180° (1/0)", String(cfg.oledFlip ? 1 : 0), 2);
    pScreenOff = addParam("screenoff", "Tắt màn hình sau N phút không có tin (0 = luôn sáng)", String(cfg.screenOffMin), 4);
    pVolUp = addParam("volup", "Chân nút tăng âm lượng (-1 = không có)", String(cfg.btnVolUp), 3);
    pVolDn = addParam("voldn", "Chân nút giảm âm lượng (-1 = không có)", String(cfg.btnVolDown), 3);

    wm.setAPCallback([](WiFiManager*) {
        Serial.printf("[WIFI] Chế độ cài đặt: kết nối Wi-Fi \"%s\" rồi mở 192.168.4.1\n", AP_NAME);
        showStatus("CÀI ĐẶT WI-FI", "Kết nối Wi-Fi:", AP_NAME, "→ 192.168.4.1");
    });
    showStatus("Trading Alert", "Đang kết nối", "Wi-Fi...", "v" FW_VERSION);
    wm.setConfigPortalBlocking(true);
    wm.setConfigPortalTimeout(0);  // chờ đến khi cài xong
    if (!wm.autoConnect(AP_NAME)) {
        showStatus("Lỗi Wi-Fi", "Khởi động lại...", "", "");
        delay(2000);
        ESP.restart();
    }
    if (restartPending) {  // vừa lưu cấu hình trong trang cài đặt lần đầu
        delay(500);
        ESP.restart();
    }
    Serial.printf("[WIFI] Đã kết nối %s, IP %s\n", WiFi.SSID().c_str(), WiFi.localIP().toString().c_str());
    WiFi.setSleep(false);  // tắt tiết kiệm điện Wi-Fi → luồng âm thanh/ntfy ổn định hơn
    wm.setConfigPortalBlocking(false);
    wm.startWebPortal();  // trang cài đặt vẫn mở ở http://<IP>/
}

// ───────────────────────── Nút bấm ─────────────────────────

struct Button {
    int pin = -1;
    bool last = true;
    uint32_t downMs = 0;
    bool longFired = false;
    void begin(int p) {
        pin = p;
        if (pin >= 0) pinMode(pin, INPUT_PULLUP);
    }
    // trả về: 0 = không có gì, 1 = bấm nhanh, 2 = giữ lâu (5s)
    int poll() {
        if (pin < 0) return 0;
        bool v = digitalRead(pin);
        uint32_t now = millis();
        int res = 0;
        if (!v && last) { downMs = now; longFired = false; }
        if (!v && !longFired && now - downMs > 5000) { longFired = true; res = 2; }
        if (v && !last && !longFired && now - downMs > 30) res = 1;
        last = v;
        return res;
    }
} btnBoot, btnUp, btnDown;

static void changeVolume(int delta) {
    cfg.volume = constrain(cfg.volume + delta, 0, 21);
    audio.setVolume(cfg.volume);
    saveVolume();
    showStatus("Âm lượng", String(cfg.volume) + " / 21", "", "");
    lastActivityMs = millis();
}

static void buttonsLoop() {
    int b = btnBoot.poll();
    if (b == 1 && screenOff) {  // màn hình đang nghỉ → lần bấm đầu chỉ để bật màn hình
        lastActivityMs = millis();  // tính lại thời gian chờ trước khi nghỉ
        idleScreenRedraw = true;
        screenWake();
        b = 0;
    }
    if (b == 1) {
        if (playState != IDLE) {  // đang đọc → bấm để dừng
            audio.stopSong();
            chunks.clear();
            playState = IDLE;
        } else if (hasLastAlert) {
            enqueueAlert(lastAlert);  // đọc lại tin cuối
        } else {
            enqueueSpeech("Chưa có cảnh báo nào.");
        }
    } else if (b == 2) {
        showStatus("XOÁ WI-FI", "Khởi động lại", "để cài đặt mới", "");
        wm.resetSettings();
        delay(1500);
        ESP.restart();
    }
    if (btnUp.poll() == 1) changeVolume(+1);
    if (btnDown.poll() == 1) changeVolume(-1);
}

// ───────────────────────── Màn hình chờ ─────────────────────────

static void idleScreenLoop() {
    static uint32_t lastDraw = 0;
    uint32_t now = millis();
    if (playState != IDLE || !alertQueue.empty()) return;
    if (!idleScreenRedraw && now - lastActivityMs < 60000) return;  // giữ tin vừa đọc trên màn hình 60 giây
    bool connected = WiFi.status() == WL_CONNECTED && ntfy.state == NtfyStream::BODY;
    // Nghỉ màn hình khi đang nghe bình thường mà lâu không có tin.
    // Mất Wi-Fi / ntfy thì vẫn để sáng (mờ) để bạn nhìn thấy lỗi.
    if (cfg.screenOffMin > 0 && connected && now - lastActivityMs > (uint32_t)cfg.screenOffMin * 60000UL) {
        screenSleep();
        return;
    }
    if (screenOff && !connected) idleScreenRedraw = true;  // vừa mất kết nối → bật lại để báo
    if (!idleScreenRedraw && now - lastDraw < 30000 && lastDraw != 0) return;
    if (screenOff && !idleScreenRedraw) return;
    idleScreenRedraw = false;
    lastDraw = now;
    struct tm t;
    char clock[8] = "--:--";
    if (getLocalTime(&t, 10)) strftime(clock, sizeof(clock), "%H:%M", &t);
    String st = ntfy.state == NtfyStream::BODY ? "Đang nghe..." : "Mất kết nối ntfy";
    if (WiFi.status() != WL_CONNECTED) st = "Mất Wi-Fi";
    String last = hasLastAlert ? textvi::cleanForDisplay(lastAlert.title.c_str()).c_str() : String("");
    std::vector<String> lines = {String("Trading  ") + clock, st, WiFi.localIP().toString()};
    if (last.length()) {
        auto w = wrapText(String("Cuối: ") + last, 1);
        if (!w.empty()) lines.push_back(w[0]);
    }
    drawLines(lines, true);
    if (oled) oled->setContrast(20);  // màn hình chờ: giảm sáng để OLED bền hơn
}

// ───────────────────────── setup / loop ─────────────────────────

void setup() {
    Serial.begin(115200);
    delay(300);
    Serial.println("\n=== Trading Alert Speaker " FW_VERSION " ===");
    Serial.printf("PSRAM: %u bytes\n", (unsigned)ESP.getPsramSize());
    loadConfig();
    setupDisplay();
    showStatus("Trading Alert", "Đang khởi động", "v" FW_VERSION, "");

    if (!LittleFS.begin(true)) Serial.println("[FS] Không mở được LittleFS — tắt tiếng chuông");
    else {
        buildChime("/chime.wav", false);
        buildChime("/chime_urgent.wav", true);
    }

    Audio::audio_info_callback = audioInfo;
    Serial.printf("[LOA] I2S BCLK=%d LRCK=%d DOUT=%d, âm lượng %d/21\n", cfg.spkBclk, cfg.spkLrck, cfg.spkDout, cfg.volume);
    audio.setPinout(cfg.spkBclk, cfg.spkLrck, cfg.spkDout);
    audio.setVolume(cfg.volume);
    audio.forceMono(true);

    btnBoot.begin(BOOT_BUTTON);
    btnUp.begin(cfg.btnVolUp);
    btnDown.begin(cfg.btnVolDown);

    Serial.println("[WIFI] Khởi động Wi-Fi...");
    setupWifi();
    configTzTime("ICT-7", "pool.ntp.org", "time.google.com");  // giờ Việt Nam
    lastActivityMs = millis();
}

void loop() {
    audio.loop();
    wm.process();
    ntfy.loop();
    playerLoop();
    buttonsLoop();
    idleScreenLoop();
    if (restartPending) {
        showStatus("Đã lưu cài đặt", "Khởi động lại...", "", "");
        delay(1000);
        ESP.restart();
    }
    // Mất Wi-Fi lâu (VD router khởi động lại) → tự kết nối lại; quá 5 phút thì khởi động lại
    static uint32_t wifiLostMs = 0;
    if (WiFi.status() != WL_CONNECTED) {
        if (!wifiLostMs) { wifiLostMs = millis(); WiFi.reconnect(); }
        if (millis() - wifiLostMs > 300000) ESP.restart();
    } else {
        wifiLostMs = 0;
    }
    vTaskDelay(1);
}
