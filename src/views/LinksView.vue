<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { deleteLink, listLinks, type ShortLink, type UserRecord } from '@/services/api';

const props = defineProps<{
  user: UserRecord | null;
  authReady: boolean;
}>();

const emit = defineEmits<{ login: [] }>();

const router = useRouter();
const links = ref<ShortLink[]>([]);
const loading = ref(true);
const error = ref('');
const deleteTarget = ref<ShortLink | null>(null);
const deleting = ref(false);

async function load() {
  if (!props.user) {
    loading.value = false;
    return;
  }
  loading.value = true;
  error.value = '';
  try {
    links.value = await listLinks();
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Ошибка загрузки';
  } finally {
    loading.value = false;
  }
}

async function confirmDelete() {
  if (!deleteTarget.value) return;
  deleting.value = true;
  try {
    await deleteLink(deleteTarget.value.slug);
    deleteTarget.value = null;
    await load();
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Ошибка удаления';
  } finally {
    deleting.value = false;
  }
}

function openView(link: ShortLink) {
  router.push(`/${link.slug}/vq`);
}

onMounted(load);
watch(() => props.user, load);
</script>

<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-4 flex-wrap gap-2">
      <h1 class="text-h4 font-weight-bold page-title mb-0">Мои ссылки</h1>
      <v-btn v-if="user" color="primary" prepend-icon="mdi-plus" to="/" size="small">Создать</v-btn>
    </div>

    <v-alert v-if="authReady && !user" type="info" variant="tonal" rounded="lg">
      Войдите, чтобы видеть свои ссылки.
      <template #append>
        <v-btn size="small" color="primary" @click="emit('login')">Войти</v-btn>
      </template>
    </v-alert>

    <v-progress-linear v-else-if="loading" indeterminate class="mb-4" />

    <v-alert v-else-if="error" type="error" variant="tonal" rounded="lg" class="mb-4">{{ error }}</v-alert>

    <v-card v-else-if="links.length === 0 && user" rounded="xl" class="pa-6 text-center">
      <v-icon size="48" color="primary" class="mb-2">mdi-link-off</v-icon>
      <div class="text-body-1 mb-4">Пока нет ссылок</div>
      <v-btn color="primary" to="/">Создать первую</v-btn>
    </v-card>

    <v-list v-else lines="two" class="bg-transparent pa-0">
      <v-card
        v-for="link in links"
        :key="link.id"
        rounded="xl"
        class="mb-3"
        @click="openView(link)"
      >
        <v-list-item>
          <template #prepend>
            <v-avatar color="primary" variant="tonal" size="40">
              <v-icon>{{ link.is_private ? 'mdi-lock' : 'mdi-earth' }}</v-icon>
            </v-avatar>
          </template>
          <v-list-item-title class="font-weight-medium">
            {{ link.title || link.slug }}
          </v-list-item-title>
          <v-list-item-subtitle class="text-truncate">
            {{ link.short_url }}
          </v-list-item-subtitle>
          <template #append>
            <div class="d-flex align-center" @click.stop>
              <v-chip v-if="!link.is_active" color="warning" size="x-small" variant="flat" class="mr-1">
                Неактивна
              </v-chip>
              <v-chip size="x-small" variant="tonal" class="mr-2">{{ link.click_count }} кликов</v-chip>
              <v-btn icon size="small" variant="text" @click="openView(link)">
                <v-icon>mdi-qrcode</v-icon>
              </v-btn>
              <v-btn icon size="small" variant="text" color="error" @click="deleteTarget = link">
                <v-icon>mdi-delete-outline</v-icon>
              </v-btn>
            </div>
          </template>
        </v-list-item>
      </v-card>
    </v-list>

    <v-dialog :model-value="!!deleteTarget" max-width="400" @update:model-value="(v) => !v && (deleteTarget = null)">
      <v-card rounded="xl" title="Удалить ссылку?">
        <v-card-text>
          Ссылка <strong>{{ deleteTarget?.slug }}</strong> перестанет работать.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteTarget = null">Отмена</v-btn>
          <v-btn color="error" :loading="deleting" @click="confirmDelete">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
