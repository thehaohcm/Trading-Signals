<template>
  <div class="gold-spread-widget mb-3">
    <div v-if="spreadLoading" class="card border-0 shadow-sm rounded-4 glass-panel border-glass p-3 text-center">
      <div class="spinner-border text-warning spinner-border-sm mb-1" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="text-muted mb-0 small" style="font-size: 0.75rem; color: #94a3b8 !important;">Đang tính toán chênh lệch giá vàng thế giới...</p>
    </div>
    
    <div v-else-if="spreadData" class="card border-0 shadow-sm rounded-4 overflow-hidden glass-panel border-glass">
      <div class="card-header bg-gradient-gold py-2 px-3 d-flex justify-content-between align-items-center border-0">
        <div class="d-flex align-items-center gap-2">
          <span class="fs-6">🏆</span>
          <h6 class="mb-0 fw-bold" style="font-family: 'Outfit', sans-serif; font-size: 0.85rem; color: #0f172a;">Chênh Lệch Vàng VN vs Thế Giới</h6>
        </div>
        <div class="d-flex align-items-center gap-2">
          <span class="small d-none d-sm-inline" style="font-size: 0.72rem; font-weight: 700; color: #334155;">Cập nhật: {{ spreadData.updatedAt }}</span>
          <button 
            class="btn btn-xs rounded-pill py-0.5 px-2 d-flex align-items-center gap-1 btn-refresh" 
            style="font-size: 0.7rem; font-weight: 700; background: rgba(0,0,0,0.15); color: #0f172a; border: none; cursor: pointer;" 
            @click="fetchSpreadData" 
            :disabled="spreadLoading"
            title="Làm mới dữ liệu"
          >
            <i class="bi bi-arrow-clockwise"></i> Làm mới
          </button>
        </div>
      </div>
      
      <div class="card-body p-3">
        <div class="row g-3 align-items-stretch">
          
          <!-- Vietnam Gold Card -->
          <div class="col-12 col-md-4">
            <div class="p-3 rounded-4 glass-card border-top border-4 border-warning h-100 d-flex flex-column justify-content-between text-center">
              <div>
                <span class="text-uppercase fw-bold small ls-1 d-block mb-1" style="font-size: 0.72rem; color: #94a3b8;">Vàng SJC</span>
                <h4 class="fw-bold mb-0 text-white" style="font-size: 1.25rem;">{{ formatMillions(spreadData.vnSell) }} <span class="fs-6" style="font-size: 0.8rem; color: #94a3b8;">/ lượng</span></h4>
              </div>
              <div class="d-flex justify-content-center gap-3 small border-top pt-2 mt-2" style="font-size: 0.72rem; border-color: rgba(255,255,255,0.08) !important; color: #cbd5e1;">
                <span>Mua: {{ formatMillions(spreadData.vnBuy) }}</span>
                <span class="opacity-50">|</span>
                <span>Bán: {{ formatMillions(spreadData.vnSell) }}</span>
              </div>
            </div>
          </div>
          
          <!-- World Gold Card -->
          <div class="col-12 col-md-4">
            <div class="p-3 rounded-4 glass-card border-top border-4 border-primary h-100 d-flex flex-column justify-content-between text-center">
              <div>
                <span class="text-uppercase fw-bold small ls-1 d-block mb-1" style="font-size: 0.72rem; color: #94a3b8;">Vàng Thế Giới (Quy đổi)</span>
                <h4 class="fw-bold mb-0 text-white" style="font-size: 1.25rem;">{{ formatMillions(spreadData.worldVnd) }} <span class="fs-6" style="font-size: 0.8rem; color: #94a3b8;">/ lượng</span></h4>
              </div>
              <div class="d-flex justify-content-center gap-3 small border-top pt-2 mt-2" style="font-size: 0.72rem; border-color: rgba(255,255,255,0.08) !important; color: #cbd5e1;">
                <span>Thế giới: ${{ spreadData.worldUsd.toFixed(2) }} / oz</span>
                <span class="opacity-50">|</span>
                <span>Tỷ giá: {{ formatCurrency(spreadData.usdVndRate) }}</span>
              </div>
            </div>
          </div>
          
          <!-- Spread Card -->
          <div class="col-12 col-md-4">
            <div class="p-3 rounded-4 spread-card h-100 text-center d-flex flex-column justify-content-center border-top border-4 border-danger shadow-sm">
              <span class="text-uppercase fw-bold small ls-1 d-block mb-1" style="font-size: 0.72rem; color: #94a3b8;">Chênh Lệch</span>
              <h3 class="fw-extrabold mb-1 text-neon-red" style="font-size: 1.35rem; font-family: 'Outfit', sans-serif;">
                {{ spreadData.spreadVnd >= 0 ? '+' : '' }}{{ formatMillions(spreadData.spreadVnd) }}
              </h3>
              <div>
                <span class="badge rounded-pill bg-neon-red-badge px-2.5 py-1" style="font-size: 0.72rem;">
                  {{ spreadData.spreadPercent >= 0 ? 'Cao hơn' : 'Thấp hơn' }} thế giới {{ Math.abs(spreadData.spreadPercent).toFixed(1) }}%
                </span>
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';

export default {
  name: 'GoldSpreadWidget',
  setup() {
    const spreadData = ref(null);
    const spreadLoading = ref(false);

    const getUTCOffset = () => {
      const d = new Date();
      const offset = -d.getTimezoneOffset();
      const sign = offset >= 0 ? '+' : '-';
      const hours = Math.floor(Math.abs(offset) / 60);
      const minutes = Math.abs(offset) % 60;
      const minutesStr = minutes > 0 ? `:${String(minutes).padStart(2, '0')}` : '';
      return `(UTC${sign}${hours}${minutesStr})`;
    };

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
        updatedAt: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' ' + getUTCOffset()
      };
      spreadLoading.value = false;
    };

    onMounted(() => {
      fetchSpreadData();
    });

    return {
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
.bg-gradient-gold {
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
}

.fw-extrabold {
  font-weight: 800;
}

.ls-1 {
  letter-spacing: 0.5px;
}

.glass-panel {
  background: rgba(18, 24, 38, 0.75) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35) !important;
  backdrop-filter: blur(16px);
  border-radius: 16px;
}

.border-glass {
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
}

.glass-card {
  background: rgba(10, 13, 20, 0.6) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 12px;
}

.spread-card {
  background: rgba(255, 75, 114, 0.08) !important;
  border: 1px solid rgba(255, 75, 114, 0.25) !important;
  border-radius: 14px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.spread-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 75, 114, 0.2) !important;
}

.text-neon-red {
  color: #ff4b72 !important;
  text-shadow: 0 0 10px rgba(255, 75, 114, 0.4) !important;
}

.bg-neon-red-badge {
  background-color: rgba(255, 75, 114, 0.12) !important;
  border: 1px solid rgba(255, 75, 114, 0.3) !important;
  color: #ff4b72 !important;
  font-weight: 700 !important;
  border-radius: 20px;
}

.btn-refresh {
  transition: all 0.2s ease;
}

.btn-refresh:hover {
  transform: rotate(30deg);
  background: rgba(0, 0, 0, 0.25) !important;
}
</style>
