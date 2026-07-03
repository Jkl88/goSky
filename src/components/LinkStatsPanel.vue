<script setup lang="ts">
import { computed } from 'vue';
import { formatDateTime, type LinkStats } from '@/services/api';

const props = defineProps<{
  stats: LinkStats;
}>();

const deviceItems = computed(() =>
  Object.entries(props.stats.device_breakdown).map(([label, count]) => ({ label, count })),
);
</script>

<template>
  <v-card rounded="xl" class="pa-4 mb-4">
    <v-card-title class="px-0 text-subtitle-1 d-flex align-center flex-wrap gap-2">
      Статистика переходов
      <v-chip v-if="!stats.is_active" color="warning" size="small" variant="flat">Неактивна</v-chip>
    </v-card-title>

    <v-alert v-if="stats.inactive_reason" type="warning" variant="tonal" density="compact" class="mb-3" rounded="lg">
      {{ stats.inactive_reason }}
    </v-alert>

    <v-row dense class="mb-3">
      <v-col cols="6" sm="3">
        <div class="text-caption text-medium-emphasis">Переходов</div>
        <div class="text-h6">{{ stats.click_count }}</div>
      </v-col>
      <v-col cols="6" sm="3">
        <div class="text-caption text-medium-emphasis">Уникальных IP</div>
        <div class="text-h6">{{ stats.unique_ips }}</div>
      </v-col>
      <v-col cols="6" sm="3">
        <div class="text-caption text-medium-emphasis">Лимит</div>
        <div class="text-body-2">{{ stats.max_clicks ?? '∞' }}</div>
      </v-col>
      <v-col cols="6" sm="3">
        <div class="text-caption text-medium-emphasis">Действует до</div>
        <div class="text-body-2">{{ formatDateTime(stats.expires_at) }}</div>
      </v-col>
    </v-row>

    <div v-if="deviceItems.length" class="mb-4">
      <div class="text-caption text-medium-emphasis mb-2">Устройства</div>
      <div class="d-flex flex-wrap gap-2">
        <v-chip v-for="item in deviceItems" :key="item.label" size="small" variant="tonal">
          {{ item.label }}: {{ item.count }}
        </v-chip>
      </div>
    </div>

    <div class="text-caption text-medium-emphasis mb-2">Последние переходы</div>
    <v-table v-if="stats.clicks.length" density="compact" class="stats-table">
      <thead>
        <tr>
          <th>Время</th>
          <th>IP</th>
          <th>Устройство</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="click in stats.clicks" :key="click.id">
          <td class="text-no-wrap">{{ formatDateTime(click.clicked_at) }}</td>
          <td>{{ click.ip_address || '—' }}</td>
          <td>{{ click.device_label }}</td>
        </tr>
      </tbody>
    </v-table>
    <div v-else class="text-body-2 text-medium-emphasis">Переходов пока нет</div>
  </v-card>
</template>

<style scoped>
.stats-table {
  font-size: 0.85rem;
}
@media (max-width: 600px) {
  .stats-table :deep(th),
  .stats-table :deep(td) {
    padding: 8px 6px !important;
  }
}
</style>
