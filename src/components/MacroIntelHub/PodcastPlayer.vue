<template>
  <div class="macro-podcast-card mb-2 mb-md-3" :class="{ 'compact-mode': compact }">
    <!-- Header -->
    <div class="podcast-header d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3">
      <div class="d-flex align-items-center gap-2 flex-wrap">
        <div class="podcast-badge" :class="sessionBadgeClass(currentPodcast.session)">
          <span class="pulse-dot"></span>
          <span class="session-icon">{{ sessionIcon(currentPodcast.session) }}</span>
          <span>{{ currentPodcast.session_name || 'Bản tin Macro' }}</span>
        </div>
        <span class="live-tag">
          <i class="fa-solid fa-tower-broadcast me-1"></i>Pre-Market Squawk
        </span>
        <span v-if="currentPodcast.created_at" class="podcast-time">
          <i class="fa-regular fa-clock me-1"></i>{{ formatDate(currentPodcast.created_at) }}
        </span>
      </div>

      <!-- Actions -->
      <div class="d-flex align-items-center gap-2 flex-wrap">
        <!-- History Dropdown if multiple podcasts exist -->
        <div v-if="podcastList.length > 1" class="dropdown">
          <button 
            class="action-btn action-btn-subtle dropdown-toggle" 
            type="button" 
            data-bs-toggle="dropdown" 
            aria-expanded="false"
            title="Xem danh sách các bản tin đã tạo trong ngày hôm nay"
          >
            <i class="fa-solid fa-list-ul me-1"></i>
            <span>Lịch sử hôm nay ({{ podcastList.length }})</span>
          </button>
          <ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end shadow-lg py-1 podcast-dropdown-menu">
            <li class="dropdown-header text-muted small px-3 py-1 d-flex justify-content-between align-items-center" style="font-size: 0.72rem; border-bottom: 1px solid rgba(255,255,255,0.06);">
              <span>BẢN TIN TRONG NGÀY</span>
              <span class="badge bg-secondary bg-opacity-25 text-info" style="font-size: 0.62rem;">Tự dọn dẹp hàng ngày</span>
            </li>
            <li v-for="item in podcastList" :key="item.id">
              <a 
                class="dropdown-item py-2 px-3 d-flex align-items-center justify-content-between" 
                :class="{ 'active-podcast': item.id === currentPodcast.id }"
                href="javascript:void(0)" 
                @click="selectPodcast(item)"
              >
                <div class="d-flex flex-column text-truncate me-2">
                  <div class="d-flex align-items-center gap-1 text-truncate">
                    <span class="session-mini-icon">{{ sessionIcon(item.session) }}</span>
                    <span class="fw-semibold text-truncate" style="font-size: 0.82rem;">{{ item.title || item.session_name }}</span>
                  </div>
                  <small class="text-muted" style="font-size: 0.72rem;">
                    <i class="fa-regular fa-clock me-1"></i>{{ formatDate(item.created_at) }}
                    <span v-if="item.id === currentPodcast.id" class="badge bg-info text-dark ms-1" style="font-size: 0.62rem;">Đang phát</span>
                  </small>
                </div>
                <span class="badge bg-secondary bg-opacity-25 text-info ms-2" style="font-size: 0.7rem;">
                  {{ formatDuration(item.duration_seconds) }}
                </span>
              </a>
            </li>
          </ul>
        </div>


        <!-- Manual Generate Button (Direct trigger with Auto-Session & Auth Check) -->
        <button 
          class="action-btn action-btn-primary"
          @click="handleGenerateClick"
          :disabled="isGenerating"
          :title="isLoggedIn ? 'Tự động tạo bản tin cho phiên hiện tại' : 'Đăng nhập để tạo bản tin podcast'"
        >
          <i v-if="!isGenerating" class="fa-solid fa-microphone-lines me-1"></i>
          <span v-else class="spinner-border spinner-border-sm me-1" role="status" style="width: 0.8rem; height: 0.8rem; border-width: 1.5px;"></span>
          <span>{{ isGenerating ? 'AI đang tạo podcast...' : 'Tạo Podcast Ngay' }}</span>
        </button>

        <!-- Refresh Button -->
        <button 
          class="icon-btn-square" 
          @click="fetchLatestPodcast(true)"
          :disabled="isLoading"
          title="Làm mới dữ liệu podcast"
        >
          <i class="fa-solid fa-rotate-right" :class="{ 'spin-anim': isLoading }"></i>
        </button>
      </div>
    </div>

    <!-- Main Player Box -->
    <div v-if="isLoading && !currentPodcast.id" class="text-center py-4">
      <div class="spinner-border text-info spinner-border-sm" role="status"></div>
      <p class="text-muted small mt-2 mb-0" style="color: #94a3b8 !important;">Đang tải bản tin podcast...</p>
    </div>

    <div v-else-if="!currentPodcast.id" class="empty-podcast-box p-4 text-center rounded-3">
      <div class="empty-icon mb-2" style="font-size: 2rem;">🎙️</div>
      <h6 class="text-light fw-bold mb-1">Chưa có bản tin Podcast nào được tạo</h6>
      <p class="text-muted small mb-3">Hệ thống sẽ tự động tạo trước mỗi phiên Á (06:30), Âu (13:30) và Mỹ (19:30). Bạn cũng có thể tạo ngay bây giờ.</p>
      <button 
        class="action-btn action-btn-primary mx-auto"
        @click="handleGenerateClick"
        :disabled="isGenerating"
      >
        <i class="fa-solid fa-microphone-lines me-1"></i> Tạo Bản Tin Ngay
      </button>
    </div>

    <div v-else class="player-container">
      <!-- Title & Focus -->
      <div class="podcast-info mb-3">
        <h5 class="podcast-title mb-0 text-light fw-bold d-flex align-items-center gap-2">
          <span style="color: #00f2fe;">🎙️</span>
          <span>{{ currentPodcast.title || (currentPodcast.session_name + ' - Tổng hợp Vĩ mô & Danh mục') }}</span>
        </h5>
      </div>

      <!-- Error message banner if audio fails to play -->
      <div v-if="audioErrorMessage" class="alert alert-warning py-2 px-3 small d-flex align-items-center justify-content-between mb-3 rounded-3" style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.35); color: #fbbf24;">
        <span><i class="fa-solid fa-triangle-exclamation me-1"></i>{{ audioErrorMessage }}</span>
        <button class="btn btn-sm btn-outline-warning py-0 px-2 ms-2" style="font-size: 0.75rem;" @click="handleGenerateClick">Tạo lại</button>
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
          <i v-if="!isPlaying" class="fa-solid fa-play ps-1"></i>
          <i v-else class="fa-solid fa-pause"></i>
        </button>

        <!-- Skip Backward 10s -->
        <button class="skip-btn" @click="skipTime(-10)" title="Lùi lại 10 giây">
          <i class="fa-solid fa-rotate-left"></i>
          <span class="skip-label">10s</span>
        </button>

        <!-- Skip Forward 10s -->
        <button class="skip-btn" @click="skipTime(10)" title="Tua tới 10 giây">
          <i class="fa-solid fa-rotate-right"></i>
          <span class="skip-label">10s</span>
        </button>

        <!-- Waveform Visualizer -->
        <div class="waveform-box d-flex align-items-center gap-1">
          <div 
            v-for="(bar, i) in 16" 
            :key="i" 
            class="wave-bar" 
            :class="{ active: isPlaying }"
            :style="{ 
              height: isPlaying ? getWaveHeight(i) : '4px',
              animationDelay: (i * 0.07) + 's'
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

        <!-- Download MP3 Button (Requires Login) -->
        <button 
          class="action-btn action-btn-subtle d-flex align-items-center gap-1"
          @click="handleDownload"
          :disabled="isDownloading"
          title="Tải file âm thanh MP3 về máy (Yêu cầu đăng nhập)"
        >
          <i v-if="!isDownloading" class="fa-solid fa-download"></i>
          <span v-else class="spinner-border spinner-border-sm" role="status" style="width: 0.75rem; height: 0.75rem; border-width: 1.5px;"></span>
          <span>{{ isDownloading ? 'Đang tải...' : 'Tải MP3' }}</span>
        </button>

        <!-- Toggle Transcript (Requires Login) -->
        <button 
          class="action-btn action-btn-subtle d-flex align-items-center gap-1"
          :class="{ active: showTranscript }"
          @click="handleToggleTranscript"
          title="Xem toàn văn kịch bản bản tin (Yêu cầu đăng nhập)"
        >
          <i class="fa-regular fa-file-lines"></i>
          <span>{{ showTranscript ? 'Ẩn Kịch Bản' : 'Xem Kịch Bản' }}</span>
          <i class="fa-solid ms-1" :class="showTranscript ? 'fa-chevron-up' : 'fa-chevron-down'" style="font-size: 0.65rem;"></i>
        </button>
      </div>



      <!-- Transcript Accordion -->
      <transition name="expand">
        <div v-if="showTranscript" class="transcript-box mt-3 p-3 rounded-3">
          <div class="d-flex align-items-center justify-content-between pb-2 mb-2 border-bottom flex-wrap gap-2" style="border-color: rgba(255, 255, 255, 0.08) !important;">
            <span class="fw-bold text-info" style="font-size: 0.85rem;">
              <i class="fa-solid fa-align-left me-1"></i> Toàn Văn Bản Tin (Kịch Bản Phát Thanh)
            </span>
            <div class="d-flex align-items-center gap-2">
              <button class="btn-copy-script" @click="handleDownloadScript" title="Tải kịch bản về máy (.txt) - Yêu cầu đăng nhập">
                <i class="fa-solid fa-file-arrow-down text-info"></i>
                <span class="ms-1" style="font-size: 0.75rem;">Tải Kịch Bản (.txt)</span>
              </button>
              <button class="btn-copy-script" @click="copyTranscript" title="Sao chép kịch bản">
                <i class="fa-solid" :class="copied ? 'fa-check text-success' : 'fa-copy'"></i>
                <span class="ms-1" style="font-size: 0.75rem;">{{ copied ? 'Đã sao chép!' : 'Copy' }}</span>
              </button>
            </div>
          </div>
          <div class="transcript-content" style="font-size: 0.88rem; line-height: 1.7; color: #e2e8f0; white-space: pre-line;">
            {{ currentPodcast.script_text }}
          </div>
        </div>
      </transition>

    </div>

    <!-- Login Confirmation Modal (Premium Glassmorphism Dialog) -->
    <transition name="modal-fade">
      <div v-if="showLoginModal" class="login-modal-overlay" @click.self="closeLoginModal">
        <div class="login-modal-card">
          <!-- Modal Header -->
          <div class="d-flex justify-content-between align-items-center mb-3">
            <div class="d-flex align-items-center gap-2">
              <div class="login-modal-icon-badge">
                <i class="fa-solid fa-user-lock"></i>
              </div>
              <h5 class="m-0 text-light fw-bold" style="font-size: 1.05rem;">{{ loginModalTitle }}</h5>
            </div>
            <button class="modal-close-btn" @click="closeLoginModal" title="Đóng modal">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>

          <!-- Modal Content -->
          <div class="modal-content-body mb-4">
            <p class="text-light fw-semibold mb-2" style="font-size: 0.96rem; line-height: 1.55;">
              {{ loginModalMessage }}
            </p>
            <p class="text-muted small m-0" style="color: #94a3b8 !important; font-size: 0.82rem; line-height: 1.5;">
              {{ loginModalSubMessage }}
            </p>
          </div>

          <!-- Modal Actions: 2 Buttons (Thoát vs Đăng nhập) -->
          <div class="d-flex align-items-center justify-content-end gap-2 pt-3 border-top" style="border-color: rgba(255, 255, 255, 0.08) !important;">
            <button class="btn-modal-dismiss" @click="closeLoginModal">
              <i class="fa-solid fa-xmark me-1"></i>Thoát
            </button>
            <button class="btn-modal-confirm" @click="proceedToLogin">
              <i class="fa-solid fa-right-to-bracket me-1"></i>Đăng nhập ngay
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

defineProps({
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
const audioErrorMessage = ref('');

const isLoggedIn = computed(() => {
  return !!localStorage.getItem('token');
});

const progressPercent = computed(() => {
  if (!duration.value || duration.value === 0) return 0;
  return Math.min(100, Math.max(0, (currentTime.value / duration.value) * 100));
});

// Auto-detect current session based on time
const autoDetectSession = () => {
  const now = new Date();
  const hour = now.getHours();
  // 00:00 - 11:59: Phiên Á ('asia')
  // 12:00 - 17:59: Phiên Âu ('europe')
  // 18:00 - 23:59: Phiên Mỹ ('us')
  if (hour < 12) return 'asia';
  if (hour < 18) return 'europe';
  return 'us';
};

const authHeader = () => {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

const isCreatedToday = (dateStr) => {
  if (!dateStr) return false;
  try {
    const d = new Date(dateStr);
    const now = new Date();
    return d.getFullYear() === now.getFullYear() &&
           d.getMonth() === now.getMonth() &&
           d.getDate() === now.getDate();
  } catch {
    return true;
  }
};

const fetchLatestPodcast = async () => {
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
    // Also fetch today's list (limit to today's sessions)
    const listRes = await fetch('/api/osint/podcasts?limit=10', { headers: authHeader() });
    if (listRes.ok) {
      const listData = await listRes.json();
      if (Array.isArray(listData)) {
        // Filter strictly for items created today
        podcastList.value = listData.filter(item => isCreatedToday(item.created_at));
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
  audioErrorMessage.value = '';
};

const togglePlay = () => {
  if (!audioPlayer.value || !currentPodcast.value.audio_url) return;
  audioErrorMessage.value = '';

  if (isPlaying.value) {
    audioPlayer.value.pause();
    isPlaying.value = false;
  } else {
    // Ensure correct source
    const expectedSrc = currentPodcast.value.audio_url;
    if (!audioPlayer.value.src || !audioPlayer.value.src.endsWith(expectedSrc)) {
      audioPlayer.value.src = expectedSrc;
      audioPlayer.value.load();
    }

    audioPlayer.value.play().then(() => {
      isPlaying.value = true;
      audioErrorMessage.value = '';
    }).catch(e => {
      console.warn('Audio play failed:', e);
      isPlaying.value = false;
      audioErrorMessage.value = 'Không thể phát audio. Vui lòng bấm "Tạo Podcast Ngay" để sinh lại file âm thanh.';
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
  audioErrorMessage.value = 'File âm thanh chưa sẵn sàng hoặc đường dẫn cũ. Hãy bấm "Tạo Podcast Ngay" để tạo file mới.';
};

const onScrubberClick = (e) => {
  if (!scrubber.value || !audioPlayer.value || !duration.value) return;
  const rect = scrubber.value.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const newRatio = Math.max(0, Math.min(1, clickX / rect.width));
  audioPlayer.value.currentTime = newRatio * duration.value;
};

const isDownloading = ref(false);

const showLoginModal = ref(false);
const loginModalTitle = ref('Yêu cầu Đăng nhập');
const loginModalMessage = ref('');
const loginModalSubMessage = ref('');

const openLoginModal = (msg, subMsg = 'Đăng nhập tài khoản để xem đầy đủ kịch bản, tải MP3 và sử dụng đầy đủ các tính năng AI chuyên sâu.') => {
  loginModalMessage.value = msg;
  loginModalSubMessage.value = subMsg;
  showLoginModal.value = true;
};

const closeLoginModal = () => {
  showLoginModal.value = false;
};

const proceedToLogin = () => {
  showLoginModal.value = false;
  if (router) {
    router.push('/login');
  } else {
    window.location.href = '/login';
  }
};

// Check login, then trigger MP3 download
const handleDownload = async () => {
  const token = localStorage.getItem('token');
  if (!token) {
    openLoginModal(
      'Vui lòng đăng nhập tài khoản để tải file MP3 podcast về máy!',
      'Bạn có thể tiếp tục nghe trực tiếp trên web hoặc đăng nhập để lưu trữ file audio.'
    );
    return;
  }

  if (!currentPodcast.value || !currentPodcast.value.audio_url) {
    audioErrorMessage.value = 'Chưa có file âm thanh sẵn sàng để tải về.';
    return;
  }

  isDownloading.value = true;
  try {
    const audioUrl = currentPodcast.value.audio_url;
    const response = await fetch(audioUrl);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    
    // Generate clean file name
    const rawTitle = currentPodcast.value.title || currentPodcast.value.session_name || 'macro_podcast';
    const cleanTitle = rawTitle.replace(/[/\\?%*:|"<>]/g, '_').trim();
    const fileName = `${cleanTitle}.mp3`;

    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
  } catch (e) {
    console.warn('Direct blob download failed, falling back to anchor link:', e);
    // Fallback: direct anchor download
    const link = document.createElement('a');
    link.href = currentPodcast.value.audio_url;
    link.download = `${currentPodcast.value.session || 'podcast'}.mp3`;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } finally {
    isDownloading.value = false;
  }
};

// Check login, then trigger script download (.txt)
const handleDownloadScript = () => {
  const token = localStorage.getItem('token');
  if (!token) {
    openLoginModal(
      'Vui lòng đăng nhập tài khoản để tải kịch bản bản tin về máy!',
      'Đăng nhập giúp bạn lưu trữ và đọc lại toàn bộ kịch bản phát thanh các phiên.'
    );
    return;
  }

  if (!currentPodcast.value || !currentPodcast.value.script_text) {
    audioErrorMessage.value = 'Chưa có nội dung kịch bản để tải về.';
    return;
  }

  try {
    const title = currentPodcast.value.title || currentPodcast.value.session_name || 'Bản Tin Macro Podcast';
    const session = currentPodcast.value.session_name || '';
    const dateStr = formatDate(currentPodcast.value.created_at);
    const durationStr = formatDuration(currentPodcast.value.duration_seconds);

    const fileContent = `======================================================================
${title.toUpperCase()}
Phiên giao dịch: ${session}
Thời gian cập nhật: ${dateStr}
Thời lượng dự kiến: ${durationStr}
======================================================================

KỊCH BẢN PHÁT THANH CHI TIẾT:

${currentPodcast.value.script_text}

======================================================================
Nguồn: Macro Intelligence - Trading Signals Platform
`;

    const blob = new Blob([fileContent], { type: 'text/plain;charset=utf-8' });
    const blobUrl = window.URL.createObjectURL(blob);

    const cleanTitle = title.replace(/[/\\?%*:|"<>]/g, '_').trim();
    const fileName = `Kich_ban_${cleanTitle}.txt`;

    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
  } catch (e) {
    console.error('Download script error:', e);
    audioErrorMessage.value = 'Có lỗi khi tạo file tải về: ' + e.message;
  }
};

// Check login, then trigger podcast creation directly
const handleGenerateClick = () => {
  const token = localStorage.getItem('token');
  if (!token) {
    openLoginModal(
      'Vui lòng đăng nhập tài khoản để tạo bản tin podcast!',
      'Tính năng tạo podcast theo yêu cầu dành riêng cho thành viên đã đăng nhập hệ thống.'
    );
    return;
  }
  triggerGeneratePodcast();
};

const triggerGeneratePodcast = async () => {
  const session = autoDetectSession();
  isGenerating.value = true;
  audioErrorMessage.value = '';

  try {
    const res = await fetch('/api/osint/podcasts/trigger', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeader()
      },
      body: JSON.stringify({ session })
    });
    const result = await res.json();
    if (res.ok && result.data) {
      currentPodcast.value = result.data;
      duration.value = result.data.duration_seconds || 0;
      currentTime.value = 0;
      await fetchLatestPodcast();
    } else {
      audioErrorMessage.value = result.message || 'Lỗi khi tạo podcast';
    }
  } catch (e) {
    console.error('Trigger podcast error:', e);
    audioErrorMessage.value = 'Lỗi kết nối khi gửi yêu cầu tạo podcast: ' + e.message;
  } finally {
    isGenerating.value = false;
  }
};

const handleToggleTranscript = () => {
  const token = localStorage.getItem('token');
  if (!token) {
    openLoginModal(
      'Vui lòng đăng nhập tài khoản để xem toàn văn kịch bản bản tin!',
      'Đăng nhập để đọc chi tiết các số liệu kinh tế và luận điểm vĩ mô của bản tin.'
    );
    return;
  }
  showTranscript.value = !showTranscript.value;
};

const copyTranscript = () => {
  const token = localStorage.getItem('token');
  if (!token) {
    openLoginModal(
      'Vui lòng đăng nhập tài khoản để sao chép kịch bản!',
      'Đăng nhập để sử dụng tính năng sao chép và trích xuất nội dung bản tin.'
    );
    return;
  }

  if (!currentPodcast.value.script_text) return;
  navigator.clipboard.writeText(currentPodcast.value.script_text);
  copied.value = true;
  setTimeout(() => {
    copied.value = false;
  }, 2000);
};


// Visual wave height calculation
const getWaveHeight = (index) => {
  const heights = [10, 22, 14, 26, 18, 12, 24, 16, 28, 20, 14, 25, 17, 12, 22, 15];
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
  background: linear-gradient(145deg, rgba(0, 242, 254, 0.08) 0%, rgba(13, 19, 33, 0.95) 100%);
  border: 1px solid rgba(0, 242, 254, 0.25);
  border-radius: 16px;
  padding: 1.25rem 1.5rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  position: relative;
  overflow: visible;
}

.macro-podcast-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #00f2fe, #4facfe, #10b981);
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
}


.compact-mode {
  padding: 1rem 1.25rem;
}

/* Badge */
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

/* Custom Action Buttons */
.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.35rem 0.85rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  outline: none;
}

.action-btn-primary {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.15) 0%, rgba(79, 172, 254, 0.1) 100%);
  border: 1px solid rgba(0, 242, 254, 0.4);
  color: #00f2fe;
}

.action-btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.25) 0%, rgba(79, 172, 254, 0.2) 100%);
  border-color: #00f2fe;
  color: #ffffff;
  box-shadow: 0 0 14px rgba(0, 242, 254, 0.3);
  transform: translateY(-1px);
}

.action-btn-subtle {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #cbd5e1;
}

.action-btn-subtle:hover,
.action-btn-subtle.active {
  background: rgba(0, 242, 254, 0.1);
  border-color: rgba(0, 242, 254, 0.35);
  color: #00f2fe;
}

.icon-btn-square {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.icon-btn-square:hover:not(:disabled) {
  background: rgba(0, 242, 254, 0.1);
  border-color: rgba(0, 242, 254, 0.35);
  color: #00f2fe;
}

/* Play Button */
.play-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
  border: none;
  color: #08101e;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(0, 242, 254, 0.4);
  flex-shrink: 0;
}

.play-btn:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 20px rgba(0, 242, 254, 0.6);
  color: #000000;
}

.play-btn.is-playing {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
  color: #ffffff;
}

/* Skip Buttons */
.skip-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #cbd5e1;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  gap: 1px;
}

.skip-btn i {
  font-size: 0.75rem;
}

.skip-btn:hover {
  background: rgba(0, 242, 254, 0.12);
  border-color: rgba(0, 242, 254, 0.4);
  color: #00f2fe;
}

.skip-label {
  font-size: 0.52rem;
  font-weight: 700;
  line-height: 1;
}

/* Waveform Visualizer */
.waveform-box {
  height: 32px;
  padding: 0 4px;
}

.wave-bar {
  width: 3px;
  background: rgba(0, 242, 254, 0.3);
  border-radius: 3px;
  transition: height 0.15s ease;
}

.wave-bar.active {
  background: linear-gradient(180deg, #00f2fe 0%, #10b981 100%);
  animation: wave-pulse 0.9s infinite alternate ease-in-out;
}

@keyframes wave-pulse {
  0% { transform: scaleY(0.35); }
  100% { transform: scaleY(1.15); }
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
  background: rgba(255, 255, 255, 0.04);
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
  padding: 3px 7px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.speed-btn.active {
  background: rgba(0, 242, 254, 0.2);
  color: #00f2fe;
}

/* Transcript Box */
.transcript-box {
  background: rgba(10, 15, 26, 0.85);
  border: 1px solid rgba(0, 242, 254, 0.2);
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4);
}

.btn-copy-script {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  padding: 3px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-copy-script:hover {
  color: #00f2fe;
  border-color: rgba(0, 242, 254, 0.4);
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

/* History Dropdown Menu */
.podcast-dropdown-menu {
  min-width: 320px !important;
  max-width: 380px !important;
  max-height: 320px !important;
  overflow-y: auto !important;
  background: #0f172a !important;
  border: 1px solid rgba(0, 242, 254, 0.3) !important;
  z-index: 1060 !important;
  border-radius: 10px !important;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.6) !important;
}

.podcast-dropdown-menu .dropdown-item {
  border-radius: 6px;
  margin: 2px 4px;
  width: auto;
  transition: all 0.15s ease;
}

.podcast-dropdown-menu .dropdown-item:hover {
  background: rgba(0, 242, 254, 0.12) !important;
  color: #00f2fe !important;
}

.podcast-dropdown-menu::-webkit-scrollbar {
  width: 5px;
}

.podcast-dropdown-menu::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.6);
}

.podcast-dropdown-menu::-webkit-scrollbar-thumb {
  background: rgba(0, 242, 254, 0.35);
  border-radius: 4px;
}

.session-mini-icon {
  font-size: 0.95rem;
  flex-shrink: 0;
}

/* Login Modal Overlay & Card (Glassmorphism) */
.login-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(5, 8, 15, 0.75);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

.login-modal-card {
  background: #0f172a;
  border: 1px solid rgba(0, 242, 254, 0.35);
  border-radius: 16px;
  max-width: 480px;
  width: 100%;
  padding: 1.5rem;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 30px rgba(0, 242, 254, 0.15);
  animation: modalScaleIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modalScaleIn {
  from {
    opacity: 0;
    transform: scale(0.94) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.login-modal-icon-badge {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(0, 242, 254, 0.15);
  color: #00f2fe;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  border: 1px solid rgba(0, 242, 254, 0.3);
}

.modal-close-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 1.1rem;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.modal-close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.modal-content-body {
  background: rgba(10, 15, 26, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 1rem 1.25rem;
}

.btn-modal-dismiss {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #94a3b8;
  padding: 0.5rem 1.25rem;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-modal-dismiss:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.3);
}

.btn-modal-confirm {
  background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
  border: none;
  color: #050b14;
  padding: 0.5rem 1.25rem;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 15px rgba(0, 242, 254, 0.3);
}

.btn-modal-confirm:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 242, 254, 0.45);
  color: #000000;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>

