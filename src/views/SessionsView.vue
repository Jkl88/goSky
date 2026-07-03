<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import QrBlock from '@/components/QrBlock.vue';
import { sessionClientLabel } from '@/composables/useSessionLabel';
import {
  createQrLoginLink,
  formatDateTime,
  getQrLoginLinkStatus,
  listUserSessions,
  parseApiDateTime,
  revokeUserSession,
  type UserRecord,
  type UserSessionRecord,
} from '@/services/api';

const props = defineProps<{
  user: UserRecord | null;
  authReady: boolean;
}>();

const emit = defineEmits<{ login: []; 'auth-changed': [] }>();

const router = useRouter();
const sessions = ref<UserSessionRecord[]>([]);
const loading = ref(true);
const error = ref('');
const revokingId = ref(0);
const snack = ref('');
const snackVisible = ref(false);

const qrDialog = ref(false);
const qrLoading = ref(false);
const qrUrl = ref('');
const qrLinkId = ref(0);
const qrRemaining = ref(0);
let qrCountdownTimer: ReturnType<typeof setInterval> | null = null;
let qrStatusTimer: ReturnType<typeof setInterval> | null = null;
let qrExpiresAtMs = 0;

function stopQrTimers() {
  if (qrCountdownTimer) clearInterval(qrCountdownTimer);
  if (qrStatusTimer) clearInterval(qrStatusTimer);
  qrCountdownTimer = null;
  qrStatusTimer = null;
}

function closeQrDialog() {
  stopQrTimers();
  qrDialog.value = false;
  qrUrl.value = '';
  qrLinkId.value = 0;
}

function updateQrCountdown() {
  const remainingMs = qrExpiresAtMs - Date.now();
  qrRemaining.value = Math.max(0, Math.ceil(remainingMs / 1000));
  if (remainingMs <= 0) {
    closeQrDialog();
    showSnack('Время QR-кода истекло');
  }
}

async function pollQrStatus() {
  if (!qrLinkId.value) return;
  try {
    const status = await getQrLoginLinkStatus(qrLinkId.value);
    if (status.status !== 'pending') {
      stopQrTimers();
      qrDialog.value = false;
      if (status.status === 'missing') {
        showSnack('Вход на другом устройстве выполнен');
      }
    }
  } catch {
    /* ignore poll errors */
  }
}

async function openQrLogin() {
  qrLoading.value = true;
  qrDialog.value = true;
  qrUrl.value = '';
  stopQrTimers();
  try {
    const link = await createQrLoginLink();
    qrUrl.value = link.login_url;
    qrLinkId.value = link.id;
    qrExpiresAtMs = parseApiDateTime(link.expires_at).getTime();
    qrRemaining.value = link.ttl_seconds;
    updateQrCountdown();
    qrCountdownTimer = setInterval(updateQrCountdown, 250);
    qrStatusTimer = setInterval(() => void pollQrStatus(), 1000);
  } catch (e) {
    qrDialog.value = false;
    error.value = e instanceof Error ? e.message : 'Ошибка создания QR';
  } finally {
    qrLoading.value = false;
  }
}

function showSnack(text: string) {
  snack.value = text;
  snackVisible.value = true;
}

async function load() {
  if (!props.user) {
    loading.value = false;
    sessions.value = [];
    return;
  }
  loading.value = true;
  error.value = '';
  try {
    sessions.value = await listUserSessions();
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Ошибка загрузки';
  } finally {
    loading.value = false;
  }
}

async function revoke(session: UserSessionRecord) {
  if (revokingId.value) return;
  revokingId.value = session.id;
  try {
    await revokeUserSession(session.id);
    if (session.current) {
      emit('auth-changed');
      router.push('/');
      return;
    }
    sessions.value = sessions.value.filter((s) => s.id !== session.id);
    showSnack('Сеанс завершён');
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Ошибка';
  } finally {
    revokingId.value = 0;
  }
}

onMounted(load);
watch(() => props.user, load);
onUnmounted(stopQrTimers);
</script>

<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-4 flex-wrap gap-2">
      <h1 class="text-h4 font-weight-bold page-title mb-0">Активные сеансы</h1>
      <v-btn
        v-if="user"
        color="primary"
        prepend-icon="mdi-qrcode"
        size="small"
        @click="openQrLogin"
      >
        Вход по QR
      </v-btn>
    </div>

    <v-alert v-if="authReady && !user" type="info" variant="tonal" rounded="lg" class="mb-4">
      Войдите, чтобы управлять сеансами.
      <template #append>
        <v-btn size="small" color="primary" @click="emit('login')">Войти</v-btn>
      </template>
    </v-alert>

    <v-card v-else-if="user" rounded="xl" class="pa-4 mb-4">
      <p class="text-body-2 text-medium-emphasis mb-4">
        Можно быть авторизованным на нескольких устройствах. Завершите сеансы, которыми больше не пользуетесь.
        Для входа на телефоне откройте «Вход по QR» на устройстве, где вы уже вошли.
      </p>

      <v-progress-linear v-if="loading" indeterminate class="mb-4" />
      <v-alert v-else-if="error" type="error" variant="tonal" rounded="lg" class="mb-4">{{ error }}</v-alert>

      <v-table v-else density="comfortable" class="sessions-table">
        <thead>
          <tr>
            <th>Устройство</th>
            <th class="d-none d-sm-table-cell">IP</th>
            <th class="d-none d-md-table-cell">Создан</th>
            <th>Активность</th>
            <th class="text-right">Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="sessions.length === 0">
            <td colspan="5" class="text-medium-emphasis">Нет активных сеансов</td>
          </tr>
          <tr v-for="session in sessions" :key="session.id">
            <td>
              <div class="d-flex align-center gap-2 flex-wrap">
                {{ sessionClientLabel(session.user_agent) }}
                <v-chip v-if="session.current" size="x-small" color="primary" variant="flat">Текущий</v-chip>
              </div>
            </td>
            <td class="d-none d-sm-table-cell">{{ session.ip_address || '—' }}</td>
            <td class="d-none d-md-table-cell text-no-wrap">{{ formatDateTime(session.created_at) }}</td>
            <td class="text-no-wrap">{{ formatDateTime(session.last_seen_at) }}</td>
            <td class="text-right">
              <v-btn
                size="small"
                variant="text"
                color="error"
                :loading="revokingId === session.id"
                :disabled="session.current && sessions.length === 1"
                @click="revoke(session)"
              >
                Завершить
              </v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

    <v-dialog v-model="qrDialog" max-width="400" @after-leave="closeQrDialog">
      <v-card rounded="xl" title="Вход по QR">
        <v-card-text>
          <p class="text-body-2 text-medium-emphasis mb-3">
            Отсканируйте код на другом устройстве. Код действует {{ qrRemaining }} с.
          </p>
          <v-progress-linear v-if="qrLoading" indeterminate class="mb-4" />
          <QrBlock v-else-if="qrUrl" :value="qrUrl" :size="200" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeQrDialog">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackVisible" :timeout="2500" color="success" location="bottom">
      {{ snack }}
    </v-snackbar>
  </div>
</template>

<style scoped>
.sessions-table {
  font-size: 0.875rem;
}
@media (max-width: 600px) {
  .sessions-table :deep(th),
  .sessions-table :deep(td) {
    padding: 8px 6px !important;
  }
}
</style>
