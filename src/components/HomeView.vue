<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />
    <notifications />
    
    <!-- Hero Section -->
    <div class="hero-section text-center py-5 position-relative overflow-hidden">
      <div class="hero-glow-1"></div>
      <div class="hero-glow-2"></div>
      <div class="container position-relative z-1">
        <span class="badge hero-badge mb-3 px-3 py-2">⚡ MULTI-ASSET SCANNER & SIGNALS</span>
        <h1 class="hero-title mb-3">Multi-Asset Intelligence & Trading Signals</h1>
        <p class="hero-subtitle mx-auto mb-4">
          Real-time analytics, pattern recognition, and trend strength rotation across global Crypto, Stock, Forex, Futures, and Commodities markets.
        </p>
        <div class="d-flex justify-content-center gap-3 flex-wrap">
          <router-link to="/crypto" class="btn-glow btn-glow--primary">
            <span>🚀 Explore Crypto</span>
          </router-link>
          <router-link to="/stock" class="btn-glow btn-glow--secondary">
            <span>📈 Scan Stocks</span>
          </router-link>
        </div>
      </div>
    </div>

    <div class="home-view container flex-grow-1 pb-5">
      <!-- Live Market Grid -->
      <div class="row g-4 mb-5">
        <div class="col-12 col-md-6 col-lg-4 col-xl-2" v-for="asset in marketAssets" :key="asset.name">
          <div class="market-card-link" @click="openChartModal(asset)" style="cursor: pointer;">
            <div class="market-card p-4 h-100 d-flex flex-column justify-content-between" :title="asset.message || asset.name">
              <div>
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <span class="market-card__icon" :style="{ background: asset.iconBg }">{{ asset.emoji }}</span>
                  <span class="market-card__change" :class="asset.positive ? 'text-neon-green' : 'text-neon-red'">
                    {{ asset.change }}
                  </span>
                </div>
                <h4 class="market-card__title">{{ asset.name }}</h4>
                <p class="market-card__price mb-0">{{ asset.price }}</p>
                <div class="market-card__time mt-1 small" :style="{ opacity: asset.relativeTime ? 1 : 0, color: '#64748b', 'font-size': '0.72rem', 'font-weight': '500', 'line-height': '1.2rem', 'height': '1.2rem' }">⏱️ {{ asset.relativeTime || 'Pending' }}</div>
              </div>
              <div class="market-card__sparkline mt-3">
                <svg viewBox="0 0 100 30" class="sparkline-svg">
                  <path :d="asset.sparkline" fill="none" :stroke="asset.positive ? '#10b981' : '#ef4444'" stroke-width="2" stroke-linecap="round"></path>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- RRG & Insights Area -->
      <div class="row g-4 mb-5">
        <!-- Left Column: Core Features Info -->
        <div class="col-lg-4 d-flex flex-column gap-4">
          <div class="feature-panel p-4 flex-grow-1">
            <h3 class="panel-heading mb-4 d-flex align-items-center gap-2">
              <span>🧠</span> Platform Intelligence
            </h3>
            <div class="feature-item d-flex gap-3 mb-4">
              <div class="feature-icon bg-blue">🤖</div>
              <div>
                <h5 class="feature-title">AI Trading Chatbot</h5>
                <p class="feature-desc mb-0">Consult our integrated assistant for real-time asset calculations, news, and indicators.</p>
              </div>
            </div>
            <div class="feature-item d-flex gap-3 mb-4">
              <div class="feature-icon bg-green">🔔</div>
              <div>
                <h5 class="feature-title">Smart Price Alerts</h5>
                <p class="feature-desc mb-0">Set glowing price triggers across tokens and pairs to receive instantaneous signals.</p>
              </div>
            </div>
            <div class="feature-item d-flex gap-3">
              <div class="feature-icon bg-gold">💼</div>
              <div>
                <h5 class="feature-title">Exclusive Portfolios</h5>
                <p class="feature-desc mb-0">Sync your custody broker deals and calculate custom break-even signals automatically.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: RRG Interactive Panel -->
        <div class="col-lg-8">
          <div class="feature-panel p-0 overflow-hidden">
            <div class="panel-header-glass py-3 px-4 d-flex justify-content-between align-items-center border-bottom border-glass">
              <h3 class="panel-heading m-0 d-flex align-items-center gap-2">
                <span>🔄</span> Sector Rotation Graph (RRG)
              </h3>
              <button
                class="btn-generate d-flex align-items-center gap-2"
                @click="runSSHScript('assets_rrg')"
                :disabled="isRunningScript"
              >
                <span v-if="isRunningScript" class="spinner-border spinner-border-sm"></span>
                <span v-else style="display: inline-flex; align-items: center; gap: 6px;">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                  Generate RRG
                </span>
              </button>
            </div>
            
            <div class="p-4 text-center">
              <p class="text-secondary small mb-4 text-start">
                The Relative Rotation Graph (RRG) maps the relative strength and momentum of global asset classes against USD. Visualizing asset rotations helps identify leading, weakening, lagging, or improving market sectors.
              </p>
              
              <div class="rrg-frame position-relative mx-auto rounded-4 overflow-hidden shadow-lg border border-glass">
                <img :src="assetsRRGUrl" class="img-fluid rrg-image" alt="Assets RRG Chart" />
                <div class="rrg-frame-overlay"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Chart Modal -->
    <div v-if="showChartModal" class="modal-backdrop" @click="closeChartModal">
      <div class="custom-modal" @click.stop>
        <div class="modal-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0">{{ selectedAsset?.name }}</h5>
          <button type="button" class="btn-close" @click="closeChartModal"></button>
        </div>
        <div class="modal-body p-0">
          <TradingViewChart v-if="selectedAssetChartSymbol" :coin="selectedAssetChartSymbol" :height="500" />
        </div>
      </div>
    </div>

    <AppFooter />
  </div>
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter  from './AppFooter.vue';
import TradingViewChart from './TradingViewChart.vue';
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useNotification } from "@kyvg/vue3-notification";

export default {
  name: 'HomeView',
  components: {
    NavBar,
    AppFooter,
    TradingViewChart,
  },
  setup() {
    const { notify } = useNotification();
    const isRunningScript = ref(false);
    const assetsRRGKey = ref(Date.now());
    const assetsRRGUrl = computed(() => `/assets_rrgchart?t=${assetsRRGKey.value}`);
    
    const showChartModal = ref(false);
    const selectedAsset = ref(null);
    const selectedAssetChartSymbol = computed(() => {
      if (!selectedAsset.value) return '';
      let sym = selectedAsset.value.symbol;
      if (selectedAsset.value.assetType === 'futures' && sym.toUpperCase().endsWith('USDT')) {
        return `BINANCE:${sym}.P`;
      }
      return sym;
    });

    const openChartModal = (asset) => {
      selectedAsset.value = asset;
      showChartModal.value = true;
    };

    const closeChartModal = () => {
      showChartModal.value = false;
      selectedAsset.value = null;
    };

    const defaultAssets = [
      {
        name: 'Stocks (VN-Index)',
        price: '1,280.50 pts',
        change: '+0.75%',
        positive: true,
        emoji: '📈',
        iconBg: 'rgba(16, 185, 129, 0.1)',
        link: '/stock',
        sparkline: 'M 0 25 L 20 22 L 40 18 L 60 10 L 80 15 L 100 5',
        message: 'Dữ liệu thị trường mô phỏng VN-Index',
        symbol: 'VNINDEX',
        assetType: 'stock'
      },
      {
        name: 'Crypto (BTCUSDT)',
        price: '$68,420.00',
        change: '+4.12%',
        positive: true,
        emoji: '🪙',
        iconBg: 'rgba(245, 158, 11, 0.1)',
        link: '/crypto',
        sparkline: 'M 0 25 L 20 20 L 40 24 L 60 12 L 80 8 L 100 2',
        message: 'Dữ liệu thị trường mô phỏng Bitcoin Spot',
        symbol: 'BTCUSDT',
        assetType: 'crypto'
      },
      {
        name: 'Forex (EURUSD)',
        price: '1.0850',
        change: '-0.15%',
        positive: false,
        emoji: '💱',
        iconBg: 'rgba(239, 68, 68, 0.1)',
        link: '/forex',
        sparkline: 'M 0 10 L 20 15 L 40 8 L 60 18 L 80 16 L 100 24',
        message: 'Dữ liệu thị trường mô phỏng EUR/USD',
        symbol: 'FX:EURUSD',
        assetType: 'forex'
      },
      {
        name: 'Commodities (Gold)',
        price: '$2,342.50 / oz',
        change: '+1.28%',
        positive: true,
        emoji: '🏆',
        iconBg: 'rgba(234, 179, 8, 0.1)',
        link: '/commodities',
        sparkline: 'M 0 20 L 20 18 L 40 12 L 60 15 L 80 5 L 100 8',
        message: 'Dữ liệu thị trường mô phỏng Gold',
        symbol: 'GC=F',
        assetType: 'commodities'
      },
      {
        name: 'Futures (VN30F1M)',
        price: '1,295.20 pts',
        change: '+0.85%',
        positive: true,
        emoji: '📊',
        iconBg: 'rgba(59, 130, 246, 0.1)',
        link: '/futures',
        sparkline: 'M 0 24 L 20 22 L 40 16 L 60 12 L 80 18 L 100 8',
        message: 'Dữ liệu thị trường mô phỏng VN30 Phái sinh',
        symbol: 'VN30F1M',
        assetType: 'futures'
      },
      {
        name: 'Stocks (S&P 500)',
        price: '5,250.25 pts',
        change: '+0.45%',
        positive: true,
        emoji: '🏛️',
        iconBg: 'rgba(16, 185, 129, 0.1)',
        link: '/stock',
        sparkline: 'M 0 20 L 20 22 L 40 18 L 60 25 L 80 15 L 100 12',
        message: 'Dữ liệu thị trường mô phỏng S&P 500',
        symbol: 'SPX',
        assetType: 'stock'
      }
    ];

    const marketAssets = ref([...defaultAssets]);

    const positiveSparklines = [
      'M 0 25 L 20 22 L 40 18 L 60 10 L 80 15 L 100 5',
      'M 0 25 L 20 20 L 40 24 L 60 12 L 80 8 L 100 2',
      'M 0 24 L 20 22 L 40 16 L 60 12 L 80 18 L 100 8',
      'M 0 22 L 20 18 L 40 20 L 60 10 L 80 8 L 100 4'
    ];

    const negativeSparklines = [
      'M 0 10 L 20 15 L 40 8 L 60 18 L 80 16 L 100 24',
      'M 0 5 L 20 12 L 40 10 L 60 18 L 80 20 L 100 25',
      'M 0 8 L 20 14 L 40 12 L 60 22 L 80 18 L 100 26'
    ];

    const getSparkline = (symbol, positive) => {
      const list = positive ? positiveSparklines : negativeSparklines;
      let hash = 0;
      for (let i = 0; i < symbol.length; i++) {
        hash += symbol.charCodeAt(i);
      }
      return list[hash % list.length];
    };

    const getRelativeTime = (timeStr) => {
      try {
        const d = new Date(timeStr);
        const diffMs = Date.now() - d.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        if (diffMins < 1) return 'Vừa xong';
        if (diffMins < 60) return `${diffMins} phút trước`;
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours} giờ trước`;
        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays} ngày trước`;
      } catch (e) {
        return '';
      }
    };

    const formatPrice = (price, assetType) => {
      if (assetType === 'stock') {
        if (price > 1000) {
          // VN stock price (VND)
          return `${price.toLocaleString('vi-VN')} đ`;
        } else {
          // US stock price (USD)
          return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
        }
      } else if (assetType === 'crypto' || assetType === 'futures' || assetType === 'commodities') {
        return `$${price.toLocaleString('en-US', { minimumFractionDigits: price < 1 ? 4 : 2 })}`;
      }
      return price.toLocaleString();
    };

    const parseAlertChange = (msg) => {
      const lowerMsg = msg.toLowerCase();
      if (lowerMsg.includes('bán') || lowerMsg.includes('sell') || lowerMsg.includes('giảm')) {
        return { change: 'SELL', positive: false };
      }
      if (lowerMsg.includes('bứt phá') || lowerMsg.includes('vượt đỉnh') || lowerMsg.includes('breakout') || lowerMsg.includes('tăng')) {
        return { change: 'BREAKOUT', positive: true };
      }
      return { change: 'ALERT', positive: true };
    };

    const fetchLatestAlerts = async () => {
      try {
        const response = await fetch('/triggeredAlerts?limit=6');
        if (!response.ok) throw new Error('Failed to fetch alerts');
        const data = await response.json();
        
        if (data && data.length > 0) {
          const mappedAlerts = data.map((alert) => {
            const parsed = parseAlertChange(alert.message);
            
            let name = '';
            let emoji = '🔔';
            let iconBg = 'rgba(139, 92, 246, 0.1)';
            let link = '/';
            
            if (alert.asset_type === 'stock') {
              const isUS = alert.symbol.includes(':') || alert.symbol.length > 3;
              name = `${isUS ? 'US Stock' : 'VN Stock'} (${alert.symbol.split(':').pop()})`;
              emoji = '📈';
              iconBg = 'rgba(16, 185, 129, 0.1)';
              link = '/stock';
            } else if (alert.asset_type === 'crypto') {
              name = `Crypto (${alert.symbol})`;
              emoji = '🪙';
              iconBg = 'rgba(245, 158, 11, 0.1)';
              link = '/crypto';
            } else if (alert.asset_type === 'futures') {
              name = `Futures (${alert.symbol})`;
              emoji = '📊';
              iconBg = 'rgba(59, 130, 246, 0.1)';
              link = '/futures';
            } else if (alert.asset_type === 'commodities') {
              const commodityNames = {
                'GC=F': 'Vàng (Gold)',
                'SI=F': 'Bạc (Silver)',
                'BZ=F': 'Dầu Brent (UKOIL)',
                'CL=F': 'Dầu WTI (USOIL)'
              };
              const comName = commodityNames[alert.symbol] || alert.symbol;
              name = `${comName}`;
              emoji = alert.symbol === 'GC=F' ? '🏆' : (alert.symbol === 'SI=F' ? '🥈' : '🛢️');
              iconBg = 'rgba(234, 179, 8, 0.1)';
              link = '/commodities';
            } else {
              name = `${alert.asset_type.toUpperCase()} (${alert.symbol})`;
            }

            return {
              name,
              price: formatPrice(alert.price, alert.asset_type),
              change: parsed.change,
              positive: parsed.positive,
              emoji,
              iconBg,
              link,
              sparkline: getSparkline(alert.symbol, parsed.positive),
              message: alert.message,
              relativeTime: getRelativeTime(alert.created_at),
              symbol: alert.symbol,
              assetType: alert.asset_type
            };
          });

          // Pad with default assets if we have fewer than 6 alerts
          if (mappedAlerts.length < 6) {
            const countNeeded = 6 - mappedAlerts.length;
            for (let i = 0; i < countNeeded; i++) {
              mappedAlerts.push(defaultAssets[i % defaultAssets.length]);
            }
          }
          marketAssets.value = mappedAlerts;
        } else {
          marketAssets.value = [...defaultAssets];
        }
      } catch (error) {
        console.error('Error loading latest alerts:', error);
        marketAssets.value = [...defaultAssets];
      }
    };

    let pollInterval = null;

    onMounted(() => {
      fetchLatestAlerts();
      // Poll every 15 seconds to fetch latest real-time alerts
      pollInterval = setInterval(fetchLatestAlerts, 15000);
    });

    onUnmounted(() => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    });

    const runSSHScript = async (scriptType) => {
      isRunningScript.value = true;
      try {
        const response = await fetch('/runSSHScript', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ script_type: scriptType }),
        });
        const data = await response.json();
        if (response.ok && data.success) {
          notify({
            type: 'success',
            title: 'Success',
            text: 'Assets RRG Chart has been updated successfully!',
          });
          assetsRRGKey.value = Date.now();
        } else {
          throw new Error(data.error || 'Server returned an error');
        }
      } catch (error) {
        console.error('Error running SSH script:', error);
        notify({
          type: 'error',
          title: 'Execution Failed',
          text: error.message || 'Failed to connect or run the SSH script.',
        });
      } finally {
        isRunningScript.value = false;
      }
    };

    return {
      isRunningScript,
      assetsRRGUrl,
      runSSHScript,
      marketAssets,
      showChartModal,
      selectedAsset,
      selectedAssetChartSymbol,
      openChartModal,
      closeChartModal
    };
  }
}
</script>

<style scoped>
/* ── Hero Section ────────────────────────────────────── */
.hero-section {
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}
.hero-glow-1 {
  position: absolute;
  top: -100px;
  left: 25%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.04) 0%, transparent 70%);
  filter: blur(50px);
}
.hero-glow-2 {
  position: absolute;
  top: -50px;
  right: 25%;
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.03) 0%, transparent 70%);
  filter: blur(40px);
}
.hero-badge {
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.15);
  color: #2563eb;
  font-weight: 700;
  letter-spacing: 0.5px;
  font-size: 0.72rem;
  border-radius: 999px;
  display: inline-block;
}
.hero-title {
  font-family: 'Outfit', sans-serif;
  font-weight: 900;
  font-size: 2.6rem;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.hero-subtitle {
  font-size: 1.05rem;
  color: #475569;
  max-width: 680px;
  line-height: 1.6;
}

/* ── Buttons ─────────────────────────────────────────── */
.btn-glow {
  padding: 11px 24px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.92rem;
  text-decoration: none;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.btn-glow--primary {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 20px rgba(37, 99, 235, 0.25);
}
.btn-glow--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(37, 99, 235, 0.35);
  color: #fff;
}
.btn-glow--secondary {
  background: rgba(0, 0, 0, 0.02);
  color: #475569;
  border: 1px solid rgba(0, 0, 0, 0.06);
}
.btn-glow--secondary:hover {
  background: rgba(0, 0, 0, 0.05);
  border-color: rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
  color: #0f172a;
}

/* ── Market Grid ─────────────────────────────────────── */
.market-card-link {
  text-decoration: none;
  color: inherit;
  display: block;
}
.market-card {
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.02);
}
.market-card:hover {
  transform: translateY(-4px);
  border-color: rgba(59, 130, 246, 0.25);
  background: #ffffff;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.06), 0 0 15px rgba(59, 130, 246, 0.04);
}
.market-card__icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
}
.market-card__change {
  font-weight: 700;
  font-size: 0.8rem;
  padding: 2px 8px;
  border-radius: 20px;
  background: rgba(0,0,0,0.02);
}
.text-neon-green {
  color: #059669;
  text-shadow: none;
}
.text-neon-red {
  color: #dc2626;
  text-shadow: none;
}
.market-card__title {
  font-size: 0.82rem;
  font-weight: 600;
  color: #475569;
  margin-bottom: 4px;
}
.market-card__price {
  font-size: 1.25rem;
  font-weight: 800;
  color: #0f172a;
}
.market-card__sparkline {
  height: 30px;
}
.sparkline-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

/* ── Panels ─────────────────────────────────────────── */
.feature-panel {
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.03);
}
.panel-heading {
  font-family: 'Outfit', sans-serif;
  font-size: 1.15rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}
.feature-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
  flex-shrink: 0;
}
.bg-blue { background: rgba(59, 130, 246, 0.08); color: #2563eb; }
.bg-green { background: rgba(16, 185, 129, 0.08); color: #059669; }
.bg-gold { background: rgba(245, 158, 11, 0.08); color: #d97706; }

.feature-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 2px;
}
.feature-desc {
  font-size: 0.8rem;
  color: #475569;
  line-height: 1.5;
}

/* ── RRG Section ─────────────────────────────────────── */
.panel-header-glass {
  background: #f8fafc;
}
.border-bottom {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
}
.btn-generate {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 6px 16px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}
.btn-generate:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.3);
}
.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.rrg-frame {
  max-width: 100%;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.06) !important;
}
.rrg-image {
  max-width: 100%;
  height: auto;
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.rrg-frame:hover .rrg-image {
  transform: scale(1.015);
}
.border-glass {
  border-color: rgba(0, 0, 0, 0.06) !important;
}

/* ── Modal ───────────────────────────────────────────── */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1050;
  display: flex;
  align-items: center;
  justify-content: center;
}
.custom-modal {
  background: #fff;
  border-radius: 12px;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.modal-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}
.modal-body {
  padding: 1rem;
  overflow-y: auto;
}
</style>
