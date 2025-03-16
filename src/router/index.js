import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../components/HomeView.vue'; // I will create this
import LoginPage from '../components/Login.vue';
import MyPortfolio from '../components/MyPortfolio.vue';
import StockVn from '../components/StockVn.vue';

const routes = [
  {
    path: '/stockvn',
    name: 'StockVn',
    component: StockVn,
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
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;