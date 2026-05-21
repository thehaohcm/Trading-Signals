<template>
  <div class="d-flex flex-column min-vh-100">
    <NavBar />
    <div class="container mt-4 flex-grow-1">
      <!-- Title -->
      <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h2 class="mb-0 fw-bold d-flex align-items-center gap-2 text-dark">
          <span>🌐</span> Other Macro Resources
        </h2>
        <span class="badge bg-primary px-3 py-2 shadow-sm" style="background-color: #3182ce !important; font-size: 0.9rem;">
          Resource Hub
        </span>
      </div>

      <!-- Introduction Panel -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="card border-0 shadow-sm" style="background: #ffffff; border-left: 4px solid #3182ce !important;">
            <div class="card-body text-dark py-3">
              <p class="mb-0" style="color: #4a5568; font-size: 0.95rem; line-height: 1.6;">
                Explore useful external charts and macroeconomic indicators from across the globe to complement your trading research and market analysis.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab Buttons -->
      <ul class="nav nav-tabs mb-4" id="otherResourcesTabs" role="tablist">
        <li class="nav-item" v-for="tab in tabs" :key="tab.id">
          <button 
            class="nav-link" 
            :class="{ active: activeTab === tab.id }" 
            @click="activeTab = tab.id"
            type="button"
          >
            {{ tab.name }}
          </button>
        </li>
      </ul>

      <!-- Tab Content -->
      <div class="tab-content">
        <div v-for="tab in tabs" :key="tab.id" v-show="activeTab === tab.id" class="tab-pane fade show active">
          <div class="card border-0 shadow-sm" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0 !important;">
            <!-- Header -->
            <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center py-3 px-4 border-0">
              <h5 class="mb-0 fw-bold text-white d-flex align-items-center gap-2">
                <span>📊</span> {{ tab.title }}
              </h5>
              <a :href="tab.url" target="_blank" class="btn btn-sm btn-outline-light px-3">
                Open Official Site ↗
              </a>
            </div>
            
            <!-- Body -->
            <div class="card-body p-0">
              <!-- Embed Chart -->
              <iframe 
                :src="tab.embedUrl" 
                width="100%" 
                height="650" 
                frameborder="0" 
                style="border:none;" 
                loading="lazy"
              ></iframe>
            </div>
          </div>
        </div>
      </div>
    </div>
    <AppFooter class="mt-5" />
  </div>
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';
import { ref } from 'vue';

export default {
  name: 'OthersView',
  components: {
    NavBar,
    AppFooter
  },
  setup() {
    const activeTab = ref('useful-links');

    const tabs = ref([
      {
        id: 'useful-links',
        name: 'Useful links',
        title: 'TradingView World Economy Charts',
        url: 'https://www.tradingview.com/markets/world-economy/charts-banking-finance',
        embedUrl: 'https://www.tradingview.com/markets/world-economy/charts-banking-finance'
      }
    ]);

    return {
      activeTab,
      tabs
    };
  }
};
</script>

<style scoped>
.nav-tabs {
  border-bottom: 1px solid #dee2e6 !important;
}
.nav-tabs .nav-link {
  color: #718096;
  border: none;
  background: none;
  font-weight: 600;
  padding: 12px 24px;
  transition: all 0.2s;
  border-radius: 0;
  border-bottom: 3px solid transparent;
}
.nav-tabs .nav-link:hover {
  color: #2d3748;
  border-bottom: 3px solid rgba(0, 0, 0, 0.1);
}
.nav-tabs .nav-link.active {
  color: #3182ce;
  background: none;
  border: none;
  border-bottom: 3px solid #3182ce;
}
</style>
