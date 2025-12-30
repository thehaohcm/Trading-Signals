<template>
  <div id="app">
    <div @click="toggleNewsPanel" class="btn btn-danger news-btn">News</div>
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
}

.news-btn {
  position: fixed;
  right: 10px;
  top: 15%;
  transform: translateY(-50%) rotate(-90deg);
  z-index: 1001;
  writing-mode: vertical-rl;
  padding: 10px 5px;
}

@media (max-width: 768px) {
  .news-btn {
    top: 20%;
    padding: 8px 4px;
    font-size: 0.875rem;
  }
}
</style>
