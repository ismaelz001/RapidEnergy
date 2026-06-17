'use client';

import { clearCookieConsent } from '@/app/lib/cookie-consent';

export default function GestionarCookiesBtn() {
  return (
    <button
      onClick={() => { clearCookieConsent(); window.location.reload(); }}
      className="text-xs text-[#94A3B8]/50 hover:text-[#94A3B8] transition-colors"
    >
      Cookies
    </button>
  );
}
