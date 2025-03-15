<template>
  <div>
    <div @click="toggleNewsPanel" class="btn btn-danger" style="position: fixed; right: 10px; top: 15%; transform: translateY(-50%) rotate(-90deg); z-index: 1001; writing-mode: vertical-rl; padding: 10px 5px;">News</div>
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
