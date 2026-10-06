import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Link from 'next/link';

interface StudentProfile {
  id: number;
  purchased_hours: number;
  used_hours: number;
  remaining_hours: number;
  ready_for_exam: boolean;
  license_type: string;
}

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

    const fetchProfile = async () => {
      try {
        const response = await api.get('/student-profiles/my_profile/');
        setProfile(response.data);
      } catch (error) {
        console.error('Error fetching profile:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, [isAuthenticated, router]);

  if (isLoading) {
    return <div className="flex justify-center items-center h-screen">Chargement...</div>;
  }

  if (!profile) {
    return <div className="flex justify-center items-center h-screen">Profil non trouvé</div>;
  }

  const progressPercent = (profile.used_hours / (profile.purchased_hours || 1)) * 100;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="container py-6">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold">Bienvenue, {user?.first_name}!</h1>
            <button
              onClick={() => {
                logout();
                router.push('/login');
              }}
              className="btn-secondary"
            >
              Déconnexion
            </button>
          </div>
        </div>
      </header>

      <main className="container py-8">
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="card">
            <h2 className="text-xl font-bold mb-4">📚 Votre progression</h2>
            <div className="mb-4">
              <div className="flex justify-between mb-2">
                <span className="font-medium">Heures utilisées</span>
                <span className="font-bold">{profile.used_hours.toFixed(1)}h / {profile.purchased_hours.toFixed(1)}h</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(progressPercent, 100)}%` }}
                ></div>
              </div>
            </div>
            <p className="text-gray-600">Heures restantes: {profile.remaining_hours.toFixed(1)}h</p>
          </div>

          <div className="card">
            <h2 className="text-xl font-bold mb-4">🎯 État de préparation</h2>
            <div className="space-y-4">
              <div>
                <p className="text-gray-600">Type de permis</p>
                <p className="font-bold text-lg">
                  {profile.license_type === 'AUTO' ? 'Automatique' : 'Manuelle'}
                </p>
              </div>
              <div>
                <p className="text-gray-600">Prêt pour l'examen</p>
                <p className="font-bold text-lg">
                  {profile.ready_for_exam ? '✅ Oui' : '⏳ Pas encore'}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <Link href="/student/reservation" className="card hover:shadow-lg transition-shadow cursor-pointer">
            <h3 className="text-xl font-bold mb-2">📅 Réserver une leçon</h3>
            <p className="text-gray-600">Consultez les créneaux disponibles et réservez</p>
          </Link>

          <Link href="/student/notebook" className="card hover:shadow-lg transition-shadow cursor-pointer">
            <h3 className="text-xl font-bold mb-2">📖 Livret numérique</h3>
            <p className="text-gray-600">Consultez vos bilans de leçons et compétences</p>
          </Link>

          <Link href="/student/documents" className="card hover:shadow-lg transition-shadow cursor-pointer">
            <h3 className="text-xl font-bold mb-2">📄 Documents</h3>
            <p className="text-gray-600">Téléchargez votre pièce d'identité et NEPH</p>
          </Link>

          <Link href="/student/purchases" className="card hover:shadow-lg transition-shadow cursor-pointer">
            <h3 className="text-xl font-bold mb-2">💳 Acheter des heures</h3>
            <p className="text-gray-600">Consultez nos tarifs et augmentez votre crédit d'heures</p>
          </Link>
        </div>
      </main>
    </div>
  );
}
