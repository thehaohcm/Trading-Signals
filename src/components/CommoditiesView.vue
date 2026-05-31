<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />

    <div class="container mt-4 flex-grow-1 pb-5">
      <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2 pt-2">
        <h2 class="mb-0 fw-bold d-flex align-items-center gap-2 text-white">
          <span>🏆</span> Commodities Terminal
        </h2>
        <span class="badge bg-primary px-3 py-2 shadow-sm" style="background-color: #f59e0b !important; color: #0d0f17 !important; font-size: 0.88rem; font-weight: 700;">
          Gold • Silver • Crude Oil
        </span>
      </div>

      <!-- Main Commodities Tabs -->
      <ul class="nav nav-pills nav-fill mb-4 p-2 glass-pills rounded-3 border-glass" role="tablist">
        <li class="nav-item" role="presentation">
          <button 
            class="nav-link fw-bold" 
            :class="{ active: selectedCommodity === 'gold', 'bg-warning text-dark': selectedCommodity === 'gold' }"
            @click="selectedCommodity = 'gold'"
            type="button"
          >
            <i class="bi bi-stopwatch"></i> Gold
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button 
            class="nav-link fw-bold" 
            :class="{ active: selectedCommodity === 'silver', 'bg-secondary text-white': selectedCommodity === 'silver' }"
            @click="selectedCommodity = 'silver'"
            type="button"
          >
            <i class="bi bi-moon-stars"></i> Silver
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button 
            class="nav-link fw-bold" 
            :class="{ active: selectedCommodity === 'oil', 'bg-dark text-white': selectedCommodity === 'oil' }"
            @click="selectedCommodity = 'oil'"
            type="button"
          >
            <i class="bi bi-fuel-pump"></i> Oil
          </button>
        </li>
      </ul>

      <!-- Toggle Content based on Commodity -->
      <div v-show="selectedCommodity === 'gold'">
        <!-- Gold Spread Widget -->
        <div class="gold-spread-widget mb-4">
          <div v-if="spreadLoading" class="card border-0 shadow-sm rounded-4 glass-panel border-glass p-4 text-center">
            <div class="spinner-border text-warning mb-2" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="text-secondary mb-0 small">Đang tính toán chênh lệch giá vàng thế giới...</p>
          </div>
          
          <div v-else-if="spreadData" class="card border-0 shadow-sm rounded-4 overflow-hidden glass-panel border-glass">
            <div class="card-header bg-gradient-gold py-2.5 px-4 d-flex justify-content-between align-items-center border-0">
              <div class="d-flex align-items-center gap-2">
                <span class="fs-5">🏆</span>
                <h6 class="mb-0 fw-bold text-dark" style="font-family: 'Outfit', sans-serif;">Chênh Lệch Vàng VN vs Thế Giới</h6>
              </div>
              <div class="d-flex align-items-center gap-2">
                <span class="small text-dark-emphasis d-none d-sm-inline" style="font-size: 0.75rem; font-weight: 600;">Cập nhật: {{ spreadData.updatedAt }}</span>
                <button class="btn btn-xs btn-outline-dark rounded-pill py-0.5 px-2.5 d-flex align-items-center gap-1 btn-refresh" style="font-size: 0.72rem; font-weight: 700; border-color: rgba(0,0,0,0.2);" @click="fetchSpreadData" :disabled="spreadLoading">
                  <i class="bi bi-arrow-clockwise"></i> Làm mới
                </button>
              </div>
            </div>
            
            <div class="card-body p-3">
              <div class="row g-3 align-items-stretch">
                
                <!-- Vietnam Gold Card -->
                <div class="col-md-4">
                  <div class="p-3 rounded-4 glass-card border-top border-4 border-warning h-100 d-flex flex-column justify-content-between text-center">
                    <div>
                      <span class="text-uppercase text-secondary fw-bold small ls-1 d-block mb-1" style="font-size: 0.72rem;">Vàng SJC</span>
                      <h4 class="fw-bold mb-0 text-dark" style="font-size: 1.25rem;">{{ formatMillions(spreadData.vnSell) }} <span class="fs-6 text-muted" style="font-size: 0.8rem;">/ lượng</span></h4>
                    </div>
                    <div class="d-flex justify-content-center gap-3 small text-secondary border-top pt-2 mt-2" style="font-size: 0.72rem; border-color: rgba(255,255,255,0.06) !important;">
                      <span>Mua: {{ formatMillions(spreadData.vnBuy) }}</span>
                      <span class="text-secondary opacity-50">|</span>
                      <span>Bán: {{ formatMillions(spreadData.vnSell) }}</span>
                    </div>
                  </div>
                </div>
                
                <!-- World Gold Card -->
                <div class="col-md-4">
                  <div class="p-3 rounded-4 glass-card border-top border-4 border-primary h-100 d-flex flex-column justify-content-between text-center">
                    <div>
                      <span class="text-uppercase text-secondary fw-bold small ls-1 d-block mb-1" style="font-size: 0.72rem;">Vàng Thế Giới (Quy đổi)</span>
                      <h4 class="fw-bold mb-0 text-dark" style="font-size: 1.25rem;">{{ formatMillions(spreadData.worldVnd) }} <span class="fs-6 text-muted" style="font-size: 0.8rem;">/ lượng</span></h4>
                    </div>
                    <div class="d-flex justify-content-center gap-3 small text-secondary border-top pt-2 mt-2" style="font-size: 0.72rem; border-color: rgba(255,255,255,0.06) !important;">
                      <span>Thế giới: ${{ spreadData.worldUsd.toFixed(2) }} / oz</span>
                      <span class="text-secondary opacity-50">|</span>
                      <span>Tỷ giá: {{ formatCurrency(spreadData.usdVndRate) }}</span>
                    </div>
                  </div>
                </div>
                
                <!-- Spread Card -->
                <div class="col-md-4">
                  <div class="p-3 rounded-4 spread-card h-100 text-center d-flex flex-column justify-content-center border-top border-4 border-danger shadow-sm">
                    <span class="text-uppercase text-secondary fw-bold small ls-1 d-block mb-1" style="font-size: 0.72rem;">Chênh Lệch</span>
                    <h3 class="fw-extrabold mb-1 text-neon-red" style="font-size: 1.35rem; font-family: 'Outfit', sans-serif;">
                      +{{ formatMillions(spreadData.spreadVnd) }}
                    </h3>
                    <div>
                      <span class="badge rounded-pill bg-neon-red-badge px-2.5 py-1" style="font-size: 0.72rem;">
                        Cao hơn thế giới {{ spreadData.spreadPercent.toFixed(1) }}%
                      </span>
                    </div>
                  </div>
                </div>
                
              </div>
            </div>
          </div>
        </div>

        <!-- Gold Sub-Tabs -->
        <ul class="nav nav-tabs mb-3" role="tablist">
          <li class="nav-item">
            <button class="nav-link" :class="{ active: goldTab === 'world' }" @click="goldTab = 'world'">
              <i class="bi bi-globe"></i> World Gold Price
            </button>
          </li>
          <li class="nav-item">
            <button class="nav-link" :class="{ active: goldTab === 'vietnam' }" @click="goldTab = 'vietnam'">
              <i class="bi bi-flag"></i> Vietnam Gold Price
            </button>
          </li>
        </ul>

        <!-- Gold Content -->
        <div class="tab-content">
          <div v-show="goldTab === 'world'" class="tab-pane fade show active">
            <TradingViewChart :coin="'OANDA:XAUUSD'" :height="380" />
            <PriceAlertWidget symbol="XAUUSD" assetType="gold" />
          </div>

          <div v-show="goldTab === 'vietnam'" class="tab-pane fade show active">
            <div class="card shadow-sm border-glass rounded-3 overflow-hidden glass-panel">
              <div class="card-header bg-warning-dark text-white d-flex justify-content-between align-items-center border-0">
                 <h5 class="mb-0 fw-bold d-flex align-items-center gap-2"><i class="bi bi-coin"></i> Gold Price in Vietnam</h5>
                 <span v-if="goldValues.latestDate" class="small">Updated: {{ goldValues.latestDate }}</span>
              </div>
              <div class="card-body">
                <div v-if="goldValues.loading" class="text-center py-4">
                  <div class="spinner-border text-warning" role="status"></div>
                </div>
                <div v-else-if="goldValues.error" class="alert alert-danger">
                  {{ goldValues.error }}
                </div>
                <div v-else-if="goldValues.data.length" class="table-responsive">
                    <table class="table table-hover table-striped">
                    <thead class="table-warning">
                      <tr>
                        <th>Type</th>
                        <th>Branch</th>
                        <th class="text-end">Buy Price</th>
                        <th class="text-end">Sell Price</th>
                        <th class="text-end">Spread</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in goldValues.data" :key="item.Id">
                        <td><strong>{{ item.TypeName }}</strong></td>
                        <td><span class="badge bg-secondary">{{ item.BranchName }}</span></td>
                        <td class="text-end text-success"><strong>{{ item.Buy }}</strong></td>
                        <td class="text-end text-danger"><strong>{{ item.Sell }}</strong></td>
                        <td class="text-end"><span class="badge bg-info">{{ calculateSpread(item.BuyValue, item.SellValue) }}</span></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="alert alert-info">No data available.</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-show="selectedCommodity === 'silver'">
        <!-- Silver Sub-Tabs -->
        <ul class="nav nav-tabs mb-3" role="tablist">
          <li class="nav-item">
            <button class="nav-link" :class="{ active: silverTab === 'world' }" @click="silverTab = 'world'">
              <i class="bi bi-globe"></i> World Silver Price
            </button>
          </li>
          <li class="nav-item">
            <button class="nav-link" :class="{ active: silverTab === 'vietnam' }" @click="silverTab = 'vietnam'">
              <i class="bi bi-flag"></i> Vietnam Silver Price
            </button>
          </li>
        </ul>

         <!-- Silver Content -->
         <div class="tab-content">
          <div v-show="silverTab === 'world'" class="tab-pane fade show active">
             <TradingViewChart :coin="'OANDA:XAGUSD'" :height="380" />
             <PriceAlertWidget symbol="XAGUSD" assetType="silver" />
          </div>

          <div v-show="silverTab === 'vietnam'" class="tab-pane fade show active">
            <div class="card border-glass rounded-3 overflow-hidden glass-panel">
              <div class="card-header bg-secondary text-white d-flex justify-content-between align-items-center border-0">
                  <h5 class="mb-0 fw-bold d-flex align-items-center gap-2"><i class="bi bi-coin"></i> Silver Price in Vietnam</h5>
                  <span v-if="silverValues.lastUpdated" class="small">Updated: {{ silverValues.lastUpdated }}</span>
               </div>
               <div class="card-body">
                   <div v-if="silverValues.loading" class="text-center py-4">
                     <div class="spinner-border text-secondary" role="status"></div>
                   </div>
                   <div v-else-if="silverValues.error" class="alert alert-danger">{{ silverValues.error }}</div>
                   <div v-else-if="silverValues.htmlContent" v-html="silverValues.htmlContent" class="silver-content"></div>
                   <div v-else class="alert alert-info">No data available.</div>
               </div>
             </div>
          </div>
        </div>
      </div>

      <div v-show="selectedCommodity === 'oil'">
        <!-- Oil Sub-Tabs -->
        <ul class="nav nav-tabs mb-3" role="tablist">
          <li class="nav-item">
            <button class="nav-link" :class="{ active: oilTab === 'wti' }" @click="oilTab = 'wti'">
              <i class="bi bi-globe"></i> WTI (USOIL)
            </button>
          </li>
          <li class="nav-item">
            <button class="nav-link" :class="{ active: oilTab === 'brent' }" @click="oilTab = 'brent'">
              <i class="bi bi-globe"></i> BRENT (UKOIL)
            </button>
          </li>
        </ul>

        <div class="tab-content">
          <div v-show="oilTab === 'wti'" class="tab-pane fade show active">
            <TradingViewChart :coin="'TVC:USOIL'" :height="380" />
          </div>
          <div v-show="oilTab === 'brent'" class="tab-pane fade show active">
            <TradingViewChart :coin="'TVC:UKOIL'" :height="380" />
          </div>
        </div>
      </div>

    </div>
    <AppFooter />
  </div>
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';
import TradingViewChart from './TradingViewChart.vue'
import PriceAlertWidget from './PriceAlertWidget.vue';
import { ref, onMounted, watch, onBeforeUnmount } from 'vue';

export default {
  name: 'CommoditiesView',
  components: {
    NavBar,
    AppFooter,
    TradingViewChart,
    PriceAlertWidget,
  },
  setup() {
    const selectedCommodity = ref('gold');
    const goldTab = ref('world');
    const silverTab = ref('world');
    const oilTab = ref('wti');

    // Gold State
    const goldValues = ref({
        data: [],
        latestDate: null,
        loading: false,
        error: null
    });

    // Silver State
    const silverValues = ref({
        htmlContent: null,
        lastUpdated: null,
        loading: false,
        error: null
    });

    // Fetch Methods
    const fetchGoldPrices = async () => {
      goldValues.value.loading = true;
      goldValues.value.error = null;
      let success = false;

      // 1. Try local/proxy relative SJC API
      try {
        const response = await fetch('/goldprice/services/priceservice.ashx');
        if (response.ok && response.headers.get('content-type')?.includes('json')) {
          const result = await response.json();
          if (result.success && Array.isArray(result.data) && result.data.length > 0) {
            goldValues.value.data = result.data;
            goldValues.value.latestDate = result.latestDate;
            success = true;
          }
        }
      } catch (err) {
        console.warn('Relative SJC fetch failed, trying absolute...', err);
      }

      // 2. Try absolute Vercel path
      if (!success) {
        try {
          const response = await fetch('https://trading-signals-pi.vercel.app/goldprice/services/priceservice.ashx');
          if (response.ok && response.headers.get('content-type')?.includes('json')) {
            const result = await response.json();
            if (result.success && Array.isArray(result.data) && result.data.length > 0) {
              goldValues.value.data = result.data;
              goldValues.value.latestDate = result.latestDate;
              success = true;
            }
          }
        } catch (err) {
          console.warn('Absolute SJC fetch failed, trying fallback...', err);
        }
      }

      // 3. Fallback to giavang.now public API
      if (!success) {
        try {
          const response = await fetch('https://giavang.now/api/prices');
          if (response.ok) {
            const result = await response.json();
            if (result && result.success && result.prices) {
              const rows = [];
              for (const [key, item] of Object.entries(result.prices)) {
                if (key === 'XAUUSD') continue; // Skip world gold
                rows.push({
                  Id: key,
                  TypeName: item.name || key,
                  BranchName: item.name?.toLowerCase().includes('hanoi') || item.name?.toLowerCase().includes('hà nội') ? 'Hà Nội' : 'TP.HCM',
                  Buy: String(item.buy),
                  Sell: String(item.sell),
                  BuyValue: item.buy,
                  SellValue: item.sell
                });
              }
              if (rows.length > 0) {
                goldValues.value.data = rows;
                goldValues.value.latestDate = `${result.date || ''} ${result.time || ''}`.trim();
                success = true;
              }
            }
          }
        } catch (err) {
          console.error('All SJC gold price API sources failed:', err);
        }
      }

      if (!success) {
        goldValues.value.error = 'Unable to load gold prices.';
      }
      goldValues.value.loading = false;
    };

    const fetchSilverPrices = async () => {
      silverValues.value.loading = true;
      silverValues.value.error = null;
      try {
        const response = await fetch('/silverprice/silverpricePartial', {
          headers: { 'Accept': 'text/html, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        silverValues.value.htmlContent = await response.text();
        silverValues.value.lastUpdated = new Date().toLocaleString('vi-VN');
      } catch (err) {
          console.error(err);
          silverValues.value.error = 'Unable to load silver prices.';
      } finally {
          silverValues.value.loading = false;
      }
    };

    // Helpers
    const calculateSpread = (buy, sell) => {
       return new Intl.NumberFormat('vi-VN').format(sell - buy);
    };

    const spreadData = ref(null);
    const spreadLoading = ref(false);

    const formatCurrency = (val) => {
      if (val === null || val === undefined) return 'N/A';
      return new Intl.NumberFormat('vi-VN').format(val) + ' VND';
    };

    const formatMillions = (val) => {
      if (val === null || val === undefined) return 'N/A';
      const millions = val / 1000000;
      return millions.toLocaleString('vi-VN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' triệu';
    };

    const fetchSpreadData = async () => {
      spreadLoading.value = true;
      let vnGoldBuy = null;
      let vnGoldSell = null;
      let worldGoldUsd = null;
      let usdVndRate = 25450;

      // 1. Fetch USD/VND and XAUUSD from /api/rates
      try {
        const res = await fetch('/api/rates');
        if (res.ok) {
          const rates = await res.json();
          if (Array.isArray(rates)) {
            const usdVndItem = rates.find(item => {
              const code = String(item.currency || item.symbol || item.pair || '').toUpperCase().replace(/[^A-Z]/g, '');
              return code === 'USDVND';
            });
            if (usdVndItem) {
              const rateVal = parseFloat(usdVndItem.rate || usdVndItem.close || usdVndItem.bid || usdVndItem.ask);
              if (rateVal > 0) usdVndRate = rateVal;
            }

            const xauUsdItem = rates.find(item => {
              const code = String(item.currency || item.symbol || item.pair || '').toUpperCase().replace(/[^A-Z]/g, '');
              return code === 'XAUUSD' || code === 'GOLD';
            });
            if (xauUsdItem) {
              const xauVal = parseFloat(xauUsdItem.rate || xauUsdItem.close || xauUsdItem.bid || xauUsdItem.ask);
              if (xauVal > 0) worldGoldUsd = xauVal;
            }
          }
        }
      } catch (err) {
        console.warn('Failed to fetch /api/rates:', err);
      }

      // 2. Fetch Vietnam Gold from SJC proxy
      try {
        const res = await fetch('/goldprice/services/priceservice.ashx');
        if (res.ok) {
          const result = await res.json();
          if (result.success && Array.isArray(result.data) && result.data.length > 0) {
            const sjcItem = result.data.find(item => item.TypeName.includes('SJC') && item.BranchName.includes('HCM')) ||
                            result.data.find(item => item.TypeName.includes('SJC'));
            if (sjcItem) {
              vnGoldBuy = sjcItem.BuyValue || parseFloat(sjcItem.Buy.replace(/,/g, ''));
              vnGoldSell = sjcItem.SellValue || parseFloat(sjcItem.Sell.replace(/,/g, ''));
            }
          }
        }
      } catch (err) {
        console.warn('Failed to fetch SJC proxy:', err);
      }

      // 3. Fetch from public giavang.now API
      try {
        const res = await fetch('https://giavang.now/api/prices');
        if (res.ok) {
          const result = await res.json();
          if (result && result.success && result.prices) {
            if (result.prices.XAUUSD) {
              worldGoldUsd = result.prices.XAUUSD.buy || result.prices.XAUUSD.sell || worldGoldUsd;
            }
            
            if (!vnGoldBuy || !vnGoldSell) {
              const pricesArray = Object.entries(result.prices);
              const sjcKeyVal = pricesArray.find(([, item]) => item.name?.includes('SJC') && item.name?.includes('HCM')) ||
                                pricesArray.find(([, item]) => item.name?.includes('SJC'));
              if (sjcKeyVal) {
                const sjcItem = sjcKeyVal[1];
                vnGoldBuy = sjcItem.buy;
                vnGoldSell = sjcItem.sell;
              }
            }
          }
        }
      } catch (err) {
        console.warn('Failed to fetch giavang.now:', err);
      }

      // Final fallbacks if we still don't have prices
      if (!vnGoldBuy || !vnGoldSell) {
        vnGoldBuy = 88500000;
        vnGoldSell = 90500000;
      }
      if (!worldGoldUsd) {
        worldGoldUsd = 2350;
      }

      const worldGoldVndPerTael = worldGoldUsd * 1.20565 * usdVndRate;
      const spreadVnd = vnGoldSell - worldGoldVndPerTael;
      const spreadPercent = (spreadVnd / worldGoldVndPerTael) * 100;

      spreadData.value = {
        vnBuy: vnGoldBuy,
        vnSell: vnGoldSell,
        worldUsd: worldGoldUsd,
        worldVnd: worldGoldVndPerTael,
        spreadVnd: spreadVnd,
        spreadPercent: spreadPercent,
        usdVndRate: usdVndRate,
        updatedAt: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      };
      spreadLoading.value = false;
    };

    let intervalId = null;

    onMounted(() => {
        fetchGoldPrices();
        fetchSilverPrices();
        fetchSpreadData();

        intervalId = setInterval(() => {
            if (selectedCommodity.value === 'gold' && goldTab.value === 'vietnam') fetchGoldPrices();
            if (selectedCommodity.value === 'silver' && silverTab.value === 'vietnam') fetchSilverPrices();
            fetchSpreadData();
        }, 5 * 60 * 1000);
    });

    onBeforeUnmount(() => {
        if(intervalId) clearInterval(intervalId);
    });

    watch(goldTab, (newVal) => {
        if (newVal === 'vietnam' && !goldValues.value.data.length) fetchGoldPrices();
    });

    watch(silverTab, (newVal) => {
        if (newVal === 'vietnam' && !silverValues.value.htmlContent) fetchSilverPrices();
    });

    return {
        selectedCommodity,
        goldTab,
        silverTab,
        oilTab,
        goldValues,
        silverValues,
        calculateSpread,
        spreadData,
        spreadLoading,
        fetchSpreadData,
        formatCurrency,
        formatMillions
    };
  }
};
</script>

<style scoped>
.nav-pills .nav-link {
    border-radius: 0.5rem;
    transition: all 0.3s;
}
.nav-pills .nav-link:hover {
    transform: translateY(-2px);
}
.nav-tabs .nav-link {
    cursor: pointer;
}
.silver-content {
  width: 100%;
  overflow-x: auto;
}
.silver-content :deep(table) {
  width: 100%;
  margin-bottom: 0;
}
.silver-content :deep(table tbody tr:hover) {
  background-color: #e2e3e5;
}

.bg-gradient-gold {
  background: linear-gradient(135deg, #fde047 0%, #f59e0b 100%);
}

.bg-gold-light {
  background-color: #fffdf5;
}

.fw-extrabold {
  font-weight: 800;
}

.ls-1 {
  letter-spacing: 0.5px;
}

.spread-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.spread-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.1);
}

.btn-refresh {
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-refresh:hover {
  transform: rotate(30deg);
}
</style>
