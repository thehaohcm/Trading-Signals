<template>
  <div v-if="visible" class="multi-chart-backdrop" :class="{ 'is-minimized-backdrop': isMinimized }" @click.self="handleBackdropClick">
    <!-- Floating Minimized Pill when minimized -->
    <div v-if="isMinimized" class="minimized-pill" @click="toggleMinimize">
      <div class="d-flex align-items-center gap-2">
        <i class="fa-solid fa-chart-line text-cyan"></i>
        <span class="fw-bold">{{ activeSymbolDisplay }}</span>
        <span class="badge bg-secondary">{{ splitCount }} Chart{{ splitCount > 1 ? 's' : '' }}</span>
      </div>
      <div class="d-flex align-items-center gap-1 ms-3">
        <button class="pill-btn" @click.stop="toggleMinimize" title="Phục hồi cửa sổ">
          <i class="fa-solid fa-window-restore"></i>
        </button>
        <button class="pill-btn pill-btn--close" @click.stop="closeModal" title="Đóng">
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>
    </div>

    <!-- Main Modal Window -->
    <div 
      v-else 
      class="multi-chart-modal" 
      :class="{ 
        'is-maximized': isMaximized,
        'split-layout-1': splitCount === 1,
        'split-layout-2': splitCount === 2,
        'split-layout-4': splitCount === 4,
        'split-layout-8': splitCount === 8
      }" 
      @click.stop
    >
      <!-- Modal Header -->
      <div class="modal-header-bar">
        <div class="header-left d-flex align-items-center gap-2">
          <div class="chart-header-icon">
            <i class="fa-solid fa-chart-candlestick"></i>
          </div>
          <div>
            <h5 class="modal-title m-0">{{ modalTitle }}</h5>
            <span class="modal-subtitle">{{ activeSubtitle }}</span>
          </div>
        </div>

        <!-- Split Window Selector Controls -->
        <div class="header-center">
          <div class="split-controls-group" title="Chia cửa sổ biểu đồ (Split Chart Windows)">
            <span class="split-label d-none d-lg-inline">Split:</span>
            <button 
              type="button"
              class="split-btn" 
              :class="{ 'is-active': splitCount === 1 }" 
              @click="setSplitCount(1)"
              title="1 Cửa sổ (Single View)"
            >
              <span class="split-icon">▢</span>
              <span class="split-text">1</span>
            </button>
            <button 
              type="button"
              class="split-btn" 
              :class="{ 'is-active': splitCount === 2 }" 
              @click="setSplitCount(2)"
              title="2 Cửa sổ song song (Split 1x2)"
            >
              <span class="split-icon">◫</span>
              <span class="split-text">2</span>
            </button>
            <button 
              type="button"
              class="split-btn" 
              :class="{ 'is-active': splitCount === 4 }" 
              @click="setSplitCount(4)"
              title="4 Cửa sổ lưới (Grid 2x2)"
            >
              <span class="split-icon">⊞</span>
              <span class="split-text">4</span>
            </button>
            <button 
              type="button"
              class="split-btn" 
              :class="{ 'is-active': splitCount === 8 }" 
              @click="setSplitCount(8)"
              title="8 Cửa sổ nâng cao (Grid 4x2)"
            >
              <span class="split-icon">▦</span>
              <span class="split-text">8</span>
            </button>
          </div>
        </div>

        <!-- Header Window Action Buttons -->
        <div class="header-right d-flex align-items-center gap-1">
          <!-- Minimize Button -->
          <button 
            type="button" 
            class="window-ctrl-btn" 
            @click="toggleMinimize" 
            title="Thu nhỏ thành thanh nổi"
          >
            <i class="fa-solid fa-minus"></i>
          </button>

          <!-- Maximize / Restore Button -->
          <button 
            type="button" 
            class="window-ctrl-btn" 
            @click="toggleMaximize" 
            :title="isMaximized ? 'Thu nhỏ về kích thước chuẩn' : 'Phóng to toàn màn hình (Full Screen)'"
          >
            <i class="fa-solid" :class="isMaximized ? 'fa-compress' : 'fa-expand'"></i>
          </button>

          <!-- Close Button -->
          <button 
            type="button" 
            class="window-ctrl-btn window-ctrl-btn--close" 
            @click="closeModal" 
            title="Đóng cửa sổ"
          >
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
      </div>

      <!-- Quick Preset & Primary Search Bar -->
      <div class="modal-quick-bar">
        <div class="quick-input-wrapper">
          <svg class="search-svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            ref="primarySearchInput"
            type="text"
            class="quick-search-input"
            v-model="primaryInputText"
            @focus="$event.target.select()"
            @keydown.enter="applyPrimarySymbol"
            @input="primaryInputText = $event.target.value.toUpperCase()"
            :placeholder="`Nhập mã cho Chart #${activeSlotIndex + 1} (e.g. BTCUSDT, AAPL, EURUSD, XAUUSD, VCB)...`"
          />
          <button 
            v-if="primaryInputText" 
            type="button" 
            class="quick-clear-btn" 
            @click="primaryInputText = ''; $refs.primarySearchInput?.focus()" 
            title="Xóa nhanh"
          >
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
        <button 
          class="quick-apply-btn" 
          @click="applyPrimarySymbol"
          :disabled="!primaryInputText || !primaryInputText.trim()"
        >
          <span>Xem Chart</span>
        </button>

        <!-- Quick preset badges -->
        <div class="quick-presets d-none d-md-flex align-items-center gap-1 ms-2">
          <span class="preset-label small text-muted">Nhanh:</span>
          <button 
            v-for="preset in quickPresets" 
            :key="preset.symbol"
            type="button" 
            class="preset-chip"
            @click="setSlotSymbol(activeSlotIndex, preset.symbol, preset.type)"
          >
            {{ preset.label }}
          </button>
        </div>
      </div>

      <!-- Multi-Chart Grid Container -->
      <div class="modal-charts-grid-wrapper custom-scrollbar">
        <div 
          class="charts-grid" 
          :class="`grid-count-${splitCount}`"
        >
          <div 
            v-for="(slot, index) in activeSlots" 
            :key="`chart-slot-${index}-${slot.resolvedSymbol}`"
            class="chart-cell"
            :class="{ 'is-active-cell': activeSlotIndex === index }"
            @click="activeSlotIndex = index"
          >
            <!-- Cell Header with Dedicated Symbol Input Bar -->
            <div class="cell-header">
              <div class="cell-info d-flex align-items-center gap-1">
                <span class="cell-num-badge">#{{ index + 1 }}</span>
                <span class="cell-symbol-title" :title="slot.symbol">{{ slot.symbol }}</span>
                <span class="cell-type-badge" v-if="slot.assetType">{{ slot.assetType }}</span>
              </div>

              <!-- Dedicated Symbol Textbox & Button for this chart -->
              <div class="cell-search-bar" @click.stop>
                <div class="cell-input-group position-relative">
                  <svg class="cell-search-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                  </svg>
                  <input 
                    type="text" 
                    class="cell-symbol-input"
                    v-model="slot.tempInput"
                    @focus="$event.target.select()"
                    @click="$event.target.select()"
                    @keydown.enter.stop="updateCellSymbol(index)"
                    @input="slot.tempInput = $event.target.value.toUpperCase()"
                    :placeholder="`Mã Chart #${index + 1}...`"
                    title="Nhập mã symbol cho chart này và nhấn Xem hoặc Enter"
                  />
                  <button 
                    v-if="slot.tempInput"
                    type="button"
                    class="cell-input-clear-btn"
                    @click.stop="slot.tempInput = ''"
                    title="Xóa"
                  >
                    <i class="fa-solid fa-xmark"></i>
                  </button>
                </div>
                <button 
                  type="button"
                  class="cell-view-btn" 
                  @click.stop="updateCellSymbol(index)" 
                  title="Cập nhật chart này"
                >
                  <i class="fa-solid fa-arrow-right d-sm-none"></i>
                  <span class="d-none d-sm-inline">Xem</span>
                </button>
              </div>
            </div>

            <!-- Chart Body -->
            <div class="cell-body">
              <template v-if="slot.isVnStock">
                <iframe
                  :key="slot.resolvedSymbol"
                  :src="`https://stockchart.vietstock.vn/?stockcode=${slot.resolvedSymbol}`"
                  width="100%"
                  :height="computedChartHeight"
                  frameborder="0"
                  allowfullscreen
                  class="vnstock-iframe"
                ></iframe>
              </template>
              <template v-else>
                <TradingViewChart 
                  :key="slot.resolvedSymbol" 
                  :coin="slot.resolvedSymbol" 
                  :height="computedChartHeight" 
                />
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import TradingViewChart from './TradingViewChart.vue';

export default {
  name: 'MultiChartModal',
  components: {
    TradingViewChart
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    initialSymbol: {
      type: String,
      default: 'BTCUSDT'
    },
    initialAsset: {
      type: Object,
      default: () => null
    }
  },
  emits: ['close', 'update:visible'],
  setup(props, { emit }) {
    const splitCount = ref(1);
    const isMaximized = ref(false);
    const isMinimized = ref(false);
    const activeSlotIndex = ref(0);
    const primaryInputText = ref('');
    const primarySearchInput = ref(null);

    const quickPresets = [
      { label: 'BTC', symbol: 'BTCUSDT', type: 'crypto' },
      { label: 'ETH', symbol: 'ETHUSDT', type: 'crypto' },
      { label: 'SOL', symbol: 'SOLUSDT', type: 'crypto' },
      { label: 'GOLD', symbol: 'GC=F', type: 'commodities' },
      { label: 'OIL', symbol: 'TVC:USOIL', type: 'commodities' },
      { label: 'EURUSD', symbol: 'EURUSD', type: 'forex' },
      { label: 'SPX', symbol: 'SPX', type: 'stock' },
      { label: 'VNINDEX', symbol: 'VNINDEX', type: 'stock_vn' }
    ];

    const defaultSymbols = [
      'BTCUSDT',
      'ETHUSDT',
      'SOLUSDT',
      'BNBUSDT',
      'XRPUSDT',
      'DOGEUSDT',
      'GC=F',
      'SPX'
    ];

    // Array of 8 slots
    const slots = ref(
      Array.from({ length: 8 }, (_, i) => ({
        symbol: defaultSymbols[i] || 'BTCUSDT',
        tempInput: defaultSymbols[i] || 'BTCUSDT',
        assetType: 'crypto',
        isVnStock: false,
        resolvedSymbol: defaultSymbols[i] || 'BTCUSDT'
      }))
    );

    const resolveVnStockCode = (code) => {
      const upper = String(code || '').trim().toUpperCase();
      if (upper === 'VN30FM1') return 'VN30F1M';
      if (upper === 'UPCOMINDEX') return 'UPCOMINDEX';
      return upper;
    };

    const checkIsVnStock = (sym, type, asset) => {
      const raw = String(sym || '').trim().toUpperCase();
      if (!raw) return false;
      const t = String(type || asset?.asset_type || asset?.assetType || '').toLowerCase();

      if (t === 'stock_vn' || t === 'stock_vietnam') return true;
      if (t === 'stock_us' || asset?.isUS) return false;
      if (asset?.message && asset.message.includes('Stock US')) return false;

      if (t === 'stock') {
        return !raw.includes(':') && raw !== 'SPX';
      }

      if (['VNINDEX', 'VN30', 'VN30F1M', 'VN30FM1', 'HNXINDEX', 'UPCOMINDEX'].includes(raw)) {
        return true;
      }
      return false;
    };

    const resolveChartSymbol = (sym, type) => {
      const raw = String(sym || '').trim();
      if (!raw) return 'BTCUSDT';
      const upper = raw.toUpperCase();
      const t = String(type || '').toLowerCase();

      if (checkIsVnStock(raw, t)) {
        return resolveVnStockCode(raw);
      }

      if (t === 'futures' && upper.endsWith('USDT')) {
        return `BINANCE:${upper}.P`;
      }
      if (raw.includes(':')) {
        return raw;
      }
      if (upper.endsWith('USDT')) {
        return `BINANCE:${upper}`;
      }
      if (upper === 'SPX') return 'SP:SPX';

      const forexMap = {
        'XAUUSD': 'OANDA:XAUUSD',
        'XAGUSD': 'OANDA:XAGUSD',
        'WTI': 'TVC:USOIL',
        'DXY': 'CAPITALCOM:DXY',
        'USDVND': 'USDVND'
      };
      if (forexMap[upper]) return forexMap[upper];

      const commodityMap = {
        'GC=F': 'OANDA:XAUUSD',
        'SI=F': 'OANDA:XAGUSD',
        'CL=F': 'TVC:USOIL',
        'USOIL': 'TVC:USOIL',
        'BZ=F': 'TVC:UKOIL',
        'UKOIL': 'TVC:UKOIL'
      };
      if (commodityMap[upper]) return commodityMap[upper];

      return raw;
    };

    const setSlotSymbol = (index, symbol, type = '') => {
      if (index < 0 || index >= slots.value.length) return;
      const clean = String(symbol || '').trim().toUpperCase();
      if (!clean) return;

      const isVn = checkIsVnStock(clean, type);
      const resolved = resolveChartSymbol(clean, type);

      slots.value[index] = {
        symbol: clean,
        tempInput: clean,
        assetType: type || (isVn ? 'stock_vn' : 'crypto'),
        isVnStock: isVn,
        resolvedSymbol: resolved
      };

      if (activeSlotIndex.value === index) {
        primaryInputText.value = clean;
      }
    };

    const initInitialSlot = () => {
      const initSym = props.initialSymbol || props.initialAsset?.symbol || 'BTCUSDT';
      const initType = props.initialAsset?.assetType || props.initialAsset?.asset_type || '';
      setSlotSymbol(0, initSym, initType);
      primaryInputText.value = initSym;
    };

    watch(() => props.visible, (val) => {
      if (val) {
        isMinimized.value = false;
        initInitialSlot();
      }
    }, { immediate: true });

    watch(() => props.initialSymbol, () => {
      if (props.visible) {
        initInitialSlot();
      }
    });

    const activeSlots = computed(() => {
      return slots.value.slice(0, splitCount.value);
    });

    const activeSlot = computed(() => {
      return slots.value[activeSlotIndex.value] || slots.value[0];
    });

    const activeSymbolDisplay = computed(() => {
      return activeSlot.value?.symbol || 'Chart';
    });

    const modalTitle = computed(() => {
      if (props.initialAsset?.name && splitCount.value === 1) {
        return props.initialAsset.name;
      }
      return `${activeSymbolDisplay.value} - Multi-Chart Studio`;
    });

    const activeSubtitle = computed(() => {
      return `Hiển thị ${splitCount.value} biểu đồ đồng thời • Nhấp vào từng ô để đổi mã`;
    });

    const computedChartHeight = computed(() => {
      if (isMaximized.value) {
        if (splitCount.value === 1) return 720;
        if (splitCount.value === 2) return 680;
        if (splitCount.value === 4) return 360;
        return 320;
      }
      if (splitCount.value === 1) return 500;
      if (splitCount.value === 2) return 460;
      if (splitCount.value === 4) return 320;
      return 280;
    });

    const setSplitCount = (count) => {
      splitCount.value = count;
      if (activeSlotIndex.value >= count) {
        activeSlotIndex.value = 0;
      }
    };

    const toggleMaximize = () => {
      isMaximized.value = !isMaximized.value;
      if (isMinimized.value) isMinimized.value = false;
    };

    const toggleMinimize = () => {
      isMinimized.value = !isMinimized.value;
    };

    const closeModal = () => {
      emit('close');
      emit('update:visible', false);
      isMinimized.value = false;
    };

    const handleBackdropClick = () => {
      closeModal();
    };

    const applyPrimarySymbol = () => {
      if (!primaryInputText.value || !primaryInputText.value.trim()) return;
      setSlotSymbol(activeSlotIndex.value, primaryInputText.value.trim());
    };

    const updateCellSymbol = (index) => {
      const slot = slots.value[index];
      if (slot && slot.tempInput && slot.tempInput.trim()) {
        setSlotSymbol(index, slot.tempInput.trim());
      }
    };

    const handleKeyDown = (e) => {
      if (!props.visible) return;
      if (e.key === 'Escape') {
        if (isMaximized.value) {
          isMaximized.value = false;
        } else {
          closeModal();
        }
      }
    };

    onMounted(() => {
      window.addEventListener('keydown', handleKeyDown);
    });

    onUnmounted(() => {
      window.removeEventListener('keydown', handleKeyDown);
    });

    return {
      splitCount,
      isMaximized,
      isMinimized,
      activeSlotIndex,
      primaryInputText,
      primarySearchInput,
      quickPresets,
      slots,
      activeSlots,
      activeSlot,
      activeSymbolDisplay,
      modalTitle,
      activeSubtitle,
      computedChartHeight,
      setSplitCount,
      toggleMaximize,
      toggleMinimize,
      closeModal,
      handleBackdropClick,
      applyPrimarySymbol,
      updateCellSymbol,
      setSlotSymbol
    };
  }
};
</script>

<style scoped>
.multi-chart-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(4, 7, 15, 0.82);
  backdrop-filter: blur(10px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  animation: modal-fade-in 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.is-minimized-backdrop {
  background: transparent !important;
  backdrop-filter: none !important;
  pointer-events: none;
  align-items: flex-end;
  justify-content: flex-end;
  padding: 24px;
}

@keyframes modal-fade-in {
  from { opacity: 0; transform: scale(0.98); }
  to { opacity: 1; transform: scale(1); }
}

/* Floating Minimized Pill */
.minimized-pill {
  pointer-events: auto;
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.95), rgba(15, 23, 42, 0.98));
  border: 1.5px solid rgba(0, 242, 254, 0.5);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6), 0 0 18px rgba(0, 242, 254, 0.3);
  border-radius: 99px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.25s ease;
  z-index: 10000;
}

.minimized-pill:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.7), 0 0 24px rgba(0, 242, 254, 0.45);
}

.pill-btn {
  background: rgba(255, 255, 255, 0.08);
  border: none;
  color: #94a3b8;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.pill-btn:hover {
  background: rgba(0, 242, 254, 0.2);
  color: #00f2fe;
}

.pill-btn--close:hover {
  background: rgba(239, 68, 68, 0.25);
  color: #f87171;
}

/* Main Modal Window */
.multi-chart-modal {
  background: #0d121f;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  width: 94%;
  max-width: 1050px;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.75), 0 0 20px rgba(0, 242, 254, 0.12);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.multi-chart-modal.split-layout-2 {
  max-width: 1280px;
}

.multi-chart-modal.split-layout-4,
.multi-chart-modal.split-layout-8 {
  max-width: 1540px;
}

/* Maximized (Full Screen) Mode */
.multi-chart-modal.is-maximized {
  width: 99vw !important;
  max-width: 99vw !important;
  height: 97vh !important;
  max-height: 97vh !important;
  border-radius: 10px;
  border-color: rgba(0, 242, 254, 0.35);
  box-shadow: 0 0 35px rgba(0, 242, 254, 0.25);
}

/* Header */
.modal-header-bar {
  padding: 10px 18px;
  background: linear-gradient(180deg, rgba(20, 28, 48, 0.95) 0%, rgba(13, 18, 31, 0.98) 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.chart-header-icon {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.2), rgba(59, 130, 246, 0.2));
  border: 1px solid rgba(0, 242, 254, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #00f2fe;
  font-size: 1rem;
}

.modal-title {
  font-family: 'Outfit', sans-serif;
  font-weight: 800;
  font-size: 1.05rem;
  color: #ffffff;
  letter-spacing: 0.3px;
}

.modal-subtitle {
  font-size: 0.72rem;
  color: #94a3b8;
}

/* Split Controls Group */
.split-controls-group {
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(8, 12, 22, 0.8);
  padding: 3px 6px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.split-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: #64748b;
  margin-right: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.split-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 7px;
  background: transparent;
  border: 1px solid transparent;
  color: #94a3b8;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.split-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #ffffff;
}

.split-btn.is-active {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.25), rgba(59, 130, 246, 0.25));
  border-color: rgba(0, 242, 254, 0.6);
  color: #00f2fe;
  box-shadow: 0 0 10px rgba(0, 242, 254, 0.25);
}

.split-icon {
  font-size: 0.88rem;
  line-height: 1;
}

/* Window Control Buttons */
.window-ctrl-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.window-ctrl-btn:hover {
  background: rgba(0, 242, 254, 0.18);
  color: #00f2fe;
  border-color: rgba(0, 242, 254, 0.4);
}

.window-ctrl-btn--close:hover {
  background: rgba(239, 68, 68, 0.25);
  color: #f87171;
  border-color: rgba(239, 68, 68, 0.5);
}

/* Quick Search Bar */
.modal-quick-bar {
  padding: 8px 18px;
  background: rgba(13, 18, 31, 0.9);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-input-wrapper {
  position: relative;
  flex: 1;
  min-width: 220px;
  display: flex;
  align-items: center;
}

.search-svg {
  position: absolute;
  left: 12px;
  color: #64748b;
  pointer-events: none;
}

.quick-search-input {
  width: 100%;
  padding: 7px 34px 7px 34px;
  border-radius: 8px;
  background: rgba(8, 12, 22, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #ffffff;
  font-size: 0.82rem;
  font-weight: 600;
  outline: none;
  transition: all 0.2s;
}

.quick-search-input:focus {
  border-color: #00f2fe;
  box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.15);
}

.quick-clear-btn {
  position: absolute;
  right: 8px;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
}

.quick-clear-btn:hover {
  color: #f87171;
}

.quick-apply-btn {
  padding: 7px 16px;
  border-radius: 8px;
  background: linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%);
  border: none;
  color: #080c16;
  font-weight: 700;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-apply-btn:hover:not(:disabled) {
  opacity: 0.94;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 242, 254, 0.35);
}

.quick-apply-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.preset-chip {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  color: #cbd5e1;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 3px 7px;
  cursor: pointer;
  transition: all 0.18s ease;
}

.preset-chip:hover {
  background: rgba(0, 242, 254, 0.15);
  border-color: rgba(0, 242, 254, 0.4);
  color: #00f2fe;
}

/* Charts Grid Container */
.modal-charts-grid-wrapper {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 10px;
  background: #090d18;
}

.charts-grid {
  display: grid;
  gap: 10px;
  width: 100%;
}

/* Grid layout variations */
.grid-count-1 {
  grid-template-columns: 1fr;
}

.grid-count-2 {
  grid-template-columns: repeat(2, 1fr);
}

.grid-count-4 {
  grid-template-columns: repeat(2, 1fr);
}

.grid-count-8 {
  grid-template-columns: repeat(4, 1fr);
}

@media (max-width: 1200px) {
  .grid-count-8 {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .grid-count-2,
  .grid-count-4,
  .grid-count-8 {
    grid-template-columns: 1fr;
  }
}

/* Chart Cell */
.chart-cell {
  background: #111726;
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: all 0.2s ease;
}

.chart-cell.is-active-cell {
  border-color: rgba(0, 242, 254, 0.55);
  box-shadow: 0 0 12px rgba(0, 242, 254, 0.2);
}

.cell-header {
  padding: 6px 10px;
  background: linear-gradient(180deg, rgba(20, 27, 44, 0.95) 0%, rgba(14, 19, 32, 0.98) 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: nowrap;
}

.cell-info {
  min-width: 0;
  flex-shrink: 0;
}

.cell-num-badge {
  font-size: 0.64rem;
  font-weight: 800;
  padding: 1.5px 5px;
  border-radius: 4px;
  background: rgba(0, 242, 254, 0.15);
  color: #00f2fe;
  border: 1px solid rgba(0, 242, 254, 0.35);
  letter-spacing: 0.3px;
}

.cell-symbol-title {
  font-size: 0.78rem;
  font-weight: 800;
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100px;
}

.cell-type-badge {
  font-size: 0.58rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #94a3b8;
  background: rgba(255, 255, 255, 0.06);
  padding: 1px 4px;
  border-radius: 4px;
}

.cell-search-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  max-width: 240px;
  justify-content: flex-end;
}

.cell-input-group {
  position: relative;
  flex: 1;
  min-width: 90px;
  display: flex;
  align-items: center;
}

.cell-search-icon {
  position: absolute;
  left: 7px;
  color: #64748b;
  pointer-events: none;
}

.cell-symbol-input {
  width: 100%;
  padding: 4px 20px 4px 23px;
  background: rgba(8, 12, 22, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 6px;
  color: #ffffff;
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.3px;
  outline: none;
  transition: all 0.2s;
}

.cell-symbol-input:focus {
  border-color: #00f2fe;
  box-shadow: 0 0 0 2px rgba(0, 242, 254, 0.2);
  background: rgba(12, 17, 30, 0.95);
}

.cell-input-clear-btn {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  color: #64748b;
  font-size: 0.65rem;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
}

.cell-input-clear-btn:hover {
  color: #f87171;
}

.cell-view-btn {
  padding: 4px 10px;
  background: linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%);
  border: none;
  border-radius: 6px;
  color: #080c16;
  font-size: 0.72rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.cell-view-btn:hover {
  opacity: 0.92;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 242, 254, 0.35);
}

.cell-body {
  flex: 1;
  background: #ffffff;
  min-height: 250px;
}

.vnstock-iframe {
  background: #ffffff;
  border-radius: 0 0 10px 10px;
}

/* Custom Scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(10, 13, 20, 0.5);
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 99px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 242, 254, 0.4);
}

.text-cyan {
  color: #00f2fe !important;
}
</style>
