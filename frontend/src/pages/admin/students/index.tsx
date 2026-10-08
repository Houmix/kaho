import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import { InstructorAdmin, Paginated, exportCsv } from '@/lib/admin';
import { StudentProfile, apiError } from '@/lib/types';

type Row = StudentProfile & { phone: string };
const FILTERS = [
  { key: '', label: 'Tous' },
  { key: 'unpaid', label: 'Paiement en attente' },
  { key: 'low', label: '≤ 1 h de crédit' },
  { key: 'ready', label: 'Prêts pour l’examen' },
  { key: 'lms', label: 'Accès code en ligne' },
];

function NewStudentForm({ onDone }: { onDone: () => void }) {
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', phone: '', password: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setError('');
    try {
      // Même endpoint que l'inscription publique ; l'admin communique le mot de passe initial à l'élève
      await api.post('/auth/register/', form);
      onDone();
    } catch (err) { setError(apiError(err, 'Création impossible.')); }
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

export default function AdminStudents() {
  const ready = useRequireAuth(['SUPERVISOR', 'ADMIN']);
  const router = useRouter();
  const [q, setQ] = useState('');
  const [filter, setFilter] = useState('');
  const [referent, setReferent] = useState('');
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Paginated<Row> | null>(null);
  const [instructors, setInstructors] = useState<InstructorAdmin[]>([]);
  const [showNew, setShowNew] = useState(false);

  useEffect(() => {
    if (!router.isReady) return;
    if (typeof router.query.filter === 'string') setFilter(router.query.filter);
    if (router.query.new === '1') setShowNew(true);
  }, [router.isReady, router.query]);

  const load = useCallback(() => {
    api.get('/admin/students/', { params: { q: q || undefined, filter: filter || undefined, referent: referent || undefined, page } }).then((r) => setData(r.data));
  }, [q, filter, referent, page]);

  useEffect(() => { if (ready) { api.get('/admin/instructors/', { params: { page_size: 200 } }).then((r) => setInstructors(r.data.results)); } }, [ready]);
  useEffect(() => { if (!ready) return; const t = setTimeout(load, 200); return () => clearTimeout(t); }, [ready, load]);

  const csv = () => data && exportCsv('eleves.csv',
    ['Nom', 'Prénom', 'Email', 'Mobile', 'Heures achetées', 'Heures faites', 'Restantes', 'Réservées', 'Compétences %', 'Code en ligne', 'Référent', 'Prêt examen'],
    data.results.map((s) => [s.user.last_name, s.user.first_name, s.user.email, s.phone, s.purchased_hours, s.used_hours, s.remaining_hours, s.reserved_hours, s.competency_progress.percent, s.has_lms_access ? 'oui' : 'non', s.referent_instructor_name, s.ready_for_exam ? 'oui' : 'non']));

  const pages = data ? Math.max(1, Math.ceil(data.count / 25)) : 1;

  return (
    <AdminShell title="Apprenants" wide>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h1 className="text-3xl">Apprenants <span className="text-lg text-brown-800/50 font-sans">{data ? data.count : ''}</span></h1>
        <div className="flex gap-2">
          <button onClick={csv} className="btn-secondary" disabled={!data?.results.length}>Exporter CSV</button>
          <button onClick={() => setShowNew((v) => !v)} className="btn-primary">+ Créer un élève</button>
        </div>
      </div>

      {showNew && <NewStudentForm onDone={() => { setShowNew(false); load(); }} />}

      <div className="flex flex-wrap gap-2 mb-4 items-center">
        <input value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} placeholder="Nom, email, téléphone…" className="input-field sm:w-72 !py-2" />
        <select value={referent} onChange={(e) => { setReferent(e.target.value); setPage(1); }} className="input-field sm:w-56 !py-2">
          <option value="">Tous les référents</option>
          {instructors.map((i) => <option key={i.id} value={i.id}>{i.full_name}</option>)}
        </select>
        <div className="flex gap-1 flex-wrap">
          {FILTERS.map((f) => <button key={f.key} onClick={() => { setFilter(f.key); setPage(1); }} className={`badge !px-3 !py-1.5 ${filter === f.key ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>{f.label}</button>)}
        </div>
      </div>

      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-cream-100 text-brown-800/70">
            <tr>
              <th className="text-left py-3 px-4 font-medium">Élève</th>
              <th className="text-left py-3 px-4 font-medium">Contact</th>
              <th className="text-right py-3 px-4 font-medium">Restantes</th>
              <th className="text-right py-3 px-4 font-medium">Réservées</th>
              <th className="text-right py-3 px-4 font-medium">Compétences</th>
              <th className="text-left py-3 px-4 font-medium">Code</th>
              <th className="text-left py-3 px-4 font-medium">Référent</th>
              <th className="text-left py-3 px-4 font-medium">Examen</th>
            </tr>
          </thead>
          <tbody>
            {!data ? <tr><td colSpan={8} className="py-10 text-center text-brown-500">Chargement…</td></tr>
              : data.results.length === 0 ? <tr><td colSpan={8} className="py-10 text-center text-brown-800/60">Aucun élève</td></tr>
              : data.results.map((s) => (
                <tr key={s.id} className="border-t border-cream-200 hover:bg-cream-50">
                  <td className="py-3 px-4"><Link href={`/admin/students/${s.id}`} className="font-medium text-brown-700 hover:underline">{s.user.last_name} {s.user.first_name}</Link></td>
                  <td className="py-3 px-4 text-brown-800/70">{s.user.email}{s.phone && <><br />{s.phone}</>}</td>
                  <td className={`py-3 px-4 text-right ${s.remaining_hours <= 1 ? 'text-red-700 font-semibold' : ''}`}>{s.remaining_hours.toFixed(1)} h</td>
                  <td className="py-3 px-4 text-right">{s.reserved_hours.toFixed(1)} h</td>
                  <td className="py-3 px-4 text-right">{s.competency_progress.percent} %</td>
                  <td className="py-3 px-4">{s.has_lms_access ? <span className="badge bg-brown-700 text-cream-50">actif</span> : <span className="text-brown-800/40">—</span>}</td>
                  <td className="py-3 px-4">{s.referent_instructor_name || <span className="text-brown-800/40">—</span>}</td>
                  <td className="py-3 px-4">{s.ready_for_exam ? <span className="badge bg-caramel text-brown-900">prêt</span> : ''}</td>
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
    </AdminShell>
  );
}
