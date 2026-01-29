<template>
  <div id="app">
    <div @click="toggleNewsPanel" class="news-btn shadow-sm">
      <span class="text">News</span>
    </div>
    <NewsPanel :isVisible="newsPanelVisible" @toggle="toggleNewsPanel" />
    <router-view></router-view>
  </div>
</template>

<script>
import NewsPanel from './components/NewsPanel.vue';

export default {
  name: 'App',
  components: {
    NewsPanel,
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
  background: #ff4757; /* More modern red */
  color: white;
  padding: 12px 16px 12px 12px;
  border-top-left-radius: 24px;
  border-bottom-left-radius: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: right 0.3s ease, background-color 0.3s ease;
  font-weight: 600;
  box-shadow: -4px 0 15px rgba(255, 71, 87, 0.4);
}

.news-btn:hover {
  right: -5px; /* Subtle hover effect */
  background: #ff6b81;
}

.news-btn .icon {
  font-size: 1.2em;
}

.news-btn .text {
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .news-btn {
    top: 20%;
    padding: 8px 4px;
    font-size: 0.875rem;
  }
}
</style>
