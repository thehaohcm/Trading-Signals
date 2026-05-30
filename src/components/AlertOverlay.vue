<template>
  <div class="alert-overlay-container">
    <!-- Floating Settings Button -->
    <div class="alert-settings-toggle shadow-lg" @click.stop="toggleSettings" title="Cài đặt âm báo động">
      <i class="fa-solid fa-bell-slash" v-if="!soundEnabled && !ttsEnabled"></i>
      <i class="fa-solid fa-bell" v-else></i>
      <i class="fa-solid fa-gear settings-gear-icon"></i>
    </div>

    <!-- Settings Pane -->
    <transition name="fade-slide">
      <div class="alert-settings-pane shadow-lg" v-if="settingsVisible" v-click-outside="closeSettings">
        <h4 class="settings-title">Cài đặt Báo Động</h4>
        
        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">Phát âm thanh (Chime)</span>
            <span class="setting-desc">Âm thanh chuông khi có lệnh lớn</span>
          </div>
          <label class="switch">
            <input type="checkbox" v-model="soundEnabled" @change="saveSettings">
            <span class="slider round"></span>
          </label>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">Đọc giọng nói (TTS)</span>
            <span class="setting-desc">Nói to thông báo bằng giọng AI</span>
          </div>
          <label class="switch">
            <input type="checkbox" v-model="ttsEnabled" @change="saveSettings">
            <span class="slider round"></span>
          </label>
        </div>

        <div class="test-chime-btn" @click="testAlert">
          <i class="fa-solid fa-play"></i> Thử nghiệm Âm báo
        </div>
        <div class="script-status" style="margin-top:8px; font-size:0.85rem; color:#fff;">
          Trạng thái script: <span :style="{color: scriptRunning ? '#2ecc71' : '#e74c3c'}">{{ scriptRunning ? 'Đang chạy' : 'Không chạy' }}</span>
          <button class="restart-btn" @click="restartScript" style="margin-left:10px;">Restart Script</button>
        </div>
      </div>
    </transition>

    <!-- Alert Cards Stacking Grid -->
    <div class="alert-stack-grid">
      <transition-group name="card-fly">
        <div 
          v-for="alert in activeAlerts" 
          :key="alert.id" 
          :class="['alert-card', 'shadow-lg', alert.asset_type]"
          @click="dismissAlert(alert.id)"
        >
          <div class="card-glow"></div>
          
          <div class="alert-header">
            <span class="badge">
              <i :class="alert.asset_type === 'stock' ? 'fa-solid fa-chart-line' : 'fa-solid fa-coins'"></i>
              {{ alert.asset_type.toUpperCase() }}
            </span>
            <span class="symbol">{{ alert.symbol }}</span>
            <button class="close-btn" @click.stop="dismissAlert(alert.id)">&times;</button>
          </div>

          <div class="alert-body">
            <p class="message">{{ alert.message }}</p>
          </div>

          <div class="alert-footer">
            <span class="time"><i class="fa-regular fa-clock"></i> {{ formatTime(alert.created_at) }}</span>
            <span class="click-info">Nhấp để đóng</span>
          </div>
        </div>
      </transition-group>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AlertOverlay',
  data() {
    return {
      activeAlerts: [],
      soundEnabled: true,
      ttsEnabled: true,
      settingsVisible: false,
      pollInterval: null,
      scriptRunning: false
    };
  },
  mounted() {
    this.loadSettings();
    this.startPolling();
  },
  beforeUnmount() {
    this.stopPolling();
  },
  methods: {
    loadSettings() {
      const soundVal = localStorage.getItem('trade_alert_sound');
      const ttsVal = localStorage.getItem('trade_alert_tts');
      
      this.soundEnabled = soundVal !== 'false'; // Default to true
      this.ttsEnabled = ttsVal !== 'false';     // Default to true
    },
    saveSettings() {
      localStorage.setItem('trade_alert_sound', this.soundEnabled.toString());
      localStorage.setItem('trade_alert_tts', this.ttsEnabled.toString());
    },
    toggleSettings() {
      this.settingsVisible = !this.settingsVisible;
    },
    closeSettings() {
      this.settingsVisible = false;
    },
    startPolling() {
      // Immediate poll on mount
      this.pollAlerts();
      this.fetchScriptStatus();

      // Poll every 4 seconds
      this.pollInterval = setInterval(() => {
        this.pollAlerts();
        this.fetchScriptStatus();
      }, 4000);
    },
    stopPolling() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval);
        this.pollInterval = null;
      }
    },
    // Script status handling
    async fetchScriptStatus() {
      try {
        const res = await fetch('/scriptStatus');
        if (!res.ok) return;
        const data = await res.json();
        this.scriptRunning = data.running;
      } catch (e) {
        console.error('Error fetching script status', e);
      }
    },
    async restartScript() {
      try {
        const res = await fetch('/restartScript', { method: 'POST' });
        if (!res.ok) return;
        await this.fetchScriptStatus();
      } catch (e) {
        console.error('Error restarting script', e);
      }
    },
    async pollAlerts() {
      try {
        const response = await fetch('/triggeredAlerts');
        if (!response.ok) return;
        
        const unreadAlerts = await response.json();
        if (unreadAlerts && unreadAlerts.length > 0) {
          // Process each unread alert
          for (const alert of unreadAlerts) {
            this.handleNewAlert(alert);
          }
        }
      } catch (e) {
        console.error("Lỗi khi tải báo động từ server:", e);
      }
    },
    async handleNewAlert(alert) {
      // 1. Add alert to UI cards stack
      this.activeAlerts.unshift(alert);

      // 2. Play Audio chime
      this.playChime();

      // 3. Synthesize Text-to-Speech (TTS)
      this.speakAlert(alert);

      // 4. Dismiss card from UI automatically after 10 seconds
      setTimeout(() => {
        this.dismissAlert(alert.id);
      }, 10000);

      // 5. Mark as read immediately in the DB
      try {
        await fetch('/triggeredAlerts/read', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ids: [alert.id] })
        });
      } catch (e) {
        console.error(`Không thể đánh dấu báo động ${alert.id} đã đọc:`, e);
      }
    },
    dismissAlert(id) {
      this.activeAlerts = this.activeAlerts.filter(a => a.id !== id);
    },
    playChime() {
      if (!this.soundEnabled) return;
      try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        
        // Note 1: E5
        const osc1 = audioCtx.createOscillator();
        const gain1 = audioCtx.createGain();
        osc1.connect(gain1);
        gain1.connect(audioCtx.destination);
        osc1.type = 'sine';
        osc1.frequency.value = 659.25; // E5
        gain1.gain.setValueAtTime(0.15, audioCtx.currentTime);
        gain1.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);
        osc1.start();
        osc1.stop(audioCtx.currentTime + 0.35);
        
        // Note 2: A5 slightly delayed
        setTimeout(() => {
          const osc2 = audioCtx.createOscillator();
          const gain2 = audioCtx.createGain();
          osc2.connect(gain2);
          gain2.connect(audioCtx.destination);
          osc2.type = 'sine';
          osc2.frequency.value = 880.00; // A5
          gain2.gain.setValueAtTime(0.15, audioCtx.currentTime);
          gain2.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.45);
          osc2.start();
          osc2.stop(audioCtx.currentTime + 0.45);
        }, 120);
      } catch (e) {
        console.warn("Web Audio API not supported or blocked by browser user gesture.", e);
      }
    },
    speakAlert(alert) {
      if (!this.ttsEnabled) return;
      try {
        // Preprocess the text to read uppercase symbols/coins letter by letter clearly
        let text = alert.message || '';
        
        // Remove 'USDT' suffix from uppercase coin pairs (e.g. TRXUSDT -> TRX)
        text = text.replace(/\b([A-Z]+)USDT\b/g, '$1');
        
        // Remove standalone 'USDT' in uppercase
        text = text.replace(/\bUSDT\b/g, '');
        
        // Split remaining uppercase symbols/coins of length 3-12 letter-by-letter
        text = text.replace(/\b[A-Z]{3,12}\b/g, (match) => match.split('').join(' '));

        const utterance = new SpeechSynthesisUtterance(text);
        
        // Speak all alerts in Vietnamese since they are now in Vietnamese
        utterance.lang = 'vi-VN';
        utterance.rate = 1.05; // Slightly faster reading
        
        // Force cancel any current speaking to prevent queue lag
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
      } catch (e) {
        console.error("Text-to-speech error:", e);
      }
    },
    testAlert() {
      // Always generate a stock (GEX) test alert
      const testItem = {
        id: Date.now(),
        asset_type: 'stock',
        symbol: 'GEX',
        message:
          "Cảnh báo Stock: Thử nghiệm lệnh lớn cho GEX. Khớp lệnh năm mươi nghìn cổ phiếu ở mức giá ba mươi nghìn đồng.",
        created_at: new Date().toISOString()
      };

      this.activeAlerts.unshift(testItem);
      this.playChime();
      this.speakAlert(testItem);

      setTimeout(() => this.dismissAlert(testItem.id), 10000);
    },
    formatTime(dateStr) {
      try {
        const d = new Date(dateStr);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      } catch (e) {
        return '';
      }
    }
  },
  directives: {
    'click-outside': {
      bind(el, binding, vnode) {
        el.clickOutsideEvent = function(event) {
          if (!(el == event.target || el.contains(event.target))) {
            vnode.context[binding.expression](event);
          }
        };
        document.body.addEventListener('click', el.clickOutsideEvent);
      },
      unbind(el) {
        document.body.removeEventListener('click', el.clickOutsideEvent);
      }
    }
  }
};
</script>

<style scoped>
.alert-overlay-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* Let clicks pass through to underneath pages */
  z-index: 9999; /* Float above everything! */
}

/* Floating Settings Button */
.alert-settings-toggle {
  position: fixed;
  bottom: 24px;
  left: 24px;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: rgba(20, 24, 33, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  color: #a4b0be;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  pointer-events: auto; /* Handle clicks */
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.alert-settings-toggle:hover {
  color: #ff4757;
  border-color: rgba(255, 71, 87, 0.4);
  transform: scale(1.08) rotate(5deg);
  box-shadow: 0 12px 40px rgba(255, 71, 87, 0.25);
}

.alert-settings-toggle:active {
  transform: scale(0.95);
}

.settings-gear-icon {
  position: absolute;
  font-size: 10px;
  bottom: 8px;
  right: 8px;
  color: #747d8c;
}

.alert-settings-toggle:hover .settings-gear-icon {
  transform: rotate(90deg);
  color: #ff4757;
  transition: transform 0.4s ease;
}

/* Settings Pane */
.alert-settings-pane {
  position: fixed;
  bottom: 80px;
  left: 24px;
  width: 320px;
  padding: 20px;
  border-radius: 16px;
  background: rgba(15, 18, 25, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  color: white;
  pointer-events: auto;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5);
  z-index: 10000;
}

.settings-title {
  margin: 0 0 16px 0;
  font-size: 1rem;
  font-weight: 700;
  color: #ff4757;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.setting-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.setting-label {
  font-weight: 600;
  font-size: 0.85rem;
  color: #f1f2f6;
}

.setting-desc {
  font-size: 0.72rem;
  color: #747d8c;
}

.test-chime-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  border-radius: 8px;
  background: rgba(255, 71, 87, 0.15);
  color: #ff4757;
  border: 1px solid rgba(255, 71, 87, 0.3);
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 10px;
}

.test-chime-btn:hover {
  background: #ff4757;
  color: white;
  transform: translateY(-2px);
}

.test-chime-btn:active {
  transform: translateY(0);
}

/* Restart button styling */
.restart-btn {
  padding: 4px 8px;
  background: rgba(255,71,87,0.3);
  border: 1px solid rgba(255,71,87,0.5);
  color: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
  transition: background 0.2s;
}
.restart-btn:hover {
  background: rgba(255,71,87,0.6);
}

/* Switch styling */
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #2f3542;
  transition: .3s;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .3s;
}

input:checked + .slider {
  background-color: #ff4757;
}

input:checked + .slider:before {
  transform: translateX(20px);
}

.slider.round {
  border-radius: 24px;
}

.slider.round:before {
  border-radius: 50%;
}

/* Alert Cards Stacking Grid */
.alert-stack-grid {
  position: fixed;
  top: 24px;
  right: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 420px;
  max-width: calc(100vw - 48px);
  z-index: 10001;
}

.alert-card {
  position: relative;
  border-radius: 16px;
  padding: 16px;
  background: rgba(18, 22, 33, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  color: white;
  pointer-events: auto;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.4);
}

.alert-card:hover {
  transform: translateY(-4px) scale(1.02);
  border-color: rgba(255, 255, 255, 0.15);
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.5);
}

.card-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at 100% 0%, rgba(255, 255, 255, 0.08) 0%, transparent 60%);
  pointer-events: none;
}

/* Asset types glowing borders */
.alert-card.stock {
  border-left: 4px solid #10ac84; /* Emerald Green */
}
.alert-card.stock:hover {
  box-shadow: 0 20px 48px rgba(16, 172, 132, 0.15), 0 0 1px rgba(16, 172, 132, 0.5);
}

.alert-card.crypto {
  border-left: 4px solid #00d2d3; /* Cyan blue */
}
.alert-card.crypto:hover {
  box-shadow: 0 20px 48px rgba(0, 210, 211, 0.15), 0 0 1px rgba(0, 210, 211, 0.5);
}

/* Header */
.alert-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.badge {
  font-size: 0.65rem;
  font-weight: 800;
  padding: 4px 8px;
  border-radius: 20px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  letter-spacing: 0.5px;
}

.stock .badge {
  background: rgba(16, 172, 132, 0.15);
  color: #10ac84;
}

.crypto .badge {
  background: rgba(0, 210, 211, 0.15);
  color: #00d2d3;
}

.symbol {
  font-weight: 800;
  font-size: 0.95rem;
  letter-spacing: 0.5px;
  color: #f1f2f6;
  flex-grow: 1;
}

.close-btn {
  background: none;
  border: none;
  color: #747d8c;
  font-size: 20px;
  font-weight: 400;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  transition: color 0.2s ease;
}

.close-btn:hover {
  color: #ff4757;
}

/* Body */
.alert-body {
  margin-bottom: 10px;
}

.message {
  margin: 0;
  font-size: 0.85rem;
  line-height: 1.45;
  color: #dfe4ea;
}

/* Footer */
.alert-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding-top: 8px;
  font-size: 0.72rem;
  color: #747d8c;
}

.time i {
  margin-right: 3px;
}

.click-info {
  font-style: italic;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.alert-card:hover .click-info {
  opacity: 1;
  color: #ff4757;
}

/* Animations */
.fade-slide-enter-active, .fade-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.fade-slide-enter, .fade-slide-leave-to {
  transform: translateY(12px) scale(0.95);
  opacity: 0;
}

.card-fly-enter-active {
  animation: fly-in 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.card-fly-leave-active {
  animation: fly-out 0.3s ease forwards;
  position: absolute;
}
.card-fly-move {
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes fly-in {
  0% {
    transform: translateX(120%) scale(0.9);
    opacity: 0;
  }
  70% {
    transform: translateX(-5%) scale(1.02);
  }
  100% {
    transform: translateX(0) scale(1);
    opacity: 1;
  }
}

@keyframes fly-out {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(0.85) translateY(-30px);
    opacity: 0;
  }
}
</style>
