import { useEffect, useRef, useState } from 'react';

type WakeLockSentinelLike = { release: () => Promise<void>; addEventListener: (t: 'release', cb: () => void) => void };

// Empêche la mise en veille de l'écran tant que `active` est vrai (Screen Wake Lock API).
export function useWakeLock(active: boolean) {
  const sentinel = useRef<WakeLockSentinelLike | null>(null);
  const [held, setHeld] = useState(false);
  const supported = typeof navigator !== 'undefined' && 'wakeLock' in navigator;

  useEffect(() => {
    if (!supported) return;
    let cancelled = false;
    const acquire = async () => {
      try {
        const s = await (navigator as any).wakeLock.request('screen');
        if (cancelled) { s.release(); return; }
        sentinel.current = s;
        setHeld(true);
        s.addEventListener('release', () => setHeld(false));
      } catch { setHeld(false); }
    };
    const onVisible = () => { if (document.visibilityState === 'visible' && active && !sentinel.current) acquire(); };
    if (active) { acquire(); document.addEventListener('visibilitychange', onVisible); }
    return () => {
      cancelled = true;
      document.removeEventListener('visibilitychange', onVisible);
      sentinel.current?.release().catch(() => {});
      sentinel.current = null;
      setHeld(false);
    };
  }, [active, supported]);

  return { supported, held };
}
