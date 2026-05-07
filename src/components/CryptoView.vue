<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />
    <notifications />
    <div class="stk-page flex-grow-1">
      <div class="stk-container">

        <!-- Tab Navigation -->
        <div class="stk-tabs">
          <button class="stk-tab" :class="{ 'stk-tab--active': activeTab === 'coins' }" @click="activeTab = 'coins'">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
            Potential Coins
          </button>
          <button class="stk-tab" :class="{ 'stk-tab--active': activeTab === 'rrg' }" @click="activeTab = 'rrg'">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10"/><path d="M2 12h20"/></svg>
            RRG Chart
          </button>
        </div>

        <!-- ==================== COINS TAB ==================== -->
        <div v-show="activeTab === 'coins'">
          <div class="stk-panel">
            <!-- Header -->
            <div class="stk-header">
              <div class="stk-header__icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
              </div>
              <div>
                <h2 class="stk-header__title">Crypto Scanner</h2>
                <p class="stk-header__sub">Discover potential coins near highs &amp; with MA9 ≥ EMA21</p>
              </div>
            </div>

            <!-- Coin Input -->
            <div class="stk-section">
              <label class="stk-label">Search coin symbol</label>
              <div style="display:flex; gap:8px;">
                <input
                  type="text"
                  class="stk-input"
                  v-model="coinInputText"
                  @keydown.enter="updateSelectedCoin"
                  @input="coinInputText = $event.target.value.toUpperCase()"
                  placeholder="Enter coin (e.g. BTCUSDT) and press Enter"
                />
                <button class="stk-btn stk-btn--primary" @click="updateSelectedCoin" :disabled="!coinInputText || !coinInputText.trim()">
                  View
                </button>
              </div>
            </div>
          </div>

          <!-- Chart (sticky) -->
          <div ref="chartRef" class="stk-sticky-chart">
            <div class="stk-chart-wrap">
              <TradingViewChart :coin="selectedCoin" :height="380" />
            </div>
            <!-- Price Alert Toggle -->
            <div class="stk-alert-toggle">
              <button class="stk-alert-toggle__btn" @click="showPriceAlert = !showPriceAlert">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                Price Alert
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'stk-chevron--open': showPriceAlert }"><polyline points="6 9 12 15 18 9"/></svg>
              </button>
              <div v-show="showPriceAlert" class="stk-alert-content">
                <PriceAlertWidget :symbol="selectedCoin" assetType="crypto" />
              </div>
            </div>
          </div>

          <!-- Potential Coins Section -->
          <div class="stk-panel">
            <div class="stk-section stk-section--potential">
              <div class="stk-section-head">
                <h3 class="stk-section-head__title">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                  Potential Coins
                </h3>
                <span v-if="potentialCoins.latest_updated" class="stk-updated">
                  Updated: {{ formatDate(potentialCoins.latest_updated) }}
                </span>
              </div>

              <!-- Filters -->
              <div class="stk-filters" v-if="potentialCoins.data && potentialCoins.data.length > 0">
                <div class="stk-filter-item">
                  <input type="text" v-model="filterText" placeholder="Filter coins..." class="stk-input" />
                </div>
                <div class="stk-filter-item">
                  <select v-model="selectedSignalType" class="stk-input">
                    <option value="">All Signals</option>
                    <option value="near_52w_ath">Near 52W High</option>
                    <option value="near_ath">Near ATH</option>
                    <option value="ma9_above_ema21">MA9 >= EMA21</option>
                  </select>
                </div>
              </div>

              <!-- Coins Table -->
              <div ref="tableWrapRef" class="stk-table-wrap stk-table-wrap--scroll" v-if="filteredPotentialCoins.length > 0">
                <table class="stk-table">
                  <thead>
                    <tr>
                      <th class="stk-th stk-th--chk"></th>
                      <th class="stk-th">Coin</th>
                      <th class="stk-th stk-th--center">Signal</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="coin in filteredPotentialCoins"
                      :key="getRowKey(coin)"
                      class="stk-row"
                      :class="{ 'stk-row--active': isRowActive(coin) }"
                      @click="selectCoin(coin)"
                    >
                      <td class="stk-td stk-td--chk">
                        <input type="checkbox" class="stk-checkbox" @click.stop="toggleStock(coin.crypto)" />
                      </td>
                      <td class="stk-td stk-td--symbol" :title="`View ${coin.crypto} chart`">{{ coin.crypto }}</td>
                      <td class="stk-td stk-td--center">
                        <span class="stk-signal" :class="'stk-signal--' + coin.signal_type">{{ getSignalLabel(coin) }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- Actions -->
              <div class="stk-actions">
                <div v-if="potentialCoins.data && potentialCoins.data.length > 0" class="stk-actions__group">
                  <button @click="exportCSV" class="stk-btn stk-btn--outline">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Export CSV
                  </button>
                </div>
                <button
                  v-if="!loadingPotentialCoins && !startScanning"
                  @click="startScanningCoins"
                  class="stk-btn stk-btn--primary stk-btn--scan"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                  Start Scanning
                </button>
                <div v-else-if="loadingPotentialCoins" class="stk-loading">
                  <div class="stk-spinner"></div>
                </div>
              </div>
              <p v-if="message" class="stk-message">{{ message }}</p>
            </div>
          </div>
        </div>

        <!-- ==================== RRG TAB ==================== -->
        <div class="stk-panel" v-show="activeTab === 'rrg'">
          <div class="stk-header">
            <div class="stk-header__icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10"/><path d="M2 12h20"/></svg>
            </div>
            <div>
              <h2 class="stk-header__title">Crypto RRG Chart</h2>
              <p class="stk-header__sub">Relative Rotation Graph for crypto market</p>
            </div>
          </div>
          <div class="stk-rrg-wrap">
            <img src="/cryto_rrgchart" class="stk-rrg-img" alt="Crypto RRG Chart" />
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
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue';
import { useNotification } from "@kyvg/vue3-notification";
import TradingViewChart from './TradingViewChart.vue';
import PriceAlertWidget from './PriceAlertWidget.vue';

const { notify } = useNotification();

export default {
  name: 'CryptoView',
  components: { NavBar, AppFooter, TradingViewChart, PriceAlertWidget },
  setup() {
    const activeTab = ref('coins');
    const selectedCoin = ref('BTCUSDT');
    const selectedRowKey = ref('');
    const coinInputText = ref('');
    const potentialCoins = ref({});
    const loadingPotentialCoins = ref(false);
    const startScanning = ref(false);
    const filterText = ref('');
    const selectedSignalType = ref('');
    const message = ref('');
    const showPriceAlert = ref(false);
    const chartRef = ref(null);
    const tableWrapRef = ref(null);

    // ---------- DATA FETCHING ----------
    onMounted(async () => {
      window.addEventListener('keydown', handleArrowNavigation);
      notify({ type: "info", title: "Welcome!", text: "The application has loaded successfully." });
    });

    onUnmounted(() => {
      window.removeEventListener('keydown', handleArrowNavigation);
    });

    const fetchPotentialCoins = async () => {
      loadingPotentialCoins.value = true;
      message.value = '';
      try {
        const response = await fetch('/getPotentialCoins');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        potentialCoins.value = data;
        if (!data.data || data.data.length === 0) {
          message.value = 'No potential coins available at the moment.';
        } else {
          message.value = `Found ${data.data.length} potential coins.`;
        }
      } catch (error) {
        console.error('Error fetching potential coins:', error);
        potentialCoins.value = { data: [] };
        message.value = 'Failed to load potential coins. Please try again later.';
      } finally {
        loadingPotentialCoins.value = false;
      }
    };

    const startScanningCoins = () => {
      startScanning.value = true;
      fetchPotentialCoins();
    };

    // ---------- FILTERING ----------
    const filteredPotentialCoins = computed(() => {
      const data = potentialCoins.value.data || [];
      return data.filter(coin => {
        const matchesText = !filterText.value ||
          coin.crypto.toLowerCase().includes(filterText.value.toLowerCase());
        const matchesSignal = !selectedSignalType.value ||
          coin.signal_type === selectedSignalType.value;
        return matchesText && matchesSignal;
      });
    });

    const getSignalLabel = (coin) => {
      const labelMap = {
        near_52w_ath: 'Near 52W High',
        near_ath: 'Near ATH',
        ma9_above_ema21: 'MA9 >= EMA21',
      };
      return coin?.signal_label || labelMap[coin?.signal_type] || coin?.signal_type || 'N/A';
    };

    // ---------- ROW SELECTION & NAVIGATION ----------
    const getRowKey = (coin) => `${coin.crypto}-${coin.signal_type || ''}`;

    const isRowActive = (coin) => {
      if (selectedRowKey.value) return selectedRowKey.value === getRowKey(coin);
      return selectedCoin.value === coin.crypto;
    };

    const selectCoin = (coin, shouldScroll = true) => {
      selectedCoin.value = coin.crypto;
      selectedRowKey.value = getRowKey(coin);

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
      const rows = filteredPotentialCoins.value;
      if (!rows.length) return;

      let currentIndex = rows.findIndex(r => getRowKey(r) === selectedRowKey.value);
      if (currentIndex === -1) {
        currentIndex = rows.findIndex(r => r.crypto === selectedCoin.value);
      }
      const baseIndex = currentIndex === -1 ? (direction > 0 ? -1 : 0) : currentIndex;
      const nextIndex = (baseIndex + direction + rows.length) % rows.length;
      const nextRow = rows[nextIndex];

      if (nextRow) {
        selectCoin(nextRow, false);
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
      if (activeTab.value !== 'coins') return;

      const direction = event.key === 'ArrowDown' ? 1 : -1;
      moveSelection(direction);
      event.preventDefault();
    };

    // ---------- MISC ----------
    const updateSelectedCoin = () => {
      const input = coinInputText.value.trim().toUpperCase();
      if (input) {
        selectedCoin.value = input;
        selectedRowKey.value = '';
        notify({ type: "success", title: "Chart Updated", text: `Switched to ${input}` });
      }
    };

    const toggleStock = () => { /* checkbox placeholder */ };

    const exportCSV = () => {
      const data = filteredPotentialCoins.value;
      if (!data || data.length === 0) return;
      const rows = data.map(c => `${c.crypto},${c.signal_type || ''},${c.signal_label || ''}`);
      const csvContent = "data:text/csv;charset=utf-8," + "coin,signal_type,signal_label\n" + rows.join("\n");
      const link = document.createElement("a");
      link.setAttribute("href", encodeURI(csvContent));
      link.setAttribute("download", "potential_coins.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };

    const formatDate = (dateString) => {
      const d = new Date(dateString);
      const pad = (n) => String(n).padStart(2, '0');
      return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
    };

    return {
      activeTab, selectedCoin, coinInputText, updateSelectedCoin,
      potentialCoins, filteredPotentialCoins, loadingPotentialCoins,
      startScanning, startScanningCoins, filterText, selectedSignalType,
      message, showPriceAlert, chartRef, tableWrapRef,
      getSignalLabel, getRowKey, isRowActive, selectCoin,
      toggleStock, exportCSV, formatDate,
    };
  }
}
</script>

<style scoped>
/* ============================== */
/*  CRYPTO PAGE – Matches Stock   */
/* ============================== */

.stk-page { background: #f0f2f5; padding: 20px 0 40px; }
.stk-container { max-width: 1280px; margin: 0 auto; padding: 0 24px; }

/* ---------- TABS ---------- */
.stk-tabs { display: flex; gap: 6px; margin-bottom: 20px; overflow-x: auto; scrollbar-width: none; }
.stk-tabs::-webkit-scrollbar { display: none; }
.stk-tab {
  display: inline-flex; align-items: center; gap: 6px; padding: 10px 20px;
  border: none; border-radius: 10px; font-size: 0.88rem; font-weight: 600;
  color: #64748b; background: #fff; cursor: pointer; transition: all 0.2s ease;
  white-space: nowrap; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.stk-tab:hover { color: #334155; background: #e8edf3; }
.stk-tab--active { color: #fff !important; background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important; box-shadow: 0 4px 12px rgba(30,41,59,0.3); }

/* ---------- PANEL ---------- */
.stk-panel { background: #fff; border-radius: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }

/* ---------- HEADER ---------- */
.stk-header { display: flex; align-items: center; gap: 14px; padding: 22px 24px; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: #fff; border-radius: 16px 16px 0 0; }
.stk-header__icon { width: 44px; height: 44px; border-radius: 12px; background: rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.stk-header__title { font-size: 1.2rem; font-weight: 700; margin: 0; line-height: 1.3; }
.stk-header__sub { font-size: 0.82rem; color: rgba(255,255,255,0.6); margin: 2px 0 0; }

/* ---------- SECTIONS ---------- */
.stk-section { padding: 20px 24px; }
.stk-section--potential { border-top: 1px solid #e2e8f0; }
.stk-label { display: block; font-size: 0.82rem; font-weight: 600; color: #475569; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.3px; }
.stk-section-head { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
.stk-section-head__title { display: inline-flex; align-items: center; gap: 8px; font-size: 1rem; font-weight: 700; color: #1e293b; margin: 0; }
.stk-updated { font-size: 0.75rem; color: #64748b; font-weight: 500; }

/* ---------- CHART (sticky) ---------- */
.stk-sticky-chart { position: sticky; top: 60px; z-index: 20; background: #f0f2f5; padding: 12px 0; margin-bottom: 12px; }
.stk-chart-wrap { position: relative; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; background: #fff; }

/* ---------- PRICE ALERT ---------- */
.stk-alert-toggle { margin-top: 10px; }
.stk-alert-toggle__btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 7px 14px;
  border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fafc;
  color: #475569; font-size: 0.82rem; font-weight: 600; cursor: pointer; transition: all 0.15s;
}
.stk-alert-toggle__btn:hover { background: #eff6ff; border-color: #93c5fd; color: #1e40af; }
.stk-alert-toggle__btn svg:last-child { transition: transform 0.2s ease; }
.stk-chevron--open { transform: rotate(180deg); }
.stk-alert-content { margin-top: 8px; }

/* ---------- FILTERS ---------- */
.stk-filters { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }
.stk-filter-item { flex: 1 1 200px; }
.stk-input {
  width: 100%; padding: 9px 14px; border: 1px solid #cbd5e1; border-radius: 8px;
  font-size: 0.85rem; color: #1e293b; background: #fff; transition: border-color 0.2s, box-shadow 0.2s; outline: none;
}
.stk-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.15); }

/* ---------- TABLE ---------- */
.stk-table-wrap { border-radius: 10px; border: 1px solid #e2e8f0; overflow: hidden; }
.stk-table-wrap--scroll { max-height: 480px; overflow-y: auto; }
.stk-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.stk-th {
  padding: 10px 14px; text-align: left; font-size: 0.72rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; background: #f8fafc;
  border-bottom: 2px solid #e2e8f0; position: sticky; top: 0; z-index: 2;
}
.stk-th--center { text-align: center; }
.stk-th--chk { width: 36px; text-align: center; }

.stk-row { cursor: pointer; transition: background 0.15s ease; }
.stk-row:hover { background: #f1f5f9; }
.stk-row--active { background: #eff6ff !important; }
.stk-td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.stk-td--chk { width: 36px; text-align: center; }
.stk-td--center { text-align: center; }
.stk-td--symbol { font-weight: 700; color: #1e40af; }

.stk-checkbox { width: 16px; height: 16px; accent-color: #3b82f6; cursor: pointer; }

/* ---------- SIGNALS ---------- */
.stk-signal { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; white-space: nowrap; }
.stk-signal--near_52w_ath { background: #dcfce7; color: #166534; }
.stk-signal--near_ath { background: #fef3c7; color: #92400e; }
.stk-signal--ma9_above_ema21 { background: #dbeafe; color: #1e40af; }

/* ---------- BUTTONS ---------- */
.stk-actions { padding: 16px 0 0; display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 10px; }
.stk-actions__group { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
.stk-btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 9px 18px;
  border: none; border-radius: 8px; font-size: 0.84rem; font-weight: 600;
  cursor: pointer; transition: all 0.2s ease; white-space: nowrap;
}
.stk-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.stk-btn--primary { background: linear-gradient(135deg, #3b82f6, #2563eb); color: #fff; box-shadow: 0 2px 8px rgba(59,130,246,0.3); }
.stk-btn--primary:hover:not(:disabled) { background: linear-gradient(135deg, #2563eb, #1d4ed8); box-shadow: 0 4px 14px rgba(37,99,235,0.4); transform: translateY(-1px); }
.stk-btn--outline { background: #fff; color: #334155; border: 1px solid #cbd5e1; }
.stk-btn--outline:hover:not(:disabled) { background: #f1f5f9; border-color: #94a3b8; }
.stk-btn--scan { min-width: 180px; justify-content: center; }

/* ---------- LOADING ---------- */
.stk-loading { display: flex; justify-content: center; padding: 20px 0; }
.stk-spinner { width: 32px; height: 32px; border: 3px solid #e2e8f0; border-top-color: #3b82f6; border-radius: 50%; animation: stk-spin 0.7s linear infinite; }
@keyframes stk-spin { to { transform: rotate(360deg); } }

.stk-message { text-align: center; font-size: 0.85rem; color: #64748b; padding: 10px 0; margin: 0; }

/* ---------- RRG ---------- */
.stk-rrg-wrap { padding: 24px; text-align: center; }
.stk-rrg-img { max-width: 100%; height: auto; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }

/* ---------- RESPONSIVE ---------- */
@media (max-width: 640px) {
  .stk-container { padding: 0 10px; }
  .stk-header { padding: 16px; }
  .stk-section { padding: 16px; }
  .stk-sticky-chart { padding: 0 12px 10px; }
  .stk-tab { padding: 8px 14px; font-size: 0.82rem; }
  .stk-filters { flex-direction: column; }
  .stk-table-wrap--scroll { max-height: 400px; }
}
</style>