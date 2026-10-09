import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AppShell from '@/components/AppShell';
import OfferCard from '@/components/OfferCard';
import PdfLink from '@/components/PdfLink';
import OfferConfigurator from '@/components/OfferConfigurator';
import { CATEGORY_LABELS, Offer, OfferCategory, Package, formatPrice } from '@/lib/offers';
import { StudentProfile, frDate } from '@/lib/types';

const statusCls: Record<Package['status'], string> = {
  PENDING: 'bg-cream-200 text-brown-800',
  COMPLETED: 'bg-brown-700 text-cream-50',
  FAILED: 'bg-red-100 text-red-700',
};

export default function Purchases() {
  const router = useRouter();
  const ready = useRequireAuth('STUDENT');
  const preselected = typeof router.query.offer === 'string' ? Number(router.query.offer) : null;
  const [offers, setOffers] = useState<Offer[]>([]);
  const [packages, setPackages] = useState<Package[]>([]);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [category, setCategory] = useState<OfferCategory | null>(null);
  const [busy, setBusy] = useState<number | null>(null);
  const [configuring, setConfiguring] = useState<Offer | null>(null);
  const [message, setMessage] = useState('');

  const load = () => Promise.all([
    api.get('/packages/').then((r) => setPackages(r.data.results ?? r.data)),
    api.get('/student-profiles/my_profile/').then((r) => setProfile(r.data)),
  ]);

  useEffect(() => {
    if (!ready) return;
    api.get('/offers/').then((r) => setOffers(r.data));
    load();
    if (router.query.paid === '1') setMessage('Paiement reçu, merci ! Vos heures et accès sont crédités (ou le seront dans quelques instants).');
    if (router.query.cancelled === '1') setMessage('Paiement annulé. Votre lien reste valable 24 h, ou contactez votre école.');
  }, [ready, router.query.paid, router.query.cancelled]);

  useEffect(() => {
    if (preselected && offers.length) {
      const o = offers.find((x) => x.id === preselected);
      if (o) setCategory(o.category);
    }
  }, [preselected, offers]);

  const choose = (offer: Offer) => { setMessage(''); setConfiguring(offer); window.scrollTo({ top: 0, behavior: 'smooth' }); };
  const payOnline = async (p: Package) => {
    setBusy(p.id); setMessage('');
    try { const r = await api.post(`/packages/${p.id}/checkout/`); window.location.href = r.data.url; }
    catch (err: any) { setMessage(err?.response?.data?.detail || 'Paiement en ligne indisponible.'); }
    finally { setBusy(null); }
  };

  const hasFormula = packages.some((p) => p.status === 'COMPLETED' && p.offer_category !== 'RECHARGE');
  const categories = (Object.keys(CATEGORY_LABELS) as OfferCategory[]).filter((c) => c !== 'OPTION' && offers.some((o) => o.category === c && !o.is_addon));
  const visible = offers.filter((o) => !o.is_addon && (!category || o.category === category));

  return (
    <AppShell title="Mes offres">
      <h1 className="text-3xl mb-2">Offres & heures</h1>
      <p className="text-brown-800/70 mb-6">Choisissez une formule ou rechargez des heures : votre moniteur valide le paiement et vos accès sont crédités.</p>

      {profile && (
        <div className="grid sm:grid-cols-3 gap-4 mb-8">
          <div className="card py-4"><p className="text-sm text-brown-800/70">Heures restantes</p><p className="text-3xl font-display">{profile.remaining_hours.toFixed(1)} h</p></div>
          <div className="card py-4">
            <p className="text-sm text-brown-800/70">Cours de code en ligne</p>
            <p className="text-xl font-display">{profile.has_lms_access ? 'Actif' : 'Non inclus'}</p>
            {profile.has_lms_access && <p className="text-xs text-brown-800/60">{profile.lms_access_until ? `jusqu'au ${frDate(profile.lms_access_until, { day: 'numeric', month: 'long', year: 'numeric' })}` : 'sans limite'}</p>}
          </div>
          <div className="card py-4"><p className="text-sm text-brown-800/70">Formule</p><p className="text-xl font-display">{hasFormula ? 'Souscrite' : 'Aucune'}</p></div>
        </div>
      )}

      {message && <div className="card mb-8 border-brown-300 bg-brown-50">{message}</div>}
      {configuring && <OfferConfigurator base={configuring} offers={offers} onDone={(text, ok = true) => { setMessage(text); if (ok) { setConfiguring(null); load(); } }} onCancel={() => setConfiguring(null)} />}

      {categories.length > 1 && (
        <div className="flex flex-wrap gap-2 mb-6">
          <button onClick={() => setCategory(null)} className={`badge !px-4 !py-2 ${category === null ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>Toutes</button>
          {categories.map((c) => (
            <button key={c} onClick={() => setCategory(c)} className={`badge !px-4 !py-2 ${category === c ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>
              {CATEGORY_LABELS[c]}{c === 'RECHARGE' && hasFormula ? ' ★' : ''}
            </button>
          ))}
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-6 mb-12">
        {visible.map((o) => (
          <OfferCard key={o.id} offer={o} highlight={o.id === preselected || (preselected === null && o.is_featured)}
            action={
              <button onClick={() => choose(o)} disabled={busy !== null} className={`${o.id === preselected ? 'btn-primary' : 'btn-secondary'} w-full disabled:opacity-60`}>
                {configuring?.id === o.id ? 'Formule sélectionnée' : 'Choisir cette offre'}
              </button>
            } />
        ))}
      </div>

      <h2 className="text-2xl mb-4">Mes achats</h2>
      {packages.length === 0 ? (
        <p className="text-brown-800/60">Aucun achat pour le moment.</p>
      ) : (
        <div className="card p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-cream-100 text-brown-800/70">
              <tr>
                <th className="text-left py-3 px-4 font-medium">Date</th>
                <th className="text-left py-3 px-4 font-medium">Offre</th>
                <th className="text-left py-3 px-4 font-medium">Contenu</th>
                <th className="text-left py-3 px-4 font-medium">Montant</th>
                <th className="text-left py-3 px-4 font-medium">Validité</th>
                <th className="text-left py-3 px-4 font-medium">Statut</th>
                <th className="text-left py-3 px-4 font-medium">Facture</th>
              </tr>
            </thead>
            <tbody>
              {packages.map((p) => (
                <tr key={p.id} className="border-t border-cream-200">
                  <td className="py-3 px-4">{new Date(p.created_at).toLocaleDateString('fr-FR')}</td>
                  <td className="py-3 px-4">{p.display_label}{p.addon_items?.length > 0 && <ul className="text-xs text-brown-800/60">{p.addon_items.map((a) => <li key={a.id}>+ {a.label}</li>)}</ul>}{p.requested_skills?.length > 0 && <p className="text-xs text-brown-800/60">Compétences : {p.requested_skills.join(', ')}</p>}</td>
                  <td className="py-3 px-4">{[p.hours_purchased > 0 ? `${p.hours_purchased} h` : null, p.includes_lms ? 'Code en ligne' : null].filter(Boolean).join(' + ') || '—'}</td>
                  <td className="py-3 px-4">{formatPrice(p.bundle_total ?? p.amount_paid)}{p.installments > 1 && <div className="text-xs text-brown-800/60">{p.installments_paid}/{p.installments} échéance(s)</div>}</td>
                  <td className="py-3 px-4">{p.expires_at ? frDate(p.expires_at, { day: 'numeric', month: 'short', year: 'numeric' }) : '—'}</td>
                  <td className="py-3 px-4"><span className={`badge ${statusCls[p.status]}`}>{p.status_display}</span>{p.status === 'PENDING' && <><br /><button onClick={() => payOnline(p)} disabled={busy === p.id} className="btn-primary !py-1 !px-3 text-xs mt-1">{busy === p.id ? '…' : 'Payer en ligne'}</button></>}</td>
                  <td className="py-3 px-4">{p.invoice_id && p.invoice_number ? <PdfLink invoiceId={p.invoice_id} number={p.invoice_number} /> : <span className="text-brown-800/40">—</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppShell>
  );
}
