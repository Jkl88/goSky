<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import CopyableLink from '@/components/CopyableLink.vue';
import LinkActivityChart from '@/components/LinkActivityChart.vue';
import LinkStatsPanel from '@/components/LinkStatsPanel.vue';
import QrBlock from '@/components/QrBlock.vue';
import {
  deleteLink,
  fetchLinkStats,
  formatDateTime,
  getLinkPasswordPageUrl,
  getOAuthSkyStartUrl,
  isPasswordRequiredError,
  updateLink,
  viewLink,
  type LinkStats,
  type ShortLinkView,
} from '@/services/api';

defineProps<{
  user: { id: number } | null;
  authReady: boolean;
}>();

const route = useRoute();
const router = useRouter();

const slug = computed(() => String(route.params.slug || ''));
const data = ref<ShortLinkView | null>(null);
const stats = ref<LinkStats | null>(null);
const loading = ref(true);
const error = ref('');
const saving = ref(false);
const deleting = ref(false);
const deleteOpen = ref(false);

const editTarget = ref('');
const editTitle = ref('');
const editPrivate = ref(false);
const editEnabled = ref(true);
const editHideTargetUrl = ref(false);
const editRedirectPassword = ref('');
const clearRedirectPassword = ref(false);
const ttlPreset = ref('keep');
const customTtlHours = ref<number | null>(null);
const maxClicks = ref<number | null>(null);

const ttlOptions = [
  { title: 'Не менять', value: 'keep' },
  { title: 'Убрать срок', value: 'clear' },
  { title: '1 час', value: '1' },
  { title: '24 часа', value: '24' },
  { title: '7 дней', value: '168' },
  { title: '30 дней', value: '720' },
  { title: 'Своё (часы)', value: 'custom' },
];

async function load() {
  loading.value = true;
  error.value = '';
  stats.value = null;
  try {
    data.value = await viewLink(slug.value);
    editTarget.value = data.value.target_url;
    editTitle.value = data.value.title || '';
    editPrivate.value = data.value.is_private;
    editEnabled.value = data.value.is_enabled;
    editHideTargetUrl.value = data.value.hide_target_url;
    editRedirectPassword.value = '';
    clearRedirectPassword.value = false;
    maxClicks.value = data.value.max_clicks;
    ttlPreset.value = 'keep';

    if (data.value.is_owner) {
      try {
        stats.value = await fetchLinkStats(slug.value);
      } catch {
        /* stats optional */
      }
    }
  } catch (e) {
    const msg = e instanceof Error ? e.message : 'Ошибка';
    if (isPasswordRequiredError(msg)) {
      window.location.href = getLinkPasswordPageUrl(slug.value);
      return;
    }
    if (msg.includes('авторизац') || (msg.includes('401') && !msg.includes('парол'))) {
      const returnTo = encodeURIComponent(route.fullPath);
      window.location.href = getOAuthSkyStartUrl(returnTo);
      return;
    }
    error.value = msg;
  } finally {
    loading.value = false;
  }
}

function buildUpdatePayload() {
  const payload: Parameters<typeof updateLink>[1] = {
    target_url: editTarget.value,
    title: editTitle.value || null,
    is_private: editPrivate.value,
    is_enabled: editEnabled.value,
    hide_target_url: editHideTargetUrl.value,
  };

  if (ttlPreset.value === 'clear') {
    payload.clear_expires_at = true;
  } else if (ttlPreset.value === 'custom' && customTtlHours.value && customTtlHours.value > 0) {
    payload.ttl_hours = customTtlHours.value;
  } else if (ttlPreset.value !== 'keep') {
    payload.ttl_hours = Number(ttlPreset.value);
  }

  if (maxClicks.value && maxClicks.value > 0) {
    payload.max_clicks = maxClicks.value;
  } else {
    payload.clear_max_clicks = true;
  }

  if (!editPrivate.value) {
    if (clearRedirectPassword.value) {
      payload.clear_redirect_password = true;
    } else if (editRedirectPassword.value) {
      if (editRedirectPassword.value.length < 4) {
        throw new Error('Пароль редиректа — минимум 4 символа');
      }
      payload.redirect_password = editRedirectPassword.value;
    }
  }

  return payload;
}

async function save() {
  if (!data.value) return;
  saving.value = true;
  error.value = '';
  try {
    const payload = buildUpdatePayload();
    await updateLink(slug.value, payload);
    await load();
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Ошибка сохранения';
  } finally {
    saving.value = false;
  }
}

async function confirmDelete() {
  deleting.value = true;
  error.value = '';
  try {
    await deleteLink(slug.value);
    deleteOpen.value = false;
    await router.push('/links');
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Ошибка удаления';
  } finally {
    deleting.value = false;
  }
}

onMounted(load);
watch(slug, load);
watch(editPrivate, (isPrivate) => {
  if (isPrivate) {
    editRedirectPassword.value = '';
    clearRedirectPassword.value = false;
  }
});
</script>

<template>
  <div>
    <v-btn variant="text" prepend-icon="mdi-arrow-left" class="mb-2 px-0" @click="router.back()">Назад</v-btn>

    <v-progress-linear v-if="loading" indeterminate class="mb-4" />

    <v-alert v-else-if="error" type="error" variant="tonal" rounded="lg">{{ error }}</v-alert>

    <template v-else-if="data">
      <div class="d-flex align-center flex-wrap gap-2 mb-1">
        <h1 class="text-h5 font-weight-bold page-title mb-0">
          {{ data.title || data.slug }}
        </h1>
        <v-chip v-if="!data.is_active" color="warning" size="small" variant="flat">Неактивна</v-chip>
      </div>
      <div class="text-caption text-medium-emphasis mb-2">
        {{ data.click_count }} переходов · {{ data.is_private ? 'Приватная' : 'Публичная' }}
        <v-chip v-if="data.has_redirect_password" size="x-small" color="secondary" variant="tonal" class="ml-1">
          С паролем
        </v-chip>
        <v-chip v-if="data.hide_target_url" size="x-small" color="info" variant="tonal" class="ml-1">
          Оригинал скрыт
        </v-chip>
        <span v-if="data.max_clicks"> · лимит {{ data.max_clicks }}</span>
        <span v-if="data.expires_at"> · до {{ formatDateTime(data.expires_at) }}</span>
      </div>

      <v-alert v-if="data.inactive_reason" type="warning" variant="tonal" density="compact" class="mb-4" rounded="lg">
        {{ data.inactive_reason }}
      </v-alert>

      <v-card rounded="xl" class="pa-4 mb-4">
        <QrBlock :value="data.short_url" />
        <CopyableLink label="Сокращённая" :url="data.short_url" />
        <CopyableLink
          label="Оригинальная"
          :url="data.target_url"
          :as-link="data.is_owner || !data.hide_target_url"
        />
      </v-card>

      <LinkActivityChart v-if="data.is_owner" :slug="slug" />
      <LinkStatsPanel v-if="stats" :stats="stats" />

      <v-card v-if="data.can_edit" rounded="xl" class="pa-4">
        <v-card-title class="px-0 text-subtitle-1">Редактирование</v-card-title>
        <v-text-field
          v-model="editTarget"
          label="Оригинальная ссылка"
          hint="http, https, ftp, tg, mailto, tel и др."
          persistent-hint
          variant="outlined"
          density="comfortable"
          class="mb-2"
        />
        <v-text-field
          v-model="editTitle"
          label="Название"
          variant="outlined"
          density="comfortable"
          class="mb-2"
        />
        <v-select
          v-model="ttlPreset"
          :items="ttlOptions"
          item-title="title"
          item-value="value"
          label="Срок действия"
          variant="outlined"
          density="comfortable"
          class="mb-2"
        />
        <v-text-field
          v-if="ttlPreset === 'custom'"
          v-model.number="customTtlHours"
          type="number"
          label="Часов до истечения"
          min="1"
          variant="outlined"
          density="comfortable"
          class="mb-2"
        />
        <v-text-field
          v-model.number="maxClicks"
          type="number"
          label="Лимит переходов"
          hint="Пусто — без лимита"
          persistent-hint
          min="1"
          clearable
          variant="outlined"
          density="comfortable"
          class="mb-2"
        />
        <v-switch
          v-model="editEnabled"
          color="primary"
          label="Ссылка включена"
          hide-details
          class="mb-2"
        />
        <v-switch
          v-model="editHideTargetUrl"
          color="primary"
          label="Скрыть оригинал ссылки"
          hint="Гости увидят только домен: https://example.com/********"
          persistent-hint
          hide-details
          class="mb-2"
        />
        <v-switch
          v-model="editPrivate"
          color="primary"
          label="Приватная ссылка"
          hide-details
          class="mb-2"
        />
        <template v-if="!editPrivate">
          <v-alert
            v-if="data.has_redirect_password"
            type="info"
            variant="tonal"
            density="compact"
            rounded="lg"
            class="mb-2"
          >
            Пароль для перехода установлен
          </v-alert>
          <v-text-field
            v-model="editRedirectPassword"
            type="password"
            label="Новый пароль для перехода"
            hint="Оставьте пустым, чтобы не менять"
            persistent-hint
            autocomplete="new-password"
            variant="outlined"
            density="comfortable"
            class="mb-2"
          />
          <v-switch
            v-if="data.has_redirect_password"
            v-model="clearRedirectPassword"
            color="warning"
            label="Снять пароль"
            hide-details
            class="mb-4"
          />
        </template>
        <v-alert v-if="error" type="error" variant="tonal" class="mb-3" rounded="lg">{{ error }}</v-alert>
        <div class="d-flex gap-2">
          <v-btn color="primary" class="flex-grow-1" :loading="saving" rounded="lg" @click="save">Сохранить</v-btn>
          <v-btn color="error" variant="tonal" rounded="lg" @click="deleteOpen = true">Удалить</v-btn>
        </div>
      </v-card>
    </template>

    <v-dialog v-model="deleteOpen" max-width="400">
      <v-card rounded="xl" title="Удалить ссылку?">
        <v-card-text>
          Ссылка <strong>{{ slug }}</strong> перестанет работать безвозвратно.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteOpen = false">Отмена</v-btn>
          <v-btn color="error" :loading="deleting" @click="confirmDelete">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
