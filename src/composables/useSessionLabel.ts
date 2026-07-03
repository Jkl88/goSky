export function sessionClientLabel(userAgent: string | null): string {
  const ua = (userAgent || '').toLowerCase();
  const os = /android/.test(ua)
    ? 'Android'
    : /iphone|ipad|ios/.test(ua)
      ? 'iOS'
      : /windows/.test(ua)
        ? 'Windows'
        : /mac os|macintosh/.test(ua)
          ? 'macOS'
          : /linux/.test(ua)
            ? 'Linux'
            : 'Неизвестно';
  const browser = /edg\//.test(ua)
    ? 'Edge'
    : /opr\//.test(ua) || /opera/.test(ua)
      ? 'Opera'
      : /firefox\//.test(ua)
        ? 'Firefox'
        : /chrome\//.test(ua) || /chromium\//.test(ua)
          ? 'Chrome'
          : /safari\//.test(ua)
            ? 'Safari'
            : '';
  const parts = [browser, os].filter(Boolean);
  return parts.length ? parts.join(' / ') : 'Неизвестный клиент';
}
