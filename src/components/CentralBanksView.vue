<template>
  <div class="d-flex flex-column min-vh-100">
    <NavBar />
    <div class="container mt-4 flex-grow-1">
      <!-- Title -->
      <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2 pt-2">
        <h2 class="mb-0 fw-bold d-flex align-items-center gap-2 text-slate-800">
          <span>🏛️</span> Central Banks & Macro Rates
        </h2>
        <span class="badge bg-primary px-3 py-2 shadow-sm" style="background-color: #3b82f6 !important; font-size: 0.88rem; font-weight: 600;">
          Macro Intel Hub
        </span>
      </div>

      <!-- Introduction Panel -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="card border-0 shadow-sm glass-panel border-glass" style="border-left: 4px solid #3b82f6 !important;">
            <div class="card-body py-3">
              <p class="mb-0" style="color: #475569; font-size: 0.95rem; line-height: 1.6;">
                Track monetary policy expectations and macro pivot points. "Global Bond Yields" provide real-time cost of capital across major economies, while "Rate Probabilities" show the market's expected target interest rates derived from futures trading prices.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Top-Level Tabs -->
      <ul class="nav nav-pills mb-4 gap-2" role="tablist">
        <li class="nav-item">
          <button 
            class="nav-link rounded-pill px-4 fw-semibold" 
            :class="{ active: mainTab === 'bonds', 'bg-primary text-white shadow-sm': mainTab === 'bonds', 'bg-light text-secondary': mainTab !== 'bonds' }" 
            @click="mainTab = 'bonds'"
          >
            📊 Global Bond Yields
          </button>
        </li>
        <li class="nav-item">
          <button 
            class="nav-link rounded-pill px-4 fw-semibold" 
            :class="{ active: mainTab === 'rates', 'bg-primary text-white shadow-sm': mainTab === 'rates', 'bg-light text-secondary': mainTab !== 'rates' }" 
            @click="mainTab = 'rates'"
          >
            🏦 Rate Probabilities
          </button>
        </li>
      </ul>

      <!-- Bonds Tab Content -->
      <div v-if="mainTab === 'bonds'">
        <ul class="nav nav-tabs mb-4" role="tablist">
          <li class="nav-item" v-for="country in bondCountries" :key="country.id">
            <button 
              class="nav-link" 
              :class="{ active: activeBondTab === country.id }" 
              @click="activeBondTab = country.id"
            >
              {{ country.flag }} {{ country.name }}
            </button>
          </li>
        </ul>
        
        <div class="row g-4">
          <div class="col-lg-6">
            <div class="card border-0 shadow-sm border-glass rounded-3 overflow-hidden glass-panel">
              <div class="card-header bg-warning-dark py-3 px-4 border-0">
                <h5 class="mb-0 fw-bold text-slate-800" style="font-family: 'Outfit', sans-serif;">2-Year Bond Yield</h5>
              </div>
              <div class="card-body p-0">
                 <TradingViewChart v-if="currentBond2Y" :coin="currentBond2Y" :height="400" />
              </div>
            </div>
          </div>
          <div class="col-lg-6">
            <div class="card border-0 shadow-sm border-glass rounded-3 overflow-hidden glass-panel">
              <div class="card-header bg-warning-dark py-3 px-4 border-0">
                <h5 class="mb-0 fw-bold text-slate-800" style="font-family: 'Outfit', sans-serif;">10-Year Bond Yield</h5>
              </div>
              <div class="card-body p-0">
                 <TradingViewChart v-if="currentBond10Y" :coin="currentBond10Y" :height="400" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Rates Probabilities Tab Content -->
      <div v-if="mainTab === 'rates'">
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
              <div class="card-header bg-warning-dark d-flex justify-content-between align-items-center py-3 px-4 border-0">
                <h5 class="mb-0 fw-bold text-slate-800 d-flex align-items-center gap-2" style="font-family: 'Outfit', sans-serif;">
                  <span>{{ tab.flag }}</span> {{ tab.title }}
                </h5>
                <a :href="tab.url" target="_blank" class="btn btn-sm btn-outline-primary px-3" style="font-weight: 600; border-color: rgba(59, 130, 246, 0.2);">
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

    </div>
    <AppFooter class="mt-5" />
  </div>
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';
import TradingViewChart from './TradingViewChart.vue';
import { ref, computed } from 'vue';

export default {
  name: 'CentralBanksView',
  components: {
    NavBar,
    AppFooter,
    TradingViewChart
  },
  setup() {
    const mainTab = ref('bonds');
    
    // Rate Probabilities states
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

    // Bond Yields states
    const activeBondTab = ref('us');
    const bondCountries = ref([
      { id: 'us', name: 'US', flag: '🇺🇸', sym2y: 'TVC:US02Y', sym10y: 'TVC:US10Y' },
      { id: 'uk', name: 'UK', flag: '🇬🇧', sym2y: 'TVC:GB02Y', sym10y: 'TVC:GB10Y' },
      { id: 'eu', name: 'Europe', flag: '🇪🇺', sym2y: 'TVC:DE02Y', sym10y: 'TVC:DE10Y' },
      { id: 'jp', name: 'Japan', flag: '🇯🇵', sym2y: 'TVC:JP02Y', sym10y: 'TVC:JP10Y' },
      { id: 'kr', name: 'South Korea', flag: '🇰🇷', sym2y: 'TVC:KR02Y', sym10y: 'TVC:KR10Y' },
      { id: 'cn', name: 'China', flag: '🇨🇳', sym2y: 'TVC:CN02Y', sym10y: 'TVC:CN10Y' },
      { id: 'vn', name: 'Vietnam', flag: '🇻🇳', sym2y: 'VN02Y', sym10y: 'VN10Y' } // Best effort symbols for VN
    ]);

    const currentBond2Y = computed(() => {
      const country = bondCountries.value.find(c => c.id === activeBondTab.value);
      return country ? country.sym2y : '';
    });

    const currentBond10Y = computed(() => {
      const country = bondCountries.value.find(c => c.id === activeBondTab.value);
      return country ? country.sym10y : '';
    });

    return {
      mainTab,
      activeTab,
      tabs,
      activeBondTab,
      bondCountries,
      currentBond2Y,
      currentBond10Y
    };
  }
};
</script>

<style scoped>
.nav-tabs {
  border-bottom: 1px solid rgba(0, 0, 0, 0.08) !important;
}
.nav-tabs .nav-link {
  color: #64748b;
  border: none;
  background: none;
  font-weight: 600;
  padding: 12px 24px;
  transition: all 0.2s;
  border-radius: 0;
  border-bottom: 3px solid transparent;
}
.nav-tabs .nav-link:hover {
  color: #0f172a;
  border-bottom: 3px solid rgba(0, 0, 0, 0.06);
}
.nav-tabs .nav-link.active {
  color: #3b82f6 !important;
  background: none;
  border: none;
  border-bottom: 3px solid #3b82f6 !important;
}

.nav-pills .nav-link {
  transition: all 0.3s;
}

.glass-panel {
  background: #ffffff !important;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04) !important;
}
.border-glass {
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
}
.bg-warning-dark {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
}
</style>
