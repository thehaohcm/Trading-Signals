<template>
  <div class="d-flex flex-column min-vh-100">
    <NavBar />
    <div class="container mt-5 flex-grow-1">
      <JournalComponent />
    </div>
    <AppFooter />
  </div>
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';
import JournalComponent from './JournalComponent.vue';

export default {
  name: 'JournalView',
  components: {
    NavBar,
    AppFooter,
    JournalComponent
  }
};
</script>

<style scoped>
</style>
