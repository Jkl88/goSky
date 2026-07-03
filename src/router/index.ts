import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '@/views/HomeView.vue';
import LinksView from '@/views/LinksView.vue';
import LinkViewPage from '@/views/LinkViewPage.vue';
import SessionsView from '@/views/SessionsView.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/links', name: 'links', component: LinksView, meta: { requiresAuth: true } },
    { path: '/sessions', name: 'sessions', component: SessionsView, meta: { requiresAuth: true } },
    { path: '/:slug/vq', name: 'link-view', component: LinkViewPage, props: true },
  ],
});

export default router;
