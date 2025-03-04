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
      <StockChart v-if="selectedStock!==null" :ticker="selectedStock ? selectedStock.code : 'HAH'" />
    </div>
  </div>
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

    onMounted(async () => {
      const response = await fetch('https://api-finfo.vndirect.com.vn/v4/stocks?q=type:STOCK~status:LISTED&fields=code&size=3000');
      const data = await response.json();
      stocks.value = data.data;
      emit('update:stocks', stocks.value);
    });

    watch(selectedStock, (newStock) => {
      if (newStock) {
        emit('update:searchText', newStock.code);
        fetchCompanyInfo(newStock.code);
        evaluatePrice(newStock.code);
      }
    });

   const onStockSelected = (value) => {
      console.log("onStockSelected", value);
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
      formatNumber
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
