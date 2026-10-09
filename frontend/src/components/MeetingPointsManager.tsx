import { useCallback, useEffect, useState } from 'react';
import api from '@/lib/api';
import { MeetingPoint, apiError } from '@/lib/types';

type Point = MeetingPoint & { description?: string };

/** Gestion des points de rendez-vous (lieux où commencent les leçons). Accessible aux moniteurs et à l'équipe admin. */
export default function MeetingPointsManager({ compact = false }: { compact?: boolean }) {
  const [points, setPoints] = useState<Point[] | null>(null);
  const [form, setForm] = useState({ name: '', address: '', description: '' });
  const [editing, setEditing] = useState<number | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const load = useCallback(() => api.get('/meeting-points/').then((r) => setPoints(r.data)), []);
  useEffect(() => { load(); }, [load]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setMsg(null);
    try {
      editing ? await api.patch(`/meeting-points/${editing}/`, form) : await api.post('/meeting-points/', form);
      setForm({ name: '', address: '', description: '' }); setEditing(null); await load();
      setMsg({ ok: true, text: editing ? 'Point de rendez-vous modifié.' : 'Point de rendez-vous ajouté : les élèves peuvent le choisir à la réservation.' });
    } catch (err) { setMsg({ ok: false, text: apiError(err, 'Enregistrement impossible.') }); }
    finally { setBusy(false); }
  };
  const remove = async (p: Point) => {
    if (!confirm(`Supprimer « ${p.name} » ? Les leçons déjà réservées à cet endroit passent en « lieu à convenir ».`)) return;
    try { await api.delete(`/meeting-points/${p.id}/`); await load(); setMsg({ ok: true, text: 'Point supprimé.' }); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Suppression impossible.') }); }
  };

  return (
    <div>
      {msg && <div className={`rounded-xl px-3 py-2 mb-3 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}
      <form onSubmit={submit} className={`grid gap-2 mb-4 ${compact ? '' : 'sm:grid-cols-[1fr_1.5fr_1fr_auto]'}`}>
        <input required placeholder="Nom (ex : Gare, Parking du lycée)" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-field !py-2 text-sm" />
        <input required placeholder="Adresse complète" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className="input-field !py-2 text-sm" />
        <input placeholder="Précision (facultatif : devant l'entrée B…)" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="input-field !py-2 text-sm" />
        <div className="flex gap-2"><button disabled={busy} className="btn-primary !py-2 text-sm whitespace-nowrap">{editing ? 'Enregistrer' : '+ Ajouter'}</button>{editing && <button type="button" onClick={() => { setEditing(null); setForm({ name: '', address: '', description: '' }); }} className="text-sm text-brown-700 hover:underline">Annuler</button>}</div>
      </form>
      {!points ? <p className="text-sm text-brown-500">Chargement…</p> : points.length === 0 ? <p className="text-sm text-brown-800/60">Aucun point de rendez-vous. Sans lieu défini, l'élève réserve avec « lieu à convenir avec le moniteur ».</p> : (
        <ul className="divide-y divide-cream-200 text-sm">
          {points.map((p) => (
            <li key={p.id} className="py-2 flex flex-wrap items-center gap-2">
              <span className="font-medium">{p.name}</span><span className="text-brown-800/70">{p.address}</span>{p.description && <span className="text-xs text-brown-800/50">· {p.description}</span>}
              <span className="ml-auto space-x-3 text-xs"><button onClick={() => { setEditing(p.id); setForm({ name: p.name, address: p.address, description: p.description || '' }); }} className="text-brown-700 hover:underline">Modifier</button><button onClick={() => remove(p)} className="text-red-700 hover:underline">Supprimer</button></span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
