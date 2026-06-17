'use client';

import dynamic from 'next/dynamic';

const CookieConsentBanner = dynamic(
  () => import('./CookieConsentBanner'),
  { ssr: false }
);

export default function CookieBannerWrapper() {
  return <CookieConsentBanner />;
}
