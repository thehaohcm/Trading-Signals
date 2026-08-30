<template>
  <div class="community-page-wrapper d-flex flex-column min-vh-100">
    <NavBar />
    
    <main class="community-main flex-grow-1">
      <div class="community-container">
        <!-- Main Feed Area -->
        <CreatePost @post-created="refreshFeed" />
        <CommunityFeed ref="feedRef" />
      </div>
    </main>

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
/*  COMMUNITY – Stable Dark Theme UI     */
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
  max-width: 780px;
  margin: 0 auto;
  width: 100%;
}

@media (max-width: 768px) {
  .community-main {
    padding: 16px 12px 36px;
  }
}
</style>
