<template>
  <div class="d-flex flex-column min-vh-100 stk-page-bg">
    <NavBar />
    <notifications />
    <div class="stk-page flex-grow-1">
      <div class="stk-container">
        <!-- Tab Navigation -->
        <div class="stk-tabs">
          <button class="stk-tab" :class="{ 'stk-tab--active': activeTab === 'potential' }" @click="activeTab = 'potential'">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
            Potential Forex Pairs
          </button>
          <button class="stk-tab" :class="{ 'stk-tab--active': activeTab === 'prices' }" @click="activeTab = 'prices'">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
            Commodity Prices
          </button>
          <button class="stk-tab" :class="{ 'stk-tab--active': activeTab === 'rrg' }" @click="activeTab = 'rrg'">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10"/><path d="M2 12h20"/></svg>
            RRG Chart
          </button>
        </div>

        <!-- Tab Content -->
        <div class="stk-content">
          <!-- ==================== COMMODITY PRICES TAB ==================== -->
          <div v-show="activeTab === 'prices'">
            <div class="stk-panel">
              <div class="stk-header">
                <div class="stk-header__icon">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                </div>
                <div>
                  <h2 class="stk-header__title">Commodity Prices</h2>
                  <p class="stk-header__sub">Real-time price feeds for oils, gold, silver and metals</p>
                </div>
              </div>
              <div class="stk-section">
                <CurrencyPrices />
              </div>
            </div>
          </div>

          <!-- ==================== POTENTIAL FOREX PAIRS TAB ==================== -->
          <div v-show="activeTab === 'potential'">
            <div class="stk-panel">
              <div class="stk-header">
                <div class="stk-header__icon">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
                </div>
                <div>
                  <h2 class="stk-header__title">Forex Scanner</h2>
                  <p class="stk-header__sub">Discover divergent strengths, buy strong and sell weak currencies</p>
                </div>
              </div>

              <!-- Pair Input -->
              <div class="stk-section">
                <label class="stk-label">Search forex pair symbol</label>
                <div style="display:flex; gap:8px;">
                  <input
                    type="text"
                    class="stk-input"
                    v-model="pairInputText"
                    @keydown.enter="updateSelectedPair"
                    @input="pairInputText = $event.target.value.toUpperCase()"
                    placeholder="Enter pair (e.g. EURUSD) and press Enter"
                  />
                  <button class="stk-btn stk-btn--primary" @click="updateSelectedPair" :disabled="!pairInputText || !pairInputText.trim()">
                    View
                  </button>
                </div>
              </div>
            </div>

            <!-- Sticky Chart Panel (Matches Crypto) -->
            <div ref="chartRef" class="stk-sticky-chart" v-if="selectedPair && activeTab === 'potential'">
              <div class="stk-chart-wrap">
                <TradingViewChart :coin="selectedPairSymbol" :height="380" />
              </div>
              <!-- Price Alert Toggle -->
              <div class="stk-alert-toggle">
                <button class="stk-alert-toggle__btn" @click="showPriceAlert = !showPriceAlert">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                  Price Alert
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'stk-chevron--open': showPriceAlert }"><polyline points="6 9 12 15 18 9"/></svg>
                </button>
                <div v-show="showPriceAlert" class="stk-alert-content">
                  <PriceAlertWidget :symbol="selectedPair" assetType="forex" />
                </div>
              </div>
            </div>

            <!-- Potential Forex Pairs List -->
            <div class="stk-panel" v-if="forexPairs.length > 0">
              <div class="stk-section stk-section--potential">
                <div class="stk-section-head">
                  <h3 class="stk-section-head__title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                    Potential Forex Pairs
                  </h3>
                  <span v-if="latestUpdated" class="stk-updated">
                    Updated: {{ formatDateTime(latestUpdated) }}
                  </span>
                </div>

                <div ref="tableWrapRef" class="stk-table-wrap stk-table-wrap--scroll">
                  <table class="stk-table">
                    <thead>
                      <tr>
                        <th class="stk-th">Pair</th>
                        <th class="stk-th stk-th--center">Action</th>
                        <th class="stk-th stk-th--right">Score Diff</th>
                        <th class="stk-th">Note</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="pair in forexPairs"
                        :key="pair.pair"
                        class="stk-row"
                        :class="{ 'stk-row--active': isRowActive(pair) }"
                        @click="selectPair(pair)"
                      >
                        <td class="stk-td stk-td--symbol" :title="`View ${pair.pair} chart`">{{ pair.pair }}</td>
                        <td class="stk-td stk-td--center">
                          <span class="stk-signal" :class="pair.action === 'Buy' ? 'stk-signal--buy' : 'stk-signal--sell'">
                            {{ pair.action }}
                          </span>
                        </td>
                        <td class="stk-td stk-td--right" style="font-weight: 600;">
                          {{ pair.score_diff.toFixed(2) }}%
                        </td>
                        <td class="stk-td">{{ pair.note || '-' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div class="stk-actions">
                  <div style="display: flex; gap: 10px; align-items: center; justify-content: center; width: 100%;">
                    <button class="stk-btn stk-btn--primary stk-btn--scan" @click="scanForexPairs" :disabled="isScanning">
                      <span v-if="isScanning" class="stk-spinner" style="width: 14px; height: 14px; margin: 0; display: inline-block; border-width: 2px;"></span>
                      <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                      Start Scanning
                    </button>
                    <button class="stk-btn stk-btn--outline" @click="runSSHScript('forex_potential')" :disabled="isRunningPotentialScript" style="border-color: #3b82f6; color: #3b82f6;">
                      <span v-if="isRunningPotentialScript" class="stk-spinner" style="width: 14px; height: 14px; margin: 0; display: inline-block; border-width: 2px;"></span>
                      <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                      Run script
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="!isScanning && scanAttempted" class="stk-message">
              No forex pairs found. Please run the scan.
            </div>

            <div v-if="isScanning" class="stk-loading">
              <div class="stk-spinner"></div>
            </div>
          </div>

          <!-- ==================== RRG CHART TAB ==================== -->
          <div v-show="activeTab === 'rrg'">
            <div class="stk-panel">
              <div class="stk-header">
                <div class="stk-header__icon">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10"/><path d="M2 12h20"/></svg>
                </div>
                <div>
                  <h2 class="stk-header__title">Forex RRG Chart</h2>
                  <p class="stk-header__sub">Relative Rotation Graph for major Forex pairs against USD</p>
                </div>
              </div>
              <div class="stk-rrg-wrap">
                <div class="stk-rrg-actions" style="margin-bottom: 20px; display: flex; justify-content: center;">
                  <button
                    class="stk-btn stk-btn--primary"
                    @click="runSSHScript('forex_rrg')"
                    :disabled="isRunningRrgScript"
                    style="min-width: 180px; justify-content: center;"
                  >
                    <span v-if="isRunningRrgScript" class="stk-spinner" style="width: 16px; height: 16px; border-top-color: #fff; margin: 0; display: inline-block; border-width: 2px;"></span>
                    <span v-else style="display: inline-flex; align-items: center; gap: 6px;">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                      Generate RRG Chart
                    </span>
                  </button>
                </div>
                <img :src="forexRRGUrl" class="stk-rrg-img" alt="Forex RRG Chart" />
                <p class="stk-message" style="margin-top: 10px;">
                  Relative Rotation Graph (RRG) tracks the strength and momentum of currencies. Updated daily.
                </p>
              </div>
            </div>
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
import CurrencyPrices from './CurrencyPrices.vue';
import TradingViewChart from './TradingViewChart.vue';
import PriceAlertWidget from './PriceAlertWidget.vue';
import { ref, onMounted, computed, onUnmounted, nextTick } from 'vue';
import axios from 'axios';
import { useNotification } from "@kyvg/vue3-notification";

export default {
  components: {
    NavBar,
    AppFooter,
    CurrencyPrices,
    TradingViewChart,
    PriceAlertWidget
  },
  setup() {
    const { notify } = useNotification();
    const activeTab = ref('potential');
    
    // Forex pairs state
    const forexPairs = ref([]);
    const isScanning = ref(false);
    const scanAttempted = ref(false);
    const latestUpdated = ref(null);
    const selectedPair = ref('EURUSD');
    const selectedRowKey = ref('');
    const pairInputText = ref('');
    const showPriceAlert = ref(false);
    
    const chartRef = ref(null);
    const tableWrapRef = ref(null);

    onMounted(async () => {
      window.addEventListener('keydown', handleArrowNavigation);
      
      // Auto-fetch potential forex pairs on mount
      scanForexPairs();

      notify({ type: "info", title: "Forex Interface", text: "Successfully switched to Forex interface." });
    });

    onUnmounted(() => {
      window.removeEventListener('keydown', handleArrowNavigation);
    });

    const getTradingViewSymbol = (pair) => {
      if (!pair) return 'FX:EURUSD';
      
      const symbolMap = {
        'WTI': 'TVC:USOIL',
        'USOIL': 'TVC:USOIL',
        'UKOIL': 'TVC:UKOIL',
        'XAUUSD': 'OANDA:XAUUSD',
        'XAGUSD': 'OANDA:XAGUSD'
      };
      
      return symbolMap[pair] || `FX:${pair}`;
    };

    const selectedPairSymbol = computed(() => {
      return getTradingViewSymbol(selectedPair.value);
    });



    const scanForexPairs = async () => {
      isScanning.value = true;
      scanAttempted.value = true;
      try {
        const response = await axios.get('/getPotentialForexPairs');
        forexPairs.value = response.data.data || [];
        latestUpdated.value = response.data.latest_updated;
      } catch (error) {
        console.error('Error fetching forex pairs:', error);
        forexPairs.value = [];
      } finally {
        isScanning.value = false;
      }
    };

    const formatDateTime = (dateString) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString();
    };

    const getRowKey = (pair) => pair.pair;

    const isRowActive = (pair) => {
      if (selectedRowKey.value) return selectedRowKey.value === getRowKey(pair);
      return selectedPair.value === pair.pair;
    };

    const selectPair = (pair, shouldScroll = true) => {
      selectedPair.value = pair.pair;
      selectedRowKey.value = getRowKey(pair);

      if (!shouldScroll) return;
      setTimeout(() => {
        if (chartRef.value) {
          const y = chartRef.value.getBoundingClientRect().top + window.scrollY - 120;
          window.scrollTo({ top: y, behavior: 'smooth' });
        }
      }, 100);
    };

    const scrollActiveRowIntoView = async () => {
      await nextTick();
      const container = tableWrapRef.value;
      if (!container) return;
      const activeRow = container.querySelector('.stk-row--active');
      if (activeRow) activeRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    };

    const moveSelection = (direction) => {
      const rows = forexPairs.value;
      if (!rows.length) return;

      let currentIndex = rows.findIndex(r => getRowKey(r) === selectedRowKey.value);
      if (currentIndex === -1) {
        currentIndex = rows.findIndex(r => r.pair === selectedPair.value);
      }
      const baseIndex = currentIndex === -1 ? (direction > 0 ? -1 : 0) : currentIndex;
      const nextIndex = (baseIndex + direction + rows.length) % rows.length;
      const nextRow = rows[nextIndex];

      if (nextRow) {
        selectPair(nextRow, false);
        scrollActiveRowIntoView();
      }
    };

    const isTypingTarget = (target) => {
      if (!target) return false;
      const tag = (target.tagName || '').toLowerCase();
      return tag === 'input' || tag === 'textarea' || tag === 'select' || target.isContentEditable;
    };

    const handleArrowNavigation = (event) => {
      if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;
      if (isTypingTarget(event.target)) return;
      if (activeTab.value !== 'potential') return;

      const direction = event.key === 'ArrowDown' ? 1 : -1;
      moveSelection(direction);
      event.preventDefault();
    };

    const updateSelectedPair = () => {
      const input = pairInputText.value.trim().toUpperCase();
      if (input) {
        selectedPair.value = input;
        selectedRowKey.value = '';
        notify({ type: "success", title: "Chart Updated", text: `Switched to ${input}` });
      }
    };

    // SSH script execution states
    const isRunningPotentialScript = ref(false);
    const isRunningRrgScript = ref(false);
    const forexRRGKey = ref(Date.now());
    const forexRRGUrl = computed(() => `/forex_rrgchart?t=${forexRRGKey.value}`);

    const runSSHScript = async (scriptType) => {
      const isRrg = scriptType === 'forex_rrg';
      if (isRrg) {
        isRunningRrgScript.value = true;
      } else {
        isRunningPotentialScript.value = true;
      }

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
            text: isRrg ? 'Forex RRG Chart has been updated successfully!' : 'Forex scanner script executed successfully!',
          });
          if (isRrg) {
            forexRRGKey.value = Date.now();
          } else {
            scanForexPairs();
          }
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
        if (isRrg) {
          isRunningRrgScript.value = false;
        } else {
          isRunningPotentialScript.value = false;
        }
      }
    };

    return {
      activeTab,
      forexPairs,
      isScanning,
      scanAttempted,
      latestUpdated,
      scanForexPairs,
      formatDateTime,
      selectedPair,
      selectedPairSymbol,
      selectPair,
      isRowActive,
      getRowKey,
      pairInputText,
      updateSelectedPair,
      showPriceAlert,
      chartRef,
      tableWrapRef,
      isRunningPotentialScript,
      isRunningRrgScript,
      forexRRGUrl,
      runSSHScript
    };
  },
};
</script>

<style scoped>
/* ============================== */
/*  FOREX PAGE – Matches Stock/Crypto */
/* ============================== */

.stk-page-bg {
  background-color: #ffffff;
}

.stk-page { background: #ffffff; padding: 20px 0 40px; }
.stk-container { max-width: 1280px; margin: 0 auto; padding: 0 24px; }

/* ---------- TABS ---------- */
.stk-tabs { display: flex; gap: 6px; margin-bottom: 20px; overflow-x: auto; scrollbar-width: none; }
.stk-tabs::-webkit-scrollbar { display: none; }
.stk-tab {
  display: inline-flex; align-items: center; gap: 6px; padding: 10px 20px;
  border: 1px solid rgba(0, 0, 0, 0.06); border-radius: 10px; font-size: 0.88rem; font-weight: 600;
  color: #475569; background: rgba(0, 0, 0, 0.02); cursor: pointer; transition: all 0.2s ease;
  white-space: nowrap; box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
.stk-tab:hover { color: #0f172a; background: rgba(0, 0, 0, 0.05); }
.stk-tab--active { color: #fff !important; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2) !important; border-color: rgba(0, 0, 0, 0.05); }

/* ---------- PANEL ---------- */
.stk-panel { background: #ffffff; border: 1px solid rgba(0, 0, 0, 0.06); border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.04); overflow: hidden; margin-bottom: 20px; }

/* ---------- HEADER ---------- */
.stk-header { display: flex; align-items: center; gap: 14px; padding: 22px 24px; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); color: #0f172a; border-bottom: 1px solid rgba(0, 0, 0, 0.06); }
.stk-header__icon { width: 44px; height: 44px; border-radius: 12px; background: #ffffff; border: 1px solid rgba(0, 0, 0, 0.08); display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #0f172a; }
.stk-header__title { font-size: 1.2rem; font-weight: 700; margin: 0; line-height: 1.3; font-family: 'Outfit', sans-serif; color: #0f172a; }
.stk-header__sub { font-size: 0.82rem; color: #475569; margin: 2px 0 0; }

/* ---------- SECTIONS ---------- */
.stk-section { padding: 20px 24px; }
.stk-section--potential { border-top: 1px solid rgba(0, 0, 0, 0.06); }
.stk-label { display: block; font-size: 0.82rem; font-weight: 600; color: #475569; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.stk-section-head { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
.stk-section-head__title { display: inline-flex; align-items: center; gap: 8px; font-size: 1rem; font-weight: 700; color: #0f172a; margin: 0; font-family: 'Outfit', sans-serif; }
.stk-updated { font-size: 0.75rem; color: #64748b; font-weight: 500; }

/* ---------- CHART (sticky) ---------- */
.stk-sticky-chart { position: sticky; top: 60px; z-index: 20; background: #ffffff; padding: 12px 0; margin-bottom: 12px; }
.stk-chart-wrap { position: relative; border-radius: 12px; overflow: hidden; border: 1px solid rgba(0, 0, 0, 0.06); background: #ffffff; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03); }

/* ---------- PRICE ALERT ---------- */
.stk-alert-toggle { margin-top: 10px; }
.stk-alert-toggle__btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 7px 14px;
  border: 1px solid rgba(0, 0, 0, 0.08); border-radius: 8px; background: rgba(0, 0, 0, 0.02);
  color: #475569; font-size: 0.82rem; font-weight: 600; cursor: pointer; transition: all 0.15s;
}
.stk-alert-toggle__btn:hover { background: rgba(59,130,246,0.08); border-color: rgba(59,130,246,0.2); color: #2563eb; }
.stk-alert-toggle__btn svg:last-child { transition: transform 0.2s ease; }
.stk-chevron--open { transform: rotate(180deg); }
.stk-alert-content { margin-top: 8px; }

/* ---------- FILTERS ---------- */
.stk-input {
  width: 100%; padding: 9px 14px; border: 1px solid rgba(0, 0, 0, 0.1); border-radius: 8px;
  font-size: 0.85rem; color: #0f172a; background: #ffffff; transition: border-color 0.2s, box-shadow 0.2s; outline: none;
}
.stk-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.15); }

/* ---------- TABLE ---------- */
.stk-table-wrap { border-radius: 10px; border: 1px solid rgba(0, 0, 0, 0.06); overflow: hidden; background: #ffffff; }
.stk-table-wrap--scroll { max-height: 480px; overflow-y: auto; }
.stk-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.stk-th {
  padding: 10px 14px; text-align: left; font-size: 0.72rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.5px; color: #475569; background: #f1f5f9;
  border-bottom: 2px solid #e2e8f0; position: sticky; top: 0; z-index: 2;
}
.stk-th--center { text-align: center; }
.stk-th--right { text-align: right; }

.stk-row { cursor: pointer; transition: background 0.15s ease; }
.stk-row:hover { background: #f8fafc; }
.stk-row--active { background: rgba(59, 130, 246, 0.05) !important; }
.stk-td { padding: 10px 14px; border-bottom: 1px solid rgba(0, 0, 0, 0.04); vertical-align: middle; color: #334155; }
.stk-td--center { text-align: center; }
.stk-td--right { text-align: right; }
.stk-td--symbol { font-weight: 700; color: #2563eb; }

/* ---------- SIGNALS & BADGES ---------- */
.stk-signal { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; white-space: nowrap; }
.stk-signal--buy { background: rgba(16, 185, 129, 0.08); color: #059669; border: 1px solid rgba(16, 185, 129, 0.2); }
.stk-signal--sell { background: rgba(239, 68, 68, 0.08); color: #dc2626; border: 1px solid rgba(239, 68, 68, 0.2); }
.stk-signal--low { background: rgba(16, 185, 129, 0.08); color: #059669; border: 1px solid rgba(16, 185, 129, 0.2); }
.stk-signal--medium { background: rgba(245, 158, 11, 0.08); color: #d97706; border: 1px solid rgba(245, 158, 11, 0.2); }
.stk-signal--high { background: rgba(239, 68, 68, 0.08); color: #dc2626; border: 1px solid rgba(239, 68, 68, 0.2); box-shadow: 0 0 8px rgba(239, 68, 68, 0.1); }

/* ---------- BUTTONS ---------- */
.stk-actions { padding: 16px 0 0; display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 10px; }
.stk-btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 9px 18px;
  border: none; border-radius: 8px; font-size: 0.84rem; font-weight: 600;
  cursor: pointer; transition: all 0.2s ease; white-space: nowrap;
}
.stk-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.stk-btn--primary { background: linear-gradient(135deg, #3b82f6, #2563eb); color: #fff; box-shadow: 0 2px 8px rgba(59,130,246,0.3); }
.stk-btn--primary:hover:not(:disabled) { background: linear-gradient(135deg, #2563eb, #1d4ed8); box-shadow: 0 4px 14px rgba(37,99,235,0.4); transform: translateY(-1px); }
.stk-btn--outline { background: rgba(255,255,255,0.03); color: #475569; border: 1px solid rgba(0, 0, 0, 0.08); }
.stk-btn--outline:hover:not(:disabled) { background: rgba(0, 0, 0, 0.02); }
.stk-btn--scan { min-width: 180px; justify-content: center; }

/* ---------- LOADING ---------- */
.stk-loading { display: flex; justify-content: center; padding: 20px 0; }
.stk-spinner { width: 32px; height: 32px; border: 3px solid rgba(0, 0, 0, 0.06); border-top-color: #3b82f6; border-radius: 50%; animation: stk-spin 0.7s linear infinite; }
@keyframes stk-spin { to { transform: rotate(360deg); } }

.stk-message { text-align: center; font-size: 0.85rem; color: #64748b; padding: 10px 0; margin: 0; }

/* ---------- RRG ---------- */
.stk-rrg-wrap { padding: 24px; text-align: center; }
.stk-rrg-img { max-width: 100%; height: auto; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.08); border: 1px solid rgba(0, 0, 0, 0.06); }

/* ---------- RESPONSIVE ---------- */
@media (max-width: 640px) {
  .stk-container { padding: 0 10px; }
  .stk-header { padding: 16px; }
  .stk-section { padding: 16px; }
  .stk-sticky-chart { padding: 0 12px 10px; }
  .stk-tab { padding: 8px 14px; font-size: 0.82rem; }
  .stk-table-wrap--scroll { max-height: 400px; }
}
</style>