#!/usr/bin/env python3
"""
ntfy_speaker.py — Raspberry Pi: nghe ntfy 24/24 và đọc cảnh báo bằng tiếng Việt qua loa
(Bluetooth hoặc jack 3.5mm).

Luồng: alert.py ──(ntfy)──► server ntfy ──(HTTP stream)──► Pi ──► chuông + giọng đọc tiếng Việt

Cấu hình qua biến môi trường (hoặc file .env cạnh script):
  NTFY_SERVER_URL   http://<IP-VPS>:8088            (bắt buộc)
  NTFY_TOPIC        trading_signals_alerts
  NTFY_TOKEN        (tuỳ chọn) access token nếu server ntfy bật xác thực
  TTS_ENGINES       gtts,espeak                     thứ tự thử: gtts (Google, cần internet) → espeak (offline)
  QUIET_HOURS       23:00-07:00                     (tuỳ chọn) giờ yên lặng: chỉ đọc tin khẩn (cắt lỗ, lỗi lệnh)
  MAX_AGE_SECONDS   300                             bỏ qua tin cũ hơn N giây (khi Pi vừa kết nối lại)
  CHIME             true                            phát tiếng chuông trước khi đọc
  AUDIO_PLAYER      (tự chọn) lệnh phát file wav/mp3, VD "paplay" hoặc "aplay"
  STARTUP_ANNOUNCE  true                            đọc "hệ thống đã sẵn sàng" khi khởi động (VD sau khi cắm điện lại)
  BT_SPEAKER_MAC    (tuỳ chọn) MAC loa Bluetooth, VD AA:BB:CC:DD:EE:FF — tự kết nối lại loa nếu loa đã ngủ
  BT_CHECK_SECONDS  60                              kiểm tra & kết nối lại loa Bluetooth mỗi N giây (chạy nền)
  DRY_RUN           false                           true = chỉ in ra màn hình, không phát âm thanh
"""

import json
import math
import os
import queue
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import wave
from datetime import datetime

import requests

# ───────────────────────── Cấu hình ─────────────────────────


def load_dotenv_file(path):
    """Đọc file .env đơn giản (KEY=VALUE) mà không cần thư viện python-dotenv."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_dotenv_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

SERVER = os.getenv("NTFY_SERVER_URL", "").rstrip("/")
TOPIC = os.getenv("NTFY_TOPIC", "trading_signals_alerts").strip()
TOKEN = os.getenv("NTFY_TOKEN", "").strip()
TTS_ENGINES = [e.strip().lower() for e in os.getenv("TTS_ENGINES", "gtts,espeak").split(",") if e.strip()]
QUIET_HOURS = os.getenv("QUIET_HOURS", "").strip()
MAX_AGE_SECONDS = int(os.getenv("MAX_AGE_SECONDS", "300"))
CHIME_ENABLED = os.getenv("CHIME", "true").lower() == "true"
AUDIO_PLAYER = os.getenv("AUDIO_PLAYER", "").strip()
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
BT_SPEAKER_MAC = os.getenv("BT_SPEAKER_MAC", "").strip()
STARTUP_ANNOUNCE = os.getenv("STARTUP_ANNOUNCE", "true").lower() == "true"
BT_CHECK_SECONDS = int(os.getenv("BT_CHECK_SECONDS", "60"))
MAX_QUEUE = 10          # tối đa số tin chờ đọc; nhiều hơn thì bỏ tin cũ nhất
MAX_SPEECH_CHARS = 350  # cắt bớt tin quá dài cho dễ nghe


def log(msg):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}", flush=True)


# ───────────────────── Chuẩn hoá văn bản để đọc ─────────────────────

_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0000FE0F\U0000200D\U00002B00-\U00002BFF\U000025A0-\U000025FF]+"
)
_QUOTE_SUFFIX_RE = re.compile(r"\b([A-Z0-9]{2,10})(USDT|USDC|BUSD|FDUSD)\b")


def _vn_number(m):
    """'1,234.56' → '1234 phẩy 56' ; '52,500' → '52500' (định dạng số tiếng Anh → cách đọc tiếng Việt)."""
    raw = m.group(0)
    int_part, _, dec_part = raw.partition(".")
    int_part = int_part.replace(",", "")
    dec_part = dec_part.rstrip("0")
    return f"{int_part} phẩy {dec_part}" if dec_part else int_part


def _title_is_redundant(title, message):
    """Tiêu đề ntfy thường lặp lại ý của nội dung → bỏ tiêu đề nếu phần lớn từ đã có trong nội dung."""
    words = re.findall(r"\w+", title.lower())
    if not words:
        return True
    body = set(re.findall(r"\w+", message.lower()))
    return sum(w in body for w in words) / len(words) >= 0.7


def to_speech_text(title, message):
    """Biến nội dung ntfy (có ký hiệu, emoji, số kiểu Anh) thành câu dễ đọc bằng tiếng Việt."""
    title, message = (title or "").strip(), (message or "").strip()
    if title and message and not _title_is_redundant(title, message):
        text = f"{title}. {message}"
    else:
        text = message or title
    text = _EMOJI_RE.sub(" ", text)
    text = text.replace("➔", " sang ").replace("→", " sang ").replace("|", ", ")
    text = re.sub(r"[\[\]\(\)\{\}<>*_#`~]", " ", text)
    # Tiền tệ: 617.42$ / $617.42 → 617.42 đô la ; 52,500đ → 52500 đồng ; 0.87% → 0.87 phần trăm
    num = r"(\d(?:[\d.,]*\d)?)"  # số không kết thúc bằng dấu chấm/phẩy của câu
    text = re.sub(num + r"\s*\$", r"\1 đô la", text)
    text = re.sub(r"\$\s*" + num, r"\1 đô la", text)
    text = text.replace("$", " đô la ")
    text = re.sub(num + r"\s*đ\b", r"\1 đồng", text)
    text = re.sub(num + r"\s*%", r"\1 phần trăm", text)
    # Dấu: -55.44 → âm 55.44 ; +0.87 → 0.87
    text = re.sub(r"(?<![\w.])-(?=\d)", "âm ", text)
    text = re.sub(r"(?<![\w.])\+(?=\d)", "", text)
    # Số định dạng tiếng Anh → tiếng Việt
    text = re.sub(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+", _vn_number, text)
    # BTCUSDT → BTC USDT ; mã có dạng EXCHANGE:SYMBOL → SYMBOL
    text = _QUOTE_SUFFIX_RE.sub(r"\1 \2", text)
    text = re.sub(r"\b[A-Z]+:([A-Z0-9]+)\b", r"\1", text)
    text = text.replace(" - ", ", ").replace("—", ", ").replace("–", ", ")
    # Dọn khoảng trắng / dấu câu thừa sau khi bỏ ngoặc
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,:;!?])", r"\1", text)
    text = re.sub(r"([.,:;])(?:\s*[.,:;])+", r"\1", text)
    text = text.strip(" .,:;")
    if len(text) > MAX_SPEECH_CHARS:
        cut = text[:MAX_SPEECH_CHARS]
        text = cut[: cut.rfind(" ")] if " " in cut else cut
    return text


# ───────────────────────── Phát âm thanh ─────────────────────────


def pick_player(ext):
    """Chọn chương trình phát phù hợp: ưu tiên PipeWire/PulseAudio (để ra loa Bluetooth)."""
    if AUDIO_PLAYER:
        return AUDIO_PLAYER.split()
    candidates = (["mpg123", "-q"], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]) if ext == "mp3" else (
        ["paplay"], ["pw-play"], ["aplay", "-q"], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"])
    for cmd in candidates:
        if shutil.which(cmd[0]):
            return cmd
    return None


def play_file(path):
    ext = path.rsplit(".", 1)[-1].lower()
    cmd = pick_player(ext)
    if DRY_RUN:
        log(f"   [DRY_RUN] phát {os.path.basename(path)} bằng {cmd[0] if cmd else 'không có player'}")
        return True
    if not cmd:
        log(f"⚠️  Không tìm thấy chương trình phát .{ext} (cài: sudo apt install mpg123 alsa-utils pulseaudio-utils)")
        return False
    try:
        subprocess.run(cmd + [path], check=True, timeout=120,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        log(f"⚠️  Lỗi phát âm thanh ({' '.join(cmd)}): {e}")
        return False


_bt_lock = threading.Lock()
_bt_last_state = None  # True/False: trạng thái lần kiểm tra trước (chỉ log khi thay đổi)


def _bt_connected():
    try:
        info = subprocess.run(["bluetoothctl", "info", BT_SPEAKER_MAC], capture_output=True, text=True, timeout=10).stdout
        return "Connected: yes" in info
    except Exception:
        return False


def _bt_sink_name():
    """Tên đầu ra âm thanh (PipeWire/PulseAudio) của loa Bluetooth, None nếu chưa có."""
    if not shutil.which("pactl"):
        return None
    try:
        out = subprocess.run(["pactl", "list", "short", "sinks"], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return None
    mac_us = BT_SPEAKER_MAC.replace(":", "_").upper()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) > 1 and "bluez" in parts[1] and mac_us in parts[1].upper():
            return parts[1]
    return None


def _bt_make_default_sink(wait_seconds=10):
    """Chờ loa xuất hiện trong danh sách đầu ra âm thanh rồi đặt làm mặc định."""
    for _ in range(wait_seconds):
        sink = _bt_sink_name()
        if sink:
            try:
                cur = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True, timeout=5).stdout.strip()
                if cur != sink:
                    subprocess.run(["pactl", "set-default-sink", sink], capture_output=True, timeout=5)
                    log(f"🔊 Đã chọn loa Bluetooth làm đầu ra âm thanh: {sink}")
            except Exception as e:
                log(f"⚠️  Không đặt được đầu ra âm thanh: {e}")
            return True
        time.sleep(1)
    log("⚠️  Loa đã kết nối Bluetooth nhưng chưa thấy trong đầu ra âm thanh "
        "(cần PipeWire: sudo apt install pipewire pipewire-pulse wireplumber libspa-0.2-bluetooth)")
    return False


def ensure_bluetooth_speaker(quiet=False):
    """
    Loa Bluetooth hay tự ngủ/ngắt → kết nối lại (thử 3 lần), chờ loa sẵn sàng rồi đặt làm đầu ra mặc định.
    quiet=True: dùng cho vòng kiểm tra nền — chỉ log khi trạng thái thay đổi để không spam log.
    """
    global _bt_last_state
    if not BT_SPEAKER_MAC or DRY_RUN or not shutil.which("bluetoothctl"):
        return True
    with _bt_lock:
        if _bt_connected():
            if _bt_last_state is not True:
                log(f"🔵 Loa Bluetooth {BT_SPEAKER_MAC} đang kết nối")
                _bt_make_default_sink()
            _bt_last_state = True
            return True
        if not quiet or _bt_last_state is not False:
            log(f"🔵 Đang kết nối lại loa Bluetooth {BT_SPEAKER_MAC}...")
        subprocess.run(["bluetoothctl", "power", "on"], capture_output=True, text=True, timeout=10)
        last_out = ""
        for attempt in range(1, 4):
            try:
                r = subprocess.run(["bluetoothctl", "connect", BT_SPEAKER_MAC],
                                   capture_output=True, text=True, timeout=25)
                last_out = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
                last_out = last_out[0]
            except Exception as e:
                last_out = str(e)
            time.sleep(2)
            if _bt_connected():
                log(f"✅ Đã kết nối loa Bluetooth (lần thử {attempt})")
                _bt_make_default_sink()
                _bt_last_state = True
                return True
            time.sleep(2)
        if not quiet or _bt_last_state is not False:
            log(f"⚠️  Không kết nối được loa Bluetooth {BT_SPEAKER_MAC}: {last_out or 'không rõ lý do'} "
                f"— loa đã bật chưa? có đang kết nối với điện thoại khác không? (sẽ tự thử lại)")
        _bt_last_state = False
        return False


def bluetooth_keeper():
    """Chạy nền: định kỳ kiểm tra & kết nối lại loa (VD loa vừa được bật lên, hoặc bị ngắt)."""
    while True:
        try:
            ensure_bluetooth_speaker(quiet=True)
        except Exception as e:
            log(f"⚠️  Lỗi kiểm tra loa Bluetooth: {e}")
        time.sleep(max(15, BT_CHECK_SECONDS))


def build_chime(path, urgent=False):
    """Tạo file chuông .wav bằng thư viện chuẩn (không cần file âm thanh có sẵn)."""
    rate = 22050
    notes = [(880, 0.12), (1320, 0.18)] if not urgent else [(988, 0.12), (740, 0.12), (988, 0.12), (740, 0.2)]
    frames = bytearray()
    for freq, dur in notes:
        n = int(rate * dur)
        for i in range(n):
            env = min(1.0, i / 300) * min(1.0, (n - i) / 600)  # fade in/out tránh tiếng "bụp"
            frames += struct.pack("<h", int(12000 * env * math.sin(2 * math.pi * freq * i / rate)))
        frames += b"\x00\x00" * int(rate * 0.04)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))


# ───────────────────────── Text-to-speech ─────────────────────────


def tts_gtts(text, workdir):
    from gtts import gTTS  # pip install gTTS
    out = os.path.join(workdir, "speech.mp3")
    gTTS(text=text, lang="vi", tld="com.vn").save(out)
    return out


def tts_espeak(text, workdir):
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        raise RuntimeError("chưa cài espeak-ng (sudo apt install espeak-ng)")
    out = os.path.join(workdir, "speech.wav")
    subprocess.run([exe, "-v", "vi", "-s", "150", "-w", out, text], check=True, timeout=60,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out


TTS_FUNCS = {"gtts": tts_gtts, "espeak": tts_espeak}


def speak(text, workdir):
    if DRY_RUN:
        log(f"   [DRY_RUN] đọc: {text}")
        return True
    for engine in TTS_ENGINES:
        fn = TTS_FUNCS.get(engine)
        if not fn:
            continue
        try:
            path = fn(text, workdir)
            if play_file(path):
                return True
        except Exception as e:
            log(f"⚠️  TTS '{engine}' lỗi: {e}")
    log("❌ Không đọc được tin (mọi TTS engine đều lỗi)")
    return False


# ───────────────────────── Giờ yên lặng ─────────────────────────


def in_quiet_hours(now=None):
    if not QUIET_HOURS or "-" not in QUIET_HOURS:
        return False
    try:
        start_s, end_s = QUIET_HOURS.split("-", 1)
        sh, sm = map(int, start_s.split(":"))
        eh, em = map(int, end_s.split(":"))
    except ValueError:
        return False
    now = now or datetime.now()
    cur, start, end = now.hour * 60 + now.minute, sh * 60 + sm, eh * 60 + em
    return start <= cur < end if start <= end else (cur >= start or cur < end)


def is_test_message(msg):
    """Tin thử do người dùng chủ động gửi (nút "Thử nghiệm Âm báo" trên website gắn tag test_tube)."""
    tags = msg.get("tags") or []
    return "test_tube" in tags or "test" in tags


def is_urgent(msg):
    """Tin khẩn: priority 5 (urgent) — cắt lỗ, lỗi lệnh thật, cần xử lý thủ công."""
    return int(msg.get("priority") or 3) >= 5


# ───────────────────────── Hàng đợi đọc tin ─────────────────────────

speech_queue = queue.Queue()


def enqueue(msg):
    while speech_queue.qsize() >= MAX_QUEUE:
        try:
            dropped = speech_queue.get_nowait()
            log(f"⏭️  Bỏ tin cũ (hàng đợi đầy): {dropped.get('title', '')[:60]}")
        except queue.Empty:
            break
    speech_queue.put(msg)


def speaker_worker():
    workdir = tempfile.mkdtemp(prefix="ntfy_speaker_")
    chime, chime_urgent = os.path.join(workdir, "chime.wav"), os.path.join(workdir, "chime_urgent.wav")
    build_chime(chime)
    build_chime(chime_urgent, urgent=True)
    while True:
        msg = speech_queue.get()
        try:
            urgent = is_urgent(msg)
            if in_quiet_hours() and not urgent and not is_test_message(msg):
                log(f"🤫 Giờ yên lặng — bỏ qua: {msg.get('title', '')[:60]}")
                continue
            text = to_speech_text(msg.get("title", ""), msg.get("message", ""))
            if not text:
                continue
            log(f"🔊 {'[KHẨN] ' if urgent else ''}{text}")
            ensure_bluetooth_speaker()
            if CHIME_ENABLED:
                play_file(chime_urgent if urgent else chime)
            speak(text, workdir)
        except Exception as e:
            log(f"⚠️  Lỗi xử lý tin: {e}")
        finally:
            speech_queue.task_done()


# ───────────────────────── Nghe ntfy (stream) ─────────────────────────


def listen_forever():
    """
    Giữ kết nối HTTP stream tới ntfy (/<topic>/json). Mỗi dòng là 1 sự kiện JSON
    (open / keepalive / message). Tự kết nối lại với backoff; dùng ?since=<id> để không mất tin
    khi rớt mạng ngắn, và bỏ qua tin quá cũ (MAX_AGE_SECONDS) để không đọc lại cả loạt tin tồn.
    """
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    last_id = None
    backoff = 2
    seen = set()
    announced = False
    while True:
        url = f"{SERVER}/{TOPIC}/json"
        params = {"since": last_id} if last_id else {}
        try:
            log(f"🔌 Kết nối {url}{' (since=' + last_id + ')' if last_id else ''}")
            # read timeout 90s: ntfy gửi keepalive ~45s/lần, quá 90s im lặng → coi như mất kết nối
            with requests.get(url, params=params, headers=headers, stream=True, timeout=(10, 90)) as r:
                if r.status_code in (401, 403):
                    log(f"❌ ntfy từ chối ({r.status_code}) — kiểm tra NTFY_TOKEN / quyền đọc topic")
                    time.sleep(60)
                    continue
                r.raise_for_status()
                backoff = 2
                for line in r.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                    except ValueError:
                        continue
                    if ev.get("event") == "open":
                        log("✅ Đang nghe cảnh báo...")
                        if STARTUP_ANNOUNCE and not announced:
                            # Báo bằng giọng nói lần kết nối đầu tiên sau khi khởi động (VD Pi vừa có điện lại)
                            announced = True
                            enqueue({"title": "", "message": "Hệ thống đọc cảnh báo Trading Signals đã sẵn sàng.",
                                     "priority": 3})
                    if ev.get("event") != "message":
                        continue
                    last_id = ev.get("id") or last_id
                    if ev.get("id") in seen:
                        continue
                    seen.add(ev.get("id"))
                    if len(seen) > 500:
                        seen.clear()
                    age = time.time() - float(ev.get("time") or time.time())
                    if age > MAX_AGE_SECONDS:
                        log(f"⏭️  Bỏ tin cũ {int(age)}s: {ev.get('title', '')[:60]}")
                        continue
                    enqueue(ev)
        except requests.exceptions.RequestException as e:
            log(f"⚠️  Mất kết nối ntfy: {e.__class__.__name__}: {e}")
        except Exception as e:
            log(f"⚠️  Lỗi không mong muốn: {e}")
        log(f"↻ Thử kết nối lại sau {backoff}s")
        time.sleep(backoff)
        backoff = min(backoff * 2, 60)


def main():
    if "--test" in sys.argv:
        # Đọc thử 1 câu để kiểm tra loa / TTS: python3 ntfy_speaker.py --test
        enqueue({"title": "[LIVE TRADE THẬT] ĐÃ VÀO LỆNH: BTCUSDT (CRYPTO)",
                 "message": "Đã vào lệnh mua tầng 1 tại giá $67,250.50 (Vốn: 1,000$, SL: 65,905.49$)",
                 "priority": 4})
        threading.Thread(target=speaker_worker, daemon=True).start()
        speech_queue.join()
        return
    if not SERVER:
        sys.exit("Thiếu NTFY_SERVER_URL (VD: http://<IP-VPS>:8088) — đặt trong file .env cạnh script")
    log(f"🎧 ntfy_speaker khởi động — topic '{TOPIC}', TTS: {', '.join(TTS_ENGINES)}"
        f"{', giờ yên lặng ' + QUIET_HOURS if QUIET_HOURS else ''}{' [DRY_RUN]' if DRY_RUN else ''}")
    if BT_SPEAKER_MAC and not DRY_RUN:
        threading.Thread(target=bluetooth_keeper, daemon=True).start()
    threading.Thread(target=speaker_worker, daemon=True).start()
    listen_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("👋 Dừng ntfy_speaker")
