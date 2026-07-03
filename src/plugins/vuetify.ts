import { createVuetify } from 'vuetify';
import { aliases, mdi } from 'vuetify/iconsets/mdi';

export type ThemeMode = 'system' | 'light' | 'dark';

const STORAGE_KEY = 'gosky-theme';

export function getStoredThemeMode(): ThemeMode {
  const v = localStorage.getItem(STORAGE_KEY);
  if (v === 'light' || v === 'dark' || v === 'system') return v;
  return 'system';
}

export function resolveDark(mode: ThemeMode): boolean {
  if (mode === 'dark') return true;
  if (mode === 'light') return false;
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

export default createVuetify({
  icons: { defaultSet: 'mdi', aliases, sets: { mdi } },
  theme: {
    defaultTheme: resolveDark(getStoredThemeMode()) ? 'goskyDark' : 'goskyLight',
    themes: {
      goskyLight: {
        dark: false,
        colors: {
          primary: '#2563eb',
          secondary: '#64748b',
          surface: '#ffffff',
          background: '#f1f5f9',
        },
      },
      goskyDark: {
        dark: true,
        colors: {
          primary: '#3b82f6',
          secondary: '#94a3b8',
          surface: '#1e293b',
          background: '#0f172a',
        },
      },
    },
  },
});
