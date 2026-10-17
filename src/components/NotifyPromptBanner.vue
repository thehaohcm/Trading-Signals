<template>
  <!-- Banner nhắc bật thông báo trên màn hình (cùng kiểu banner Breaking News, nổi trên đầu trang) -->
  <teleport to="body">
    <transition name="notify-prompt-anim">
      <div v-if="visible" class="notify-prompt-banner" role="region" aria-label="Bật thông báo">
        <div class="notify-prompt-inner d-flex align-items-center justify-content-between gap-2">
          <div class="notify-prompt-content d-flex align-items-center gap-2 overflow-hidden">
            <div class="notify-prompt-badge d-flex align-items-center gap-1 flex-shrink-0">
              <span class="notify-pulse-dot"></span>
              <i class="fa-solid fa-bell"></i>
              <span class="badge-text">THÔNG BÁO</span>
            </div>
            <span v-if="status.permission === 'denied'" class="notify-prompt-text">
              Thông báo đang bị chặn. Bấm biểu tượng <i class="fa-solid fa-lock"></i> cạnh địa chỉ web → <b>Thông báo</b> → <b>Cho phép</b>, rồi tải lại trang.
            </span>
            <span v-else-if="error" class="notify-prompt-text notify-prompt-error">{{ error }}</span>
            <span v-else class="notify-prompt-text">
              Bật thông báo để nhận <b>cảnh báo giao dịch</b> ngay trên màn hình — kể cả khi đã đóng tab.
            </span>
          </div>

          <div class="notify-prompt-actions d-flex align-items-center gap-2 flex-shrink-0">
            <button
              v-if="status.permission === 'denied'"
              class="notify-prompt-btn"
              data-notify-cta
              @click="reload"
            >
              <i class="fa-solid fa-rotate-right"></i> Đã cho phép, tải lại
            </button>
            <button
              v-else
              class="notify-prompt-btn"
              data-notify-cta
              :disabled="busy"
              @click="enable"
            >
              <i class="fa-solid" :class="busy ? 'fa-spinner fa-spin' : 'fa-bell'"></i>
              {{ busy ? 'Đang bật...' : 'Bật thông báo' }}
            </button>
            <button class="notify-prompt-close" data-notify-cta title="Để sau" @click="dismiss">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script>
import {
  getNotificationStatus,
  enableNotifications,
  setNotifyOptOut,
  sendTestPush,
} from '../utils/webPush';

const DISMISS_KEY = 'notify_prompt_dismissed'; // sessionStorage: ẩn tới lần vào web sau
const SHOW_DELAY_MS = 2500;

export default {
  name: 'NotifyPromptBanner',
  data() {
    return {
      status: getNotificationStatus(),
      ready: false,
      dismissed: false,
      busy: false,
      error: '',
      timer: null,
    };
  },
  computed: {
    visible() {
      return this.ready && !this.dismissed && this.status.supported && !this.status.mode;
    },
  },
  mounted() {
    try {
      this.dismissed = sessionStorage.getItem(DISMISS_KEY) === 'true';
    } catch (e) { /* ignore */ }
    window.addEventListener('notify-status-changed', this.onStatusChanged);
    // Đợi một chút để tự đăng ký lại (người dùng đã cho phép trước đó) kịp hoàn tất, tránh nháy banner
    this.timer = setTimeout(() => {
      this.status = getNotificationStatus();
      this.ready = true;
    }, SHOW_DELAY_MS);
  },
  beforeUnmount() {
    clearTimeout(this.timer);
    window.removeEventListener('notify-status-changed', this.onStatusChanged);
  },
  methods: {
    onStatusChanged(e) {
      this.status = (e && e.detail) || getNotificationStatus();
    },
    async enable() {
      this.busy = true;
      this.error = '';
      setNotifyOptOut(false);
      try {
        const result = await enableNotifications(); // gọi ngay trong cú click → trình duyệt hiện hộp hỏi quyền
        this.status = getNotificationStatus();
        if (result.mode === 'push') {
          sendTestPush().catch(() => { /* đã bật, chỉ là gửi thử lỗi */ });
        } else if (result.permission === 'default') {
          this.error = 'Bạn chưa chọn "Cho phép". Bấm "Bật thông báo" để thử lại.';
        } else if (!result.mode && result.error) {
          this.error = `Chưa bật được thông báo: ${result.error}`;
        }
      } catch (e) {
        this.error = `Chưa bật được thông báo: ${e.message || e}`;
      } finally {
        this.busy = false;
      }
    },
    dismiss() {
      this.dismissed = true;
      try {
        sessionStorage.setItem(DISMISS_KEY, 'true');
      } catch (e) { /* ignore */ }
    },
    reload() {
      window.location.reload();
    },
  },
};
</script>

<style scoped>
.notify-prompt-banner {
  position: fixed;
  top: 14px;
  left: 50%;
  transform: translateX(-50%);
  width: 96%;
  max-width: 1400px;
  border-radius: 10px;
  background: linear-gradient(90deg, rgba(8, 145, 178, 0.96) 0%, rgba(30, 64, 175, 0.97) 50%, rgba(10, 14, 28, 0.98) 100%);
  border: 1.5px solid rgba(103, 232, 249, 0.65);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), 0 0 22px rgba(34, 211, 238, 0.35);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  padding: 8px 12px 8px 16px;
  /* Thấp hơn banner Breaking News (9999999) để tin nóng luôn hiện đè lên */
  z-index: 9999990;
}

.notify-prompt-inner {
  min-height: 30px;
}

.notify-prompt-badge {
  background: rgba(34, 211, 238, 0.2);
  border: 1px solid rgba(103, 232, 249, 0.7);
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 700;
  color: #a5f3fc;
  letter-spacing: 0.5px;
  box-shadow: 0 0 12px rgba(34, 211, 238, 0.35);
}

.notify-pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #22d3ee;
  box-shadow: 0 0 8px #22d3ee;
  animation: notify-pulse 1.4s infinite;
}

@keyframes notify-pulse {
  0%, 100% { transform: scale(0.9); opacity: 0.8; }
  50% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 14px #22d3ee; }
}

.notify-prompt-text {
  font-size: 0.85rem;
  font-weight: 500;
  color: #ffffff;
  line-height: 1.35;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notify-prompt-error {
  color: #fde68a;
}

.notify-prompt-btn {
  background: linear-gradient(90deg, #67e8f9, #60a5fa);
  color: #0b1220;
  border: none;
  border-radius: 8px;
  padding: 5px 14px;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s;
}

.notify-prompt-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(103, 232, 249, 0.45);
}

.notify-prompt-btn:disabled {
  opacity: 0.7;
  cursor: wait;
}

.notify-prompt-close {
  background: transparent;
  border: none;
  color: #a5f3fc;
  font-size: 0.9rem;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.notify-prompt-close:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.2);
}

/* Điện thoại / màn hình hẹp: cho chữ xuống dòng */
@media (max-width: 640px) {
  .notify-prompt-inner {
    flex-wrap: wrap;
  }
  .notify-prompt-text {
    white-space: normal;
  }
  .notify-prompt-badge {
    display: none !important;
  }
  .notify-prompt-actions {
    margin-left: auto;
  }
}

.notify-prompt-anim-enter-active,
.notify-prompt-anim-leave-active {
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

.notify-prompt-anim-enter-from,
.notify-prompt-anim-leave-to {
  opacity: 0;
  transform: translate(-50%, -100%) scale(0.96);
}

.notify-prompt-anim-enter-to,
.notify-prompt-anim-leave-from {
  opacity: 1;
  transform: translate(-50%, 0) scale(1);
}
</style>
