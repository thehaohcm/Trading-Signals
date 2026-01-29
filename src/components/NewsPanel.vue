<template>
  <div class="news-panel" v-if="isVisible">
    <div class="news-panel-header bg-light border-bottom p-3 d-flex justify-content-between align-items-center">
      <h2 class="mb-0">🔴 Latest News</h2>
      <div>
        <button class="btn btn-secondary me-2" @click="togglePanel" title="Close">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 20px; height: 20px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L21 21" />
          </svg>
        </button>
      </div>
    </div>
    <div class="news-panel-content p-3" style="font-family: 'Times New Roman', serif; font-size: 15px;">
      <!-- FeedWind Widget -->
      <div ref="feedwindContainer" class="mb-3"></div>
      <!-- End FeedWind Widget -->
    </div>
  </div>
</template>

<script>
export default {
  name: 'NewsPanel',
  props: {
    isVisible: Boolean,
  },
  mounted() {
    this.$nextTick(() => {
      const script = document.createElement('script');
      script.src = "https://feed.mikle.com/js/fw-loader.js";
      script.setAttribute("preloader-text", "Loading");
      script.setAttribute("data-fw-param", "176927/");
      // Remove async=true to try to ensure better execution context or default behavior
      if (this.$refs.feedwindContainer) {
          this.$refs.feedwindContainer.appendChild(script);
      }
    });
  },
  methods: {
    togglePanel() {
      this.$emit('toggle');
    },
  },
};
</script>

<style scoped>
.news-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 400px; /* Adjust width as needed */
  height: 100vh;
  background-color: white;
  border-left: 1px solid #ccc;
  overflow-y: auto;
  z-index: 1000;
}
</style>