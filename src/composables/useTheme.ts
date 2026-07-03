import { ref, watch, onMounted, onUnmounted, type Ref } from 'vue';
import { useTheme } from 'vuetify';
import { getStoredThemeMode, resolveDark, type ThemeMode } from '@/plugins/vuetify';

const STORAGE_KEY = 'gosky-theme';

export function useAppTheme() {
  const theme = useTheme();
  const mode: Ref<ThemeMode> = ref(getStoredThemeMode());

  function apply() {
    const dark = resolveDark(mode.value);
    theme.global.name.value = dark ? 'goskyDark' : 'goskyLight';
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', dark ? '#0f172a' : '#f1f5f9');
  }

  function setMode(next: ThemeMode) {
    mode.value = next;
    localStorage.setItem(STORAGE_KEY, next);
    apply();
  }

  function cycleMode() {
    const order: ThemeMode[] = ['system', 'light', 'dark'];
    const idx = order.indexOf(mode.value);
    setMode(order[(idx + 1) % order.length]);
  }

  const modeLabel = () => {
    if (mode.value === 'system') return 'Системная';
    if (mode.value === 'light') return 'Светлая';
    return 'Тёмная';
  };

  const modeIcon = () => {
    if (mode.value === 'system') return 'mdi-theme-light-dark';
    if (mode.value === 'light') return 'mdi-white-balance-sunny';
    return 'mdi-moon-waning-crescent';
  };

  let mq: MediaQueryList | null = null;
  const onMq = () => {
    if (mode.value === 'system') apply();
  };

  onMounted(() => {
    apply();
    mq = window.matchMedia('(prefers-color-scheme: dark)');
    mq.addEventListener('change', onMq);
  });

  onUnmounted(() => {
    mq?.removeEventListener('change', onMq);
  });

  watch(mode, apply);

  return { mode, setMode, cycleMode, modeLabel, modeIcon };
}
