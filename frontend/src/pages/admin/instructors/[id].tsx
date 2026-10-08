import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { BACKOFFICE, useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import { GEARBOX_LABELS, HoursBreakdown, InstructorAdmin, InstructorOverview, ReassignResult } from '@/lib/admin';
import { Unavailability, WEEKDAYS, apiError, frDate, hm } from '@/lib/types';

const thisMonth = () => new Date().toISOString().slice(0, 7);
const dt = (iso: string) => new Date(iso).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' });
const absenceCls: Record<string, string> = { PENDING: 'bg-caramel text-brown-900', APPROVED: 'bg-brown-700 text-cream-50', REJECTED: 'bg-red-100 text-red-700' };
const HOUR_LABELS: Record<string, string> = { done: 'Effectuées (payées)', no_show: 'Élève absent', cancelled_late: 'Annulées hors délai', cancelled: 'Annulées', to_review: 'Bilan à saisir', upcoming: 'À venir' };

export default function AdminInstructorDetail() {
  const ready = useRequireAuth(BACKOFFICE);
  const router = useRouter();
  const id = typeof router.query.id === 'string' ? router.query.id : null;
  const [d, setD] = useState<InstructorOverview | null>(null);
  const [absences, setAbsences] = useState<Unavailability[]>([]);
  const [hours, setHours] = useState<HoursBreakdown | null>(null);
  const [month, setMonth] = useState(thisMonth());
  const [others, setOthers] = useState<InstructorAdmin[]>([]);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [absence, setAbsence] = useState({ start: '', end: '', reason: '' });
  const [re, setRe] = useState({ start: '', end: '', target: '', notify: true });
  const [reResult, setReResult] = useState<ReassignResult | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const load = useCallback(() => id && Promise.all([
    api.get(`/admin/instructors/${id}/overview/`).then((r) => setD(r.data)),
    api.get(`/admin/instructors/${id}/absences/`).then((r) => setAbsences(r.data)),
  ]), [id]);
  useEffect(() => { if (ready && id) { load(); api.get('/admin/instructors/', { params: { page_size: 200, active: 1 } }).then((r) => setOthers(r.data.results.filter((i: InstructorAdmin) => String(i.id) !== id))); } }, [ready, id, load]);
  useEffect(() => { if (ready && id) api.get(`/admin/instructors/${id}/hours/`, { params: { month } }).then((r) => setHours(r.data)); }, [ready, id, month, d]);

  const act = async (fn: () => Promise<unknown>, okText: string) => {
    setMsg(null);
    try { await fn(); await load(); setMsg({ ok: true, text: okText }); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Action impossible.') }); }
  };
  const patch = (data: object, okText = 'Fiche mise à jour.') => act(() => api.patch(`/admin/instructors/${id}/`, data), okText);
  const resend = () => act(() => api.post(`/admin/instructors/${id}/resend_invite/`), 'Invitation renvoyée.');
  const reassign = async (e: React.FormEvent) => {
    e.preventDefault(); setMsg(null); setReResult(null);
    if (!confirm(`Réattribuer toutes les leçons du ${re.start} au ${re.end} ? Les élèves ${re.notify ? 'seront' : 'ne seront pas'} prévenus par email.`)) return;
    try { const r = await api.post(`/admin/instructors/${id}/reassign/`, re); setReResult(r.data); await load(); setMsg({ ok: true, text: `${r.data.moved.length} leçon(s) réattribuée(s), ${r.data.failed.length} conflit(s).` }); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Réattribution impossible.') }); }
  };

  if (!d) return <AdminShell title="Moniteur"><p className="text-brown-500">Chargement…</p></AdminShell>;
  const i = d.instructor;
  const p = i.profile;
  const field = (k: string, label: string, type = 'text', placeholder = '') => (
    <label className="block"><span className="text-brown-800/70 text-sm">{label}</span>
      <input type={type} step={type === 'number' ? '0.5' : undefined} placeholder={placeholder} defaultValue={(p as any)[k] ?? ''} onBlur={(e) => String((p as any)[k] ?? '') !== e.target.value && patch({ [k]: e.target.value })} className="input-field !py-2 mt-1" /></label>
  );

  return (
    <AdminShell title={i.full_name} wide>
      <Link href="/admin/instructors" className="text-sm text-brown-700 hover:underline">← Formateurs</Link>
      <div className="flex flex-wrap items-start justify-between gap-3 mt-2 mb-6">
        <div><h1 className="text-3xl">{i.full_name}</h1><p className="text-brown-800/70">{i.email}{p.phone && ` · ${p.phone}`}{p.zones && ` · ${p.zones}`}</p></div>
        <div className="flex gap-2 flex-wrap items-center">
          {!i.is_active ? <span className="badge bg-red-100 text-red-700">Compte désactivé</span> : !i.has_password ? <><span className="badge bg-caramel text-brown-900">Invitation en attente</span><button onClick={resend} className="btn-secondary !py-1.5 text-sm">Renvoyer l'invitation</button></> : <span className="badge bg-brown-700 text-cream-50">Compte actif</span>}
        </div>
      </div>
      {msg && <div className={`rounded-xl px-4 py-3 mb-6 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="card py-4"><p className="text-sm text-brown-800/70">Leçons à venir</p><p className="text-3xl font-display">{i.stats.upcoming}</p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Leçons données</p><p className="text-3xl font-display">{i.stats.lessons}</p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Élèves</p><p className="text-3xl font-display">{i.stats.students}</p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Note</p><p className="text-3xl font-display">{i.stats.rating_average !== null ? `${i.stats.rating_average.toFixed(1)} / 5` : '—'}</p><p className="text-xs text-brown-800/60">{i.stats.rating_count} avis</p></div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <section className="card space-y-3">
          <h2 className="text-xl">Fiche opérationnelle</h2>
          {field('phone', 'Téléphone')}
          {field('hourly_rate', 'Taux horaire (€)', 'number')}
          <label className="block"><span className="text-brown-800/70 text-sm">Boîte enseignée</span>
            <select value={p.gearbox} onChange={(e) => patch({ gearbox: e.target.value })} className="input-field !py-2 mt-1">{Object.entries(GEARBOX_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
          {field('vehicle', 'Véhicule', 'text', 'Ex : Peugeot 208 double commande')}
          {field('zones', 'Zones de prise en charge', 'text', 'Ex : Lyon 3, Villeurbanne, Bron')}
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={p.is_bookable} onChange={(e) => patch({ is_bookable: e.target.checked })} className="accent-brown-700" /> Réservable par les élèves</label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={i.is_active} onChange={(e) => (e.target.checked || confirm('Désactiver ce compte ? Le moniteur ne pourra plus se connecter.')) && patch({ is_active: e.target.checked })} className="accent-brown-700" /> Compte actif</label>
        </section>

        <section className="card">
          <h2 className="text-xl mb-3">Congés & absences</h2>
          {absences.length === 0 ? <p className="text-sm text-brown-800/60">Aucune absence récente.</p> : (
            <ul className="text-sm divide-y divide-cream-200 mb-4">{absences.map((u) => (
              <li key={u.id} className="py-2">
                <div className="flex items-center justify-between gap-2"><span>{dt(u.start)} → {dt(u.end)}</span><span className={`badge ${absenceCls[u.status]}`}>{u.status_display}</span></div>
                {u.reason && <p className="text-xs text-brown-800/60">{u.reason}</p>}
                {u.status === 'PENDING' ? (
                  <div className="flex gap-2 mt-1 text-xs">
                    <button onClick={() => act(() => api.post(`/admin/absences/${u.id}/approve/`), 'Absence validée, moniteur prévenu.')} className="btn-primary !py-0.5 !px-2 text-xs">Valider</button>
                    <button onClick={() => { const n = prompt('Motif du refus (envoyé au moniteur) :'); if (n !== null) act(() => api.post(`/admin/absences/${u.id}/reject/`, { note: n }), 'Absence refusée, créneau rouvert.'); }} className="text-red-700 hover:underline">Refuser</button>
                  </div>
                ) : u.reviewed_by_name && <p className="text-xs text-brown-800/50">par {u.reviewed_by_name}{u.review_note && ` — ${u.review_note}`}</p>}
              </li>
            ))}</ul>
          )}
          <form onSubmit={(e) => { e.preventDefault(); act(() => api.post(`/admin/instructors/${id}/add_absence/`, absence), 'Absence enregistrée.').then(() => setAbsence({ start: '', end: '', reason: '' })); }} className="border-t border-cream-200 pt-3 space-y-2 text-sm">
            <p className="text-brown-800/70">Saisir une absence (arrêt, formation) :</p>
            <div className="grid grid-cols-2 gap-2">
              <input type="datetime-local" required value={absence.start} onChange={(e) => setAbsence({ ...absence, start: e.target.value })} className="input-field !py-1.5 text-xs" />
              <input type="datetime-local" required value={absence.end} onChange={(e) => setAbsence({ ...absence, end: e.target.value })} className="input-field !py-1.5 text-xs" />
            </div>
            <div className="flex gap-2"><input placeholder="Motif" value={absence.reason} onChange={(e) => setAbsence({ ...absence, reason: e.target.value })} className="input-field !py-1.5 text-xs" /><button className="btn-secondary !py-1.5 text-xs whitespace-nowrap">Ajouter</button></div>
          </form>
        </section>

        <section className="card">
          <h2 className="text-xl mb-1">Réattribution de planning</h2>
          <p className="text-sm text-brown-800/70 mb-3">Absence imprévue : bascule en masse les leçons réservées vers un autre moniteur (refus individuel en cas de conflit).</p>
          <form onSubmit={reassign} className="space-y-2 text-sm">
            <div className="grid grid-cols-2 gap-2">
              <label className="block"><span className="text-xs text-brown-800/70">Du</span><input type="date" required value={re.start} onChange={(e) => setRe({ ...re, start: e.target.value })} className="input-field !py-1.5" /></label>
              <label className="block"><span className="text-xs text-brown-800/70">Au</span><input type="date" required value={re.end} onChange={(e) => setRe({ ...re, end: e.target.value })} className="input-field !py-1.5" /></label>
            </div>
            <select required value={re.target} onChange={(e) => setRe({ ...re, target: e.target.value })} className="input-field !py-1.5"><option value="">Vers le moniteur…</option>{others.map((o) => <option key={o.id} value={o.id}>{o.full_name}{o.profile.zones ? ` · ${o.profile.zones}` : ''}</option>)}</select>
            <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={re.notify} onChange={(e) => setRe({ ...re, notify: e.target.checked })} className="accent-brown-700" /> Prévenir les élèves par email</label>
            <button className="btn-primary !py-2 text-sm w-full">Réattribuer les leçons</button>
          </form>
          {reResult && (
            <div className="mt-3 text-xs space-y-1">
              {reResult.moved.map((m) => <p key={m.id} className="text-brown-700">✓ {m.label}</p>)}
              {reResult.failed.map((f) => <p key={f.id} className="text-red-700">✗ {f.label} — {f.reason}</p>)}
            </div>
          )}
        </section>

        <section className="card lg:col-span-2">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <h2 className="text-xl">Heures du mois</h2>
            <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} className="input-field !py-1.5 text-sm w-44" />
          </div>
          {!hours ? <p className="text-brown-500 text-sm">Chargement…</p> : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm mb-3">
                {(Object.keys(HOUR_LABELS) as (keyof HoursBreakdown['summary'])[]).map((k) => (
                  <div key={k} className={`rounded-xl px-3 py-2 ${k === 'done' ? 'bg-brown-700 text-cream-50' : k === 'no_show' || k === 'cancelled_late' ? 'bg-caramel/30' : 'bg-cream-100'}`}>
                    <p className="text-xs opacity-80">{HOUR_LABELS[k]}</p>
                    <p className="text-xl font-display">{hours.summary[k].hours} h <span className="text-xs font-sans opacity-70">({hours.summary[k].count})</span></p>
                  </div>
                ))}
              </div>
              <p className="text-sm">Rémunération estimée : <strong>{hours.paid_hours} h × {hours.hourly_rate} € = {hours.amount.toLocaleString('fr-FR')} €</strong> <span className="text-brown-800/60">(heures effectuées avec bilan saisi ; absences et annulations hors délai sont facturées à l'élève mais non payées au moniteur)</span></p>
              <button onClick={() => setShowDetails((v) => !v)} className="text-sm text-brown-700 hover:underline mt-2">{showDetails ? 'Masquer le détail' : `Voir le détail (${hours.details.length} créneaux)`}</button>
              {showDetails && (
                <ul className="mt-2 text-xs divide-y divide-cream-200 max-h-64 overflow-auto">{hours.details.map((s) => <li key={s.id} className="py-1 flex justify-between gap-2"><span>{frDate(s.date, { day: '2-digit', month: '2-digit' })} {hm(s.start_time)}–{hm(s.end_time)} · {s.student_name ?? 'libre'} · {s.meeting_point_name}</span><span className="text-brown-800/60">{s.status_display}{s.has_lesson ? ' · bilan' : ''}</span></li>)}</ul>
              )}
            </>
          )}
        </section>

        <section className="card">
          <h2 className="text-xl mb-3">Disponibilités</h2>
          {d.availabilities.length === 0 ? <p className="text-sm text-red-700">Aucune disponibilité saisie : ce moniteur n'apparaît pas à la réservation.</p> : (
            <ul className="text-sm divide-y divide-cream-200">{WEEKDAYS.map((w, idx) => { const items = d.availabilities.filter((a) => a.weekday === idx); return items.length ? <li key={w} className="py-1.5 flex gap-3"><span className="w-20 font-medium">{w}</span><span>{items.map((a) => `${hm(a.start_time)}–${hm(a.end_time)}`).join(', ')}</span></li> : null; })}</ul>
          )}
          <h2 className="text-xl mt-6 mb-3">Prochaines leçons</h2>
          {d.upcoming_slots.length === 0 ? <p className="text-sm text-brown-800/60">Aucune.</p> : (
            <ul className="text-sm divide-y divide-cream-200">{d.upcoming_slots.slice(0, 10).map((s) => <li key={s.id} className="py-1.5">{frDate(s.date, { weekday: 'short', day: 'numeric', month: 'short' })} {hm(s.start_time)} · {s.student_name} · {s.meeting_point_name}</li>)}</ul>
          )}
        </section>

        <section className="card">
          <h2 className="text-xl mb-3">Élèves ({d.students.length})</h2>
          {d.students.length === 0 ? <p className="text-sm text-brown-800/60">Aucun élève encore.</p> : (
            <ul className="text-sm divide-y divide-cream-200">{d.students.map((s) => <li key={s.id} className="py-1.5 flex justify-between"><Link href={`/admin/students/${s.id}`} className="text-brown-700 hover:underline">{s.user.first_name} {s.user.last_name}</Link><span className="text-brown-800/60">{s.remaining_hours.toFixed(1)} h · {s.competency_progress.percent} %</span></li>)}</ul>
          )}
        </section>

        <section className="card lg:col-span-2">
          <h2 className="text-xl mb-3">Derniers avis</h2>
          {d.ratings.length === 0 ? <p className="text-sm text-brown-800/60">Aucun avis.</p> : (
            <ul className="divide-y divide-cream-200 text-sm">{d.ratings.map((r) => (
              <li key={r.id} className={`py-2 ${r.is_hidden ? 'opacity-50' : ''}`}><span className="text-caramel">{'★'.repeat(r.score)}</span> <span className="text-brown-800/60">{r.student_name} · {frDate(r.lesson_date, { day: 'numeric', month: 'short' })}</span>{r.comment && <> — « {r.comment} »</>}{r.is_hidden && <span className="badge bg-cream-200 text-brown-800 ml-2">masqué</span>}{r.reply && <p className="text-brown-800/70 ml-4 mt-1">↳ {r.reply}</p>}</li>
            ))}</ul>
          )}
          <Link href={`/admin/reviews?instructor=${i.id}`} className="text-sm text-brown-700 hover:underline mt-3 inline-block">Modérer les avis →</Link>
        </section>
      </div>
    </AdminShell>
  );
}
