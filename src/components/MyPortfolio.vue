<template>
  <div id="portfolio-view-root" class="d-flex flex-column min-vh-100">
    <notifications />

    <div class="my-portfolio container-xxl py-4 flex-grow-1">
      <!-- Header Section -->
      <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
        <div>
          <h1 class="display-6 fw-bold mb-1" style="font-family: 'Outfit', sans-serif; color: #ffffff;"><i class="fa-solid fa-wallet text-primary me-2"></i>My Portfolio</h1>
          <p class="small" style="color: #94a3b8;">Overview of your real-time holdings, signals, and account value</p>
        </div>
        
        <div class="account-selector-wrapper">
           <select id="account-select" v-model="selectedAccount" class="stk-input shadow-sm" style="min-width: 220px; font-weight: 600;">
            <option v-for="account in accounts" :key="account.id || account.accountNo" :value="account.id || account.accountNo">
              {{ account.id || account.accountNo }} {{ account.name ? '- ' + account.name : '' }}
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
                    <h5 class="text-uppercase fw-bold mb-2 ls-1" style="font-size: 0.8rem; letter-spacing: 1px; color: #94a3b8;">Net Asset Value</h5>
                    <h2 class="display-5 fw-bold mb-0 nav-glow" style="color: #00f2fe;">{{ formatNumber(accountBalance.netAssetValue) }} <span class="fs-5" style="color: #94a3b8;">VND</span></h2>
                 </div>
               </div>
             </div>

             <!-- Detailed Metrics -->
             <div class="col-md-6 col-lg-4">
                <div class="stk-panel h-100 detail-card">
                  <div class="card-body p-4">
                    <h5 class="card-title fw-bold mb-4" style="font-size: 0.95rem; font-family: 'Outfit', sans-serif; color: #ffffff;"><i class="fa-solid fa-money-bill-wave me-2 text-primary"></i>Cash Assets</h5>
                    <div class="d-flex justify-content-between mb-3 item-row">
                      <span style="color: #94a3b8;">Total Cash</span>
                      <span class="fw-semibold" style="color: #ffffff;">{{ formatNumber(accountBalance.totalCash) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-3 item-row">
                      <span style="color: #94a3b8;">Withdrawable</span>
                      <span class="fw-semibold" style="color: #ffffff;">{{ formatNumber(accountBalance.withdrawableCash) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-0 item-row">
                      <span style="color: #94a3b8;">Deposit Interest</span>
                      <span class="fw-semibold text-success">+{{ formatNumber(accountBalance.depositInterest) }}</span>
                    </div>
                  </div>
                </div>
             </div>

             <div class="col-md-6 col-lg-4">
                <div class="stk-panel h-100 detail-card">
                  <div class="card-body p-4">
                    <h5 class="card-title fw-bold mb-4" style="font-size: 0.95rem; font-family: 'Outfit', sans-serif; color: #ffffff;"><i class="fa-solid fa-chart-line me-2 text-primary"></i>Trading Power</h5>
                    <div class="d-flex justify-content-between mb-3 item-row">
                      <span style="color: #94a3b8;">Purchasing Power</span>
                      <span class="fw-semibold" style="color: #ffffff;">{{ formatNumber(accountBalance.purchasingPower) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-3 item-row">
                      <span style="color: #94a3b8;">Marginable Amt</span>
                      <span class="fw-semibold" style="color: #ffffff;">{{ formatNumber(accountBalance.marginableAmount) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-0 item-row">
                      <span style="color: #94a3b8;">Stock Value</span>
                      <span class="fw-semibold" style="color: #ffffff;">{{ formatNumber(accountBalance.stockValue) }}</span>
                    </div>
                  </div>
                </div>
             </div>

              <div class="col-md-6 col-lg-4">
                <div class="stk-panel h-100 detail-card">
                  <div class="card-body p-4">
                    <h5 class="card-title fw-bold mb-4" style="font-size: 0.95rem; font-family: 'Outfit', sans-serif; color: #ffffff;"><i class="fa-solid fa-shield-halved me-2 text-primary"></i>Security & Debt</h5>
                    <div class="d-flex justify-content-between mb-3 item-row">
                      <span style="color: #94a3b8;">Secure Amount</span>
                      <span class="fw-semibold" style="color: #ffffff;">{{ formatNumber(accountBalance.secureAmount) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-3 item-row">
                      <span style="color: #94a3b8;">Receiving Amt</span>
                      <span class="fw-semibold" style="color: #ffffff;">{{ formatNumber(accountBalance.receivingAmount) }}</span>
                    </div>
                     <div class="d-flex justify-content-between mb-0 item-row">
                      <span style="color: #94a3b8;">Total Debt</span>
                      <span class="fw-semibold text-danger">{{ formatNumber(accountBalance.totalDebt) }}</span>
                    </div>
                  </div>
                </div>
              </div>

             <!-- Open Position Deals inside Overview Tab -->
             <div class="col-12 mt-4">
               <div class="stk-panel">
                 <div class="stk-header d-flex justify-content-between align-items-center">
                   <h4 class="stk-header__title m-0" style="font-size: 1.05rem; color: #ffffff;">
                     <i class="fa-solid fa-briefcase me-2 text-primary"></i>Danh Mục Cổ Phiếu Nắm Giữ (Holdings)
                   </h4>
                   <span class="badge bg-primary bg-opacity-25 text-primary px-3 py-2" style="font-size: 0.78rem;">
                     {{ deals.length }} mã trong danh mục
                   </span>
                 </div>
                 <div class="stk-section p-0">
                   <div v-if="deals.length > 0" class="stk-table-wrap table-responsive">
                      <table class="stk-table align-middle m-0">
                        <thead>
                          <tr>
                            <th class="stk-th">Mã CP</th>
                            <th class="stk-th text-center">Khối lượng</th>
                            <th class="stk-th text-end">Giá vốn TB</th>
                            <th class="stk-th text-end">Giá hiện tại</th>
                            <th class="stk-th text-end">Lãi / Lỗ tạm tính</th>
                            <th class="stk-th text-center">Thao tác</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="deal in deals" :key="deal.id || deal.dealId || deal.symbol" class="stk-row">
                             <td class="stk-td fw-bold" style="color: #00f2fe; font-size: 0.95rem;">{{ deal.symbol || deal.stockCode }}</td>
                             <td class="stk-td text-center" style="color: #e2e8f0; font-weight: 600;">{{ formatNumber(deal.openQuantity ?? deal.quantity ?? 0) }}</td>
                             <td class="stk-td text-end" style="color: #94a3b8;">{{ formatNumber(deal.breakEvenPrice ?? deal.costPrice ?? deal.avgPrice ?? deal.price) }}</td>
                             <td class="stk-td text-end" style="color: #f1f5f9; font-weight: 600;">{{ formatNumber(deal.marketPrice ?? deal.currentPrice ?? deal.price) }}</td>
                             <td class="stk-td text-end fw-bold" :class="(deal.unrealizedProfit ?? deal.pnl ?? 0) >= 0 ? 'text-success' : 'text-danger'">
                               {{ (deal.unrealizedProfit ?? deal.pnl ?? 0) >= 0 ? '+' : '' }}{{ formatNumber(deal.unrealizedProfit ?? deal.pnl ?? 0) }}
                               <span v-if="deal.unrealizedProfitRatio !== undefined" style="font-size: 0.75rem; display: block;">
                                 ({{ (deal.unrealizedProfitRatio * 100).toFixed(2) }}%)
                               </span>
                             </td>
                             <td class="stk-td text-center">
                                <div class="d-inline-flex gap-2">
                                  <button class="stk-btn stk-btn-xxs stk-btn--success" @click="openOrderPopup('Buy', deal.symbol || deal.stockCode)">Mua</button>
                                  <button class="stk-btn stk-btn-xxs stk-btn--danger" @click="openOrderPopup('Sell', deal.symbol || deal.stockCode)">Bán</button>
                                </div>
                             </td>
                          </tr>
                        </tbody>
                      </table>
                   </div>
                   <div v-else class="text-center py-5 text-muted">
                      <i class="fa-solid fa-box-open fs-2 mb-3 d-block text-secondary"></i>
                      Hiện tại chưa có vị thế cổ phiếu nào đang mở trong tài khoản này.
                   </div>
                 </div>
               </div>
             </div>
           </div>
           
            <div v-else-if="isLoading" class="d-flex justify-content-center py-5">
               <div class="spinner-border text-info" role="status">
                 <span class="visually-hidden">Loading...</span>
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
                           <th class="stk-th text-end">Break Even Price</th>
                           <th class="stk-th text-end">Market Price</th>
                           <th class="stk-th text-end">Unrealized Profit</th>
                           <th class="stk-th text-center">Actions</th>
                         </tr>
                       </thead>
                       <tbody>
                         <tr v-for="deal in deals" :key="deal.id || deal.dealId || deal.symbol" class="stk-row">
                            <td class="stk-td fw-bold" style="color: #00f2fe;">{{ deal.symbol || deal.stockCode }}</td>
                            <td class="stk-td text-center" style="color: #e2e8f0;">{{ deal.openQuantity ?? deal.quantity ?? 0 }}</td>
                            <td class="stk-td text-end text-muted">{{ formatNumber(deal.breakEvenPrice ?? deal.costPrice ?? deal.avgPrice ?? deal.price) }}</td>
                            <td class="stk-td text-end text-white">{{ formatNumber(deal.marketPrice ?? deal.currentPrice ?? deal.price) }}</td>
                            <td class="stk-td text-end fw-bold" :class="(deal.unrealizedProfit ?? deal.pnl ?? 0) >= 0 ? 'text-success' : 'text-danger'">
                              {{ (deal.unrealizedProfit ?? deal.pnl ?? 0) >= 0 ? '+' : '' }}{{ formatNumber(deal.unrealizedProfit ?? deal.pnl ?? 0) }}
                              <span v-if="deal.unrealizedProfitRatio !== undefined" style="font-size: 0.75rem; display: block;">
                                ({{ (deal.unrealizedProfitRatio * 100).toFixed(2) }}%)
                              </span>
                            </td>
                            <td class="stk-td text-center">
                               <div class="d-inline-flex gap-2">
                                 <button class="stk-btn stk-btn-xxs stk-btn--success" @click="openOrderPopup('Buy', deal.symbol || deal.stockCode)">Buy</button>
                                 <button class="stk-btn stk-btn-xxs stk-btn--danger" @click="openOrderPopup('Sell', deal.symbol || deal.stockCode)">Sell</button>
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
                             <td class="stk-td font-monospace" style="font-size: 0.8rem; color: #94a3b8;">{{ order.id }}</td>
                             <td class="stk-td fw-bold" style="color: #ffffff;">{{ order.symbol }}</td>
                             <td class="stk-td text-center" style="color: #e2e8f0;">{{ order.quantity }}</td>
                             <td class="stk-td text-end" style="color: #cbd5e1;">{{ formatNumber(order.price) }}</td>
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

       <!-- Order Popup -->
      <div v-if="showOrderPopup" class="modal-backdrop-custom d-flex align-items-center justify-content-center">
        <div class="stk-modal overflow-hidden p-0" style="max-width: 500px; width: 100%;">
           <div class="stk-header p-4 d-flex justify-content-between align-items-center">
              <h5 class="fw-bold mb-0" style="color: #ffffff;"><i class="fa-solid fa-cart-shopping text-primary me-2"></i>Place Order</h5>
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
           <div class="p-3 border-top border-opacity-10 border-dark bg-light d-flex gap-2 justify-content-end">
               <button class="stk-btn stk-btn--outline px-4" @click="closeOrderPopup">Cancel</button>
               <button class="stk-btn stk-btn--primary px-4" @click="placeOrder">Place Order</button>
           </div>
        </div>
      </div>

       <!-- OTP Popup -->
       <div v-if="showOtpPopup" class="modal-backdrop-custom d-flex align-items-center justify-content-center">
          <div class="stk-modal p-4" style="max-width: 450px; width: 100%;">
             <h4 class="fw-bold mb-4 text-dark" style="font-family: 'Outfit', sans-serif;"><i class="fa-solid fa-shield-halved text-primary me-2"></i>Security Verification</h4>
             
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
import AppFooter from './AppFooter.vue';
import JournalComponent from './JournalComponent.vue';
import { ref, onMounted, watch, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useNotification } from '@kyvg/vue3-notification';

export default {
  name: 'MyPortfolio',
  components: {
    AppFooter,
    JournalComponent
  },
  setup() {
    const { notify } = useNotification();
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
    const tabs = ref(['Balance Account', 'Journal', 'Deals', 'Orders']);
    
    // Data refs
    const orders = ref([]);
    const ordersErrorMessage = ref('');
    const isLoading = ref(false);
    
    // Order Popup
    const showOrderPopup = ref(false);
    const selectedStock = ref('');
    const orderSide = ref('');
    const orderPrice = ref(null);
    const stocks = ref([]);
    const orderType = ref('LO');
    const orderQuantity = ref(100);

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

    const fetchOrders = async (accountNumber) => {
      isLoading.value = true;
      ordersErrorMessage.value = '';
      const token = localStorage.getItem('token');
      if (!token) return;

      try {
        const response = await fetch(`/dnse-order-service/v2/orders?accountNo=${accountNumber}`, {
          headers: { 'Authorization': `Bearer ${token}` },
          signal: AbortSignal.timeout(6000)
        });

        if (response.ok) {
          const data = await response.json();
          orders.value = data.orders || [];
        } else {
          orders.value = [];
          ordersErrorMessage.value = 'Không thể tải lịch sử lệnh từ DNSE.';
        }
      } catch (error) {
        orders.value = [];
        ordersErrorMessage.value = 'Lỗi kết nối khi tải lịch sử lệnh.';
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
          signal: AbortSignal.timeout(6000)
        });

        if (response.ok) {
          const data = await response.json();
          accountBalance.value = data;
        } else {
          accountBalance.value = null;
          balanceErrorMessage.value = 'Không thể tải số dư tài khoản DNSE.';
        }
      } catch (error) {
        accountBalance.value = null;
        balanceErrorMessage.value = 'Lỗi kết nối khi tải số dư tài khoản.';
      } finally {
        isLoading.value = false;
      }
    };

    const fetchDeals = async (accountNumber) => {
      isLoading.value = true;
      dealsErrorMessage.value = '';
      const token = localStorage.getItem('token');
      if (!token) {
        isLoading.value = false;
        return;
      }

      try {
        const response = await fetch(`/dnse-deal-service/deals?accountNo=${encodeURIComponent(accountNumber)}`, {
          headers: { 'Authorization': `Bearer ${token}` },
          signal: AbortSignal.timeout(6000)
        });

        if (response.ok) {
          const data = await response.json();
          deals.value = Array.isArray(data?.deals) ? data.deals : (Array.isArray(data?.data) ? data.data : (Array.isArray(data) ? data : []));
        } else {
          deals.value = [];
          dealsErrorMessage.value = 'Không thể tải danh sách cổ phiếu từ DNSE.';
        }
      } catch (error) {
        deals.value = [];
        dealsErrorMessage.value = 'Lỗi kết nối khi tải danh mục cổ phiếu.';
        console.error(error);
      } finally {
        isLoading.value = false;
      }
    };

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
                notify({ type: 'error', title: 'Error', text: 'Please input the OTP' });
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
                    notify({ type: 'error', title: 'Error', text: `Authentication failed: ${errorData.message || 'Unknown error'}` });
                }
            } catch (error) {
                console.error(error);
                notify({ type: 'error', title: 'Error', text: 'Authentication error.' });
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
                notify({ type: 'error', title: 'Error', text: `Order failed: ${errorData.message || 'Unknown error'}` });
            }
        } catch (error) {
            console.error(error);
            notify({ type: 'error', title: 'Error', text: 'Order placement error.' });
        } finally {
            pendingOrder.value = false;
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
          accounts.value = Array.isArray(data.accounts) ? data.accounts : (Array.isArray(data) ? data : []);
          const defaultAccount = data.default;
          let defaultAccId = '';
          if (defaultAccount && typeof defaultAccount === 'object' && defaultAccount.id) {
            defaultAccId = defaultAccount.id;
          } else if (typeof defaultAccount === 'string' && defaultAccount) {
            defaultAccId = defaultAccount;
          } else if (accounts.value.length > 0) {
            defaultAccId = accounts.value[0].id || accounts.value[0].accountNo;
          }

          if (!defaultAccId) {
            try {
              const userStorage = JSON.parse(localStorage.getItem('userInfo') || '{}');
              defaultAccId = userStorage.accountNo || userStorage.accounts?.[0]?.accountNo || userStorage.accounts?.[0]?.id;
            } catch (e) {
              console.warn('Error reading userInfo fallback:', e);
            }
          }

          if (defaultAccId) {
            selectedAccount.value = defaultAccId;
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
      }
    });

    return {
      accounts, selectedAccount, accountBalance, deals, orders,
      errorMessage, balanceErrorMessage,
      isLoading, isMenuOpen, toggleMenu, isLoggedIn, userInfo, showDropdown, logout,
      selectedTab, tabs, formatNumber,
      // Order
      showOrderPopup, selectedStock, orderSide, orderPrice, stocks, openOrderPopup, closeOrderPopup, placeOrder,
      orderType, orderQuantity,
      // OTP
      showOtpPopup, closeOtpPopup, selectedAuthMethod, handleOtpSubmit, otpInput
    };
  }
};
</script>

<style scoped>
/* ==================================== */
/*  PORTFOLIO PAGE – Dark Cyber UI      */
/* ==================================== */

.stk-page {
  background: #0a0d14;
  min-height: 100vh;
  color: #e2e8f0;
}

.my-portfolio {
  max-width: 1400px;
  margin: 0 auto;
}

/* ---------- TABS GLASS ---------- */
.stk-tabs-glass {
  display: inline-flex;
  gap: 4px;
  background: rgba(18, 24, 38, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(16px);
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
  color: #00f2fe;
  background: rgba(0, 242, 254, 0.08);
}
.stk-tab-pill.active {
  color: #0a0d14 !important;
  font-weight: 700;
  background: linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%) !important;
  box-shadow: 0 4px 14px rgba(0, 242, 254, 0.35) !important;
}

/* ---------- PANEL ---------- */
.stk-panel {
  background: rgba(18, 24, 38, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  overflow: hidden;
  margin-bottom: 20px;
  backdrop-filter: blur(16px);
}

/* ---------- BALANCE CARD ---------- */
.stk-balance-card {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.08) 0%, rgba(59, 130, 246, 0.08) 100%);
  border: 1px solid rgba(0, 242, 254, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  margin-bottom: 20px;
  backdrop-filter: blur(16px);
}

/* ---------- HEADER ---------- */
.stk-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 24px;
  background: rgba(10, 13, 20, 0.85);
  color: #ffffff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.stk-header__title {
  font-size: 1.15rem;
  font-weight: 700;
  margin: 0;
  line-height: 1.3;
  font-family: 'Outfit', sans-serif;
  color: #ffffff;
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
  border-color: rgba(0, 242, 254, 0.3) !important;
  box-shadow: 0 8px 24px rgba(0, 242, 254, 0.1) !important;
}
.item-row {
  border-bottom: 1px dashed rgba(255, 255, 255, 0.08);
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
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  font-size: 0.88rem;
  color: #ffffff;
  background: rgba(10, 13, 20, 0.8);
  transition: border-color 0.2s, box-shadow 0.2s, background-color 0.2s;
  outline: none;
}
.stk-input:focus {
  border-color: #00f2fe;
  box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.15);
  background: rgba(10, 13, 20, 0.95);
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
  background: linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%);
  color: #0a0d14;
  border: none;
  font-weight: 700;
}
.stk-btn--primary:hover {
  box-shadow: 0 4px 14px rgba(0, 242, 254, 0.4);
  transform: translateY(-1px);
}
.stk-btn--success {
  background: rgba(0, 245, 160, 0.15);
  color: #00f5a0;
  border: 1px solid rgba(0, 245, 160, 0.3);
}
.stk-btn--success:hover {
  background: #00f5a0;
  color: #0a0d14;
}
.stk-btn--danger {
  background: rgba(255, 75, 114, 0.15);
  color: #ff4b72;
  border: 1px solid rgba(255, 75, 114, 0.3);
}
.stk-btn--danger:hover {
  background: #ff4b72;
  color: #ffffff;
}
.stk-btn--outline {
  background: transparent;
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.15);
}
.stk-btn--outline:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.25);
}

/* ---------- TABLE ---------- */
.stk-table-wrap {
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  background: rgba(18, 24, 38, 0.75);
  backdrop-filter: blur(16px);
}
.stk-table-wrap::-webkit-scrollbar {
  height: 6px;
}
.stk-table-wrap::-webkit-scrollbar-track {
  background: rgba(10, 13, 20, 0.6);
  border-radius: 4px;
}
.stk-table-wrap::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
}
.stk-table-wrap::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 242, 254, 0.4);
}
.stk-table {
  width: 100%;
  min-width: 860px;
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
  color: #64748b;
  background: rgba(10, 13, 20, 0.9);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: sticky;
  top: 0;
  z-index: 2;
}
.stk-td {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  vertical-align: middle;
  color: #e2e8f0;
}
.stk-row {
  cursor: pointer;
  transition: background 0.15s ease;
}
.stk-row:hover {
  background: rgba(0, 242, 254, 0.04);
}

/* ---------- MODALS ---------- */
.modal-backdrop-custom {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.75);
  z-index: 1050;
  backdrop-filter: blur(8px);
}
.stk-modal {
  background: #111726;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
  max-width: 500px;
  width: 90%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  color: #e2e8f0;
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
  background: rgba(10, 13, 20, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
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
  background: rgba(0, 245, 160, 0.15);
  color: #00f5a0;
  border: 1px solid rgba(0, 245, 160, 0.3);
}
.stk-type-badge.apartment {
  background: rgba(255, 75, 114, 0.15);
  color: #ff4b72;
  border: 1px solid rgba(255, 75, 114, 0.3);
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
  background: rgba(0, 245, 160, 0.15);
  color: #00f5a0;
  border-color: rgba(0, 245, 160, 0.3);
}
.stk-signal-pill.sell {
  background: rgba(255, 75, 114, 0.15);
  color: #ff4b72;
  border-color: rgba(255, 75, 114, 0.3);
}
.bg-primary-glow {
  background: rgba(0, 242, 254, 0.12);
  border: 1px solid rgba(0, 242, 254, 0.25);
  color: #00f2fe;
}

.nav-glow {
  text-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
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

/* ========================================================== */
/*  RESPONSIVE STYLES (Smartphones & Tablets)                 */
/* ========================================================== */
@media (max-width: 991px) {
  .stk-container {
    padding: 0 14px !important;
  }
}

@media (max-width: 768px) {
  .stk-tabs {
    overflow-x: auto !important;
    flex-wrap: nowrap !important;
    padding-bottom: 6px !important;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }
  .stk-tabs::-webkit-scrollbar {
    display: none;
  }

  .stk-tab {
    flex-shrink: 0 !important;
    font-size: 0.8rem !important;
    padding: 8px 14px !important;
  }

  .stk-header {
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 12px !important;
    padding: 16px !important;
  }

  .stk-table-wrap {
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch;
  }

  .stk-table {
    min-width: 860px !important;
    font-size: 0.82rem !important;
  }

  .modal-dialog {
    margin: 10px auto !important;
    max-width: 95% !important;
  }
}
</style>