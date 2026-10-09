import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { BACKOFFICE, useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import ProgressGauge from '@/components/ProgressGauge';
import PdfLink from '@/components/PdfLink';
import StudentActions, { ActionKey } from '@/components/StudentActions';
import { ActivityEntry, InstructorAdmin, StudentOverview, downloadFile } from '@/lib/admin';
import { formatPrice } from '@/lib/offers';
import { FreeWindow, MeetingPoint, STUDENT_STATUSES, apiError, frDate, hm, statusOf } from '@/lib/types';
import { ActivityList } from '../activity';
import { ReadinessGauge, ScoreChart, StatTiles, TopicBars } from '@/components/LmsAnalytics';
import { StudentLmsReport } from '@/lib/lms';

const DOC_TYPES = [['IDENTITY', 'Pièce d’identité'], ['PHOTO', 'ePhoto'], ['PROOF_ADDRESS', 'Justificatif de domicile'], ['JDC', 'Attestation JDC'], ['NEPH_CERTIFICATE', 'Attestation NEPH'], ['CONTRACT', 'Contrat signé']];

/** Réservation d'une leçon pour l'élève depuis sa fiche : date → créneaux libres → confirmation. */
function BookForStudent({ studentId, onDone }: { studentId: number; onDone: (text: string, ok?: boolean) => void }) {
  const [date, setDate] = useState('');
  const [instructor, setInstructor] = useState('');
  const [instructors, setInstructors] = useState<InstructorAdmin[]>([]);
  const [points, setPoints] = useState<MeetingPoint[]>([]);
  const [point, setPoint] = useState('');
  const [windows, setWindows] = useState<FreeWindow[] | null>(null);
  const [sel, setSel] = useState<FreeWindow | null>(null);
  const [force, setForce] = useState(false);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    api.get('/admin/instructors/', { params: { page_size: 200, active: 1 } }).then((r) => setInstructors(r.data.results));
    api.get('/meeting-points/').then((r) => { setPoints(r.data); if (r.data[0]) setPoint(String(r.data[0].id)); });
  }, []);
  useEffect(() => {
    if (!date) { setWindows(null); return; }
    api.get('/slots/free/', { params: { date, instructor: instructor || undefined } }).then((r) => { setWindows(r.data); setSel(null); });
  }, [date, instructor]);
  const book = async () => {
    if (!sel) return;
    setBusy(true);
    try {
      await api.post(`/admin/students/${studentId}/book/`, { instructor: sel.instructor_id, meeting_point: point || null, date: sel.date, start_time: sel.start_time, end_time: sel.end_time, force });
      onDone(`Leçon réservée le ${frDate(sel.date, { day: 'numeric', month: 'short' })} à ${sel.start_time} avec ${sel.instructor_name} (élève prévenu par email).`);
      setSel(null); setDate('');
    } catch (err) { onDone(apiError(err, 'Réservation impossible.'), false); }
    finally { setBusy(false); }
  };
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-2">
        <input type="date" value={date} min={new Date().toISOString().slice(0, 10)} onChange={(e) => setDate(e.target.value)} className="input-field !py-2" />
        <select value={instructor} onChange={(e) => setInstructor(e.target.value)} className="input-field !py-2"><option value="">Tous les moniteurs</option>{instructors.map((i) => <option key={i.id} value={i.id}>{i.full_name}</option>)}</select>
      </div>
      {windows && (windows.length === 0 ? <p className="text-sm text-brown-800/60">Aucun créneau libre ce jour-là.</p> : (
        <div className="flex flex-wrap gap-1.5 max-h-40 overflow-auto">
          {windows.map((w) => <button key={`${w.instructor_id}-${w.start_time}`} onClick={() => setSel(w)} className={`badge !px-2.5 !py-1.5 ${sel === w ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800 hover:bg-cream-200'}`}>{w.start_time} · {w.instructor_name.split(' ')[0]}</button>)}
        </div>
      ))}
      {sel && (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <select value={point} onChange={(e) => setPoint(e.target.value)} className="input-field !py-2 w-48">{points.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}<option value="">Lieu à convenir</option></select>
          <label className="flex items-center gap-1 text-xs"><input type="checkbox" checked={force} onChange={(e) => setForce(e.target.checked)} className="accent-brown-700" /> forcer même sans crédit</label>
          <button onClick={book} disabled={busy} className="btn-primary !py-2 text-sm">Réserver {sel.start_time}–{sel.end_time}</button>
        </div>
      )}
    </div>
  );
}

export default function AdminStudentDetail() {
  const ready = useRequireAuth(BACKOFFICE);
  const router = useRouter();
  const id = typeof router.query.id === 'string' ? router.query.id : null;
  const [d, setD] = useState<StudentOverview | null>(null);
  const [history, setHistory] = useState<ActivityEntry[]>([]);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [tab, setTab] = useState<'overview' | 'lessons' | 'slots' | 'history' | 'code'>('overview');
  const [lms, setLms] = useState<StudentLmsReport | null>(null);
  const [action, setAction] = useState<ActionKey | undefined>(undefined);
  const [uploadType, setUploadType] = useState('IDENTITY');
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(() => id && Promise.all([
    api.get(`/admin/students/${id}/overview/`).then((r) => setD(r.data)),
    api.get('/admin/activity/', { params: { student: id, page_size: 50 } }).then((r) => setHistory(r.data.results)),
    api.get(`/lms/admin/students/${id}/`).then((r) => setLms(r.data)).catch(() => {}),
  ]), [id]);
  useEffect(() => { if (ready && id) load(); }, [ready, id, load]);

  const act = async (fn: () => Promise<unknown>, okText: string) => {
    setMsg(null);
    try { await fn(); await load(); setMsg({ ok: true, text: okText }); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Action impossible.') }); }
  };
  const patch = (data: object, okText = 'Profil mis à jour.') => act(() => api.patch(`/admin/students/${id}/update_profile/`, data), okText);
  const upload = async (f: File | undefined) => {
    if (!f) return;
    const fd = new FormData(); fd.append('document_type', uploadType); fd.append('file', f);
    await act(() => api.post(`/admin/students/${id}/upload_document/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } }), 'Pièce déposée et validée.');
    if (fileRef.current) fileRef.current.value = '';
  };
  const focusAction = (k: ActionKey) => { setAction(k); window.scrollTo({ top: 0, behavior: 'smooth' }); };

  if (!d) return <AdminShell title="Élève"><p className="text-brown-500">Chargement…</p></AdminShell>;
  const s = d.student;
  const stIndex = STUDENT_STATUSES.findIndex((x) => x.key === s.status);

  return (
    <AdminShell title={`${s.user.first_name} ${s.user.last_name}`} wide>
      <Link href="/admin/students" className="text-sm text-brown-700 hover:underline">← Apprenants</Link>
      <div className="flex flex-wrap items-start justify-between gap-3 mt-2 mb-4">
        <div>
          <h1 className="text-3xl">{s.user.first_name} {s.user.last_name}</h1>
          <p className="text-brown-800/70">{s.user.email}{s.phone && ` · ${s.phone}`} · inscrit le {frDate(s.created_at ?? new Date().toISOString(), { day: 'numeric', month: 'short', year: 'numeric' })}</p>
        </div>
        <div className="flex gap-2 flex-wrap items-center">
          <span className={`badge ${statusOf(s.status).cls}`}>{s.status_display}</span>
          {s.ready_for_exam && <span className="badge bg-caramel text-brown-900">Prêt pour l'examen</span>}
          {s.has_lms_access && <span className="badge bg-brown-700 text-cream-50">Code en ligne</span>}
          <button onClick={() => downloadFile(`/admin/students/${id}/contract/`, `contrat-${s.user.last_name.toLowerCase()}.pdf`)} className="btn-secondary !py-1.5 text-sm">Contrat PDF</button>
        </div>
      </div>

      <div className="flex flex-wrap gap-1 mb-6" role="group" aria-label="Statut du parcours">
        {STUDENT_STATUSES.map((st, i) => (
          <button key={st.key} onClick={() => st.key !== s.status && confirm(`Passer ${s.user.first_name} au statut « ${st.label} » ?`) && act(() => api.post(`/admin/students/${id}/set_status/`, { status: st.key }), `Statut : ${st.label}.`)}
            className={`text-xs rounded-full px-3 py-1.5 border ${st.key === s.status ? 'bg-brown-700 text-cream-50 border-brown-700' : i < stIndex ? 'bg-brown-100 border-brown-200 text-brown-800' : 'bg-white border-cream-300 text-brown-800/70 hover:border-brown-300'}`}>{i + 1}. {st.label}</button>
        ))}
      </div>

      {msg && <div className={`rounded-xl px-4 py-3 mb-6 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}

      <div className="flex gap-1 mb-6 flex-wrap">
        {([['overview', 'Vue d’ensemble'], ['code', `Code en ligne${lms ? ` (${lms.readiness ?? '—'} %)` : ''}`], ['lessons', `Bilans (${d.lessons.length})`], ['slots', `Créneaux (${d.upcoming_slots.length + d.past_slots.length})`], ['history', `Historique (${history.length})`]] as const).map(([k, l]) => (
          <button key={k} onClick={() => setTab(k)} className={`badge !px-4 !py-2 ${tab === k ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>{l}</button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="grid lg:grid-cols-3 gap-6">
          <section className="card lg:col-span-2">
            <h2 className="text-xl mb-3">Actions</h2>
            <StudentActions student={s} initial={action} onDone={(text) => { setMsg({ ok: true, text }); load(); }} />
          </section>

          <section className="card">
            <h2 className="text-xl mb-3">Heures & suivi</h2>
            <dl className="text-sm space-y-1 mb-4">
              <div className="flex justify-between"><dt className="text-brown-800/70">Achetées</dt><dd className="font-semibold">{s.purchased_hours.toFixed(1)} h</dd></div>
              <div className="flex justify-between"><dt className="text-brown-800/70">Effectuées</dt><dd>{s.used_hours.toFixed(1)} h</dd></div>
              <div className="flex justify-between"><dt className="text-brown-800/70">Réservées à venir</dt><dd>{s.reserved_hours.toFixed(1)} h</dd></div>
              <div className="flex justify-between border-t border-cream-200 pt-1"><dt className="text-brown-800/70">Restantes</dt><dd className={`font-semibold ${s.remaining_hours <= 1 ? 'text-red-700' : ''}`}>{s.remaining_hours.toFixed(1)} h</dd></div>
            </dl>
            <ProgressGauge progress={d.progress} compact />
            <div className="mt-4 space-y-3 text-sm">
              <p><span className="text-brown-800/70">Moniteur référent :</span> {s.referent_instructor_name || '—'} <button onClick={() => focusAction('referent')} className="text-brown-700 text-xs hover:underline">modifier</button></p>
              <label className="block"><span className="text-brown-800/70">Boîte</span>
                <select value={s.license_type} onChange={(e) => patch({ license_type: e.target.value })} className="input-field !py-2 mt-1"><option value="AUTO">Automatique</option><option value="MANUAL">Manuelle</option></select></label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={s.ready_for_exam} onChange={(e) => patch({ ready_for_exam: e.target.checked })} className="accent-brown-700" /> Prêt pour l'examen</label>
            </div>
          </section>

          <section className="card">
            <h2 className="text-xl mb-3">Planifier une leçon</h2>
            <p className="text-sm text-brown-800/70 mb-3">Réservation pour le compte de l'élève, confirmée par email.</p>
            <BookForStudent studentId={s.id} onDone={(text, ok = true) => { setMsg({ ok, text }); if (ok) load(); }} />
          </section>

          <section className="card">
            <h2 className="text-xl mb-3">Coordonnées</h2>
            <dl className="text-sm space-y-2">
              {([['phone', 'Mobile'], ['neph_number', 'N° NEPH'], ['emergency_contact', 'Contact d’urgence'], ['emergency_phone', 'Tél. urgence']] as const).map(([k, l]) => (
                <label key={k} className="block"><span className="text-brown-800/70">{l}</span>
                  <input defaultValue={(s as any)[k] || ''} onBlur={(e) => e.target.value !== ((s as any)[k] || '') && patch({ [k]: e.target.value })} className="input-field !py-2 mt-1" /></label>
              ))}
            </dl>
          </section>

          <section className="card">
            <h2 className="text-xl mb-1">Dossier administratif {d.dossier.complete ? <span className="badge bg-brown-700 text-cream-50 ml-1">complet</span> : <span className="badge bg-cream-200 text-brown-800 ml-1">incomplet</span>}</h2>
            <ul className="text-sm space-y-2 mb-4">
              {d.dossier.items.map((item) => {
                const doc = d.documents.find((x) => x.document_type === item.type);
                return (
                  <li key={item.type} className="border-t border-cream-200 pt-2">
                    <div className="flex items-center justify-between gap-2">
                      <span>{item.label}{!item.required && <span className="text-xs text-brown-800/50"> (si &lt; 25 ans)</span>}</span>
                      <span className={`badge ${item.status === 'VERIFIED' ? 'bg-brown-700 text-cream-50' : item.status === 'PENDING' ? 'bg-caramel text-brown-900' : item.status === 'REJECTED' ? 'bg-red-100 text-red-700' : 'bg-cream-200 text-brown-800'}`}>
                        {item.status === 'MISSING' ? 'manquant' : doc?.status_display.toLowerCase()}
                      </span>
                    </div>
                    {doc && (
                      <div className="flex flex-wrap items-center gap-2 mt-1 text-xs">
                        <a href={doc.file} target="_blank" rel="noreferrer" className="text-brown-700 hover:underline">Voir le fichier ↗</a>
                        {doc.status === 'PENDING' && <>
                          <button onClick={() => act(() => api.post(`/admin/documents/${doc.id}/verify/`), 'Pièce validée, élève prévenu.')} className="btn-primary !py-0.5 !px-2 text-xs">Valider</button>
                          <button onClick={() => { const n = prompt('Motif du refus (envoyé à l’élève) :'); if (n) act(() => api.post(`/admin/documents/${doc.id}/reject/`, { note: n }), 'Pièce refusée, élève prévenu.'); }} className="text-red-700 hover:underline">Refuser</button>
                        </>}
                        {doc.status === 'REJECTED' && <span className="text-red-700">{doc.review_note}</span>}
                        {doc.status === 'VERIFIED' && doc.verified_by_name && <span className="text-brown-800/50">par {doc.verified_by_name}</span>}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
            <div className="border-t border-cream-200 pt-3 text-sm">
              <p className="text-brown-800/70 mb-2">Déposer une pièce pour l'élève (validée d'office) :</p>
              <div className="flex gap-2">
                <select value={uploadType} onChange={(e) => setUploadType(e.target.value)} className="input-field !py-1.5 text-xs">{DOC_TYPES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
                <input ref={fileRef} type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => upload(e.target.files?.[0])} className="text-xs" aria-label="Fichier" />
              </div>
            </div>
          </section>

          <section className="card lg:col-span-3">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
              <h2 className="text-xl">Achats & règlements</h2>
              <div className="flex gap-2"><button onClick={() => focusAction('payment')} className="btn-secondary !py-1.5 text-sm">+ Règlement reçu</button><button onClick={() => focusAction('link')} className="btn-primary !py-1.5 text-sm">Lien de paiement</button></div>
            </div>
            {d.packages.length === 0 ? <p className="text-brown-800/60 text-sm">Aucun achat.</p> : (
              <table className="w-full text-sm">
                <thead className="text-brown-800/70"><tr><th className="text-left py-2">Date</th><th className="text-left py-2">Désignation</th><th className="text-right py-2">Heures</th><th className="text-right py-2">Montant</th><th className="text-left py-2 pl-4">Règlement</th><th className="text-left py-2">Statut</th><th className="text-left py-2">Note</th><th className="py-2"></th></tr></thead>
                <tbody>
                  {d.packages.map((p) => (
                    <tr key={p.id} className="border-t border-cream-200 align-top">
                      <td className="py-2 whitespace-nowrap">{new Date(p.created_at).toLocaleDateString('fr-FR')}</td>
                      <td className="py-2">{p.display_label}</td>
                      <td className="py-2 text-right">{p.hours_purchased ? `${p.hours_purchased} h` : '—'}</td>
                      <td className="py-2 text-right">{formatPrice(p.amount_paid)}</td>
                      <td className="py-2 pl-4 text-xs">{p.payment_method ? p.payment_method_display : '—'}{p.stripe_checkout_url && p.status === 'PENDING' && <><br /><a href={p.stripe_checkout_url} target="_blank" rel="noreferrer" className="text-brown-700 hover:underline">lien de paiement ↗</a></>}</td>
                      <td className="py-2"><span className={`badge ${p.status === 'COMPLETED' ? 'bg-brown-700 text-cream-50' : p.status === 'PENDING' ? 'bg-caramel text-brown-900' : 'bg-red-100 text-red-700'}`}>{p.status_display}</span></td>
                      <td className="py-2 text-xs text-brown-800/60 whitespace-pre-line max-w-xs">{p.note}</td>
                      <td className="py-2 text-right whitespace-nowrap space-x-2">
                        {p.invoice_id && p.invoice_number && <PdfLink invoiceId={p.invoice_id} number={p.invoice_number} className="text-brown-700 text-xs hover:underline" />}
                        {p.status === 'PENDING' && <>
                          <button onClick={() => { const m = prompt('Mode de règlement reçu : CASH, CHECK, TRANSFER, CPF ou STRIPE', 'TRANSFER'); if (m) act(() => api.post(`/admin/packages/${p.id}/mark_paid/`, { method: m.toUpperCase() }), 'Paiement validé, heures et accès crédités.'); }} className="btn-primary !py-1 text-xs">Valider le paiement</button>
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
            <thead className="bg-cream-100 text-brown-800/70"><tr><th className="text-left py-3 px-4">Date</th><th className="text-left py-3 px-4">Heure</th><th className="text-left py-3 px-4">Moniteur</th><th className="text-left py-3 px-4">Lieu</th><th className="text-left py-3 px-4">Statut</th><th></th></tr></thead>
            <tbody>
              {[...d.upcoming_slots, ...d.past_slots].map((sl) => (
                <tr key={sl.id} className="border-t border-cream-200"><td className="py-2 px-4">{frDate(sl.date, { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })}</td><td className="py-2 px-4">{hm(sl.start_time)}–{hm(sl.end_time)}</td><td className="py-2 px-4">{sl.instructor_name}</td><td className="py-2 px-4">{sl.meeting_point_name}</td><td className="py-2 px-4">{sl.status_display}{sl.hours_refunded && ' · re-crédité'}</td>
                  <td className="py-2 px-4 text-right text-xs">{sl.status === 'BOOKED' && !sl.is_past && <button onClick={() => confirm('Annuler cette leçon (sans débit) ?') && act(() => api.post(`/slots/${sl.id}/cancel/`), 'Leçon annulée.')} className="text-red-700 hover:underline">Annuler</button>}{(sl.status === 'NO_SHOW' || sl.status === 'CANCELLED_LATE') && sl.hours_debited && !sl.hours_refunded && <button onClick={() => { const n = prompt('Justificatif du re-crédit :'); if (n) act(() => api.post(`/slots/${sl.id}/refund/`, { note: n }), 'Heure re-créditée.'); }} className="text-brown-700 hover:underline">Re-créditer</button>}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'code' && (
        !lms ? <p className="text-brown-500">Chargement…</p> : (
          <div className="grid lg:grid-cols-3 gap-6">
            <section className="card lg:col-span-2">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-4"><h2 className="text-xl">Préparation à l'examen du code</h2>{!lms.has_lms_access && <span className="badge bg-cream-200 text-brown-800">pas d'accès actif</span>}</div>
              <div className="grid md:grid-cols-[220px_1fr] gap-6 items-start"><ReadinessGauge value={lms.readiness} count={lms.readiness_count} /><StatTiles s={lms} /></div>
              <div className="grid md:grid-cols-2 gap-6 mt-6"><div><p className="text-sm font-medium mb-2">Évolution des scores</p><ScoreChart points={lms.evolution} /></div><div><p className="text-sm font-medium mb-2">Thème par thème</p><TopicBars topics={lms.by_topic} /></div></div>
            </section>
            <section className="card">
              <h2 className="text-xl mb-2">Inscription à l'examen officiel (ETG)</h2>
              {lms.etg_validated_at ? (
                <><p className="text-sm"><span className="badge bg-brown-700 text-cream-50">Validée</span> le {frDate(lms.etg_validated_at, { day: 'numeric', month: 'short', year: 'numeric' })}{lms.etg_validated_by && ` par ${lms.etg_validated_by}`}</p>
                  <button onClick={() => confirm('Annuler la validation ?') && act(() => api.post(`/lms/admin/students/${id}/`, { cancel: true }), 'Validation annulée.')} className="text-xs text-red-700 hover:underline mt-3">Annuler la validation</button></>
              ) : (
                <><p className="text-sm text-brown-800/70 mb-3">{lms.readiness !== null && lms.readiness >= 88 ? 'Le niveau est atteint (≥ 88 % sur les derniers examens blancs).' : 'Recommandé lorsque la jauge dépasse 88 % sur les 5 derniers examens blancs.'}</p>
                  <button onClick={() => confirm(`Valider l'inscription de ${s.user.first_name} à l'examen du code ?`) && act(() => api.post(`/lms/admin/students/${id}/`), 'Inscription à l’ETG validée (tracée dans l’historique).')} className="btn-primary !py-2 text-sm">Valider l'inscription à l'ETG</button></>
              )}
              <h3 className="font-semibold text-sm mt-6 mb-2">Derniers examens blancs</h3>
              {lms.history.length === 0 ? <p className="text-sm text-brown-800/60">Aucun.</p> : <ul className="text-sm divide-y divide-cream-200">{lms.history.slice(0, 8).map((a) => <li key={a.id} className="py-1.5 flex justify-between"><span>{a.submitted_at ? frDate(a.submitted_at, { day: 'numeric', month: 'short' }) : ''} · {a.exam_title}</span><span className={a.passed ? 'text-brown-700 font-medium' : 'text-red-700'}>{a.score} %</span></li>)}</ul>}
              <h3 className="font-semibold text-sm mt-4 mb-2">Dernières séries de quiz</h3>
              {lms.quizzes.length === 0 ? <p className="text-sm text-brown-800/60">Aucune.</p> : <ul className="text-sm divide-y divide-cream-200">{lms.quizzes.slice(0, 8).map((qa) => <li key={qa.id} className="py-1.5 flex justify-between"><span>{frDate(qa.created_at, { day: 'numeric', month: 'short' })} · {qa.quiz_title}</span><span className={qa.passed ? 'text-brown-700 font-medium' : 'text-red-700'}>{qa.score} %</span></li>)}</ul>}
            </section>
          </div>
        )
      )}

      {tab === 'history' && (
        <div className="card">{history.length === 0 ? <p className="text-sm text-brown-800/60">Aucun événement.</p> : <ActivityList items={history} />}</div>
      )}
    </AdminShell>
  );
}
