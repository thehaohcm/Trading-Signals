<template>
  <div id="app" class="d-flex flex-column min-vh-100">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark d-flex">
      <div class="container-fluid">
        <a class="navbar-brand" href="#">
          <img src="../assets/logo.png" alt="Vue logo" style="width: 40px; margin-left: 25px;">
        </a>
        <button class="navbar-toggler" type="button" @click="toggleMenu" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav" :class="{ show: isMenuOpen }">
          <ul class="navbar-nav">
            <li class="nav-item">
              <router-link to="/" class="nav-link" :class="{ active: activeTab === 'Crypto' }" @click="activeTab = 'Crypto'">
                <img :src="require('../assets/btc.svg')" style="width: 20px; height: 20px; margin-right: 5px;" />
                Crypto
              </router-link>
            </li>
            <li class="nav-item">
              <router-link to="/" class="nav-link" :class="{ active: activeTab === 'Stock VN' }" @click="activeTab = 'Stock VN'">
                <img :src="require('../assets/stock.svg')" style="width: 20px; height: 20px; margin-right: 5px;" />
                Stock VN
              </router-link>
            </li>
            <li class="nav-item">
              <router-link to="/" class="nav-link" :class="{ active: activeTab === 'Gold' }" @click="activeTab = 'Gold'">
                <img :src="require('../assets/gold.svg')" style="width: 20px; height: 20px; margin-right: 5px;" />
                Gold
              </router-link>
            </li>
            <li class="nav-item" v-if="isLoggedIn">
              <router-link to="/my-portfolio" class="nav-link" :class="{ active: activeTab === 'MyPortfolio' }" @click="activeTab = 'MyPortfolio'">
                <img :src="require('../assets/portfolio.svg')" style="width: 20px; height: 20px; margin-right: 5px;" />
                My Portfolio
              </router-link>
            </li>
          </ul>
        </div>
          <!-- Login Button / User Greeting -->
          <div class="ms-auto">
              <template v-if="isLoggedIn && userInfo">
                  <span class="text-white">{{ userInfo.name }} ({{ userInfo.custodyCode }})</span>
              </template>
              <template v-else>
                  <router-link to="/login" class="btn btn-outline-light">Login</router-link>
              </template>
          </div>
      </div>
    </nav>
  <div class="my-portfolio container mt-4 flex-grow-1">
    <h1>My Portfolio</h1>

    <div class="mb-3">
      <label for="account-select" class="form-label">Select Account:</label>
      <select id="account-select" v-model="selectedAccount" class="form-select">
        <option v-for="account in accounts" :key="account.id" :value="account.id">
          {{ account.id }} - {{ account.name }}
        </option>
      </select>
    </div>
    <div v-if="errorMessage" class="alert alert-danger">
      {{ errorMessage }}
    </div>

    <div v-if="accountBalance" class="card mb-4">
      <div class="card-body">
        <h2 class="card-title">Account Balance</h2>
        <div class="account-info">
          <div class="info-item"><strong>Total Cash:</strong> {{ formatNumber(accountBalance.totalCash) }}</div>
          <div class="info-item"><strong>Deposit Interest:</strong> {{ formatNumber(accountBalance.depositInterest) }}</div>
          <div class="info-item"><strong>Stock Value:</strong> {{ formatNumber(accountBalance.stockValue) }}</div>
          <div class="info-item"><strong>Marginable Amount:</strong> {{ formatNumber(accountBalance.marginableAmount) }}</div>
          <div class="info-item"><strong>Total Debt:</strong> {{ formatNumber(accountBalance.totalDebt) }}</div>
          <div class="info-item"><strong>Net Asset Value:</strong> {{ formatNumber(accountBalance.netAssetValue) }}</div>
          <div class="info-item"><strong>Receiving Amount:</strong> {{ formatNumber(accountBalance.receivingAmount) }}</div>
          <div class="info-item"><strong>Secure Amount:</strong> {{ formatNumber(accountBalance.secureAmount) }}</div>
          <div class="info-item"><strong>Deposit Fee Amount:</strong> {{ formatNumber(accountBalance.depositFeeAmount) }}</div>
          <div class="info-item"><strong>Withdrawable Cash:</strong> {{ formatNumber(accountBalance.withdrawableCash) }}</div>
          <div class="info-item"><strong>Purchasing Power:</strong> {{ formatNumber(accountBalance.purchasingPower) }}</div>
        </div>
      </div>
    </div>
    <div v-if="balanceErrorMessage" class="alert alert-danger">
      <p>{{balanceErrorMessage}}</p>
    </div>

    <div v-if="deals.length > 0">
      <h2>Deals</h2>
      <table class="table table-striped table-hover">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Open Quantity</th>
            <th>Unrealized Profit</th>
            <th>Break Even Price</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="deal in deals" :key="deal.id">
            <td>{{ deal.symbol }}</td>
            <td>{{ deal.openQuantity }}</td>
            <td>{{ formatNumber(deal.unrealizedProfit) }}</td>
            <td>{{ formatNumber(deal.breakEvenPrice) }}</td>
            <td>
              <button class="btn btn-success btn-sm" @click="openOrderPopup('Buy', deal.symbol)">Buy</button>
              <button class="btn btn-danger btn-sm" @click="openOrderPopup('Sell', deal.symbol)">Sell</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Order Popup -->
    <div v-if="showOrderPopup" class="order-popup">
      <div class="order-popup-content">
        <h2>Place Order</h2>
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
          <label for="price" class="form-label">Price:</label>
          <input type="number" id="price" v-model="orderPrice" class="form-control">
        </div>
        <button class="btn btn-primary" @click="placeOrder">Apply</button>
        <button class="btn btn-secondary" @click="closeOrderPopup">Cancel</button>
      </div>
    </div>
    <div v-else-if="dealsErrorMessage" class="alert alert-danger">
        <p>{{dealsErrorMessage}}</p>
    </div>
    <div v-else>
        <p>Loading deals...</p>
    </div>
  </div>
    <footer class="mt-5 text-center text-white bg-dark py-3">Copyright © by Nguyen The Hao 2025. All rights reserved.</footer>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue';

export default {
  name: 'MyPortfolio',
  setup() {
    const accounts = ref([]);
    const selectedAccount = ref('');
    const accountBalance = ref(null);
    const deals = ref([]);
    const errorMessage = ref('');
    const balanceErrorMessage = ref('');
    const dealsErrorMessage = ref('');
    const isMenuOpen = ref(false);
    const userInfo = ref(null);
    const activeTab = ref('MyPortfolio')
    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value;
    };

    const fetchAccountBalance = async (accountNumber) => {
      balanceErrorMessage.value = '';
      const token = localStorage.getItem('token');
      if (!token) {
        balanceErrorMessage.value = 'Not authorized.';
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
      }
    };

    const fetchDeals = async (accountNumber) => {
        dealsErrorMessage.value = '';
        const token = localStorage.getItem('token');
        if(!token){
            dealsErrorMessage.value = 'Not authorized.';
            return;
        }

        try {
            const response = await fetch(`/dnse-deal-service/deals?accountNo=${accountNumber}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if(response.ok){
                const data = await response.json();
                deals.value = data.deals;
                console.log('Deals data:', data); // Log the deals data
            } else {
                dealsErrorMessage.value = 'Failed to fetch deals.';
                console.error('Failed to fetch deals. Status:', response.status, 'Response:', await response.text()); // Log the error
            }
        } catch (error){
            dealsErrorMessage.value = 'An error occurred while fetching deals.';
            console.error('Error fetching deals:', error); // Log the error
        }
    }

    const fetchUserInfo = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const response = await fetch('https://services.entrade.com.vn/dnse-user-service/api/me', {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          });
          const data = await response.json();
          if (response.ok) {
            userInfo.value = data;
          } else {
            console.error('Failed to fetch user info:', data);
            // Optionally clear the token if it's invalid
            localStorage.removeItem('token');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('userInfo');
          }
        } catch (error) {
          console.error('Error fetching user info:', error);
        }
      }
    };

    onMounted(async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        errorMessage.value = 'Not authorized.';
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
      await fetchUserInfo();
    });

    watch(selectedAccount, (newAccountNumber) => {
      if (newAccountNumber) {
        fetchAccountBalance(newAccountNumber);
        fetchDeals(newAccountNumber);
      }
    });

    const isLoggedIn = computed(() => {
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
      // Placeholder for order placement logic
      closeOrderPopup();
    }

    onMounted(async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        errorMessage.value = 'Not authorized.';
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
      await fetchUserInfo();
      await fetchStocks(); // Fetch the stock list when the component is mounted
    });

    watch(selectedAccount, (newAccountNumber) => {
      if (newAccountNumber) {
        fetchAccountBalance(newAccountNumber);
        fetchDeals(newAccountNumber);
      }
    });



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
      orderType
    };
  },
};
</script>

<style scoped>
.order-popup {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.order-popup-content {
  background-color: white;
  padding: 20px;
  border-radius: 5px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  min-width: 300px;
}
</style>

<style>
/* Remove default styling */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 0; /* Remove top margin */
}

/* Tab styling */
.nav-link {
  cursor: pointer;
  transition: background-color 0.3s ease;
  border-radius: 0.25rem;
  margin: 0 2px;
}

.nav-item {
  width: 150px; /* Adjust as needed */
  text-align: center;
}

.nav-link:hover {
  background-color: #2d3748; /* Dark background for active tab */
  color: white;
  border-bottom: 2px solid #6cb2eb; /* Highlight active tab */
  font-weight: bolder;
}

.table-light {
  background-color: #edf2f7;
  text-align: left;
}

.price-div{
  font-weight:1000;
  color:#2c3e50;
  float: right;
}

/* Stock VN section */
.card {
  border: none;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Add some padding to the footer */
footer {
  padding: 20px 0;
}
</style>

<style scoped>
.card-title {
  text-align: center;
}
.account-info {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.info-item {
  min-width: 300px; /* Adjust as needed */
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  text-align: right;
  /* Add other styling for individual items if necessary */
}
.info-item strong {
  display: inline-block;
  text-align: left;
}
</style>