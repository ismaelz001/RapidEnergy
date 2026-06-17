'use client';

import { getCookieConsent, setCookieConsent } from '@/app/lib/cookie-consent';
import { useEffect, useState } from 'react';

export default function CookieConsentBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (getCookieConsent() === null) {
      setVisible(true);
    }
  }, []);

  if (!visible) return null;

  const accept = () => { setCookieConsent('accepted'); setVisible(false); };
  const reject = () => { setCookieConsent('rejected'); setVisible(false); };

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 bg-[#0B1220] border-t border-[rgba(255,255,255,0.1)] px-4 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <p className="text-sm text-[#94A3B8]">
        Usamos cookies propias y de terceros (Google Fonts) para mejorar tu experiencia.{' '}
        <a href="/cookies" className="underline text-[#0073EC] hover:opacity-80">Politica de cookies</a>
      </p>
      <div className="flex gap-2 shrink-0">
        <button
          onClick={reject}
          className="px-4 py-1.5 text-sm border border-[rgba(255,255,255,0.2)] rounded text-[#94A3B8] hover:text-white transition-colors"
        >
          Rechazar
        </button>
        <button
          onClick={accept}
          className="px-4 py-1.5 text-sm bg-[#0073EC] text-white rounded hover:bg-blue-600 transition-colors"
        >
          Aceptar
        </button>
      </div>
    </div>
  );
}
