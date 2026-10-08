import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { BACKOFFICE, useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import StudentActions from '@/components/StudentActions';
import { InstructorAdmin, Paginated, downloadFile } from '@/lib/admin';
import { STUDENT_STATUSES, StudentProfile, apiError, statusOf } from '@/lib/types';

type Row = StudentProfile & { phone: string; referent_instructor?: number | null };
const FILTERS = [
  { key: '', label: 'Tous' },
  { key: 'unpaid', label: 'Paiement en attente' },
  { key: 'low', label: '≤ 1 h de crédit' },
  { key: 'ready', label: 'Prêts pour l’examen' },
  { key: 'lms', label: 'Accès code en ligne' },
  { key: 'documents', label: 'Pièces à vérifier' },
  { key: 'incomplete', label: 'Dossier incomplet' },
];

function NewStudentForm({ onDone }: { onDone: () => void }) {
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', phone: '', password: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setError('');
    try { await api.post('/auth/register/', form); onDone(); }
    catch (err) { setError(apiError(err, 'Création impossible.')); }
    finally { setBusy(false); }
  };
  const f = (k: keyof typeof form) => ({ value: form[k], onChange: (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value }) });
  return (
    <form onSubmit={submit} className="card mb-6 grid sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
      <label className="block"><span className="text-xs text-brown-800/70">Prénom</span><input required className="input-field" {...f('first_name')} /></label>
      <label className="block"><span className="text-xs text-brown-800/70">Nom</span><input required className="input-field" {...f('last_name')} /></label>
      <label className="block"><span className="text-xs text-brown-800/70">Email</span><input required type="email" className="input-field" {...f('email')} /></label>
      <label className="block"><span className="text-xs text-brown-800/70">Mobile</span><input className="input-field" {...f('phone')} /></label>
      <label className="block"><span className="text-xs text-brown-800/70">Mot de passe initial</span><input required minLength={8} className="input-field" {...f('password')} /></label>
      {error && <p className="sm:col-span-2 lg:col-span-5 text-sm text-red-700">{error}</p>}
      <div className="sm:col-span-2 lg:col-span-5 flex gap-2"><button disabled={busy} className="btn-primary">Créer l'élève</button><button type="button" onClick={onDone} className="btn-secondary">Annuler</button></div>
    </form>
  );
}

/** Barre d'actions groupées sur la sélection : message, statut, relances. */
function BulkBar({ ids, onDone, onClear }: { ids: number[]; onDone: (text: string, ok?: boolean) => void; onClear: () => void }) {
  const [mode, setMode] = useState<'' | 'message' | 'status'>('');
  const [m, setM] = useState({ subject: '', body: '', channel: 'email', status: 'REGISTERED' });
  const [busy, setBusy] = useState(false);
  const run = async (payload: object, confirmText?: string) => {
    if (confirmText && !confirm(confirmText)) return;
    setBusy(true);
    try { const r = await api.post('/admin/students/bulk/', { ids, ...payload }); onDone(r.data.detail); setMode(''); setM({ ...m, subject: '', body: '' }); }
    catch (err) { onDone(apiError(err, 'Action impossible.'), false); }
    finally { setBusy(false); }
  };
  return (
    <div className="card border-brown-300 bg-brown-50 mb-4">
      <div className="flex flex-wrap items-center gap-2">
        <strong className="mr-2">{ids.length} sélectionné{ids.length > 1 ? 's' : ''}</strong>
        <button onClick={() => setMode(mode === 'message' ? '' : 'message')} className={`badge !px-3 !py-1.5 ${mode === 'message' ? 'bg-brown-700 text-cream-50' : 'bg-white text-brown-800'}`}>✉ Email / SMS</button>
        <button onClick={() => setMode(mode === 'status' ? '' : 'status')} className={`badge !px-3 !py-1.5 ${mode === 'status' ? 'bg-brown-700 text-cream-50' : 'bg-white text-brown-800'}`}>◉ Changer le statut</button>
        <button disabled={busy} onClick={() => run({ action: 'remind_documents' }, 'Relancer par email les élèves sélectionnés dont le dossier est incomplet ?')} className="badge !px-3 !py-1.5 bg-white text-brown-800">Relance dossier</button>
        <button disabled={busy} onClick={() => run({ action: 'remind_payment' }, 'Relancer par email les élèves sélectionnés ayant un paiement en attente ?')} className="badge !px-3 !py-1.5 bg-white text-brown-800">Relance paiement</button>
        <button onClick={onClear} className="ml-auto text-sm text-brown-700 hover:underline">Tout désélectionner</button>
      </div>
      {mode === 'message' && (
        <form onSubmit={(e) => { e.preventDefault(); run({ action: 'message', ...m }); }} className="mt-3 space-y-2">
          <div className="flex gap-2 items-center text-sm">
            <span className="text-brown-800/70">Canal</span>
            {[['email', 'Email'], ['sms', 'SMS'], ['both', 'Les deux']].map(([k, l]) => <label key={k} className="flex items-center gap-1"><input type="radio" checked={m.channel === k} onChange={() => setM({ ...m, channel: k })} className="accent-brown-700" />{l}</label>)}
            <span className="text-xs text-brown-800/50 ml-2">Variables : {'{prenom}'} {'{nom}'}</span>
          </div>
          {m.channel !== 'sms' && <input required placeholder="Objet" value={m.subject} onChange={(e) => setM({ ...m, subject: e.target.value })} className="input-field !py-2" />}
          <textarea required rows={3} placeholder="Message" value={m.body} onChange={(e) => setM({ ...m, body: e.target.value })} className="input-field" />
          <button disabled={busy} className="btn-primary !py-2 text-sm">{busy ? 'Envoi…' : `Envoyer à ${ids.length} élève${ids.length > 1 ? 's' : ''}`}</button>
        </form>
      )}
      {mode === 'status' && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <select value={m.status} onChange={(e) => setM({ ...m, status: e.target.value })} className="input-field !py-2 w-64">{STUDENT_STATUSES.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}</select>
          <button disabled={busy} onClick={() => run({ action: 'status', status: m.status }, `Passer ${ids.length} élève(s) au statut « ${statusOf(m.status).label} » ?`)} className="btn-primary !py-2 text-sm">Appliquer</button>
        </div>
      )}
    </div>
  );
}

export default function AdminStudents() {
  const ready = useRequireAuth(BACKOFFICE);
  const router = useRouter();
  const [q, setQ] = useState('');
  const [filter, setFilter] = useState('');
  const [status, setStatus] = useState('');
  const [referent, setReferent] = useState('');
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Paginated<Row> | null>(null);
  const [instructors, setInstructors] = useState<InstructorAdmin[]>([]);
  const [showNew, setShowNew] = useState(false);
  const [selected, setSelected] = useState<number[]>([]);
  const [quick, setQuick] = useState<Row | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    if (!router.isReady) return;
    if (typeof router.query.filter === 'string') setFilter(router.query.filter);
    if (typeof router.query.status === 'string') setStatus(router.query.status);
    if (router.query.new === '1') setShowNew(true);
  }, [router.isReady, router.query]);

  const params = useCallback(() => ({ q: q || undefined, filter: filter || undefined, status: status || undefined, referent: referent || undefined }), [q, filter, status, referent]);
  const load = useCallback(() => {
    api.get('/admin/students/', { params: { ...params(), page } }).then((r) => setData(r.data));
  }, [params, page]);

  useEffect(() => { if (ready) { api.get('/admin/instructors/', { params: { page_size: 200 } }).then((r) => setInstructors(r.data.results)); } }, [ready]);
  useEffect(() => { if (!ready) return; const t = setTimeout(load, 200); return () => clearTimeout(t); }, [ready, load]);

  const csv = () => downloadFile('/admin/students/export/', `eleves-${new Date().toISOString().slice(0, 10)}.csv`, params());
  const pages = data ? Math.max(1, Math.ceil(data.count / 25)) : 1;
  const allChecked = !!data && data.results.length > 0 && data.results.every((s) => selected.includes(s.id));
  const toggleAll = () => setSelected(allChecked ? selected.filter((id) => !data!.results.some((s) => s.id === id)) : Array.from(new Set([...selected, ...data!.results.map((s) => s.id)])));
  const toggle = (id: number) => setSelected(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);

  return (
    <AdminShell title="Apprenants" wide>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h1 className="text-3xl">Apprenants <span className="text-lg text-brown-800/50 font-sans">{data ? data.count : ''}</span></h1>
        <div className="flex gap-2">
          <button onClick={csv} className="btn-secondary" disabled={!data?.results.length}>Exporter CSV</button>
          <button onClick={() => setShowNew((v) => !v)} className="btn-primary">+ Créer un élève</button>
        </div>
      </div>
      {msg && <div className={`rounded-xl px-4 py-3 mb-4 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}
      {showNew && <NewStudentForm onDone={() => { setShowNew(false); load(); }} />}

      <div className="flex flex-wrap gap-2 mb-3 items-center">
        <input value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} placeholder="Nom, email, téléphone…" className="input-field sm:w-64 !py-2" />
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="input-field sm:w-60 !py-2">
          <option value="">Tous les statuts (hors archivés)</option>
          {STUDENT_STATUSES.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
        </select>
        <select value={referent} onChange={(e) => { setReferent(e.target.value); setPage(1); }} className="input-field sm:w-52 !py-2">
          <option value="">Tous les référents</option>
          {instructors.map((i) => <option key={i.id} value={i.id}>{i.full_name}</option>)}
        </select>
      </div>
      <div className="flex gap-1 flex-wrap mb-4">
        {FILTERS.map((f) => <button key={f.key} onClick={() => { setFilter(f.key); setPage(1); }} className={`badge !px-3 !py-1.5 ${filter === f.key ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>{f.label}</button>)}
      </div>

      {selected.length > 0 && <BulkBar ids={selected} onDone={(text, ok = true) => { setMsg({ ok, text }); if (ok) { setSelected([]); load(); } }} onClear={() => setSelected([])} />}

      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-cream-100 text-brown-800/70">
            <tr>
              <th className="py-3 px-3 w-8"><input type="checkbox" checked={allChecked} onChange={toggleAll} className="accent-brown-700" aria-label="Tout sélectionner" /></th>
              <th className="text-left py-3 px-3 font-medium">Élève</th>
              <th className="text-left py-3 px-3 font-medium">Statut</th>
              <th className="text-left py-3 px-3 font-medium">Contact</th>
              <th className="text-right py-3 px-3 font-medium">Restantes</th>
              <th className="text-right py-3 px-3 font-medium">Compét.</th>
              <th className="text-left py-3 px-3 font-medium">Code</th>
              <th className="text-left py-3 px-3 font-medium">Dossier</th>
              <th className="text-left py-3 px-3 font-medium">Référent</th>
              <th className="py-3 px-3"></th>
            </tr>
          </thead>
          <tbody>
            {!data ? <tr><td colSpan={10} className="py-10 text-center text-brown-500">Chargement…</td></tr>
              : data.results.length === 0 ? <tr><td colSpan={10} className="py-10 text-center text-brown-800/60">Aucun élève</td></tr>
              : data.results.map((s) => (
                <tr key={s.id} className={`border-t border-cream-200 hover:bg-cream-50 ${selected.includes(s.id) ? 'bg-brown-50' : ''}`}>
                  <td className="py-3 px-3"><input type="checkbox" checked={selected.includes(s.id)} onChange={() => toggle(s.id)} className="accent-brown-700" aria-label={`Sélectionner ${s.user.first_name}`} /></td>
                  <td className="py-3 px-3"><Link href={`/admin/students/${s.id}`} className="font-medium text-brown-700 hover:underline">{s.user.last_name} {s.user.first_name}</Link>{s.ready_for_exam && <span className="badge bg-caramel text-brown-900 ml-2">prêt</span>}</td>
                  <td className="py-3 px-3"><span className={`badge ${statusOf(s.status).cls}`}>{s.status_display}</span></td>
                  <td className="py-3 px-3 text-brown-800/70 text-xs">{s.user.email}{s.phone && <><br />{s.phone}</>}</td>
                  <td className={`py-3 px-3 text-right ${s.remaining_hours <= 1 ? 'text-red-700 font-semibold' : ''}`}>{s.remaining_hours.toFixed(1)} h</td>
                  <td className="py-3 px-3 text-right">{s.competency_progress.percent} %</td>
                  <td className="py-3 px-3">{s.has_lms_access ? <span className="badge bg-brown-700 text-cream-50">actif</span> : <span className="text-brown-800/40">—</span>}</td>
                  <td className="py-3 px-3">{s.dossier.complete ? <span className="badge bg-brown-700 text-cream-50">complet</span> : s.dossier.pending ? <span className="badge bg-caramel text-brown-900">{s.dossier.pending} à vérifier</span> : <span className="badge bg-cream-200 text-brown-800">{s.dossier.missing} manquante{s.dossier.missing > 1 ? 's' : ''}</span>}</td>
                  <td className="py-3 px-3">{s.referent_instructor_name || <span className="text-brown-800/40">—</span>}</td>
                  <td className="py-3 px-3 text-right"><button onClick={() => setQuick(s)} className="btn-secondary !py-1 !px-2.5 text-xs whitespace-nowrap">Actions ▸</button></td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      {pages > 1 && (
        <div className="flex items-center justify-end gap-2 mt-3 text-sm">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="btn-secondary !py-1.5 disabled:opacity-40">←</button>
          <span>Page {page} / {pages}</span>
          <button disabled={page >= pages} onClick={() => setPage(page + 1)} className="btn-secondary !py-1.5 disabled:opacity-40">→</button>
        </div>
      )}

      {quick && (
        <div className="fixed inset-0 z-30 bg-brown-900/40" onClick={() => setQuick(null)}>
          <aside className="absolute right-0 top-0 h-full w-full max-w-xl bg-cream-50 shadow-2xl p-5 overflow-auto" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Actions rapides">
            <div className="flex items-start justify-between gap-3 mb-4">
              <div>
                <p className="text-xs uppercase tracking-wide text-caramel font-medium">Action rapide</p>
                <h2 className="text-2xl">{quick.user.first_name} {quick.user.last_name}</h2>
                <p className="text-sm text-brown-800/70">{quick.remaining_hours.toFixed(1)} h restantes · <span className={`badge ${statusOf(quick.status).cls}`}>{quick.status_display}</span> · <Link href={`/admin/students/${quick.id}`} className="text-brown-700 hover:underline">fiche complète →</Link></p>
              </div>
              <button onClick={() => setQuick(null)} aria-label="Fermer" className="btn-secondary !px-3 !py-1.5">✕</button>
            </div>
            <StudentActions compact student={quick} onDone={(text) => { setMsg({ ok: true, text }); load(); api.get(`/admin/students/${quick.id}/`).then((r) => setQuick(r.data)); }} />
          </aside>
        </div>
      )}
    </AdminShell>
  );
}
