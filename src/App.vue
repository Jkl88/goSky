<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useDisplay } from 'vuetify';
import { useAppTheme } from '@/composables/useTheme';
import {
  consumeQrLoginLink,
  fetchOAuthSkyConfig,
  getCurrentUser,
  getOAuthSkyStartUrl,
  logout,
  type OAuthSkyConfig,
  type UserRecord,
} from '@/services/api';

const route = useRoute();
const router = useRouter();
const { mobile } = useDisplay();
const { cycleMode, modeIcon, modeLabel } = useAppTheme();

const user = ref<UserRecord | null>(null);
const oauthConfig = ref<OAuthSkyConfig | null>(null);
const authReady = ref(false);
const drawer = ref(false);

const isAuthed = computed(() => !!user.value);

async function loadAuth() {
  try {
    oauthConfig.value = await fetchOAuthSkyConfig();
  } catch {
    oauthConfig.value = { enabled: false, portal_url: '' };
  }

  const params = new URLSearchParams(window.location.search);
  const qrLoginToken = params.get('qrLoginToken');
  if (qrLoginToken) {
    try {
      user.value = await consumeQrLoginLink(qrLoginToken);
      params.delete('qrLoginToken');
      const q = params.toString();
      window.history.replaceState({}, '', window.location.pathname + (q ? `?${q}` : ''));
    } catch {
      user.value = await getCurrentUser();
    }
  } else {
    user.value = await getCurrentUser();
  }

  authReady.value = true;

  if (params.get('oauthsky') === '1' || params.get('oauthsky_error')) {
    params.delete('oauthsky');
    params.delete('oauthsky_error');
    const q = params.toString();
    const path = window.location.pathname + (q ? `?${q}` : '');
    window.history.replaceState({}, '', path);
  }
}

function login() {
  const returnTo = route.fullPath || '/';
  window.location.href = getOAuthSkyStartUrl(returnTo);
}

async function onLogout() {
  await logout();
  if (oauthConfig.value?.enabled && oauthConfig.value.portal_url) {
    const returnTo = encodeURIComponent(window.location.origin);
    window.location.href = `${oauthConfig.value.portal_url}/logout?return_to=${returnTo}`;
    return;
  }
  user.value = null;
  router.push('/');
}

function navTo(path: string) {
  drawer.value = false;
  router.push(path);
}

onMounted(loadAuth);
</script>

<template>
  <v-app>
    <v-app-bar flat border="b" density="comfortable">
      <v-app-bar-nav-icon v-if="mobile" @click="drawer = !drawer" />
      <router-link to="/" class="text-decoration-none d-flex align-center ml-2">
        <v-icon color="primary" class="mr-2">mdi-link-variant</v-icon>
        <span class="text-h6 font-weight-bold text-high-emphasis">goSky</span>
      </router-link>

      <v-spacer />

      <v-btn icon variant="text" :title="modeLabel()" @click="cycleMode">
        <v-icon>{{ modeIcon() }}</v-icon>
      </v-btn>

      <template v-if="authReady">
        <template v-if="isAuthed">
          <v-btn v-if="!mobile" variant="text" to="/links" prepend-icon="mdi-link-multiple">
            Мои ссылки
          </v-btn>
          <v-btn v-if="!mobile" variant="text" to="/sessions" prepend-icon="mdi-devices">
            Сеансы
          </v-btn>
          <v-menu>
            <template #activator="{ props }">
              <v-btn v-bind="props" variant="tonal" class="ml-2 mr-2" size="small">
                <v-icon start>mdi-account-circle</v-icon>
                <span v-if="!mobile">{{ user?.login }}</span>
              </v-btn>
            </template>
            <v-list density="compact">
              <v-list-item v-if="mobile" prepend-icon="mdi-link-multiple" title="Мои ссылки" @click="navTo('/links')" />
              <v-list-item prepend-icon="mdi-devices" title="Активные сеансы" @click="navTo('/sessions')" />
              <v-list-item prepend-icon="mdi-logout" title="Выйти" @click="onLogout" />
            </v-list>
          </v-menu>
        </template>
        <v-btn v-else class="mr-2" color="primary" variant="flat" size="small" @click="login">
          Войти
        </v-btn>
      </template>
      <v-progress-circular v-else indeterminate size="24" class="mr-4" />
    </v-app-bar>

    <v-navigation-drawer v-if="mobile" v-model="drawer" temporary>
      <v-list nav>
        <v-list-item prepend-icon="mdi-home" title="Главная" @click="navTo('/')" />
        <v-list-item
          v-if="isAuthed"
          prepend-icon="mdi-link-multiple"
          title="Мои ссылки"
          @click="navTo('/links')"
        />
        <v-list-item
          v-if="isAuthed"
          prepend-icon="mdi-devices"
          title="Активные сеансы"
          @click="navTo('/sessions')"
        />
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container class="py-6" :class="{ 'px-3': mobile }" style="max-width: 720px">
        <router-view v-slot="{ Component }">
          <component :is="Component" :user="user" :auth-ready="authReady" @login="login" @auth-changed="loadAuth" />
        </router-view>
      </v-container>
    </v-main>

    <v-footer app border="t" class="text-caption text-medium-emphasis justify-center py-3">
      SkyKraft · go.skykraft.su
    </v-footer>
  </v-app>
</template>
