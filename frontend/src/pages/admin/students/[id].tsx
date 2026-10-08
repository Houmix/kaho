import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import ProgressGauge from '@/components/ProgressGauge';
import { InstructorAdmin, StudentOverview } from '@/lib/admin';
import { formatPrice } from '@/lib/offers';
import { apiError, frDate, hm } from '@/lib/types';

export default function AdminStudentDetail() {
  const ready = useRequireAuth(['SUPERVISOR', 'ADMIN']);
  const router = useRouter();
  const id = typeof router.query.id === 'string' ? router.query.id : null;
  const [d, setD] = useState<StudentOverview | null>(null);
  const [instructors, setInstructors] = useState<InstructorAdmin[]>([]);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [hours, setHours] = useState({ hours: '', note: '' });
  const [tab, setTab] = useState<'overview' | 'lessons' | 'slots'>('overview');

  const load = useCallback(() => id && api.get(`/admin/students/${id}/overview/`).then((r) => setD(r.data)), [id]);
  useEffect(() => { if (ready && id) { load(); api.get('/admin/instructors/', { params: { page_size: 200 } }).then((r) => setInstructors(r.data.results)); } }, [ready, id, load]);

  const act = async (fn: () => Promise<unknown>, okText: string) => {
    setMsg(null);
    try { await fn(); await load(); setMsg({ ok: true, text: okText }); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Action impossible.') }); }
  };
  const patch = (data: object, okText = 'Profil mis à jour.') => act(() => api.patch(`/admin/students/${id}/update_profile/`, data), okText);

  if (!d) return <AdminShell title="Élève"><p className="text-brown-500">Chargement…</p></AdminShell>;
  const s = d.student;

  return (
    <AdminShell title={`${s.user.first_name} ${s.user.last_name}`}>
      <Link href="/admin/students" className="text-sm text-brown-700 hover:underline">← Apprenants</Link>
      <div className="flex flex-wrap items-start justify-between gap-3 mt-2 mb-6">
        <div>
          <h1 className="text-3xl">{s.user.first_name} {s.user.last_name}</h1>
          <p className="text-brown-800/70">{s.user.email}{s.phone && ` · ${s.phone}`} · inscrit le {frDate(s.created_at ?? new Date().toISOString(), { day: 'numeric', month: 'short', year: 'numeric' })}</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {s.ready_for_exam ? <span className="badge bg-caramel text-brown-900">Prêt pour l'examen</span> : null}
          {s.has_lms_access && <span className="badge bg-brown-700 text-cream-50">Code en ligne</span>}
        </div>
      </div>

      {msg && <div className={`rounded-xl px-4 py-3 mb-6 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}

      <div className="flex gap-1 mb-6">
        {([['overview', 'Vue d’ensemble'], ['lessons', `Bilans (${d.lessons.length})`], ['slots', `Créneaux (${d.upcoming_slots.length + d.past_slots.length})`]] as const).map(([k, l]) => (
          <button key={k} onClick={() => setTab(k)} className={`badge !px-4 !py-2 ${tab === k ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>{l}</button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="grid lg:grid-cols-3 gap-6">
          <section className="card">
            <h2 className="text-xl mb-3">Heures</h2>
            <dl className="text-sm space-y-1 mb-4">
              <div className="flex justify-between"><dt className="text-brown-800/70">Achetées</dt><dd className="font-semibold">{s.purchased_hours.toFixed(1)} h</dd></div>
              <div className="flex justify-between"><dt className="text-brown-800/70">Effectuées</dt><dd>{s.used_hours.toFixed(1)} h</dd></div>
              <div className="flex justify-between"><dt className="text-brown-800/70">Réservées à venir</dt><dd>{s.reserved_hours.toFixed(1)} h</dd></div>
              <div className="flex justify-between border-t border-cream-200 pt-1"><dt className="text-brown-800/70">Restantes</dt><dd className={`font-semibold ${s.remaining_hours <= 1 ? 'text-red-700' : ''}`}>{s.remaining_hours.toFixed(1)} h</dd></div>
            </dl>
            <form onSubmit={(e) => { e.preventDefault(); act(() => api.post(`/admin/students/${id}/adjust_hours/`, hours), 'Heures ajoutées.').then(() => setHours({ hours: '', note: '' })); }} className="space-y-2">
              <p className="text-xs text-brown-800/60">Ajout manuel (geste commercial, régularisation) — tracé dans les achats.</p>
              <div className="flex gap-2">
                <input type="number" step="0.5" min="0.5" placeholder="h" value={hours.hours} onChange={(e) => setHours({ ...hours, hours: e.target.value })} className="input-field w-24 !py-2" required />
                <input placeholder="Motif (obligatoire)" value={hours.note} onChange={(e) => setHours({ ...hours, note: e.target.value })} className="input-field !py-2" required />
              </div>
              <button className="btn-secondary !py-2 text-sm">Ajouter des heures</button>
            </form>
          </section>

          <section className="card">
            <h2 className="text-xl mb-3">Suivi</h2>
            <ProgressGauge progress={d.progress} compact />
            <div className="mt-4 space-y-3 text-sm">
              <label className="block"><span className="text-brown-800/70">Moniteur référent</span>
                <select value={s.referent_instructor ?? ''} onChange={(e) => patch({ referent_instructor: e.target.value || null })} className="input-field !py-2 mt-1">
                  <option value="">— aucun —</option>
                  {instructors.map((i) => <option key={i.id} value={i.id}>{i.full_name}</option>)}
                </select></label>
              <label className="block"><span className="text-brown-800/70">Boîte</span>
                <select value={s.license_type} onChange={(e) => patch({ license_type: e.target.value })} className="input-field !py-2 mt-1"><option value="AUTO">Automatique</option><option value="MANUAL">Manuelle</option></select></label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={s.ready_for_exam} onChange={(e) => patch({ ready_for_exam: e.target.checked })} className="accent-brown-700" /> Prêt pour l'examen</label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={s.lms_access} onChange={(e) => patch({ lms_access: e.target.checked })} className="accent-brown-700" /> Accès code en ligne {s.lms_access_until && <span className="text-brown-800/60">(jusqu'au {frDate(s.lms_access_until, { day: 'numeric', month: 'short', year: 'numeric' })})</span>}</label>
            </div>
          </section>

          <section className="card">
            <h2 className="text-xl mb-3">Coordonnées</h2>
            <dl className="text-sm space-y-2">
              {([['phone', 'Mobile'], ['neph_number', 'N° NEPH'], ['emergency_contact', 'Contact d’urgence'], ['emergency_phone', 'Tél. urgence']] as const).map(([k, l]) => (
                <label key={k} className="block"><span className="text-brown-800/70">{l}</span>
                  <input defaultValue={(s as any)[k] || ''} onBlur={(e) => e.target.value !== ((s as any)[k] || '') && patch({ [k]: e.target.value })} className="input-field !py-2 mt-1" /></label>
              ))}
            </dl>
            <h3 className="font-semibold mt-4 mb-2 text-sm">Documents</h3>
            {d.documents.length === 0 ? <p className="text-sm text-brown-800/60">Aucun document déposé.</p> : (
              <ul className="text-sm space-y-1">{d.documents.map((doc) => <li key={doc.id}><a href={doc.file} target="_blank" rel="noreferrer" className="text-brown-700 hover:underline">{doc.document_type}</a> {doc.verified ? '✓' : <span className="text-brown-800/50">(à vérifier)</span>}</li>)}</ul>
            )}
          </section>

          <section className="card lg:col-span-3">
            <h2 className="text-xl mb-3">Achats & paiements</h2>
            {d.packages.length === 0 ? <p className="text-brown-800/60 text-sm">Aucun achat.</p> : (
              <table className="w-full text-sm">
                <thead className="text-brown-800/70"><tr><th className="text-left py-2">Date</th><th className="text-left py-2">Offre</th><th className="text-right py-2">Heures</th><th className="text-right py-2">Montant</th><th className="text-left py-2 pl-4">Statut</th><th className="text-left py-2">Note</th><th className="py-2"></th></tr></thead>
                <tbody>
                  {d.packages.map((p) => (
                    <tr key={p.id} className="border-t border-cream-200 align-top">
                      <td className="py-2 whitespace-nowrap">{new Date(p.created_at).toLocaleDateString('fr-FR')}</td>
                      <td className="py-2">{p.offer_name || 'Ajout manuel'}</td>
                      <td className="py-2 text-right">{p.hours_purchased} h</td>
                      <td className="py-2 text-right">{formatPrice(p.amount_paid)}</td>
                      <td className="py-2 pl-4"><span className={`badge ${p.status === 'COMPLETED' ? 'bg-brown-700 text-cream-50' : p.status === 'PENDING' ? 'bg-caramel text-brown-900' : 'bg-red-100 text-red-700'}`}>{p.status_display}</span></td>
                      <td className="py-2 text-xs text-brown-800/60 whitespace-pre-line max-w-xs">{(p as any).note}</td>
                      <td className="py-2 text-right whitespace-nowrap space-x-2">
                        {p.status === 'PENDING' && <>
                          <button onClick={() => act(() => api.post(`/admin/packages/${p.id}/mark_paid/`), 'Paiement validé, heures et accès crédités.')} className="btn-primary !py-1 text-xs">Valider le paiement</button>
                          <button onClick={() => confirm('Annuler cet achat ?') && act(() => api.post(`/admin/packages/${p.id}/cancel/`), 'Achat annulé.')} className="text-red-700 text-xs hover:underline">Annuler</button>
                        </>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </div>
      )}

      {tab === 'lessons' && (
        d.lessons.length === 0 ? <p className="text-brown-800/60">Aucun bilan.</p> : (
          <div className="space-y-3">
            {d.lessons.map((l) => (
              <article key={l.id} className="card">
                <div className="flex flex-wrap justify-between gap-2"><strong>{frDate(l.slot.date)} · {hm(l.slot.start_time)} — {l.instructor_name}</strong>{!l.attended && <span className="badge bg-red-100 text-red-700">Absent</span>}{l.rating && <span className="text-caramel">{'★'.repeat(l.rating.score)}</span>}</div>
                {l.instructor_notes && <p className="mt-2 text-sm whitespace-pre-line">{l.instructor_notes}</p>}
                {l.assessments.length > 0 && <div className="flex flex-wrap gap-1 mt-2">{l.assessments.map((a) => <span key={a.competency} className="badge bg-cream-200 text-brown-800">{a.code} {a.status_display}</span>)}</div>}
                {l.rating?.comment && <p className="mt-2 text-sm text-brown-800/70">Avis de l'élève : « {l.rating.comment} »</p>}
              </article>
            ))}
          </div>
        )
      )}

      {tab === 'slots' && (
        <div className="card p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-cream-100 text-brown-800/70"><tr><th className="text-left py-3 px-4">Date</th><th className="text-left py-3 px-4">Heure</th><th className="text-left py-3 px-4">Moniteur</th><th className="text-left py-3 px-4">Lieu</th><th className="text-left py-3 px-4">Statut</th></tr></thead>
            <tbody>
              {[...d.upcoming_slots, ...d.past_slots].map((sl) => (
                <tr key={sl.id} className="border-t border-cream-200"><td className="py-2 px-4">{frDate(sl.date, { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })}</td><td className="py-2 px-4">{hm(sl.start_time)}–{hm(sl.end_time)}</td><td className="py-2 px-4">{sl.instructor_name}</td><td className="py-2 px-4">{sl.meeting_point_name}</td><td className="py-2 px-4">{sl.status_display}{sl.hours_refunded && ' · re-crédité'}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AdminShell>
  );
}
