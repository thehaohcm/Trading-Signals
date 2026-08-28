<template>
  <div class="stk-page d-flex flex-column min-vh-100">
    <NavBar />
    
    <div class="stk-container flex-grow-1 py-4">
      <div class="row justify-content-center">
        <!-- Main Feed Area -->
        <div class="col-lg-8 col-md-10">
          <CreatePost @post-created="refreshFeed" />
          <CommunityFeed ref="feedRef" />
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
  background: #0a0d14;
  min-height: 100vh;
  color: #e2e8f0;
  padding: 20px 0 40px;
}

.stk-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
}

/* ---------- PANEL ---------- */
.stk-panel {
  background: rgba(18, 24, 38, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  overflow: hidden;
  backdrop-filter: blur(16px);
}

.stk-trend-link {
  color: #00f2fe;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.15s ease;
}
.stk-trend-link:hover {
  color: #38bdf8;
  text-decoration: underline;
  padding-left: 2px;
}

.nav-glow {
  text-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
}
</style>
