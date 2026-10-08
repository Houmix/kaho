import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Link from 'next/link';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import Logo from '@/components/Logo';
import { Offer, Package, formatPrice } from '@/lib/offers';

const statusCls: Record<Package['status'], string> = {
  PENDING: 'bg-cream-200 text-brown-800',
  COMPLETED: 'bg-brown-700 text-cream-50',
  FAILED: 'bg-red-100 text-red-700',
};

export default function Purchases() {
  const router = useRouter();
  const { logout } = useAuth();
  const ready = useRequireAuth();
  const preselected = typeof router.query.offer === 'string' ? Number(router.query.offer) : null;
  const [offers, setOffers] = useState<Offer[]>([]);
  const [packages, setPackages] = useState<Package[]>([]);
  const [busy, setBusy] = useState<number | null>(null);
  const [message, setMessage] = useState('');

  const loadPackages = () => api.get('/packages/').then((r) => setPackages(r.data.results ?? r.data));

  useEffect(() => {
    if (!ready) return;
    api.get('/offers/').then((r) => setOffers(r.data));
    loadPackages();
  }, [ready]);

  const choose = async (offer: Offer) => {
    setBusy(offer.id);
    setMessage('');
    try {
      await api.post('/packages/', { offer: offer.id });
      await loadPackages();
      setMessage(`Demande enregistrée pour « ${offer.name} ». Vos heures seront créditées dès validation du paiement par votre monitrice.`);
    } catch {
      setMessage("Impossible d'enregistrer la demande. Réessayez.");
    } finally {
      setBusy(null);
    }
  };

  return (
    <>
      <Head><title>Acheter des heures — Kaho</title></Head>
      <header className="bg-white border-b border-cream-200">
        <div className="container flex items-center justify-between py-3">
          <Logo />
          <div className="flex gap-2">
            <Link href="/student/dashboard" className="btn-outline">Mon espace</Link>
            <button onClick={() => { logout(); router.push('/login'); }} className="btn-secondary">Déconnexion</button>
          </div>
        </div>
      </header>

      <main className="container py-8">
        <h1 className="text-3xl mb-2">Acheter des heures</h1>
        <p className="text-brown-800/70 mb-8">Choisissez une offre : votre monitrice valide le paiement et vos heures sont créditées.</p>

        {message && <div className="card mb-8 border-brown-300 bg-brown-50">{message}</div>}

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {offers.map((o) => {
            const highlight = o.id === preselected || (preselected === null && o.is_featured);
            return (
              <div key={o.id} className={`card text-center ${highlight ? 'ring-2 ring-brown-500' : ''}`}>
                {o.is_featured && <span className="badge bg-brown-700 text-cream-50 mb-3">Le plus choisi</span>}
                <h2 className="text-xl mb-1">{o.name}</h2>
                <p className="text-4xl font-display text-brown-700 my-3">{formatPrice(o.price)}</p>
                <p className="text-brown-800/70">{o.hours} h de conduite</p>
                <p className="text-sm text-brown-800/60 mb-5">{o.description || `soit ${formatPrice(o.price_per_hour)} / heure`}</p>
                <button onClick={() => choose(o)} disabled={busy !== null} className={`${highlight ? 'btn-primary' : 'btn-secondary'} w-full disabled:opacity-60`}>
                  {busy === o.id ? 'Enregistrement…' : 'Choisir cette offre'}
                </button>
              </div>
            );
          })}
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
                  <th className="text-left py-3 px-4 font-medium">Heures</th>
                  <th className="text-left py-3 px-4 font-medium">Montant</th>
                  <th className="text-left py-3 px-4 font-medium">Statut</th>
                </tr>
              </thead>
              <tbody>
                {packages.map((p) => (
                  <tr key={p.id} className="border-t border-cream-200">
                    <td className="py-3 px-4">{new Date(p.created_at).toLocaleDateString('fr-FR')}</td>
                    <td className="py-3 px-4">{p.offer_name || '—'}</td>
                    <td className="py-3 px-4">{p.hours_purchased} h</td>
                    <td className="py-3 px-4">{formatPrice(p.amount_paid)}</td>
                    <td className="py-3 px-4"><span className={`badge ${statusCls[p.status]}`}>{p.status_display}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </>
  );
}
