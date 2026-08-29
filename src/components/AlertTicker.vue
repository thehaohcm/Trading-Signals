<template>
  <div class="alert-ticker-bar" v-if="marketAssets.length > 0">
    <div class="alert-ticker-inner">
      <!-- Latest Alert Tag / Fixed Card -->
      <div class="latest-alert-badge" v-if="marketAssets.length > 0">
        <div 
          class="market-card-link" 
          @click="openChartModal(marketAssets[0])" 
          :title="marketAssets[0].message || marketAssets[0].name"
        >
          <div class="market-card market-card--mini market-card--latest">
            <div class="d-flex justify-content-between align-items-center mb-1 gap-1">
              <div class="d-flex align-items-center gap-1">
                <span class="live-pulse-dot" title="Live alert stream"></span>
                <span class="market-card__icon" :style="{ background: marketAssets[0].iconBg }">{{ marketAssets[0].emoji }}</span>
              </div>
              <span class="market-card__change" :class="marketAssets[0].positive ? 'text-neon-green' : 'text-neon-red'">
                {{ marketAssets[0].change }}
              </span>
            </div>
            <h4 class="market-card__title">{{ marketAssets[0].name }}</h4>
            <p class="market-card__price mb-0">{{ marketAssets[0].price }}</p>
            <div class="market-card__time small">⏱️ {{ marketAssets[0].relativeTime || 'Vừa xong' }}</div>
            <div class="market-card__sparkline">
              <svg viewBox="0 0 100 30" class="sparkline-svg">
                <path :d="marketAssets[0].sparkline" fill="none" :stroke="marketAssets[0].positive ? '#10b981' : '#ef4444'" stroke-width="2" stroke-linecap="round"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Auto-scrolling Marquee Stream -->
      <div class="marquee-stream-wrapper" v-if="marketAssets.length > 1">
        <!-- Left Navigation Button -->
        <button 
          class="marquee-nav-btn marquee-nav-btn--left" 
          @click="scrollMarquee('left')"
          aria-label="Scroll left"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>

        <div 
          ref="marqueeContainer"
          class="marquee-container custom-horizontal-scroll" 
          @scroll="handleMarqueeScroll"
          @wheel="onMarqueeWheel"
          @mouseenter="pauseMarquee"
          @mouseleave="resumeMarquee"
          @touchstart="pauseMarquee"
          @touchend="resumeMarquee"
        >
          <div ref="marqueeContent" class="marquee-js-content">
            <!-- Double tracks for seamless infinite loop -->
            <div class="marquee-track marquee-track--mini" v-for="i in 2" :key="i">
              <template v-for="(asset, idx) in scrollingAssets" :key="`marquee-group-${i}-${idx}`">
                <div class="market-card-wrapper market-card-wrapper--mini">
                  <div class="market-card-link" @click="openChartModal(asset)">
                    <div class="market-card market-card--mini" :title="asset.message || asset.name">
                      <div class="d-flex justify-content-between align-items-center mb-1 gap-1">
                        <span class="market-card__icon" :style="{ background: asset.iconBg }">{{ asset.emoji }}</span>
                        <span class="market-card__change" :class="asset.positive ? 'text-neon-green' : 'text-neon-red'">
                          {{ asset.change }}
                        </span>
                      </div>
                      <h4 class="market-card__title">{{ asset.name }}</h4>
                      <p class="market-card__price mb-0">{{ asset.price }}</p>
                      <div class="market-card__time small">⏱️ {{ asset.relativeTime || 'Vừa xong' }}</div>
                      <div class="market-card__sparkline">
                        <svg viewBox="0 0 100 30" class="sparkline-svg">
                          <path :d="asset.sparkline" fill="none" :stroke="asset.positive ? '#10b981' : '#ef4444'" stroke-width="2" stroke-linecap="round"></path>
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Loop cycle separator -->
                <div 
                  v-if="marketAssets.length > 2 && (idx + 1) % (marketAssets.length - 1) === 0"
                  class="marquee-separator"
                  :key="`marquee-sep-${i}-${idx}`"
                >
                  <div class="marquee-separator-line">
                    <div class="marquee-separator-dot"></div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>

        <!-- Right Navigation Button -->
        <button 
          class="marquee-nav-btn marquee-nav-btn--right" 
          @click="scrollMarquee('right')"
          aria-label="Scroll right"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
        </button>
      </div>
    </div>

    <!-- Chart Modal -->
    <div v-if="showChartModal" class="modal-backdrop" @click="closeChartModal">
      <div class="custom-modal" @click.stop>
        <div class="modal-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0 modal-title-text">{{ displayTitle }}</h5>
          <button type="button" class="btn-close btn-close-white" @click="closeChartModal"></button>
        </div>
        <!-- Search Symbol Input Bar -->
        <div class="modal-symbol-bar">
          <div class="modal-input-group">
            <svg class="modal-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input
              type="text"
              class="modal-symbol-input"
              v-model="symbolInputText"
              @keydown.enter="updateModalSymbol"
              @input="symbolInputText = $event.target.value.toUpperCase()"
              placeholder="Enter symbol (e.g. BTCUSDT, AAPL, EURUSD, XAUUSD...) and press Enter"
            />
          </div>
          <button
            class="modal-symbol-btn"
            @click="updateModalSymbol"
            :disabled="!symbolInputText || !symbolInputText.trim()"
          >
            View
          </button>
        </div>
        <div class="modal-body p-0">
          <template v-if="isVnStock">
            <iframe
              :key="currentSymbol"
              :src="`https://stockchart.vietstock.vn/?stockcode=${currentSymbol}`"
              width="100%"
              height="500"
              frameborder="0"
              allowfullscreen
              style="border-radius: 0 0 16px 16px; background: #ffffff;"
            ></iframe>
          </template>
          <template v-else>
            <TradingViewChart :key="selectedAssetChartSymbol" v-if="selectedAssetChartSymbol" :coin="selectedAssetChartSymbol" :height="500" />
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import TradingViewChart from './TradingViewChart.vue';

export default {
  name: 'AlertTicker',
  components: {
    TradingViewChart,
  },
  setup() {
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
        emoji: '₿',
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
      if (typeof price !== 'number') {
        const num = parseFloat(price);
        if (isNaN(num)) return price || '0';
        price = num;
      }
      if (assetType === 'stock') {
        if (price > 1000) {
          return `${price.toLocaleString('vi-VN')} đ`;
        } else {
          return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
        }
      } else if (assetType === 'crypto' || assetType === 'futures' || assetType === 'commodities' || assetType === 'forex') {
        let minFractionDigits = 2;
        if (assetType === 'forex' || price < 1) {
          minFractionDigits = 4;
        }
        return `$${price.toLocaleString('en-US', { minimumFractionDigits: minFractionDigits })}`;
      }
      return price.toLocaleString();
    };

    const parseAlertChange = (msg) => {
      if (!msg) return { change: 'ALERT', positive: true };
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
        const response = await fetch('/triggeredAlerts?limit=50');
        if (!response.ok) throw new Error('Failed to fetch alerts');
        const data = await response.json();
        
        if (data && data.length > 0) {
          const seenSymbols = new Set();
          const mappedAlerts = [];
          
          for (const alert of data) {
            const key = `${alert.asset_type}-${alert.symbol}`;
            if (seenSymbols.has(key)) continue;
            seenSymbols.add(key);

            const parsed = parseAlertChange(alert.message);
            
            let name = '';
            let emoji = '🔔';
            let iconBg = 'rgba(139, 92, 246, 0.1)';
            let link = '/';
            let isUS = false;

            if (alert.asset_type === 'stock') {
              isUS = alert.symbol.includes(':') || alert.symbol.length > 3 || alert.message.includes('Stock US');
              name = `${isUS ? 'US Stock' : 'VN Stock'} (${alert.symbol.split(':').pop()})`;
              emoji = '📈';
              iconBg = 'rgba(16, 185, 129, 0.1)';
              link = '/stock';
            } else if (alert.asset_type === 'crypto') {
              name = `Crypto (${alert.symbol})`;
              emoji = '₿';
              iconBg = 'rgba(245, 158, 11, 0.1)';
              link = '/crypto';
            } else if (alert.asset_type === 'futures') {
              name = `Futures (${alert.symbol})`;
              emoji = '📊';
              iconBg = 'rgba(59, 130, 246, 0.1)';
              link = '/futures';
            } else if (alert.asset_type === 'commodities' || alert.asset_type === 'gold' || alert.asset_type === 'silver' || alert.asset_type === 'oil') {
              const commodityNames = {
                'GC=F': 'Vàng (Gold)',
                'XAUUSD': 'Vàng (Gold)',
                'SI=F': 'Bạc (Silver)',
                'XAGUSD': 'Bạc (Silver)',
                'BZ=F': 'Dầu Brent (UKOIL)',
                'UKOIL': 'Dầu Brent (UKOIL)',
                'CL=F': 'Dầu WTI (USOIL)',
                'USOIL': 'Dầu WTI (USOIL)'
              };
              const comName = commodityNames[alert.symbol] || alert.symbol;
              name = `${comName}`;
              emoji = (alert.symbol === 'GC=F' || alert.symbol === 'XAUUSD' || alert.asset_type === 'gold') ? '🏆' : 
                      ((alert.symbol === 'SI=F' || alert.symbol === 'XAGUSD' || alert.asset_type === 'silver') ? '🥈' : '🛢️');
              iconBg = 'rgba(234, 179, 8, 0.1)';
              link = '/commodities';
            } else if (alert.asset_type === 'forex') {
              name = `Forex (${alert.symbol})`;
              emoji = '💱';
              iconBg = 'rgba(139, 92, 246, 0.1)';
              link = '/forex';
            } else {
              name = `${alert.asset_type.toUpperCase()} (${alert.symbol})`;
            }

            mappedAlerts.push({
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
              assetType: alert.asset_type,
              isUS: isUS
            });
          }

          marketAssets.value = mappedAlerts.length > 0 ? mappedAlerts : [...defaultAssets];
        }
      } catch (error) {
        console.error('Error loading latest alerts:', error);
      }
    };

    // Marquee state & animation
    const marqueeContainer = ref(null);
    const marqueeContent = ref(null);
    let marqueeAnimFrame = null;
    const marqueeSpeed = 0.6;
    let marqueePaused = false;
    let marqueeUserScrolling = false;
    let marqueeResumeTimeout = null;
    let totalTrackWidth = 0;
    let pollInterval = null;

    const scrollingAssets = computed(() => {
      const list = marketAssets.value.slice(1);
      if (list.length === 0) return [];
      const repeated = [];
      while (repeated.length < 15) {
        repeated.push(...list);
      }
      return repeated;
    });

    const recalcTrackWidth = () => {
      if (!marqueeContainer.value) return;
      const el = marqueeContainer.value.querySelector('.marquee-js-content');
      if (el) {
        totalTrackWidth = el.scrollWidth;
      }
    };

    const stepMarquee = () => {
      if (!marqueeContainer.value || !marqueeContent.value) {
        marqueeAnimFrame = requestAnimationFrame(stepMarquee);
        return;
      }
      if (totalTrackWidth === 0) {
        recalcTrackWidth();
      }
      if (totalTrackWidth === 0) {
        marqueeAnimFrame = requestAnimationFrame(stepMarquee);
        return;
      }
      if (!marqueePaused && !marqueeUserScrolling) {
        marqueeContainer.value.scrollLeft += marqueeSpeed;
      }
      marqueeAnimFrame = requestAnimationFrame(stepMarquee);
    };

    const startMarqueeScroll = () => {
      recalcTrackWidth();
      if (marqueeAnimFrame) return;
      marqueeAnimFrame = requestAnimationFrame(stepMarquee);
    };

    const stopMarqueeScroll = () => {
      if (marqueeAnimFrame) {
        cancelAnimationFrame(marqueeAnimFrame);
        marqueeAnimFrame = null;
      }
    };

    const pauseMarquee = () => {
      marqueePaused = true;
    };

    const resumeMarquee = () => {
      marqueePaused = false;
    };

    const handleMarqueeScroll = () => {
      if (!marqueeContainer.value || totalTrackWidth === 0) return;
      const container = marqueeContainer.value;
      const scrollLeft = container.scrollLeft;
      const halfWidth = totalTrackWidth / 2;

      if (!marqueeUserScrolling) {
        if (scrollLeft >= halfWidth) {
          container.scrollLeft = scrollLeft - halfWidth;
        }
      }
    };

    const scrollMarquee = (direction) => {
      if (!marqueeContainer.value) return;
      marqueeUserScrolling = true;

      const scrollAmount = 300;
      const container = marqueeContainer.value;
      const targetScroll = direction === 'left'
        ? container.scrollLeft - scrollAmount
        : container.scrollLeft + scrollAmount;

      container.scrollTo({
        left: targetScroll,
        behavior: 'smooth'
      });

      if (marqueeResumeTimeout) clearTimeout(marqueeResumeTimeout);
      marqueeResumeTimeout = setTimeout(() => {
        marqueeUserScrolling = false;
      }, 2000);
    };

    const onMarqueeWheel = (event) => {
      if (!marqueeContainer.value) return;
      marqueeUserScrolling = true;
      marqueeContainer.value.scrollLeft += event.deltaY;

      if (marqueeResumeTimeout) clearTimeout(marqueeResumeTimeout);
      marqueeResumeTimeout = setTimeout(() => {
        marqueeUserScrolling = false;
      }, 1000);
    };

    // Chart Modal State
    const showChartModal = ref(false);
    const selectedAsset = ref(null);
    const symbolInputText = ref('');
    const customSymbol = ref('');

    const displayTitle = computed(() => {
      const sym = customSymbol.value || selectedAsset.value?.symbol || '';
      if (customSymbol.value && (!selectedAsset.value || customSymbol.value !== selectedAsset.value.symbol)) {
        return `${sym} - CHART`;
      }
      return selectedAsset.value?.name || (sym ? `${sym} - CHART` : 'Chart');
    });

    const currentSymbol = computed(() => {
      return customSymbol.value || (selectedAsset.value ? selectedAsset.value.symbol : '');
    });

    const selectedAssetChartSymbol = computed(() => {
      const sym = currentSymbol.value;
      if (!sym) return '';
      let type = (selectedAsset.value && !customSymbol.value) ? selectedAsset.value.assetType : '';
      if (type === 'futures' && sym.toUpperCase().endsWith('USDT')) {
        return `BINANCE:${sym}.P`;
      }
      if (sym.includes(':')) {
        return sym;
      }
      if (sym.toUpperCase().endsWith('USDT')) {
        return `BINANCE:${sym}`;
      }
      if (type === 'stock') {
        if (sym === 'SPX') return 'SP:SPX';
      }
      if (type === 'forex' && !sym.includes(':')) {
        const forexMap = {
          'XAUUSD': 'OANDA:XAUUSD',
          'XAGUSD': 'OANDA:XAGUSD',
          'WTI': 'TVC:USOIL',
          'DXY': 'TVC:DXY'
        };
        return forexMap[sym] || `FX:${sym}`;
      }
      if (type === 'commodities' || type === 'gold' || type === 'silver' || type === 'oil') {
        const commodityMap = {
          'GC=F': 'OANDA:XAUUSD',
          'XAUUSD': 'OANDA:XAUUSD',
          'SI=F': 'OANDA:XAGUSD',
          'XAGUSD': 'OANDA:XAGUSD',
          'CL=F': 'TVC:USOIL',
          'USOIL': 'TVC:USOIL',
          'BZ=F': 'TVC:UKOIL',
          'UKOIL': 'TVC:UKOIL'
        };
        return commodityMap[sym] || sym;
      }
      if (type === 'yield') {
        const yieldMap = {
          'US02Y': 'TVC:US02Y',
          'US05Y': 'TVC:US05Y',
          'US10Y': 'TVC:US10Y',
          'US30Y': 'TVC:US30Y',
          'JP02Y': 'TVC:JP02Y',
          'JP10Y': 'TVC:JP10Y',
          'JP30Y': 'TVC:JP30Y',
          'GB02Y': 'TVC:GB02Y',
          'GB10Y': 'TVC:GB10Y',
          'GB30Y': 'TVC:GB30Y',
          'DE02Y': 'TVC:DE02Y',
          'DE10Y': 'TVC:DE10Y',
          'DE30Y': 'TVC:DE30Y'
        };
        return yieldMap[sym] || `TVC:${sym}`;
      }
      return sym;
    });

    const isVnStock = computed(() => {
      const sym = currentSymbol.value;
      if (!sym) return false;
      if (!selectedAsset.value || selectedAsset.value.assetType !== 'stock') return false;
      if (selectedAsset.value.isUS) return false;
      if (selectedAsset.value.message && selectedAsset.value.message.includes('Stock US')) return false;
      return !sym.includes(':') && sym !== 'SPX';
    });

    const openChartModal = (asset) => {
      selectedAsset.value = asset;
      customSymbol.value = '';
      symbolInputText.value = asset?.symbol || '';
      showChartModal.value = true;
    };

    const closeChartModal = () => {
      showChartModal.value = false;
      selectedAsset.value = null;
      customSymbol.value = '';
      symbolInputText.value = '';
    };

    const updateModalSymbol = () => {
      const input = (symbolInputText.value || '').trim().toUpperCase();
      if (input) {
        customSymbol.value = input;
      }
    };

    onMounted(() => {
      fetchLatestAlerts();
      pollInterval = setInterval(fetchLatestAlerts, 15000);
      nextTick(() => {
        startMarqueeScroll();
      });
    });

    onUnmounted(() => {
      if (pollInterval) clearInterval(pollInterval);
      stopMarqueeScroll();
      if (marqueeResumeTimeout) clearTimeout(marqueeResumeTimeout);
    });

    return {
      marketAssets,
      scrollingAssets,
      marqueeContainer,
      marqueeContent,
      pauseMarquee,
      resumeMarquee,
      onMarqueeWheel,
      handleMarqueeScroll,
      scrollMarquee,
      showChartModal,
      selectedAsset,
      symbolInputText,
      displayTitle,
      currentSymbol,
      updateModalSymbol,
      selectedAssetChartSymbol,
      isVnStock,
      openChartModal,
      closeChartModal
    };
  }
};
</script>

<style scoped>
.alert-ticker-bar {
  width: 100%;
  background: rgba(10, 13, 20, 0.85);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding: 6px 14px;
  position: relative;
  z-index: 1040;
}

.alert-ticker-inner {
  display: flex;
  align-items: stretch;
  gap: 8px;
  max-width: 100%;
  margin: 0 auto;
}

/* Latest Alert Badge */
.latest-alert-badge {
  flex-shrink: 0;
  display: flex;
  align-items: stretch;
}

.market-card-link {
  text-decoration: none;
  color: inherit;
  display: block;
  cursor: pointer;
  height: 100%;
}

.market-card {
  background: rgba(18, 24, 38, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(12px);
  user-select: none;
}

.market-card:hover {
  transform: translateY(-2px);
  border-color: rgba(0, 242, 254, 0.4);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4), 0 0 12px rgba(0, 242, 254, 0.2);
}

.market-card--mini {
  width: 135px;
  padding: 5px 9px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.market-card--latest {
  border: 1.5px solid rgba(0, 242, 254, 0.5);
  box-shadow: 0 0 14px rgba(0, 242, 254, 0.2);
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.08) 0%, rgba(18, 24, 38, 0.95) 100%);
}

.live-pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #00f2fe;
  box-shadow: 0 0 6px #00f2fe;
  animation: pulse-glow 1.5s infinite alternate;
  display: inline-block;
}

@keyframes pulse-glow {
  0% { opacity: 0.4; transform: scale(0.85); }
  100% { opacity: 1; transform: scale(1.15); box-shadow: 0 0 10px #00f2fe; }
}

.market-card__icon {
  width: 17px;
  height: 17px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.68rem;
}

.market-card__change {
  font-weight: 800;
  font-size: 0.55rem;
  padding: 0.5px 4px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  letter-spacing: 0.3px;
}

.text-neon-green {
  color: #00f5a0;
  text-shadow: 0 0 8px rgba(0, 245, 160, 0.35);
}

.text-neon-red {
  color: #ff4b72;
  text-shadow: 0 0 8px rgba(255, 75, 114, 0.35);
}

.market-card__title {
  font-size: 0.64rem;
  font-weight: 700;
  color: #94a3b8;
  margin-bottom: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.market-card__price {
  font-size: 0.74rem;
  font-weight: 800;
  color: #ffffff;
  white-space: nowrap;
}

.market-card__time {
  font-size: 0.52rem;
  line-height: 0.75rem;
  color: #64748b;
  font-weight: 500;
  margin-top: 1px;
}

.market-card__sparkline {
  height: 12px;
  margin-top: 3px;
}

.sparkline-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

/* Marquee Stream */
.marquee-stream-wrapper {
  position: relative;
  flex-grow: 1;
  min-width: 0;
  display: flex;
  align-items: stretch;
}

.marquee-container {
  overflow-x: auto;
  position: relative;
  min-width: 0;
  display: flex;
  align-items: stretch;
  width: 100%;
  scrollbar-width: none; /* Hide default scrollbar */
}

.marquee-container::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

.marquee-js-content {
  display: flex;
  align-items: stretch;
  width: max-content;
}

.marquee-track--mini {
  display: flex;
  align-items: stretch;
  gap: 0.45rem;
  padding-right: 0.45rem;
}

.market-card-wrapper--mini {
  width: 135px;
  flex-shrink: 0;
  white-space: normal;
}

/* Loop cycle separator */
.marquee-separator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  flex-shrink: 0;
  height: 100%;
  align-self: center;
}

.marquee-separator-line {
  width: 2px;
  height: 60%;
  background: linear-gradient(to bottom, transparent, rgba(0, 242, 254, 0.3) 20%, rgba(0, 242, 254, 0.3) 80%, transparent);
  border-radius: 99px;
  position: relative;
}

.marquee-separator-dot {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 5px;
  height: 5px;
  background-color: #00f2fe;
  border-radius: 50%;
  box-shadow: 0 0 6px rgba(0, 242, 254, 0.6);
}

/* Navigation Buttons */
.marquee-nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(18, 24, 38, 0.95);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: all 0.2s ease;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.35);
  opacity: 0;
  pointer-events: none;
}

.marquee-stream-wrapper:hover .marquee-nav-btn {
  opacity: 1;
  pointer-events: auto;
}

.marquee-nav-btn:hover {
  background: #00f2fe;
  color: #0a0d14;
  border-color: #00f2fe;
  box-shadow: 0 4px 14px rgba(0, 242, 254, 0.45);
  transform: translateY(-50%) scale(1.1);
}

.marquee-nav-btn:active {
  transform: translateY(-50%) scale(0.95);
}

.marquee-nav-btn--left {
  left: 4px;
}

.marquee-nav-btn--right {
  right: 4px;
}

/* Modal styles */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.75);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(6px);
}

.custom-modal {
  background: #111726;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
}

.modal-header {
  padding: 0.9rem 1.4rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(10, 13, 20, 0.85);
}

.modal-title-text {
  font-family: 'Outfit', sans-serif;
  font-weight: 800;
  color: #ffffff;
  font-size: 1.05rem;
}

.modal-symbol-bar {
  display: flex;
  gap: 10px;
  padding: 10px 1.4rem;
  background: rgba(18, 24, 38, 0.6);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  align-items: center;
}

.modal-input-group {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
}

.modal-search-icon {
  position: absolute;
  left: 12px;
  color: #94a3b8;
  pointer-events: none;
}

.modal-symbol-input {
  width: 100%;
  padding: 8px 14px 8px 36px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #ffffff;
  background: rgba(10, 13, 20, 0.85);
  outline: none;
  transition: all 0.2s;
  letter-spacing: 0.5px;
}

.modal-symbol-input:focus {
  border-color: #00f2fe;
  box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.15);
}

.modal-symbol-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
  color: #0a0d14;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-symbol-btn:hover:not(:disabled) {
  opacity: 0.92;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 242, 254, 0.3);
}

.modal-symbol-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-close-white {
  filter: invert(1) grayscale(100%) brightness(200%);
}

@media (max-width: 768px) {
  .alert-ticker-bar {
    padding: 4px 8px;
  }
  .market-card--mini {
    width: 115px;
    padding: 4px 7px;
  }
  .market-card-wrapper--mini {
    width: 115px;
  }
  .custom-modal {
    width: 96%;
  }
}
</style>
