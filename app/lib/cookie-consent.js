export const COOKIE_CONSENT_KEY = 'mecaenergy-cookie-consent';

export function getCookieConsent() {
  if (typeof window === 'undefined') return null;
  const val = localStorage.getItem(COOKIE_CONSENT_KEY);
  if (val === 'accepted' || val === 'rejected') return val;
  return null;
}

export function setCookieConsent(choice) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(COOKIE_CONSENT_KEY, choice);
}

export function clearCookieConsent() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(COOKIE_CONSENT_KEY);
}
