import { useEffect } from 'react';
import { useRouter } from 'next/router';

/** Avertit avant de quitter la page (fermeture, rechargement ou navigation interne) si des modifications ne sont pas enregistrées. */
export function useUnsavedGuard(dirty: boolean, message = 'Des modifications ne sont pas enregistrées. Voulez-vous quitter sans enregistrer ?') {
  const router = useRouter();
  useEffect(() => {
    if (!dirty) return;
    const onBeforeUnload = (e: BeforeUnloadEvent) => { e.preventDefault(); e.returnValue = ''; };
    const onRouteChange = (url: string) => {
      if (!confirm(message)) { router.events.emit('routeChangeError'); throw new Error(`Navigation annulée vers ${url}`); }
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    router.events.on('routeChangeStart', onRouteChange);
    return () => { window.removeEventListener('beforeunload', onBeforeUnload); router.events.off('routeChangeStart', onRouteChange); };
  }, [dirty, message, router]);
}
