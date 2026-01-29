import { createRouter, createWebHistory } from 'vue-router';
import CryptoView from '../components/CryptoView.vue';
import LoginPage from '../components/Login.vue';
import MyPortfolio from '../components/MyPortfolio.vue';
import StockMarket from '../components/Stock.vue';
import CryptoView from '../components/CryptoView.vue';
import CommoditiesView from '../components/CommoditiesView.vue';
import ForexView from '../components/ForexView.vue';
import NotFound from '../components/NotFound.vue';

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
  },
  {
    path: '/',
    name: 'Crypto',
    component: CryptoView,
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
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;