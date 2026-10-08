import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import { GEARBOX_LABELS, InstructorOverview } from '@/lib/admin';
import { WEEKDAYS, apiError, frDate, hm } from '@/lib/types';

export default function AdminInstructorDetail() {
  const ready = useRequireAuth(['SUPERVISOR', 'ADMIN']);
  const router = useRouter();
  const id = typeof router.query.id === 'string' ? router.query.id : null;
  const [d, setD] = useState<InstructorOverview | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const load = useCallback(() => id && api.get(`/admin/instructors/${id}/overview/`).then((r) => setD(r.data)), [id]);
  useEffect(() => { if (ready && id) load(); }, [ready, id, load]);

  const patch = async (data: object, okText = 'Fiche mise à jour.') => {
    setMsg(null);
    try { await api.patch(`/admin/instructors/${id}/`, data); await load(); setMsg({ ok: true, text: okText }); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Mise à jour impossible.') }); }
  };
  const resend = async () => {
    try { const r = await api.post(`/admin/instructors/${id}/resend_invite/`); setMsg({ ok: true, text: r.data.detail }); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Envoi impossible.') }); }
  };

  if (!d) return <AdminShell title="Moniteur"><p className="text-brown-500">Chargement…</p></AdminShell>;
  const i = d.instructor;
  const p = i.profile;
  const field = (k: string, label: string, type = 'text') => (
    <label className="block"><span className="text-brown-800/70 text-sm">{label}</span>
      <input type={type} step={type === 'number' ? '0.5' : undefined} defaultValue={(p as any)[k] ?? ''} onBlur={(e) => String((p as any)[k] ?? '') !== e.target.value && patch({ [k]: e.target.value })} className="input-field !py-2 mt-1" /></label>
  );

  return (
    <AdminShell title={i.full_name}>
      <Link href="/admin/instructors" className="text-sm text-brown-700 hover:underline">← Formateurs</Link>
      <div className="flex flex-wrap items-start justify-between gap-3 mt-2 mb-6">
        <div><h1 className="text-3xl">{i.full_name}</h1><p className="text-brown-800/70">{i.email}{p.phone && ` · ${p.phone}`}</p></div>
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
          <h2 className="text-xl">Fiche</h2>
          {field('phone', 'Téléphone')}
          {field('hourly_rate', 'Taux horaire (€)', 'number')}
          <label className="block"><span className="text-brown-800/70 text-sm">Boîte enseignée</span>
            <select value={p.gearbox} onChange={(e) => patch({ gearbox: e.target.value })} className="input-field !py-2 mt-1">{Object.entries(GEARBOX_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
          {field('vehicle', 'Véhicule')}
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={p.is_bookable} onChange={(e) => patch({ is_bookable: e.target.checked })} className="accent-brown-700" /> Réservable par les élèves</label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={i.is_active} onChange={(e) => (e.target.checked || confirm('Désactiver ce compte ? Le moniteur ne pourra plus se connecter.')) && patch({ is_active: e.target.checked })} className="accent-brown-700" /> Compte actif</label>
        </section>

        <section className="card">
          <h2 className="text-xl mb-3">Disponibilités</h2>
          {d.availabilities.length === 0 ? <p className="text-sm text-red-700">Aucune disponibilité saisie : ce moniteur n'apparaît pas à la réservation. Il doit les renseigner depuis son espace.</p> : (
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

        <section className="card lg:col-span-3">
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
