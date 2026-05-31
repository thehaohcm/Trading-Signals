<template>
  <div class="d-flex flex-column min-vh-100">
    <NavBar />
    <div class="container mt-4 flex-grow-1">
      <!-- Title -->
      <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2 pt-2">
        <h2 class="mb-0 fw-bold d-flex align-items-center gap-2 text-white">
          <span>🏛️</span> Central Banks Rate Probabilities
        </h2>
        <span class="badge bg-primary px-3 py-2 shadow-sm" style="background-color: #3b82f6 !important; font-size: 0.88rem; font-weight: 600;">
          Macro Intel Hub
        </span>
      </div>

      <!-- Introduction Panel -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="card border-0 shadow-sm glass-panel border-glass" style="border-left: 4px solid #3b82f6 !important;">
            <div class="card-body text-secondary py-3">
              <p class="mb-0" style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.6;">
                Rate probabilities show the market's expected target interest rates derived from futures trading prices. Use these indicators to track monetary policy expectations, forecast policy changes, and identify potential macro pivot points across major global central banks.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab Buttons -->
      <ul class="nav nav-tabs mb-4" id="centralBankTabs" role="tablist">
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
          <div class="card border-0 shadow-sm border-glass rounded-3 overflow-hidden glass-panel">
            <!-- Header -->
            <div class="card-header bg-warning-dark text-white d-flex justify-content-between align-items-center py-3 px-4 border-0">
              <h5 class="mb-0 fw-bold text-white d-flex align-items-center gap-2" style="font-family: 'Outfit', sans-serif;">
                <span>{{ tab.flag }}</span> {{ tab.title }}
              </h5>
              <a :href="tab.url" target="_blank" class="btn btn-sm btn-outline-light px-3" style="font-weight: 600; border-color: rgba(255,255,255,0.2);">
                Open Official Site ↗
              </a>
            </div>
            
            <!-- Body -->
            <div class="card-body p-0">
              <!-- Embed Chart as requested exactly by user -->
              <iframe 
                :src="tab.embedUrl" 
                width="100%" 
                height="450" 
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
  name: 'CentralBanksView',
  components: {
    NavBar,
    AppFooter
  },
  setup() {
    const activeTab = ref('fed');

    const tabs = ref([
      {
        id: 'fed',
        name: 'FED',
        flag: '🇺🇸',
        title: 'Federal Reserve Rate Probability Chart (US)',
        url: 'https://centralbank.watch/charts/federal-reserve-rate-probability-chart/',
        embedUrl: 'https://centralbank.watch/charts/federal-reserve-rate-probability-chart/?embed=true'
      },
      {
        id: 'boe',
        name: 'BOE',
        flag: '🇬🇧',
        title: 'Bank of England Rate Probability Chart (UK)',
        url: 'https://centralbank.watch/charts/bank-of-england-rate-probability-chart/',
        embedUrl: 'https://centralbank.watch/charts/bank-of-england-rate-probability-chart/?embed=true'
      },
      {
        id: 'ecb',
        name: 'ECB',
        flag: '🇪🇺',
        title: 'European Central Bank Rate Probability Chart (EU)',
        url: 'https://centralbank.watch/charts/ecb-rate-probability-chart/',
        embedUrl: 'https://centralbank.watch/charts/ecb-rate-probability-chart/?embed=true'
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
}
.nav-tabs .nav-link {
  color: #94a3b8;
  border: none;
  background: none;
  font-weight: 600;
  padding: 12px 24px;
  transition: all 0.2s;
  border-radius: 0;
  border-bottom: 3px solid transparent;
}
.nav-tabs .nav-link:hover {
  color: #f1f5f9;
  border-bottom: 3px solid rgba(255, 255, 255, 0.1);
}
.nav-tabs .nav-link.active {
  color: #3b82f6 !important;
  background: none;
  border: none;
  border-bottom: 3px solid #3b82f6 !important;
}

.glass-panel {
  background: rgba(17, 22, 34, 0.65) !important;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}
.border-glass {
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
}
.bg-warning-dark {
  background: linear-gradient(135deg, #1e293b 0%, #0d0f17 100%) !important;
  border-bottom: 1px solid rgba(255,255,255,0.06) !important;
}
</style>
