import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { BACKOFFICE, useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import { ActivityEntry, Paginated, downloadFile } from '@/lib/admin';

export const KIND_STYLE: Record<string, string> = {
  BOOKING: 'bg-brown-700 text-cream-50', CANCELLATION: 'bg-cream-200 text-brown-800', LATE_CANCELLATION: 'bg-caramel/50 text-brown-900',
  NO_SHOW: 'bg-red-100 text-red-700', REFUND: 'bg-cream-200 text-brown-800', SLOT_MOVED: 'bg-caramel/30 text-brown-900',
  PAYMENT: 'bg-brown-500 text-cream-50', HOURS_ADDED: 'bg-brown-300 text-brown-900', APPLICATION: 'bg-cream-200 text-brown-800',
  INSTRUCTOR: 'bg-cream-200 text-brown-800', LESSON: 'bg-cream-200 text-brown-800', REMINDERS: 'bg-cream-100 text-brown-800/70',
  STATUS: 'bg-caramel/40 text-brown-900', MESSAGE: 'bg-cream-200 text-brown-800', ABSENCE: 'bg-caramel/30 text-brown-900', PLANNING: 'bg-caramel/30 text-brown-900',
  TEAM: 'bg-brown-900 text-cream-50', CONTRACT: 'bg-cream-200 text-brown-800', LMS: 'bg-brown-300 text-brown-900', PAYMENT_LINK: 'bg-brown-500 text-cream-50',
};
const KINDS = [
  ['', 'Tout'], ['BOOKING,CANCELLATION,LATE_CANCELLATION,SLOT_MOVED,PLANNING', 'Réservations & planning'], ['NO_SHOW,REFUND', 'Absences & re-crédits'],
  ['PAYMENT,HOURS_ADDED,PAYMENT_LINK,LMS', 'Paiements & crédits'], ['STATUS,DOCUMENT,CONTRACT', 'Dossiers élèves'], ['APPLICATION,INSTRUCTOR,ABSENCE', 'Moniteurs'],
  ['MESSAGE,REMINDERS', 'Messages'], ['TEAM', 'Équipe admin'],
];

export function ActivityList({ items }: { items: ActivityEntry[] }) {
  return (
    <ul className="divide-y divide-cream-200">
      {items.map((e) => (
        <li key={e.id} className="py-2 flex gap-3 text-sm">
          <span className="text-brown-800/50 whitespace-nowrap w-28 shrink-0">{new Date(e.created_at).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</span>
          <span className={`badge shrink-0 ${KIND_STYLE[e.kind] || 'bg-cream-200 text-brown-800'}`}>{e.kind_display}</span>
          <span className="flex-1">
            {e.message}
            {e.actor_name && <span className="text-brown-800/50"> — par {e.actor_name}</span>}
            {e.student && <> · <Link href={`/admin/students/${e.student}`} className="text-brown-700 hover:underline">élève</Link></>}
            {e.instructor && <> · <Link href={`/admin/instructors/${e.instructor}`} className="text-brown-700 hover:underline">moniteur</Link></>}
          </span>
        </li>
      ))}
    </ul>
  );
}

export default function AdminActivity() {
  const ready = useRequireAuth(BACKOFFICE);
  const [kind, setKind] = useState('');
  const [actor, setActor] = useState('');
  const [adminOnly, setAdminOnly] = useState(false);
  const [q, setQ] = useState('');
  const [since, setSince] = useState('');
  const [page, setPage] = useState(1);
  const [actors, setActors] = useState<{ id: number; name: string; role: string }[]>([]);
  const [data, setData] = useState<Paginated<ActivityEntry> | null>(null);
  const params = useCallback(() => ({ kind: kind || undefined, actor: actor || undefined, admin_only: adminOnly ? 1 : undefined, q: q || undefined, since: since || undefined }), [kind, actor, adminOnly, q, since]);
  const load = useCallback(() => api.get('/admin/activity/', { params: { ...params(), page, page_size: 50 } }).then((r) => setData(r.data)), [params, page]);
  useEffect(() => { if (ready) api.get('/admin/activity/actors/').then((r) => setActors(r.data)); }, [ready]);
  useEffect(() => { if (!ready) return; const t = setTimeout(load, 200); return () => clearTimeout(t); }, [ready, load]);
  const pages = data ? Math.max(1, Math.ceil(data.count / 50)) : 1;

  return (
    <AdminShell title="Activité">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
        <h1 className="text-3xl">Historique & audit</h1>
        <button onClick={() => downloadFile('/admin/activity/export/', `journal-${new Date().toISOString().slice(0, 10)}.csv`, params())} className="btn-secondary">Exporter CSV</button>
      </div>
      <p className="text-brown-800/70 mb-6">Chaque action est tracée avec son auteur : réservations, paiements, statuts, documents, absences, messages, comptes admin.</p>
      <div className="flex flex-wrap gap-2 mb-3 items-center">
        <input value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} placeholder="Rechercher dans les messages…" className="input-field sm:w-64 !py-2" />
        <select value={actor} onChange={(e) => { setActor(e.target.value); setPage(1); }} className="input-field sm:w-56 !py-2">
          <option value="">Tous les auteurs</option>
          {actors.map((a) => <option key={a.id} value={a.id}>{a.name} · {a.role}</option>)}
        </select>
        <input type="date" value={since} onChange={(e) => { setSince(e.target.value); setPage(1); }} className="input-field !py-2" aria-label="Depuis le" />
        <label className="flex items-center gap-1.5 text-sm"><input type="checkbox" checked={adminOnly} onChange={(e) => { setAdminOnly(e.target.checked); setPage(1); }} className="accent-brown-700" /> Actions des administrateurs uniquement</label>
      </div>
      <div className="flex flex-wrap gap-1 mb-4">{KINDS.map(([k, l]) => <button key={k} onClick={() => { setKind(k); setPage(1); }} className={`badge !px-3 !py-1.5 ${kind === k ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>{l}</button>)}</div>
      <div className="card">
        {!data ? <p className="text-brown-500">Chargement…</p> : data.results.length === 0 ? <p className="text-brown-800/60">Aucun événement.</p> : <ActivityList items={data.results} />}
      </div>
      {pages > 1 && <div className="flex items-center justify-end gap-2 mt-3 text-sm"><button disabled={page <= 1} onClick={() => setPage(page - 1)} className="btn-secondary !py-1.5 disabled:opacity-40">←</button><span>Page {page} / {pages}</span><button disabled={page >= pages} onClick={() => setPage(page + 1)} className="btn-secondary !py-1.5 disabled:opacity-40">→</button></div>}
    </AdminShell>
  );
}
