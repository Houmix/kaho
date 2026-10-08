import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { BACKOFFICE, useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import { Application, GEARBOX_LABELS, InstructorAdmin, Paginated, exportCsv } from '@/lib/admin';
import { Unavailability, apiError, frDate } from '@/lib/types';

function NewInstructorForm({ onDone }: { onDone: () => void }) {
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', phone: '', hourly_rate: '', gearbox: 'BOTH', vehicle: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const f = (k: keyof typeof form) => ({ value: form[k], onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setForm({ ...form, [k]: e.target.value }) });
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setError('');
    try { await api.post('/admin/instructors/', { ...form, hourly_rate: form.hourly_rate || 0 }); onDone(); }
    catch (err) { setError(apiError(err, 'Création impossible.')); }
    finally { setBusy(false); }
  };
  return (
    <form onSubmit={submit} className="card mb-6">
      <h2 className="text-xl mb-1">Ajouter un moniteur</h2>
      <p className="text-sm text-brown-800/60 mb-4">Un email d'invitation lui sera envoyé pour créer son mot de passe (lien valable 72 h).</p>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <label className="block"><span className="text-xs text-brown-800/70">Prénom</span><input required className="input-field" {...f('first_name')} /></label>
        <label className="block"><span className="text-xs text-brown-800/70">Nom</span><input required className="input-field" {...f('last_name')} /></label>
        <label className="block"><span className="text-xs text-brown-800/70">Email</span><input required type="email" className="input-field" {...f('email')} /></label>
        <label className="block"><span className="text-xs text-brown-800/70">Téléphone</span><input className="input-field" {...f('phone')} /></label>
        <label className="block"><span className="text-xs text-brown-800/70">Taux horaire (€)</span><input type="number" step="0.5" min="0" className="input-field" {...f('hourly_rate')} /></label>
        <label className="block"><span className="text-xs text-brown-800/70">Boîte</span><select className="input-field" {...f('gearbox')}>{Object.entries(GEARBOX_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        <label className="block sm:col-span-2"><span className="text-xs text-brown-800/70">Véhicule</span><input placeholder="Ex : Peugeot 208 double commande" className="input-field" {...f('vehicle')} /></label>
      </div>
      {error && <p className="text-sm text-red-700 mt-3">{error}</p>}
      <div className="flex gap-2 mt-4"><button disabled={busy} className="btn-primary">{busy ? 'Envoi…' : 'Créer et inviter'}</button><button type="button" onClick={onDone} className="btn-secondary">Annuler</button></div>
    </form>
  );
}

function ApplicationCard({ app, onChange }: { app: Application; onChange: (text: string, ok?: boolean) => void }) {
  const [rate, setRate] = useState('');
  const [note, setNote] = useState('');
  const approve = async () => {
    if (!confirm(`Créer le compte moniteur de ${app.first_name} ${app.last_name} et envoyer l'invitation ?`)) return;
    try { await api.post(`/admin/applications/${app.id}/approve/`, { hourly_rate: rate || 0, note }); onChange(`Compte créé, invitation envoyée à ${app.email}.`); }
    catch (err) { onChange(apiError(err, 'Validation impossible.'), false); }
  };
  const reject = async () => {
    const n = prompt('Motif du refus (envoyé au candidat si renseigné) :', note);
    if (n === null) return;
    try { await api.post(`/admin/applications/${app.id}/reject/`, { note: n, notify_note: n ? 1 : 0 }); onChange('Candidature refusée.'); }
    catch (err) { onChange(apiError(err, 'Refus impossible.'), false); }
  };
  const Doc = ({ href, label }: { href: string | null; label: string }) => href ? <a href={href} target="_blank" rel="noreferrer" className="badge bg-cream-200 text-brown-800 hover:bg-cream-300">{label} ↗</a> : <span className="badge bg-cream-100 text-brown-800/40">{label} —</span>;
  return (
    <article className={`card ${app.status === 'PENDING' ? 'border-caramel' : ''}`}>
      <div className="flex flex-wrap justify-between gap-2">
        <div>
          <h3 className="font-semibold text-lg">{app.first_name} {app.last_name}</h3>
          <p className="text-sm text-brown-800/70">{app.email}{app.phone && ` · ${app.phone}`} · {app.gearbox_display} · reçue le {frDate(app.created_at, { day: 'numeric', month: 'short' })}</p>
        </div>
        <span className={`badge self-start ${app.status === 'PENDING' ? 'bg-caramel text-brown-900' : app.status === 'APPROVED' ? 'bg-brown-700 text-cream-50' : 'bg-red-100 text-red-700'}`}>{app.status_display}</span>
      </div>
      {app.message && <p className="mt-3 text-sm whitespace-pre-line">{app.message}</p>}
      <div className="flex flex-wrap gap-2 mt-3"><Doc href={app.diploma} label="Diplôme / autorisation" /><Doc href={app.driving_license} label="Permis" /><Doc href={app.business_doc} label="Kbis / statut" /></div>
      {app.status === 'PENDING' ? (
        <div className="mt-4 flex flex-wrap items-end gap-2">
          <label className="block"><span className="text-xs text-brown-800/70">Taux horaire (€)</span><input type="number" step="0.5" value={rate} onChange={(e) => setRate(e.target.value)} className="input-field w-28 !py-2" /></label>
          <label className="block flex-1 min-w-48"><span className="text-xs text-brown-800/70">Note interne</span><input value={note} onChange={(e) => setNote(e.target.value)} className="input-field !py-2" /></label>
          <button onClick={approve} className="btn-primary !py-2">✓ Valider et créer le compte</button>
          <button onClick={reject} className="btn-outline !py-2 text-red-700 border-red-300">Refuser</button>
        </div>
      ) : (
        <p className="mt-3 text-xs text-brown-800/60">{app.status_display} par {app.reviewed_by_name} le {app.reviewed_at && frDate(app.reviewed_at, { day: 'numeric', month: 'short' })}{app.admin_note && ` — ${app.admin_note}`}{app.created_user && <> · <Link href={`/admin/instructors/${app.created_user}`} className="text-brown-700 hover:underline">voir la fiche</Link></>}</p>
      )}
    </article>
  );
}

export default function AdminInstructors() {
  const ready = useRequireAuth(BACKOFFICE);
  const router = useRouter();
  const [tab, setTab] = useState<'list' | 'applications' | 'absences'>('list');
  const [absences, setAbsences] = useState<Paginated<Unavailability> | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [q, setQ] = useState('');
  const [list, setList] = useState<Paginated<InstructorAdmin> | null>(null);
  const [apps, setApps] = useState<Paginated<Application> | null>(null);
  const [appStatus, setAppStatus] = useState('PENDING');
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    if (!router.isReady) return;
    if (router.query.tab === 'applications') setTab('applications');
    if (router.query.tab === 'absences') setTab('absences');
    if (router.query.new === '1') setShowNew(true);
  }, [router.isReady, router.query]);

  const load = useCallback(() => {
    api.get('/admin/instructors/', { params: { q: q || undefined, page_size: 100 } }).then((r) => setList(r.data));
    api.get('/admin/applications/', { params: { status: appStatus || undefined } }).then((r) => setApps(r.data));
    api.get('/admin/absences/', { params: { status: 'PENDING', page_size: 100 } }).then((r) => setAbsences(r.data));
  }, [q, appStatus]);
  useEffect(() => { if (!ready) return; const t = setTimeout(load, 200); return () => clearTimeout(t); }, [ready, load]);

  const resend = async (i: InstructorAdmin) => {
    try { const r = await api.post(`/admin/instructors/${i.id}/resend_invite/`); setMsg({ ok: true, text: r.data.detail }); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Envoi impossible.') }); }
  };
  const pendingCount = apps && appStatus === 'PENDING' ? apps.count : null;
  const review = async (u: Unavailability, ok: boolean) => {
    const note = ok ? '' : prompt('Motif du refus (envoyé au moniteur) :');
    if (!ok && note === null) return;
    try { await api.post(`/admin/absences/${u.id}/${ok ? 'approve' : 'reject'}/`, { note }); setMsg({ ok: true, text: ok ? 'Absence validée.' : 'Absence refusée, créneau rouvert.' }); load(); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Action impossible.') }); }
  };
  const csv = () => list && exportCsv('moniteurs.csv', ['Nom', 'Prénom', 'Email', 'Téléphone', 'Boîte', 'Véhicule', 'Zones', 'Taux horaire', 'Réservable', 'Actif', 'Leçons', 'Élèves', 'Note', 'Avis'],
    list.results.map((i) => [i.last_name, i.first_name, i.email, i.profile.phone, i.profile.gearbox_display, i.profile.vehicle, i.profile.zones, i.profile.hourly_rate, i.profile.is_bookable ? 'oui' : 'non', i.is_active ? 'oui' : 'non', i.stats.lessons, i.stats.students, i.stats.rating_average ?? '', i.stats.rating_count]));

  return (
    <AdminShell title="Formateurs" wide>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h1 className="text-3xl">Formateurs</h1>
        <div className="flex gap-2"><button onClick={csv} className="btn-secondary" disabled={!list?.results.length}>Exporter CSV</button><button onClick={() => { setTab('list'); setShowNew((v) => !v); }} className="btn-primary">+ Ajouter un moniteur</button></div>
      </div>
      {msg && <div className={`rounded-xl px-4 py-3 mb-4 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}

      <div className="flex gap-1 mb-6">
        <button onClick={() => setTab('list')} className={`badge !px-4 !py-2 ${tab === 'list' ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>Moniteurs {list ? `(${list.count})` : ''}</button>
        <button onClick={() => setTab('applications')} className={`badge !px-4 !py-2 ${tab === 'applications' ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>Candidatures {pendingCount ? `(${pendingCount})` : ''}</button>
        <button onClick={() => setTab('absences')} className={`badge !px-4 !py-2 ${tab === 'absences' ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>Absences à valider {absences?.count ? `(${absences.count})` : ''}</button>
      </div>

      {tab === 'absences' && (
        !absences ? <p className="text-brown-500">Chargement…</p> : absences.results.length === 0 ? <p className="text-brown-800/60">Aucune demande d'absence en attente.</p> : (
          <div className="card p-0 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-cream-100 text-brown-800/70"><tr><th className="text-left py-3 px-4 font-medium">Moniteur</th><th className="text-left py-3 px-4 font-medium">Du</th><th className="text-left py-3 px-4 font-medium">Au</th><th className="text-left py-3 px-4 font-medium">Motif</th><th></th></tr></thead>
              <tbody>{absences.results.map((u) => (
                <tr key={u.id} className="border-t border-cream-200">
                  <td className="py-3 px-4"><Link href={`/admin/instructors/${u.instructor}`} className="text-brown-700 hover:underline">{u.instructor_name}</Link></td>
                  <td className="py-3 px-4">{new Date(u.start).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })}</td>
                  <td className="py-3 px-4">{new Date(u.end).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })}</td>
                  <td className="py-3 px-4 text-brown-800/70">{u.reason || '—'}</td>
                  <td className="py-3 px-4 text-right whitespace-nowrap space-x-3"><button onClick={() => review(u, true)} className="btn-primary !py-1 text-xs">Valider</button><button onClick={() => review(u, false)} className="text-red-700 text-xs hover:underline">Refuser</button></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )
      )}

      {tab === 'list' && (
        <>
          {showNew && <NewInstructorForm onDone={() => { setShowNew(false); load(); setMsg({ ok: true, text: 'Moniteur créé, invitation envoyée.' }); }} />}
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nom, email…" className="input-field sm:w-72 !py-2 mb-4" />
          <div className="card p-0 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-cream-100 text-brown-800/70"><tr>
                <th className="text-left py-3 px-4 font-medium">Moniteur</th><th className="text-left py-3 px-4 font-medium">Contact</th><th className="text-left py-3 px-4 font-medium">Boîte · zones</th><th className="text-right py-3 px-4 font-medium">Taux</th><th className="text-right py-3 px-4 font-medium">Dispos</th><th className="text-right py-3 px-4 font-medium">À venir</th><th className="text-left py-3 px-4 font-medium">Note</th><th className="text-left py-3 px-4 font-medium">Statut</th><th></th>
              </tr></thead>
              <tbody>
                {!list ? <tr><td colSpan={9} className="py-10 text-center text-brown-500">Chargement…</td></tr> : list.results.length === 0 ? <tr><td colSpan={9} className="py-10 text-center text-brown-800/60">Aucun moniteur</td></tr> : list.results.map((i) => (
                  <tr key={i.id} className="border-t border-cream-200 hover:bg-cream-50">
                    <td className="py-3 px-4"><Link href={`/admin/instructors/${i.id}`} className="font-medium text-brown-700 hover:underline">{i.last_name} {i.first_name}</Link></td>
                    <td className="py-3 px-4 text-brown-800/70">{i.email}{i.profile.phone && <><br />{i.profile.phone}</>}</td>
                    <td className="py-3 px-4">{i.profile.gearbox_display}{i.profile.zones && <><br /><span className="text-xs text-brown-800/60">{i.profile.zones}</span></>}</td>
                    <td className="py-3 px-4 text-right">{Number(i.profile.hourly_rate)} €/h</td>
                    <td className={`py-3 px-4 text-right ${i.stats.availability_slots === 0 ? 'text-red-700 font-semibold' : ''}`}>{i.stats.availability_slots}</td>
                    <td className="py-3 px-4 text-right">{i.stats.upcoming}</td>
                    <td className="py-3 px-4">{i.stats.rating_average !== null ? `${i.stats.rating_average.toFixed(1)} ★ (${i.stats.rating_count})` : <span className="text-brown-800/40">—</span>}</td>
                    <td className="py-3 px-4">
                      {!i.is_active ? <span className="badge bg-red-100 text-red-700">désactivé</span> : !i.has_password ? <span className="badge bg-caramel text-brown-900">invitation en attente</span> : i.profile.is_bookable ? <span className="badge bg-brown-700 text-cream-50">réservable</span> : <span className="badge bg-cream-200 text-brown-800">non réservable</span>}
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">{!i.has_password && i.is_active && <button onClick={() => resend(i)} className="text-brown-700 text-xs hover:underline">Renvoyer l'invitation</button>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'applications' && (
        <>
          <div className="flex gap-1 mb-4">
            {[['PENDING', 'À examiner'], ['APPROVED', 'Acceptées'], ['REJECTED', 'Refusées'], ['', 'Toutes']].map(([k, l]) => (
              <button key={k} onClick={() => setAppStatus(k)} className={`badge !px-3 !py-1.5 ${appStatus === k ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>{l}</button>
            ))}
            <Link href="/devenir-moniteur" target="_blank" className="ml-auto text-sm text-brown-700 hover:underline self-center">Page publique de candidature ↗</Link>
          </div>
          {!apps ? <p className="text-brown-500">Chargement…</p> : apps.results.length === 0 ? <p className="text-brown-800/60">Aucune candidature.</p> : (
            <div className="space-y-4">{apps.results.map((a) => <ApplicationCard key={a.id} app={a} onChange={(text, ok = true) => { setMsg({ ok, text }); load(); }} />)}</div>
          )}
        </>
      )}
    </AdminShell>
  );
}
