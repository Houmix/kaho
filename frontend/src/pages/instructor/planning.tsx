import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { STAFF_ROLES, useRequireAuth } from '@/hooks/useRequireAuth';
import AppShell from '@/components/AppShell';
import BackLink, { studentHref } from '@/components/BackLink';
import { Slot, apiError, frDate, hm } from '@/lib/types';

const statusCls: Record<Slot['status'], string> = {
  BOOKED: 'bg-brown-700 text-cream-50',
  AVAILABLE: 'bg-cream-200 text-brown-800',
  CANCELLED: 'bg-cream-100 text-brown-800/60',
  CANCELLED_LATE: 'bg-caramel/40 text-brown-900',
  NO_SHOW: 'bg-red-100 text-red-700',
};

export default function InstructorPlanning() {
  const ready = useRequireAuth(STAFF_ROLES);
  const { user } = useAuth();
  const [slots, setSlots] = useState<Slot[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<'upcoming' | 'past' | 'all'>('upcoming');
  const [message, setMessage] = useState('');

  const load = useCallback(() => api.get('/slots/').then((r) => setSlots(r.data.results ?? r.data)).finally(() => setIsLoading(false)), []);
  useEffect(() => { if (ready) load(); }, [ready, load]);

  const act = async (path: string, body?: object) => {
    setMessage('');
    try { await api.post(path, body); await load(); }
    catch (err) { setMessage(apiError(err, 'Action impossible.')); }
  };
  const noShow = (s: Slot) => { if (confirm(`Marquer ${s.student_name} absent le ${frDate(s.date)} à ${hm(s.start_time)} ? L'heure sera décomptée.`)) act(`/slots/${s.id}/no_show/`); };
  const refund = (s: Slot) => { const note = prompt('Justificatif de la dérogation (ex : certificat médical du …) :'); if (note) act(`/slots/${s.id}/refund/`, { note }); };
  const cancel = (s: Slot) => {
    if (!confirm(`Annuler le créneau du ${frDate(s.date)} à ${hm(s.start_time)} (sans frais pour l'élève) ?`)) return;
    const reason = prompt('Motif de l’annulation (facultatif) :') ?? '';
    act(`/slots/${s.id}/cancel/`, { reason });
  };

  if (isLoading) return <AppShell title="Planning"><p className="text-brown-500">Chargement…</p></AppShell>;

  const isSupervisor = user?.role === 'SUPERVISOR' || user?.role === 'ADMIN' || user?.role === 'OWNER';
  const opensAt = (s: Slot) => new Date(s.assessment_opens_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  const visible = slots.filter((s) => filter === 'all' || (filter === 'past' ? s.is_past : !s.is_past));
  const counts = {
    booked: slots.filter((s) => s.status === 'BOOKED' && !s.is_past).length,
    toReview: slots.filter((s) => s.status === 'BOOKED' && s.can_assess && !s.has_lesson).length,
    noShow: slots.filter((s) => s.status === 'NO_SHOW' || s.status === 'CANCELLED_LATE').length,
  };

  return (
    <AppShell title="Planning">
      {isSupervisor && <BackLink fallbackHref="/admin" fallbackLabel="← Retour au tableau de bord" />}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <h1 className="text-3xl">Planning</h1>
        <div className="flex gap-1">
          {(['upcoming', 'past', 'all'] as const).map((f) => (
            <button key={f} onClick={() => setFilter(f)} className={`badge !px-4 !py-2 ${filter === f ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>
              {f === 'upcoming' ? 'À venir' : f === 'past' ? 'Passés' : 'Tous'}
            </button>
          ))}
        </div>
      </div>

      {message && <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 mb-6 text-sm">{message}</div>}

      <div className="grid sm:grid-cols-3 gap-4 mb-8">
        <div className="card py-4"><p className="text-sm text-brown-800/70">Réservés à venir</p><p className="text-3xl font-display">{counts.booked}</p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Bilans à saisir</p><p className="text-3xl font-display">{counts.toReview}</p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Absences / annul. tardives</p><p className="text-3xl font-display">{counts.noShow}</p></div>
      </div>

      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-cream-100 text-brown-800/70">
            <tr>
              <th className="text-left py-3 px-4 font-medium">Date</th>
              <th className="text-left py-3 px-4 font-medium">Heure</th>
              <th className="text-left py-3 px-4 font-medium">Lieu</th>
              <th className="text-left py-3 px-4 font-medium">Moniteur</th>
              <th className="text-left py-3 px-4 font-medium">Élève</th>
              <th className="text-left py-3 px-4 font-medium">Statut</th>
              <th className="text-left py-3 px-4 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-10 text-brown-800/60">Aucun créneau</td></tr>
            ) : visible.map((s) => (
              <tr key={s.id} className="border-t border-cream-200 hover:bg-cream-50">
                <td className="py-3 px-4 whitespace-nowrap">{frDate(s.date, { weekday: 'short', day: 'numeric', month: 'short' })}</td>
                <td className="py-3 px-4 whitespace-nowrap">{hm(s.start_time)} – {hm(s.end_time)}</td>
                <td className="py-3 px-4">{s.meeting_point_name}</td>
                <td className="py-3 px-4">{s.instructor_name}</td>
                <td className="py-3 px-4">
                  {s.student && s.student_name
                    ? <Link href={studentHref(isSupervisor, s.student, 'planning')} className="font-medium text-brown-700 hover:underline" title="Ouvrir la fiche élève">{s.student_name}</Link>
                    : '—'}
                </td>
                <td className="py-3 px-4">
                  <span className={`badge ${statusCls[s.status]}`}>{s.status_display}</span>
                  {s.hours_refunded && <span className="badge bg-cream-200 text-brown-800 ml-1" title={s.refund_note}>re-crédité</span>}
                  {Number(s.cancellation_fee) > 0 && <span className="badge bg-caramel/40 text-brown-900 ml-1">frais {Number(s.cancellation_fee).toFixed(0)} €</span>}
                  {s.cancel_reason && <div className="text-xs text-brown-800/60 mt-1 max-w-[16rem] truncate" title={s.cancel_reason}>Motif : {s.cancel_reason}</div>}
                </td>
                <td className="py-3 px-4 whitespace-nowrap space-x-2">
                  {s.status === 'BOOKED' && s.is_past && !s.has_lesson && <>
                    {s.can_assess
                      ? <Link href={`/instructor/lesson/${s.id}?from=planning`} className="text-brown-700 font-medium hover:underline">Bilan</Link>
                      : <span className="text-brown-800/50" title="Le bilan s'ouvre dans les 10 dernières minutes de la leçon">🔒 Bilan dès {opensAt(s)}</span>}
                    <button onClick={() => noShow(s)} className="text-red-700 hover:underline">Absent</button>
                  </>}
                  {s.has_lesson && <Link href={`/instructor/lesson/${s.id}?from=planning`} className="text-brown-700 hover:underline">Voir le bilan</Link>}
                  {s.status === 'BOOKED' && !s.is_past && <button onClick={() => cancel(s)} className="text-brown-800/60 hover:underline">Annuler</button>}
                  {isSupervisor && ((s.hours_debited && !s.hours_refunded) || Number(s.cancellation_fee) > 0) && <button onClick={() => refund(s)} className="text-brown-700 hover:underline">Re-créditer</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
