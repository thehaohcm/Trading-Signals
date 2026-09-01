<template>
  <div class="community-view-root d-flex flex-column min-vh-100">
    <div class="community-view container-xxl py-4 flex-grow-1">
      <div class="community-container container">
        <!-- Community Header & Action Bar -->
        <div class="community-header-panel mb-4 p-4 rounded-4 d-flex justify-content-between align-items-center flex-wrap gap-3">
          <div class="d-flex align-items-center gap-3">
            <div class="header-icon-box">
              <i class="fa-solid fa-users-viewfinder"></i>
            </div>
            <div>
              <div class="d-flex align-items-center gap-2 flex-wrap">
                <h2 class="header-title m-0">Cộng Đồng Giao Dịch</h2>
                <span class="badge-tag-community">TRADING PERSPECTIVES</span>
              </div>
              <p class="header-subtitle m-0 mt-1">Nơi chia sẻ góc nhìn vĩ mô, thảo luận chiến lược và đúc kết bài học thực chiến</p>
            </div>
          </div>

          <!-- AI Action Buttons -->
          <div class="d-flex align-items-center gap-2 flex-wrap">
            <button 
              class="btn-ai-lessons d-flex align-items-center gap-2 py-2 px-3 rounded-3" 
              @click="handleGenerateLessons"
              :disabled="isGeneratingLessons"
              title="Yêu cầu AI phân tích tất cả bài viết và đúc kết các bài học kinh nghiệm trading"
            >
              <span v-if="isGeneratingLessons" class="spinner-border spinner-border-sm text-dark" role="status"></span>
              <i v-else class="fa-solid fa-wand-magic-sparkles"></i>
              <span>{{ isGeneratingLessons ? 'AI Đang Đúc Kết Bài Học...' : 'Đúc Kết Bài Học Bằng AI' }}</span>
            </button>
          </div>
        </div>

        <!-- AI Lessons Insight Panel (collapsible) -->
        <div v-if="isGeneratingLessons || aiLessons" class="ai-lessons-panel mb-4 rounded-4 overflow-hidden">
          <div class="ai-panel-header py-3 px-4 d-flex justify-content-between align-items-center flex-wrap gap-2 border-bottom">
            <div class="d-flex align-items-center gap-2">
              <span class="ai-brain-icon">🧠</span>
              <h5 class="m-0 fw-bold text-white" style="font-size: 1rem;">
                Đúc Kết Bài Học & Góc Nhìn Từ Cộng Đồng (AI Insights)
              </h5>
              <span v-if="lessonsUpdatedAt" class="text-muted small ms-2 d-none d-sm-inline" style="font-size: 0.75rem;">
                <i class="bi bi-clock-history me-1"></i>{{ lessonsUpdatedAt }}
              </span>
            </div>

            <div class="d-flex align-items-center gap-2">
              <button 
                v-if="aiLessons && !isGeneratingLessons" 
                class="btn-ai-action" 
                @click="copyLessons"
                title="Sao chép toàn bộ bài học"
              >
                <i :class="copied ? 'fa-solid fa-check text-success' : 'fa-regular fa-copy'"></i>
                <span>{{ copied ? 'Đã chép' : 'Sao chép' }}</span>
              </button>

              <button 
                v-if="aiLessons && !isGeneratingLessons" 
                class="btn-ai-action" 
                @click="handleGenerateLessons"
                title="Phân tích lại các bài viết mới nhất"
              >
                <i class="fa-solid fa-rotate-right"></i>
                <span>Làm mới</span>
              </button>

              <button 
                class="btn-ai-action" 
                @click="isLessonsExpanded = !isLessonsExpanded"
                :title="isLessonsExpanded ? 'Thu gọn' : 'Mở rộng'"
              >
                <i :class="isLessonsExpanded ? 'fa-solid fa-chevron-up' : 'fa-solid fa-chevron-down'"></i>
              </button>

              <button 
                v-if="!isGeneratingLessons"
                class="btn-ai-action text-danger" 
                @click="closeLessons"
                title="Đóng bảng bài học"
              >
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="isGeneratingLessons" class="p-5 text-center ai-loading-wrap">
            <div class="ai-spinner mb-3"></div>
            <h6 class="fw-bold text-white mb-1">AI đang đọc & tổng hợp bài viết từ cộng đồng...</h6>
            <p class="text-muted small m-0" style="max-width: 480px; margin: 0 auto !important;">
              Hệ thống đang chắt lọc các góc nhìn vĩ mô, đúc kết chiến lược trading và cảnh báo rủi ro thực chiến.
            </p>
          </div>

          <!-- Content Body -->
          <div v-else-if="isLessonsExpanded" class="ai-lessons-body p-4">
            <div class="markdown-content" v-html="renderedLessons"></div>
          </div>
        </div>

        <!-- Main Feed Area -->
        <CreatePost @post-created="refreshFeed" />
        <CommunityFeed ref="feedRef" />
      </div>
    </div>

    <AppFooter />
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useNotification } from '@kyvg/vue3-notification';
import AppFooter from './AppFooter.vue';
import CreatePost from './CreatePost.vue';
import CommunityFeed from './CommunityFeed.vue';
import communityService from '../services/communityService';
import { parseMarkdown } from '@/utils/markdown';

export default {
  name: 'CommunityView',
  components: {
    AppFooter,
    CreatePost,
    CommunityFeed
  },
  setup() {
    const { notify } = useNotification();
    const feedRef = ref(null);
    const userInfo = ref({});
    const isGeneratingLessons = ref(false);
    const aiLessons = ref('');
    const lessonsUpdatedAt = ref('');
    const isLessonsExpanded = ref(true);
    const copied = ref(false);

    onMounted(() => {
      try {
        userInfo.value = JSON.parse(localStorage.getItem('userInfo') || '{}');
      } catch (e) {
        console.error(e);
      }

      // Load cached lessons if any
      const cached = localStorage.getItem('community_ai_lessons');
      const cachedTime = localStorage.getItem('community_ai_lessons_time');
      if (cached) {
        aiLessons.value = cached;
        lessonsUpdatedAt.value = cachedTime || '';
      }
    });

    const refreshFeed = () => {
      if (feedRef.value) {
        feedRef.value.fetchPosts();
      }
    };

    const userInitials = computed(() => {
      const name = userInfo.value.name || 'User';
      return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
    });

    const renderedLessons = computed(() => {
      if (!aiLessons.value) return '';
      return parseMarkdown(aiLessons.value);
    });

    const handleGenerateLessons = async () => {
      isGeneratingLessons.value = true;
      isLessonsExpanded.value = true;

      try {
        // Lấy danh sách posts từ feedRef nếu có sẵn, hoặc gọi API
        let currentPosts = feedRef.value?.posts || [];
        if (!currentPosts || currentPosts.length === 0) {
          currentPosts = await communityService.getPosts();
        }

        if (!currentPosts || currentPosts.length === 0) {
          notify({
            type: 'warn',
            title: 'Chưa có bài viết',
            text: 'Chưa có bài viết nào trong cộng đồng để AI phân tích.'
          });
          isGeneratingLessons.value = false;
          return;
        }

        const lessonsText = await communityService.generateLessons(currentPosts);
        aiLessons.value = lessonsText;

        const nowStr = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) + ' ' + new Date().toLocaleDateString('vi-VN');
        lessonsUpdatedAt.value = nowStr;

        // Lưu cache
        localStorage.setItem('community_ai_lessons', lessonsText);
        localStorage.setItem('community_ai_lessons_time', nowStr);

        notify({
          type: 'success',
          title: 'Đúc kết thành công',
          text: 'AI đã hoàn thành đúc kết bài học từ các bài viết cộng đồng!'
        });
      } catch (error) {
        console.error('Error generating AI lessons:', error);
        notify({
          type: 'error',
          title: 'Lỗi đúc kết AI',
          text: error.message || 'Không thể kết nối đến dịch vụ AI. Vui lòng thử lại sau.'
        });
      } finally {
        isGeneratingLessons.value = false;
      }
    };

    const copyLessons = () => {
      if (!aiLessons.value) return;
      navigator.clipboard.writeText(aiLessons.value).then(() => {
        copied.value = true;
        notify({
          type: 'info',
          title: 'Đã sao chép',
          text: 'Đã sao chép nội dung bài học vào bộ nhớ tạm.'
        });
        setTimeout(() => {
          copied.value = false;
        }, 2000);
      });
    };

    const closeLessons = () => {
      aiLessons.value = '';
      localStorage.removeItem('community_ai_lessons');
      localStorage.removeItem('community_ai_lessons_time');
    };

    return {
      feedRef,
      refreshFeed,
      userInfo,
      userInitials,
      isGeneratingLessons,
      aiLessons,
      lessonsUpdatedAt,
      isLessonsExpanded,
      renderedLessons,
      handleGenerateLessons,
      copyLessons,
      closeLessons,
      copied
    };
  }
};
</script>

<style scoped>
/* ===================================== */
/*  COMMUNITY – Premium Dark Theme UI    */
/* ===================================== */

.community-page-wrapper {
  background: #0a0d14;
  min-height: 100vh;
  color: #e2e8f0;
  display: flex;
  flex-direction: column;
}

.community-main {
  padding: 24px 16px 48px;
  width: 100%;
}

.community-container {
  max-width: 1320px;
  margin: 0 auto;
  width: 100%;
}

/* ── Community Header Panel ─────────── */
.community-header-panel {
  background: linear-gradient(135deg, rgba(18, 24, 38, 0.85) 0%, rgba(10, 13, 20, 0.95) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(16px);
}

.header-icon-box {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.2) 0%, rgba(59, 130, 246, 0.25) 100%);
  border: 1px solid rgba(0, 242, 254, 0.35);
  color: #00f2fe;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.35rem;
  box-shadow: 0 4px 16px rgba(0, 242, 254, 0.15);
}

.header-title {
  font-family: 'Outfit', sans-serif;
  font-weight: 800;
  color: #ffffff;
  font-size: 1.35rem;
  letter-spacing: -0.3px;
}

.header-subtitle {
  color: #94a3b8;
  font-size: 0.85rem;
}

.badge-tag-community {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  background: rgba(0, 242, 254, 0.12);
  border: 1px solid rgba(0, 242, 254, 0.3);
  color: #00f2fe;
  border-radius: 20px;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.6px;
}

/* ── AI Lessons Button ──────────────── */
.btn-ai-lessons {
  background: linear-gradient(135deg, #00f2fe 0%, #00f5a0 100%);
  border: none;
  color: #0a0d14;
  font-weight: 800;
  font-size: 0.85rem;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0, 242, 254, 0.3);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  letter-spacing: 0.2px;
}

.btn-ai-lessons:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 22px rgba(0, 242, 254, 0.45);
  filter: brightness(1.05);
}

.btn-ai-lessons:active:not(:disabled) {
  transform: translateY(0);
}

.btn-ai-lessons:disabled {
  opacity: 0.75;
  cursor: not-allowed;
}

/* ── AI Lessons Panel ───────────────── */
.ai-lessons-panel {
  background: linear-gradient(145deg, rgba(0, 242, 254, 0.04) 0%, rgba(18, 24, 38, 0.95) 100%);
  border: 1px solid rgba(0, 242, 254, 0.3);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45), 0 0 20px rgba(0, 242, 254, 0.1);
  backdrop-filter: blur(16px);
  animation: fadeInDown 0.3s ease;
}

.ai-panel-header {
  background: rgba(10, 13, 20, 0.6);
  border-color: rgba(255, 255, 255, 0.08) !important;
}

.ai-brain-icon {
  font-size: 1.2rem;
  filter: drop-shadow(0 0 8px rgba(0, 242, 254, 0.4));
}

.btn-ai-action {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: all 0.2s ease;
}

.btn-ai-action:hover {
  background: rgba(0, 242, 254, 0.15);
  border-color: rgba(0, 242, 254, 0.3);
  color: #00f2fe;
}

.ai-loading-wrap {
  background: rgba(10, 13, 20, 0.4);
}

.ai-spinner {
  width: 42px;
  height: 42px;
  margin: 0 auto;
  border: 3px solid rgba(0, 242, 254, 0.2);
  border-top-color: #00f2fe;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.ai-lessons-body {
  color: #e2e8f0;
  line-height: 1.75;
  font-size: 0.95rem;
  background: rgba(10, 13, 20, 0.4);
}

/* Markdown styling inside AI Lessons */
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4) {
  color: #00f2fe;
  font-weight: 700;
  margin-top: 1.2rem;
  margin-bottom: 0.6rem;
  font-size: 1.05rem;
}

.markdown-content :deep(strong) {
  color: #ffffff;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 1.4rem;
  margin-bottom: 1rem;
}

.markdown-content :deep(li) {
  margin-bottom: 0.35rem;
}

.markdown-content :deep(p) {
  margin-bottom: 0.8rem;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid #00f2fe;
  padding-left: 12px;
  margin-left: 0;
  color: #94a3b8;
  background: rgba(0, 242, 254, 0.05);
  padding: 8px 12px;
  border-radius: 0 8px 8px 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .community-main {
    padding: 16px 12px 36px;
  }

  .community-header-panel {
    padding: 16px !important;
  }

  .header-title {
    font-size: 1.15rem;
  }

  .btn-ai-lessons {
    width: 100%;
    justify-content: center;
  }
}
</style>
