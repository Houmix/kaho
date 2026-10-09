import { useCallback, useEffect, useState } from 'react';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import { BILLING_LABELS, CATEGORY_LABELS, OfferAdmin, formatPrice } from '@/lib/offers';
import { apiError } from '@/lib/types';

const EMPTY = { name: '', description: '', category: 'PERMIS_B', hours: 20, price: '', billing_type: 'ONE_TIME', includes_lms: false, validity_months: '', for_code_status: 'ANY', for_level: 'ANY', gearbox: 'ANY', is_featured: false, is_active: true, display_order: 0 };

function OfferForm({ offer, onDone }: { offer: OfferAdmin | null; onDone: () => void }) {
  const [f, setF] = useState<any>(offer ? { ...offer, validity_months: offer.validity_months ?? '' } : { ...EMPTY });
  const [error, setError] = useState('');
  const set = (k: string, v: unknown) => setF({ ...f, [k]: v });
  const save = async (e: React.FormEvent) => {
    e.preventDefault(); setError('');
    const body = { ...f, validity_months: f.validity_months === '' ? null : Number(f.validity_months) };
    try { offer ? await api.patch(`/admin/offers/${offer.id}/`, body) : await api.post('/admin/offers/', body); onDone(); }
    catch (err) { setError(apiError(err, 'Enregistrement impossible.')); }
  };
  const sel = (k: string, opts: [string, string][]) => <select value={f[k]} onChange={(e) => set(k, e.target.value)} className="input-field !py-2">{opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>;
  return (
    <form onSubmit={save} className="card border-brown-300 mb-6 space-y-3">
      <h2 className="text-xl">{offer ? `Modifier « ${offer.name} »` : 'Nouvelle offre'}</h2>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <label className="block lg:col-span-2"><span className="text-xs text-brown-800/70">Nom</span><input required value={f.name} onChange={(e) => set('name', e.target.value)} className="input-field !py-2" /></label>
        <label className="block lg:col-span-2"><span className="text-xs text-brown-800/70">Description courte</span><input value={f.description} onChange={(e) => set('description', e.target.value)} className="input-field !py-2" /></label>
        <label className="block"><span className="text-xs text-brown-800/70">Catégorie</span>{sel('category', Object.entries(CATEGORY_LABELS) as [string, string][])}</label>
        <label className="block"><span className="text-xs text-brown-800/70">Heures de conduite</span><input type="number" min={0} step={0.5} value={f.hours} onChange={(e) => set('hours', Number(e.target.value))} className="input-field !py-2" /></label>
        <label className="block"><span className="text-xs text-brown-800/70">Prix TTC (€)</span><input required type="number" min={0} step={1} value={f.price} onChange={(e) => set('price', e.target.value)} className="input-field !py-2" /></label>
        <label className="block"><span className="text-xs text-brown-800/70">Facturation</span>{sel('billing_type', Object.entries(BILLING_LABELS) as [string, string][])}</label>
        <label className="block"><span className="text-xs text-brown-800/70">Validité (mois, vide = illimitée)</span><input type="number" min={1} value={f.validity_months} onChange={(e) => set('validity_months', e.target.value)} className="input-field !py-2" /></label>
        <label className="block"><span className="text-xs text-brown-800/70">Cible : code</span>{sel('for_code_status', [['ANY', 'Indifférent'], ['TO_PASS', 'Code à passer'], ['OBTAINED', 'Code obtenu']])}</label>
        <label className="block"><span className="text-xs text-brown-800/70">Cible : niveau</span>{sel('for_level', [['ANY', 'Indifférent'], ['BEGINNER', 'Débutant'], ['REFRESH', 'Remise à niveau']])}</label>
        <label className="block"><span className="text-xs text-brown-800/70">Boîte</span>{sel('gearbox', [['ANY', 'Indifférent'], ['AUTO', 'Automatique'], ['MANUAL', 'Manuelle']])}</label>
        <label className="block"><span className="text-xs text-brown-800/70">Ordre d'affichage</span><input type="number" value={f.display_order} onChange={(e) => set('display_order', Number(e.target.value))} className="input-field !py-2" /></label>
      </div>
      <div className="flex flex-wrap gap-4 text-sm">
        <label className="flex items-center gap-1.5"><input type="checkbox" checked={f.includes_lms} onChange={(e) => set('includes_lms', e.target.checked)} className="accent-brown-700" /> Inclut le code en ligne (cours, quiz, examens blancs)</label>
        <label className="flex items-center gap-1.5"><input type="checkbox" checked={f.is_featured} onChange={(e) => set('is_featured', e.target.checked)} className="accent-brown-700" /> Mise en avant</label>
        <label className="flex items-center gap-1.5"><input type="checkbox" checked={f.is_active} onChange={(e) => set('is_active', e.target.checked)} className="accent-brown-700" /> Visible sur le site</label>
      </div>
      {error && <p className="text-sm text-red-700">{error}</p>}
      <div className="flex gap-2"><button className="btn-primary !py-2 text-sm">Enregistrer</button><button type="button" onClick={onDone} className="btn-secondary !py-2 text-sm">Annuler</button></div>
    </form>
  );
}

export default function AdminOffers() {
  const ready = useRequireAuth('OWNER');
  const [offers, setOffers] = useState<OfferAdmin[] | null>(null);
  const [editing, setEditing] = useState<OfferAdmin | null | 'new'>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const load = useCallback(() => api.get('/admin/offers/').then((r) => setOffers(r.data)), []);
  useEffect(() => { if (ready) load(); }, [ready, load]);
  const act = async (fn: () => Promise<unknown>, ok: string) => { setMsg(null); try { await fn(); await load(); setMsg({ ok: true, text: ok }); } catch (err) { setMsg({ ok: false, text: apiError(err, 'Action impossible.') }); } };

  return (
    <AdminShell title="Offres & tarifs" wide>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-2"><h1 className="text-3xl">Offres & tarifs</h1><button onClick={() => setEditing('new')} className="btn-primary">+ Nouvelle offre</button></div>
      <p className="text-brown-800/70 mb-6">Formules affichées sur le site et proposées par le simulateur. Une offre déjà vendue est désactivée plutôt que supprimée.</p>
      {msg && <div className={`rounded-xl px-4 py-3 mb-4 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}
      {editing && <OfferForm offer={editing === 'new' ? null : editing} onDone={() => { setEditing(null); load(); }} />}
      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-cream-100 text-brown-800/70"><tr><th className="text-left py-3 px-4 font-medium">Offre</th><th className="text-left py-3 px-4 font-medium">Catégorie</th><th className="text-right py-3 px-4 font-medium">Heures</th><th className="text-right py-3 px-4 font-medium">Prix</th><th className="text-left py-3 px-4 font-medium">Facturation</th><th className="text-left py-3 px-4 font-medium">Options</th><th className="text-right py-3 px-4 font-medium">Ventes</th><th className="text-left py-3 px-4 font-medium">Statut</th><th></th></tr></thead>
          <tbody>
            {!offers ? <tr><td colSpan={9} className="py-8 text-center text-brown-500">Chargement…</td></tr> : offers.length === 0 ? <tr><td colSpan={9} className="py-8 text-center text-brown-800/60">Aucune offre. Créez votre première formule.</td></tr> : offers.map((o) => (
              <tr key={o.id} className={`border-t border-cream-200 ${!o.is_active ? 'opacity-60' : ''}`}>
                <td className="py-3 px-4"><div className="font-medium">{o.name}{o.is_featured && <span className="badge bg-caramel text-brown-900 ml-2">mise en avant</span>}</div><div className="text-xs text-brown-800/60">{o.description}</div></td>
                <td className="py-3 px-4">{o.category_display}</td>
                <td className="py-3 px-4 text-right">{o.hours ? `${o.hours} h` : '—'}</td>
                <td className="py-3 px-4 text-right font-semibold">{formatPrice(o.price)}{o.price_per_hour ? <div className="text-xs font-normal text-brown-800/60">{o.price_per_hour} €/h</div> : null}</td>
                <td className="py-3 px-4">{o.billing_display}</td>
                <td className="py-3 px-4 text-xs">{[o.includes_lms ? 'code en ligne' : null, o.validity_months ? `${o.validity_months} mois` : 'illimitée'].filter(Boolean).join(' · ')}</td>
                <td className="py-3 px-4 text-right">{o.sales}</td>
                <td className="py-3 px-4"><label className="text-xs flex items-center gap-1"><input type="checkbox" checked={o.is_active} onChange={(e) => act(() => api.patch(`/admin/offers/${o.id}/`, { is_active: e.target.checked }), e.target.checked ? 'Offre visible.' : 'Offre masquée.')} className="accent-brown-700" /> visible</label></td>
                <td className="py-3 px-4 text-right whitespace-nowrap space-x-3"><button onClick={() => setEditing(o)} className="text-brown-700 text-xs hover:underline">Modifier</button><button onClick={() => confirm(`Supprimer « ${o.name} » ?`) && act(() => api.delete(`/admin/offers/${o.id}/`), 'Offre supprimée ou désactivée.')} className="text-red-700 text-xs hover:underline">Supprimer</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AdminShell>
  );
}
