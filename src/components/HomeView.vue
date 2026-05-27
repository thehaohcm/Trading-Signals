<template>
  <div id="app" class="d-flex flex-column min-vh-100 bg-light-gray">
    <NavBar />
    <notifications />
    
    <div class="home-view container mt-4 flex-grow-1">
      
      <!-- Gold Spread Widget -->
      <div class="gold-spread-widget mb-4">
        <div v-if="loading" class="card border-0 shadow-sm rounded-4 bg-white p-5 text-center">
          <div class="spinner-border text-warning mb-3" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="text-muted mb-0">Đang tải tỷ giá vàng và tính toán chênh lệch...</p>
        </div>
        
        <div v-else-if="data" class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
          <div class="card-header bg-gradient-gold py-3 px-4 d-flex justify-content-between align-items-center border-0">
            <div class="d-flex align-items-center gap-2">
              <span class="fs-4">🏆</span>
              <h4 class="mb-0 fw-bold text-dark">Chênh Lệch Vàng VN vs Thế Giới</h4>
            </div>
            <div class="d-flex align-items-center gap-3">
              <span class="small text-dark-emphasis d-none d-sm-inline">Cập nhật: {{ data.updatedAt }}</span>
              <button class="btn btn-sm btn-outline-dark rounded-pill py-1 px-3 d-flex align-items-center gap-1 btn-refresh" @click="fetchAllData" :disabled="loading">
                <i class="bi bi-arrow-clockwise"></i> Làm mới
              </button>
            </div>
          </div>
          
          <div class="card-body p-4">
            <div class="row g-4 align-items-stretch">
              
              <!-- Vietnam Gold Card -->
              <div class="col-md-4">
                <div class="p-3 rounded-4 bg-light border-start border-4 border-warning h-100 d-flex flex-column justify-content-between">
                  <div>
                    <span class="text-uppercase text-muted fw-bold small ls-1 d-block mb-2">Vàng Trong Nước (SJC)</span>
                    <h3 class="fw-bold mb-1 text-dark">{{ formatMillions(data.vnSell) }} <span class="fs-6 text-muted">/ lượng</span></h3>
                  </div>
                  <div class="d-flex justify-content-between small text-muted border-top pt-2 mt-2">
                    <span>Mua: {{ formatMillions(data.vnBuy) }}</span>
                    <span>Bán: {{ formatMillions(data.vnSell) }}</span>
                  </div>
                </div>
              </div>
              
              <!-- World Gold Card -->
              <div class="col-md-4">
                <div class="p-3 rounded-4 bg-light border-start border-4 border-primary h-100 d-flex flex-column justify-content-between">
                  <div>
                    <span class="text-uppercase text-muted fw-bold small ls-1 d-block mb-2">Vàng Thế Giới (Quy đổi)</span>
                    <h3 class="fw-bold mb-1 text-dark">{{ formatMillions(data.worldVnd) }} <span class="fs-6 text-muted">/ lượng</span></h3>
                  </div>
                  <div class="d-flex justify-content-between small text-muted border-top pt-2 mt-2">
                    <span>Thế giới: ${{ data.worldUsd.toFixed(2) }} / oz</span>
                    <span>Tỷ giá: {{ formatCurrency(data.usdVndRate) }}</span>
                  </div>
                </div>
              </div>
              
              <!-- Spread Card -->
              <div class="col-md-4">
                <div class="p-3 rounded-4 spread-card bg-gold-light h-100 text-center text-md-start d-flex flex-column justify-content-center border border-warning-subtle">
                  <span class="text-uppercase text-muted fw-bold small ls-1 d-block mb-1">Chênh Lệch Thực Tế</span>
                  <h2 class="fw-extrabold mb-1 text-danger">
                    +{{ formatMillions(data.spreadVnd) }}
                  </h2>
                  <div>
                    <span class="badge rounded-pill fs-6 bg-danger px-3 py-1">
                      Cao hơn thế giới {{ data.spreadPercent.toFixed(1) }}%
                    </span>
                  </div>
                </div>
              </div>
              
            </div>
            
            <div class="text-center mt-3 text-muted small">
              <i class="bi bi-info-circle me-1"></i> Quy đổi: 1 lượng vàng = 1.20565 ounce thế giới, tính theo tỷ giá USD/VND thực tế.
            </div>
          </div>
        </div>
      </div>

      <!-- Tabs and Main Content -->
      <ul class="nav nav-tabs" id="myTab" role="tablist">
        <li class="nav-item" role="presentation">
          <button class="nav-link active fw-bold" id="rrg-tab" data-bs-toggle="tab" data-bs-target="#rrg" type="button" role="tab" aria-controls="rrg" aria-selected="true">RRG Chart</button>
        </li>
      </ul>
      <div class="tab-content" id="myTabContent">
        <div class="tab-pane fade show active" id="rrg" role="tabpanel" aria-labelledby="rrg-tab">
          <div class="d-flex justify-content-center mt-3">
              <img src="/assets_rrgchart" class="img-fluid rounded-4 shadow-sm" alt="RRG Chart" />
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
import { ref, onMounted } from 'vue';

export default {
  name: 'HomeView',
  components: {
    NavBar,
    AppFooter,
  },
  setup() {
    const loading = ref(false);
    const error = ref(null);
    const data = ref(null);

    const formatCurrency = (val) => {
      if (val === null || val === undefined) return 'N/A';
      return new Intl.NumberFormat('vi-VN').format(val) + ' VND';
    };

    const formatMillions = (val) => {
      if (val === null || val === undefined) return 'N/A';
      const millions = val / 1000000;
      return millions.toLocaleString('vi-VN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' triệu';
    };

    const fetchAllData = async () => {
      loading.value = true;
      error.value = null;

      let vnGoldBuy = null;
      let vnGoldSell = null;
      let worldGoldUsd = null;
      let usdVndRate = 25450; // standard default

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

      data.value = {
        vnBuy: vnGoldBuy,
        vnSell: vnGoldSell,
        worldUsd: worldGoldUsd,
        worldVnd: worldGoldVndPerTael,
        spreadVnd: spreadVnd,
        spreadPercent: spreadPercent,
        usdVndRate: usdVndRate,
        updatedAt: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      };

      loading.value = false;
    };

    onMounted(() => {
      fetchAllData();
    });

    return {
      loading,
      error,
      data,
      fetchAllData,
      formatCurrency,
      formatMillions
    };
  }
}
</script>

<style scoped>
.bg-light-gray {
  background-color: #f4f6f9;
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
