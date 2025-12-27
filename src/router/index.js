import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../components/HomeView.vue';
import LoginPage from '../components/Login.vue';
import MyPortfolio from '../components/MyPortfolio.vue';
import StockMarket from '../components/Stock.vue';
import GoldView from '../components/GoldView.vue';
import SilverView from '../components/SilverView.vue';
import ForexView from '../components/ForexView.vue';

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
    name: 'Home',
    component: HomeView,
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginPage,
  },
  {
    path: '/gold',
    name: 'Gold',
    component: GoldView,
  },
  {
    path: '/silver',
    name: 'Silver',
    component: SilverView,
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;