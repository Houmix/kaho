import Link from 'next/link';
import { useRouter } from 'next/router';

const ORIGINS: Record<string, { href: string; label: string }> = {
  planning: { href: '/instructor/planning', label: '← Retour au planning' },
  calendar: { href: '/admin/calendar', label: '← Retour au planning' },
  dashboard: { href: '/instructor/dashboard', label: '← Retour au tableau de bord' },
};

/** Lien de retour : revient à la page d'où l'on vient (?from=planning|calendar|dashboard), sinon à la page par défaut. */
export default function BackLink({ fallbackHref, fallbackLabel }: { fallbackHref: string; fallbackLabel: string }) {
  const { query } = useRouter();
  const origin = typeof query.from === 'string' ? ORIGINS[query.from] : undefined;
  const target = origin ?? { href: fallbackHref, label: fallbackLabel };
  return <Link href={target.href} className="inline-flex items-center gap-1 text-sm text-brown-700 hover:underline mb-2">{target.label}</Link>;
}

/** Fiche élève (unique, adaptée au rôle) en conservant l'origine pour le bouton de retour. */
export function studentHref(studentId: number | string, from: 'planning' | 'calendar' | 'dashboard' = 'planning') {
  return `/admin/students/${studentId}?from=${from}`;
}
