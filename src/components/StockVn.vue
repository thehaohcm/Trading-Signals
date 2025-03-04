 <template>
  <div>
    <v-select v-model="selectedStock" :options="stocks" label="code" @input="onStockSelected" :filter-options="filterOptions"></v-select>
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
    <div>
      <StockChart v-if="selectedStock!==null && selectedStock.code!==''" :ticker="selectedStock.code" />
    </div>
  </div>
  <hr/>
    <table class="table table-striped">
      <thead>
          <tr>
              <th>Potential symbols</th>
          </tr>
      </thead>
      <tbody>
        <tr v-for="stock in potentialStocks" :key="stock" @click="selectedStock = stocks.find(s => s.code === stock);" style="cursor: pointer;">
          <td :title="`Click to see more the ${stock} info...`">{{ stock }}</td>
        </tr>
        <tr class="table-danger" v-if="loadingPotentialStocks" style="cursor: pointer;" @click="stopFetchingPotentialStocks">
          <td colspan="1" :title="`Evaluating...Click here to stop`">Evaluating...Click here to stop</td>
        </tr>
        <tr class="table-info" v-if="!loadingPotentialStocks && !startScanning" style="cursor: pointer;" @click="startScanningStocks">
          <td colspan="1" :title="`Click here to start scanning`">Start to scan...</td>
        </tr>
      </tbody>
    </table>

  <button v-if="potentialStocks.length > 0" @click="exportCSV">Export CSV file</button>
</template>

<script>
import { ref, onMounted, watch } from 'vue';
import vSelect from 'vue3-select';
import StockChart from './StockChart.vue';

export default {
  name: 'StockVn',
  components: {
    vSelect,
    StockChart
  },
  props: {
    searchText: String,
  },
  emits: ['update:searchText', 'update:selectedStock'],
  setup(props, { emit }) {
    const selectedStock = ref(null);
    const stocks = ref([]);
    const companyName = ref('');
    const currentPrice = ref(null);
    const fiPrice = ref(null); // Fundamental Index price
    const dcfPrice = ref(null); // DCF price
    const averagePrice = ref(null); // Average price
    const potentialStocks = ref([]);
    const loadingPotentialStocks = ref(false);
    const stopFetching = ref(false);
    let controller = null;
    const startScanning = ref(false);

    onMounted(async () => {
      const response = await fetch('https://api-finfo.vndirect.com.vn/v4/stocks?q=type:STOCK~status:LISTED&fields=code&size=3000');
      const data = await response.json();
      stocks.value = data.data;
      emit('update:stocks', stocks.value);
      // fetchPotentialStocks(); // Don't fetch on mount
    });

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
        companyName.value = '';
        currentPrice.value = null;
        fiPrice.value = null;
        dcfPrice.value = null;
        averagePrice.value = null;
      }
    });

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
      try {
        const response = await fetch(`https://services.entrade.com.vn/dnse-financial-product/securities/${stockCode}`);
        const data = await response.json();
        console.log("fetchCompanyInfo data:", data);
        companyName.value = data.issuer || 'N/A';
        currentPrice.value = data.basicPrice || null;
      } catch (error) {
        console.error('Error fetching company info:', error);
        companyName.value = 'Error fetching data';
      }
    };

    const evaluatePrice = async (ticket) => {
      try {
        const res = await fetch(`/tcanalysis/v1/evaluation/${ticket}/evaluation`);
        if (res.status === 200) {
          const json_body = await res.json();
          console.log("evaluatePrice data:", json_body);

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

          dcfPrice.value = (cap_value && shareOutstanding) ?  Math.round(cap_value / shareOutstanding) : null;

          // Average both Fundamental Index and DCF method
          averagePrice.value = (fiPrice.value != null && dcfPrice.value != null) ? Math.round((fiPrice.value + dcfPrice.value) / 2) : null;
        }
      }
      catch (error){
        console.error('Error fetching evaluation data:', error);
      }
    }

    const fetchPotentialStocks = async () => {
      loadingPotentialStocks.value = true;
      stopFetching.value = false;
      controller = new AbortController(); // Create a new AbortController each time
      const { signal } = controller;

      for (const stock of stocks.value) {
        if (stopFetching.value) {
          break;
        }
        try {
          const response = await fetch(`/tcanalysis/v1/ticker/${stock.code}/price-volatility`, { signal }); // Pass the signal
          await new Promise(resolve => setTimeout(resolve, 1000));
          const data = await response.json();
          if (data.highestPricePercent >= -0.05) {
            const [avgVol9, avgPrice9] = await getAvgVolumePrice(stock.code, 9);
            if (avgVol9 > 500000) {
              const [, avgPrice20] = await getAvgVolumePrice(stock.code, 20);
              await new Promise(resolve => setTimeout(resolve, 1000));
              const [, avgPrice50] = await getAvgVolumePrice(stock.code, 50);
              await new Promise(resolve => setTimeout(resolve, 1000));
              if (avgPrice9 > avgPrice20 || avgPrice20 > avgPrice50) {
                potentialStocks.value.push(stock.code);
              }
            }
          }
        } catch (error) {
          if (error.name === 'AbortError') {
            console.log('Fetch aborted for', stock.code);
            loadingPotentialStocks.value = false;
          } else {
            console.error(`Error fetching price volatility for ${stock.code}:`, error);
          }
        }
        await new Promise(resolve => setTimeout(resolve, 1000)); // 1s delay
      }
      loadingPotentialStocks.value = false;
    };

    const getAvgVolumePrice = async (ticket, numberOfDay) => {
      const currentUnixTs = String(Math.floor(Date.now() / 1000));
      const url = `/stock-insight/v2/stock/bars-long-term?ticker=${ticket}&type=stock&resolution=D&to=${currentUnixTs}&countBack=${numberOfDay}`;
        try {
            const res = await fetch(url);
            if (res.ok) {
                const jsonBody = await res.json();
                const dataList = jsonBody.data;
                if (!dataList) {
                    console.error("No data found for", ticket);
                    return [null, null];
                }
                let sumVol = 0;
                let sumPrice = 0;
                for (const data of dataList) {
                    const vol = data.volume;
                    sumVol += vol;
                    sumPrice += data.close;
                }
                const avgVol = Math.floor(sumVol / dataList.length);
                const avgPrice = Math.floor(sumPrice / dataList.length);
                return [avgVol, avgPrice];
            } else {
                console.error("Error fetching data:", res.status);
                return [null, null];
            }
        }
        catch (e) {
            console.error("exception", e);
            return [null, null];
        }
    }

    const stopFetchingPotentialStocks = () => {
      stopFetching.value = true;
      controller.abort(); // Abort the fetch requests
      stopFetching.value = false;
      loadingPotentialStocks.value = false;
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
      loadingPotentialStocks,
      stopFetchingPotentialStocks,
      exportCSV,
      startScanningStocks
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
.tr-stockvn{
  font-weight: bold;
  text-align: left;
}

td:nth-child(2) {
  padding-left: 50px;
  text-align: left;
}

</style>


