<template>
  <div id="app">
    <div @click="toggleNewsPanel" class="news-btn shadow-sm" title="Mở bảng tin tức">
      <svg class="news-btn-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 20H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v1m2 4a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2v-1"></path>
        <path d="M12 9h2"></path>
        <path d="M12 13h2"></path>
      </svg>
      <span class="text">News</span>
    </div>
    <NewsPanel :isVisible="newsPanelVisible" @toggle="toggleNewsPanel" />
    <router-view></router-view>
    <Chatbox />
  </div>
</template>

<script>
import NewsPanel from './components/NewsPanel.vue';
import Chatbox from './components/Chatbox.vue';

export default {
  name: 'App',
  components: {
    NewsPanel,
    Chatbox,
  },
  data() {
    return {
      newsPanelVisible: false,
    };
  },
  methods: {
    toggleNewsPanel() {
      this.newsPanelVisible = !this.newsPanelVisible;
    },
  },
};
</script>

<style>
* {
  box-sizing: border-box;
}

html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow-x: hidden;
}

#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.news-btn {
  position: fixed;
  right: 0;
  top: 15%;
  transform: translateY(-50%);
  z-index: 1001;
  background: linear-gradient(135deg, #ff4757 0%, #ff6b81 100%);
  color: white;
  padding: 10px 16px 10px 14px;
  border-radius: 30px 0 0 30px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-right: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  font-weight: 700;
  box-shadow: -4px 0 20px rgba(255, 71, 87, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.news-btn:hover {
  transform: translateY(-50%) translateX(-4px);
  background: linear-gradient(135deg, #ff6b81 0%, #ff879a 100%);
  box-shadow: -6px 0 25px rgba(255, 71, 87, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.news-btn:active {
  transform: translateY(-50%) translateX(-2px) scale(0.96);
}

.news-btn-icon {
  width: 18px;
  height: 18px;
  color: white;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.15));
  animation: gentle-pulse 2s infinite alternate;
}

.news-btn .text {
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-size: 0.8rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

@keyframes gentle-pulse {
  0% { transform: scale(1); }
  100% { transform: scale(1.1); }
}

@media (max-width: 768px) {
  .news-btn {
    top: 20%;
    padding: 8px 12px 8px 10px;
    font-size: 0.75rem;
  }
  .news-btn-icon {
    width: 15px;
    height: 15px;
  }
}
</style>
