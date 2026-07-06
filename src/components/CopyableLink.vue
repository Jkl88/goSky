<script setup lang="ts">
import { ref } from 'vue';
import { openExternalUrl } from '@/composables/openExternalUrl';
import { copyToClipboard } from '@/services/api';

const props = withDefaults(
  defineProps<{
    label: string;
    url: string;
    asLink?: boolean;
  }>(),
  { asLink: true },
);

const snack = ref(false);

async function onCopy(e: Event) {
  e.preventDefault();
  e.stopPropagation();
  const ok = await copyToClipboard(props.url);
  if (ok) snack.value = true;
}

function onLinkClick(e: MouseEvent) {
  e.preventDefault();
  openExternalUrl(props.url);
}
</script>

<template>
  <v-card variant="tonal" class="mb-3" rounded="lg">
    <v-card-text class="pb-2">
      <div class="text-caption text-medium-emphasis mb-1">{{ label }}</div>
      <div class="d-flex align-center gap-1 link-row">
        <a
          v-if="asLink"
          :href="url"
          class="text-primary text-body-2 text-break flex-grow-1 text-decoration-none link-open"
          target="_blank"
          rel="noopener noreferrer"
          @click="onLinkClick"
        >
          {{ url }}
        </a>
        <span v-else class="text-primary text-body-2 text-break flex-grow-1">{{ url }}</span>
        <v-btn
          icon
          size="small"
          variant="text"
          density="comfortable"
          title="Скопировать"
          aria-label="Скопировать ссылку"
          @click="onCopy"
        >
          <v-icon size="small">mdi-content-copy</v-icon>
        </v-btn>
      </div>
    </v-card-text>
  </v-card>

  <v-snackbar v-model="snack" :timeout="2000" color="success" location="bottom">
    Скопировано в буфер
  </v-snackbar>
</template>

<style scoped>
.link-open:hover {
  text-decoration: underline;
}
.link-row {
  min-width: 0;
}
</style>
