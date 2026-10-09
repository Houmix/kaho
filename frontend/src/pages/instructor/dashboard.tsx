import { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AppShell from '@/components/AppShell';
import { InstructorDashboard, Slot, frDate, hm } from '@/lib/types';
import { formatPrice } from '@/lib/offers';

function SlotRow({ s }: { s: Slot }) {
  return (
    <li className="flex items-center justify-between gap-3 py-2 border-t border-cream-200 first:border-t-0">
      <div>
        <div className="font-semibold">{hm(s.start_time)} – {hm(s.end_time)} · {s.student_name ?? 'Libre'}</div>
        <div className="text-sm text-brown-800/70">{frDate(s.date, { weekday: 'short', day: 'numeric', month: 'short' })} · {s.meeting_point_name}</div>
      </div>
    </li>
  );
}

export default function InstructorHome() {
  const ready = useRequireAuth('INSTRUCTOR');
  const { user } = useAuth();
  const [data, setData] = useState<InstructorDashboard | null>(null);

  useEffect(() => {
    if (!ready) return;
    api.get('/instructors/dashboard/').then((r) => setData(r.data));
  }, [ready]);

  if (!data) return <AppShell title="Tableau de bord"><p className="text-brown-500">Chargement…</p></AppShell>;

  const month = new Date().toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });

  return (
    <AppShell title="Tableau de bord">
      <h1 className="text-3xl mb-6">Bonjour, {user?.first_name}</h1>

      {data.to_review.length > 0 && (
        <section className="card mb-6 border-caramel bg-brown-50">
          <h2 className="text-xl mb-2">Bilans à saisir ({data.to_review.length})</h2>
          <ul className="divide-y divide-cream-200">
            {data.to_review.map((s) => (
              <li key={s.id} className="py-2 flex items-center justify-between gap-3">
                <span>{frDate(s.date, { weekday: 'short', day: 'numeric', month: 'short' })} · {hm(s.start_time)} · <strong>{s.student_name}</strong></span>
                <Link href={`/instructor/lesson/${s.id}`} className="btn-primary !py-1.5 text-sm">Saisir le bilan</Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="grid sm:grid-cols-4 gap-4 mb-8">
        <div className="card py-4"><p className="text-sm text-brown-800/70">Aujourd'hui</p><p className="text-3xl font-display">{data.today.length} <span className="text-base font-sans">leçon{data.today.length > 1 ? 's' : ''}</span></p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Avis élèves</p><p className="text-3xl font-display">{data.rating.average !== null ? `${data.rating.average.toFixed(1)}/5` : '—'}</p><p className="text-xs text-brown-800/60">{data.rating.count} avis</p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Heures effectuées — {month}</p><p className="text-3xl font-display">{data.month.hours} h</p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Montant — {month}</p><p className="text-3xl font-display">{formatPrice(data.month.amount)}</p><p className="text-xs text-brown-800/60">{data.month.lessons} leçons × {formatPrice(data.month.hourly_rate)}/h</p></div>
      </div>

      {!data.profile.is_bookable && (
        <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 mb-6 text-sm">
          Vous n'êtes pas réservable par les élèves pour le moment (réglage administrateur).
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <section className="card">
          <h2 className="text-xl mb-3">Aujourd'hui</h2>
          {data.today.length === 0 ? <p className="text-brown-800/60">Rien de prévu.</p> : <ul>{data.today.map((s) => <SlotRow key={s.id} s={s} />)}</ul>}
        </section>
        <section className="card">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xl">À venir</h2>
            <Link href="/instructor/planning" className="text-sm text-brown-700 hover:underline">Tout le planning →</Link>
          </div>
          {data.upcoming.length === 0 ? <p className="text-brown-800/60">Aucune réservation à venir.</p> : <ul>{data.upcoming.slice(0, 8).map((s) => <SlotRow key={s.id} s={s} />)}</ul>}
        </section>
      </div>

      <section className="card mb-8">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl">Mes élèves</h2>
          <span className="text-sm text-brown-800/60">{data.students.length}</span>
        </div>
        {data.students.length === 0 ? (
          <p className="text-brown-800/60">Aucun élève pour le moment — ils apparaîtront dès leur première réservation avec vous.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-brown-800/70"><tr><th className="text-left py-2">Élève</th><th className="text-left py-2">Boîte</th><th className="text-right py-2">Compétences</th><th className="text-right py-2">Faites</th><th className="text-right py-2">Restantes</th><th className="text-left py-2 pl-4">Examen</th></tr></thead>
              <tbody>
                {data.students.map((st) => (
                  <tr key={st.id} className="border-t border-cream-200">
                    <td className="py-2"><Link href={`/instructor/students/${st.id}?from=dashboard`} className="font-medium text-brown-700 hover:underline">{st.user.first_name} {st.user.last_name}</Link></td>
                    <td className="py-2">{st.license_type === 'AUTO' ? 'Auto' : 'Manuelle'}</td>
                    <td className="py-2 text-right">{st.competency_progress.percent} %</td>
                    <td className="py-2 text-right">{st.used_hours.toFixed(1)} h</td>
                    <td className="py-2 text-right">{st.remaining_hours.toFixed(1)} h</td>
                    <td className="py-2 pl-4">{st.ready_for_exam ? <span className="badge bg-brown-700 text-cream-50">Prêt</span> : <span className="badge bg-cream-200 text-brown-800">En cours</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <Link href="/instructor/availability" className="btn-outline">Gérer mes disponibilités →</Link>
    </AppShell>
  );
}
