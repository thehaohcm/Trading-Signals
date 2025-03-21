<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <NavBar />

    <div class="my-portfolio container mt-4 flex-grow-1">
      <h1 class="mb-4">My Portfolio</h1>

      <div class="mb-3">
        <label for="account-select" class="form-label">Select Account:</label>
        <select id="account-select" v-model="selectedAccount" class="form-select">
          <option v-for="account in accounts" :key="account.id" :value="account.id">
            {{ account.id }} - {{ account.name }}
          </option>
        </select>
      </div>

      <!-- Tabs -->
      <div class="mb-3">
        <button
          v-for="tab in tabs"
          :key="tab"
          :class="['btn', 'me-2', selectedTab === tab ? 'btn-primary' : 'btn-outline-primary']"
          @click="selectedTab = tab"
        >
          {{ tab }}
        </button>
      </div>

      <div v-if="errorMessage" class="alert alert-danger">
        {{ errorMessage }}
      </div>

      <!-- Tab Content -->
      <div v-if="selectedTab === 'Balance Account'">
        <div v-if="accountBalance" class="card mb-4 shadow-sm">
          <div class="card-body">
            <h2 class="card-title text-center mb-5">Account Balance</h2>
            <div class="row">
              <div class="col-md-6">
                <div class="info-item p-2 mb-2 bg-light rounded">
                  <div class="row">
                    <div class="col-6 text-start"><strong>Net Asset Value:</strong></div>
                    <div class="col-6 text-end">{{ formatNumber(accountBalance.netAssetValue) }}</div>
                  </div>
                </div>
                <div class="info-item p-2 mb-2 bg-light rounded">
                  <div class="row">
                    <div class="col-6 text-start"><strong>Total Cash:</strong></div>
                    <div class="col-6 text-end">{{ formatNumber(accountBalance.totalCash) }}</div>
                  </div>
                </div>
                <div class="info-item p-2 mb-2 bg-light rounded">
                  <div class="row">
                    <div class="col-6 text-start"><strong>Deposit Interest:</strong></div>
                    <div class="col-6 text-end">{{ formatNumber(accountBalance.depositInterest) }}</div>
                  </div>
                </div>
                <div class="info-item p-2 mb-2 bg-light rounded">
                  <div class="row">
                    <div class="col-6 text-start"><strong>Stock Value:</strong></div>
                    <div class="col-6 text-end">{{ formatNumber(accountBalance.stockValue) }}</div>
                  </div>
                </div>
                <div class="info-item p-2 mb-2 bg-light rounded">
                  <div class="row">
                    <div class="col-6 text-start"><strong>Marginable Amount:</strong></div>
                    <div class="col-6 text-end">{{ formatNumber(accountBalance.marginableAmount) }}</div>
                  </div>
                </div>
                <div class="info-item p-2 mb-2 bg-light rounded">
                  <div class="row">
                    <div class="col-6 text-start"><strong>Total Debt:</strong></div>
                    <div class="col-6 text-end">{{ formatNumber(accountBalance.totalDebt) }}</div>
                  </div>
                </div>
              </div>
              <div class="col-md-6">
                <div class="info-item p-2 mb-2 rounded">
                  <div class="row">
                    <div class="col-6 text-start"><strong>Currency Unit:</strong></div>
                    <div class="col-6 text-end">VND</div>
                  </div>
                </div>
                <div class="info-item p-2 mb-2 bg-light rounded">
                  <div class="row">
                    <div class="col-6 text-start"><strong>Receiving Amount:</strong></div>
                    <div class="col-6 text-end">{{ formatNumber(accountBalance.receivingAmount) }}</div>
                  </div>
                </div>
                <div class="info-item p-2 mb-2 bg-light rounded">
                  <div class="row">
                    <div class="col-6 text-start"><strong>Secure Amount:</strong></div>
                    <div class="col-6 text-end">{{ formatNumber(accountBalance.secureAmount) }}</div>
                  </div>
                </div>
                <div class="info-item p-2 mb-2 bg-light rounded">
                  <div class="row">
                    <div class="col-6 text-start"><strong>Deposit Fee Amount:</strong></div>
                    <div class="col-6 text-end">{{ formatNumber(accountBalance.depositFeeAmount) }}</div>
                  </div>
                </div>
                <div class="info-item p-2 mb-2 bg-light rounded">
                  <div class="row">
                    <div class="col-6 text-start"><strong>Withdrawable Cash:</strong></div>
                    <div class="col-6 text-end">{{ formatNumber(accountBalance.withdrawableCash) }}</div>
                  </div>
                </div>
                <div class="info-item p-2 mb-2 bg-light rounded">
                  <div class="row">
                    <div class="col-6 text-start"><strong>Purchasing Power:</strong></div>
                    <div class="col-6 text-end">{{ formatNumber(accountBalance.purchasingPower) }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="balanceErrorMessage" class="alert alert-danger">
          <p>{{ balanceErrorMessage }}</p>
        </div>
      </div>

     <div v-if="isLoading" class="text-center">
       <div class="spinner"></div>
     </div>

      <div v-else-if="selectedTab === 'Deals'">
        <div v-if="deals.length > 0" class="mb-4">
          <h2 class="mb-3">Deals</h2>
          <div class="table-responsive">
            <table class="table table-striped table-hover">
              <thead class="table-light text-center">
                <tr>
                  <th>Symbol</th>
                  <th>Open Quantity</th>
                  <th>Unrealized Profit</th>
                  <th>Break Even Price</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="deal in deals" :key="deal.id">
                  <td style="font-weight: bolder;">{{ deal.symbol }}</td>
                  <td>{{ deal.openQuantity }}</td>
                  <td>{{ formatNumber(deal.unrealizedProfit) }}</td>
                  <td>{{ formatNumber(deal.breakEvenPrice) }}</td>
                  <td>
                    <div v-if="deal.openQuantity !== 0">
                      <button class="btn btn-success btn-sm me-2" @click="openOrderPopup('Buy', deal.symbol)">Buy</button>
                      <button class="btn btn-danger btn-sm" @click="openOrderPopup('Sell', deal.symbol)">Sell</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Confirmation Dialog -->
        <div v-if="showConfirmationDialog" class="confirmation-dialog"
          style="display: block; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 1000; background-color: white;">
          <div class="confirmation-dialog-content p-4 rounded shadow">
            <h2 class="mb-4">Update Portfolio</h2>
            <p>Do you need to update your portfolio to get signal?</p>
            <div class="d-grid gap-2">
              <button class="btn btn-primary" @click="confirmUpdatePortfolio">Yes</button>
              <button class="btn btn-secondary" @click="showConfirmationDialog = false">No</button>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="selectedTab === 'Exclusive Signals'">
        <div v-if="isLoading" class="text-center">
          <div class="spinner"></div>
        </div>
        <div v-if="exclusiveSignalsErrorMessage" class="alert alert-danger">
          {{ exclusiveSignalsErrorMessage }}
        </div>
        <div v-else-if="exclusiveSignals.length > 0" class="mb-4">
          <h2 class="mb-3">Exclusive Signals</h2>
          <div style="font-style: italic; text-align: right;"><strong>Currency Unit: VND</strong></div>
          <div class="table-responsive">
            <table class="table table-striped table-hover">
              <thead class="table-light text-center">
                <tr>
                  <th>Symbol</th>
                  <th>Entry Price</th>
                  <th>Avg Price</th>
                  <th>Current Price</th>
                  <th>% Changed</th>
                  <th>Signal</th>
                  <!-- Add more headers as needed based on the API response -->
                </tr>
              </thead>
              <tbody>
                <tr v-for="signal in exclusiveSignals" :key="signal.id">
                  <td>{{ signal.symbol }}</td>
                  <td>{{ formatNumber(signal.entry_price) }}</td>
                  <td>{{ signal.avg_price }}</td>
                  <td>{{ signal.current_price }}</td>
                  <td>{{ (signal.percent_change * 100).toFixed(2) + '%' }}</td>
                  <td>{{ signal.signal }}</td>
                  <!-- Add more data display as needed -->
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-else>
          <p>No exclusive signals to display.</p>
        </div>
      </div>

      <div v-else>
        <!-- Content for Orders tab -->
        <div v-if="orders.length > 0" class="mb-4">
          <h2 class="mb-3">Orders</h2>
          <div class="table-responsive">
            <table class="table table-striped table-hover">
              <thead class="table-light text-center">
                <tr>
                  <th>Order ID</th>
                  <th>Symbol</th>
                  <th>Quantity</th>
                  <th>Price</th>
                  <th>Side</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="order in orders" :key="order.orderId">
                  <td>{{ order.id }}</td>
                  <td>{{ order.symbol }}</td>
                  <td>{{ order.quantity }}</td>
                  <td>{{ formatNumber(order.price) }}</td>
                  <td>{{ order.side }}</td>
                  <td>{{ order.orderStatus }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-else>
          <p>No orders to display.</p>
        </div>
      </div>

      <!-- Order Popup -->
      <div v-if="showOrderPopup" class="order-popup"
        style="display: block; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 1000; background-color: white;">
        <div class="order-popup-content p-4 rounded shadow">
          <h2 class="mb-4">Place Order</h2>
          <div class="mb-3">
            <label for="stock-select" class="form-label">Stock Symbol:</label>
            <select id="stock-select" v-model="selectedStock" class="form-select">
              <option v-for="stock in stocks" :key="stock.code" :value="stock.code">
                {{ stock.code }}
              </option>
            </select>
          </div>
          <div class="mb-3">
            <label for="order-side" class="form-label">Order Side:</label>
            <input type="text" id="order-side" v-model="orderSide" class="form-control" readonly>
          </div>
          <div class="mb-3">
            <label for="order-type" class="form-label">Order Type:</label>
            <select id="order-type" v-model="orderType" class="form-select">
              <option value="LO">LO</option>
              <option value="MP">MP</option>
              <option value="MTL">MTL</option>
              <option value="ATO">ATO</option>
              <option value="ATC">ATC</option>
              <option value="MOK">MOK</option>
              <option value="MAK">MAK</option>
            </select>
          </div>
          <div class="mb-3">
            <label for="quantity" class="form-label">Quantity:</label>
            <input type="number" id="quantity" v-model="orderQuantity" class="form-control" step="100" min="0">
          </div>
          <div class="mb-3">
            <label for="price" class="form-label">Price:</label>
            <input type="number" id="price" v-model="orderPrice" class="form-control">
          </div>
          <div class="d-grid gap-2">
            <button class="btn btn-primary" @click="placeOrder">Apply</button>
            <button class="btn btn-secondary" @click="closeOrderPopup">Cancel</button>
          </div>
        </div>
      </div>

      <!-- OTP Authentication Popup -->
      <div v-if="showOtpPopup" class="otp-popup"
        style="display: block; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 1000; background-color: white;">
        <div class="otp-popup-content p-4 rounded shadow">
          <h2 class="mb-4">Authentication</h2>
          <div class="mb-3">
            <label for="auth-method-select" class="form-label">Authentication Method:</label>
            <select id="auth-method-select" v-model="selectedAuthMethod" class="form-select">
              <option value="smart-otp">Authenticate by Smart OTP</option>
              <option value="email">Authenticate by Email</option>
            </select>
          </div>
          <div v-if="selectedAuthMethod === 'smart-otp'" class="mb-3">
            <label class="form-label">
              Please open the Entrade X application on your phone and input the OTP here:
            </label>
            <input type="text" v-model="otpInput" class="form-control" placeholder="Enter OTP">
          </div>
          <div v-if="selectedAuthMethod === 'email'" class="mb-3">
          </div>
          <div class="d-grid gap-2">
            <button class="btn btn-primary" @click="handleOtpSubmit">OK</button>
            <button class="btn btn-secondary" @click="closeOtpPopup">Cancel</button>
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
import { useRouter } from 'vue-router';

export default {
  name: 'MyPortfolio',
  components: {
    NavBar,
    AppFooter
  },
  setup() {
    const accounts = ref([]);
    const selectedAccount = ref('');
    const accountBalance = ref(null);
    const deals = ref([]);
    const errorMessage = ref('');
    const balanceErrorMessage = ref('');
    const dealsErrorMessage = ref('');
    const isMenuOpen = ref(false);
    const userInfo = ref({}); // Initialize userInfo to an empty object
    const activeTab = ref('MyPortfolio');
    const showDropdown = ref(false);
    const router = useRouter();

    // OTP Popup variables
    const showOtpPopup = ref(false);
    const selectedAuthMethod = ref('smart-otp');
    const otpInput = ref('');
    let pendingOrder = ref(false);
    const tradingToken = ref('');

    const selectedTab = ref('Balance Account');
    const tabs = ref(['Balance Account', 'Deals', 'Orders', 'Exclusive Signals']);
    const orders = ref([]);
    const ordersErrorMessage = ref('');
    const exclusiveSignals = ref([]);
    const exclusiveSignalsErrorMessage = ref('');

   // Confirmation Dialog
    const showConfirmationDialog = ref(false);
   const isLoading = ref(false);

    const fetchExclusiveSignals = async () => {
     isLoading.value = true;
      exclusiveSignalsErrorMessage.value = '';
      exclusiveSignals.value = [];
      userInfo.value = JSON.parse(localStorage.getItem('userInfo'));
      if (!userInfo.value || !userInfo.value.custodyCode) {
        exclusiveSignalsErrorMessage.value = 'User information not available.';
        isLoading.value = false;
        logout();
        return;
      }

      try {
        const response = await fetch(`/getUserTrade?user_id=${userInfo.value.custodyCode}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        exclusiveSignals.value = data;
      } catch (error) {
        if (error.response) {
          exclusiveSignalsErrorMessage.value = `Failed to fetch exclusive signals: ${error.response.data.message || 'Unknown error'}`;
        } else {
          exclusiveSignalsErrorMessage.value = 'An error occurred while fetching exclusive signals.';
          console.error('Error fetching exclusive signals:', error);
        }
      } finally {
        isLoading.value = false;
      }
    };

    const fetchOrders = async (accountNumber) => {
     isLoading.value = true;
      ordersErrorMessage.value = '';
      const token = localStorage.getItem('token');
      if (!token) {
        ordersErrorMessage.value = 'Not authorized.';
       isLoading.value = false;
        return;
      }

      try {
        const response = await fetch(`/dnse-order-service/v2/orders?accountNo=${accountNumber}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          orders.value = data.orders;
        } else {
          orders.value = [];
          ordersErrorMessage.value = 'Failed to fetch orders.';
        }
      } catch (error) {
        orders.value = [];
        ordersErrorMessage.value = 'An error occurred while fetching orders.';
      } finally {
       isLoading.value = false;
      }
    };

    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value;
    };

    const logout = () => {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('userInfo');
      userInfo.value = null;
      isLoggedIn = false;
      router.push('/');
    }

    const openOtpPopup = () => {
      showOtpPopup.value = true;
    };

    const closeOtpPopup = () => {
      showOtpPopup.value = false;
      otpInput.value = ''; // Reset OTP input
      pendingOrder.value = false;
    };

    const handleOtpSubmit = async () => {
      if (selectedAuthMethod.value === 'smart-otp') {
        if (!otpInput.value) {
          alert('Please input the OTP');
          return;
        }

        const token = localStorage.getItem('token');
        if (!token) {
          alert('Not authorized.');
          return;
        }

        try {
          const response = await fetch('/dnse-order-service/trading-token', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'smart-otp': otpInput.value
            },
          });

          if (response.ok) {
            const data = await response.json();
            tradingToken.value = data.tradingToken; // Store the trading token

            // Check if there's a pending order
            if (pendingOrder.value) {
              finalizeOrder(); // Call finalizeOrder after successful OTP
            }

            closeOtpPopup();
          } else {
            const errorData = await response.json();
            console.error('OTP Authentication Failed:', errorData);
            alert(`Authentication failed: ${errorData.message || 'Unknown error'}`);
          }
        } catch (error) {
          console.error('Error during OTP authentication:', error);
          alert('An error occurred during authentication.');
        }
      }
    };

    const fetchAccountBalance = async (accountNumber) => {
     isLoading.value = true;
      balanceErrorMessage.value = '';
      const token = localStorage.getItem('token');
      if (!token) {
        balanceErrorMessage.value = 'Not authorized.';
       isLoading.value = false;
        return;
      }

      try {
        const response = await fetch(`/dnse-order-service/account-balances/${accountNumber}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          accountBalance.value = data;
        } else {
          accountBalance.value = null;
          balanceErrorMessage.value = 'Failed to fetch account balance.';
        }
      } catch (error) {
        accountBalance.value = null;
        balanceErrorMessage.value = 'An error occurred while fetching account balance.';
      } finally {
       isLoading.value = false;
      }
    };

    const fetchDeals = async (accountNumber) => {
     isLoading.value = true;
      dealsErrorMessage.value = '';
      const token = localStorage.getItem('token');
      if (!token) {
        dealsErrorMessage.value = 'Not authorized.';
       isLoading.value = false;
        return;
      }

      try {
        const response = await fetch(`/dnse-deal-service/deals?accountNo=${accountNumber}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          deals.value = data.deals;

          // Show confirmation dialog after fetching deals
          showConfirmationDialog.value = true;

        } else {
          dealsErrorMessage.value = 'Failed to fetch deals.';
          console.error('Failed to fetch deals. Status:', response.status, 'Response:', await response.text()); // Log the error
        }
      } catch (error) {
        dealsErrorMessage.value = 'An error occurred while fetching deals.';
        console.error('Error fetching deals:', error); // Log the error
      } finally {
       isLoading.value = false;
      }
    }

    onMounted(async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        router.push('/login');
        return;
      }

      try {
        const response = await fetch('/dnse-order-service/accounts', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          accounts.value = data.accounts;

          const defaultAccount = data.default;
          if (defaultAccount) {
            selectedAccount.value = defaultAccount.id;
            fetchAccountBalance(selectedAccount.value); // Fetch balance for default account
            fetchDeals(selectedAccount.value);
          }
        } else {
          errorMessage.value = 'Failed to fetch accounts.';
        }
      } catch (error) {
        errorMessage.value = 'An error occurred while fetching accounts.';
      }
      await fetchStocks(); // Fetch the stock list when the component is mounted

    });

    watch(selectedAccount, (newAccountNumber) => {
      if (newAccountNumber) {
        fetchAccountBalance(newAccountNumber);
        fetchDeals(newAccountNumber);
      }
    });

    watch(selectedTab, (newTab) => {
      if (newTab === 'Orders' && selectedAccount.value) {
        fetchOrders(selectedAccount.value);
      } else if (newTab === 'Exclusive Signals') {
        fetchExclusiveSignals();
      }
    });

    var isLoggedIn = computed(() => {
      return !!localStorage.getItem('token');
    });

    const formatNumber = (number) => {
      if (number === null || number === undefined) {
        return ''; // Or any other placeholder you prefer
      }
      return number.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 });
    };

    const showOrderPopup = ref(false);
    const selectedStock = ref('');
    const orderSide = ref('');
    const orderPrice = ref(null);
    const stocks = ref([]);
    const orderType = ref('');
    const orderQuantity = ref(100);

    const fetchStocks = async () => {
      try {
        const response = await fetch('https://api-finfo.vndirect.com.vn/v4/stocks?q=type:STOCK~status:LISTED&fields=code&size=3000');
        const data = await response.json();
        stocks.value = data.data;
      } catch (error) {
        console.error('Error fetching stocks:', error);
      }
    };

    const openOrderPopup = (side, symbol) => {
      orderSide.value = side;
      selectedStock.value = symbol;
      showOrderPopup.value = true;
      orderType.value = 'LO';
    };

    const closeOrderPopup = () => {
      showOrderPopup.value = false;
      selectedStock.value = '';
      orderSide.value = '';
      orderPrice.value = null;
    };

    const placeOrder = () => {
      if (!tradingToken.value) {
        // If tradingToken is not available, open the OTP popup
        openOtpPopup();
        pendingOrder.value = true; // Indicate that an order is pending
      } else {
        // If tradingToken is available, proceed with order placement
        finalizeOrder();
      }
    };

    const finalizeOrder = async () => {

      const token = localStorage.getItem('token');
      if (!token) {
        alert('Not authorized.');
        return;
      }

      try {
        const response = await fetch('/dnse-order-service/v2/orders', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Trading-Token': tradingToken.value, // Use the tradingToken
          },
          body: JSON.stringify({
            symbol: selectedStock.value,
            quantity: orderQuantity.value,
            price: orderPrice.value,
            side: orderSide.value,
            orderType: orderType.value,
            accountNumber: selectedAccount.value
          }),
        });

        if (response.ok) {
          // const data = await response.json();
          closeOrderPopup();
          fetchDeals(selectedAccount.value); // Refresh deals after placing order
          selectedTab.value = 'Orders';
          fetchOrders(selectedAccount.value);
        } else {
          const errorData = await response.json();
          console.error('Order Placement Failed:', errorData);
          alert(`Order placement failed: ${errorData.message || 'Unknown error'}`);
        }
      } catch (error) {
        console.error('Error during order placement:', error);
        alert('An error occurred during order placement.');
      } finally {
        pendingOrder.value = false; // Reset the flag
      }
    };

    const confirmUpdatePortfolio = async () => {
      showConfirmationDialog.value = false;
      const symbolsAndPrices = deals.value.map(deal => ({
        user_id: userInfo.value.custodyCode,
        symbol: deal.symbol,
        break_even_price: parseInt(deal.breakEvenPrice)
      }));

      try {
        const response = await fetch('/updateTradingSignal', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(symbolsAndPrices)
        });

        if (response.ok) {
          // Handle success
          console.log('Portfolio update request sent successfully');
          // Optionally, refetch data or show a success message
        } else {
          // Handle error
          const errorData = await response.json();
          console.error('Failed to send portfolio update request:', errorData);
          alert(`Failed to update portfolio: ${errorData.message || 'Unknown error'}`);
        }
      } catch (error) {
        console.error('Error sending portfolio update request:', error);
        alert('An error occurred while updating the portfolio.');
      }
    };


    return {
      accounts,
      selectedAccount,
      accountBalance,
      deals,
      errorMessage,
      balanceErrorMessage,
      dealsErrorMessage,
      isMenuOpen,
      toggleMenu,
      isLoggedIn,
      userInfo,
      activeTab,
      formatNumber,
      showOrderPopup,
      selectedStock,
      orderSide,
      orderPrice,
      stocks,
      openOrderPopup,
      closeOrderPopup,
      placeOrder,
      orderType,
      orderQuantity,
      logout,
      showDropdown,
      showOtpPopup,
      closeOtpPopup,
      selectedAuthMethod,
      handleOtpSubmit,
      otpInput,
      selectedTab,
      tabs,
      orders,
      ordersErrorMessage,
      exclusiveSignals,
      showConfirmationDialog,
      confirmUpdatePortfolio
    };
  },
};
</script>
<style scoped>
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