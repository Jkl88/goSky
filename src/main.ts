import 'vuetify/styles';
import '@mdi/font/css/materialdesignicons.css';
import './style.css';

import { registerSW } from 'virtual:pwa-register';
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import vuetify from './plugins/vuetify';

registerSW({ immediate: true });

createApp(App).use(router).use(vuetify).mount('#app');
