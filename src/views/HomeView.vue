<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import CopyableLink from '@/components/CopyableLink.vue';
import QrBlock from '@/components/QrBlock.vue';
import { createLink, type ShortLink, type UserRecord } from '@/services/api';

defineProps<{
  user: UserRecord | null;
  authReady: boolean;
}>();

const emit = defineEmits<{ login: []; 'auth-changed': [] }>();

const router = useRouter();

const targetUrl = ref('');
const title = ref('');
const isPrivate = ref(false);
const ttlPreset = ref<string>('none');
const customTtlHours = ref<number | null>(null);
const maxClicks = ref<number | null>(null);
const loading = ref(false);
const error = ref('');
const created = ref<ShortLink | null>(null);

const ttlOptions = [
  { title: 'Без срока', value: 'none' },
  { title: '1 час', value: '1' },
  { title: '24 часа', value: '24' },
  { title: '7 дней', value: '168' },
  { title: '30 дней', value: '720' },
  { title: 'Своё (часы)', value: 'custom' },
];

function resolveTtlHours(): number | null {
  if (ttlPreset.value === 'none') return null;
  if (ttlPreset.value === 'custom') return customTtlHours.value && customTtlHours.value > 0 ? customTtlHours.value : null;
  return Number(ttlPreset.value);
}

async function onSubmit() {
  error.value = '';
  if (!targetUrl.value.trim()) {
    error.value = 'Укажите оригинальную ссылку';
    return;
  }
  if (ttlPreset.value === 'custom' && (!customTtlHours.value || customTtlHours.value < 1)) {
    error.value = 'Укажите срок действия в часах';
    return;
  }

  loading.value = true;
  try {
    created.value = await createLink({
      target_url: targetUrl.value.trim(),
      title: title.value.trim() || null,
      is_private: isPrivate.value,
      ttl_hours: resolveTtlHours(),
      max_clicks: maxClicks.value && maxClicks.value > 0 ? maxClicks.value : null,
    });
    emit('auth-changed');
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Ошибка создания';
  } finally {
    loading.value = false;
  }
}

function resetForm() {
  created.value = null;
  targetUrl.value = '';
  title.value = '';
  isPrivate.value = false;
  ttlPreset.value = 'none';
  customTtlHours.value = null;
  maxClicks.value = null;
}

function goLinks() {
  router.push('/links');
}
</script>

<template>
  <div>
    <h1 class="text-h4 font-weight-bold mb-2 page-title">Сократитель ссылок</h1>
    <p class="text-body-2 text-medium-emphasis mb-6">
      Короткий код присваивается автоматически при создании, например <code>go.skykraft.su/Xk9#2a</code>.
    </p>

    <v-alert v-if="!user && authReady" type="info" variant="tonal" class="mb-4" rounded="lg">
      Для создания ссылок войдите через OAuthSky.
      <template #append>
        <v-btn size="small" color="primary" @click="emit('login')">Войти</v-btn>
      </template>
    </v-alert>

    <template v-if="created">
      <v-card rounded="xl" class="pa-4 mb-4">
        <v-card-title class="text-h6 px-0">Ссылка создана</v-card-title>
        <div class="text-caption text-medium-emphasis mb-3">Код: <strong>{{ created.slug }}</strong></div>
        <QrBlock :value="created.short_url" />
        <CopyableLink label="Сокращённая" :url="created.short_url" />
        <CopyableLink label="Оригинальная" :url="created.target_url" />
        <CopyableLink label="Страница просмотра" :url="created.view_url" />
        <div class="d-flex flex-wrap gap-2 mt-2">
          <v-btn variant="tonal" prepend-icon="mdi-plus" @click="resetForm">Ещё одна</v-btn>
          <v-btn color="primary" prepend-icon="mdi-link-multiple" @click="goLinks">Мои ссылки</v-btn>
        </div>
      </v-card>
    </template>

    <v-card v-else-if="user" rounded="xl" class="pa-4">
      <v-form @submit.prevent="onSubmit">
        <v-text-field
          v-model="targetUrl"
          label="Оригинальная ссылка"
          placeholder="https://…, ftp://…, tg://…, mailto:…"
          hint="http, https, ftp, tg, mailto, tel и другие схемы"
          persistent-hint
          variant="outlined"
          density="comfortable"
          class="mb-2"
        />

        <v-text-field
          v-model="title"
          label="Название (необязательно)"
          variant="outlined"
          density="comfortable"
          class="mb-2"
        />

        <v-select
          v-model="ttlPreset"
          :items="ttlOptions"
          item-title="title"
          item-value="value"
          label="Срок действия (TTL)"
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
          label="Лимит переходов (необязательно)"
          hint="После лимита ссылка станет неактивной, но не удалится"
          persistent-hint
          min="1"
          clearable
          variant="outlined"
          density="comfortable"
          class="mb-2"
        />

        <v-switch
          v-model="isPrivate"
          color="primary"
          label="Приватная — только для меня (нужна авторизация)"
          hide-details
          class="mb-4"
        />

        <v-alert v-if="error" type="error" variant="tonal" class="mb-4" rounded="lg">{{ error }}</v-alert>

        <v-btn type="submit" color="primary" size="large" block :loading="loading" rounded="lg">
          Создать ссылку
        </v-btn>
      </v-form>
    </v-card>
  </div>
</template>
