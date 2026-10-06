import { useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/router';

export default function Home() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) return;
    router.push(user?.role === 'INSTRUCTOR' ? '/instructor/planning' : '/student/dashboard');
  }, [isAuthenticated, user, router]);

  if (isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-500 to-blue-600">
      <header className="bg-white shadow">
        <nav className="container flex justify-between items-center py-4">
          <h1 className="text-2xl font-bold text-blue-600">Kaho</h1>
          <div className="space-x-4">
            <Link href="/login" className="text-gray-700 hover:text-blue-600">
              Se connecter
            </Link>
            <Link href="/signup" className="btn-primary">
              S'inscrire
            </Link>
          </div>
        </nav>
      </header>

      <section className="container py-20 text-center text-white">
        <h2 className="text-4xl font-bold mb-6">
          Votre plateforme d'auto-école moderne
        </h2>
        <p className="text-xl mb-8 opacity-90">
          Réservez vos leçons de conduite en ligne, suivi pédagogique complet et même hors-ligne
        </p>
        <Link href="/login" className="inline-block bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100">
          Commencer
        </Link>
      </section>

      <section className="bg-white py-20">
        <div className="container">
          <h3 className="text-3xl font-bold text-center mb-12">Fonctionnalités</h3>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="card">
              <h4 className="text-xl font-bold mb-3">📅 Réservation Simple</h4>
              <p className="text-gray-600">Calendrier intuitif pour réserver vos leçons en quelques clics</p>
            </div>
            <div className="card">
              <h4 className="text-xl font-bold mb-3">📚 Suivi Pédagogique</h4>
              <p className="text-gray-600">Accédez à votre livret numérique avec tous vos bilans de leçon</p>
            </div>
            <div className="card">
              <h4 className="text-xl font-bold mb-3">📱 Hors-ligne</h4>
              <p className="text-gray-600">Utilisez l'app même sans connexion internet - synchronisation automatique</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
