<template>
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
            <router-link to="/" class="nav-link">
              <img :src="require('../assets/btc.svg')" style="width: 20px; height: 20px; margin-right: 5px;" />
              Crypto
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/stockvn" class="nav-link">
              <img :src="require('../assets/stock.svg')" style="width: 20px; height: 20px; margin-right: 5px;" />
              Stock VN
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/gold" class="nav-link" >
              <img :src="require('../assets/gold.svg')" style="width: 20px; height: 20px; margin-right: 5px;" />
              Gold
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/forex" class="nav-link">
              <img :src="require('../assets/forex.svg')" style="width: 20px; height: 20px; margin-right: 5px;" />
              Forex
            </router-link>
          </li>
          <li class="nav-item" v-if="isLoggedIn">
            <router-link to="/my-portfolio" class="nav-link">
              <img :src="require('../assets/portfolio.svg')" style="width: 20px; height: 20px; margin-right: 5px;" />
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
  <div class="text-center mt-3">
      <h2>Disclaimer</h2>
      <p>The information and indicators on this website reflect the owner's views and should not be taken as investment
        advice.
      </p>
  </div>
  <hr />
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';

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
      userInfo
    };
  },
};
</script>

<style scoped>
/* Add scoped to limit the styles to this component */
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

.user-info {
  cursor: pointer;
}

.dropdown {
  position: relative;
  display: inline-block;
}

.dropdown-content {
  display: none;
  position: absolute;
  background-color: #f9f9f9;
  min-width: 160px;
  box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
  z-index: 1;
  right: 0; /* Align to the right */
}

.dropdown-content a {
  color: black;
  padding: 12px 16px;
  text-decoration: none;
  display: block;
  text-align: left;
}

.dropdown-content a:hover {
  background-color: #ddd;
}

.dropdown:hover .dropdown-content {
  display: block;
}
</style>