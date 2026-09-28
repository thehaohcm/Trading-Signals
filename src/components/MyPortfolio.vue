<template>
  <div id="portfolio-view-root" class="d-flex flex-column min-vh-100">
    <notifications />

    <div class="my-portfolio container-xxl py-4 flex-grow-1">
      <!-- Header Section -->
      <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
        <div>
          <h1 class="display-6 fw-bold mb-1" style="font-family: 'Outfit', sans-serif; color: #ffffff;">
            <i class="fa-solid fa-wallet text-primary me-2"></i>My Portfolio
          </h1>
        </div>
      </div>

      <!-- Main Journal Component -->
      <div class="tab-content-container fade-in">
        <JournalComponent />
      </div>
    </div>
  </div>
</template>

<script>
import JournalComponent from './JournalComponent.vue';

export default {
  name: 'MyPortfolio',
  components: {
    JournalComponent,
  },
};
</script>

<style scoped>
.my-portfolio {
  padding-bottom: 80px;
}
.fade-in {
  animation: fadeIn 0.3s ease-in-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>