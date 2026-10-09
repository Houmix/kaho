import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { STAFF_ROLES, useRequireAuth } from '@/hooks/useRequireAuth';
import AppShell from '@/components/AppShell';
import ProgressGauge from '@/components/ProgressGauge';
import BackLink from '@/components/BackLink';
import { Logbook, STATUS_LABELS, Slot, apiError, frDate, hm } from '@/lib/types';

export default function InstructorStudentSheet() {
  const ready = useRequireAuth(STAFF_ROLES);
  const router = useRouter();
  const id = typeof router.query.id === 'string' ? router.query.id : null;
  const [lb, setLb] = useState<Logbook | null>(null);
  const [upcoming, setUpcoming] = useState<Slot[]>([]);
  const [tab, setTab] = useState<'lessons' | 'skills'>('lessons');
  const [msgForm, setMsgForm] = useState<{ open: boolean; subject: string; body: string; channel: 'email' | 'sms' | 'both' }>({ open: false, subject: '', body: '', channel: 'email' });
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [error, setError] = useState('');

  const load = useCallback(() => id && Promise.all([
    api.get(`/student-profiles/${id}/logbook/`).then((r) => setLb(r.data)),
    api.get('/slots/', { params: { page_size: 200 } }).then((r) => { const today = new Date().toISOString().slice(0, 10); setUpcoming((r.data.results ?? r.data).filter((s: Slot) => String(s.student) === id && s.status === 'BOOKED' && s.date >= today)); }),
  ]).catch(() => setError("Élève introuvable ou hors de votre suivi.")), [id]);
  useEffect(() => { if (ready && id) load(); }, [ready, id, load]);

  const send = async (e: React.FormEvent) => {
    e.preventDefault(); setMsg(null);
    try { const r = await api.post('/instructors/message/', { student: id, ...msgForm }); setMsg({ ok: true, text: r.data.detail }); setMsgForm({ open: false, subject: '', body: '', channel: 'email' }); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Envoi impossible.') }); }
  };

  if (error) return <AppShell title="Élève"><p className="text-red-700">{error}</p></AppShell>;
  if (!lb) return <AppShell title="Élève"><p className="text-brown-500">Chargement…</p></AppShell>;
  const s = lb.student;
  const groups = Array.from(new Set(lb.competencies.map((c) => c.group))).sort();
  const counts = { ACQUIRED: lb.competencies.filter((c) => c.status === 'ACQUIRED').length, IN_PROGRESS: lb.competencies.filter((c) => c.status === 'IN_PROGRESS').length, NOT_COVERED: lb.competencies.filter((c) => c.status === 'NOT_COVERED').length };

  return (
    <AppShell title={`${s.user.first_name} ${s.user.last_name}`}>
      <BackLink fallbackHref="/instructor/dashboard" fallbackLabel="← Mes élèves" />
      <div className="flex flex-wrap items-start justify-between gap-3 mt-2 mb-4">
        <div>
          <h1 className="text-3xl">{s.user.first_name} {s.user.last_name}</h1>
          <p className="text-brown-800/70">{s.user.email}{s.phone && ` · ${s.phone}`} · boîte {s.license_type === 'AUTO' ? 'automatique' : 'manuelle'}{s.referent_instructor_name && ` · référent : ${s.referent_instructor_name}`}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {s.phone && <a href={`tel:${s.phone}`} className="btn-secondary !py-1.5 text-sm">📞 Appeler</a>}
          {s.phone && <a href={`sms:${s.phone}`} className="btn-secondary !py-1.5 text-sm">💬 SMS</a>}
          <a href={`mailto:${s.user.email}`} className="btn-secondary !py-1.5 text-sm">✉ Email</a>
          <button onClick={() => setMsgForm({ ...msgForm, open: !msgForm.open })} className="btn-primary !py-1.5 text-sm">Contacter l'élève</button>
        </div>
      </div>
      {msg && <div className={`rounded-xl px-4 py-3 mb-4 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}
      {msgForm.open && (
        <form onSubmit={send} className="card border-brown-300 mb-6 space-y-2">
          <h2 className="text-lg">Message à {s.user.first_name}</h2>
          <div className="flex gap-3 text-sm">{([['email', 'Email'], ['sms', 'SMS'], ['both', 'Les deux']] as const).map(([k, l]) => <label key={k} className="flex items-center gap-1"><input type="radio" checked={msgForm.channel === k} onChange={() => setMsgForm({ ...msgForm, channel: k })} className="accent-brown-700" disabled={k !== 'email' && !s.phone} />{l}</label>)}</div>
          {msgForm.channel !== 'sms' && <input required placeholder="Objet" value={msgForm.subject} onChange={(e) => setMsgForm({ ...msgForm, subject: e.target.value })} className="input-field !py-2" />}
          <textarea required rows={3} placeholder="Votre message (RDV, conseils, rappel…)" value={msgForm.body} onChange={(e) => setMsgForm({ ...msgForm, body: e.target.value })} className="input-field" />
          <div className="flex gap-2"><button className="btn-primary !py-2 text-sm">Envoyer</button><button type="button" onClick={() => setMsgForm({ ...msgForm, open: false })} className="btn-secondary !py-2 text-sm">Annuler</button></div>
        </form>
      )}

      <div className="grid sm:grid-cols-4 gap-4 mb-6">
        <div className="card py-4"><p className="text-sm text-brown-800/70">Formule</p><p className="text-lg font-display leading-tight">{s.formula?.name ?? '—'}</p>{s.formula?.expires_at && <p className="text-xs text-brown-800/60">jusqu'au {frDate(s.formula.expires_at, { day: 'numeric', month: 'short', year: 'numeric' })}</p>}</div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Heures effectuées</p><p className="text-3xl font-display">{s.used_hours.toFixed(1)} h</p><p className="text-xs text-brown-800/60">sur {s.purchased_hours.toFixed(1)} h achetées</p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Heures restantes</p><p className={`text-3xl font-display ${s.remaining_hours <= 1 ? 'text-red-700' : ''}`}>{s.remaining_hours.toFixed(1)} h</p><p className="text-xs text-brown-800/60">{s.reserved_hours.toFixed(1)} h réservées</p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Livret</p><ProgressGauge progress={lb.progress} compact /></div>
      </div>

      {upcoming.length > 0 && (
        <section className="card mb-6">
          <h2 className="text-xl mb-2">Prochaines leçons</h2>
          <ul className="divide-y divide-cream-200 text-sm">{upcoming.map((sl) => <li key={sl.id} className="py-1.5 flex flex-wrap justify-between gap-2"><span>{frDate(sl.date, { weekday: 'short', day: 'numeric', month: 'short' })} · {hm(sl.start_time)}–{hm(sl.end_time)} · {sl.meeting_point_name}</span><span className="text-brown-800/70">{sl.instructor_name}</span></li>)}</ul>
        </section>
      )}

      <div className="flex gap-1 mb-4">
        {([['lessons', `Historique des leçons (${lb.lessons.length})`], ['skills', 'Bilan des compétences']] as const).map(([k, l]) => <button key={k} onClick={() => setTab(k)} className={`badge !px-4 !py-2 ${tab === k ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>{l}</button>)}
      </div>

      {tab === 'lessons' && (
        lb.lessons.length === 0 ? <p className="text-brown-800/60">Aucune leçon effectuée.</p> : (
          <div className="space-y-3">
            {lb.lessons.map((l) => (
              <article key={l.id} className="card">
                <div className="flex flex-wrap justify-between gap-2">
                  <strong>{frDate(l.slot.date, { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })} · {hm(l.slot.start_time)}–{hm(l.slot.end_time)}</strong>
                  <span className="text-sm">par <strong>{l.instructor_name}</strong>{!l.attended && <span className="badge bg-red-100 text-red-700 ml-2">absent</span>}{l.rating && <span className="text-caramel ml-2">{'★'.repeat(l.rating.score)}</span>}</span>
                </div>
                {l.instructor_notes && <p className="mt-2 text-sm whitespace-pre-line border-l-2 border-caramel pl-3">{l.instructor_notes}</p>}
                {l.weather_conditions && <p className="mt-1 text-xs text-brown-800/60">Conditions : {l.weather_conditions}</p>}
                {l.assessments.length > 0 && <div className="flex flex-wrap gap-1 mt-2">{l.assessments.map((a) => <span key={a.competency} className={`badge ${a.status === 'ACQUIRED' ? 'bg-brown-700 text-cream-50' : 'bg-caramel/40 text-brown-900'}`} title={a.label}>{a.code} {STATUS_LABELS[a.status]}</span>)}</div>}
                <Link href={`/instructor/lesson/${l.slot.id}`} className="inline-block mt-2 text-xs text-brown-700 hover:underline">Modifier ce bilan</Link>
              </article>
            ))}
          </div>
        )
      )}

      {tab === 'skills' && (
        <div className="space-y-4">
          <p className="text-sm text-brown-800/70"><span className="badge bg-brown-700 text-cream-50 mr-1">{counts.ACQUIRED} acquises</span><span className="badge bg-caramel/40 text-brown-900 mr-1">{counts.IN_PROGRESS} à travailler</span><span className="badge bg-cream-200 text-brown-800">{counts.NOT_COVERED} non abordées</span></p>
          {groups.map((g) => { const items = lb.competencies.filter((c) => c.group === g); return (
            <div key={g} className="card">
              <h3 className="font-semibold mb-2">{g}. {items[0].group_label}</h3>
              <ul className="divide-y divide-cream-200 text-sm">{items.map((c) => <li key={c.id} className="py-1.5 flex items-center justify-between gap-2"><span><span className="text-brown-800/50 mr-2">{c.code}</span>{c.label}</span><span className={`badge ${c.status === 'ACQUIRED' ? 'bg-brown-700 text-cream-50' : c.status === 'IN_PROGRESS' ? 'bg-caramel/40 text-brown-900' : 'bg-cream-200 text-brown-800/60'}`}>{STATUS_LABELS[c.status]}{c.last_assessed && ` · ${frDate(c.last_assessed, { day: 'numeric', month: 'short' })}`}</span></li>)}</ul>
            </div>
          ); })}
        </div>
      )}
    </AppShell>
  );
}
