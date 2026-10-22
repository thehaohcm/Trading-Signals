#!/usr/bin/env bash
# Cài ntfy_speaker lên Raspberry Pi (Raspberry Pi OS Bookworm). Chạy bằng user thường (VD: pi), KHÔNG dùng sudo:
#   bash install.sh
set -e
APP_DIR="$HOME/ntfy-speaker"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Cài gói hệ thống (cần sudo)"
sudo apt-get update
sudo apt-get install -y python3-venv mpg123 espeak-ng alsa-utils pulseaudio-utils bluez

echo "==> Copy script vào $APP_DIR"
mkdir -p "$APP_DIR"
cp "$SRC_DIR/ntfy_speaker.py" "$APP_DIR/"
if [ ! -f "$APP_DIR/.env" ]; then
  cp "$SRC_DIR/.env.example" "$APP_DIR/.env"
  echo "   ⚠️  Đã tạo $APP_DIR/.env — nhớ sửa NTFY_SERVER_URL!"
fi

echo "==> Tạo Python venv + cài thư viện"
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip >/dev/null
"$APP_DIR/venv/bin/pip" install requests gTTS

echo "==> Cài systemd user service"
mkdir -p "$HOME/.config/systemd/user"
cp "$SRC_DIR/ntfy-speaker.service" "$HOME/.config/systemd/user/"
# Cho service của user chạy ngay khi Pi khởi động, không cần đăng nhập
sudo loginctl enable-linger "$USER"
systemctl --user daemon-reload
systemctl --user enable --now ntfy-speaker.service

echo
echo "✅ Xong. Các lệnh hữu ích:"
echo "   Đọc thử 1 câu:   $APP_DIR/venv/bin/python $APP_DIR/ntfy_speaker.py --test"
echo "   Xem log:         journalctl --user -u ntfy-speaker -f"
echo "   Khởi động lại:   systemctl --user restart ntfy-speaker   (sau khi sửa .env)"
