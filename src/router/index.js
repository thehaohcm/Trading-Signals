import { createRouter, createWebHistory } from 'vue-router';
import CryptoView from '../components/CryptoView.vue';
import HomeView from '../components/HomeView.vue';
import LoginPage from '../components/Login.vue';
import MyPortfolio from '../components/MyPortfolio.vue';
import StockMarket from '../components/Stock.vue';
import CommoditiesView from '../components/CommoditiesView.vue';
import ForexView from '../components/ForexView.vue';

import NotFound from '../components/NotFound.vue';

import CommunityView from '../components/CommunityView.vue';

const routes = [
  {
    path: '/forex',
    name: 'Forex',
    component: ForexView,
  },
  {
    path: '/stock',
    name: 'StockMarket',
    component: StockMarket,
  },
  {
    path: '/my-portfolio',
    name: 'MyPortfolio',
    component: MyPortfolio,
    meta: { requiresAuth: true }
  },
  {
    path: '/crypto',
    name: 'Crypto',
    component: CryptoView,
  },
  {
    path: '/',
    name: 'Home',
    component: HomeView,
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginPage,
  },
  {
    path: '/commodities',
    name: 'Commodities',
    component: CommoditiesView,
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
  },

  {
    path: '/community',
    name: 'Community',
    component: CommunityView,
    meta: { requiresAuth: true }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,

});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!token) {
      next({ name: 'Login' });
    } else {
      next();
    }
  } else {
    next();
  }
});

export default router;