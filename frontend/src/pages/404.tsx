import { useEffect, useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';
import Logo from '@/components/Logo';

const LINKS = {
  guest: [
    { href: '/', label: 'Accueil', hint: 'Présentation, simulateur et offres' },
    { href: '/#tarifs', label: 'Nos offres', hint: 'Formules permis, code, perfectionnement' },
    { href: '/demo', label: 'Essai gratuit du code', hint: 'Un chapitre et 10 questions offerts' },
    { href: '/login', label: 'Connexion', hint: 'Accéder à mon espace' },
    { href: '/signup', label: 'Créer un compte', hint: 'Je suis nouveau' },
  ],
  STUDENT: [
    { href: '/student/dashboard', label: 'Mon espace', hint: 'Heures, progression, prochaines leçons' },
    { href: '/student/reservation', label: 'Réserver une leçon', hint: 'Créneaux disponibles' },
    { href: '/student/notebook', label: 'Mon livret', hint: 'Compétences et bilans' },
    { href: '/student/documents', label: 'Mes documents', hint: 'Dossier administratif' },
    { href: '/student/purchases', label: 'Offres & heures', hint: 'Formules et recharges' },
  ],
  INSTRUCTOR: [
    { href: '/instructor/dashboard', label: 'Tableau de bord', hint: 'Leçons du jour, bilans à saisir' },
    { href: '/instructor/planning', label: 'Planning', hint: 'Tous mes créneaux' },
    { href: '/instructor/availability', label: 'Disponibilités', hint: 'Horaires et absences' },
  ],
  STAFF: [
    { href: '/instructor/planning', label: 'Planning', hint: 'Tous les créneaux' },
    { href: '/instructor/performance', label: 'Performance', hint: 'Avis et activité des moniteurs' },
  ],
};

export default function NotFound() {
  const { isAuthenticated, user, hasHydrated } = useAuth();
  const router = useRouter();
  // Page pré-rendue en statique : le chemin réel n'est connu qu'au montage (évite un écart d'hydratation)
  const [path, setPath] = useState('');
  useEffect(() => setPath(window.location.pathname), []);
  const role = hasHydrated && isAuthenticated && user ? user.role : null;
  const links = role === 'STUDENT' ? LINKS.STUDENT : role === 'INSTRUCTOR' ? LINKS.INSTRUCTOR : role ? LINKS.STAFF : LINKS.guest;

  return (
    <>
      <Head><title>Page introuvable — Kaho</title></Head>
      <div className="min-h-screen flex flex-col">
        <header className="container py-4"><Logo /></header>
        <main className="container flex-1 flex flex-col justify-center py-10 max-w-2xl">
          <p className="text-caramel font-medium tracking-wide uppercase text-sm mb-2">Erreur 404</p>
          <h1 className="text-4xl md:text-5xl mb-3">Cette page n'existe pas.</h1>
          <p className="text-brown-800/70 mb-8">
            {path ? <>L'adresse <code className="bg-cream-200 px-1.5 py-0.5 rounded text-sm">{path}</code> a peut-être été déplacée, ou le lien contient une faute de frappe.</> : 'Cette adresse a peut-être été déplacée, ou le lien contient une faute de frappe.'} Voici où aller :
          </p>
          <div className="grid sm:grid-cols-2 gap-3 mb-8">
            {links.map((l) => (
              <Link key={l.href} href={l.href} className="card py-4 hover:border-brown-300 transition-colors">
                <div className="font-semibold">{l.label} →</div>
                <div className="text-sm text-brown-800/60">{l.hint}</div>
              </Link>
            ))}
          </div>
          <button onClick={() => router.back()} className="text-sm text-brown-700 hover:underline self-start">← Revenir à la page précédente</button>
        </main>
        <footer className="container py-6 text-sm text-brown-800/60">Kaho — auto-école & centre de formation</footer>
      </div>
    </>
  );
}
