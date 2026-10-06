import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';

interface Slot {
  id: number;
  date: string;
  start_time: string;
  end_time: string;
  status: string;
  meeting_point_name: string;
  student_name: string;
}

export default function InstructorPlanning() {
  const [slots, setSlots] = useState<Slot[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { isAuthenticated, user, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'INSTRUCTOR') {
      router.push('/login');
      return;
    }

    const fetchSlots = async () => {
      try {
        const response = await api.get('/slots/');
        setSlots(response.data);
      } catch (error) {
        console.error('Error fetching slots:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSlots();
  }, [isAuthenticated, user, router]);

  if (isLoading) {
    return <div className="flex justify-center items-center h-screen">Chargement...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="container py-6">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold">Planning de la monitrice</h1>
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
        <div className="mb-6 flex justify-between items-center">
          <h2 className="text-2xl font-bold">Créneaux</h2>
          <button className="btn-primary">+ Ajouter un créneau</button>
        </div>

        <div className="card">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">Date</th>
                  <th className="text-left py-3 px-4">Heure</th>
                  <th className="text-left py-3 px-4">Lieu</th>
                  <th className="text-left py-3 px-4">Élève</th>
                  <th className="text-left py-3 px-4">Statut</th>
                  <th className="text-left py-3 px-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {slots.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-gray-500">
                      Aucun créneau pour le moment
                    </td>
                  </tr>
                ) : (
                  slots.map((slot) => (
                    <tr key={slot.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4">{slot.date}</td>
                      <td className="py-3 px-4">{slot.start_time} - {slot.end_time}</td>
                      <td className="py-3 px-4">{slot.meeting_point_name}</td>
                      <td className="py-3 px-4">{slot.student_name || '-'}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-sm font-medium ${
                          slot.status === 'BOOKED'
                            ? 'bg-green-100 text-green-700'
                            : slot.status === 'AVAILABLE'
                            ? 'bg-blue-100 text-blue-700'
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {slot.status === 'BOOKED' ? '✅ Réservé' : slot.status === 'AVAILABLE' ? '⏳ Disponible' : '❌ Annulé'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <button className="text-blue-600 hover:text-blue-700">Éditer</button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mt-8">
          <div className="card">
            <h3 className="text-xl font-bold mb-4">📊 Statistiques du jour</h3>
            <div className="space-y-2">
              <p>Créneaux réservés: {slots.filter(s => s.status === 'BOOKED').length}</p>
              <p>Créneaux disponibles: {slots.filter(s => s.status === 'AVAILABLE').length}</p>
            </div>
          </div>

          <div className="card">
            <h3 className="text-xl font-bold mb-4">🚗 Carnet de bord</h3>
            <button className="btn-primary w-full">Ajouter une entrée kilométrique</button>
          </div>
        </div>
      </main>
    </div>
  );
}
