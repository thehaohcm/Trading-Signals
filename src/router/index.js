import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../components/HomeView.vue'; // I will create this
import LoginPage from '../components/Login.vue';

const routes = [
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