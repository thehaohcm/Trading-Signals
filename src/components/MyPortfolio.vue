<template>
  <div class="stk-page d-flex flex-column min-vh-100">
    <NavBar />

    <div class="my-portfolio container-xxl py-4 flex-grow-1">
      <!-- Header Section -->
      <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
        <div>
          <h1 class="display-6 fw-bold mb-1 text-white" style="font-family: 'Outfit', sans-serif;"><i class="fa-solid fa-wallet text-primary me-2"></i>My Portfolio</h1>
          <p class="text-muted small">Overview of your real-time holdings, signals, and account value</p>
        </div>
        
        <div class="account-selector-wrapper">
           <select id="account-select" v-model="selectedAccount" class="stk-input shadow-sm" style="min-width: 220px; font-weight: 600;">
            <option v-for="account in accounts" :key="account.id" :value="account.id">
              {{ account.id }} - {{ account.name }}
            </option>
          </select>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="nav-tabs-wrapper mb-4 d-flex justify-content-center">
        <div class="stk-tabs-glass p-1">
          <button
            v-for="tab in tabs"
            :key="tab"
            :class="['stk-tab-pill', selectedTab === tab ? 'active' : '']"
            @click="selectedTab = tab"
          >
            {{ tab }}
          </button>
        </div>
      </div>

      <!-- Error Messages -->
      <div v-if="errorMessage" class="alert alert-danger shadow-sm border-0 rounded-3 fade show bg-danger bg-opacity-10 text-danger border border-danger border-opacity-20 mb-3">
        <i class="fa-solid fa-triangle-exclamation me-2"></i> {{ errorMessage }}
      </div>
      <div v-if="balanceErrorMessage" class="alert alert-danger shadow-sm border-0 rounded-3 fade show bg-danger bg-opacity-10 text-danger border border-danger border-opacity-20 mb-3">
        <i class="fa-solid fa-triangle-exclamation me-2"></i> {{ balanceErrorMessage }}
      </div>

      <!-- Tab Content Area -->
      <div class="tab-content-container fade-in">
        
        <!-- Balance Account Tab -->
        <div v-if="selectedTab === 'Balance Account'">
           <div v-if="accountBalance" class="row g-4">
             <!-- Net Asset Value Card -->
             <div class="col-12 mb-2">
               <div class="stk-balance-card overflow-hidden">
                 <div class="card-body p-4 text-center">
                    <h5 class="text-uppercase text-muted fw-bold mb-2 ls-1" style="font-size: 0.8rem; letter-spacing: 1px;">Net Asset Value</h5>
                    <h2 class="display-5 fw-bold text-white mb-0 nav-glow">{{ formatNumber(accountBalance.netAssetValue) }} <span class="fs-5 text-muted">VND</span></h2>
                 </div>
               </div>
             </div>

             <!-- Detailed Metrics -->
             <div class="col-md-6 col-lg-4">
                <div class="stk-panel h-100 detail-card">
                  <div class="card-body p-4">
                    <h5 class="card-title fw-bold mb-4 text-white" style="font-size: 0.95rem; font-family: 'Outfit', sans-serif;"><i class="fa-solid fa-money-bill-wave me-2 text-primary"></i>Cash Assets</h5>
                    <div class="d-flex justify-content-between mb-3 item-row">
                      <span class="text-muted">Total Cash</span>
                      <span class="fw-semibold text-white">{{ formatNumber(accountBalance.totalCash) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-3 item-row">
                      <span class="text-muted">Withdrawable</span>
                      <span class="fw-semibold text-white">{{ formatNumber(accountBalance.withdrawableCash) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-0 item-row">
                      <span class="text-muted">Deposit Interest</span>
                      <span class="fw-semibold text-success">+{{ formatNumber(accountBalance.depositInterest) }}</span>
                    </div>
                  </div>
                </div>
             </div>

             <div class="col-md-6 col-lg-4">
                <div class="stk-panel h-100 detail-card">
                  <div class="card-body p-4">
                    <h5 class="card-title fw-bold mb-4 text-white" style="font-size: 0.95rem; font-family: 'Outfit', sans-serif;"><i class="fa-solid fa-chart-line me-2 text-primary"></i>Trading Power</h5>
                    <div class="d-flex justify-content-between mb-3 item-row">
                      <span class="text-muted">Purchasing Power</span>
                      <span class="fw-semibold text-white">{{ formatNumber(accountBalance.purchasingPower) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-3 item-row">
                      <span class="text-muted">Marginable Amt</span>
                      <span class="fw-semibold text-white">{{ formatNumber(accountBalance.marginableAmount) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-0 item-row">
                      <span class="text-muted">Stock Value</span>
                      <span class="fw-semibold text-white">{{ formatNumber(accountBalance.stockValue) }}</span>
                    </div>
                  </div>
                </div>
             </div>

              <div class="col-md-6 col-lg-4">
                <div class="stk-panel h-100 detail-card">
                  <div class="card-body p-4">
                    <h5 class="card-title fw-bold mb-4 text-white" style="font-size: 0.95rem; font-family: 'Outfit', sans-serif;"><i class="fa-solid fa-shield-halved me-2 text-primary"></i>Security & Debt</h5>
                    <div class="d-flex justify-content-between mb-3 item-row">
                      <span class="text-muted">Secure Amount</span>
                      <span class="fw-semibold text-white">{{ formatNumber(accountBalance.secureAmount) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-3 item-row">
                      <span class="text-muted">Receiving Amt</span>
                      <span class="fw-semibold text-white">{{ formatNumber(accountBalance.receivingAmount) }}</span>
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
           <div class="stk-panel">
              <div class="stk-header justify-content-between align-items-center flex-wrap gap-2">
                 <h3 class="stk-header__title"><i class="fa-solid fa-bolt me-2 text-warning"></i>Exclusive Signals Analysis</h3>
                 <span class="badge bg-primary-glow px-2 py-1" style="font-size: 0.75rem;">Currency: VND</span>
              </div>
              <div class="stk-section">
                
                <div v-if="isLoading" class="text-center py-5">
                  <div class="spinner-border text-primary" role="status"></div>
                </div>
                
                <div v-else-if="exclusiveSignalsErrorMessage" class="alert alert-danger border-0 rounded-3 bg-danger bg-opacity-10 text-danger border border-danger border-opacity-20">
                   {{ exclusiveSignalsErrorMessage }}
                </div>
                
                <div v-else-if="exclusiveSignals.length > 0" class="stk-table-wrap table-responsive">
                    <table class="stk-table align-middle">
                      <thead>
                        <tr>
                          <th class="stk-th">Symbol</th>
                          <th class="stk-th text-end">Entry Price</th>
                          <th class="stk-th text-end">Avg Price</th>
                          <th class="stk-th text-end">Current Price</th>
                          <th class="stk-th text-end">% Changed</th>
                          <th class="stk-th text-center">Signal</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="signal in exclusiveSignals" :key="signal.id" class="stk-row">
                          <td class="stk-td fw-bold text-white">{{ signal.symbol }}</td>
                          <td class="stk-td text-end text-muted">{{ formatNumber(signal.entry_price) }}</td>
                          <td class="stk-td text-end text-muted">{{ formatNumber(signal.avg_price) }}</td>
                          <td class="stk-td text-end text-white">{{ formatNumber(signal.current_price) }}</td>
                          <td class="stk-td text-end">
                            <span :class="signal.percent_change >= 0 ? 'text-success' : 'text-danger'" class="fw-bold">
                               <i :class="signal.percent_change >= 0 ? 'fa-solid fa-caret-up' : 'fa-solid fa-caret-down'"></i>
                               {{ (signal.percent_change * 100).toFixed(2) }}%
                            </span>
                          </td>
                          <td class="stk-td text-center">
                            <span :class="['stk-signal-pill', signal.signal ? signal.signal.toLowerCase() : '']">
                              {{ signal.signal }}
                            </span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                </div>
                <div v-else class="text-center py-5 text-muted">
                  <i class="fa-regular fa-folder-open fs-2 mb-3 d-block text-secondary"></i>
                  No exclusive portfolio signals to display at the moment.
                </div>
              </div>
           </div>
        </div>
        
        <!-- Journal Tab -->
        <div v-if="selectedTab === 'Journal'">
             <JournalComponent :account-number="selectedAccount" />
        </div>

        <!-- Deals Tab -->
        <div v-if="selectedTab === 'Deals'">
          <div class="stk-panel">
             <div class="stk-header">
                 <h3 class="stk-header__title"><i class="fa-solid fa-briefcase me-2 text-primary"></i>Open Position Deals</h3>
             </div>
             <div class="stk-section">
                  <div v-if="deals.length > 0" class="stk-table-wrap table-responsive">
                     <table class="stk-table align-middle">
                       <thead>
                         <tr>
                           <th class="stk-th">Symbol</th>
                           <th class="stk-th text-center">Open Quantity</th>
                           <th class="stk-th text-end">Unrealized Profit</th>
                           <th class="stk-th text-end">Break Even Price</th>
                           <th class="stk-th text-center">Actions</th>
                         </tr>
                       </thead>
                       <tbody>
                         <tr v-for="deal in deals" :key="deal.id" class="stk-row">
                            <td class="stk-td fw-bold text-white">{{ deal.symbol }}</td>
                            <td class="stk-td text-center text-white">{{ deal.openQuantity }}</td>
                            <td class="stk-td text-end fw-bold" :class="deal.unrealizedProfit >= 0 ? 'text-success' : 'text-danger'">
                              {{ formatNumber(deal.unrealizedProfit) }}
                            </td>
                            <td class="stk-td text-end text-muted">{{ formatNumber(deal.breakEvenPrice) }}</td>
                            <td class="stk-td text-center">
                               <div v-if="deal.openQuantity !== 0" class="d-inline-flex gap-2">
                                 <button class="stk-btn stk-btn-xxs stk-btn--success" @click="openOrderPopup('Buy', deal.symbol)">Buy</button>
                                 <button class="stk-btn stk-btn-xxs stk-btn--danger" @click="openOrderPopup('Sell', deal.symbol)">Sell</button>
                               </div>
                            </td>
                         </tr>
                       </tbody>
                     </table>
                  </div>
                  <div v-else class="text-center py-5 text-muted">
                     <i class="fa-solid fa-box-open fs-2 mb-3 d-block text-secondary"></i>
                      No open deals found.
                  </div>
             </div>
          </div>
        </div>

        <!-- Orders Tab -->
        <div v-if="selectedTab === 'Orders'">
           <div class="stk-panel">
             <div class="stk-header">
                 <h3 class="stk-header__title"><i class="fa-solid fa-list-check me-2 text-primary"></i>Order Executions</h3>
             </div>
             <div class="stk-section">
                  <div v-if="orders.length > 0" class="stk-table-wrap table-responsive">
                     <table class="stk-table align-middle">
                        <thead>
                          <tr>
                            <th class="stk-th">Order ID</th>
                            <th class="stk-th">Symbol</th>
                            <th class="stk-th text-center">Quantity</th>
                            <th class="stk-th text-end">Price</th>
                            <th class="stk-th text-center">Side</th>
                            <th class="stk-th text-center">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="order in orders" :key="order.orderId" class="stk-row">
                             <td class="stk-td text-muted font-monospace" style="font-size: 0.8rem;">{{ order.id }}</td>
                             <td class="stk-td fw-bold text-white">{{ order.symbol }}</td>
                             <td class="stk-td text-center text-white">{{ order.quantity }}</td>
                             <td class="stk-td text-end text-muted">{{ formatNumber(order.price) }}</td>
                             <td class="stk-td text-center">
                                <span :class="['stk-type-badge', order.side === 'NB' ? 'house' : 'apartment']" style="font-size: 0.7rem; padding: 2px 8px;">
                                  {{ order.side === 'NB' ? 'BUY' : 'SELL' }}
                                </span>
                             </td>
                              <td class="stk-td text-center">
                                <span class="badge bg-primary-glow px-2 py-1" style="font-size: 0.72rem; letter-spacing: 0.5px;">
                                  {{ order.orderStatus }}
                                </span>
                              </td>
                          </tr>
                        </tbody>
                     </table>
                  </div>
                  <div v-else class="text-center py-5 text-muted">
                     <i class="fa-solid fa-history fs-2 mb-3 d-block text-secondary"></i>
                      No active orders or order history found.
                  </div>
             </div>
           </div>
        </div>

      </div>

      <!-- --- Modals --- -->

      <!-- Confirmation Dialog -->
      <div v-if="showConfirmationDialog" class="modal-backdrop-custom d-flex align-items-center justify-content-center">
         <div class="stk-modal p-4">
            <div class="text-center mb-3">
               <div class="mb-2 text-primary">
                  <i class="fa-solid fa-cloud-arrow-up fs-2"></i>
               </div>
               <h3 class="fw-bold mb-2 text-white" style="font-family: 'Outfit', sans-serif;">Sync Portfolio?</h3>
               <p class="text-muted small mb-3">Would you like to update your portfolio signal analysis based on your current holdings?</p>
            </div>

            <!-- Option to input current price -->
            <div class="form-check form-switch mb-3 p-3 stk-card d-flex align-items-center justify-content-between">
               <label class="form-check-label fw-semibold text-white mb-0 ms-0" for="updateCurrentPriceSwitch" style="cursor: pointer; font-size: 0.85rem;">
                  <i class="fa-solid fa-coins me-2 text-primary"></i>
                  Cập nhật giá hiện tại theo giá nhập
               </label>
               <input class="form-check-input ms-3 cursor-pointer" type="checkbox" id="updateCurrentPriceSwitch" v-model="updateCurrentPrice" style="width: 2.4em; height: 1.2em;">
            </div>

            <!-- List of symbols to sync -->
            <div v-if="deals && deals.length > 0" class="flex-grow-1 overflow-y-auto mb-3 px-2 stk-table-wrap" style="max-height: 250px;">
               <div class="table-responsive">
                  <table class="stk-table table-sm">
                     <thead>
                        <tr class="text-muted small" style="border-bottom: 1px solid rgba(255,255,255,0.06);">
                           <th class="stk-th py-2">Mã CP</th>
                           <th class="stk-th py-2">Giá vốn</th>
                           <th v-if="updateCurrentPrice" class="stk-th py-2">Giá hiện tại</th>
                        </tr>
                     </thead>
                     <tbody>
                        <tr v-for="deal in deals" :key="deal.id" class="stk-row">
                           <td class="stk-td fw-bold text-white py-2">{{ deal.symbol }}</td>
                           <td class="stk-td py-2 text-muted">{{ formatNumber(deal.breakEvenPrice) }}</td>
                           <td v-if="updateCurrentPrice" style="width: 150px;" class="stk-td py-1">
                              <input type="number" 
                                     v-model.number="deal.enteredCurrentPrice" 
                                     class="stk-input py-1" 
                                     placeholder="Nhập giá..."
                                     style="font-size: 0.8rem; height: 28px;">
                           </td>
                        </tr>
                     </tbody>
                  </table>
               </div>
            </div>

            <div class="d-flex gap-2 justify-content-center mt-auto pt-3 border-top border-opacity-10 border-white">
               <button class="stk-btn stk-btn--primary px-4 py-2" @click="confirmUpdatePortfolio">Yes, Sync</button>
               <button class="stk-btn stk-btn--outline px-4 py-2" @click="showConfirmationDialog = false">Not Now</button>
            </div>
         </div>
      </div>

       <!-- Order Popup -->
      <div v-if="showOrderPopup" class="modal-backdrop-custom d-flex align-items-center justify-content-center">
        <div class="stk-modal overflow-hidden p-0" style="max-width: 500px; width: 100%;">
           <div class="stk-header p-4 d-flex justify-content-between align-items-center">
              <h5 class="fw-bold mb-0 text-white"><i class="fa-solid fa-cart-shopping text-primary me-2"></i>Place Order</h5>
              <button type="button" class="btn-close btn-close-white" @click="closeOrderPopup"></button>
           </div>
           <div class="p-4">
              <div class="mb-3">
                <label class="stk-label">Symbol</label>
                <select v-model="selectedStock" class="stk-input">
                  <option v-for="stock in stocks" :key="stock.code" :value="stock.code">{{ stock.code }}</option>
                </select>
              </div>
              <div class="row">
                 <div class="col-6 mb-3">
                    <label class="stk-label">Side</label>
                    <input type="text" v-model="orderSide" class="stk-input fw-bold" readonly 
                           :style="{color: orderSide === 'Buy' ? '#34d399' : '#f43f5e'}">
                 </div>
                 <div class="col-6 mb-3">
                    <label class="stk-label">Type</label>
                    <select v-model="orderType" class="stk-input">
                       <option value="LO">LO</option>
                       <option value="MP">MP</option>
                       <option value="ATO">ATO</option>
                       <option value="ATC">ATC</option>
                    </select>
                 </div>
              </div>
               <div class="row">
                 <div class="col-6 mb-3">
                    <label class="stk-label">Quantity</label>
                    <input type="number" v-model="orderQuantity" class="stk-input" step="100">
                 </div>
                 <div class="col-6 mb-3">
                    <label class="stk-label">Price</label>
                    <input type="number" v-model="orderPrice" class="stk-input">
                 </div>
              </div>
           </div>
           <div class="p-3 border-top border-opacity-10 border-white bg-dark bg-opacity-20 d-flex gap-2 justify-content-end">
               <button class="stk-btn stk-btn--outline px-4" @click="closeOrderPopup">Cancel</button>
               <button class="stk-btn stk-btn--primary px-4" @click="placeOrder">Place Order</button>
           </div>
        </div>
      </div>

       <!-- OTP Popup -->
       <div v-if="showOtpPopup" class="modal-backdrop-custom d-flex align-items-center justify-content-center">
          <div class="stk-modal p-4" style="max-width: 450px; width: 100%;">
             <h4 class="fw-bold mb-4 text-white" style="font-family: 'Outfit', sans-serif;"><i class="fa-solid fa-shield-halved text-primary me-2"></i>Security Verification</h4>
             
             <div class="mb-4">
               <label class="stk-label">Authentication Method</label>
               <select v-model="selectedAuthMethod" class="stk-input">
                  <option value="smart-otp">Smart OTP (Entrade X App)</option>
                  <option value="email">Email Verification</option>
               </select>
             </div>

             <div v-if="selectedAuthMethod === 'smart-otp'" class="mb-4">
                <p class="small text-muted mb-2">Please enter the Smart OTP code from your Entrade X application:</p>
                <input type="text" v-model="otpInput" class="stk-input text-center letter-spacing-2" placeholder="------" style="font-size: 1.25rem; font-weight: 700; height: 50px;">
             </div>

             <div class="d-grid gap-2">
                <button class="stk-btn stk-btn--primary btn-lg py-2" @click="handleOtpSubmit">Verify Now</button>
                <button class="stk-btn stk-btn--outline py-2 mt-2" @click="closeOtpPopup">Cancel</button>
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
    const updateCurrentPrice = ref(false);

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
               // Load signals to pre-populate current prices if not already loaded
               if (exclusiveSignals.value.length === 0) {
                   await fetchExclusiveSignals();
               }
               data.deals.forEach(deal => {
                   const matchedSignal = exclusiveSignals.value.find(s => s.symbol === deal.symbol);
                   deal.enteredCurrentPrice = matchedSignal ? matchedSignal.current_price : null;
               });
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
      const symbolsAndPrices = deals.value.map(deal => {
        const updateObj = {
          user_id: userInfo.value.custodyCode,
          symbol: deal.symbol,
          break_even_price: parseInt(deal.breakEvenPrice)
        };
        if (updateCurrentPrice.value && deal.enteredCurrentPrice !== undefined && deal.enteredCurrentPrice !== null && deal.enteredCurrentPrice !== '') {
          updateObj.current_price = parseInt(deal.enteredCurrentPrice);
        }
        return updateObj;
      });

      try {
        await fetch('/updateTradingSignal', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(symbolsAndPrices)
        });
        // Refresh signals
        await fetchExclusiveSignals();
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
      showConfirmationDialog, confirmUpdatePortfolio, updateCurrentPrice
    };
  }
};
</script>

<style scoped>
/* ==================================== */
/*  PORTFOLIO PAGE – Premium Desk UI    */
/* ==================================== */

.stk-page {
  background: #23273a;
  min-height: 100vh;
  color: #f1f5f9;
}

.my-portfolio {
  max-width: 1400px;
  margin: 0 auto;
}

/* ---------- TABS GLASS ---------- */
.stk-tabs-glass {
  display: inline-flex;
  gap: 4px;
  background: rgba(13, 16, 27, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 30px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.25);
  backdrop-filter: blur(8px);
}
.stk-tab-pill {
  padding: 8px 24px;
  border-radius: 30px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #94a3b8;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.25s ease;
  outline: none;
}
.stk-tab-pill:hover {
  color: #f1f5f9;
  background: rgba(255, 255, 255, 0.03);
}
.stk-tab-pill.active {
  color: #fff !important;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.35);
}

/* ---------- PANEL ---------- */
.stk-panel {
  background: rgba(17, 22, 34, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.35);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  overflow: hidden;
  margin-bottom: 20px;
}

/* ---------- BALANCE CARD ---------- */
.stk-balance-card {
  background: radial-gradient(circle at top, rgba(37, 99, 235, 0.15) 0%, rgba(17, 22, 34, 0.8) 100%);
  border: 1px solid rgba(59, 130, 246, 0.25);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(37, 99, 235, 0.1);
  backdrop-filter: blur(16px);
  margin-bottom: 20px;
}

/* ---------- HEADER ---------- */
.stk-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #1e293b 0%, #0d0f17 100%);
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.stk-header__title {
  font-size: 1.15rem;
  font-weight: 700;
  margin: 0;
  line-height: 1.3;
  font-family: 'Outfit', sans-serif;
  color: #f1f5f9;
  display: flex;
  align-items: center;
}

/* ---------- SECTIONS ---------- */
.stk-section {
  padding: 24px;
}
.detail-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.detail-card:hover {
  transform: translateY(-4px);
  border-color: rgba(59, 130, 246, 0.3) !important;
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.1) !important;
}
.item-row {
  border-bottom: 1px dashed rgba(255, 255, 255, 0.06);
  padding-bottom: 0.75rem;
}
.item-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

/* ---------- INPUTS ---------- */
.stk-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  font-size: 0.88rem;
  color: #f1f5f9;
  background: rgba(13, 16, 27, 0.85);
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
}
.stk-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.25);
}

/* ---------- BUTTONS ---------- */
.stk-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 9px 18px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  outline: none;
}
.stk-btn-xxs {
  padding: 4px 12px;
  font-size: 0.72rem;
  border-radius: 6px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}
.stk-btn--primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border-color: rgba(255,255,255,0.1);
}
.stk-btn--primary:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
}
.stk-btn--success {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.35);
}
.stk-btn--success:hover {
  background: #10b981;
  color: #fff;
}
.stk-btn--danger {
  background: rgba(244, 63, 94, 0.15);
  color: #fb7185;
  border: 1px solid rgba(244, 63, 94, 0.35);
}
.stk-btn--danger:hover {
  background: #f43f5e;
  color: #fff;
}
.stk-btn--outline {
  background: transparent;
  color: #cbd5e1;
  border: 1px solid rgba(255, 255, 255, 0.12);
}
.stk-btn--outline:hover {
  background: rgba(255, 255, 255, 0.04);
  color: #fff;
}

/* ---------- TABLE ---------- */
.stk-table-wrap {
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  overflow: hidden;
  background: rgba(13, 16, 27, 0.2);
}
.stk-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.stk-th {
  padding: 12px 16px;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #94a3b8;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 2px solid rgba(255, 255, 255, 0.08);
  position: sticky;
  top: 0;
  z-index: 2;
}
.stk-td {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  vertical-align: middle;
}
.stk-row {
  cursor: pointer;
  transition: background 0.15s ease;
}
.stk-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

/* ---------- MODALS ---------- */
.modal-backdrop-custom {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(8, 10, 18, 0.75);
  z-index: 1050;
  backdrop-filter: blur(10px);
}
.stk-modal {
  background: rgba(22, 28, 45, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5);
  max-width: 500px;
  width: 90%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  color: #f1f5f9;
}

/* ---------- BADGES & GLOWS ---------- */
.stk-label {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.stk-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}
.stk-type-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.3px;
  text-transform: uppercase;
}
.stk-type-badge.house {
  background: rgba(16, 185, 129, 0.12);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.25);
}
.stk-type-badge.apartment {
  background: rgba(244, 63, 94, 0.12);
  color: #fb7185;
  border: 1px solid rgba(244, 63, 94, 0.25);
}
.stk-signal-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 3px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  border: 1px solid transparent;
}
.stk-signal-pill.buy {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border-color: rgba(16, 185, 129, 0.3);
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.1);
}
.stk-signal-pill.sell {
  background: rgba(244, 63, 94, 0.15);
  color: #fb7185;
  border-color: rgba(244, 63, 94, 0.3);
  box-shadow: 0 0 10px rgba(244, 63, 94, 0.1);
}
.bg-primary-glow {
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #60a5fa;
}

.nav-glow {
  text-shadow: 0 0 20px rgba(59, 130, 246, 0.35);
}
.ls-1 {
  letter-spacing: 1px;
}
.letter-spacing-2 {
  letter-spacing: 4px;
}
.fade-in {
  animation: fadeIn 0.4s ease-in-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>