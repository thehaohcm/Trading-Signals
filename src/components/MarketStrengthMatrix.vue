<template>
  <div class="market-strength-matrix-wrapper">
    <!-- Header Controls & Title -->
    <div class="matrix-header-bar d-flex justify-content-between align-items-center flex-wrap gap-3 mb-3">
      <div class="d-flex align-items-center gap-2.5">
        <div class="matrix-icon-badge">
          <span class="pulse-ring"></span>
          <span>⚡</span>
        </div>
        <div>
          <div class="d-flex align-items-center gap-2 flex-wrap">
            <h4 class="matrix-title m-0">Market Strength Matrix</h4>
            <span class="badge-live-scan">
              <span class="live-dot"></span>
              REALTIME SCANNED
            </span>
          </div>
          <p class="matrix-subtitle m-0 text-muted small">
            Relative Strength (RS) Ranking, Momentum Compression & Active Positions
          </p>
        </div>
      </div>

      <!-- Quick Actions: Search, Sort, Limit & Refresh -->
      <div class="d-flex align-items-center gap-2 flex-wrap">
        <div class="search-input-wrap">
          <i class="fa-solid fa-magnifying-glass search-icon"></i>
          <input 
            v-model="searchQuery" 
            type="text" 
            class="matrix-search-input" 
            placeholder="Search symbol (Gold, BTC, EUR...)" 
          />
          <button v-if="searchQuery" class="clear-search-btn" @click="searchQuery = ''">&times;</button>
        </div>

        <div class="sort-select-wrap">
          <select v-model="sortBy" class="matrix-select">
            <option value="strength_desc">🔥 RS Score: High ➔ Low (Live First)</option>
            <option value="strength_asc">❄️ RS Score: Low ➔ High</option>
            <option value="mcap_asc">👑 Top Market Cap (Crypto #1-100)</option>
            <option value="roi_desc">📈 Highest ROI / 24h Change</option>
            <option value="winrate_desc">🎯 Highest Win Rate</option>
            <option value="name_asc">🔤 Symbol (A-Z)</option>
          </select>
        </div>

        <!-- Limit items selector (5-10 items) -->
        <div class="limit-toggle-group" title="Số lượng item hiển thị">
          <button 
            v-for="lim in [5, 8, 10]" 
            :key="lim"
            type="button"
            class="limit-btn"
            :class="{ 'is-active': displayLimit === lim }"
            @click="displayLimit = lim"
          >
            Top {{ lim }}
          </button>
        </div>

        <button 
          class="btn-matrix-refresh" 
          @click="refreshData" 
          :disabled="isLoading"
          title="Refresh strength matrix"
        >
          <i class="fa-solid fa-rotate-right" :class="{ 'spin-anim': isLoading }"></i>
        </button>
      </div>
    </div>

    <!-- Category Tabs Navigation -->
    <div class="matrix-tabs-container mb-3">
      <div class="matrix-tabs-track">
        <button 
          v-for="tab in categoryTabs" 
          :key="tab.id"
          class="matrix-tab-btn"
          :class="{ 'is-active': currentTab === tab.id }"
          @click="currentTab = tab.id"
        >
          <span class="tab-emoji">{{ tab.icon }}</span>
          <span class="tab-label">{{ tab.name }}</span>
          <span class="tab-count-badge" :class="{ 'count-active': getTabCount(tab.id) > 0 }">
            {{ getTabCount(tab.id) }}
          </span>
          <span v-if="tab.id === 'IN_TRADE' && inTradeCount > 0" class="tab-hot-pulse"></span>
        </button>
      </div>
    </div>

    <!-- Summary Highlights Bar -->
    <div class="matrix-highlights-row mb-3 d-flex align-items-center justify-content-between flex-wrap gap-2">
      <div class="d-flex align-items-center gap-3 flex-wrap">
        <!-- Strongest Symbol in Category -->
        <div v-if="topLeaderSymbol" class="leader-highlight-pill" @click="openChart(topLeaderSymbol)">
          <span class="badge-leader-tag">👑 TOP LEADER</span>
          <strong class="text-white">{{ topLeaderSymbol.symbol }}</strong>
          <span class="score-pill score-super">
            ⚡ {{ topLeaderSymbol.strengthScore.toFixed(0) }} RS
          </span>
          <span class="text-muted small">({{ topLeaderSymbol.categoryName }})</span>
        </div>

        <!-- Strongest Active Trade if exists -->
        <div v-if="topActiveTradeSymbol" class="leader-highlight-pill pill-trade" @click="openChart(topActiveTradeSymbol)">
          <span class="badge-trade-tag">🚀 STRONGEST POSITION</span>
          <strong class="text-white">{{ topActiveTradeSymbol.symbol }}</strong>
          <span class="score-pill score-green">
            ROI {{ topActiveTradeSymbol.roi >= 0 ? '+' : '' }}{{ topActiveTradeSymbol.roi.toFixed(1) }}%
          </span>
          <span class="text-muted small">(Layer {{ topActiveTradeSymbol.layer || 1 }}/3)</span>
        </div>
      </div>

      <!-- Strength Legend Hint -->
      <div class="matrix-legend-hint d-none d-md-flex align-items-center gap-2 text-muted small">
        <span class="legend-item"><span class="dot dot-super"></span> &gt;80: Super Strong</span>
        <span class="legend-item"><span class="dot dot-bull"></span> 65-79: Bullish</span>
        <span class="legend-item"><span class="dot dot-neutral"></span> 45-64: Neutral</span>
        <span class="legend-item"><span class="dot dot-bear"></span> &lt;45: Weak</span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading && filteredItems.length === 0" class="matrix-loading-box text-center py-5">
      <div class="spinner-border text-info" role="status"></div>
      <p class="text-muted small mt-2 mb-0">Computing Relative Strength (RS) matrix...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredItems.length === 0" class="matrix-empty-box text-center py-5 rounded-3">
      <div class="empty-icon mb-2" style="font-size: 2.2rem;">📡</div>
      <h6 class="text-white fw-bold mb-1">No matching symbols in this category</h6>
      <p class="text-muted small mb-0">
        {{ searchQuery ? `No results found matching "${searchQuery}".` : 'Scanning live market tickers...' }}
      </p>
    </div>

    <!-- Items Grid Cards -->
    <div v-else class="matrix-grid-cards">
      <div 
        v-for="(item, idx) in filteredItems" 
        :key="item.symbol + idx"
        class="matrix-card"
        :class="{ 
          'card-in-trade': item.isInTrade, 
          'card-leader': idx === 0 && !searchQuery,
          'card-selected': selectedChartSymbol === item.symbol
        }"
        @click="openChart(item)"
      >
        <!-- Card Top: Symbol, Badge, & Category -->
        <div class="card-top-row d-flex align-items-center justify-content-between gap-2 mb-2">
          <div class="d-flex align-items-center gap-2 text-truncate">
            <span class="symbol-type-icon">{{ item.icon }}</span>
            <div class="text-truncate">
              <div class="d-flex align-items-center gap-1.5 flex-wrap">
                <span class="symbol-name fw-bold text-white">{{ item.symbol }}</span>
                <span v-if="item.marketCapRank" class="badge-mcap-rank" :title="`Xếp hạng Vốn hóa Thị trường #${item.marketCapRank}`">
                  #{{ item.marketCapRank }} MCAP
                </span>
                <span v-if="item.isInTrade" class="badge-trade-active" title="Open position in Live Trading">
                  TRADE L{{ item.layer || 1 }}
                </span>
                <span v-else-if="idx === 0 && !searchQuery" class="badge-rank-one" title="Top Leader in category">
                  #1 LEADER
                </span>
              </div>
              <span class="symbol-subname text-muted" style="font-size: 0.73rem;">{{ item.fullName || item.categoryName }}</span>
            </div>
          </div>

          <!-- Price & 24h Change -->
          <div class="text-end flex-shrink-0">
            <div class="symbol-price font-monospace fw-bold text-white">
              {{ formatPrice(item.price, item.assetType) }}
            </div>
            <div 
              class="symbol-change font-monospace small fw-semibold"
              :class="item.change24h >= 0 ? 'text-neon-green' : 'text-neon-red'"
            >
              {{ item.change24h >= 0 ? '+' : '' }}{{ item.change24h.toFixed(2) }}%
            </div>
          </div>
        </div>

        <!-- Strength Score Bar & Value -->
        <div class="strength-meter-section mb-2.5">
          <div class="d-flex align-items-center justify-content-between gap-1 mb-1">
            <span class="meter-label text-muted" style="font-size: 0.72rem;">Relative Strength (RS)</span>
            <div class="d-flex align-items-center gap-1">
              <span class="strength-status-text" :class="getStrengthClass(item.strengthScore)">
                {{ getStrengthStatusText(item.strengthScore, item.isInTrade) }}
              </span>
              <span class="strength-score-badge" :class="getStrengthBadgeClass(item.strengthScore)">
                {{ item.strengthScore.toFixed(0) }} / 100
              </span>
            </div>
          </div>

          <!-- Visual Gradient Bar -->
          <div class="strength-track">
            <div 
              class="strength-fill" 
              :class="getStrengthBarClass(item.strengthScore)"
              :style="{ width: item.strengthScore + '%' }"
            >
              <span class="strength-glow-head"></span>
            </div>
          </div>
        </div>

        <!-- Card Bottom Details Row: RSI, Win Rate, PnL, Action -->
        <div class="card-bottom-row d-flex align-items-center justify-content-between pt-2 border-top border-glass gap-2">
          <!-- Metric Badges -->
          <div class="d-flex align-items-center gap-1.5 flex-wrap">
            <span 
              v-if="item.winRate !== undefined && item.winRate > 0" 
              class="mini-metric-pill"
              :title="`Historical Win Rate: ${item.winRate.toFixed(1)}% (${item.totalTrades || 0} trades)`"
            >
              🎯 {{ item.winRate.toFixed(0) }}% WR
            </span>

            <span 
              v-if="item.isInTrade && item.pnl !== undefined" 
              class="mini-metric-pill"
              :class="item.pnl >= 0 ? 'metric-pnl-win' : 'metric-pnl-loss'"
              :title="`Position Unrealized PnL: ${formatCurrency(item.pnl)}`"
            >
              💵 {{ item.pnl >= 0 ? '+' : '' }}{{ formatCurrency(item.pnl) }}
            </span>

            <span 
              v-else-if="item.breakoutDist !== undefined && item.breakoutDist > 0" 
              class="mini-metric-pill"
              :title="`Distance to Breakout target: ${item.breakoutDist.toFixed(2)}%`"
            >
              📍 {{ item.breakoutDist.toFixed(1) }}% to ATH
            </span>

            <span 
              v-if="item.rsi" 
              class="mini-metric-pill"
              :class="item.rsi >= 70 ? 'text-warning' : (item.rsi <= 30 ? 'text-info' : '')"
              :title="`RSI (14): ${item.rsi.toFixed(1)}`"
            >
              RSI {{ item.rsi.toFixed(0) }}
            </span>
          </div>

          <!-- Quick Chart Button -->
          <button 
            class="btn-quick-chart d-flex align-items-center gap-1" 
            @click.stop="openChart(item)"
            title="Open TradingView Chart Modal"
          >
            <i class="fa-solid fa-chart-line" style="font-size: 0.74rem;"></i>
            <span>Chart</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Multi-Chart Modal Popup (Rich Popup with 1/2/4/8 Split & Vietstock/TradingView Engine) -->
    <MultiChartModal 
      :visible="showChartModal" 
      :initial-symbol="selectedChartAsset?.symbol || selectedChartSymbol || 'BTCUSDT'" 
      :initial-asset="selectedChartAsset" 
      @close="closeChartModal" 
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import MultiChartModal from './MultiChartModal.vue';

export default {
  name: 'MarketStrengthMatrix',
  components: {
    MultiChartModal
  },
  props: {
    externalPositions: {
      type: Array,
      default: () => []
    },
    syncParentChart: {
      type: Boolean,
      default: false
    }
  },
  emits: ['select-symbol'],
  setup(props, { emit }) {
    const isLoading = ref(false);
    const searchQuery = ref('');
    const sortBy = ref('strength_desc');
    const currentTab = ref('ALL');
    const displayLimit = ref(8); // Default to Top 8 items (5-10 range)
    const showChartModal = ref(false);
    const selectedChartSymbol = ref(null);
    const selectedChartAsset = ref(null);

    const rawPositions = ref([]);
    const rawWatchlist = ref([]);
    const rawLeaderboard = ref([]);
    const rawCommodities = ref([]);

    const categoryTabs = [
      { id: 'ALL', name: '⚡ All Markets', icon: '🌐' },
      { id: 'IN_TRADE', name: '🚀 Active Trades', icon: '🎯' },
      { id: 'COMMODITIES', name: '🥇 Commodities', icon: '💎' },
      { id: 'FOREX', name: '💱 Forex', icon: '💱' },
      { id: 'CRYPTO', name: '🪙 Crypto', icon: '🪙' },
      { id: 'STOCKS', name: '📈 Stocks', icon: '📈' }
    ];

    const getAuthHeaders = () => {
      const token = localStorage.getItem('token');
      return token ? { 'Authorization': `Bearer ${token}` } : {};
    };

    const calculateStrength = (item) => {
      let score = 50;

      const change = item.change24h || item.roi || 0;
      if (change > 0) {
        score += Math.min(25, change * 4);
      } else {
        score -= Math.min(25, Math.abs(change) * 3.5);
      }

      if (item.isInTrade) {
        score += 12;
        const layer = item.layer || 1;
        score += (layer - 1) * 6;
      }

      if (item.winRate && item.winRate > 0) {
        if (item.winRate >= 65) score += 12;
        else if (item.winRate >= 50) score += 5;
        else score -= 8;
      }

      if (item.rsi) {
        if (item.rsi >= 60 && item.rsi <= 80) score += 10;
        else if (item.rsi > 80) score += 5;
        else if (item.rsi < 40) score -= 10;
      }

      if (item.breakoutDist !== undefined) {
        if (item.breakoutDist <= 1.0) score += 10;
        else if (item.breakoutDist <= 3.0) score += 5;
      }

      return Math.min(99, Math.max(8, score));
    };

    const fetchAllData = async (isBackground = false) => {
      if (!isBackground) {
        isLoading.value = true;
      }
      try {
        const headers = getAuthHeaders();
        const [posRes, watchRes, leadRes, currRes] = await Promise.allSettled([
          fetch('/breakout/positions', { headers }),
          fetch('/breakout/watchlist', { headers }),
          fetch('/breakout/leaderboard', { headers }),
          fetch('/api/currency-prices')
        ]);

        if (posRes.status === 'fulfilled' && posRes.value.ok) {
          rawPositions.value = await posRes.value.json() || [];
        }
        if (watchRes.status === 'fulfilled' && watchRes.value.ok) {
          rawWatchlist.value = await watchRes.value.json() || [];
        }
        if (leadRes.status === 'fulfilled' && leadRes.value.ok) {
          rawLeaderboard.value = await leadRes.value.json() || [];
        }
        if (currRes.status === 'fulfilled' && currRes.value.ok) {
          rawCommodities.value = await currRes.value.json() || [];
        }
      } catch (e) {
        console.warn('Error fetching matrix data:', e);
      } finally {
        if (!isBackground) {
          isLoading.value = false;
        }
      }
    };

    const mapAssetToCategory = (assetType, symbol) => {
      const sym = (symbol || '').toUpperCase();
      if (assetType === 'commodities' || sym.includes('XAU') || sym.includes('XAG') || sym.includes('OIL') || sym.includes('GOLD')) {
        return 'COMMODITIES';
      }
      if (assetType === 'forex' || sym.includes('USD') && (sym.includes('EUR') || sym.includes('GBP') || sym.includes('JPY') || sym.includes('AUD') || sym.includes('CHF') || sym.includes('CAD') || sym.includes('NZD'))) {
        return 'FOREX';
      }
      if (assetType === 'crypto' || sym.includes('USDT') || sym.includes('BTC') || sym.includes('ETH') || sym.includes('SOL') || sym.includes('BNB')) {
        return 'CRYPTO';
      }
      if (assetType === 'stock_vn' || assetType === 'stock_us' || assetType === 'futures') {
        return 'STOCKS';
      }
      return 'COMMODITIES';
    };

    const getAssetIcon = (assetType, symbol) => {
      const sym = (symbol || '').toUpperCase();
      if (sym.includes('XAU') || sym.includes('GOLD')) return '🥇';
      if (sym.includes('XAG') || sym.includes('SILVER')) return '🥈';
      if (sym.includes('OIL') || sym.includes('WTI')) return '🛢️';
      if (sym.includes('BTC')) return '₿';
      if (sym.includes('ETH')) return 'Ξ';
      if (sym.includes('SOL')) return '◎';
      if (assetType === 'forex' || sym.includes('EUR') || sym.includes('JPY') || sym.includes('GBP')) return '💱';
      if (assetType === 'stock_vn') return '🇻🇳';
      if (assetType === 'stock_us') return '🇺🇸';
      return '💎';
    };

    const getCategoryDisplayName = (assetType, symbol) => {
      const cat = mapAssetToCategory(assetType, symbol);
      if (cat === 'COMMODITIES') return 'Commodities & Metals';
      if (cat === 'FOREX') return 'Forex / Currencies';
      if (cat === 'CRYPTO') return 'Crypto Assets';
      if (cat === 'STOCKS') return 'Equities & Stocks';
      return 'Market Asset';
    };

    const addDefaultMarketFallbacks = (map) => {
      const defaults = [
        { symbol: 'XAUUSD', fullName: 'Spot Gold / USD', price: 2685.50, change24h: 1.25, assetType: 'commodities' },
        { symbol: 'XAGUSD', fullName: 'Spot Silver / USD', price: 31.40, change24h: 0.85, assetType: 'commodities' },
        { symbol: 'USOIL', fullName: 'WTI Crude Oil', price: 71.20, change24h: -0.45, assetType: 'commodities' },
        { symbol: 'EURUSD', fullName: 'Euro / US Dollar', price: 1.0850, change24h: 0.15, assetType: 'forex' },
        { symbol: 'GBPUSD', fullName: 'British Pound / USD', price: 1.2980, change24h: 0.32, assetType: 'forex' },
        { symbol: 'USDJPY', fullName: 'US Dollar / Japanese Yen', price: 152.60, change24h: -0.28, assetType: 'forex' },
        { symbol: 'BTCUSDT', fullName: 'Bitcoin', price: 68500.00, change24h: 2.80, assetType: 'crypto' },
        { symbol: 'ETHUSDT', fullName: 'Ethereum', price: 2640.00, change24h: 1.95, assetType: 'crypto' },
        { symbol: 'SOLUSDT', fullName: 'Solana', price: 172.50, change24h: 4.10, assetType: 'crypto' },
        { symbol: 'VNINDEX', fullName: 'VN-Index', price: 1280.00, change24h: 0.45, assetType: 'stock_vn' },
        { symbol: 'SPX', fullName: 'S&P 500 Index', price: 5860.00, change24h: 0.65, assetType: 'stock_us' }
      ];

      defaults.forEach(d => {
        if (!map.has(d.symbol)) {
          map.set(d.symbol, {
            ...d,
            isInTrade: false,
            category: mapAssetToCategory(d.assetType, d.symbol),
            icon: getAssetIcon(d.assetType, d.symbol),
            categoryName: getCategoryDisplayName(d.assetType, d.symbol)
          });
        }
      });
    };

    const cryptoMcapRanks = {
      'BTC': 1, 'BTCUSDT': 1, 'ETH': 2, 'ETHUSDT': 2, 'USDT': 3, 'BNB': 4, 'BNBUSDT': 4,
      'SOL': 5, 'SOLUSDT': 5, 'USDC': 6, 'XRP': 7, 'XRPUSDT': 7, 'DOGE': 8, 'DOGEUSDT': 8,
      'ADA': 9, 'ADAUSDT': 9, 'TRX': 10, 'TRXUSDT': 10, 'AVAX': 11, 'AVAXUSDT': 11,
      'LINK': 12, 'LINKUSDT': 12, 'SHIB': 13, 'SHIBUSDT': 13, 'SUI': 14, 'SUIUSDT': 14,
      'XLM': 15, 'XLMUSDT': 15, 'DOT': 16, 'DOTUSDT': 16, 'HBAR': 17, 'HBARUSDT': 17,
      'BCH': 18, 'BCHUSDT': 18, 'UNI': 19, 'UNIUSDT': 19, 'LTC': 20, 'LTCUSDT': 20,
      'PEPE': 21, 'PEPEUSDT': 21, 'NEAR': 22, 'NEARUSDT': 22, 'APT': 23, 'APTUSDT': 23,
      'ICP': 24, 'ICPUSDT': 24, 'POL': 25, 'POLUSDT': 25, 'MATIC': 25, 'MATICUSDT': 25,
      'RENDER': 26, 'RENDERUSDT': 26, 'FET': 27, 'FETUSDT': 27, 'ETC': 28, 'ETCUSDT': 28,
      'XMR': 29, 'XMRUSDT': 29, 'TAO': 30, 'TAOUSDT': 30, 'ARB': 31, 'ARBUSDT': 31,
      'VET': 32, 'VETUSDT': 32, 'ATOM': 33, 'ATOMUSDT': 33, 'FIL': 34, 'FILUSDT': 34,
      'OM': 35, 'OMUSDT': 35, 'KAS': 36, 'KASUSDT': 36, 'AAVE': 37, 'AAVEUSDT': 37,
      'ALGO': 38, 'ALGOUSDT': 38, 'FTM': 39, 'FTMUSDT': 39, 'S': 39, 'SUSDT': 39,
      'TIA': 40, 'TIAUSDT': 40, 'OP': 41, 'OPUSDT': 41, 'INJ': 42, 'INJUSDT': 42,
      'GRT': 43, 'GRTUSDT': 43, 'SEI': 44, 'SEIUSDT': 44, 'BONK': 45, 'BONKUSDT': 45,
      'WIF': 46, 'WIFUSDT': 46, 'FLOKI': 47, 'FLOKIUSDT': 47, 'THETA': 48, 'THETAUSDT': 48,
      'JUP': 49, 'JUPUSDT': 49, 'ENA': 50, 'ENAUSDT': 50, 'ONDO': 51, 'ONDOUSDT': 51,
      'GALA': 52, 'GALAUSDT': 52, 'PYTH': 53, 'PYTHUSDT': 53, 'CRV': 54, 'CRVUSDT': 54,
      'DYDX': 55, 'DYDXUSDT': 55, 'LDO': 56, 'LDOUSDT': 56, 'RUNE': 57, 'RUNEUSDT': 57,
      'SAND': 58, 'SANDUSDT': 58, 'MANA': 59, 'MANAUSDT': 59, 'PENDLE': 60, 'PENDLEUSDT': 60,
      'RAY': 61, 'RAYUSDT': 61, 'POPCAT': 62, 'POPCATUSDT': 62, 'WLD': 63, 'WLDUSDT': 63,
      'STX': 64, 'STXUSDT': 64, 'AR': 65, 'ARUSDT': 65, 'FLOW': 66, 'FLOWUSDT': 66,
      'EGLD': 67, 'EGLDUSDT': 67, 'QNT': 68, 'QNTUSDT': 68, 'CHZ': 69, 'CHZUSDT': 69,
      'AXS': 70, 'AXSUSDT': 70, 'EOS': 71, 'EOSUSDT': 71, 'NEO': 72, 'NEOUSDT': 72,
      'MINA': 73, 'MINAUSDT': 73, 'KLAY': 74, 'KLAYUSDT': 74, 'STRK': 75, 'STRKUSDT': 75,
      'ZRO': 76, 'ZROUSDT': 76, 'BOME': 77, 'BOMEUSDT': 77, 'MEME': 78, 'MEMEUSDT': 78,
      'ORDI': 79, 'ORDIUSDT': 79, 'KAVA': 80, 'KAVAUSDT': 80, 'W': 81, 'WUSDT': 81,
      'BLUR': 82, 'BLURUSDT': 82, 'JTO': 83, 'JTOUSDT': 83, '1INCH': 84, '1INCHUSDT': 84,
      'SNX': 85, 'SNXUSDT': 85, 'IOTA': 86, 'IOTAUSDT': 86, 'ENJ': 87, 'ENJUSDT': 87,
      'CAKE': 88, 'CAKEUSDT': 88, 'DYM': 89, 'DYMUSDT': 89, 'ALT': 90, 'ALTUSDT': 90,
      'SUPER': 91, 'SUPERUSDT': 91, 'ZEC': 92, 'ZECUSDT': 92, 'ROSE': 93, 'ROSEUSDT': 93,
      'WOO': 94, 'WOOUSDT': 94, 'XEC': 95, 'XECUSDT': 95, 'ASTR': 96, 'ASTRUSDT': 96,
      'APE': 97, 'APEUSDT': 97, 'BEAM': 98, 'BEAMUSDT': 98, 'SAFE': 99, 'SAFEUSDT': 99
    };

    const getCryptoMarketCapRank = (sym) => {
      if (!sym) return null;
      const clean = String(sym).toUpperCase().trim().split(':').pop().trim();
      const base = clean.replace(/USDT$|BUSD$|USDC$|\.P$|\/USDT$/g, '').trim();
      return cryptoMcapRanks[clean] || cryptoMcapRanks[base] || null;
    };

    const allNormalizedItems = computed(() => {
      const map = new Map();

      const positionsList = (props.externalPositions && props.externalPositions.length > 0) 
        ? props.externalPositions 
        : rawPositions.value;

      positionsList.forEach(pos => {
        if (pos.status === 'OPEN' || !pos.status) {
          const sym = pos.symbol;
          const assetType = pos.asset_type || 'crypto';
          const roi = pos.unrealized_roi_pct || 0;
          const pnl = pos.unrealized_pnl || 0;
          
          map.set(sym, {
            symbol: sym,
            fullName: pos.name || sym,
            price: pos.current_price || pos.avg_entry_price || 0,
            change24h: roi,
            roi: roi,
            pnl: pnl,
            layer: pos.current_layer || 1,
            isInTrade: true,
            assetType: assetType,
            category: mapAssetToCategory(assetType, sym),
            icon: getAssetIcon(assetType, sym),
            categoryName: getCategoryDisplayName(assetType, sym)
          });
        }
      });

      rawWatchlist.value.forEach(w => {
        const sym = w.symbol;
        if (!map.has(sym)) {
          const assetType = w.asset_type || 'crypto';
          const curPrice = w.current_price || 0;
          const breakPrice = w.breakout_price || w.resistance_level || 0;
          let dist = 0;
          if (breakPrice > 0 && curPrice > 0) {
            dist = Math.max(0, ((breakPrice - curPrice) / breakPrice) * 100);
          }

          map.set(sym, {
            symbol: sym,
            fullName: w.name || sym,
            price: curPrice,
            change24h: w.change_24h || 0,
            breakoutDist: dist,
            isInTrade: false,
            assetType: assetType,
            category: mapAssetToCategory(assetType, sym),
            icon: getAssetIcon(assetType, sym),
            categoryName: getCategoryDisplayName(assetType, sym)
          });
        }
      });

      rawLeaderboard.value.forEach(lead => {
        const sym = lead.symbol;
        if (map.has(sym)) {
          const existing = map.get(sym);
          existing.winRate = lead.win_rate_pct || 0;
          existing.totalTrades = lead.total_trades || 0;
          existing.totalRealizedPnL = lead.total_realized_pnl || 0;
        } else {
          const assetType = lead.asset_type || 'crypto';
          map.set(sym, {
            symbol: sym,
            fullName: sym,
            price: lead.current_pnl || 0,
            change24h: lead.cur_roi || lead.avg_roi || 0,
            winRate: lead.win_rate_pct || 0,
            totalTrades: lead.total_trades || 0,
            isInTrade: lead.current_status === 'OPEN',
            assetType: assetType,
            category: mapAssetToCategory(assetType, sym),
            icon: getAssetIcon(assetType, sym),
            categoryName: getCategoryDisplayName(assetType, sym)
          });
        }
      });

      addDefaultMarketFallbacks(map);

      return Array.from(map.values()).map(item => {
        item.strengthScore = calculateStrength(item);
        if (item.category === 'CRYPTO' || item.assetType === 'crypto' || item.symbol.includes('USDT')) {
          item.marketCapRank = getCryptoMarketCapRank(item.symbol);
        }
        return item;
      });
    });

    const filteredItems = computed(() => {
      let list = allNormalizedItems.value;

      if (currentTab.value === 'IN_TRADE') {
        list = list.filter(i => i.isInTrade);
      } else if (currentTab.value !== 'ALL') {
        list = list.filter(i => i.category === currentTab.value);
      }

      if (searchQuery.value.trim()) {
        const q = searchQuery.value.toLowerCase().trim();
        list = list.filter(i => 
          i.symbol.toLowerCase().includes(q) || 
          (i.fullName && i.fullName.toLowerCase().includes(q)) ||
          (i.categoryName && i.categoryName.toLowerCase().includes(q))
        );
      }

      // Live Trade (isInTrade) items are prioritized first when viewing strength/roi, followed by strongest RS scores
      const sorted = [...list].sort((a, b) => {
        if (sortBy.value === 'strength_desc') {
          if (a.isInTrade !== b.isInTrade) {
            return b.isInTrade ? 1 : -1;
          }
          return (b.strengthScore || 0) - (a.strengthScore || 0);
        } else if (sortBy.value === 'strength_asc') {
          return (a.strengthScore || 0) - (b.strengthScore || 0);
        } else if (sortBy.value === 'mcap_asc') {
          return (a.marketCapRank || 999) - (b.marketCapRank || 999);
        } else if (sortBy.value === 'roi_desc') {
          if (a.isInTrade !== b.isInTrade) {
            return b.isInTrade ? 1 : -1;
          }
          return (b.change24h || b.roi || 0) - (a.change24h || a.roi || 0);
        } else if (sortBy.value === 'winrate_desc') {
          return (b.winRate || 0) - (a.winRate || 0);
        } else if (sortBy.value === 'name_asc') {
          return a.symbol.localeCompare(b.symbol);
        }
        return 0;
      });

      // Show top 5-10 items only (displayLimit)
      return sorted.slice(0, displayLimit.value);
    });

    const inTradeCount = computed(() => {
      return allNormalizedItems.value.filter(i => i.isInTrade).length;
    });

    const getTabCount = (tabId) => {
      if (tabId === 'ALL') return allNormalizedItems.value.length;
      if (tabId === 'IN_TRADE') return inTradeCount.value;
      return allNormalizedItems.value.filter(i => i.category === tabId).length;
    };

    const topLeaderSymbol = computed(() => {
      const items = filteredItems.value;
      return items.length > 0 ? items[0] : null;
    });

    const topActiveTradeSymbol = computed(() => {
      const active = allNormalizedItems.value.filter(i => i.isInTrade);
      if (active.length === 0) return null;
      return [...active].sort((a, b) => (b.roi || 0) - (a.roi || 0))[0];
    });

    const getStrengthClass = (score) => {
      if (score >= 80) return 'text-purple-glow';
      if (score >= 65) return 'text-neon-green';
      if (score >= 45) return 'text-warning';
      return 'text-danger';
    };

    const getStrengthBadgeClass = (score) => {
      if (score >= 80) return 'badge-score-super';
      if (score >= 65) return 'badge-score-bull';
      if (score >= 45) return 'badge-score-neutral';
      return 'badge-score-bear';
    };

    const getStrengthBarClass = (score) => {
      if (score >= 80) return 'bar-super';
      if (score >= 65) return 'bar-bull';
      if (score >= 45) return 'bar-neutral';
      return 'bar-bear';
    };

    const getStrengthStatusText = (score, isInTrade) => {
      if (isInTrade) return '🚀 ACTIVE TRADE';
      if (score >= 80) return '⚡ SUPER LEADER';
      if (score >= 65) return '🟢 BULLISH TREND';
      if (score >= 45) return '⚖️ CONSOLIDATING';
      return '🔴 WEAK';
    };

    const formatPrice = (val, assetType) => {
      if (!val || isNaN(val)) return '0.00';
      const num = Number(val);
      if (assetType === 'forex' || num < 2) return num.toFixed(4);
      if (num > 1000) return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      return num.toFixed(2);
    };

    const formatCurrency = (val) => {
      if (val === undefined || val === null || isNaN(val)) return '$0.00';
      return '$' + Number(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    };

    const openChart = (item) => {
      if (!item) return;
      selectedChartSymbol.value = item.symbol;
      selectedChartAsset.value = {
        symbol: item.symbol,
        asset_type: item.assetType || (item.category === 'STOCKS' ? 'stock_vn' : (item.category === 'FOREX' ? 'forex' : (item.category === 'COMMODITIES' ? 'commodities' : 'crypto'))),
        name: item.fullName || item.symbol,
        ...item
      };
      showChartModal.value = true;
      if (props.syncParentChart) {
        emit('select-symbol', item);
      }
    };

    const closeChartModal = () => {
      showChartModal.value = false;
      selectedChartSymbol.value = null;
      selectedChartAsset.value = null;
    };

    const refreshData = () => {
      fetchAllData();
    };

    let pollTimer = null;

    watch(() => props.externalPositions, (newPos) => {
      if (newPos && newPos.length > 0) {
        rawPositions.value = newPos;
      }
    }, { deep: true, immediate: true });

    onMounted(() => {
      fetchAllData();
      pollTimer = setInterval(() => {
        fetchAllData(true);
      }, 5000);
    });

    onUnmounted(() => {
      if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
      }
    });

    return {
      isLoading,
      searchQuery,
      sortBy,
      currentTab,
      categoryTabs,
      displayLimit,
      filteredItems,
      inTradeCount,
      getTabCount,
      topLeaderSymbol,
      topActiveTradeSymbol,
      showChartModal,
      selectedChartSymbol,
      selectedChartAsset,
      getStrengthClass,
      getStrengthBadgeClass,
      getStrengthBarClass,
      getStrengthStatusText,
      formatPrice,
      formatCurrency,
      openChart,
      closeChartModal,
      refreshData
    };
  }
};
</script>

<style scoped>
.market-strength-matrix-wrapper {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 1.25rem 1.5rem;
  backdrop-filter: blur(16px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  margin-bottom: 2rem;
}

/* Header */
.matrix-icon-badge {
  position: relative;
  width: 38px;
  height: 38px;
  background: rgba(0, 242, 254, 0.12);
  border: 1px solid rgba(0, 242, 254, 0.35);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  color: #00f2fe;
}

.pulse-ring {
  position: absolute;
  inset: -3px;
  border-radius: 12px;
  border: 1px solid rgba(0, 242, 254, 0.4);
  animation: pulseAnim 2.5s infinite;
}

@keyframes pulseAnim {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.08); opacity: 0.2; }
  100% { transform: scale(0.95); opacity: 0.8; }
}

.matrix-title {
  color: #ffffff;
  font-weight: 700;
  font-size: 1.15rem;
  letter-spacing: -0.01em;
}

.badge-live-scan {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: 20px;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.35);
  color: #34d399;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 6px #10b981;
  animation: blink 1.5s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* Controls */
.search-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 10px;
  color: #64748b;
  font-size: 0.78rem;
}

.matrix-search-input {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.4rem 1.8rem 0.4rem 2rem;
  color: #f1f5f9;
  font-size: 0.82rem;
  outline: none;
  width: 200px;
  transition: all 0.2s;
}

.matrix-search-input:focus {
  border-color: rgba(0, 242, 254, 0.5);
  width: 240px;
  box-shadow: 0 0 10px rgba(0, 242, 254, 0.15);
}

.clear-search-btn {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 1rem;
  cursor: pointer;
}

.matrix-select {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.4rem 0.8rem;
  color: #e2e8f0;
  font-size: 0.82rem;
  font-weight: 500;
  outline: none;
  cursor: pointer;
}

.limit-toggle-group {
  display: flex;
  align-items: center;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 2px;
  gap: 2px;
}

.limit-btn {
  padding: 0.25rem 0.6rem;
  font-size: 0.74rem;
  font-weight: 700;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.limit-btn:hover {
  color: #f1f5f9;
  background: rgba(255, 255, 255, 0.06);
}

.limit-btn.is-active {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.25), rgba(79, 172, 254, 0.2));
  color: #00f2fe;
  border-color: rgba(0, 242, 254, 0.4);
}

.btn-matrix-refresh {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #00f2fe;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-matrix-refresh:hover:not(:disabled) {
  background: rgba(0, 242, 254, 0.15);
  border-color: rgba(0, 242, 254, 0.4);
  transform: rotate(45deg);
}

.spin-anim {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Tabs */
.matrix-tabs-container {
  overflow-x: auto;
  padding-bottom: 4px;
}

.matrix-tabs-track {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: max-content;
}

.matrix-tab-btn {
  position: relative;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #94a3b8;
  padding: 0.45rem 0.85rem;
  border-radius: 10px;
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.45rem;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  user-select: none;
}

.matrix-tab-btn:hover {
  background: rgba(30, 41, 59, 0.85);
  color: #f1f5f9;
  border-color: rgba(255, 255, 255, 0.18);
  transform: translateY(-1px);
}

.matrix-tab-btn.is-active {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.18), rgba(79, 172, 254, 0.12));
  border-color: rgba(0, 242, 254, 0.5);
  color: #00f2fe;
  box-shadow: 0 4px 14px rgba(0, 242, 254, 0.15);
}

.tab-count-badge {
  font-size: 0.7rem;
  padding: 0.1rem 0.45rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  color: #94a3b8;
}

.tab-count-badge.count-active {
  background: rgba(0, 242, 254, 0.15);
  color: #00f2fe;
}

.tab-hot-pulse {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 8px;
  height: 8px;
  background: #f43f5e;
  border-radius: 50%;
  box-shadow: 0 0 8px #f43f5e;
}

/* Highlights Row */
.leader-highlight-pill {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0.3rem 0.75rem;
  border-radius: 20px;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.leader-highlight-pill:hover {
  border-color: rgba(0, 242, 254, 0.4);
  background: rgba(30, 41, 59, 0.9);
  transform: translateY(-1px);
}

.badge-leader-tag {
  font-size: 0.68rem;
  font-weight: 800;
  color: #fbbf24;
}

.badge-trade-tag {
  font-size: 0.68rem;
  font-weight: 800;
  color: #38bdf8;
}

.score-pill {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 6px;
}

.score-super {
  background: rgba(168, 85, 247, 0.2);
  color: #c084fc;
}

.score-green {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}
.dot-super { background: #c084fc; box-shadow: 0 0 4px #c084fc; }
.dot-bull { background: #34d399; }
.dot-neutral { background: #f59e0b; }
.dot-bear { background: #ef4444; }

/* Grid Cards */
.matrix-grid-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 1rem;
}

.matrix-card {
  background: rgba(18, 24, 38, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 12px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  overflow: hidden;
}

.matrix-card:hover {
  background: rgba(26, 35, 54, 0.95);
  border-color: rgba(0, 242, 254, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.matrix-card.card-in-trade {
  border-color: rgba(0, 242, 254, 0.3);
  background: linear-gradient(145deg, rgba(14, 165, 233, 0.08), rgba(18, 24, 38, 0.92));
}

.matrix-card.card-leader {
  border-color: rgba(234, 179, 8, 0.35);
}

.symbol-type-icon {
  font-size: 1.35rem;
}

.symbol-name {
  font-size: 0.95rem;
}

.badge-trade-active {
  font-size: 0.65rem;
  font-weight: 800;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  background: rgba(14, 165, 233, 0.2);
  color: #38bdf8;
  border: 1px solid rgba(14, 165, 233, 0.4);
}

.badge-rank-one {
  font-size: 0.65rem;
  font-weight: 800;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  background: rgba(234, 179, 8, 0.18);
  color: #fbbf24;
  border: 1px solid rgba(234, 179, 8, 0.35);
}

/* Strength Meter */
.strength-track {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.strength-fill {
  height: 100%;
  border-radius: 6px;
  position: relative;
  transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.bar-super {
  background: linear-gradient(90deg, #8b5cf6, #00f2fe);
  box-shadow: 0 0 10px rgba(0, 242, 254, 0.5);
}

.bar-bull {
  background: linear-gradient(90deg, #10b981, #34d399);
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
}

.bar-neutral {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.bar-bear {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.strength-status-text {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.strength-score-badge {
  font-size: 0.7rem;
  font-weight: 800;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
}

.badge-score-super { background: rgba(168, 85, 247, 0.15); color: #c084fc; }
.badge-score-bull { background: rgba(16, 185, 129, 0.15); color: #34d399; }
.badge-score-neutral { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
.badge-score-bear { background: rgba(239, 68, 68, 0.15); color: #f87171; }

.text-purple-glow {
  color: #c084fc;
  text-shadow: 0 0 8px rgba(192, 132, 252, 0.5);
}

.text-neon-green {
  color: #10b981;
}

.text-neon-red {
  color: #ef4444;
}

.border-glass {
  border-color: rgba(255, 255, 255, 0.07) !important;
}

/* Card Bottom */
.mini-metric-pill {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  color: #94a3b8;
}

.metric-pnl-win {
  color: #34d399;
  background: rgba(16, 185, 129, 0.12);
}

.metric-pnl-loss {
  color: #f87171;
  background: rgba(239, 68, 68, 0.12);
}

.badge-rank-one {
  background: linear-gradient(135deg, rgba(234, 179, 8, 0.25), rgba(245, 158, 11, 0.25));
  border: 1px solid rgba(234, 179, 8, 0.5);
  color: #fbbf24;
  font-size: 0.62rem;
  font-weight: 800;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
}

.badge-mcap-rank {
  font-size: 0.64rem;
  font-weight: 800;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.35);
  letter-spacing: 0.3px;
  line-height: 1.2;
}

.btn-quick-chart {
  background: rgba(0, 242, 254, 0.08);
  border: 1px solid rgba(0, 242, 254, 0.25);
  color: #00f2fe;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.25rem 0.55rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-quick-chart:hover {
  background: rgba(0, 242, 254, 0.2);
  border-color: rgba(0, 242, 254, 0.5);
  transform: translateY(-1px);
}

/* Modal */
.chart-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  z-index: 1050;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.chart-modal-card {
  background: #0f172a;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  width: 100%;
  max-width: 1020px;
  padding: 1.25rem;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
}

.vnstock-iframe {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 8px;
  background: #0b0f19;
}

/* Engine Toggle (TradingView vs Vietstock) */
.cell-engine-toggle {
  display: inline-flex;
  align-items: center;
  background: rgba(8, 12, 22, 0.95);
  padding: 2px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  gap: 2px;
  flex-shrink: 0;
}

.engine-btn {
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid transparent;
  background: transparent;
  color: #64748b;
  font-size: 0.68rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  line-height: 1.3;
}

.engine-btn:hover {
  color: #cbd5e1;
  background: rgba(255, 255, 255, 0.08);
}

.engine-btn.is-active {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.25) 0%, rgba(59, 130, 246, 0.25) 100%);
  color: #00f2fe;
  border-color: rgba(0, 242, 254, 0.4);
}

.btn-close-modal {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
}
.btn-close-modal:hover {
  color: #ffffff;
}

@media (max-width: 768px) {
  .market-strength-matrix-wrapper {
    padding: 1rem;
  }
  .matrix-grid-cards {
    grid-template-columns: 1fr;
  }
  .matrix-search-input {
    width: 140px;
  }
  .matrix-search-input:focus {
    width: 180px;
  }
}
</style>
