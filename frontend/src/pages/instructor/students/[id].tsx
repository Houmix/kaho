import { useEffect } from 'react';
import { useRouter } from 'next/router';

/** Ancienne adresse de la fiche élève : une seule fiche, /admin/students/[id], adaptée au rôle de l'utilisateur. */
export default function LegacyStudentSheet() {
  const router = useRouter();
  useEffect(() => {
    if (!router.isReady) return;
    const { id, from } = router.query;
    router.replace({ pathname: `/admin/students/${id}`, query: from ? { from } : {} });
  }, [router]);
  return null;
}
