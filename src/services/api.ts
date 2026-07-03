export type UserRecord = {
  id: number;
  login: string;
  email: string;
  role: string;
  blocked: boolean;
  created_at: string;
};

export type ShortLink = {
  id: number;
  slug: string;
  target_url: string;
  title: string | null;
  is_private: boolean;
  is_enabled: boolean;
  click_count: number;
  expires_at: string | null;
  max_clicks: number | null;
  is_active: boolean;
  inactive_reason: string | null;
  created_at: string;
  updated_at: string | null;
  short_url: string;
  view_url: string;
};

export type ShortLinkView = {
  slug: string;
  target_url: string;
  title: string | null;
  is_private: boolean;
  is_enabled: boolean;
  click_count: number;
  expires_at: string | null;
  max_clicks: number | null;
  is_active: boolean;
  inactive_reason: string | null;
  short_url: string;
  view_url: string;
  is_owner: boolean;
  can_edit: boolean;
};

export type LinkClickRecord = {
  id: number;
  ip_address: string | null;
  user_agent: string | null;
  device_type: string;
  device_label: string;
  clicked_at: string;
};

export type LinkStats = {
  slug: string;
  click_count: number;
  unique_ips: number;
  is_active: boolean;
  inactive_reason: string | null;
  expires_at: string | null;
  max_clicks: number | null;
  device_breakdown: Record<string, number>;
  clicks: LinkClickRecord[];
};

export type OAuthSkyConfig = {
  enabled: boolean;
  portal_url: string;
};

export type UserSessionRecord = {
  id: number;
  expires_at: string;
  refresh_expires_at: string;
  created_at: string;
  last_seen_at: string | null;
  user_agent: string | null;
  ip_address: string | null;
  current: boolean;
};

export type QrLoginLinkOut = {
  id: number;
  login_url: string;
  expires_at: string;
  ttl_seconds: number;
};

export type QrLoginStatusOut = {
  status: 'pending' | 'missing' | 'expired';
};

const RAW_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
// Относительный /api — пути уже содержат /api/...; полный URL — префикс к пути.
const API_BASE =
  RAW_BASE.startsWith('http://') || RAW_BASE.startsWith('https://') ? RAW_BASE : '';

function apiUrl(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`;
  return API_BASE ? `${API_BASE}${p}` : p;
}

export function formatApiErrorDetail(detail: unknown): string {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((e) => (typeof e === 'object' && e && 'msg' in e ? String((e as { msg: string }).msg) : String(e))).join('; ');
  }
  return 'Ошибка запроса';
}

export async function api<T>(path: string, init: RequestInit = {}, retryOn401 = true): Promise<T> {
  const res = await fetch(apiUrl(path), {
    ...init,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(init.headers || {}),
    },
  });

  if (res.status === 401 && retryOn401 && !path.includes('/auth/refresh')) {
    const refresh = await fetch(apiUrl('/api/auth/refresh'), {
      method: 'POST',
      credentials: 'include',
    });
    if (refresh.ok) {
      return api<T>(path, init, false);
    }
  }

  if (!res.ok) {
    let detail: unknown = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? body.message ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(formatApiErrorDetail(detail));
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function fetchOAuthSkyConfig(): Promise<OAuthSkyConfig> {
  return api<OAuthSkyConfig>('/api/auth/oauthsky/config', {}, false);
}

export function getOAuthSkyStartUrl(returnTo = '/'): string {
  return apiUrl(`/api/auth/oauthsky/start?return_to=${encodeURIComponent(returnTo)}`);
}

export async function getCurrentUser(): Promise<UserRecord | null> {
  try {
    return await api<UserRecord>('/api/auth/me');
  } catch {
    return null;
  }
}

export async function logout(): Promise<void> {
  await api('/api/auth/logout', { method: 'POST' }, false);
}

export async function listUserSessions(): Promise<UserSessionRecord[]> {
  return api<UserSessionRecord[]>('/api/auth/sessions');
}

export async function revokeUserSession(sessionId: number): Promise<void> {
  await api(`/api/auth/sessions/${sessionId}`, { method: 'DELETE' });
}

export async function createQrLoginLink(): Promise<QrLoginLinkOut> {
  return api<QrLoginLinkOut>('/api/auth/qr-login-links', { method: 'POST' });
}

export async function getQrLoginLinkStatus(linkId: number): Promise<QrLoginStatusOut> {
  return api<QrLoginStatusOut>(`/api/auth/qr-login-links/${linkId}/status`);
}

export async function consumeQrLoginLink(token: string): Promise<UserRecord> {
  return api<UserRecord>('/api/auth/qr-login/consume', {
    method: 'POST',
    body: JSON.stringify({ token: token.trim() }),
  }, false);
}

export async function listLinks(): Promise<ShortLink[]> {
  return api<ShortLink[]>('/api/links');
}

export async function createLink(data: {
  target_url: string;
  title?: string | null;
  is_private: boolean;
  ttl_hours?: number | null;
  max_clicks?: number | null;
}): Promise<ShortLink> {
  return api<ShortLink>('/api/links', { method: 'POST', body: JSON.stringify(data) });
}

export async function updateLink(
  slug: string,
  data: {
    target_url?: string;
    title?: string | null;
    is_private?: boolean;
    is_enabled?: boolean;
    ttl_hours?: number | null;
    max_clicks?: number | null;
    clear_expires_at?: boolean;
    clear_max_clicks?: boolean;
  },
): Promise<ShortLink> {
  return api<ShortLink>(`/api/links/${encodeURIComponent(slug)}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteLink(slug: string): Promise<void> {
  await api(`/api/links/${encodeURIComponent(slug)}`, { method: 'DELETE' });
}

export async function viewLink(slug: string): Promise<ShortLinkView> {
  return api<ShortLinkView>(`/api/links/${encodeURIComponent(slug)}/view`, {}, false);
}

export async function fetchLinkStats(slug: string): Promise<LinkStats> {
  return api<LinkStats>(`/api/links/${encodeURIComponent(slug)}/stats`);
}

export function parseApiDateTime(iso: string): Date {
  const s = iso.trim();
  if (!s) return new Date(NaN);
  if (/[zZ]|[+-]\d{2}:\d{2}$/.test(s)) {
    return new Date(s);
  }
  return new Date(`${s}Z`);
}

export function formatDateTime(iso: string | null): string {
  if (!iso) return '—';
  const date = parseApiDateTime(iso);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleString('ru-RU');
}

export const SLUG_PATTERN = /^[A-Za-z0-9$@!%#]{1,6}$/;

export function validateSlug(slug: string): string | null {
  if (!SLUG_PATTERN.test(slug)) {
    return '1–6 символов: цифры, латиница и $ @ ! % #';
  }
  return null;
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(ta);
    return ok;
  }
}
