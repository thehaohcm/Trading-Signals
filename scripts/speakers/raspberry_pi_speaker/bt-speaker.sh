#!/usr/bin/env bash
# Chọn & kết nối loa Bluetooth cho Raspberry Pi bằng dòng lệnh.
#   bash bt-speaker.sh            # quét → chọn loa → pair, trust, connect → đặt làm đầu ra âm thanh
#   bash bt-speaker.sh status     # xem loa đang kết nối & đầu ra âm thanh mặc định
#   bash bt-speaker.sh reconnect  # kết nối lại loa đã lưu trong ~/ntfy-speaker/.env
# Trước khi chạy: bật loa và cho loa vào chế độ pair (thường giữ nút Bluetooth tới khi đèn nháy nhanh).
set -e
ENV_FILE="$HOME/ntfy-speaker/.env"
SCAN_SECONDS="${SCAN_SECONDS:-15}"

need() { command -v "$1" >/dev/null 2>&1 || { echo "❌ Thiếu lệnh '$1' — cài: sudo apt install $2"; exit 1; }; }
need bluetoothctl bluez

set_default_sink() {
  # Đặt loa Bluetooth làm đầu ra mặc định (PipeWire/PulseAudio)
  command -v pactl >/dev/null 2>&1 || { echo "   (bỏ qua chọn đầu ra: chưa cài pulseaudio-utils)"; return; }
  local mac_us sink
  mac_us=$(echo "$1" | tr ':' '_')
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    sink=$(pactl list short sinks 2>/dev/null | awk '{print $2}' | grep -i "bluez.*${mac_us}" | head -n1 || true)
    [ -n "$sink" ] && break
    sleep 1
  done
  if [ -n "$sink" ]; then
    pactl set-default-sink "$sink"
    echo "🔊 Đã đặt đầu ra âm thanh mặc định: $sink"
  else
    echo "⚠️  Chưa thấy loa trong danh sách đầu ra âm thanh. Bluetooth audio cần PipeWire:"
    echo "    sudo apt install pipewire pipewire-pulse wireplumber libspa-0.2-bluetooth && reboot"
  fi
}

save_mac() {
  [ -f "$ENV_FILE" ] || return 0
  if grep -qE '^#?\s*BT_SPEAKER_MAC=' "$ENV_FILE"; then
    sed -i -E "s|^#?\s*BT_SPEAKER_MAC=.*|BT_SPEAKER_MAC=$1|" "$ENV_FILE"
  else
    echo "BT_SPEAKER_MAC=$1" >> "$ENV_FILE"
  fi
  echo "💾 Đã lưu BT_SPEAKER_MAC=$1 vào $ENV_FILE"
  systemctl --user restart ntfy-speaker 2>/dev/null && echo "↻ Đã khởi động lại ntfy-speaker" || true
}

connect_mac() {
  local mac="$1"
  echo "🔗 Pair / trust / connect $mac ..."
  bluetoothctl pair "$mac" >/dev/null 2>&1 || true      # đã pair rồi thì bỏ qua lỗi
  bluetoothctl trust "$mac" >/dev/null
  for i in 1 2 3; do
    if bluetoothctl connect "$mac" 2>&1 | grep -q "Connection successful"; then
      echo "✅ Đã kết nối $(bluetoothctl info "$mac" | sed -n 's/^\s*Name: //p')"
      set_default_sink "$mac"
      return 0
    fi
    echo "   Thử lại ($i/3)..."; sleep 3
  done
  echo "❌ Không kết nối được. Kiểm tra loa đã bật / đang ở chế độ pair và ở gần Pi."
  return 1
}

case "${1:-}" in
  status)
    echo "== Thiết bị đã pair =="; bluetoothctl devices Paired 2>/dev/null || bluetoothctl paired-devices
    echo "== Đang kết nối =="; bluetoothctl devices Connected 2>/dev/null || true
    command -v pactl >/dev/null && { echo "== Đầu ra mặc định =="; pactl get-default-sink; }
    exit 0 ;;
  reconnect)
    mac=$(sed -n -E 's/^BT_SPEAKER_MAC=([0-9A-Fa-f:]{17}).*/\1/p' "$ENV_FILE" 2>/dev/null | head -n1)
    [ -n "$mac" ] || { echo "❌ Chưa có BT_SPEAKER_MAC trong $ENV_FILE — chạy: bash bt-speaker.sh"; exit 1; }
    connect_mac "$mac"; exit $? ;;
esac

echo "🔵 Bật Bluetooth..."
sudo rfkill unblock bluetooth 2>/dev/null || true
bluetoothctl power on >/dev/null
bluetoothctl agent NoInputNoOutput >/dev/null 2>&1 || true
bluetoothctl default-agent >/dev/null 2>&1 || true

echo "📡 Đang quét ${SCAN_SECONDS}s — hãy bật chế độ pair trên loa..."
bluetoothctl --timeout "$SCAN_SECONDS" scan on >/dev/null 2>&1 || true

mapfile -t DEVICES < <(bluetoothctl devices | sed -n 's/^Device \([0-9A-F:]\{17\}\) \(.*\)$/\1 \2/p')
if [ ${#DEVICES[@]} -eq 0 ]; then
  echo "❌ Không tìm thấy thiết bị nào. Bật chế độ pair trên loa rồi chạy lại."; exit 1
fi

echo; echo "Chọn loa:"
for i in "${!DEVICES[@]}"; do printf "  %2d) %s\n" "$((i+1))" "${DEVICES[$i]}"; done
read -rp "Nhập số thứ tự: " choice
[[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#DEVICES[@]} ] || { echo "Lựa chọn không hợp lệ"; exit 1; }
MAC=$(echo "${DEVICES[$((choice-1))]}" | awk '{print $1}')

connect_mac "$MAC" && save_mac "$MAC"
echo; echo "Thử loa: ~/ntfy-speaker/venv/bin/python ~/ntfy-speaker/ntfy_speaker.py --test"
