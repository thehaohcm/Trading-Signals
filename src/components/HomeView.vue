<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />
    <notifications />
    <div class="home-view container mt-4 flex-grow-1">
      <ul class="nav nav-tabs" id="myTab" role="tablist">
        <li class="nav-item" role="presentation">
          <button class="nav-link active" id="rrg-tab" data-bs-toggle="tab" data-bs-target="#rrg" type="button" role="tab" aria-controls="rrg" aria-selected="true">RRG Chart</button>
        </li>
      </ul>
      <div class="tab-content" id="myTabContent">
        <div class="tab-pane fade show active" id="rrg" role="tabpanel" aria-labelledby="rrg-tab">
          <div class="d-flex justify-content-center mt-3">
              <img src="/assets_rrgchart" class="img-fluid" alt="RRG Chart" />
          </div>
        </div>
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter  from './AppFooter.vue';

export default {
  name: 'HomeView',
  components: {
    NavBar,
    AppFooter,
  },
}
</script>

<style scoped>
/* Scoped styles if necessary */
</style>
