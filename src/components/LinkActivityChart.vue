<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { fetchLinkActivity, type LinkActivity } from '@/services/api';

const props = defineProps<{
  slug: string;
}>();

const mode = ref<'day' | 'month'>('day');
const selectedDate = ref('');
const selectedMonth = ref('');
const loading = ref(true);
const error = ref('');
const activity = ref<LinkActivity | null>(null);
const hoverIndex = ref<number | null>(null);

const chartWidth = 640;
const chartHeight = 220;
const padX = 28;
const padY = 24;

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function currentMonthIso(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

function initFilters() {
  selectedDate.value = todayIso();
  selectedMonth.value = currentMonthIso();
}

const activeDate = computed(() => (mode.value === 'day' ? selectedDate.value : selectedMonth.value));

const maxCount = computed(() => {
  const points = activity.value?.points ?? [];
  return Math.max(1, ...points.map((p) => p.count));
});

const barWidth = computed(() => (chartWidth - padX * 2) / 24);

const bars = computed(() => {
  const points = activity.value?.points ?? [];
  return points.map((point, index) => {
    const height = (point.count / maxCount.value) * (chartHeight - padY * 2);
    const x = padX + index * barWidth.value + barWidth.value * 0.12;
    const width = barWidth.value * 0.76;
    const y = chartHeight - padY - height;
    return { ...point, index, x, y, width, height };
  });
});

const linePath = computed(() => {
  if (!bars.value.length) return '';
  return bars.value
    .map((bar, idx) => {
      const x = bar.x + bar.width / 2;
      const y = bar.y;
      return `${idx === 0 ? 'M' : 'L'} ${x} ${y}`;
    })
    .join(' ');
});

const areaPath = computed(() => {
  if (!linePath.value) return '';
  const first = bars.value[0];
  const last = bars.value[bars.value.length - 1];
  const baseY = chartHeight - padY;
  return `${linePath.value} L ${last.x + last.width / 2} ${baseY} L ${first.x + first.width / 2} ${baseY} Z`;
});

const hoverBar = computed(() => (hoverIndex.value === null ? null : bars.value[hoverIndex.value] ?? null));

const tooltipStyle = computed(() => {
  if (!hoverBar.value) return { display: 'none' };
  const x = hoverBar.value.x + hoverBar.value.width / 2;
  const y = hoverBar.value.y;
  const leftPct = (x / chartWidth) * 100;
  const topPct = (y / chartHeight) * 100;
  return {
    left: `${leftPct}%`,
    top: `${topPct}%`,
  };
});

async function load() {
  loading.value = true;
  error.value = '';
  try {
    activity.value = await fetchLinkActivity(props.slug, {
      mode: mode.value,
      date: activeDate.value,
    });
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Не удалось загрузить график';
    activity.value = null;
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  initFilters();
  void load();
});

watch([mode, selectedDate, selectedMonth], () => {
  void load();
});
</script>

<template>
  <v-card rounded="xl" class="pa-4 mb-4 activity-card">
    <div class="d-flex align-center justify-space-between flex-wrap gap-2 mb-3">
      <div>
        <v-card-title class="px-0 pt-0 text-subtitle-1">Активность по часам</v-card-title>
        <div v-if="activity" class="text-caption text-medium-emphasis">
          {{ activity.range_label }} · всего {{ activity.total }}
        </div>
      </div>
      <v-btn-toggle v-model="mode" mandatory density="compact" color="primary" rounded="lg">
        <v-btn value="day" size="small">День</v-btn>
        <v-btn value="month" size="small">Месяц</v-btn>
      </v-btn-toggle>
    </div>

    <div class="d-flex flex-wrap gap-2 mb-3">
      <v-text-field
        v-if="mode === 'day'"
        v-model="selectedDate"
        type="date"
        label="День"
        density="compact"
        variant="outlined"
        hide-details
        style="max-width: 200px"
      />
      <v-text-field
        v-else
        v-model="selectedMonth"
        type="month"
        label="Месяц"
        density="compact"
        variant="outlined"
        hide-details
        style="max-width: 200px"
      />
    </div>

    <v-progress-linear v-if="loading" indeterminate class="mb-3" />
    <v-alert v-else-if="error" type="error" variant="tonal" rounded="lg" density="compact">{{ error }}</v-alert>

    <div v-else class="chart-shell">
      <div v-if="activity && activity.total === 0" class="text-body-2 text-medium-emphasis text-center py-8">
        За выбранный период переходов нет
      </div>
      <div v-else class="chart-wrap">
        <svg
          :viewBox="`0 0 ${chartWidth} ${chartHeight}`"
          class="activity-chart"
          @mouseleave="hoverIndex = null"
        >
          <defs>
            <linearGradient id="activityFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="rgb(var(--v-theme-primary))" stop-opacity="0.35" />
              <stop offset="100%" stop-color="rgb(var(--v-theme-primary))" stop-opacity="0.02" />
            </linearGradient>
          </defs>

          <line
            :x1="padX"
            :y1="chartHeight - padY"
            :x2="chartWidth - padX"
            :y2="chartHeight - padY"
            class="axis-line"
          />

          <path v-if="areaPath" :d="areaPath" fill="url(#activityFill)" />
          <path v-if="linePath" :d="linePath" class="line-path" />

          <g v-for="bar in bars" :key="bar.hour">
            <rect
              :x="bar.x"
              :y="bar.y"
              :width="bar.width"
              :height="Math.max(bar.height, bar.count > 0 ? 3 : 0)"
              rx="4"
              class="bar"
              :class="{ active: hoverIndex === bar.index }"
              @mouseenter="hoverIndex = bar.index"
            />
            <text
              v-if="bar.hour % 3 === 0"
              :x="bar.x + bar.width / 2"
              :y="chartHeight - 6"
              text-anchor="middle"
              class="axis-label"
            >
              {{ bar.label }}
            </text>
          </g>

          <circle
            v-if="hoverBar"
            :cx="hoverBar.x + hoverBar.width / 2"
            :cy="hoverBar.y"
            r="5"
            class="hover-dot"
          />
        </svg>

        <div v-if="hoverBar" class="chart-tooltip" :style="tooltipStyle">
          <div class="tooltip-time">{{ hoverBar.label }}</div>
          <div class="tooltip-count">{{ hoverBar.count }} кликов</div>
        </div>
      </div>
    </div>
  </v-card>
</template>

<style scoped>
.activity-card {
  overflow: hidden;
}

.chart-wrap {
  position: relative;
}

.activity-chart {
  width: 100%;
  height: auto;
  display: block;
}

.axis-line {
  stroke: rgba(var(--v-theme-on-surface), 0.12);
  stroke-width: 1;
}

.line-path {
  fill: none;
  stroke: rgb(var(--v-theme-primary));
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.bar {
  fill: rgba(var(--v-theme-primary), 0.18);
  transition: fill 0.15s ease, transform 0.15s ease;
}

.bar.active {
  fill: rgba(var(--v-theme-primary), 0.55);
}

.hover-dot {
  fill: rgb(var(--v-theme-primary));
  stroke: rgb(var(--v-theme-surface));
  stroke-width: 2;
}

.axis-label {
  font-size: 11px;
  fill: rgba(var(--v-theme-on-surface), 0.55);
}

.chart-tooltip {
  position: absolute;
  transform: translate(-50%, calc(-100% - 12px));
  pointer-events: none;
  background: rgba(var(--v-theme-surface-variant), 0.96);
  color: rgb(var(--v-theme-on-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 12px;
  padding: 8px 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
  min-width: 88px;
  text-align: center;
  z-index: 2;
}

.tooltip-time {
  font-size: 12px;
  opacity: 0.75;
}

.tooltip-count {
  font-size: 15px;
  font-weight: 700;
}
</style>
