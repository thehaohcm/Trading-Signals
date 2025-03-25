<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />

    <div class="container mt-4 flex-grow-1">
      <div class="row justify-content-center">
        <!-- <div class="col-md-8"> -->
        <div class="card">
          <div class="card-header bg-secondary text-white">
            <h5 class="mb-0">Vietnam Stock Evaluator</h5>
          </div>
          <div class="card-body">
            <p class="card-text" style="margin-top:0px; font-weight: bold;">Choose a stock symbol:</p>
            <v-select v-model="selectedStock" :options="stocks" label="code" @input="onStockSelected"
              :filter-options="filterOptions"></v-select>
            <hr />
            <table>
              <tbody>
                <tr>
                  <td class="tr-stockvn">Company Name:</td>
                  <td>{{ companyName ?? 'N/A' }}</td>
                </tr>
                <tr>
                  <td class="tr-stockvn">Current Price:</td>
                  <td>{{ formatNumber(currentPrice) }}</td>
                </tr>
                <tr>
                  <td class="tr-stockvn">FI Price:</td>
                  <td>{{ formatNumber(fiPrice) }}</td>
                </tr>
                <tr>
                  <td class="tr-stockvn">DCF Price:</td>
                  <td>{{ formatNumber(dcfPrice) }}</td>
                </tr>
                <tr>
                  <td class="tr-stockvn">Avg. Predict Price:</td>
                  <td>{{ formatNumber(averagePrice) }}</td>
                </tr>
              </tbody>
            </table>
            <div v-if="selectedStock !== null && selectedStock.code !== ''" style="position: sticky; top: 0; background-color: #fff; z-index: 100;">
              <iframe :src="`https://stockchart.vietstock.vn/?stockcode=${selectedStock.code}`" width="100%"
                height="500px"></iframe>
              <div v-if="isLoading" class="d-flex justify-content-center">
                <div class="spinner"></div>
              </div>
            </div>
            <hr />
            <h5 class="mb-0">Potential symbols</h5>
            <div class="card-body">
              <div class="mb-2" v-if="potentialStocks.data && potentialStocks.data.length > 0">
                <input type="text" v-model="filterText" placeholder="Filter symbols..." class="form-control" />
              </div>
              <div v-if="potentialStocks.latest_updated" style="text-align: right; font-weight: bold;">
                <strong>Last Updated:</strong> {{ formatDate(potentialStocks.latest_updated) }}
              </div>
              <table class="table table-striped">
                <tbody>
                  <tr v-for="stock in filteredPotentialStocks" :key="stock.symbol"
                    @click="$nextTick(() => { selectedStock = { code: stock.symbol }; });" style="cursor: pointer;"
                    :class="{ 'highlighted-row': selectedStock && selectedStock.code === stock.symbol }">
                    <td style="text-align: left; width: 1%;">
                      <input type="checkbox" @click="toggleStock(stock.symbol)">
                    </td>
                    <td :title="`Click to see more the ${stock.symbol} info...`">{{ stock.symbol }}</td>
                  </tr>
                </tbody>
              </table>

              <div v-if="potentialStocks.data && potentialStocks.data.length > 0"
                class="d-flex justify-content-center gap-2 my-2">
                <button @click="exportCSV" class="btn btn-primary">Export CSV file</button>
                <button class="btn btn-secondary" @click="addToWatchList" :disabled="!isLoggedIn">Add to my watch
                  list</button>
              </div>
              <button v-if="!loadingPotentialStocks && !startScanning" @click="startScanningStocks"
                class="btn btn-success">Start to
                scan...</button>
              <p v-if="message" class="text-center">{{ message }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
  <AppFooter />
</template>

<script>
import NavBar from './NavBar.vue';
import AppFooter from './AppFooter.vue';
import { ref, onMounted, watch, computed } from 'vue';
import vSelect from 'vue3-select';
import axios from 'axios';

export default {
  name: 'StockVn',
  components: {
    NavBar,
    AppFooter,
    vSelect,
  },
  props: {
    searchText: String,
  },
  emits: ['update:searchText', 'update:selectedStock'],
  setup(props, { emit }) {
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
    const potentialStocks = ref({}); // Changed to object
    const loadingPotentialStocks = ref(false);
    const startScanning = ref(false);
    const selectedStocks = ref([]); // Store selected stocks and initialize as an empty array
    const message = ref(''); // Store success/error message
    const isLoading = ref(false);
    const filterText = ref(''); // Add filterText

    const filteredPotentialStocks = computed(() => {
      if (!filterText.value) {
        return potentialStocks.value.data || [];
      }
      return (potentialStocks.value.data || []).filter(stock =>
        stock.symbol.toLowerCase().includes(filterText.value.toLowerCase())
      );
    });

    onMounted(async () => {
      const response = await fetch('https://api-finfo.vndirect.com.vn/v4/stocks?q=type:STOCK~status:LISTED&fields=code&size=3000');
      const data = await response.json();
      stocks.value = data.data;
      emit('update:stocks', stocks.value);
      fetchStocks();
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
      try {
        const response = await fetch('/getPotentialSymbols');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        potentialStocks.value = data; // Assign directly
      } catch (error) {
        console.error('Error fetching potential stocks:', error);
        potentialStocks.value = {}; // Clear the list on error
      } finally {
        loadingPotentialStocks.value = false;
        isLoading.value = false;
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
      if (potentialStocks.value.length === 0) {
        return;
      }

      const csvContent = "data:text/csv;charset=utf-8," + "potential stock symbol\n" + potentialStocks.value.join("\n");
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
      potentialStocks,
      updateSelectedStock,
      updateStocks,
      loadingPotentialStocks,
      exportCSV,
      startScanningStocks,
      addToWatchList,
      formatDate,
      toggleStock,
      isLoggedIn,
      isLoading,
      toggleMenu,
      isMenuOpen,
      userInfo,
      filterText, // Return filterText
      filteredPotentialStocks, // Return filteredPotentialStocks
    };
  },
};

const formatNumber = (number) => {
  if (number === null || number === undefined) {
    return 'N/A';
  }
  return number.toLocaleString() + ' VND';
}
</script>

<style scoped>
/* Add component-specific styles here */
.tr-stockvn {
  font-weight: bold;
  text-align: left;
}

td:nth-child(1) {
  text-align: left;
}

.highlighted-row {
  background-color: #f0f0f0; /* Light gray background */
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #09f;
  animation: spin 1s ease infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}
</style>
