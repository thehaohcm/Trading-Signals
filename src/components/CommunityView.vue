<template>
  <div class="stk-page d-flex flex-column min-vh-100">
    <NavBar />
    
    <div class="stk-container flex-grow-1 py-4">
      <div class="row justify-content-center">
        <!-- Left Sidebar (Profile Overview) -->
        <div class="col-md-3 d-none d-md-block">
          <div class="stk-panel mb-3 position-sticky" style="top: 80px;">
            <div class="card-body p-4 text-center">
              <div class="mb-3">
                 <div class="avatar-large mx-auto bg-primary text-white d-flex align-items-center justify-content-center rounded-circle nav-glow fw-bold" style="width: 80px; height: 80px; font-size: 32px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important; box-shadow: 0 4px 14px rgba(59, 130, 246, 0.35);">
                   {{ userInitials }}
                 </div>
              </div>
              <h5 class="fw-bold text-white mb-1" style="font-family: 'Outfit', sans-serif;">{{ userInfo.name }}</h5>
              <p class="text-muted small mb-3">{{ userInfo.email }}</p>
              <hr style="border-top: 1px solid rgba(255,255,255,0.08); margin: 15px 0;">
              <div class="text-start d-flex flex-column gap-2" style="font-size: 0.88rem;">
                 <div class="d-flex align-items-center gap-2 text-white"><i class="fas fa-rss text-primary" style="width: 18px;"></i> Feed Activity</div>
                 <div class="d-flex align-items-center gap-2 text-muted"><i class="fas fa-user-friends text-info" style="width: 18px;"></i> Connections (0)</div>
                 <div class="d-flex align-items-center gap-2 text-muted"><i class="fas fa-bookmark text-warning" style="width: 18px;"></i> Saved Posts</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Main Feed Area -->
        <div class="col-md-6">
          <CreatePost @post-created="refreshFeed" />
          <CommunityFeed ref="feedRef" />
        </div>

        <!-- Right Sidebar (Trending/News) -->
        <div class="col-md-3 d-none d-lg-block">
          <div class="stk-panel position-sticky" style="top: 80px;">
             <div class="stk-header p-3 border-bottom border-opacity-10 border-white bg-dark bg-opacity-25 d-flex align-items-center">
               <h5 class="fw-bold mb-0 text-white" style="font-family: 'Outfit', sans-serif; font-size: 0.95rem;">
                 <i class="fa-solid fa-fire text-warning me-2"></i>Trending Topics
               </h5>
             </div>
             <div class="card-body p-3">
               <ul class="list-unstyled mb-0 d-flex flex-column gap-2" style="font-size: 0.88rem;">
                 <li><a href="#" class="stk-trend-link">#VNIndex</a></li>
                 <li><a href="#" class="stk-trend-link">#GoldPrice</a></li>
                 <li><a href="#" class="stk-trend-link">#CryptoTrading</a></li>
                 <li><a href="#" class="stk-trend-link">#StockAnalysis</a></li>
               </ul>
             </div>
          </div>
          <div class="small text-muted text-center mt-3 py-2" style="font-size: 0.72rem;">
            &copy; 2026 Trading Signals Community. <br>
            Privacy · Terms · Cookies
          </div>
        </div>
      </div>
    </div>

    <AppFooter />
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';
import CreatePost from './CreatePost.vue';
import CommunityFeed from './CommunityFeed.vue';

export default {
  name: 'CommunityView',
  components: {
    NavBar,
    AppFooter,
    CreatePost,
    CommunityFeed
  },
  setup() {
    const feedRef = ref(null);
    const userInfo = ref({});

    onMounted(() => {
       try {
         userInfo.value = JSON.parse(localStorage.getItem('userInfo') || '{}');
       } catch (e) {
         console.error(e);
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

    return {
      feedRef,
      refreshFeed,
      userInfo,
      userInitials
    };
  }
};
</script>

<style scoped>
/* ===================================== */
/*  COMMUNITY – Premium Dark Theme UI    */
/* ===================================== */

.stk-page {
  background: #2e334a;
  min-height: 100vh;
  color: #f1f5f9;
}

.stk-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
}

/* ---------- PANEL ---------- */
.stk-panel {
  background: rgba(17, 22, 34, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.35);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  overflow: hidden;
}

.stk-trend-link {
  color: #60a5fa;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.15s ease;
}
.stk-trend-link:hover {
  color: #93c5fd;
  text-decoration: underline;
  padding-left: 2px;
}

.nav-glow {
  text-shadow: 0 0 20px rgba(59, 130, 246, 0.35);
}
</style>
