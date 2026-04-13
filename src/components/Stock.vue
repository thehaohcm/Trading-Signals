<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />

    <div class="stk-page flex-grow-1">
      <div class="stk-container">

        <!-- Tab Navigation -->
        <div class="stk-tabs">
          <button
            class="stk-tab"
            :class="{ 'stk-tab--active': activeTab === 'vn' }"
            @click="activeTab = 'vn'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
            VN Stock
          </button>
          <button
            class="stk-tab"
            :class="{ 'stk-tab--active': activeTab === 'vn_rrg' }"
            @click="activeTab = 'vn_rrg'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10"/><path d="M2 12h20"/></svg>
            RRG Chart
          </button>
          <button
            class="stk-tab"
            :class="{ 'stk-tab--active': activeTab === 'global' }"
            @click="activeTab = 'global'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10"/><path d="M12 2a15 15 0 0 0-4 10 15 15 0 0 0 4 10"/></svg>
            Global Stock
          </button>
        </div>

        <!-- ==================== VN TAB ==================== -->
        <div v-show="activeTab === 'vn'">
          <div class="stk-panel">
            <!-- Header -->
            <div class="stk-header">
              <div class="stk-header__icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
              </div>
              <div>
                <h2 class="stk-header__title">Vietnam Stock Evaluator</h2>
                <p class="stk-header__sub">Search, evaluate &amp; discover potential VN stocks</p>
              </div>
            </div>

            <!-- Stock Selector -->
            <div class="stk-section">
              <label class="stk-label">Choose a stock symbol</label>
              <v-select
                v-model="selectedStock"
                :options="stocks"
                label="code"
                @input="onStockSelected"
                :filter-options="filterOptions"
                class="stk-select"
              ></v-select>
            </div>
          </div>

          <!-- Chart (sticky, outside panel so it works) -->
          <div ref="vnChartRef" v-if="selectedStock !== null && selectedStock.code !== ''" class="stk-sticky-chart">
            <div class="stk-chart-wrap">
              <iframe
                :src="`https://stockchart.vietstock.vn/?stockcode=${selectedStock.code}`"
                width="100%"
                height="380"
                frameborder="0"
              ></iframe>
              <div v-if="isLoading" class="stk-loading">
                <div class="stk-spinner"></div>
              </div>
            </div>

            <!-- Price Alert Toggle -->
            <div v-if="selectedStock && selectedStock.code" class="stk-alert-toggle">
              <button class="stk-alert-toggle__btn" @click="showPriceAlert = !showPriceAlert">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                Price Alert
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'stk-chevron--open': showPriceAlert }"><polyline points="6 9 12 15 18 9"/></svg>
              </button>
              <div v-show="showPriceAlert" class="stk-alert-content">
                <PriceAlertWidget
                  :symbol="selectedStock.code"
                  assetType="stock"
                />
              </div>
            </div>
          </div>

          <!-- Potential Symbols Section -->
          <div class="stk-panel">
            <div class="stk-section stk-section--potential">
            <div class="stk-section-head">
              <h3 class="stk-section-head__title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                Potential Symbols
              </h3>
              <span v-if="potentialStocks.latest_updated" class="stk-updated">
                Updated: {{ formatDate(potentialStocks.latest_updated) }}
              </span>
            </div>

            <!-- Filters -->
            <div class="stk-filters" v-if="potentialStocks.data && potentialStocks.data.length > 0">
              <div class="stk-filter-item">
                <input
                  type="text"
                  v-model="filterTextVN"
                  placeholder="Filter symbols..."
                  class="stk-input"
                />
              </div>
              <div class="stk-filter-item">
                <select v-model="selectedSignalType" class="stk-input">
                  <option value="">All Signals</option>
                  <option value="near_52w_ath">Highest 52W</option>
                  <option value="ma9_above_ema21">MA9 >= EMA21</option>
                </select>
              </div>
            </div>

            <!-- Potential Stocks Table -->
            <div class="stk-table-wrap stk-table-wrap--scroll" v-if="filteredPotentialStocks.length > 0">
              <table class="stk-table">
                <thead>
                  <tr>
                    <th class="stk-th stk-th--chk"></th>
                    <th class="stk-th">Symbol</th>
                    <th class="stk-th stk-th--right">Volume</th>
                    <th class="stk-th stk-th--center">Signal</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="stock in filteredPotentialStocks"
                    :key="`${stock.symbol}-${stock.signal_type}`"
                    class="stk-row"
                    :class="{ 'stk-row--active': selectedStock && selectedStock.code === stock.symbol }"
                    @click="selectVnStock(stock.symbol)"
                  >
                    <td class="stk-td stk-td--chk">
                      <input type="checkbox" class="stk-checkbox" @click.stop="toggleStock(stock.symbol)" />
                    </td>
                    <td class="stk-td stk-td--symbol" :title="`View ${stock.symbol} details`">{{ stock.symbol }}</td>
                    <td class="stk-td stk-td--right stk-td--mono">{{ formatVolume(stock.volume) }}</td>
                    <td class="stk-td stk-td--center">
                      <span class="stk-signal" :class="'stk-signal--' + stock.signal_type">{{ stock.signal_label }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Actions -->
            <div class="stk-actions">
              <div v-if="potentialStocks.data && potentialStocks.data.length > 0" class="stk-actions__group">
                <button @click="exportCSV" class="stk-btn stk-btn--outline">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                  Export CSV
                </button>
                <button class="stk-btn stk-btn--secondary" @click="addToWatchList" :disabled="!isLoggedIn">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
                  Add to Watchlist
                </button>
              </div>

              <button
                v-if="!loadingPotentialStocks && !startScanning"
                @click="startScanningStocks"
                class="stk-btn stk-btn--primary stk-btn--scan"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                Start Scanning
              </button>
              <div v-else-if="loadingPotentialStocks" class="stk-loading">
                <div class="stk-spinner"></div>
              </div>
            </div>
            <p v-if="message" class="stk-message">{{ message }}</p>
          </div>
          </div>
        </div>

        <!-- ==================== GLOBAL TAB ==================== -->
        <div class="stk-panel" v-show="activeTab === 'global'">
          <div class="stk-header">
            <div class="stk-header__icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10"/><path d="M12 2a15 15 0 0 0-4 10 15 15 0 0 0 4 10"/></svg>
            </div>
            <div>
              <h2 class="stk-header__title">Global Stock Scanner</h2>
              <p class="stk-header__sub">Discover potential stocks across world markets</p>
            </div>
          </div>

          <!-- TradingView Chart -->
          <div v-if="selectedGlobalSymbol" class="stk-chart-wrap">
            <TradingViewChart :coin="selectedGlobalSymbol" />
          </div>

          <!-- Price Alert -->
          <PriceAlertWidget
            v-if="selectedGlobalSymbol"
            :symbol="selectedGlobalSymbol"
            assetType="stock"
          />

          <!-- Filters -->
          <div class="stk-filters">
            <div class="stk-filter-item" v-if="globalStocks.length > 0">
              <input type="text" v-model="filterTextGlobal" placeholder="Filter symbols..." class="stk-input" />
            </div>
            <div class="stk-filter-item" v-if="countriesList.length > 0">
              <select v-model="selectedCountry" class="stk-input">
                <option value="">All Countries</option>
                <option v-for="c in countriesList" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
          </div>

          <span v-if="globalLatestUpdated" class="stk-updated" style="display:block; text-align:right; margin-bottom:8px;">
            Updated: {{ formatDate(globalLatestUpdated) }}
          </span>

          <!-- Global Table -->
          <div class="stk-table-wrap stk-table-wrap--scroll" v-if="filteredGlobalStocks.length > 0">
            <table class="stk-table">
              <thead>
                <tr>
                  <th class="stk-th">Country</th>
                  <th class="stk-th">Symbol</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in filteredGlobalStocks"
                  :key="item.symbol"
                  class="stk-row"
                  :class="{ 'stk-row--active': selectedGlobalSymbol === item.symbol }"
                  @click="onSelectGlobal(item)"
                >
                  <td class="stk-td">{{ item.country }}</td>
                  <td class="stk-td stk-td--symbol">{{ item.symbol }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="stk-actions">
            <button
              v-if="!loadingGlobalStocks && !startScanningGlobal"
              @click="startScanningWorld"
              class="stk-btn stk-btn--primary stk-btn--scan"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              Start Scanning
            </button>
            <div v-else-if="loadingGlobalStocks" class="stk-loading">
              <div class="stk-spinner"></div>
            </div>
          </div>
          <p v-if="messageGlobal" class="stk-message">{{ messageGlobal }}</p>
        </div>

        <!-- ==================== RRG TAB ==================== -->
        <div class="stk-panel" v-show="activeTab === 'vn_rrg'">
          <div class="stk-header">
            <div class="stk-header__icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10"/><path d="M2 12h20"/></svg>
            </div>
            <div>
              <h2 class="stk-header__title">VN Stock RRG Chart</h2>
              <p class="stk-header__sub">Relative Rotation Graph for Vietnam market</p>
            </div>
          </div>
          <div class="stk-rrg-wrap">
            <img src="/vnstock_rrgchart" class="stk-rrg-img" alt="VN Stock RRG Chart" />
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
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import vSelect from 'vue3-select';
import axios from 'axios';
import TradingViewChart from './TradingViewChart.vue';
import PriceAlertWidget from './PriceAlertWidget.vue';

export default {
  name: 'StockMarket',
  components: {
    NavBar,
    AppFooter,
    vSelect,
    TradingViewChart,
    PriceAlertWidget,
  },
  props: {
    searchText: String,
  },
  emits: ['update:searchText', 'update:selectedStock'],
  setup(props, { emit }) {
    // Tabs
    const activeTab = ref('vn');
    const vnChartRef = ref(null);
    const showPriceAlert = ref(false);

    const isMenuOpen = ref(false);
    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value;
    };
    const userInfo = ref(null);
    const selectedStock = ref(null);
    const stocks = ref([]);
    const companyName = ref(null);
    const currentPrice = ref(null);
    const fiPrice = ref(null); // Fundamental Index price
    const dcfPrice = ref(null); // DCF price
    const averagePrice = ref(null); // Average price
    const potentialStocks = ref({}); // VN potential symbols
    const loadingPotentialStocks = ref(false);
    const startScanning = ref(false);
    const selectedStocks = ref([]); // Store selected stocks and initialize as an empty array
    const message = ref(''); // VN message
    const isLoading = ref(false);
    const filterTextVN = ref('');
    const selectedSignalType = ref('');

    // Global potential symbols
    const globalStocks = ref([]); // [{ symbol, country }]
    const globalLatestUpdated = ref(null);
    const loadingGlobalStocks = ref(false);
    const startScanningGlobal = ref(false);
    const messageGlobal = ref('');
    const filterTextGlobal = ref('');
  const selectedGlobalSymbol = ref('');
    const selectedCountry = ref('');
    const countriesList = computed(() => {
      const set = new Set((globalStocks.value || []).map(i => i.country).filter(Boolean));
      return Array.from(set).sort();
    });

    const filteredPotentialStocks = computed(() => {
      const filtered = (potentialStocks.value.data || []).filter(stock => {
        const matchesText = !filterTextVN.value || stock.symbol.toLowerCase().includes(filterTextVN.value.toLowerCase());
        const matchesSignal = !selectedSignalType.value || stock.signal_type === selectedSignalType.value;
        return matchesText && matchesSignal;
      });

      return filtered.sort((a, b) => Number(b.volume || 0) - Number(a.volume || 0));
    });

    const filteredGlobalStocks = computed(() => {
      const q = (filterTextGlobal.value || '').toLowerCase();
      const country = selectedCountry.value;
      return globalStocks.value.filter(it => {
        const matchText = !q || (it.symbol || '').toLowerCase().includes(q);
        const matchCountry = !country || it.country === country;
        return matchText && matchCountry;
      });
    });

    onMounted(async () => {
      window.addEventListener('keydown', handleArrowNavigation);
      const response = await fetch('https://api-finfo.vndirect.com.vn/v4/stocks?q=type:STOCK~status:LISTED&fields=code&size=3000');
      const data = await response.json();
      stocks.value = data.data;
      emit('update:stocks', stocks.value);
      fetchStocks();
    });

    onUnmounted(() => {
      window.removeEventListener('keydown', handleArrowNavigation);
    });

    const updateSelectedStock = (newStock) => {
      selectedStock.value = newStock ? newStock : null;
    }

    const updateStocks = (newStocks) => {
      stocks.value = newStocks;
    }

    const startScanningStocks = () => {
      startScanning.value = true;
      fetchPotentialStocks();
    }

    const startScanningWorld = () => {
      startScanningGlobal.value = true;
      messageGlobal.value = '';
      fetchPotentialWorldSymbols();
    }

    const selectVnStock = (symbol, shouldScroll = true) => {
      selectedStock.value = { code: symbol };
      if (!shouldScroll) {
        return;
      }
      setTimeout(() => {
        if (vnChartRef.value) {
          const el = vnChartRef.value;
          const y = el.getBoundingClientRect().top + window.scrollY - 120;
          window.scrollTo({ top: y, behavior: 'smooth' });
        }
      }, 100);
    };

    const onSelectGlobal = (item) => {
      selectedGlobalSymbol.value = item.symbol;
    }

    const isTypingTarget = (target) => {
      if (!target) {
        return false;
      }
      const tagName = (target.tagName || '').toLowerCase();
      return tagName === 'input' || tagName === 'textarea' || tagName === 'select' || target.isContentEditable;
    };

    const moveVnSelection = (direction) => {
      const rows = filteredPotentialStocks.value || [];
      if (!rows.length) {
        return;
      }

      const currentSymbol = selectedStock.value?.code;
      const currentIndex = rows.findIndex((row) => row.symbol === currentSymbol);
      const baseIndex = currentIndex === -1
        ? (direction > 0 ? -1 : 0)
        : currentIndex;
      const nextIndex = (baseIndex + direction + rows.length) % rows.length;
      const nextSymbol = rows[nextIndex]?.symbol;

      if (nextSymbol) {
        selectVnStock(nextSymbol, false);
      }
    };

    const moveGlobalSelection = (direction) => {
      const rows = filteredGlobalStocks.value || [];
      if (!rows.length) {
        return;
      }

      const currentIndex = rows.findIndex((row) => row.symbol === selectedGlobalSymbol.value);
      const baseIndex = currentIndex === -1
        ? (direction > 0 ? -1 : 0)
        : currentIndex;
      const nextIndex = (baseIndex + direction + rows.length) % rows.length;
      const nextItem = rows[nextIndex];

      if (nextItem) {
        onSelectGlobal(nextItem);
      }
    };

    const handleArrowNavigation = (event) => {
      if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') {
        return;
      }
      if (isTypingTarget(event.target)) {
        return;
      }

      const direction = event.key === 'ArrowDown' ? 1 : -1;

      if (activeTab.value === 'vn') {
        moveVnSelection(direction);
        event.preventDefault();
      } else if (activeTab.value === 'global') {
        moveGlobalSelection(direction);
        event.preventDefault();
      }
    };

    watch(selectedStock, (newStock) => {
      if (newStock) {
        fetchCompanyInfo(newStock.code);
        evaluatePrice(newStock.code);
      } else {
        // Clear previous stock data when no stock is selected
        companyName.value = null;
        currentPrice.value = null;
        fiPrice.value = null;
        dcfPrice.value = null;
        averagePrice.value = null;
      }
    });
    const addToWatchList = async () => {
      if (selectedStocks.value.length === 0) {
        message.value = 'No stocks selected.';
        return;
      }

      const userInfo = JSON.parse(localStorage.getItem('userInfo'));

      // Disable the button and show an alert if not logged in
      if (!userInfo || !userInfo.custodyCode) {
        alert('You need to log in to use this feature.'); // More prominent message
        return; // Stop execution
      }

      try {
        // Construct the data to send, including entry_price for each stock
        const stocksData = [];
        if (potentialStocks.value && potentialStocks.value.data) {
          for (const symbol of selectedStocks.value) {
            const stockData = potentialStocks.value.data.find((stock) => stock.symbol === symbol);
            if (stockData) {
              stocksData.push({
                symbol: stockData.symbol,
                entry_price: stockData.highest_price,
              });
            }
          }
        }

        const requestData = {
          user_id: userInfo.custodyCode,
          stocks: stocksData, // Send an array of objects with symbol and entry_price
          operator: 'Add',
        };

        const response = await axios.post('/userTrade', requestData);

        if (response.status === 200) {
          message.value = 'Stocks added to watch list successfully!';
          alert("Stocks added to watch list successfully!");
          selectedStocks.value = []; // Clear the selected stocks array
        } else {
          message.value = `Failed to add stocks: ${response.status} - ${response.data}`;
        }
      } catch (error) {
        message.value = `Error: ${error.message}`;
        console.error('API error:', error); // Improved error handling
      }
    };

    const isLoggedIn = computed(() => {
      try {
        const userInfo = JSON.parse(localStorage.getItem('userInfo'));
        const loggedIn = userInfo && userInfo.custodyCode;
        return loggedIn;
      } catch (error) {
        console.error('Error parsing userInfo:', error);
        return false; // Return false if parsing fails
      }
    });

    const toggleStock = (symbol) => {
      const index = selectedStocks.value.indexOf(symbol);
      if (index > -1) {
        selectedStocks.value.splice(index, 1); // Remove if exists
      } else {
        selectedStocks.value.push(symbol); // Add if doesn't exist
      }
    };

    const onStockSelected = (value) => {
      emit('update:selectedStock', value);
    };


    const filterOptions = (options, search) => {
      if (!search) {
        return options
      }
      return options.filter((option) =>
        option.code.toLowerCase().includes(search.toLowerCase())
      )
    }

    const fetchCompanyInfo = async (stockCode) => {
      isLoading.value = true;
      try {
        const response = await fetch(`https://services.entrade.com.vn/dnse-financial-product/securities/${stockCode}`);
        const data = await response.json();
        companyName.value = data.issuer || 'N/A';
        currentPrice.value = data.basicPrice || null;
      } catch (error) {
        console.error('Error fetching company info:', error);
        companyName.value = 'Error fetching data';
      } finally {
        isLoading.value = false;
      }
    };

    const evaluatePrice = async (ticket) => {
      isLoading.value = true;
      try {
        const res = await fetch(`/tcanalysis/v1/evaluation/${ticket}/evaluation`);
        if (res.status === 200) {
          const json_body = await res.json();

          // Fundamental Index method
          const pe = json_body.industry?.pe;
          const eps = json_body.eps;
          const pb = json_body.industry?.pb;
          const bvps = json_body.bvps;
          const evebitda = json_body.industry?.evebitda;
          const ebitda = json_body.ebitda;

          fiPrice.value = (pe && eps && pb && bvps && evebitda && ebitda) ? Math.round(((pe * eps) + (pb * bvps) + (evebitda * ebitda)) / 3) : null;

          // DCF method
          const enterpriceValue = json_body.enterpriseValue;
          const cash = json_body.cash;
          const shortTermDebt = json_body.shortTermDebt;
          const longTermDebt = json_body.longTermDebt;
          const minorityInterest = json_body.minorityInterest;
          const cap_value = enterpriceValue + cash + shortTermDebt + longTermDebt + minorityInterest;
          const shareOutstanding = json_body.shareOutstanding;

          dcfPrice.value = (cap_value && shareOutstanding) ? Math.round(cap_value / shareOutstanding) : null;

          // Average both Fundamental Index and DCF method
          averagePrice.value = (fiPrice.value != null && dcfPrice.value != null) ? Math.round((fiPrice.value + dcfPrice.value) / 2) : null;
        }
      }
      catch (error) {
        console.error('Error fetching evaluation data:', error);
      } finally {
        isLoading.value = false;
      }
    }

    const fetchPotentialStocks = async () => {
      loadingPotentialStocks.value = true;
      isLoading.value = true;
      message.value = '';
      try {
        const response = await fetch('/getPotentialSymbols');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        potentialStocks.value = data; // Assign directly
        
        // Show message if no data
        if (!data.data || data.data.length === 0) {
          message.value = 'No potential stocks available at the moment.';
        } else {
          message.value = `Found ${data.data.length} potential stocks.`;
        }
      } catch (error) {
        console.error('Error fetching potential stocks:', error);
        potentialStocks.value = { data: [] }; // Clear the list on error
        message.value = 'Failed to load potential stocks. Please try again later.';
      } finally {
        loadingPotentialStocks.value = false;
        isLoading.value = false;
      }
    };

    // Global: fetch via proxy /world
    const fetchPotentialWorldSymbols = async () => {
      loadingGlobalStocks.value = true;
      messageGlobal.value = '';
      try {
        const res = await fetch('/world/getPotentialWorldSymbols');
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const json = await res.json();
        const items = Array.isArray(json) ? json : (json.data || []);
        globalStocks.value = items.map(it => ({ symbol: it.symbol, country: it.country }));
        globalLatestUpdated.value = json.latest_updated || null;
        
        if (globalStocks.value.length === 0) {
          messageGlobal.value = 'No global symbols available at the moment.';
        } else {
          messageGlobal.value = `Found ${globalStocks.value.length} global symbols.`;
        }
      } catch (e) {
        console.error('Error fetching global symbols:', e);
        globalStocks.value = [];
        messageGlobal.value = 'Failed to load global symbols. Please try again later.';
      } finally {
        loadingGlobalStocks.value = false;
      }
    };

    const formatDate = (dateString) => {
      const date = new Date(dateString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      const seconds = String(date.getSeconds()).padStart(2, '0');

      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    }

    const exportCSV = () => {
      if (!filteredPotentialStocks.value.length) {
        return;
      }

      const rows = filteredPotentialStocks.value.map(stock => `${stock.symbol},${stock.signal_label},${stock.volume ?? 0},${stock.highest_price},${stock.lowest_price}`);
      const csvContent = "data:text/csv;charset=utf-8," + "symbol,signal,volume,highest_price,lowest_price\n" + rows.join("\n");
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", "potential_stocks.csv");
      document.body.appendChild(link); // Required for Firefox

      link.click(); // This will download the data file named "potential_stocks.csv".

      document.body.removeChild(link);
    };

    const fetchStocks = async () => {
      const response = await fetch('https://api-finfo.vndirect.com.vn/v4/stocks?q=type:STOCK~status:LISTED&fields=code&size=3000');
      const data = await response.json();
      stocks.value = data.data;
    };

    return {
      activeTab,
      vnChartRef,
      showPriceAlert,
      selectVnStock,
      selectedStock,
      stocks,
      onStockSelected,
      filterOptions,
      companyName,
      currentPrice,
      fiPrice,
      dcfPrice,
      averagePrice,
      formatNumber,
      formatVolume,
      potentialStocks,
      updateSelectedStock,
      updateStocks,
      loadingPotentialStocks,
      exportCSV,
      startScanningStocks,
      startScanningWorld,
  onSelectGlobal,
      addToWatchList,
      formatDate,
      toggleStock,
      isLoggedIn,
      isLoading,
      toggleMenu,
      isMenuOpen,
      userInfo,
      // VN tab state
      filterTextVN,
      selectedSignalType,
      filteredPotentialStocks,
      message,
      // Global tab state
      globalStocks,
      globalLatestUpdated,
      loadingGlobalStocks,
      startScanningGlobal,
      messageGlobal,
      filterTextGlobal,
      filteredGlobalStocks,
      selectedGlobalSymbol,
      selectedCountry,
      countriesList,
    };
  },
};

const formatNumber = (number) => {
  if (number === null || number === undefined) {
    return 'N/A';
  }
  return number.toLocaleString() + ' VND';
}

const formatVolume = (volume) => {
  if (volume === null || volume === undefined) {
    return '0';
  }
  return Number(volume).toLocaleString();
}
</script>

<style scoped>
/* ============================== */
/*  STOCK PAGE – Modern Dark UI   */
/* ============================== */

.stk-page {
  background: #f0f2f5;
  padding: 20px 0 40px;
}

.stk-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
}

/* ---------- TABS ---------- */
.stk-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 20px;
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}
.stk-tabs::-webkit-scrollbar { display: none; }

.stk-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border: none;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 600;
  color: #64748b;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.stk-tab:hover {
  color: #334155;
  background: #e8edf3;
}
.stk-tab--active {
  color: #fff !important;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
  box-shadow: 0 4px 12px rgba(30,41,59,0.3);
}
.stk-tab svg { flex-shrink: 0; }

/* ---------- PANEL ---------- */
.stk-panel {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

/* ---------- HEADER ---------- */
.stk-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 22px 24px;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  color: #fff;
}
.stk-header__icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255,255,255,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stk-header__title {
  font-size: 1.2rem;
  font-weight: 700;
  margin: 0;
  line-height: 1.3;
}
.stk-header__sub {
  font-size: 0.82rem;
  color: rgba(255,255,255,0.6);
  margin: 2px 0 0;
}

/* ---------- SECTIONS ---------- */
.stk-section {
  padding: 20px 24px;
}
.stk-section--potential {
  border-top: 1px solid #e2e8f0;
}
.stk-label {
  display: block;
  font-size: 0.82rem;
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

/* ---------- SECTION HEAD ---------- */
.stk-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}
.stk-section-head__title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}
.stk-updated {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
}

/* ---------- STOCK INFO GRID ---------- */
.stk-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
  padding: 0 24px 20px;
}
.stk-info-card {
  background: #f8fafc;
  border-radius: 10px;
  padding: 14px 16px;
  border: 1px solid #e2e8f0;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.stk-info-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.stk-info-card--accent {
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  border-color: #93c5fd;
}
.stk-info-card--highlight {
  background: linear-gradient(135deg, #fefce8, #fef9c3);
  border-color: #fbbf24;
}
.stk-info-card__label {
  display: block;
  font-size: 0.72rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  margin-bottom: 4px;
}
.stk-info-card__value {
  display: block;
  font-size: 0.95rem;
  font-weight: 700;
  color: #1e293b;
  word-break: break-word;
}

/* ---------- CHART (sticky) ---------- */
.stk-sticky-chart {
  position: sticky;
  top: 60px;
  z-index: 20;
  background: #f0f2f5;
  padding: 12px 0;
  margin-bottom: 12px;
}
.stk-chart-wrap {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  background: #fff;
}
.stk-chart-wrap iframe {
  display: block;
  border: none;
}

/* ---------- PRICE ALERT TOGGLE ---------- */
.stk-alert-toggle {
  margin-top: 10px;
}
.stk-alert-toggle__btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
  color: #475569;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.stk-alert-toggle__btn:hover {
  background: #eff6ff;
  border-color: #93c5fd;
  color: #1e40af;
}
.stk-alert-toggle__btn svg:last-child {
  transition: transform 0.2s ease;
}
.stk-chevron--open {
  transform: rotate(180deg);
}
.stk-alert-content {
  margin-top: 8px;
}

/* ---------- FILTERS ---------- */
.stk-filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.stk-filter-item {
  flex: 1 1 200px;
}
.stk-input {
  width: 100%;
  padding: 9px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #1e293b;
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
}
.stk-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
}

/* ---------- TABLE ---------- */
.stk-table-wrap {
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}
.stk-table-wrap--scroll {
  max-height: 480px;
  overflow-y: auto;
}
.stk-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.stk-th {
  padding: 10px 14px;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #64748b;
  background: #f8fafc;
  border-bottom: 2px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 2;
}
.stk-th--right { text-align: right; }
.stk-th--center { text-align: center; }
.stk-th--chk { width: 36px; text-align: center; }

.stk-row {
  cursor: pointer;
  transition: background 0.15s ease;
}
.stk-row:hover {
  background: #f1f5f9;
}
.stk-row--active {
  background: #eff6ff !important;
}
.stk-td {
  padding: 10px 14px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}
.stk-td--chk { width: 36px; text-align: center; }
.stk-td--right { text-align: right; }
.stk-td--center { text-align: center; }
.stk-td--symbol {
  font-weight: 700;
  color: #1e40af;
}
.stk-td--mono {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.82rem;
}

.stk-checkbox {
  width: 16px;
  height: 16px;
  accent-color: #3b82f6;
  cursor: pointer;
}

/* ---------- SIGNALS ---------- */
.stk-signal {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}
.stk-signal--near_52w_ath {
  background: #dbeafe;
  color: #1e40af;
}
.stk-signal--ma9_above_ema21 {
  background: #dcfce7;
  color: #166534;
}

/* ---------- BUTTONS ---------- */
.stk-actions {
  padding: 16px 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
}
.stk-actions__group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.stk-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  border: none;
  border-radius: 8px;
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}
.stk-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.stk-btn--primary {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  box-shadow: 0 2px 8px rgba(59,130,246,0.3);
}
.stk-btn--primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  box-shadow: 0 4px 14px rgba(37,99,235,0.4);
  transform: translateY(-1px);
}
.stk-btn--secondary {
  background: #334155;
  color: #fff;
}
.stk-btn--secondary:hover:not(:disabled) {
  background: #1e293b;
}
.stk-btn--outline {
  background: #fff;
  color: #334155;
  border: 1px solid #cbd5e1;
}
.stk-btn--outline:hover:not(:disabled) {
  background: #f1f5f9;
  border-color: #94a3b8;
}
.stk-btn--scan {
  min-width: 180px;
  justify-content: center;
}

/* ---------- LOADING / SPINNER ---------- */
.stk-loading {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}
.stk-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: stk-spin 0.7s linear infinite;
}
@keyframes stk-spin {
  to { transform: rotate(360deg); }
}

/* ---------- MESSAGE ---------- */
.stk-message {
  text-align: center;
  font-size: 0.85rem;
  color: #64748b;
  padding: 10px 0;
  margin: 0;
}

/* ---------- RRG ---------- */
.stk-rrg-wrap {
  padding: 24px;
  text-align: center;
}
.stk-rrg-img {
  max-width: 100%;
  height: auto;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

/* ---------- v-select override ---------- */
.stk-select :deep(.vs__dropdown-toggle) {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 6px 10px;
  min-height: 40px;
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.stk-select :deep(.vs__dropdown-toggle:focus-within) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
}
.stk-select :deep(.vs__search) {
  font-size: 0.88rem;
  color: #1e293b;
}
.stk-select :deep(.vs__selected) {
  font-size: 0.88rem;
  font-weight: 600;
  color: #1e293b;
}
.stk-select :deep(.vs__dropdown-menu) {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
  max-height: 280px;
}
.stk-select :deep(.vs__dropdown-option--highlight) {
  background: #eff6ff;
  color: #1e40af;
}

/* ---------- RESPONSIVE ---------- */
@media (max-width: 640px) {
  .stk-container { padding: 0 10px; }
  .stk-header { padding: 16px; }
  .stk-section { padding: 16px; }
  .stk-sticky-chart {
    padding: 0 12px 10px;
  }
  .stk-tab {
    padding: 8px 14px;
    font-size: 0.82rem;
  }
  .stk-filters {
    flex-direction: column;
  }
  .stk-table-wrap--scroll {
    max-height: 400px;
  }
}
</style>
