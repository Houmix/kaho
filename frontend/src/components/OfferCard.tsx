import { ReactNode } from 'react';
import { Offer, billingSuffix, formatPrice, offerHighlights } from '@/lib/offers';

export default function OfferCard({ offer, highlight, action, badge }: { offer: Offer; highlight?: boolean; action: ReactNode; badge?: string }) {
  const suffix = billingSuffix(offer);
  return (
    <div className={`card flex flex-col text-center ${highlight ? 'ring-2 ring-brown-500' : ''}`}>
      {(badge || offer.is_featured) && <span className="badge bg-brown-700 text-cream-50 mb-3 self-center">{badge ?? 'Le plus choisi'}</span>}
      <p className="text-xs uppercase tracking-wide text-caramel font-medium">{offer.category_display}</p>
      <h3 className="text-xl mb-1">{offer.name}</h3>
      <p className="text-4xl font-display text-brown-700 mt-3 mb-1">{formatPrice(offer.price)}</p>
      {suffix && <p className="text-sm text-brown-800/60">{suffix}</p>}
      {offer.description && <p className="text-brown-800/70 mt-2">{offer.description}</p>}
      <ul className="text-sm text-brown-800/80 my-4 space-y-1 text-left mx-auto">
        {offerHighlights(offer).map((h) => <li key={h} className="flex gap-2"><span className="text-brown-500">✓</span>{h}</li>)}
      </ul>
      <div className="mt-auto">{action}</div>
    </div>
  );
}
