<template>
  <div class="d-flex flex-column min-vh-100 bg-light-gray">
    <NavBar />

    <div class="my-portfolio container py-5 flex-grow-1">
      <!-- Header Section -->
      <div class="d-flex justify-content-between align-items-center mb-5">
        <div>
          <h1 class="display-5 fw-bold text-dark mb-1">My Portfolio</h1>
          <p class="text-muted">Overview of your assets and performance</p>
        </div>
        
        <div class="account-selector-wrapper">
           <select id="account-select" v-model="selectedAccount" class="form-select form-select-lg shadow-sm border-0">
            <option v-for="account in accounts" :key="account.id" :value="account.id">
              {{ account.id }} - {{ account.name }}
            </option>
          </select>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="nav-tabs-wrapper mb-4">
        <div class="nav nav-pills custom-tabs shadow-sm bg-white p-2 rounded-pill d-inline-flex">
          <button
            v-for="tab in tabs"
            :key="tab"
            :class="['nav-link', 'rounded-pill', 'px-4', selectedTab === tab ? 'active' : '']"
            @click="selectedTab = tab"
          >
            {{ tab }}
          </button>
        </div>
      </div>

      <!-- Error Messages -->
      <div v-if="errorMessage" class="alert alert-danger shadow-sm border-0 rounded-3 fade show">
        <i class="bi bi-exclamation-circle-fill me-2"></i> {{ errorMessage }}
      </div>
      <div v-if="balanceErrorMessage" class="alert alert-danger shadow-sm border-0 rounded-3 fade show">
        <i class="bi bi-exclamation-circle-fill me-2"></i> {{ balanceErrorMessage }}
      </div>

      <!-- Tab Content Area -->
      <div class="tab-content-container fade-in">
        
        <!-- Balance Account Tab -->
        <div v-if="selectedTab === 'Balance Account'">
           <div v-if="accountBalance" class="row g-4">
             <!-- Net Asset Value Card -->
             <div class="col-12 mb-4">
               <div class="card border-0 shadow-sm bg-white rounded-3 overflow-hidden h-100 main-balance-card">
                 <div class="card-body p-4 text-center">
                    <h5 class="text-uppercase text-muted fw-bold mb-3 ls-1">Net Asset Value</h5>
                    <h2 class="display-4 fw-bold text-primary mb-0">{{ formatNumber(accountBalance.netAssetValue) }} <span class="fs-4 text-muted">VND</span></h2>
                 </div>
               </div>
             </div>

             <!-- Detailed Metrics -->
             <div class="col-md-6 col-lg-4">
                <div class="card border-0 shadow-sm bg-white rounded-3 h-100 detail-card">
                  <div class="card-body p-4">
                    <h5 class="card-title fw-bold mb-4 text-secondary"><i class="bi bi-wallet2 me-2"></i>Cash Assets</h5>
                    <div class="d-flex justify-content-between mb-3 item-row">
                      <span class="text-muted">Total Cash</span>
                      <span class="fw-semibold">{{ formatNumber(accountBalance.totalCash) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-3 item-row">
                      <span class="text-muted">Withdrawable</span>
                      <span class="fw-semibold">{{ formatNumber(accountBalance.withdrawableCash) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-0 item-row">
                      <span class="text-muted">Deposit Interest</span>
                      <span class="fw-semibold text-success">+{{ formatNumber(accountBalance.depositInterest) }}</span>
                    </div>
                  </div>
                </div>
             </div>

             <div class="col-md-6 col-lg-4">
                <div class="card border-0 shadow-sm bg-white rounded-3 h-100 detail-card">
                  <div class="card-body p-4">
                    <h5 class="card-title fw-bold mb-4 text-secondary"><i class="bi bi-graph-up-arrow me-2"></i>Trading Power</h5>
                    <div class="d-flex justify-content-between mb-3 item-row">
                      <span class="text-muted">Purchasing Power</span>
                      <span class="fw-semibold">{{ formatNumber(accountBalance.purchasingPower) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-3 item-row">
                      <span class="text-muted">Marginable Amt</span>
                      <span class="fw-semibold">{{ formatNumber(accountBalance.marginableAmount) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-0 item-row">
                      <span class="text-muted">Stock Value</span>
                      <span class="fw-semibold">{{ formatNumber(accountBalance.stockValue) }}</span>
                    </div>
                  </div>
                </div>
             </div>

              <div class="col-md-6 col-lg-4">
                <div class="card border-0 shadow-sm bg-white rounded-3 h-100 detail-card">
                  <div class="card-body p-4">
                    <h5 class="card-title fw-bold mb-4 text-secondary"><i class="bi bi-shield-check me-2"></i>Security & Debt</h5>
                    <div class="d-flex justify-content-between mb-3 item-row">
                      <span class="text-muted">Secure Amount</span>
                      <span class="fw-semibold">{{ formatNumber(accountBalance.secureAmount) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-3 item-row">
                      <span class="text-muted">Receiving Amt</span>
                      <span class="fw-semibold">{{ formatNumber(accountBalance.receivingAmount) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-0 item-row">
                      <span class="text-muted">Total Debt</span>
                      <span class="fw-semibold text-danger">{{ formatNumber(accountBalance.totalDebt) }}</span>
                    </div>
                  </div>
                </div>
             </div>
           </div>
           
           <div v-else-if="isLoading" class="d-flex justify-content-center py-5">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
           </div>
        </div>

        <!-- Exclusive Signals Tab -->
        <div v-if="selectedTab === 'Exclusive Signals'">
           <div class="card border-0 shadow-sm bg-white rounded-3">
             <div class="card-body p-4">
                <div class="d-flex justify-content-between align-items-center mb-4">
                   <h3 class="fw-bold mb-0">Exclusive Signals</h3>
                   <span class="badge bg-light text-dark border">Currency: VND</span>
                </div>
                
                <div v-if="isLoading" class="text-center py-5">
                  <div class="spinner-border text-primary" role="status"></div>
                </div>
                
                <div v-else-if="exclusiveSignalsErrorMessage" class="alert alert-danger border-0 rounded-3">
                   {{ exclusiveSignalsErrorMessage }}
                </div>
                
                <div v-else-if="exclusiveSignals.length > 0" class="table-responsive">
                    <table class="table table-hover align-middle custom-table">
                      <thead class="bg-light text-muted">
                        <tr>
                          <th class="py-3 ps-3 rounded-start">Symbol</th>
                          <th class="py-3">Entry Price</th>
                          <th class="py-3">Avg Price</th>
                          <th class="py-3">Current Price</th>
                          <th class="py-3">% Changed</th>
                          <th class="py-3 pe-3 rounded-end">Signal</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="signal in exclusiveSignals" :key="signal.id">
                          <td class="fw-bold ps-3">{{ signal.symbol }}</td>
                          <td>{{ formatNumber(signal.entry_price) }}</td>
                          <td>{{ formatNumber(signal.avg_price) }}</td>
                          <td>{{ formatNumber(signal.current_price) }}</td>
                          <td>
                            <span :class="signal.percent_change >= 0 ? 'text-success' : 'text-danger'" class="fw-bold">
                               <i :class="signal.percent_change >= 0 ? 'bi bi-caret-up-fill' : 'bi bi-caret-down-fill'"></i>
                               {{ (signal.percent_change * 100).toFixed(2) }}%
                            </span>
                          </td>
                          <td class="pe-3">
                            <span :class="['badge', 'rounded-pill', signal.signal === 'BUY' ? 'bg-success' : (signal.signal === 'SELL' ? 'bg-danger' : 'bg-secondary')]">
                              {{ signal.signal }}
                            </span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                </div>
                <div v-else class="text-center py-5 text-muted">
                  <i class="bi bi-inbox fs-1 mb-3 d-block"></i>
                  No exclusive signals to display at the moment.
                </div>
             </div>
           </div>
        </div>
        
        <!-- Journal Tab -->
        <div v-if="selectedTab === 'Journal'">
             <JournalComponent />
        </div>

        <!-- Deals Tab -->
        <div v-if="selectedTab === 'Deals'">
          <div class="card border-0 shadow-sm bg-white rounded-3">
            <div class="card-body p-4">
                <h3 class="fw-bold mb-4">Open Deals</h3>
                 <div v-if="deals.length > 0" class="table-responsive">
                    <table class="table table-hover align-middle custom-table">
                      <thead class="bg-light text-muted">
                        <tr>
                          <th class="py-3 ps-3 rounded-start">Symbol</th>
                          <th class="py-3">Open Quantity</th>
                          <th class="py-3">Unrealized Profit</th>
                          <th class="py-3">Break Even Price</th>
                          <th class="py-3 pe-3 rounded-end text-end">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="deal in deals" :key="deal.id">
                           <td class="fw-bold ps-3">{{ deal.symbol }}</td>
                           <td>{{ deal.openQuantity }}</td>
                           <td :class="deal.unrealizedProfit >= 0 ? 'text-success' : 'text-danger'" class="fw-bold">
                             {{ formatNumber(deal.unrealizedProfit) }}
                           </td>
                           <td>{{ formatNumber(deal.breakEvenPrice) }}</td>
                           <td class="text-end pe-3">
                              <div v-if="deal.openQuantity !== 0">
                                <button class="btn btn-success btn-sm me-2 rounded-pill px-3" @click="openOrderPopup('Buy', deal.symbol)">Buy</button>
                                <button class="btn btn-danger btn-sm rounded-pill px-3" @click="openOrderPopup('Sell', deal.symbol)">Sell</button>
                              </div>
                           </td>
                        </tr>
                      </tbody>
                    </table>
                 </div>
                 <div v-else class="text-center py-5 text-muted">
                    <i class="bi bi-briefcase fs-1 mb-3 d-block"></i>
                     No open deals found.
                 </div>
            </div>
          </div>
        </div>

        <!-- Orders Tab -->
        <div v-if="selectedTab === 'Orders'">
           <div class="card border-0 shadow-sm bg-white rounded-3">
             <div class="card-body p-4">
                <h3 class="fw-bold mb-4">Order History</h3>
                 <div v-if="orders.length > 0" class="table-responsive">
                    <table class="table table-hover align-middle custom-table">
                       <thead class="bg-light text-muted">
                         <tr>
                           <th class="py-3 ps-3 rounded-start">Order ID</th>
                           <th class="py-3">Symbol</th>
                           <th class="py-3">Quantity</th>
                           <th class="py-3">Price</th>
                           <th class="py-3">Side</th>
                           <th class="py-3 pe-3 rounded-end">Status</th>
                         </tr>
                       </thead>
                       <tbody>
                         <tr v-for="order in orders" :key="order.orderId">
                            <td class="ps-3 text-secondary font-monospace">{{ order.id }}</td>
                            <td class="fw-bold">{{ order.symbol }}</td>
                            <td>{{ order.quantity }}</td>
                            <td>{{ formatNumber(order.price) }}</td>
                            <td>
                               <span :class="['badge', 'rounded-pill', order.side === 'NB' ? 'bg-success' : 'bg-danger']">
                                 {{ order.side === 'NB' ? 'BUY' : 'SELL' }}
                               </span>
                            </td>
                             <td class="pe-3">
                               <span :class="['badge', 'bg-light', 'text-dark', 'border']">
                                 {{ order.orderStatus }}
                               </span>
                             </td>
                         </tr>
                       </tbody>
                    </table>
                 </div>
                 <div v-else class="text-center py-5 text-muted">
                    <i class="bi bi-list-check fs-1 mb-3 d-block"></i>
                     No orders found.
                 </div>
             </div>
           </div>
        </div>

      </div>

      <!-- --- Modals --- -->

      <!-- Confirmation Dialog -->
      <div v-if="showConfirmationDialog" class="modal-backdrop-custom d-flex align-items-center justify-content-center">
         <div class="bg-white rounded-4 shadow-lg p-5 text-center" style="max-width: 400px; width: 90%;">
            <div class="mb-4 text-primary">
               <i class="bi bi-cloud-arrow-up fs-1"></i>
            </div>
            <h3 class="fw-bold mb-3">Sync Portfolio?</h3>
            <p class="text-muted mb-4">Would you like to update your portfolio signal analysis based on your current holdings?</p>
            <div class="d-flex gap-2 justify-content-center">
               <button class="btn btn-primary rounded-pill px-4" @click="confirmUpdatePortfolio">Yes, Sync</button>
               <button class="btn btn-outline-secondary rounded-pill px-4" @click="showConfirmationDialog = false">Not Now</button>
            </div>
         </div>
      </div>

       <!-- Order Popup -->
      <div v-if="showOrderPopup" class="modal-backdrop-custom d-flex align-items-center justify-content-center">
        <div class="bg-white rounded-4 shadow-lg overflow-hidden" style="max-width: 500px; width: 100%;">
           <div class="modal-header p-4 bg-light border-bottom">
              <h5 class="fw-bold mb-0">Place Order</h5>
              <button type="button" class="btn-close" @click="closeOrderPopup"></button>
           </div>
           <div class="modal-body p-4">
              <div class="mb-3">
                <label class="form-label fw-bold small text-muted">Symbol</label>
                <select v-model="selectedStock" class="form-select">
                  <option v-for="stock in stocks" :key="stock.code" :value="stock.code">{{ stock.code }}</option>
                </select>
              </div>
              <div class="row">
                 <div class="col-6 mb-3">
                    <label class="form-label fw-bold small text-muted">Side</label>
                    <input type="text" v-model="orderSide" class="form-control" readonly 
                           :class="orderSide === 'Buy' ? 'text-success fw-bold' : 'text-danger fw-bold'">
                 </div>
                 <div class="col-6 mb-3">
                    <label class="form-label fw-bold small text-muted">Type</label>
                    <select v-model="orderType" class="form-select">
                       <option value="LO">LO</option>
                       <option value="MP">MP</option>
                       <option value="ATO">ATO</option>
                       <option value="ATC">ATC</option>
                    </select>
                 </div>
              </div>
               <div class="row">
                 <div class="col-6 mb-3">
                    <label class="form-label fw-bold small text-muted">Quantity</label>
                    <input type="number" v-model="orderQuantity" class="form-control" step="100">
                 </div>
                 <div class="col-6 mb-3">
                    <label class="form-label fw-bold small text-muted">Price</label>
                    <input type="number" v-model="orderPrice" class="form-control">
                 </div>
              </div>
           </div>
           <div class="modal-footer p-3 bg-light border-top d-flex gap-2 justify-content-end">
               <button class="btn btn-light rounded-pill px-4" @click="closeOrderPopup">Cancel</button>
               <button class="btn btn-primary rounded-pill px-4" @click="placeOrder">Place Order</button>
           </div>
        </div>
      </div>

       <!-- OTP Popup -->
       <div v-if="showOtpPopup" class="modal-backdrop-custom d-flex align-items-center justify-content-center">
          <div class="bg-white rounded-4 shadow-lg p-4" style="max-width: 450px; width: 100%;">
             <h4 class="fw-bold mb-4">Security Verification</h4>
             
             <div class="mb-4">
               <label class="form-label text-muted small fw-bold">Authentication Method</label>
               <select v-model="selectedAuthMethod" class="form-select">
                  <option value="smart-otp">Smart OTP (Entrade X App)</option>
                  <option value="email">Email Verification</option>
               </select>
             </div>

             <div v-if="selectedAuthMethod === 'smart-otp'" class="mb-4">
                <p class="small text-muted mb-2">Please enter the Smart OTP code from your Entrade X application:</p>
                <input type="text" v-model="otpInput" class="form-control form-control-lg text-center letter-spacing-2" placeholder="------">
             </div>

             <div class="d-grid gap-2">
                <button class="btn btn-primary btn-lg rounded-pill" @click="handleOtpSubmit">Verify Now</button>
                <button class="btn btn-link text-muted text-decoration-none" @click="closeOtpPopup">Cancel</button>
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
import JournalComponent from './JournalComponent.vue';
import { ref, onMounted, watch, computed } from 'vue';
import { useRouter } from 'vue-router';

export default {
  name: 'MyPortfolio',
  components: {
    NavBar,
    AppFooter,
    JournalComponent
  },
  setup() {
    const router = useRouter();
    const accounts = ref([]);
    const selectedAccount = ref('');
    const accountBalance = ref(null);
    const deals = ref([]);
    const errorMessage = ref('');
    const balanceErrorMessage = ref('');
    const dealsErrorMessage = ref('');
    const isMenuOpen = ref(false);
    const userInfo = ref({});
    const showDropdown = ref(false);

    // OTP Popup variables
    const showOtpPopup = ref(false);
    const selectedAuthMethod = ref('smart-otp');
    const otpInput = ref('');
    let pendingOrder = ref(false);
    const tradingToken = ref('');

    // Tabs - Reordered as requested
    const selectedTab = ref('Balance Account');
    const tabs = ref(['Balance Account', 'Exclusive Signals', 'Journal', 'Deals', 'Orders']);
    
    // Data refs
    const orders = ref([]);
    const ordersErrorMessage = ref('');
    const exclusiveSignals = ref([]);
    const exclusiveSignalsErrorMessage = ref('');
    const isLoading = ref(false);
    
    // Order Popup
    const showOrderPopup = ref(false);
    const selectedStock = ref('');
    const orderSide = ref('');
    const orderPrice = ref(null);
    const stocks = ref([]);
    const orderType = ref('LO');
    const orderQuantity = ref(100);

    // Confirmation Dialog
    const showConfirmationDialog = ref(false);

    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value;
    };

    const logout = () => {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('userInfo');
      userInfo.value = null;
      router.push('/');
    }
    
    const isLoggedIn = computed(() => {
      return !!localStorage.getItem('token');
    });

    const formatNumber = (number) => {
      if (number === null || number === undefined) {
        return '-';
      }
      return number.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 });
    };

    // --- API Calls ---

    const fetchExclusiveSignals = async () => {
      isLoading.value = true;
      exclusiveSignalsErrorMessage.value = '';
      exclusiveSignals.value = [];
      userInfo.value = JSON.parse(localStorage.getItem('userInfo'));
      
      if (!userInfo.value || !userInfo.value.custodyCode) {
        exclusiveSignalsErrorMessage.value = 'User information not available.';
        isLoading.value = false;
        // Do not force logout immediately here, just show error
        return;
      }

      try {
        const response = await fetch(`/getUserTrade?user_id=${userInfo.value.custodyCode}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        exclusiveSignals.value = data;
        
        if (!data || data.length === 0) {
          // No signals is fine, layout handles it
        }
      } catch (error) {
        if (error.response) {
            exclusiveSignalsErrorMessage.value = `Failed to fetch exclusive signals: ${error.response.data.message || 'Unknown error'}`;
        } else {
             // Often this API might not be ready or fail, show generic message
            exclusiveSignalsErrorMessage.value = 'Could not load signals.';
            console.error('Error fetching signals:', error);
        }
      } finally {
        isLoading.value = false;
      }
    };

    const fetchOrders = async (accountNumber) => {
      isLoading.value = true;
      ordersErrorMessage.value = '';
      const token = localStorage.getItem('token');
      if (!token) return;

      try {
        const response = await fetch(`/dnse-order-service/v2/orders?accountNo=${accountNumber}`, {
          headers: { 'Authorization': `Bearer ${token}` },
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
        ordersErrorMessage.value = 'Error fetching orders.';
      } finally {
        isLoading.value = false;
      }
    };

    const fetchAccountBalance = async (accountNumber) => {
      isLoading.value = true;
      balanceErrorMessage.value = '';
      const token = localStorage.getItem('token');
      if (!token) return;

      try {
        const response = await fetch(`/dnse-order-service/account-balances/${accountNumber}`, {
          headers: { 'Authorization': `Bearer ${token}` },
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
        balanceErrorMessage.value = 'Error fetching balance.';
      } finally {
        isLoading.value = false;
      }
    };

    const fetchDeals = async (accountNumber) => {
      isLoading.value = true;
      dealsErrorMessage.value = '';
      const token = localStorage.getItem('token');
      if (!token) return;

      try {
        const response = await fetch(`/dnse-deal-service/deals?accountNo=${accountNumber}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
          const data = await response.json();
          deals.value = data.deals;

          // Only show dialog if we have meaningful deals to sync AND we haven't synced this session
          // For now, simpler logic: show if deals exist
           if (data.deals && data.deals.length > 0) {
               showConfirmationDialog.value = true;
           }
        } else {
          dealsErrorMessage.value = 'Failed to fetch deals.';
        }
      } catch (error) {
        dealsErrorMessage.value = 'Error fetching deals.';
        console.error(error);
      } finally {
        isLoading.value = false;
      }
    }

    const fetchStocks = async () => {
      try {
        const response = await fetch('https://api-finfo.vndirect.com.vn/v4/stocks?q=type:STOCK~status:LISTED&fields=code&size=3000');
        const data = await response.json();
        stocks.value = data.data;
      } catch (error) {
        console.error('Error fetching stocks:', error);
      }
    };

    // --- Order Logic ---

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

    const openOtpPopup = () => showOtpPopup.value = true;
    
    const closeOtpPopup = () => {
      showOtpPopup.value = false;
      otpInput.value = '';
      pendingOrder.value = false;
    };

    const handleOtpSubmit = async () => {
        if (selectedAuthMethod.value === 'smart-otp') {
            if (!otpInput.value) {
                alert('Please input the OTP');
                return;
            }
            const token = localStorage.getItem('token');
            if (!token) return;

            try {
                const response = await fetch('/dnse-order-service/trading-token', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}`, 'smart-otp': otpInput.value },
                });

                if (response.ok) {
                    const data = await response.json();
                    tradingToken.value = data.tradingToken;
                    if (pendingOrder.value) finalizeOrder();
                    closeOtpPopup();
                } else {
                    const errorData = await response.json();
                    alert(`Authentication failed: ${errorData.message || 'Unknown error'}`);
                }
            } catch (error) {
                console.error(error);
                alert('Authentication error.');
            }
        }
    };

    const placeOrder = () => {
      if (!tradingToken.value) {
        openOtpPopup();
        pendingOrder.value = true;
      } else {
        finalizeOrder();
      }
    };

    const finalizeOrder = async () => {
        const token = localStorage.getItem('token');
        if (!token) return;

        try {
            const response = await fetch('/dnse-order-service/v2/orders', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}`, 'Trading-Token': tradingToken.value },
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
                closeOrderPopup();
                fetchDeals(selectedAccount.value);
                selectedTab.value = 'Orders'; // Switch to orders tab
                fetchOrders(selectedAccount.value);
            } else {
                const errorData = await response.json();
                alert(`Order failed: ${errorData.message || 'Unknown error'}`);
            }
        } catch (error) {
            console.error(error);
            alert('Order placement error.');
        } finally {
            pendingOrder.value = false;
        }
    };

    const confirmUpdatePortfolio = async () => {
      userInfo.value = JSON.parse(localStorage.getItem('userInfo'));
      if (!userInfo.value || !userInfo.value.custodyCode) {
        logout();
        return;
      }
      
      showConfirmationDialog.value = false;
      const symbolsAndPrices = deals.value.map(deal => ({
        user_id: userInfo.value.custodyCode,
        symbol: deal.symbol,
        break_even_price: parseInt(deal.breakEvenPrice)
      }));

      try {
        await fetch('/updateTradingSignal', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(symbolsAndPrices)
        });
        // Success silently
      } catch (error) {
        console.error('Update portfolio error:', error);
      }
    };

    // --- Lifecycle & Watchers ---

    onMounted(async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        router.push('/login');
        return;
      }

      try {
        const response = await fetch('/dnse-order-service/accounts', {
          headers: { 'Authorization': `Bearer ${token}` },
        });

        if (response.ok) {
          const data = await response.json();
          accounts.value = data.accounts;
          const defaultAccount = data.default;
          if (defaultAccount) {
            selectedAccount.value = defaultAccount.id;
            fetchAccountBalance(selectedAccount.value);
            fetchDeals(selectedAccount.value);
          }
        } else {
          errorMessage.value = 'Failed to fetch accounts.';
        }
      } catch (error) {
        errorMessage.value = 'Connection error fetching accounts.';
      }
      await fetchStocks();
    });

    watch(selectedAccount, (newAccountNumber) => {
      if (newAccountNumber) {
        fetchAccountBalance(newAccountNumber);
        fetchDeals(newAccountNumber);
        // Refresh other tabs if active
        if (selectedTab.value === 'Orders') fetchOrders(newAccountNumber);
      }
    });

    watch(selectedTab, (newTab) => {
      if (newTab === 'Orders' && selectedAccount.value) {
        fetchOrders(selectedAccount.value);
      } else if (newTab === 'Exclusive Signals') {
        fetchExclusiveSignals();
      }
    });

    return {
      accounts, selectedAccount, accountBalance, deals, orders, exclusiveSignals,
      errorMessage, balanceErrorMessage, exclusiveSignalsErrorMessage,
      isLoading, isMenuOpen, toggleMenu, isLoggedIn, userInfo, showDropdown,
      selectedTab, tabs, formatNumber,
      // Order
      showOrderPopup, selectedStock, orderSide, orderPrice, stocks, openOrderPopup, closeOrderPopup, placeOrder,
      orderType, orderQuantity,
      // OTP
      showOtpPopup, closeOtpPopup, selectedAuthMethod, handleOtpSubmit, otpInput,
      // Confirmation
      showConfirmationDialog, confirmUpdatePortfolio
    };
  }
};
</script>

<style scoped>
.bg-light-gray {
  background-color: #f8f9fa;
}

.custom-tabs .nav-link {
  color: #6c757d;
  font-weight: 500;
  border: none;
  transition: all 0.3s ease;
}

.custom-tabs .nav-link.active {
  background-color: #0d6efd;
  color: white;
  box-shadow: 0 4px 6px rgba(13, 110, 253, 0.2);
}

.custom-tabs .nav-link:hover:not(.active) {
  background-color: #e9ecef;
  color: #495057;
}

.detail-card {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.detail-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 .5rem 1rem rgba(0,0,0,.15)!important;
}
.main-balance-card {
    background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
}

.item-row {
    border-bottom: 1px dashed #e9ecef;
    padding-bottom: 0.5rem;
}
.item-row:last-child {
    border-bottom: none;
    padding-bottom: 0;
}

.ls-1 {
    letter-spacing: 1px;
}

.custom-table th {
    font-weight: 600;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.modal-backdrop-custom {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.5);
    z-index: 1050;
    backdrop-filter: blur(4px);
}

.fade-in {
    animation: fadeIn 0.4s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.letter-spacing-2 {
    letter-spacing: 4px;
}
</style>