<template>
  <div class="d-flex flex-column min-vh-100">
    <NavBar />
    <div class="community-container mt-5 flex-grow-1">
      <div class="container text-center text-white">
        <h1><i class="fas fa-users mb-3" style="font-size: 3rem;"></i></h1>
        <h2 class="mb-4">Community Features Coming Soon</h2>
        <p class="lead">Connect with other investors, share strategies, and discuss market trends.</p>
        <div class="mt-5">
          <button class="btn btn-outline-light" @click="$router.push('/')">Return to Home</button>
        </div>
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';

export default {
  name: 'CommunityView',
  components: {
    NavBar,
    AppFooter
  }
};
</script>

<style scoped>
.community-container {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
