<template>
  <div class="d-flex flex-column min-vh-100 bg-dark text-white" style="background-color: #141622 !important;">
    <NavBar />
    <div class="container mt-4 flex-grow-1">
      <!-- Title -->
      <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h2 class="mb-0 fw-bold d-flex align-items-center gap-2">
          <span>🏛️</span> Central Banks Rate Probabilities
        </h2>
        <span class="badge bg-primary px-3 py-2 shadow-sm" style="background-color: #3182ce !important; font-size: 0.9rem;">
          Macro Intel Hub
        </span>
      </div>

      <!-- Introduction Panel -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="card border-0 shadow-sm" style="background: linear-gradient(135deg, #1e2230 0%, #151821 100%); border-left: 4px solid #3182ce !important;">
            <div class="card-body text-light py-3">
              <p class="mb-0" style="color: #cbd5e0; font-size: 0.95rem; line-height: 1.6;">
                Rate probabilities show the market's expected target interest rates derived from futures trading prices. Use these indicators to track monetary policy expectations, forecast policy changes, and identify potential macro pivot points across major global central banks.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab Buttons -->
      <ul class="nav nav-tabs mb-4 border-bottom-secondary" id="centralBankTabs" role="tablist">
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
          <div class="card border-0 shadow-lg" style="background-color: #1e2230; border-radius: 12px; overflow: hidden;">
            <!-- Header -->
            <div class="card-header bg-gradient-dark d-flex justify-content-between align-items-center py-3 px-4">
              <h5 class="mb-0 fw-bold text-white d-flex align-items-center gap-2">
                <span>{{ tab.flag }}</span> {{ tab.title }}
              </h5>
              <a v-if="tab.embedUrl" :href="tab.url" target="_blank" class="btn btn-sm btn-outline-info px-3">
                Open Official Site ↗
              </a>
            </div>
            
            <!-- Body -->
            <div class="card-body p-0">
              <!-- Embed Chart -->
              <div v-if="tab.embedUrl" class="embed-responsive-container">
                <iframe 
                  :src="tab.embedUrl" 
                  class="embed-iframe" 
                  frameborder="0" 
                  allowfullscreen
                ></iframe>
              </div>
              
              <!-- BOJ Placeholder & Analysis -->
              <div v-else class="boj-container p-5 text-center">
                <div class="boj-content mx-auto" style="max-width: 650px;">
                  <span class="boj-icon">🇯🇵</span>
                  <h4 class="mt-4 text-warning fw-bold">Bank of Japan (BOJ) Interest Rate Policy</h4>
                  
                  <p class="text-light mt-3" style="color: #a0aec0 !important; font-size: 0.97rem; line-height: 1.7;">
                    Market-implied rate probabilities are not directly available for the Bank of Japan (BOJ) because Japan's policy rate futures markets are not as active or standardized as the Fed Funds Futures (US) or SONIA Futures (UK).
                  </p>
                  
                  <p class="text-light" style="color: #a0aec0 !important; font-size: 0.97rem; line-height: 1.7;">
                    To gauge market expectations, analysts and the BOJ utilize **TONA (Tokyo Overnight Average Rate)** and overnight index swaps (OIS) instead of direct interest rate futures probabilities.
                  </p>
                  
                  <div class="boj-policy-card p-4 my-4 text-start border rounded" style="background-color: #151821; border-color: #2d3748 !important;">
                    <h6 class="text-info fw-bold mb-3 d-flex align-items-center gap-2">
                      <span style="font-size: 1.1rem;">📊</span> Current Policy Stance (2026):
                    </h6>
                    <ul class="mb-0 text-light list-unstyled" style="padding-left: 0;">
                      <li class="mb-3 d-flex align-items-start gap-2">
                        <span class="text-info">•</span>
                        <div>
                          <strong>Policy Interest Rate:</strong> <span class="text-warning">0.25%</span> (Raised in July 2024, successfully exiting the decades-long Negative Interest Rate Policy).
                        </div>
                      </li>
                      <li class="mb-3 d-flex align-items-start gap-2">
                        <span class="text-info">•</span>
                        <div>
                          <strong>Yield Curve Control (YCC):</strong> Terminated in March 2024, letting market forces determine long-term 10-year JGB yields while maintaining stable sovereign purchases.
                        </div>
                      </li>
                      <li class="d-flex align-items-start gap-2">
                        <span class="text-info">•</span>
                        <div>
                          <strong>Policy Target:</strong> Achieving a sustainable 2.0% inflation target driven by robust domestic demand and wage growth.
                        </div>
                      </li>
                    </ul>
                  </div>
                  
                  <a href="https://www.boj.or.jp/en/mopo/index.htm" target="_blank" class="btn btn-outline-warning px-4 py-2 mt-2 fw-semibold">
                    View Official BOJ Monetary Policy Releases ↗
                  </a>
                </div>
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
      },
      {
        id: 'boj',
        name: 'BOJ',
        flag: '🇯🇵',
        title: 'Bank of Japan Monetary Policy Expectations (JP)',
        url: 'https://www.boj.or.jp/en/mopo/index.htm',
        embedUrl: '' // Empty so it renders the custom BOJ card
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
.bg-gradient-dark {
  background: linear-gradient(135deg, #1f222e 0%, #151821 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.embed-responsive-container {
  position: relative;
  width: 100%;
  height: 650px;
  overflow: hidden;
  background-color: #1a1d29;
}
.embed-iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 0;
}
.nav-tabs {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
}
.nav-tabs .nav-link {
  color: #a0aec0;
  border: none;
  background: none;
  font-weight: 600;
  padding: 12px 24px;
  transition: all 0.2s;
  border-radius: 0;
  border-bottom: 3px solid transparent;
}
.nav-tabs .nav-link:hover {
  color: #e2e8f0;
  border-bottom: 3px solid rgba(255, 255, 255, 0.2);
}
.nav-tabs .nav-link.active {
  color: #63b3ed;
  background: none;
  border: none;
  border-bottom: 3px solid #63b3ed;
}
.boj-container {
  background-color: #1a1d29;
  padding: 60px 20px !important;
}
.boj-icon {
  font-size: 64px;
  line-height: 1;
}
.boj-policy-card li {
  line-height: 1.6;
}
</style>
