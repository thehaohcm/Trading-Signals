<template>
  <div class="d-flex flex-column min-vh-100 bg-light">
    <NavBar />
    
    <div class="container mt-4 flex-grow-1">
      <div class="row justify-content-center">
        <!-- Left Sidebar (Optional Profile/Links) -->
        <div class="col-md-3 d-none d-md-block">
          <div class="card border-0 shadow-sm mb-3 position-sticky" style="top: 80px;">
            <div class="card-body text-center">
              <div class="mb-3">
                 <div class="avatar-large mx-auto bg-primary text-white d-flex align-items-center justify-content-center rounded-circle" style="width: 80px; height: 80px; font-size: 32px;">
                   {{ userInitials }}
                 </div>
              </div>
              <h5 class="card-title">{{ userInfo.name }}</h5>
              <p class="text-muted small">{{ userInfo.email }}</p>
              <hr>
              <div class="text-start">
                 <p class="mb-2"><i class="fas fa-rss me-2 text-primary"></i> Feed</p>
                 <p class="mb-2"><i class="fas fa-user-friends me-2 text-info"></i> Connections (0)</p>
                 <p class="mb-2"><i class="fas fa-bookmark me-2 text-warning"></i> Saved</p>
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
          <div class="card border-0 shadow-sm position-sticky" style="top: 80px;">
             <div class="card-header bg-white border-0 fw-bold">
               Trending Topics
             </div>
             <div class="card-body pt-0">
               <ul class="list-unstyled mb-0">
                 <li class="mb-2"><a href="#" class="text-decoration-none text-dark">#VNIndex</a></li>
                 <li class="mb-2"><a href="#" class="text-decoration-none text-dark">#GoldPrice</a></li>
                 <li class="mb-2"><a href="#" class="text-decoration-none text-dark">#CryptoTrading</a></li>
                 <li class="mb-2"><a href="#" class="text-decoration-none text-dark">#StockAnalysis</a></li>
               </ul>
             </div>
          </div>
           <div class="card border-0 shadow-sm mt-3 position-sticky" style="top: 250px;">
             <div class="card-body small text-muted">
               &copy; 2026 Trading Signals Community. <br>
               Privacy · Terms · Cookies
             </div>
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
.bg-light {
  background-color: #f0f2f5 !important;
}
</style>
