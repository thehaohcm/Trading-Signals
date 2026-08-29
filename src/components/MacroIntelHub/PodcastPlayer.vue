<template>
  <div class="macro-podcast-card mb-4" :class="{ 'compact-mode': compact }">
    <!-- Header -->
    <div class="podcast-header d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3">
      <div class="d-flex align-items-center gap-2 flex-wrap">
        <div class="podcast-badge" :class="sessionBadgeClass(currentPodcast.session)">
          <span class="pulse-dot"></span>
          <span class="session-icon">{{ sessionIcon(currentPodcast.session) }}</span>
          <span>{{ currentPodcast.session_name || 'Bản tin Macro' }}</span>
        </div>
        <span class="live-tag"><i class="bi bi-broadcast me-1"></i>Pre-Market Squawk</span>
        <span v-if="currentPodcast.created_at" class="podcast-time">
          <i class="bi bi-clock-history me-1"></i>{{ formatDate(currentPodcast.created_at) }}
        </span>
      </div>

      <!-- Actions -->
      <div class="d-flex align-items-center gap-2 flex-wrap">
        <!-- History Dropdown if multiple podcasts exist -->
        <div v-if="podcastList.length > 1" class="dropdown">
          <button 
            class="stk-btn stk-btn--outline d-flex align-items-center gap-1 py-1 px-2 rounded-3 text-secondary" 
            type="button" 
            data-bs-toggle="dropdown" 
            aria-expanded="false"
            style="font-size: 0.75rem; font-weight: 600;"
            title="Nghe lại các phiên trước"
          >
            <i class="bi bi-collection-play me-1"></i>
            <span>Các phiên khác ({{ podcastList.length }})</span>
            <i class="bi bi-chevron-down ms-1" style="font-size: 0.7rem;"></i>
          </button>
          <ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end shadow-lg py-1" style="min-width: 260px; font-size: 0.82rem; background: #131b2e; border: 1px solid rgba(0, 242, 254, 0.2);">
            <li v-for="item in podcastList" :key="item.id">
              <a 
                class="dropdown-item py-2 d-flex align-items-center justify-content-between" 
                :class="{ 'active-podcast': item.id === currentPodcast.id }"
                href="javascript:void(0)" 
                @click="selectPodcast(item)"
              >
                <div class="d-flex flex-column text-truncate me-2">
                  <span class="fw-semibold text-truncate">{{ item.title || item.session_name }}</span>
                  <small class="text-muted" style="font-size: 0.72rem;">{{ formatDate(item.created_at) }}</small>
                </div>
                <span class="badge bg-secondary bg-opacity-25 text-info" style="font-size: 0.7rem;">
                  {{ formatDuration(item.duration_seconds) }}
                </span>
              </a>
            </li>
          </ul>
        </div>

        <!-- Manual Generate Button -->
        <button 
          class="stk-btn stk-btn--outline d-flex align-items-center gap-1 py-1 px-2 rounded-3 text-info border-info" 
          style="font-size: 0.75rem; font-weight: 600;"
          @click="openTriggerModal"
          :disabled="isGenerating"
          title="Yêu cầu AI tổng hợp và sinh bản tin Podcast mới"
        >
          <i v-if="!isGenerating" class="bi bi-mic-fill" style="font-size: 0.85rem;"></i>
          <span v-else class="spinner-border spinner-border-sm text-info" role="status" style="width: 0.85rem; height: 0.85rem; border-width: 1.5px;"></span>
          <span>{{ isGenerating ? 'AI đang tạo podcast...' : 'Tạo Podcast Ngay' }}</span>
        </button>

        <button 
          class="stk-btn stk-btn--outline d-flex align-items-center gap-1 py-1 px-2 rounded-3 text-light" 
          style="font-size: 0.75rem; font-weight: 600;"
          @click="fetchLatestPodcast(true)"
          :disabled="isLoading"
          title="Làm mới"
        >
          <i class="bi bi-arrow-clockwise" :class="{ 'spin-anim': isLoading }" style="font-size: 0.85rem;"></i>
        </button>
      </div>
    </div>

    <!-- Main Player Box -->
    <div v-if="isLoading && !currentPodcast.id" class="text-center py-4">
      <div class="spinner-border text-info spinner-border-sm" role="status"></div>
      <p class="text-muted small mt-2 mb-0" style="color: #94a3b8 !important;">Đang tải bản tin podcast...</p>
    </div>

    <div v-else-if="!currentPodcast.id" class="empty-podcast-box p-4 text-center rounded-3">
      <div class="empty-icon mb-2">🎙️</div>
      <h6 class="text-light fw-bold mb-1">Chưa có bản tin Podcast nào được tạo</h6>
      <p class="text-muted small mb-3">Hệ thống sẽ tự động tạo trước mỗi phiên Á (06:30), Âu (13:30) và Mỹ (19:30). Bạn cũng có thể tạo ngay bây giờ.</p>
      <button 
        class="btn btn-sm btn-info px-3 py-1 fw-semibold text-dark"
        @click="openTriggerModal"
        :disabled="isGenerating"
      >
        <i class="bi bi-mic-fill me-1"></i> Tạo Bản Tin Ngay
      </button>
    </div>

    <div v-else class="player-container">
      <!-- Title & Focus -->
      <div class="podcast-info mb-3">
        <h5 class="podcast-title mb-1 text-light fw-bold d-flex align-items-center gap-2">
          <span>🎙️</span>
          <span>{{ currentPodcast.title || (currentPodcast.session_name + ' - Tổng hợp Vĩ mô & Danh mục') }}</span>
        </h5>
      </div>

      <!-- Hidden Audio Element -->
      <audio 
        ref="audioPlayer" 
        :src="currentPodcast.audio_url" 
        preload="metadata"
        @timeupdate="onTimeUpdate"
        @loadedmetadata="onLoadedMetadata"
        @ended="onEnded"
        @error="onAudioError"
      ></audio>

      <!-- Player Controls Row -->
      <div class="controls-row d-flex align-items-center gap-3 flex-wrap">
        <!-- Play / Pause Button -->
        <button 
          class="play-btn d-flex align-items-center justify-content-center"
          :class="{ 'is-playing': isPlaying }"
          @click="togglePlay"
          :title="isPlaying ? 'Tạm dừng' : 'Phát bản tin'"
        >
          <i v-if="!isPlaying" class="bi bi-play-fill"></i>
          <i v-else class="bi bi-pause-fill"></i>
        </button>

        <!-- Skip Backward 10s -->
        <button class="skip-btn" @click="skipTime(-10)" title="Lùi lại 10 giây">
          <i class="bi bi-arrow-counterclockwise"></i>
          <span class="skip-label">10s</span>
        </button>

        <!-- Skip Forward 10s -->
        <button class="skip-btn" @click="skipTime(10)" title="Tua tới 10 giây">
          <i class="bi bi-arrow-clockwise"></i>
          <span class="skip-label">10s</span>
        </button>

        <!-- Waveform Visualizer -->
        <div class="waveform-box d-flex align-items-center gap-1">
          <div 
            v-for="(bar, i) in 20" 
            :key="i" 
            class="wave-bar" 
            :class="{ active: isPlaying }"
            :style="{ 
              height: isPlaying ? getWaveHeight(i) : '4px',
              animationDelay: (i * 0.06) + 's'
            }"
          ></div>
        </div>

        <!-- Progress Scrubber & Times -->
        <div class="progress-wrap flex-grow-1 d-flex align-items-center gap-2">
          <span class="time-display">{{ formatSeconds(currentTime) }}</span>
          <div class="scrubber-bar flex-grow-1" ref="scrubber" @click="onScrubberClick">
            <div class="scrubber-track">
              <div class="scrubber-progress" :style="{ width: progressPercent + '%' }">
                <span class="scrubber-thumb"></span>
              </div>
            </div>
          </div>
          <span class="time-display total-time">{{ formatSeconds(duration || currentPodcast.duration_seconds || 0) }}</span>
        </div>

        <!-- Speed Selector -->
        <div class="speed-selector d-flex align-items-center">
          <button 
            v-for="s in [1.0, 1.25, 1.5]" 
            :key="s"
            class="speed-btn"
            :class="{ active: playbackRate === s }"
            @click="setPlaybackRate(s)"
          >
            {{ s }}x
          </button>
        </div>

        <!-- Toggle Transcript -->
        <button 
          class="transcript-toggle-btn d-flex align-items-center gap-1"
          :class="{ active: showTranscript }"
          @click="showTranscript = !showTranscript"
          title="Xem toàn văn kịch bản bản tin"
        >
          <i class="bi bi-file-text"></i>
          <span>{{ showTranscript ? 'Ẩn Kịch Bản' : 'Xem Kịch Bản' }}</span>
          <i class="bi" :class="showTranscript ? 'bi-chevron-up' : 'bi-chevron-down'" style="font-size: 0.7rem;"></i>
        </button>
      </div>

      <!-- Transcript Accordion -->
      <transition name="expand">
        <div v-if="showTranscript" class="transcript-box mt-3 p-3 rounded-3">
          <div class="d-flex align-items-center justify-content-between pb-2 mb-2 border-bottom" style="border-color: rgba(255, 255, 255, 0.08) !important;">
            <span class="fw-bold text-info" style="font-size: 0.85rem;">
              <i class="bi bi-card-text me-1"></i> Toàn Văn Bản Tin (Kịch Bản Phát Thanh)
            </span>
            <button class="btn-copy-script" @click="copyTranscript" title="Sao chép kịch bản">
              <i class="bi" :class="copied ? 'bi-check-lg text-success' : 'bi-clipboard'"></i>
              <span class="ms-1" style="font-size: 0.75rem;">{{ copied ? 'Đã sao chép!' : 'Copy' }}</span>
            </button>
          </div>
          <div class="transcript-content" style="font-size: 0.88rem; line-height: 1.7; color: #e2e8f0; white-space: pre-line;">
            {{ currentPodcast.script_text }}
          </div>
        </div>
      </transition>
    </div>

    <!-- Manual Generate Modal -->
    <div v-if="showModal" class="modal-backdrop-custom d-flex align-items-center justify-content-center">
      <div class="trigger-modal-card p-4 rounded-4 shadow-2xl">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h5 class="fw-bold text-light mb-0 d-flex align-items-center gap-2">
            <span>🎙️</span> Tạo Bản Tin Macro Podcast
          </h5>
          <button class="btn-close btn-close-white" @click="showModal = false"></button>
        </div>

        <p class="text-muted small mb-3">
          AI sẽ đọc dữ liệu thời gian thực từ <strong>Current World State</strong>, <strong>Platform Intelligence</strong> và <strong>Tín hiệu OSINT</strong> để biên tập kịch bản và sinh giọng đọc phát thanh.
        </p>

        <div class="mb-3">
          <label class="form-label text-light small fw-semibold">Chọn Phiên Giao Dịch Mục Tiêu:</label>
          <div class="d-flex gap-2">
            <button 
              type="button" 
              class="session-select-btn flex-grow-1 py-2 px-3 rounded-3"
              :class="{ active: selectedSession === 'asia' }"
              @click="selectedSession = 'asia'"
            >
              <div class="session-icon">🌅</div>
              <div class="session-name">Phiên Á</div>
              <div class="session-time">06:30 ICT</div>
            </button>

            <button 
              type="button" 
              class="session-select-btn flex-grow-1 py-2 px-3 rounded-3"
              :class="{ active: selectedSession === 'europe' }"
              @click="selectedSession = 'europe'"
            >
              <div class="session-icon">☀️</div>
              <div class="session-name">Phiên Âu</div>
              <div class="session-time">13:30 ICT</div>
            </button>

            <button 
              type="button" 
              class="session-select-btn flex-grow-1 py-2 px-3 rounded-3"
              :class="{ active: selectedSession === 'us' }"
              @click="selectedSession = 'us'"
            >
              <div class="session-icon">🌙</div>
              <div class="session-name">Phiên Mỹ</div>
              <div class="session-time">19:30 ICT</div>
            </button>
          </div>
        </div>

        <div class="d-flex justify-content-end gap-2 mt-4 pt-3 border-top" style="border-color: rgba(255, 255, 255, 0.08) !important;">
          <button class="btn btn-sm btn-outline-secondary px-3" @click="showModal = false" :disabled="isGenerating">Hủy</button>
          <button 
            class="btn btn-sm btn-info px-4 fw-semibold text-dark d-flex align-items-center gap-2"
            @click="triggerGeneratePodcast"
            :disabled="isGenerating"
          >
            <span v-if="isGenerating" class="spinner-border spinner-border-sm" role="status"></span>
            <i v-else class="bi bi-stars"></i>
            <span>{{ isGenerating ? 'AI đang tổng hợp & sinh audio...' : 'Bắt Đầu Tạo' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';

const props = defineProps({
  compact: {
    type: Boolean,
    default: false
  }
});

const audioPlayer = ref(null);
const scrubber = ref(null);

const currentPodcast = ref({});
const podcastList = ref([]);
const isLoading = ref(false);
const isGenerating = ref(false);
const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const playbackRate = ref(1.0);
const showTranscript = ref(false);
const copied = ref(false);

const showModal = ref(false);
const selectedSession = ref('asia');

const progressPercent = computed(() => {
  if (!duration.value || duration.value === 0) return 0;
  return Math.min(100, Math.max(0, (currentTime.value / duration.value) * 100));
});

// Auto-detect current session
const autoDetectSession = () => {
  const hour = new Date().getHours();
  if (hour < 12) return 'asia';
  if (hour < 18) return 'europe';
  return 'us';
};

const authHeader = () => {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

const fetchLatestPodcast = async (manualRefresh = false) => {
  isLoading.value = true;
  try {
    const res = await fetch('/api/osint/podcasts/latest', { headers: authHeader() });
    if (res.ok) {
      const data = await res.json();
      if (data && data.id) {
        currentPodcast.value = data;
        duration.value = data.duration_seconds || 0;
      }
    }
    // Also fetch recent list
    const listRes = await fetch('/api/osint/podcasts?limit=6', { headers: authHeader() });
    if (listRes.ok) {
      const listData = await listRes.json();
      if (Array.isArray(listData)) {
        podcastList.value = listData;
      }
    }
  } catch (e) {
    console.error('Error fetching latest podcast:', e);
  } finally {
    isLoading.value = false;
  }
};

const selectPodcast = (item) => {
  if (isPlaying.value && audioPlayer.value) {
    audioPlayer.value.pause();
    isPlaying.value = false;
  }
  currentPodcast.value = item;
  currentTime.value = 0;
  duration.value = item.duration_seconds || 0;
};

const togglePlay = () => {
  if (!audioPlayer.value) return;
  if (isPlaying.value) {
    audioPlayer.value.pause();
    isPlaying.value = false;
  } else {
    audioPlayer.value.play().then(() => {
      isPlaying.value = true;
    }).catch(e => {
      console.warn('Audio play failed:', e);
      isPlaying.value = false;
    });
  }
};

const skipTime = (seconds) => {
  if (!audioPlayer.value) return;
  audioPlayer.value.currentTime = Math.min(duration.value, Math.max(0, audioPlayer.value.currentTime + seconds));
};

const setPlaybackRate = (rate) => {
  playbackRate.value = rate;
  if (audioPlayer.value) {
    audioPlayer.value.playbackRate = rate;
  }
};

const onTimeUpdate = () => {
  if (audioPlayer.value) {
    currentTime.value = audioPlayer.value.currentTime;
  }
};

const onLoadedMetadata = () => {
  if (audioPlayer.value && audioPlayer.value.duration) {
    duration.value = audioPlayer.value.duration;
  }
};

const onEnded = () => {
  isPlaying.value = false;
  currentTime.value = 0;
};

const onAudioError = (e) => {
  console.warn('Audio element error:', e);
  isPlaying.value = false;
};

const onScrubberClick = (e) => {
  if (!scrubber.value || !audioPlayer.value || !duration.value) return;
  const rect = scrubber.value.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const newRatio = Math.max(0, Math.min(1, clickX / rect.width));
  audioPlayer.value.currentTime = newRatio * duration.value;
};

const openTriggerModal = () => {
  selectedSession.value = autoDetectSession();
  showModal.value = true;
};

const triggerGeneratePodcast = async () => {
  isGenerating.value = true;
  try {
    const res = await fetch('/api/osint/podcasts/trigger', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeader()
      },
      body: JSON.stringify({ session: selectedSession.value })
    });
    const result = await res.json();
    if (res.ok && result.data) {
      currentPodcast.value = result.data;
      duration.value = result.data.duration_seconds || 0;
      currentTime.value = 0;
      showModal.value = false;
      await fetchLatestPodcast();
    } else {
      alert(result.message || 'Lỗi khi tạo podcast');
    }
  } catch (e) {
    console.error('Trigger podcast error:', e);
    alert('Lỗi kết nối khi gửi yêu cầu tạo podcast: ' + e.message);
  } finally {
    isGenerating.value = false;
  }
};

const copyTranscript = () => {
  if (!currentPodcast.value.script_text) return;
  navigator.clipboard.writeText(currentPodcast.value.script_text);
  copied.value = true;
  setTimeout(() => {
    copied.value = false;
  }, 2000);
};

// Visual wave height calculation
const getWaveHeight = (index) => {
  const heights = [12, 22, 16, 28, 20, 14, 26, 18, 30, 24, 15, 27, 21, 13, 25, 17, 29, 19, 14, 20];
  return (heights[index % heights.length]) + 'px';
};

const formatSeconds = (sec) => {
  if (!sec || isNaN(sec)) return '00:00';
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`;
};

const formatDuration = (sec) => {
  if (!sec) return '0p';
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return s > 0 ? `${m}p ${s}s` : `${m}p`;
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    return d.toLocaleString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateStr;
  }
};

const sessionBadgeClass = (session) => {
  if (session === 'asia') return 'badge-asia';
  if (session === 'europe') return 'badge-europe';
  if (session === 'us') return 'badge-us';
  return 'badge-default';
};

const sessionIcon = (session) => {
  if (session === 'asia') return '🌅';
  if (session === 'europe') return '☀️';
  if (session === 'us') return '🌙';
  return '🎙️';
};

onMounted(() => {
  fetchLatestPodcast();
});

onBeforeUnmount(() => {
  if (audioPlayer.value) {
    audioPlayer.value.pause();
  }
});
</script>

<style scoped>
.macro-podcast-card {
  background: linear-gradient(145deg, rgba(0, 242, 254, 0.07) 0%, rgba(13, 19, 33, 0.95) 100%);
  border: 1px solid rgba(0, 242, 254, 0.25);
  border-radius: 16px;
  padding: 1.25rem 1.5rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  position: relative;
  overflow: hidden;
}

.macro-podcast-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #00f2fe, #4facfe, #10b981);
}

.compact-mode {
  padding: 1rem 1.25rem;
}

.podcast-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge-asia {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.4);
}

.badge-europe {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.4);
}

.badge-us {
  background: rgba(168, 85, 247, 0.15);
  color: #c084fc;
  border: 1px solid rgba(168, 85, 247, 0.4);
}

.badge-default {
  background: rgba(0, 242, 254, 0.15);
  color: #00f2fe;
  border: 1px solid rgba(0, 242, 254, 0.4);
}

.pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 8px currentColor;
  animation: pulse-anim 1.5s infinite;
}

@keyframes pulse-anim {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

.live-tag {
  font-size: 0.72rem;
  font-weight: 600;
  color: #94a3b8;
  background: rgba(255, 255, 255, 0.05);
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.podcast-time {
  font-size: 0.75rem;
  color: #64748b;
}

.podcast-title {
  font-size: 1.05rem;
  line-height: 1.4;
  color: #f8fafc;
}

/* Play Button */
.play-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
  border: none;
  color: #0d1321;
  font-size: 1.35rem;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(0, 242, 254, 0.35);
  flex-shrink: 0;
}

.play-btn:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 20px rgba(0, 242, 254, 0.5);
}

.play-btn.is-playing {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
  color: #ffffff;
}

/* Skip Buttons */
.skip-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #cbd5e1;
  border-radius: 50%;
  width: 34px;
  height: 34px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  flex-shrink: 0;
}

.skip-btn:hover {
  background: rgba(0, 242, 254, 0.15);
  border-color: rgba(0, 242, 254, 0.4);
  color: #00f2fe;
}

.skip-label {
  font-size: 0.55rem;
  font-weight: 700;
  margin-top: -3px;
}

/* Waveform Visualizer */
.waveform-box {
  height: 32px;
  padding: 0 6px;
}

.wave-bar {
  width: 3px;
  background: rgba(0, 242, 254, 0.35);
  border-radius: 3px;
  transition: height 0.15s ease;
}

.wave-bar.active {
  background: linear-gradient(180deg, #00f2fe 0%, #10b981 100%);
  animation: wave-pulse 1s infinite alternate ease-in-out;
}

@keyframes wave-pulse {
  0% { transform: scaleY(0.4); }
  100% { transform: scaleY(1.1); }
}

/* Progress Scrubber */
.progress-wrap {
  min-width: 140px;
}

.time-display {
  font-size: 0.75rem;
  font-family: 'JetBrains Mono', monospace, sans-serif;
  color: #94a3b8;
  min-width: 38px;
}

.total-time {
  text-align: right;
}

.scrubber-bar {
  height: 20px;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.scrubber-track {
  width: 100%;
  height: 5px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  position: relative;
}

.scrubber-progress {
  height: 100%;
  background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%);
  border-radius: 4px;
  position: relative;
}

.scrubber-thumb {
  position: absolute;
  right: -5px;
  top: -4px;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 0 8px rgba(0, 242, 254, 0.8);
  opacity: 0;
  transition: opacity 0.15s ease;
}

.scrubber-bar:hover .scrubber-thumb {
  opacity: 1;
}

/* Speed Selector */
.speed-selector {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 2px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.speed-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.speed-btn.active {
  background: rgba(0, 242, 254, 0.2);
  color: #00f2fe;
}

/* Transcript Toggle */
.transcript-toggle-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #cbd5e1;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 5px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.transcript-toggle-btn:hover,
.transcript-toggle-btn.active {
  background: rgba(0, 242, 254, 0.12);
  border-color: rgba(0, 242, 254, 0.35);
  color: #00f2fe;
}

/* Transcript Box */
.transcript-box {
  background: rgba(10, 15, 26, 0.8);
  border: 1px solid rgba(0, 242, 254, 0.2);
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4);
}

.btn-copy-script {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  padding: 2px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-copy-script:hover {
  color: #00f2fe;
  border-color: rgba(0, 242, 254, 0.4);
}

/* Modal */
.modal-backdrop-custom {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(5px);
  z-index: 9999;
}

.trigger-modal-card {
  background: #0f172a;
  border: 1px solid rgba(0, 242, 254, 0.3);
  max-width: 480px;
  width: 90%;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.6);
}

.session-select-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.session-select-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
}

.session-select-btn.active {
  background: rgba(0, 242, 254, 0.12);
  border-color: #00f2fe;
  color: #00f2fe;
}

.session-icon {
  font-size: 1.4rem;
  margin-bottom: 2px;
}

.session-name {
  font-size: 0.8rem;
  font-weight: 700;
}

.session-time {
  font-size: 0.7rem;
  color: #94a3b8;
}

.active-podcast {
  background: rgba(0, 242, 254, 0.15) !important;
  color: #00f2fe !important;
}

.spin-anim {
  animation: spin 1s infinite linear;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.25s ease-out;
  max-height: 500px;
  opacity: 1;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
  overflow: hidden;
}
</style>
