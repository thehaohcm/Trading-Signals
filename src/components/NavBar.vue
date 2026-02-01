<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark d-flex">
    <div class="container-fluid">
      <router-link class="navbar-brand" to="/">
        <img :src="logoImg" alt="Vue logo" style="width: 40px; margin-left: 25px;">
      </router-link>
      <button class="navbar-toggler" type="button" @click="toggleMenu" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav" :class="{ show: isMenuOpen }">
        <ul class="navbar-nav">
          <li class="nav-item">
            <router-link to="/crypto" class="nav-link">
              <img :src="btcImg" style="width: 20px; height: 20px; margin-right: 5px;" />
              Crypto
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/stock" class="nav-link">
              <img :src="stockImg" style="width: 20px; height: 20px; margin-right: 5px;" />
              Stock
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/commodities" class="nav-link" >
              <img :src="goldImg" style="width: 20px; height: 20px; margin-right: 5px;" />
              Commodities
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/forex" class="nav-link">
              <img :src="forexImg" style="width: 20px; height: 20px; margin-right: 5px;" />
              Forex
            </router-link>
          </li>
          <li class="nav-item" v-if="isLoggedIn">
            <router-link to="/journal" class="nav-link">
              Journal
            </router-link>
          </li>
          <li class="nav-item" v-if="isLoggedIn">
            <router-link to="/community" class="nav-link">
              Community
            </router-link>
          </li>
          <li class="nav-item" v-if="isLoggedIn">
            <router-link to="/my-portfolio" class="nav-link">
              <img :src="portfolioImg" style="width: 20px; height: 20px; margin-right: 5px;" />
              My Portfolio
            </router-link>
          </li>
        </ul>
      </div>
        <!-- Login Button / User Greeting -->
        <div class="ms-auto">
          <template v-if="isLoggedIn && userInfo">
            <div class="dropdown" @mouseover="showDropdown = true" @mouseleave="showDropdown = false">
              <span class="text-white user-info">{{ userInfo.name }} ({{ userInfo.custodyCode }})</span>
            <div v-if="showDropdown" class="dropdown-content">
              <a @click="logout"  style="cursor: pointer;">Log out</a>
            </div>
            </div>
          </template>
          <template v-else>
            <router-link to="/login" class="btn btn-outline-light">Login</router-link>
          </template>
        </div>
    </div>
  </nav>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import logoImg from '../assets/logo.png';
import btcImg from '../assets/btc.svg';
import stockImg from '../assets/stock.svg';
import goldImg from '../assets/gold.svg';
import silverImg from '../assets/silver.svg';
import forexImg from '../assets/forex.svg';
import portfolioImg from '../assets/portfolio.svg';

export default {
  props: {
  },
  setup() {
    const router = useRouter();
    var userInfo = ref(null);
    const isMenuOpen = ref(false);
    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value;
    };
    const showDropdown = ref(false);
    
    onMounted(() => {
      fetchUserInfo(); // Fetch user info on mount
    });

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
            localStorage.setItem('userInfo', JSON.stringify(data));
          }
        } catch (error) {
          console.error('Error fetching user info:', error);
        }
      }
    };

    const logout = () => {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('userInfo');
      userInfo.value = null;
      router.push('/');
    }


    const isLoggedIn = computed(() => {
      try {
        const loggedIn = userInfo.value && userInfo.value.custodyCode;
        return loggedIn;
      } catch (error) {
        console.error('Error parsing userInfo:', error);
      }
      return false; // Return false if parsing fails
    });

    return {
      isMenuOpen,
      toggleMenu,
      showDropdown,
      logout,
      isLoggedIn,
      userInfo,
      logoImg,
      btcImg,
      stockImg,
      goldImg,
      silverImg,
      forexImg,
      portfolioImg
    };
  },
};
</script>

<style scoped>
/* Add scoped to limit the styles to this component */
.nav-link {
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 0.5rem;
  margin: 0 5px;
  padding: 10px 15px;
  display: flex;
  align-items: center; /* Vertically center icon and text */
  justify-content: center;
}

.nav-item {
  /* removed fixed width to allow flexible layout */
  margin: 0 5px;
}

.nav-link:hover {
  background-color: #2d3748; /* Dark background for active tab */
  color: #6cb2eb; /* Highlight text color */
  transform: translateY(-2px);
  /* removed border-bottom to avoid layout shift, using color/bg instead */
}

/* Active link style (if vue-router adds router-link-active class) */
.router-link-active {
  background-color: #2d3748;
  color: #6cb2eb !important;
  font-weight: bold;
}

.user-info {
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.user-info:hover {
  background-color: rgba(255,255,255,0.1);
}

.dropdown {
  position: relative;
  display: inline-block;
}

.dropdown-content {
  display: none;
  position: absolute;
  background-color: #fff;
  min-width: 160px;
  box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
  z-index: 1000;
  right: 0; /* Align to the right */
  border-radius: 4px;
  overflow: hidden;
}

.dropdown-content a {
  color: #333;
  padding: 12px 16px;
  text-decoration: none;
  display: block;
  text-align: left;
  transition: background-color 0.2s;
}

.dropdown-content a:hover {
  background-color: #f1f1f1;
}

.dropdown:hover .dropdown-content {
  display: block;
}

@media (max-width: 991px) {
  .nav-item {
    margin: 5px 0;
    width: 100%;
    text-align: left;
  }
  
  .nav-link {
    justify-content: flex-start;
    padding: 12px 20px;
  }
}
</style>