<template>
  <div>
    <button class="btn btn-primary" @click="toggleNewsPanel">Toggle News</button>
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
