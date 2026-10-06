import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Logo from '@/components/Logo';

interface Slot {
  id: number;
  date: string;
  start_time: string;
  end_time: string;
  status: 'AVAILABLE' | 'BOOKED' | 'CANCELLED';
  meeting_point_name: string;
  student_name: string | null;
}

const statusStyle: Record<Slot['status'], { label: string; cls: string }> = {
  BOOKED: { label: 'Réservé', cls: 'bg-brown-700 text-cream-50' },
  AVAILABLE: { label: 'Disponible', cls: 'bg-cream-200 text-brown-800' },
  CANCELLED: { label: 'Annulé', cls: 'bg-red-100 text-red-700' },
};

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
    api.get('/slots/')
      .then((r) => setSlots(r.data.results ?? r.data))
      .catch((e) => console.error(e))
      .finally(() => setIsLoading(false));
  }, [isAuthenticated, user, router]);

  if (isLoading) return <div className="flex justify-center items-center h-screen text-brown-500">Chargement…</div>;

  const booked = slots.filter((s) => s.status === 'BOOKED').length;
  const available = slots.filter((s) => s.status === 'AVAILABLE').length;

  return (
    <>
      <Head><title>Planning — Kaho</title></Head>
      <header className="bg-white border-b border-cream-200">
        <div className="container flex items-center justify-between py-3">
          <Logo />
          <button onClick={() => { logout(); router.push('/login'); }} className="btn-secondary">Déconnexion</button>
        </div>
      </header>

      <main className="container py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl">Planning</h1>
          <button className="btn-primary">+ Créneau</button>
        </div>

        <div className="grid sm:grid-cols-3 gap-4 mb-8">
          <div className="card py-4"><p className="text-sm text-brown-800/70">Réservés</p><p className="text-3xl font-display">{booked}</p></div>
          <div className="card py-4"><p className="text-sm text-brown-800/70">Disponibles</p><p className="text-3xl font-display">{available}</p></div>
          <button className="card py-4 text-left hover:border-brown-300 transition-colors">
            <p className="text-sm text-brown-800/70">Carnet de bord</p>
            <p className="font-medium text-brown-700">Ajouter km / plein →</p>
          </button>
        </div>

        <div className="card p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-cream-100 text-brown-800/70">
              <tr>
                <th className="text-left py-3 px-4 font-medium">Date</th>
                <th className="text-left py-3 px-4 font-medium">Heure</th>
                <th className="text-left py-3 px-4 font-medium">Lieu</th>
                <th className="text-left py-3 px-4 font-medium">Élève</th>
                <th className="text-left py-3 px-4 font-medium">Statut</th>
              </tr>
            </thead>
            <tbody>
              {slots.length === 0 ? (
                <tr><td colSpan={5} className="text-center py-10 text-brown-800/60">Aucun créneau pour le moment</td></tr>
              ) : slots.map((s) => (
                <tr key={s.id} className="border-t border-cream-200 hover:bg-cream-50">
                  <td className="py-3 px-4">{s.date}</td>
                  <td className="py-3 px-4">{s.start_time.slice(0, 5)} – {s.end_time.slice(0, 5)}</td>
                  <td className="py-3 px-4">{s.meeting_point_name}</td>
                  <td className="py-3 px-4">{s.student_name || '—'}</td>
                  <td className="py-3 px-4"><span className={`badge ${statusStyle[s.status].cls}`}>{statusStyle[s.status].label}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </>
  );
}
