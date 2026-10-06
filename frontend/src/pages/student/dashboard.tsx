import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Logo from '@/components/Logo';

interface StudentProfile {
  id: number;
  purchased_hours: number;
  used_hours: number;
  remaining_hours: number;
  ready_for_exam: boolean;
  license_type: string;
}

const links = [
  { href: '/student/reservation', title: 'Réserver une leçon', text: 'Créneaux disponibles et points de rendez-vous' },
  { href: '/student/notebook', title: 'Livret numérique', text: 'Bilans de leçons et compétences validées' },
  { href: '/student/documents', title: 'Documents', text: 'Pièce d’identité, attestation NEPH' },
  { href: '/student/purchases', title: 'Acheter des heures', text: 'Packs et paiement sécurisé' },
];

export default function StudentDashboard() {
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { isAuthenticated, user, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    api.get('/student-profiles/my_profile/')
      .then((r) => setProfile(r.data))
      .catch((e) => console.error(e))
      .finally(() => setIsLoading(false));
  }, [isAuthenticated, router]);

  if (isLoading) return <div className="flex justify-center items-center h-screen text-brown-500">Chargement…</div>;
  if (!profile) return <div className="flex justify-center items-center h-screen text-brown-500">Profil introuvable</div>;

  const progress = Math.min((profile.used_hours / (profile.purchased_hours || 1)) * 100, 100);

  return (
    <>
      <Head><title>Mon espace — Kaho</title></Head>
      <header className="bg-white border-b border-cream-200">
        <div className="container flex items-center justify-between py-3">
          <Logo />
          <button onClick={() => { logout(); router.push('/login'); }} className="btn-secondary">Déconnexion</button>
        </div>
      </header>

      <main className="container py-8">
        <h1 className="text-3xl mb-6">Bonjour, {user?.first_name} 👋</h1>

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="card">
            <h2 className="text-xl mb-4">Votre progression</h2>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-brown-800/70">Heures effectuées</span>
              <span className="font-semibold">{profile.used_hours.toFixed(1)} h / {profile.purchased_hours.toFixed(1)} h</span>
            </div>
            <div className="w-full bg-cream-200 rounded-full h-2.5">
              <div className="bg-brown-700 h-2.5 rounded-full transition-all" style={{ width: `${progress}%` }} />
            </div>
            <p className="mt-3 text-brown-800/70">Il vous reste <strong className="text-brown-900">{profile.remaining_hours.toFixed(1)} h</strong></p>
          </div>

          <div className="card">
            <h2 className="text-xl mb-4">Préparation à l’examen</h2>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-brown-800/70">Boîte</dt>
                <dd className="font-medium">{profile.license_type === 'AUTO' ? 'Automatique' : 'Manuelle'}</dd>
              </div>
              <div className="flex justify-between items-center">
                <dt className="text-brown-800/70">Prêt pour l’examen</dt>
                <dd>
                  <span className={`badge ${profile.ready_for_exam ? 'bg-brown-700 text-cream-50' : 'bg-cream-200 text-brown-800'}`}>
                    {profile.ready_for_exam ? 'Oui' : 'Pas encore'}
                  </span>
                </dd>
              </div>
            </dl>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {links.map((l) => (
            <Link key={l.href} href={l.href} className="card hover:border-brown-300 transition-colors">
              <h3 className="text-xl mb-1">{l.title}</h3>
              <p className="text-brown-800/70">{l.text}</p>
            </Link>
          ))}
        </div>
      </main>
    </>
  );
}
