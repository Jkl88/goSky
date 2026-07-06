export function isStandalonePwa(): boolean {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    window.matchMedia('(display-mode: fullscreen)').matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  );
}

/** Открыть URL во внешнем браузере (важно для установленного PWA). */
export function openExternalUrl(url: string): void {
  if (!url) return;

  let parsed: URL;
  try {
    parsed = new URL(url, window.location.origin);
  } catch {
    window.open(url, '_blank', 'noopener,noreferrer');
    return;
  }

  const href = parsed.href;
  const scheme = parsed.protocol.replace(':', '');

  if (isStandalonePwa() && /android/i.test(navigator.userAgent) && (scheme === 'http' || scheme === 'https')) {
    const path = `${parsed.host}${parsed.pathname}${parsed.search}${parsed.hash}`;
    const intent =
      `intent://${path}#Intent;` +
      `scheme=${scheme};` +
      `action=android.intent.action.VIEW;` +
      `category=android.intent.category.BROWSABLE;` +
      `S.browser_fallback_url=${encodeURIComponent(href)};` +
      'end';
    window.location.assign(intent);
    return;
  }

  const opened = window.open(href, '_blank', 'noopener,noreferrer');
  if (!opened) {
    window.location.assign(href);
  }
}
